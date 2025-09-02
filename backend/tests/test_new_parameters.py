"""
Test new bot parameters (trade_step_pct and cooldown_minutes) specifically.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


class TestNewBotParameters:
    """Test the newly added trade_step_pct and cooldown_minutes parameters."""
    
    def test_create_bot_with_new_parameters(self, client):
        """Test creating a bot with the new trade control parameters."""
        bot_data = {
            "name": "New Parameters Test Bot",
            "description": "Testing trade_step_pct and cooldown_minutes",
            "pair": "BTC-USD",
            "position_size_usd": 500.0,
            "trade_step_pct": 3.5,  # Custom trade step
            "cooldown_minutes": 45,  # Custom cooldown
            "signal_config": {
                "rsi": {
                    "enabled": True,
                    "weight": 1.0,
                    "period": 14,
                    "buy_threshold": 30,
                    "sell_threshold": 70
                }
            }
        }
        
        response = client.post("/api/v1/bots/", json=bot_data)
        assert response.status_code == 200
        
        bot = response.json()
        # Verify new parameters are stored correctly
        assert bot["trade_step_pct"] == 3.5
        assert bot["cooldown_minutes"] == 45
        
        # Verify other parameters are also correct
        assert bot["position_size_usd"] == 500.0
        assert bot["name"] == bot_data["name"]
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")
    
    def test_new_parameters_use_defaults(self, client):
        """Test that new parameters use correct defaults when not specified."""
        bot_data = {
            "name": "Default Parameters Bot",
            "description": "Testing default values for new parameters",
            "pair": "ETH-USD"
            # Note: not specifying trade_step_pct or cooldown_minutes
        }
        
        response = client.post("/api/v1/bots/", json=bot_data)
        assert response.status_code == 200
        
        bot = response.json()
        # Check that defaults are applied
        assert bot["trade_step_pct"] == 2.0  # Default value
        assert bot["cooldown_minutes"] == 15  # Default value
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")
    
    def test_update_new_parameters(self, client):
        """Test updating the new parameters on existing bots."""
        # Create a bot first
        bot_data = {
            "name": "Update Test Bot",
            "description": "Bot for testing parameter updates",
            "pair": "BTC-USD",
            "trade_step_pct": 1.0,
            "cooldown_minutes": 10
        }
        
        create_response = client.post("/api/v1/bots/", json=bot_data)
        bot = create_response.json()
        bot_id = bot["id"]
        
        # Update the new parameters
        update_data = {
            "trade_step_pct": 5.0,
            "cooldown_minutes": 60
        }
        
        update_response = client.put(f"/api/v1/bots/{bot_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated_bot = update_response.json()
        assert updated_bot["trade_step_pct"] == 5.0
        assert updated_bot["cooldown_minutes"] == 60
        
        # Verify other fields weren't changed
        assert updated_bot["name"] == bot_data["name"]
        assert updated_bot["pair"] == bot_data["pair"]
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot_id}")
    
    def test_extreme_new_parameter_values(self, client):
        """Test extreme but valid values for new parameters."""
        bot_data = {
            "name": "Extreme New Params Bot",
            "description": "Testing extreme values for new parameters",
            "pair": "BTC-USD",
            "trade_step_pct": 0.1,  # Very small step
            "cooldown_minutes": 120  # Long cooldown
        }
        
        response = client.post("/api/v1/bots/", json=bot_data)
        assert response.status_code == 200
        
        bot = response.json()
        assert bot["trade_step_pct"] == 0.1
        assert bot["cooldown_minutes"] == 120
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")
    
    def test_zero_trade_step(self, client):
        """Test zero trade step parameter."""
        bot_data = {
            "name": "Zero Trade Step Bot",
            "description": "Testing zero trade step",
            "pair": "ETH-USD",
            "trade_step_pct": 0.0  # Zero trade step
        }
        
        response = client.post("/api/v1/bots/", json=bot_data)
        # This should be allowed (means no minimum step required)
        assert response.status_code == 200
        
        bot = response.json()
        assert bot["trade_step_pct"] == 0.0
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")
    
    def test_minimal_cooldown(self, client):
        """Test minimal cooldown parameter."""
        bot_data = {
            "name": "Minimal Cooldown Bot",
            "description": "Testing minimal cooldown",
            "pair": "BTC-USD",
            "cooldown_minutes": 1  # Minimal cooldown
        }
        
        response = client.post("/api/v1/bots/", json=bot_data)
        assert response.status_code == 200
        
        bot = response.json()
        assert bot["cooldown_minutes"] == 1
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")
    
    def test_parameter_persistence_across_status_changes(self, client):
        """Test that new parameters persist through start/stop operations."""
        # Create bot with specific parameter values
        bot_data = {
            "name": "Persistence Test Bot",
            "description": "Testing parameter persistence",
            "pair": "BTC-USD",
            "trade_step_pct": 2.5,
            "cooldown_minutes": 30
        }
        
        create_response = client.post("/api/v1/bots/", json=bot_data)
        bot = create_response.json()
        bot_id = bot["id"]
        
        # Start the bot
        start_response = client.post(f"/api/v1/bots/{bot_id}/start")
        assert start_response.status_code == 200
        
        # Check parameters are still there
        get_response = client.get(f"/api/v1/bots/{bot_id}")
        running_bot = get_response.json()
        assert running_bot["trade_step_pct"] == 2.5
        assert running_bot["cooldown_minutes"] == 30
        assert running_bot["status"] == "RUNNING"
        
        # Stop the bot
        stop_response = client.post(f"/api/v1/bots/{bot_id}/stop")
        assert stop_response.status_code == 200
        
        # Check parameters are still there
        get_response = client.get(f"/api/v1/bots/{bot_id}")
        stopped_bot = get_response.json()
        assert stopped_bot["trade_step_pct"] == 2.5
        assert stopped_bot["cooldown_minutes"] == 30
        assert stopped_bot["status"] == "STOPPED"
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot_id}")
    
    def test_all_parameters_together(self, client):
        """Test creating a bot with all parameters including new ones."""
        comprehensive_bot = {
            "name": "Comprehensive Test Bot",
            "description": "Bot with all parameters specified",
            "pair": "BTC-USD",
            "position_size_usd": 750.0,
            "max_positions": 2,
            "stop_loss_pct": 4.5,
            "take_profit_pct": 8.0,
            "confirmation_minutes": 7,
            "trade_step_pct": 1.8,
            "cooldown_minutes": 25,
            "signal_config": {
                "rsi": {
                    "enabled": True,
                    "weight": 0.4,
                    "period": 21,
                    "buy_threshold": 25,
                    "sell_threshold": 75
                },
                "moving_average": {
                    "enabled": True,
                    "weight": 0.35,
                    "fast_period": 8,
                    "slow_period": 21
                },
                "macd": {
                    "enabled": True,
                    "weight": 0.25,
                    "fast_period": 10,
                    "slow_period": 24,
                    "signal_period": 7
                }
            }
        }
        
        response = client.post("/api/v1/bots/", json=comprehensive_bot)
        assert response.status_code == 200
        
        bot = response.json()
        
        # Verify all parameters
        assert bot["position_size_usd"] == 750.0
        assert bot["max_positions"] == 2
        assert bot["stop_loss_pct"] == 4.5
        assert bot["take_profit_pct"] == 8.0
        assert bot["confirmation_minutes"] == 7
        assert bot["trade_step_pct"] == 1.8  # New parameter
        assert bot["cooldown_minutes"] == 25  # New parameter
        
        # Verify signal configuration
        signals = bot["signal_config"]
        assert signals["rsi"]["weight"] == 0.4
        assert signals["moving_average"]["weight"] == 0.35
        assert signals["macd"]["weight"] == 0.25
        # Total weight should be 1.0
        total_weight = signals["rsi"]["weight"] + signals["moving_average"]["weight"] + signals["macd"]["weight"]
        assert abs(total_weight - 1.0) < 0.001  # Allow for floating point precision
        
        # Clean up
        client.delete(f"/api/v1/bots/{bot['id']}")


if __name__ == "__main__":
    pytest.main([__file__])
