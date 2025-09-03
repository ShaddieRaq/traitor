"""
Phase 4.1.2 Integration Tests: Trade Execution Service
Comprehensive testing of real trade execution with safety integration.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.services.trading_service import TradingService, TradeExecutionError
from app.models.models import Bot, Trade


class TestTradingServiceCore:
    """Test core trading service functionality."""
    
    def test_trading_service_initialization(self, db_session):
        """Test trading service initializes correctly."""
        service = TradingService(db_session)
        
        assert service.db == db_session
        assert service.coinbase_service is not None
        assert service.safety_service is not None
        assert service.bot_evaluator is not None
    
    def test_get_bot_valid(self, db_session, sample_bot):
        """Test getting a valid running bot."""
        service = TradingService(db_session)
        
        bot = service._get_bot(sample_bot.id)
        assert bot.id == sample_bot.id
        assert bot.name == sample_bot.name
    
    def test_get_bot_not_found(self, db_session):
        """Test error when bot doesn't exist."""
        service = TradingService(db_session)
        
        with pytest.raises(TradeExecutionError, match="Bot 999 not found"):
            service._get_bot(999)
    
    def test_get_bot_not_running(self, db_session, sample_bot):
        """Test error when bot is not running."""
        sample_bot.status = "STOPPED"
        db_session.commit()
        
        service = TradingService(db_session)
        
        with pytest.raises(TradeExecutionError, match="is not running"):
            service._get_bot(sample_bot.id)


class TestTradeExecution:
    """Test complete trade execution pipeline."""
    
    @patch('app.services.trading_service.TradingService._place_order')
    @patch('app.services.trading_service.TradingService._get_current_price')
    def test_successful_buy_trade(self, mock_price, mock_order, db_session, sample_bot):
        """Test successful buy trade execution."""
        # Setup mocks
        mock_price.return_value = 50000.0
        mock_order.return_value = {
            "order_id": "test-order-123",
            "status": "pending",
            "side": "buy"
        }
        
        service = TradingService(db_session)
        
        result = service.execute_trade(
            bot_id=sample_bot.id,
            side="buy",
            size_usd=10.0,
            current_temperature="HOT"
        )
        
        # Verify successful result
        assert result["success"] is True
        assert "trade_id" in result
        assert result["order_id"] == "test-order-123"
        assert result["execution"]["side"] == "buy"
        assert result["execution"]["size_usd"] == 10.0
        assert result["execution"]["temperature"] == "HOT"
        
        # Verify trade was recorded
        trade = db_session.query(Trade).filter(Trade.order_id == "test-order-123").first()
        assert trade is not None
        assert trade.bot_id == sample_bot.id
        assert trade.side == "buy"
        assert trade.size == 10.0
    
    @patch('app.services.trading_service.TradingService._place_order')
    @patch('app.services.trading_service.TradingService._get_current_price')
    def test_successful_sell_trade(self, mock_price, mock_order, db_session, sample_bot):
        """Test successful sell trade execution."""
        # Setup mocks
        mock_price.return_value = 50000.0
        mock_order.return_value = {
            "order_id": "test-sell-456", 
            "status": "pending",
            "side": "sell"
        }
        
        # Set bot position to enable selling
        sample_bot.current_position_size = 25.0
        db_session.commit()
        
        service = TradingService(db_session)
        
        result = service.execute_trade(
            bot_id=sample_bot.id,
            side="sell",
            size_usd=15.0,
            current_temperature="WARM"
        )
        
        # Verify successful result
        assert result["success"] is True
        assert result["execution"]["side"] == "sell"
        assert result["execution"]["size_usd"] == 15.0
        
        # Verify position was updated
        db_session.refresh(sample_bot)
        assert sample_bot.current_position_size == 10.0  # 25.0 - 15.0
    
    def test_trade_execution_safety_rejection(self, db_session, sample_bot):
        """Test trade rejected by safety system."""
        service = TradingService(db_session)
        
        # Try to execute oversized trade (over $25 limit)
        result = service.execute_trade(
            bot_id=sample_bot.id,
            side="buy",
            size_usd=50.0,  # Over safety limit
            current_temperature="HOT"
        )
        
        # Verify rejection
        assert result["success"] is False
        assert "safety" in result["error"].lower()
        assert result["error_type"] == "trade_execution_error"
    
    def test_trade_execution_invalid_bot(self, db_session):
        """Test trade execution with invalid bot ID."""
        service = TradingService(db_session)
        
        result = service.execute_trade(
            bot_id=999,
            side="buy", 
            size_usd=10.0,
            current_temperature="HOT"
        )
        
        # Verify error
        assert result["success"] is False
        assert "Bot 999 not found" in result["error"]
    
    @patch('app.services.trading_service.TradingService._get_current_price')
    def test_trade_execution_price_fetch_error(self, mock_price, db_session, sample_bot):
        """Test handling of price fetch errors."""
        mock_price.side_effect = Exception("Price fetch failed")
        
        service = TradingService(db_session)
        
        result = service.execute_trade(
            bot_id=sample_bot.id,
            side="buy",
            size_usd=10.0,
            current_temperature="HOT"
        )
        
        # Verify error handling
        assert result["success"] is False
        assert "Price fetch failed" in result["error"]


