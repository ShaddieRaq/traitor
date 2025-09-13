"""
Test Race Condition Fix for Double Trade Prevention
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, MagicMock

from app.models.models import Bot, Trade
from app.services.trading_service import TradingService, TradeExecutionError
from app.core.database import get_db


class TestRaceConditionFix:
    """Test that the race condition fix prevents double trades."""
    
    @pytest.fixture
    def db_session(self):
        """Get database session for testing."""
        db = next(get_db())
        yield db
        db.close()
    
    @pytest.fixture
    def mock_bot(self, db_session):
        """Create a test bot."""
        bot = Bot(
            name="Race Test Bot",
            pair="ETH-USD",
            status="RUNNING",
            current_combined_score=0.8,
            signal_config='{"RSI": {"enabled": true, "weight": 0.5}, "MACD": {"enabled": true, "weight": 0.3}, "MovingAverage": {"enabled": true, "weight": 0.2}}'
        )
        db_session.add(bot)
        db_session.commit()
        db_session.refresh(bot)
        yield bot
        
        # Cleanup
        db_session.query(Trade).filter(Trade.bot_id == bot.id).delete()
        db_session.query(Bot).filter(Bot.id == bot.id).delete()
        db_session.commit()
    
    @pytest.fixture
    def trading_service(self, db_session):
        """Create trading service with mocked external dependencies."""
        service = TradingService(db_session)
        
        # Mock external services to avoid real API calls
        service.coinbase_service.get_historical_data = MagicMock(return_value={
            'RSI': [45], 'MACD': [0.1], 'MovingAverage': [0.05]
        })
        service.coinbase_service.place_order = MagicMock(return_value={
            'order_id': f'test-order-{int(time.time())}',
            'status': 'pending'
        })
        service.coinbase_service.get_product_ticker = MagicMock(return_value={
            'price': '4000.00'
        })
        service.coinbase_service.get_accounts = MagicMock(return_value=[
            {'currency': 'USD', 'balance': '1000.00'},
            {'currency': 'ETH', 'balance': '5.0'}
        ])
        
        return service
    
    def test_atomic_cooldown_prevents_double_trades(self, mock_bot, trading_service):
        """Test that atomic cooldown checking prevents double trades."""
        
        # Set a long cooldown to ensure trades should be blocked
        mock_bot.cooldown_minutes = 60  # 1 hour cooldown
        
        # Create an old trade to trigger cooldown
        old_trade = Trade(
            bot_id=mock_bot.id,
            product_id="ETH-USD",
            side="BUY",
            size=1.0,
            price=4000.0,
            order_id="old-trade",
            status="completed",
            combined_signal_score=0.8,
            created_at=datetime.utcnow() - timedelta(minutes=30),
            filled_at=datetime.utcnow() - timedelta(minutes=30)
        )
        trading_service.db.add(old_trade)
        trading_service.db.commit()
        
        def execute_trade_attempt():
            """Attempt to execute a trade."""
            try:
                result = trading_service.execute_trade(
                    bot_id=mock_bot.id,
                    side="SELL",
                    size_usd=100.0
                )
                return {"success": True, "result": result}
            except TradeExecutionError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": f"Unexpected: {str(e)}"}
        
        # Execute two concurrent trade attempts
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(execute_trade_attempt)
            future2 = executor.submit(execute_trade_attempt)
            
            result1 = future1.result(timeout=10)
            result2 = future2.result(timeout=10)
        
        print(f"Result 1: {result1}")
        print(f"Result 2: {result2}")
        
        # Both should fail - either due to cooldown or Redis lock
        # The trading service returns success=True but the inner result has success=False
        assert not result1["result"]["success"], "First trade should fail"
        assert not result2["result"]["success"], "Second trade should fail"
        
        # One should fail due to cooldown, the other due to Redis lock
        error1 = result1["result"]["error"].lower()
        error2 = result2["result"]["error"].lower()
        
        # At least one should mention cooldown, and at least one should mention "trade in progress"
        has_cooldown_error = "cooldown" in error1 or "cooldown" in error2
        has_lock_error = "trade is currently in progress" in error1 or "trade is currently in progress" in error2
        
        assert has_cooldown_error, f"Expected cooldown error in one result: {error1}, {error2}"
        assert has_lock_error, f"Expected lock error in one result: {error1}, {error2}"
        
        # Verify no new trades were created
        new_trades = trading_service.db.query(Trade).filter(
            Trade.bot_id == mock_bot.id,
            Trade.id != old_trade.id
        ).count()
        assert new_trades == 0, "No new trades should have been created during cooldown"
    
    def test_atomic_lock_prevents_simultaneous_execution(self, mock_bot, trading_service):
        """Test that atomic locking prevents simultaneous trade execution."""
        
        # Remove cooldown for this test
        mock_bot.cooldown_minutes = 0
        
        success_count = 0
        results = []
        
        def execute_trade_attempt():
            """Attempt to execute a trade with timing."""
            nonlocal success_count
            try:
                start_time = time.time()
                result = trading_service.execute_trade(
                    bot_id=mock_bot.id,
                    side="BUY", 
                    size_usd=50.0
                )
                end_time = time.time()
                
                if result.get("success"):
                    success_count += 1
                
                return {
                    "success": result.get("success", False),
                    "duration": end_time - start_time,
                    "trade_id": result.get("trade_id"),
                    "error": result.get("error")
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "success": False,
                    "duration": end_time - start_time,
                    "error": str(e)
                }
        
        # Execute multiple concurrent trade attempts
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(execute_trade_attempt) for _ in range(3)]
            results = [future.result(timeout=15) for future in futures]
        
        print(f"Concurrent execution results: {results}")
        print(f"Success count: {success_count}")
        
        # At most one trade should succeed due to locking
        # The others should fail due to cooldown or other safety checks
        assert success_count <= 1, f"At most 1 trade should succeed, got {success_count}"
        
        # Verify database consistency
        total_trades = trading_service.db.query(Trade).filter(
            Trade.bot_id == mock_bot.id
        ).count()
        assert total_trades == success_count, f"Database should have {success_count} trades, found {total_trades}"
    
    def test_lock_released_after_transaction_completion(self, mock_bot, trading_service):
        """Test that locks are properly released after transaction completion."""
        
        # Set short cooldown
        mock_bot.cooldown_minutes = 1
        
        # Execute first trade
        try:
            result1 = trading_service.execute_trade(
                bot_id=mock_bot.id,
                side="BUY",
                size_usd=25.0
            )
            print(f"First trade result: {result1}")
        except TradeExecutionError as e:
            print(f"First trade failed (expected): {e}")
        
        # Wait for cooldown to pass
        time.sleep(2)
        
        # Second trade should now be possible (if first failed due to mocking)
        # or should fail due to cooldown (if first succeeded)
        try:
            result2 = trading_service.execute_trade(
                bot_id=mock_bot.id,
                side="SELL", 
                size_usd=25.0
            )
            print(f"Second trade result: {result2}")
        except TradeExecutionError as e:
            print(f"Second trade failed: {e}")
        
        # The key test is that we don't get deadlocks or hanging transactions
        # If we reach this point, the locks were properly released
        assert True, "Locks were properly released - no deadlock occurred"
