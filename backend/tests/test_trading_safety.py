"""
Tests for Trading Safety Service - Phase 4.1.1
Comprehensive testing of all safety limits and circuit breakers.
"""

import pytest
from unittest.mock import Mock

from app.services.trading_safety import TradingSafetyService, TradingSafetyLimits


class TestTradingSafetyLimits:
    """Test the hardcoded safety limits configuration."""
    
    def test_safety_limits_constants(self):
        """Verify all safety limits are properly defined."""
        limits = TradingSafetyLimits()
        
        # Daily limits
        assert limits.MAX_DAILY_LOSS_USD == 100.00
        assert limits.MAX_DAILY_TRADES == 10
        assert limits.MAX_TRADES_PER_BOT_DAILY == 5
        
        # Position limits
        assert limits.MAX_POSITION_SIZE_USD == 25.00
        assert limits.MIN_POSITION_SIZE_USD == 5.00
        
        # Bot limits
        assert limits.MAX_ACTIVE_POSITIONS == 2
        assert limits.MIN_TEMPERATURE_FOR_TRADING == "WARM"
        
        # Emergency limits
        assert limits.MAX_CONSECUTIVE_LOSSES == 3
        assert limits.EMERGENCY_STOP_LOSS_USD == 50.00


class TestTradingSafetyServiceCore:
    """Test core functionality of trading safety service."""
    
    def test_position_size_validation_valid(self):
        """Test valid position size acceptance."""
        safety_service = TradingSafetyService(Mock())
        
        # Valid sizes within limits
        valid_sizes = [5.00, 15.00, 25.00]
        
        for size in valid_sizes:
            result = safety_service._check_position_size(size)
            assert result is True, f"Size {size} should be valid"
    
    def test_position_size_validation_invalid(self):
        """Test invalid position size rejection."""
        safety_service = TradingSafetyService(Mock())
        
        # Invalid sizes outside limits
        invalid_sizes = [4.99, 0.01, 25.01, 50.00, 100.00]
        
        for size in invalid_sizes:
            result = safety_service._check_position_size(size)
            assert result is False, f"Size {size} should be invalid"
    
    def test_temperature_requirements_valid(self):
        """Test valid temperature levels for trading."""
        safety_service = TradingSafetyService(Mock())
        
        valid_temperatures = ["WARM", "HOT"]
        
        for temp in valid_temperatures:
            result = safety_service._check_temperature_requirements(temp)
            assert result is True, f"Temperature {temp} should allow trading"
    
    def test_temperature_requirements_invalid(self):
        """Test invalid temperature levels that block trading."""
        safety_service = TradingSafetyService(Mock())
        
        invalid_temperatures = ["COOL", "FROZEN", "UNKNOWN"]
        
        for temp in invalid_temperatures:
            result = safety_service._check_temperature_requirements(temp)
            assert result is False, f"Temperature {temp} should block trading"


class TestTradingSafetyEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_invalid_temperature_string(self):
        """Test handling of invalid temperature strings."""
        safety_service = TradingSafetyService(Mock())
        
        result = safety_service._check_temperature_requirements("INVALID_TEMP")
        assert result is False
    
    def test_zero_position_size(self):
        """Test handling of zero position size."""
        safety_service = TradingSafetyService(Mock())
        
        result = safety_service._check_position_size(0.0)
        assert result is False
    
    def test_negative_position_size(self):
        """Test handling of negative position size."""
        safety_service = TradingSafetyService(Mock())
        
        result = safety_service._check_position_size(-10.0)
        assert result is False


# Note: Comprehensive integration testing is done in test_phase_4_1_1_integration.py
# which tests the complete safety validation pipeline with real API calls.


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
