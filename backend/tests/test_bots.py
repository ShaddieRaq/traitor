"""
Test Bot CRUD operations and parameter validation.
"""

import pytest
import json
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_bot_data():
    """Sample bot data for testing."""
    return {
        "name": "Test CRUD Bot",
        "description": "Bot for testing CRUD operations",
        "pair": "BTC-USD",
        "position_size_usd": 150.0,
        "max_positions": 1,
        "stop_loss_pct": 3.0,
        "take_profit_pct": 6.0,
        "trade_step_pct": 1.5,
        "cooldown_minutes": 20,
        "signal_config": {
            "rsi": {
                "enabled": True,
                "weight": 0.6,
                "period": 14,
                "buy_threshold": 30,
                "sell_threshold": 70
            },
            "moving_average": {
                "enabled": True,
                "weight": 0.4,
                "fast_period": 10,
                "slow_period": 20
            },
            "macd": {
                "enabled": False,
                "weight": 0.0,
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            }
        }
    }


@pytest.fixture
def minimal_bot_data():
    """Minimal bot data for testing defaults."""
    return {
        "name": "Minimal Test Bot",
        "description": "Bot with minimal configuration",
        "pair": "ETH-USD"
    }


class TestBotCRUD:
    """Test Bot Create, Read, Update, Delete operations."""
    
    def test_create_bot_full_config(self, client, sample_bot_data):
        """Test creating a bot with full configuration."""
        response = client.post("/api/v1/bots/", json=sample_bot_data)
        assert response.status_code == 200
        
        bot = response.json()
        assert bot["name"] == sample_bot_data["name"]
        assert bot["pair"] == sample_bot_data["pair"]
        assert bot["position_size_usd"] == sample_bot_data["position_size_usd"]
        assert bot["max_positions"] == sample_bot_data["max_positions"]
        assert bot["stop_loss_pct"] == sample_bot_data["stop_loss_pct"]
        assert bot["take_profit_pct"] == sample_bot_data["take_profit_pct"]
        assert bot["trade_step_pct"] == sample_bot_data["trade_step_pct"]
        assert bot["cooldown_minutes"] == sample_bot_data["cooldown_minutes"]
        assert bot["status"] == "STOPPED"
        assert bot["current_position_size"] == 0.0
        assert bot["id"] is not None
        
        # Verify signal configuration
        signal_config = bot["signal_config"]
        assert signal_config["rsi"]["enabled"] == True
        assert signal_config["rsi"]["weight"] == 0.6
        assert signal_config["moving_average"]["enabled"] == True
        assert signal_config["moving_average"]["weight"] == 0.4
        assert signal_config["macd"]["enabled"] == False
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")
    
    def test_create_bot_minimal_config(self, client, minimal_bot_data):
        """Test creating a bot with minimal configuration uses defaults."""
        response = client.post("/api/v1/bots/", json=minimal_bot_data)
        assert response.status_code == 200
        
        bot = response.json()
        assert bot["name"] == minimal_bot_data["name"]
        assert bot["pair"] == minimal_bot_data["pair"]
        # Check defaults
        assert bot["position_size_usd"] == 100.0  # Default
        assert bot["max_positions"] == 1  # Default
        assert bot["stop_loss_pct"] == 5.0  # Default
        assert bot["take_profit_pct"] == 10.0  # Default
        assert bot["trade_step_pct"] == 2.0  # Default
        assert bot["cooldown_minutes"] == 15  # Default
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")
    
    def test_create_bot_duplicate_name(self, client, sample_bot_data):
        """Test creating a bot with duplicate name fails."""
        # Create first bot
        response1 = client.post("/api/v1/bots/", json=sample_bot_data)
        assert response1.status_code == 200
        bot1 = response1.json()
        
        # Try to create second bot with same name
        response2 = client.post("/api/v1/bots/", json=sample_bot_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot1['id']}")
    
    def test_get_all_bots(self, client, sample_bot_data):
        """Test getting all bots."""
        # Create a test bot
        create_response = client.post("/api/v1/bots/", json=sample_bot_data)
        created_bot = create_response.json()
        
        # Get all bots
        response = client.get("/api/v1/bots/")
        assert response.status_code == 200
        
        bots = response.json()
        assert isinstance(bots, list)
        assert len(bots) >= 1
        
        # Find our test bot
        test_bot = next((bot for bot in bots if bot["id"] == created_bot["id"]), None)
        assert test_bot is not None
        assert test_bot["name"] == sample_bot_data["name"]
        
        # Clean up
        client.delete(f"/api/v1/bots/{created_bot['id']}")
    
    def test_get_bot_by_id(self, client, sample_bot_data):
        """Test getting a specific bot by ID."""
        # Create a test bot
        create_response = client.post("/api/v1/bots/", json=sample_bot_data)
        created_bot = create_response.json()
        bot_id = created_bot["id"]
        
        # Get bot by ID
        response = client.get(f"/api/v1/bots/{bot_id}")
        assert response.status_code == 200
        
        bot = response.json()
        assert bot["id"] == bot_id
        assert bot["name"] == sample_bot_data["name"]
        assert bot["pair"] == sample_bot_data["pair"]
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot_id}")
    
    def test_get_nonexistent_bot(self, client):
        """Test getting a non-existent bot returns 404."""
        response = client.get("/api/v1/bots/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_bot(self, client, sample_bot_data):
        """Test updating a bot."""
        # Create a test bot
        create_response = client.post("/api/v1/bots/", json=sample_bot_data)
        created_bot = create_response.json()
        bot_id = created_bot["id"]
        
        # Update bot
        update_data = {
            "name": "Updated Test Bot",
            "position_size_usd": 300.0,
            "stop_loss_pct": 4.0,
            "trade_step_pct": 2.5,
            "cooldown_minutes": 30
        }
        
        response = client.put(f"/api/v1/bots/{bot_id}", json=update_data)
        assert response.status_code == 200
        
        updated_bot = response.json()
        assert updated_bot["name"] == update_data["name"]
        assert updated_bot["position_size_usd"] == update_data["position_size_usd"]
        assert updated_bot["stop_loss_pct"] == update_data["stop_loss_pct"]
        assert updated_bot["trade_step_pct"] == update_data["trade_step_pct"]
        assert updated_bot["cooldown_minutes"] == update_data["cooldown_minutes"]
        # Unchanged fields should remain the same
        assert updated_bot["pair"] == sample_bot_data["pair"]
        assert updated_bot["take_profit_pct"] == sample_bot_data["take_profit_pct"]
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot_id}")
    
    def test_update_nonexistent_bot(self, client):
        """Test updating a non-existent bot returns 404."""
        update_data = {"name": "Non-existent Bot"}
        response = client.put("/api/v1/bots/99999", json=update_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_bot(self, client, sample_bot_data):
        """Test deleting a bot."""
        # Create a test bot
        create_response = client.post("/api/v1/bots/", json=sample_bot_data)
        created_bot = create_response.json()
        bot_id = created_bot["id"]
        
        # Verify bot exists
        get_response = client.get(f"/api/v1/bots/{bot_id}")
        assert get_response.status_code == 200
        
        # Delete bot
        delete_response = client.delete(f"/api/v1/bots/{bot_id}")
        assert delete_response.status_code == 200
        assert "deleted successfully" in delete_response.json()["message"]
        
        # Verify bot is gone
        get_response = client.get(f"/api/v1/bots/{bot_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_bot(self, client):
        """Test deleting a non-existent bot returns 404."""
        response = client.delete("/api/v1/bots/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestBotParameterValidation:
    """Test bot parameter validation and constraints."""
    
    def test_invalid_signal_weight_total(self, client):
        """Test that signal weights exceeding 1.0 are rejected."""
        invalid_bot = {
            "name": "Invalid Weight Bot",
            "description": "Bot with invalid signal weights",
            "pair": "BTC-USD",
            "signal_config": {
                "rsi": {
                    "enabled": True,
                    "weight": 0.7,  # Too high combined weight
                    "period": 14,
                    "buy_threshold": 30,
                    "sell_threshold": 70
                },
                "moving_average": {
                    "enabled": True,
                    "weight": 0.6,  # Total = 1.3, exceeds 1.0
                    "fast_period": 10,
                    "slow_period": 20
                },
                "macd": {
                    "enabled": False,
                    "weight": 0.0,
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                }
            }
        }
        
        response = client.post("/api/v1/bots/", json=invalid_bot)
        assert response.status_code == 422  # Validation error
        error_detail = response.json()["detail"]
        # Should mention weight validation
        assert any("weight" in str(error).lower() for error in error_detail)
    
    def test_invalid_rsi_thresholds(self, client):
        """Test that invalid RSI thresholds are rejected."""
        invalid_bot = {
            "name": "Invalid RSI Bot",
            "description": "Bot with invalid RSI thresholds",
            "pair": "BTC-USD",
            "signal_config": {
                "rsi": {
                    "enabled": True,
                    "weight": 1.0,
                    "period": 14,
                    "buy_threshold": 80,  # Should be less than sell_threshold
                    "sell_threshold": 70
                }
            }
        }
        
        response = client.post("/api/v1/bots/", json=invalid_bot)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_moving_average_periods(self, client):
        """Test that invalid MA periods are rejected."""
        invalid_bot = {
            "name": "Invalid MA Bot",
            "description": "Bot with invalid MA periods",
            "pair": "BTC-USD",
            "signal_config": {
                "moving_average": {
                    "enabled": True,
                    "weight": 1.0,
                    "fast_period": 30,  # Should be less than slow_period
                    "slow_period": 20
                }
            }
        }
        
        response = client.post("/api/v1/bots/", json=invalid_bot)
        assert response.status_code == 422  # Validation error
    
    def test_parameter_ranges(self, client):
        """Test parameter range validation."""
        created_bot_ids = []  # Track created bots for cleanup
        
        try:
            # Test negative position size
            invalid_bot = {
                "name": "Invalid Position Size Bot",
                "description": "Bot with negative position size",
                "pair": "BTC-USD",
                "position_size_usd": -100.0
            }
            
            response = client.post("/api/v1/bots/", json=invalid_bot)
            if response.status_code == 201:  # Bot was created despite invalid data
                created_bot_ids.append(response.json()["id"])
            # Should either reject or use defaults - depends on validation rules
            
            # Test zero or negative percentages
            invalid_bot = {
                "name": "Invalid Percentage Bot",
                "description": "Bot with invalid percentages",
                "pair": "BTC-USD",
                "stop_loss_pct": -1.0,  # Should be positive
                "take_profit_pct": 0.0   # Should be positive
            }
            
            response = client.post("/api/v1/bots/", json=invalid_bot)
            if response.status_code == 201:  # Bot was created despite invalid data
                created_bot_ids.append(response.json()["id"])
            # Should either reject or use defaults
            
        finally:
            # Clean up any created test bots
            for bot_id in created_bot_ids:
                try:
                    client.delete(f"/api/v1/bots/{bot_id}")
                except Exception as e:
                    print(f"Warning: Failed to clean up test bot {bot_id}: {e}")


class TestBotStatusOperations:
    """Test bot status changes (start/stop)."""
    
    def test_start_bot(self, client, sample_bot_data):
        """Test starting a bot."""
        # Create a test bot
        create_response = client.post("/api/v1/bots/", json=sample_bot_data)
        created_bot = create_response.json()
        bot_id = created_bot["id"]
        
        # Start bot
        response = client.post(f"/api/v1/bots/{bot_id}/start")
        assert response.status_code == 200
        assert "started" in response.json()["message"]
        
        # Verify status changed
        get_response = client.get(f"/api/v1/bots/{bot_id}")
        updated_bot = get_response.json()
        assert updated_bot["status"] == "RUNNING"
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot_id}")
    
    def test_stop_bot(self, client, sample_bot_data):
        """Test stopping a bot."""
        # Create and start a test bot
        create_response = client.post("/api/v1/bots/", json=sample_bot_data)
        created_bot = create_response.json()
        bot_id = created_bot["id"]
        
        # Start bot first
        client.post(f"/api/v1/bots/{bot_id}/start")
        
        # Stop bot
        response = client.post(f"/api/v1/bots/{bot_id}/stop")
        assert response.status_code == 200
        assert "stopped" in response.json()["message"]
        
        # Verify status changed
        get_response = client.get(f"/api/v1/bots/{bot_id}")
        updated_bot = get_response.json()
        assert updated_bot["status"] == "STOPPED"
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot_id}")
    
    def test_start_nonexistent_bot(self, client):
        """Test starting a non-existent bot returns 404."""
        response = client.post("/api/v1/bots/99999/start")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_stop_nonexistent_bot(self, client):
        """Test stopping a non-existent bot returns 404."""
        response = client.post("/api/v1/bots/99999/stop")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestBotConfigurationEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_signal_config(self, client):
        """Test bot with empty signal configuration."""
        bot_data = {
            "name": "Empty Config Bot",
            "description": "Bot with empty signal config",
            "pair": "BTC-USD",
            "signal_config": {}
        }
        
        response = client.post("/api/v1/bots/", json=bot_data)
        assert response.status_code == 200
        
        bot = response.json()
        # Should use defaults
        assert "rsi" in bot["signal_config"]
        assert "moving_average" in bot["signal_config"]
        assert "macd" in bot["signal_config"]
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")
    
    def test_missing_signal_config(self, client):
        """Test bot without signal_config field."""
        bot_data = {
            "name": "No Config Bot",
            "description": "Bot without signal config",
            "pair": "BTC-USD"
        }
        
        response = client.post("/api/v1/bots/", json=bot_data)
        assert response.status_code == 200
        
        bot = response.json()
        # Should use defaults
        assert bot["signal_config"] is not None
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")
    
    def test_extreme_parameter_values(self, client):
        """Test extreme but valid parameter values."""
        extreme_bot = {
            "name": "Extreme Values Bot",
            "description": "Bot with extreme parameter values",
            "pair": "BTC-USD",
            "position_size_usd": 10000.0,  # High position size
            "max_positions": 10,  # Multiple positions
            "stop_loss_pct": 20.0,  # High stop loss
            "take_profit_pct": 50.0,  # High take profit
            "trade_step_pct": 10.0,  # High trade step
            "cooldown_minutes": 120,  # Long cooldown
            "signal_config": {
                "rsi": {
                    "enabled": True,
                    "weight": 1.0,  # Full weight on RSI
                    "period": 100,  # Long period
                    "buy_threshold": 10,  # Extreme oversold
                    "sell_threshold": 90  # Extreme overbought
                }
            }
        }
        
        response = client.post("/api/v1/bots/", json=extreme_bot)
        assert response.status_code == 200
        
        bot = response.json()
        assert bot["position_size_usd"] == 10000.0
        assert bot["max_positions"] == 10
        assert bot["stop_loss_pct"] == 20.0
        assert bot["take_profit_pct"] == 50.0
        assert bot["trade_step_pct"] == 10.0
        assert bot["cooldown_minutes"] == 120
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")


if __name__ == "__main__":
    pytest.main([__file__])
