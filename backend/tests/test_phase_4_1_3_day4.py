"""
PHASE 4.1.3 DAY 4: API ENHANCEMENT & TESTING COMPREHENSIVE TEST SUITE 🚀
============================================================================

Test suite for Phase 4.1.3 Day 4 enhanced API responses, performance monitoring,
and comprehensive analytics integration.

Created: Day 4 Phase 4.1.3
Purpose: Validate enhanced API endpoints with advanced analytics and monitoring
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from sqlalchemy.orm import Session

from app.main import app
from app.models.models import Bot, Trade
from app.services.trading_service import TradingService
from app.services.position_service import PositionService
from app.core.database import get_db


# =================================================================================
# PHASE 4.1.3 DAY 4: ENHANCED API TESTING FIXTURES
# =================================================================================

@pytest.fixture
def test_client(db_session):
    """Create a test client with test database session."""
    from app.core.database import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_services():
    """Mock all external services for Day 4 testing."""
    mocks = {}
    
    # Mock TradingService
    mock_trading_service = Mock()
    mock_trading_service.execute_trade.return_value = {
        "success": True,
        "trade_id": 123,
        "order_id": "test-order-123",
        "status": "pending",
        "message": "Trade executed successfully",
        "signal_strength": 0.75,
        "details": {
            "bot_id": 1,
            "side": "BUY",
            "size_usd": 75.0,
            "price": 2000.0
        }
    }
    mocks['trading_service'] = mock_trading_service
    
    # Mock PositionService
    mock_position_service = Mock()
    mock_position_service.get_position_summary.return_value = {
        "total_size_usd": 150.0,
        "total_size_crypto": 0.075,
        "average_entry_price": 1983.33,
        "current_unrealized_pnl": 5.25,
        "current_unrealized_pnl_pct": 3.5,
        "total_tranches": 2,
        "total_return_pct": 3.5
    }
    
    mock_position_service.analyze_position_performance.return_value = {
        "total_return_pct": 3.5,
        "sharpe_ratio": 1.2,
        "max_drawdown_pct": 2.1,
        "win_rate": 0.67,
        "performance_grade": "B+",
        "efficiency_score": 0.78
    }
    
    mock_position_service.optimize_position_scaling.return_value = {
        "action": "HOLD",
        "confidence": 0.75,
        "suggested_size_usd": 100.0
    }
    mocks['position_service'] = mock_position_service
    
    return mocks


@pytest.fixture
def test_bot_with_position(db_session):
    """Create a test bot with an existing position for Day 4 testing."""
    bot = Bot(
        name="Day 4 Test Bot",
        pair="ETH-USD", 
        status="RUNNING",
        position_size_usd=100.0,
        max_positions=3,
        stop_loss_pct=5.0,
        take_profit_pct=15.0,
        trade_step_pct=3.0,
        cooldown_minutes=10,
        signal_config=json.dumps({
            "RSI": {"enabled": True, "weight": 0.4, "period": 14, "oversold": 30, "overbought": 70},
            "MACD": {"enabled": True, "weight": 0.3, "fast": 12, "slow": 26, "signal": 9},
            "BB": {"enabled": True, "weight": 0.3, "period": 20, "std_dev": 2}
        })
    )
    
    # Add to database session and commit
    db_session.add(bot)
    db_session.commit()
    db_session.refresh(bot)

    # Create some sample trades to establish a position
    trades = [
        Trade(
            bot_id=bot.id,
            product_id="ETH-USD",
            side="buy",
            size=0.5,
            price=2000.0,
            status="filled",
            filled_at=datetime.utcnow() - timedelta(hours=2),
            size_usd=100.0,
            position_tranches=json.dumps({
                "tranches": [{"id": 1, "entry_price": 2000.0, "size_usd": 100.0, "timestamp": datetime.utcnow().isoformat()}]
            }),
            average_entry_price=2000.0,
            tranche_number=1,
            position_status="open"
        ),
        Trade(
            bot_id=bot.id,
            product_id="ETH-USD",
            side="buy", 
            size=0.25,
            price=1950.0,
            status="filled",
            filled_at=datetime.utcnow() - timedelta(hours=1),
            size_usd=50.0,
            position_tranches=json.dumps({
                "tranches": [
                    {"id": 1, "entry_price": 2000.0, "size_usd": 100.0, "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()},
                    {"id": 2, "entry_price": 1950.0, "size_usd": 50.0, "timestamp": datetime.utcnow().isoformat()}
                ]
            }),
            average_entry_price=1983.33,
            tranche_number=2,
            position_status="open"
        )
    ]
    
    # Add trades to database
    for trade in trades:
        db_session.add(trade)
    db_session.commit()
    
    return bot
# =================================================================================
# PHASE 4.1.3 DAY 4: ENHANCED API ENDPOINT TESTS
# =================================================================================

class TestEnhancedTradeExecution:
    """Test enhanced trade execution API with advanced analytics."""
    
    def test_execute_trade_with_analytics(self, test_client, test_bot_with_position, mock_services):
        """Test trade execution with enhanced Day 4 analytics."""
        # Mock the services to bypass database lookup issues
        with patch('app.api.trades.TradingService') as mock_trading_service_class, \
             patch('app.api.trades.PositionService') as mock_position_service_class:
            
            mock_trading_service_class.return_value = mock_services['trading_service']
            mock_position_service_class.return_value = mock_services['position_service']
            
            response = test_client.post("/api/v1/trades/execute", json={
                "bot_id": test_bot_with_position.id,
                "side": "BUY",
                "size_usd": 75.0,
                "current_temperature": "WARM",  # Override FROZEN temperature for testing
                "include_analytics": True
            })
            
            assert response.status_code == 200
            
            # Verify Day 4 enhanced response structure
            result = response.json()
            assert result["success"] is True
            assert "analytics" in result
            assert "position_summary" in result["analytics"]
            assert "performance_metrics" in result["analytics"]  
            assert "recommendations" in result["analytics"]
            assert "execution_timestamp" in result["analytics"]
            
            # Verify position summary has key metrics
            position_summary = result["analytics"]["position_summary"]
            assert "total_tranches" in position_summary
            assert "total_return_pct" in position_summary
            
            # Verify performance metrics
            performance_metrics = result["analytics"]["performance_metrics"]
            assert "performance_grade" in performance_metrics
            assert "efficiency_score" in performance_metrics
    
    def test_execute_trade_with_auto_sizing(self, test_client, test_bot_with_position, mock_services):
        """Test enhanced trade execution with intelligent auto-sizing."""
        with patch('app.api.trades.TradingService') as mock_trading_service_class, \
             patch('app.api.trades.PositionService') as mock_position_service_class:
            
            mock_trading_service_class.return_value = mock_services['trading_service']
            mock_position_service_class.return_value = mock_services['position_service']
            
            response = test_client.post("/api/v1/trades/execute", json={
                "bot_id": test_bot_with_position.id,
                "side": "BUY",
                "auto_size": True,
                "current_temperature": "HOT",
                "include_analytics": True
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have success and analytics
            assert data.get("success") is True
            assert "analytics" in data
            
            # Should include intelligent sizing information
            assert "size_usd" in data["details"] or "intelligent_size" in data
    
    def test_execute_trade_analytics_failure_handling(self, test_client, test_bot_with_position, mock_services):
        """Test that trade execution succeeds even if analytics fail."""
        # Set up the position service to fail for analytics
        mock_services['position_service'].get_position_summary.side_effect = Exception("Analytics service down")
        
        with patch('app.api.trades.TradingService') as mock_trading_service_class, \
             patch('app.api.trades.PositionService') as mock_position_service_class:
            
            mock_trading_service_class.return_value = mock_services['trading_service']
            mock_position_service_class.return_value = mock_services['position_service']
            
            response = test_client.post("/api/v1/trades/execute", json={
                "bot_id": test_bot_with_position.id,
                "side": "BUY",
                "size_usd": 50.0,
                "current_temperature": "WARM",  # Override FROZEN temperature for testing
                "include_analytics": True
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Trade should succeed
            assert data.get("success") is True
            
            # Should have analytics warning instead of failing
            assert "analytics_warning" in data


class TestEnhancedTradeStatus:
    """Test enhanced trade status API with comprehensive analytics."""
    
    def test_get_trade_status_with_analytics(self, test_client, test_bot_with_position, db_session):
        """Test trade status endpoint with enhanced Day 4 analytics."""
        # Get a trade ID
        trade = db_session.query(Trade).filter(Trade.bot_id == test_bot_with_position.id).first()
        assert trade is not None
        
        response = test_client.get(f"/api/v1/trades/status/{trade.id}?include_analytics=true")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify enhanced response structure
        assert "enhanced_analytics" in data
        
        # Verify analytics components
        analytics = data["enhanced_analytics"]
        assert "position_summary" in analytics
        assert "performance_metrics" in analytics
        assert "dca_analysis" in analytics
        assert "query_timestamp" in analytics
    
    def test_get_trade_status_without_analytics(self, test_client, test_bot_with_position, db_session):
        """Test trade status endpoint without analytics for performance."""
        trade = db_session.query(Trade).filter(Trade.bot_id == test_bot_with_position.id).first()
        
        response = test_client.get(f"/api/v1/trades/status/{trade.id}?include_analytics=false")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have basic trade info but no enhanced analytics
        assert "trade_id" in data
        assert "enhanced_analytics" not in data


class TestLivePerformanceMonitoring:
    """Test Phase 4.1.3 Day 4 real-time performance monitoring endpoints."""
    
    def test_live_performance_analytics(self, test_client, test_bot_with_position):
        """Test system-wide live performance analytics endpoint."""
        response = test_client.get("/api/v1/trades/analytics/live-performance")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify system performance structure
        assert "system_performance" in data
        assert "bot_analytics" in data
        assert "market_conditions" in data
        
        # Verify system metrics
        system_perf = data["system_performance"]
        assert "total_active_bots" in system_perf
        assert "total_positions" in system_perf
        assert "performance_distribution" in system_perf
        
        # Verify bot analytics array
        bot_analytics = data["bot_analytics"]
        assert isinstance(bot_analytics, list)
        
        # If bots exist, verify their structure
        if len(bot_analytics) > 0:
            bot_data = bot_analytics[0]
            assert "bot_id" in bot_data
            assert "bot_name" in bot_data
            assert "temperature" in bot_data
    
    def test_bot_dashboard_analytics(self, test_client, test_bot_with_position):
        """Test comprehensive bot dashboard analytics."""
        response = test_client.get(
            f"/api/v1/trades/analytics/bot-dashboard/{test_bot_with_position.id}"
            "?include_recommendations=true&include_projections=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify comprehensive dashboard structure
        assert "bot_info" in data
        assert "position_summary" in data
        assert "performance_metrics" in data
        assert "recommendations" in data
        assert "strategy_projections" in data
        assert "dashboard_timestamp" in data
        
        # Verify bot info
        bot_info = data["bot_info"]
        assert bot_info["id"] == test_bot_with_position.id
        assert "temperature" in bot_info
        
        # Verify strategy projections
        projections = data["strategy_projections"]
        expected_strategies = ["equal_size", "pyramid_up", "pyramid_down", "adaptive"]
        for strategy in expected_strategies:
            assert strategy in projections
    
    def test_bot_dashboard_analytics_minimal(self, test_client, test_bot_with_position):
        """Test bot dashboard with minimal analytics for performance."""
        response = test_client.get(
            f"/api/v1/trades/analytics/bot-dashboard/{test_bot_with_position.id}"
            "?include_recommendations=false&include_projections=false"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have core analytics but not enhanced features
        assert "bot_info" in data
        assert "position_summary" in data
        assert "performance_metrics" in data
        assert "recommendations" not in data
        assert "strategy_projections" not in data


# =================================================================================
# PHASE 4.1.3 DAY 4: PERFORMANCE AND INTEGRATION TESTS
# =================================================================================

class TestAPIPerformance:
    """Test API performance and response times for Day 4 enhancements."""
    
    def test_enhanced_api_response_time(self, test_client, test_bot_with_position):
        """Test that enhanced APIs maintain acceptable response times."""
        import time
        
        start_time = time.time()
        response = test_client.post("/api/v1/trades/execute", json={
            "bot_id": test_bot_with_position.id,
            "side": "BUY",
            "size_usd": 25.0,
            "current_temperature": "WARM",  # Override FROZEN temperature for testing
            "include_analytics": True
        })
        end_time = time.time()
        
        # Should complete within reasonable time (2 seconds for enhanced analytics)
        response_time = end_time - start_time
        assert response_time < 2.0, f"Enhanced API too slow: {response_time:.2f}s"
        assert response.status_code == 200
    
    def test_live_analytics_performance(self, test_client, test_bot_with_position):
        """Test live performance analytics response time."""
        import time
        
        start_time = time.time()
        response = test_client.get("/api/v1/trades/analytics/live-performance")
        end_time = time.time()
        
        # Live analytics should be fast for dashboard use
        response_time = end_time - start_time
        assert response_time < 1.0, f"Live analytics too slow: {response_time:.2f}s"
        assert response.status_code == 200


class TestEnhancedAPIIntegration:
    """Test integration between Day 4 enhanced APIs and existing services."""
    
    def test_end_to_end_enhanced_trading_workflow(self, test_client, test_bot_with_position, db_session):
        """Test complete enhanced trading workflow from execution to monitoring."""
        
        # Step 1: Execute trade with analytics
        execute_response = test_client.post("/api/v1/trades/execute", json={
            "bot_id": test_bot_with_position.id,
            "side": "BUY",
            "size_usd": 20.0,  # Use fixed size within safety limits instead of auto_size
            "current_temperature": "WARM",  # Override FROZEN temperature for testing
            "include_analytics": True
        })
        
        assert execute_response.status_code == 200
        execute_data = execute_response.json()
        assert execute_data.get("success") is True
        assert "analytics" in execute_data
        
        # Step 2: Check enhanced trade status
        if "trade_id" in execute_data:
            status_response = test_client.get(
                f"/api/v1/trades/status/{execute_data['trade_id']}?include_analytics=true"
            )
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert "enhanced_analytics" in status_data
        
        # Step 3: Check live performance monitoring
        performance_response = test_client.get("/api/v1/trades/analytics/live-performance")
        assert performance_response.status_code == 200
        performance_data = performance_response.json()
        assert "system_performance" in performance_data
        
        # Step 4: Check bot dashboard
        dashboard_response = test_client.get(
            f"/api/v1/trades/analytics/bot-dashboard/{test_bot_with_position.id}"
        )
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        assert "bot_info" in dashboard_data
    
    def test_enhanced_api_error_handling(self, test_client):
        """Test enhanced API error handling and graceful degradation."""
        
        # Test with non-existent bot
        response = test_client.post("/api/v1/trades/execute", json={
            "bot_id": 99999,
            "side": "BUY",
            "size_usd": 50.0
        })
        assert response.status_code == 404
        
        # Test invalid parameters
        response = test_client.post("/api/v1/trades/execute", json={
            "bot_id": 1,
            "side": "INVALID",
            "size_usd": -50.0
        })
        assert response.status_code == 400
        
        # Test analytics endpoints with invalid bot
        response = test_client.get("/api/v1/trades/analytics/bot-dashboard/99999")
        assert response.status_code == 404


# =================================================================================
# PHASE 4.1.3 DAY 4: INTEGRATION TESTS
# =================================================================================

def test_integration_day4_complete_analytics_pipeline(test_client, test_bot_with_position, db_session):
    """
    Integration test for complete Day 4 analytics pipeline.
    Tests the full flow of enhanced APIs working together.
    """
    # Test the complete enhanced analytics pipeline
    
    # 1. Get baseline live performance
    baseline_response = test_client.get("/api/v1/trades/analytics/live-performance")
    assert baseline_response.status_code == 200
    baseline_data = baseline_response.json()
    
    # 2. Execute enhanced trade
    trade_response = test_client.post("/api/v1/trades/execute", json={
        "bot_id": test_bot_with_position.id,
        "side": "BUY",
        "size_usd": 20.0,  # Use fixed size within safety limits instead of auto_size
        "current_temperature": "WARM",  # Override FROZEN temperature for testing
        "include_analytics": True
    })
    assert trade_response.status_code == 200
    trade_data = trade_response.json()
    
    # 3. Verify analytics were included
    assert "analytics" in trade_data
    assert "position_summary" in trade_data["analytics"]
    
    # 4. Check updated live performance
    updated_response = test_client.get("/api/v1/trades/analytics/live-performance")
    assert updated_response.status_code == 200
    updated_data = updated_response.json()
    
    # 5. Verify comprehensive dashboard reflects changes
    dashboard_response = test_client.get(
        f"/api/v1/trades/analytics/bot-dashboard/{test_bot_with_position.id}"
        "?include_recommendations=true&include_projections=true"
    )
    assert dashboard_response.status_code == 200
    dashboard_data = dashboard_response.json()
    
    # Verify comprehensive analytics structure
    assert "strategy_projections" in dashboard_data
    assert len(dashboard_data["strategy_projections"]) == 4  # All 4 strategies


def test_integration_day4_analytics_consistency(test_client, test_bot_with_position):
    """
    Test that Day 4 analytics are consistent across different endpoints.
    """
    # Get analytics from different endpoints for the same bot
    
    # 1. Dashboard analytics
    dashboard_response = test_client.get(
        f"/api/v1/trades/analytics/bot-dashboard/{test_bot_with_position.id}"
    )
    assert dashboard_response.status_code == 200
    dashboard_data = dashboard_response.json()
    
    # 2. Live performance analytics
    live_response = test_client.get("/api/v1/trades/analytics/live-performance")
    assert live_response.status_code == 200
    live_data = live_response.json()
    
    # Find the bot in live data
    bot_live_data = None
    for bot_data in live_data["bot_analytics"]:
        if bot_data.get("bot_id") == test_bot_with_position.id:
            bot_live_data = bot_data
            break
    
    # Verify consistency between endpoints
    if bot_live_data:
        assert dashboard_data["bot_info"]["id"] == bot_live_data["bot_id"]
        assert dashboard_data["bot_info"]["name"] == bot_live_data["bot_name"]
        assert dashboard_data["bot_info"]["temperature"] == bot_live_data["temperature"]