class TestPositionManagement:
    """Test position size calculations and updates."""
    
    def test_calculate_base_size_buy(self, db_session):
        """Test base size calculation for buy orders."""
        service = TradingService(db_session)
        
        # $10 USD at $50,000 per BTC
        base_size = service._calculate_base_size("buy", 10.0, 50000.0)
        
        expected = 10.0 / 50000.0  # 0.0002 BTC
        assert abs(base_size - expected) < 1e-8
    
    def test_calculate_base_size_sell(self, db_session):
        """Test base size calculation for sell orders."""
        service = TradingService(db_session)
        
        # $15 USD at $60,000 per BTC
        base_size = service._calculate_base_size("sell", 15.0, 60000.0)
        
        expected = 15.0 / 60000.0  # 0.00025 BTC
        assert abs(base_size - expected) < 1e-8
    
    def test_update_bot_position_buy(self, db_session, sample_bot):
        """Test position update for buy trades."""
        service = TradingService(db_session)
        
        initial_position = sample_bot.current_position_size
        
        service._update_bot_position(sample_bot, "buy", 20.0)
        
        db_session.refresh(sample_bot)
        assert sample_bot.current_position_size == initial_position + 20.0
    
    def test_update_bot_position_sell(self, db_session, sample_bot):
        """Test position update for sell trades."""
        sample_bot.current_position_size = 30.0
        db_session.commit()
        
        service = TradingService(db_session)
        
        service._update_bot_position(sample_bot, "sell", 10.0)
        
        db_session.refresh(sample_bot)
        assert sample_bot.current_position_size == 20.0
    
    def test_update_bot_position_prevent_negative(self, db_session, sample_bot):
        """Test position doesn't go negative."""
        sample_bot.current_position_size = 5.0
        db_session.commit()
        
        service = TradingService(db_session)
        
        service._update_bot_position(sample_bot, "sell", 10.0)  # Sell more than we have
        
        db_session.refresh(sample_bot)
        assert sample_bot.current_position_size == 0.0  # Should be clamped to 0


class TestTradeStatusTracking:
    """Test trade status and history functionality."""
    
    def test_get_trade_status_valid(self, db_session, sample_trade):
        """Test getting status for valid trade."""
        service = TradingService(db_session)
        
        status = service.get_trade_status(sample_trade.id)
        
        assert status["trade_id"] == sample_trade.id
        assert status["bot_id"] == sample_trade.bot_id
        assert status["order_id"] == sample_trade.order_id
        assert status["side"] == sample_trade.side
        assert status["size"] == sample_trade.size
    
    def test_get_trade_status_not_found(self, db_session):
        """Test getting status for non-existent trade."""
        service = TradingService(db_session)
        
        status = service.get_trade_status(999)
        
        assert "error" in status
        assert "Trade not found" in status["error"]
        assert status["trade_id"] == 999


class TestSignalScoreRecording:
    """Test signal score recording during trades."""
    
    @patch('app.services.trading_service.TradingService._place_order')
    @patch('app.services.trading_service.TradingService._get_current_price')
    def test_signal_scores_recorded(self, mock_price, mock_order, db_session, sample_bot):
        """Test that signal scores are properly recorded."""
        mock_price.return_value = 50000.0
        mock_order.return_value = {
            "order_id": "signal-test-789",
            "status": "pending"
        }
        
        service = TradingService(db_session)
        
        result = service.execute_trade(
            bot_id=sample_bot.id,
            side="buy",
            size_usd=10.0,
            current_temperature="HOT"
        )
        
        # Get the recorded trade
        trade = db_session.query(Trade).filter(Trade.order_id == "signal-test-789").first()
        assert trade is not None
        
        # Verify signal scores were recorded
        assert trade.signal_scores is not None
        signal_data = json.loads(trade.signal_scores)
        assert "recorded_at" in signal_data
        assert "combined_score" in signal_data
        assert signal_data["combined_score"] == sample_bot.current_combined_score


# Test fixtures for trading service
@pytest.fixture
def sample_bot(db_session):
    """Create a sample bot for testing."""
    from app.models.models import Bot
    
    bot = Bot(
        name="Test Trading Bot",
        pair="BTC-USD",
        signal_config='{"RSI": {"weight": 0.4, "period": 14, "oversold": 30, "overbought": 70, "enabled": true}, "MA": {"weight": 0.3, "short_period": 10, "long_period": 20, "enabled": true}, "MACD": {"weight": 0.3, "fast": 12, "slow": 26, "signal": 9, "enabled": true}}',
        status="RUNNING",
        current_combined_score=0.5,
        current_position_size=0.0
    )
    
    db_session.add(bot)
    db_session.commit()
    db_session.refresh(bot)
    
    yield bot
    
    # Cleanup
    try:
        db_session.delete(bot)
        db_session.commit()
    except:
        db_session.rollback()


@pytest.fixture
def sample_trade(db_session, sample_bot):
    """Create a sample trade for testing."""
    from app.models.models import Trade
    
    trade = Trade(
        bot_id=sample_bot.id,
        product_id=sample_bot.pair,
        side="buy",
        size=10.0,
        price=50000.0,
        order_id="test-order-fixture",
        status="filled",
        combined_signal_score=0.5,
        signal_scores='{"test": "data"}',
        created_at=datetime.utcnow()
    )
    
    db_session.add(trade)
    db_session.commit()
    db_session.refresh(trade)
    
    yield trade
    
    # Cleanup
    try:
        db_session.delete(trade)
        db_session.commit()
    except:
        db_session.rollback()
