"""
Tests for the unified temperature system (Phase 3.2/3.3)
"""
import pytest
from app.utils.temperature import calculate_bot_temperature, get_temperature_emoji


class TestTemperatureCalculation:
    """Test the unified temperature calculation logic."""

    def test_hot_temperature_positive(self):
        """Test HOT temperature for positive scores >= 0.3"""
        assert calculate_bot_temperature(0.3) == "HOT"
        assert calculate_bot_temperature(0.5) == "HOT"
        assert calculate_bot_temperature(1.0) == "HOT"

    def test_hot_temperature_negative(self):
        """Test HOT temperature for negative scores <= -0.3"""
        assert calculate_bot_temperature(-0.3) == "HOT"
        assert calculate_bot_temperature(-0.5) == "HOT"
        assert calculate_bot_temperature(-1.0) == "HOT"

    def test_warm_temperature_positive(self):
        """Test WARM temperature for positive scores 0.15-0.29"""
        assert calculate_bot_temperature(0.15) == "WARM"
        assert calculate_bot_temperature(0.2) == "WARM"
        assert calculate_bot_temperature(0.29) == "WARM"

    def test_warm_temperature_negative(self):
        """Test WARM temperature for negative scores -0.15 to -0.29"""
        assert calculate_bot_temperature(-0.15) == "WARM"
        assert calculate_bot_temperature(-0.166) == "WARM"  # Real ETH bot score
        assert calculate_bot_temperature(-0.2) == "WARM"
        assert calculate_bot_temperature(-0.29) == "WARM"

    def test_cool_temperature_positive(self):
        """Test COOL temperature for positive scores 0.05-0.14"""
        assert calculate_bot_temperature(0.05) == "COOL"
        assert calculate_bot_temperature(0.1) == "COOL"
        assert calculate_bot_temperature(0.14) == "COOL"

    def test_cool_temperature_negative(self):
        """Test COOL temperature for negative scores -0.05 to -0.14"""
        assert calculate_bot_temperature(-0.05) == "COOL"
        assert calculate_bot_temperature(-0.1) == "COOL"
        assert calculate_bot_temperature(-0.14) == "COOL"

    def test_frozen_temperature(self):
        """Test FROZEN temperature for scores between -0.05 and 0.05"""
        assert calculate_bot_temperature(0.0) == "FROZEN"
        assert calculate_bot_temperature(0.01) == "FROZEN"
        assert calculate_bot_temperature(-0.01) == "FROZEN"
        assert calculate_bot_temperature(0.049) == "FROZEN"
        assert calculate_bot_temperature(-0.049) == "FROZEN"

    def test_threshold_boundaries(self):
        """Test exact threshold boundaries"""
        # Just below thresholds should be lower temperature
        assert calculate_bot_temperature(0.049) == "FROZEN"
        assert calculate_bot_temperature(0.149) == "COOL"
        assert calculate_bot_temperature(0.299) == "WARM"
        
        # At thresholds should be higher temperature
        assert calculate_bot_temperature(0.05) == "COOL"
        assert calculate_bot_temperature(0.15) == "WARM"
        assert calculate_bot_temperature(0.3) == "HOT"

    def test_realistic_trading_scores(self):
        """Test with realistic trading signal scores"""
        # BTC Scalper example (ultra-sensitive)
        assert calculate_bot_temperature(-0.756) == "HOT"
        
        # ETH Momentum example (moderate signals)
        assert calculate_bot_temperature(-0.166) == "WARM"
        
        # Typical small trading signals
        assert calculate_bot_temperature(0.08) == "COOL"
        assert calculate_bot_temperature(-0.03) == "FROZEN"


class TestTemperatureEmojis:
    """Test temperature emoji mapping."""

    def test_valid_temperature_emojis(self):
        """Test all valid temperature emoji mappings"""
        assert get_temperature_emoji("HOT") == "🔥"
        assert get_temperature_emoji("WARM") == "🌡️"
        assert get_temperature_emoji("COOL") == "❄️"
        assert get_temperature_emoji("FROZEN") == "🧊"

    def test_invalid_temperature_emoji(self):
        """Test invalid temperature returns default emoji"""
        assert get_temperature_emoji("INVALID") == "⚪"
        assert get_temperature_emoji("") == "⚪"
        assert get_temperature_emoji(None) == "⚪"

    def test_case_sensitivity(self):
        """Test emoji mapping is case sensitive"""
        assert get_temperature_emoji("hot") == "⚪"  # lowercase should fail
        assert get_temperature_emoji("Hot") == "⚪"  # mixed case should fail


class TestTemperatureIntegration:
    """Test temperature system integration patterns."""

    def test_score_to_emoji_pipeline(self):
        """Test complete score to emoji conversion pipeline"""
        # Test the full pipeline used in production
        score = -0.166  # ETH bot score
        temperature = calculate_bot_temperature(score)
        emoji = get_temperature_emoji(temperature)
        
        assert temperature == "WARM"
        assert emoji == "🌡️"

    def test_temperature_consistency(self):
        """Test temperature calculation is consistent for same inputs"""
        score = 0.25
        temp1 = calculate_bot_temperature(score)
        temp2 = calculate_bot_temperature(score)
        assert temp1 == temp2 == "WARM"

    def test_production_bot_examples(self):
        """Test with actual production bot configurations"""
        # BTC Scalper: Ultra-sensitive RSI (period=2, thresholds 80/90)
        btc_score = -0.756
        assert calculate_bot_temperature(btc_score) == "HOT"
        assert get_temperature_emoji(calculate_bot_temperature(btc_score)) == "🔥"
        
        # ETH Momentum: Multi-signal (RSI 0.4 + MA 0.35 + MACD 0.25)
        eth_score = -0.166
        assert calculate_bot_temperature(eth_score) == "WARM"
        assert get_temperature_emoji(calculate_bot_temperature(eth_score)) == "🌡️"
