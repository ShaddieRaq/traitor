"""
Test Phase 4.1.3 Day 2: Enhanced Tranche Management Algorithms

Comprehensive tests for advanced position management features including:
- Dollar-cost averaging optimization
- Partial exit strategies
- Position scaling recommendations
- Performance analysis
"""

import pytest
import json
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import datetime

from app.main import app
from app.core.database import SessionLocal
from app.models.models import Bot, Trade
from app.services.position_service import PositionService, TrancheStrategy


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db():
    """Database session fixture."""
    return SessionLocal()


@pytest.fixture
def test_bot_with_position(db):
    """Create a test bot with multiple tranches for testing."""
    # Create bot
    bot = Bot(
        name="Phase 4.1.3 Test Bot",
        description="Bot for testing advanced tranche management",
        pair="BTC-USD",
        status="RUNNING",
        position_size_usd=300.0,
        signal_config=json.dumps({
            "rsi": {"enabled": True, "weight": 1.0}
        })
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    
    # Create multiple tranches
    tranches = [
        Trade(
            bot_id=bot.id,
            product_id="BTC-USD",
            side="buy",
            size=0.002,
            price=50000.0,
            size_usd=100.0,
            status="filled",
            position_status="BUILDING",
            tranche_number=1,
            order_id="test-order-1"
        ),
        Trade(
            bot_id=bot.id,
            product_id="BTC-USD",
            side="buy",
            size=0.003,
            price=48000.0,
            size_usd=144.0,
            status="filled",
            position_status="OPEN",
            tranche_number=2,
            order_id="test-order-2"
        )
    ]
    
    for trade in tranches:
        db.add(trade)
    
    db.commit()
    
    yield bot
    
    # Cleanup
    db.delete(bot)
    for trade in tranches:
        db.delete(trade)
    db.commit()


class TestAdvancedTrancheManagement:
    """Test advanced tranche management algorithms."""
    
    def test_calculate_optimal_tranche_size_equal_strategy(self, db, test_bot_with_position):
        """Test equal size tranche strategy."""
        position_service = PositionService(db)
        
        optimal_size, reasoning = position_service.calculate_optimal_tranche_size(
            test_bot_with_position.id,
            current_price=49000.0,
            strategy=TrancheStrategy.EQUAL_SIZE
        )
        
        # Should be base position size / max tranches
        expected_size = test_bot_with_position.position_size_usd / position_service.MAX_TRANCHES_PER_POSITION
        assert optimal_size == expected_size
        assert "Equal size strategy" in reasoning
    
    def test_calculate_optimal_tranche_size_pyramid_up(self, db, test_bot_with_position):
        """Test pyramid up strategy (increasing size)."""
        position_service = PositionService(db)
        
        optimal_size, reasoning = position_service.calculate_optimal_tranche_size(
            test_bot_with_position.id,
            current_price=49000.0,
            strategy=TrancheStrategy.PYRAMID_UP
        )
        
        assert optimal_size > 0
        assert "Pyramid up strategy" in reasoning
        assert "tranche 3" in reasoning  # Should be adding 3rd tranche
    
    def test_calculate_optimal_tranche_size_adaptive(self, db, test_bot_with_position):
        """Test adaptive strategy based on position performance."""
        position_service = PositionService(db)
        
        # Test with profitable position (current price > average entry)
        optimal_size, reasoning = position_service.calculate_optimal_tranche_size(
            test_bot_with_position.id,
            current_price=52000.0,  # Higher than average entry
            strategy=TrancheStrategy.ADAPTIVE
        )
        
        assert optimal_size > 0
        assert "Adaptive strategy" in reasoning
        
        # Test with losing position (current price < average entry)
        optimal_size_loss, reasoning_loss = position_service.calculate_optimal_tranche_size(
            test_bot_with_position.id,
            current_price=45000.0,  # Lower than average entry
            strategy=TrancheStrategy.ADAPTIVE
        )
        
        assert optimal_size_loss > 0
        assert "decline" in reasoning_loss
    
    def test_dollar_cost_average_metrics(self, db, test_bot_with_position):
        """Test DCA impact calculation."""
        position_service = PositionService(db)
        
        # Calculate DCA metrics for adding new tranche at lower price
        metrics = position_service.calculate_dollar_cost_average_metrics(
            test_bot_with_position.id,
            new_price=46000.0,  # Lower than current average
            new_size_usd=100.0
        )
        
        assert "current_average_price" in metrics
        assert "new_average_price" in metrics
        assert "price_improvement" in metrics
        assert "position_size_increase" in metrics
        
        # New average should be lower than current (price improvement)
        assert metrics["new_average_price"] < metrics["current_average_price"]
        assert metrics["price_improvement"] > 0  # Positive improvement


class TestPartialExitStrategies:
    """Test partial exit functionality."""
    
    def test_calculate_partial_exit_strategy(self, db, test_bot_with_position):
        """Test partial exit strategy calculation."""
        position_service = PositionService(db)
        
        # Test 50% exit strategy
        exit_strategy = position_service.calculate_partial_exit_strategy(
            test_bot_with_position.id,
            exit_percentage=0.5,
            current_price=51000.0
        )
        
        assert exit_strategy["exit_strategy"] == "FIFO"
        assert exit_strategy["exit_percentage"] == 50.0
        assert "exit_plan" in exit_strategy
        assert "remaining_position" in exit_strategy
        
        # Should have exit plan with tranches
        assert len(exit_strategy["exit_plan"]) > 0
        
        # Check exit plan structure
        for plan_item in exit_strategy["exit_plan"]:
            assert "tranche_id" in plan_item
            assert "exit_size_usd" in plan_item
            assert "entry_price" in plan_item
            assert "exit_price" in plan_item
            assert "tranche_pnl" in plan_item
    
    def test_partial_exit_no_position(self, db):
        """Test partial exit when no position exists."""
        # Create bot without trades
        bot = Bot(
            name="Empty Bot",
            description="Bot with no position",
            pair="BTC-USD",
            position_size_usd=100.0,
            signal_config=json.dumps({})
        )
        db.add(bot)
        db.commit()
        
        position_service = PositionService(db)
        exit_strategy = position_service.calculate_partial_exit_strategy(
            bot.id,
            exit_percentage=0.5,
            current_price=50000.0
        )
        
        assert "error" in exit_strategy
        assert "No position to exit" in exit_strategy["error"]
        
        # Cleanup
        db.delete(bot)
        db.commit()


class TestPositionScaling:
    """Test position scaling optimization."""
    
    def test_optimize_position_scaling_strong_buy(self, db, test_bot_with_position):
        """Test scaling recommendations for strong buy signal."""
        position_service = PositionService(db)
        
        recommendations = position_service.optimize_position_scaling(
            test_bot_with_position.id,
            market_signal_strength=0.8  # Strong buy
        )
        
        assert recommendations["action"] == "add_tranche"
        assert recommendations["confidence"] > 0.7
        assert "Strong buy signal" in recommendations["reasoning"]
        assert recommendations["risk_level"] in ["low", "medium"]
        assert "suggested_size_usd" in recommendations
    
    def test_optimize_position_scaling_strong_sell(self, db, test_bot_with_position):
        """Test scaling recommendations for strong sell signal."""
        position_service = PositionService(db)
        
        recommendations = position_service.optimize_position_scaling(
            test_bot_with_position.id,
            market_signal_strength=-0.8  # Strong sell
        )
        
        assert recommendations["action"] == "partial_exit"
        assert recommendations["confidence"] > 0.7
        assert "Strong sell signal" in recommendations["reasoning"]
        assert recommendations["risk_level"] == "high"
        assert "suggested_exit_percentage" in recommendations
    
    def test_optimize_position_scaling_neutral(self, db, test_bot_with_position):
        """Test scaling recommendations for neutral signal."""
        position_service = PositionService(db)
        
        recommendations = position_service.optimize_position_scaling(
            test_bot_with_position.id,
            market_signal_strength=0.2  # Weak signal
        )
        
        assert recommendations["action"] == "hold"
        assert "Weak signal" in recommendations["reasoning"]
        assert recommendations["risk_level"] == "medium"


class TestPerformanceAnalysis:
    """Test position performance analysis."""
    
    def test_analyze_position_performance(self, db, test_bot_with_position):
        """Test comprehensive position performance analysis."""
        position_service = PositionService(db)
        
        analysis = position_service.analyze_position_performance(
            test_bot_with_position.id,
            current_price=51000.0
        )
        
        # Check main sections
        assert "position_summary" in analysis
        assert "tranche_analysis" in analysis
        assert "performance_metrics" in analysis
        assert "recommendations" in analysis
        
        # Check position summary
        summary = analysis["position_summary"]
        assert "total_return_pct" in summary
        assert "total_return_usd" in summary
        assert "average_entry_price" in summary
        assert "total_tranches" in summary
        
        # Check performance metrics
        metrics = analysis["performance_metrics"]
        assert "best_tranche" in metrics
        assert "worst_tranche" in metrics
        assert "efficiency_score" in metrics
        assert "performance_grade" in metrics
        
        # Check recommendations
        recommendations = analysis["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_performance_analysis_no_position(self, db):
        """Test performance analysis with no position."""
        # Create bot without trades
        bot = Bot(
            name="Empty Bot Performance",
            description="Bot with no position for performance test",
            pair="BTC-USD",
            position_size_usd=100.0,
            signal_config=json.dumps({})
        )
        db.add(bot)
        db.commit()
        
        position_service = PositionService(db)
        analysis = position_service.analyze_position_performance(
            bot.id,
            current_price=50000.0
        )
        
        assert "error" in analysis
        assert "No position to analyze" in analysis["error"]
        
        # Cleanup
        db.delete(bot)
        db.commit()


class TestAPIEndpoints:
    """Test Phase 4.1.3 Day 2 API endpoints."""
    
    def test_calculate_tranche_size_endpoint(self, client, test_bot_with_position):
        """Test optimal tranche size calculation endpoint."""
        response = client.post(
            f"/api/v1/trades/position/{test_bot_with_position.id}/calculate-tranche-size",
            json={
                "current_price": 49000.0,
                "strategy": "adaptive",
                "market_conditions": {
                    "volatility": 0.25,
                    "trend": "bullish"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["bot_id"] == test_bot_with_position.id
        assert data["current_price"] == 49000.0
        assert data["strategy"] == "adaptive"
        assert "optimal_size_usd" in data
        assert "reasoning" in data
    
    def test_dca_impact_analysis_endpoint(self, client, test_bot_with_position):
        """Test DCA impact analysis endpoint."""
        response = client.post(
            f"/api/v1/trades/position/{test_bot_with_position.id}/analyze-dca-impact",
            json={
                "new_price": 47000.0,
                "new_size_usd": 120.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["bot_id"] == test_bot_with_position.id
        assert "impact_analysis" in data
        
        impact = data["impact_analysis"]
        assert "current_average_price" in impact
        assert "new_average_price" in impact
        assert "price_improvement" in impact
    
    def test_partial_exit_strategy_endpoint(self, client, test_bot_with_position):
        """Test partial exit strategy endpoint."""
        response = client.post(
            f"/api/v1/trades/position/{test_bot_with_position.id}/partial-exit-strategy",
            json={
                "exit_percentage": 0.4,
                "current_price": 52000.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["bot_id"] == test_bot_with_position.id
        assert "exit_strategy" in data
        
        strategy = data["exit_strategy"]
        assert strategy["exit_percentage"] == 40.0
        assert "exit_plan" in strategy
    
    def test_position_scaling_endpoint(self, client, test_bot_with_position):
        """Test position scaling optimization endpoint."""
        response = client.post(
            f"/api/v1/trades/position/{test_bot_with_position.id}/optimize-scaling",
            json={
                "market_signal_strength": 0.75
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["bot_id"] == test_bot_with_position.id
        assert data["signal_strength"] == 0.75
        assert "recommendations" in data
        
        recommendations = data["recommendations"]
        assert "action" in recommendations
        assert "confidence" in recommendations
        assert "reasoning" in recommendations
    
    def test_performance_analysis_endpoint(self, client, test_bot_with_position):
        """Test position performance analysis endpoint."""
        response = client.get(
            f"/api/v1/trades/position/{test_bot_with_position.id}/performance-analysis",
            params={"current_price": 51500.0}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["bot_id"] == test_bot_with_position.id
        assert data["bot_name"] == test_bot_with_position.name
        assert "analysis" in data
        
        analysis = data["analysis"]
        assert "position_summary" in analysis
        assert "performance_metrics" in analysis
        assert "recommendations" in analysis
    
    def test_invalid_strategy_error(self, client, test_bot_with_position):
        """Test error handling for invalid tranche strategy."""
        response = client.post(
            f"/api/v1/trades/position/{test_bot_with_position.id}/calculate-tranche-size",
            json={
                "current_price": 49000.0,
                "strategy": "invalid_strategy"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid strategy" in response.json()["detail"]
    
    def test_invalid_exit_percentage_error(self, client, test_bot_with_position):
        """Test error handling for invalid exit percentage."""
        response = client.post(
            f"/api/v1/trades/position/{test_bot_with_position.id}/partial-exit-strategy",
            json={
                "exit_percentage": 1.5,  # > 1.0
                "current_price": 50000.0
            }
        )
        
        assert response.status_code == 400
        assert "exit_percentage must be between 0 and 1" in response.json()["detail"]


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_max_tranches_reached(self, db):
        """Test behavior when maximum tranches are reached."""
        # Create bot with maximum tranches
        bot = Bot(
            name="Max Tranches Bot",
            description="Bot at max tranche capacity",
            pair="BTC-USD",
            position_size_usd=300.0,
            signal_config=json.dumps({})
        )
        db.add(bot)
        db.commit()
        
        # Add maximum number of tranches
        position_service = PositionService(db)
        for i in range(position_service.MAX_TRANCHES_PER_POSITION):
            trade = Trade(
                bot_id=bot.id,
                product_id="BTC-USD",
                side="buy",
                size=0.002,
                price=50000.0 - (i * 1000),  # Decreasing prices
                size_usd=100.0,
                status="filled",
                position_status="OPEN",
                tranche_number=i + 1,
                order_id=f"test-order-{i}"
            )
            db.add(trade)
        
        db.commit()
        
        # Test that no more tranches can be added
        can_add, reason = position_service.can_add_tranche(bot.id)
        assert not can_add
        assert "Maximum tranches" in reason
        
        # Cleanup
        db.query(Trade).filter(Trade.bot_id == bot.id).delete()
        db.delete(bot)
        db.commit()
    
    def test_single_tranche_analysis(self, db):
        """Test analysis with only one tranche."""
        # Create bot with single tranche
        bot = Bot(
            name="Single Tranche Bot",
            description="Bot with one tranche",
            pair="BTC-USD",
            position_size_usd=100.0,
            signal_config=json.dumps({})
        )
        db.add(bot)
        db.commit()
        
        trade = Trade(
            bot_id=bot.id,
            product_id="BTC-USD",
            side="buy",
            size=0.002,
            price=50000.0,
            size_usd=100.0,
            status="filled",
            position_status="BUILDING",
            tranche_number=1,
            order_id="single-tranche"
        )
        db.add(trade)
        db.commit()
        
        position_service = PositionService(db)
        
        # Test performance analysis with single tranche
        analysis = position_service.analyze_position_performance(bot.id, 52000.0)
        assert "position_summary" in analysis
        assert analysis["position_summary"]["total_tranches"] == 1
        
        # Cleanup
        db.delete(trade)
        db.delete(bot)
        db.commit()
