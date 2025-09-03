"""
Test bot signal evaluation and aggregation functionality.
"""

import pytest
import pandas as pd
import numpy as np
import json
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.bot_evaluator import BotSignalEvaluator
from app.models.models import Bot
from tests.test_signals import create_test_data


class TestBotSignalEvaluator:
    """Test bot signal evaluation and aggregation."""
    
    def create_test_bot(self, signal_config: dict, name: str = "Test Bot") -> Bot:
        """Create a test bot with given signal configuration."""
        bot = Bot(
            id=1,
            name=name,
            description="Test bot for signal evaluation",
            pair="BTC-USD",
            status="STOPPED",
            position_size_usd=100.0,
            max_positions=1,
            stop_loss_pct=5.0,
            take_profit_pct=10.0,
            confirmation_minutes=5,
            trade_step_pct=2.0,
            cooldown_minutes=15,
            signal_config=json.dumps(signal_config)
        )
        return bot
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def evaluator(self, mock_db):
        """Create bot evaluator instance."""
        return BotSignalEvaluator(mock_db, enable_confirmation=False)
    
    def test_single_signal_evaluation(self, evaluator):
        """Test evaluation with a single RSI signal."""
        # Bot with only RSI enabled
        signal_config = {
            "rsi": {
                "enabled": True,
                "weight": 1.0,
                "period": 14,
                "buy_threshold": 30,
                "sell_threshold": 70
            }
        }
        
        bot = self.create_test_bot(signal_config)
        market_data = create_test_data("downtrend", length=30)  # Should trigger RSI buy signal
        
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Should return valid evaluation
        assert 'overall_score' in result
        assert 'action' in result
        assert 'confidence' in result
        assert 'signal_results' in result
        assert 'metadata' in result
        
        # Score should be within valid range
        assert -1.0 <= result['overall_score'] <= 1.0
        assert result['action'] in ['buy', 'sell', 'hold']
        assert 0 <= result['confidence'] <= 1.0
        
        # Should have RSI result
        assert 'rsi' in result['signal_results']
        assert result['metadata']['enabled_signals'] == 1
        assert result['metadata']['total_weight'] == 1.0
    
    def test_multiple_signal_evaluation(self, evaluator):
        """Test evaluation with multiple signals."""
        # Bot with RSI and Moving Average
        signal_config = {
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
            }
        }
        
        bot = self.create_test_bot(signal_config)
        market_data = create_test_data("uptrend", length=40)
        
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Should aggregate both signals
        assert result['metadata']['enabled_signals'] == 2
        assert result['metadata']['total_weight'] == 1.0
        assert 'rsi' in result['signal_results']
        assert 'moving_average' in result['signal_results']
        
        # Overall score should be weighted average
        rsi_score = result['signal_results']['rsi']['score']
        ma_score = result['signal_results']['moving_average']['score']
        expected_score = (rsi_score * 0.6) + (ma_score * 0.4)
        
        assert abs(result['overall_score'] - expected_score) < 0.001
    
    def test_weighted_aggregation_logic(self, evaluator):
        """Test that weighted aggregation works correctly."""
        # Create signals with known scores by using extreme market conditions
        signal_config = {
            "rsi": {
                "enabled": True,
                "weight": 0.3,
                "period": 14,
                "buy_threshold": 30,
                "sell_threshold": 70
            },
            "moving_average": {
                "enabled": True,
                "weight": 0.7,
                "fast_period": 5,
                "slow_period": 10
            }
        }
        
        bot = self.create_test_bot(signal_config)
        
        # Use strong uptrend to get predictable signals
        uptrend_data = create_test_data("uptrend", length=30)
        result = evaluator.evaluate_bot(bot, uptrend_data)
        
        # Verify weighted calculation
        rsi_weight = 0.3
        ma_weight = 0.7
        
        rsi_score = result['signal_results']['rsi']['score']
        ma_score = result['signal_results']['moving_average']['score']
        
        expected_overall = (rsi_score * rsi_weight) + (ma_score * ma_weight)
        actual_overall = result['overall_score']
        
        assert abs(actual_overall - expected_overall) < 0.001, f"Expected {expected_overall}, got {actual_overall}"
        assert result['metadata']['total_weight'] == 1.0
    
    def test_disabled_signals_ignored(self, evaluator):
        """Test that disabled signals are ignored."""
        signal_config = {
            "rsi": {
                "enabled": True,
                "weight": 0.8,
                "period": 14,
                "buy_threshold": 30,
                "sell_threshold": 70
            },
            "moving_average": {
                "enabled": False,  # Disabled
                "weight": 0.2,
                "fast_period": 10,
                "slow_period": 20
            }
        }
        
        bot = self.create_test_bot(signal_config)
        market_data = create_test_data("sideways", length=30)
        
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Should only evaluate RSI
        assert result['metadata']['enabled_signals'] == 1
        assert result['metadata']['total_weight'] == 0.8
        assert 'rsi' in result['signal_results']
        assert 'moving_average' not in result['signal_results']
        
        # Overall score should match RSI score (with floating point tolerance)
        rsi_score = result['signal_results']['rsi']['score']
        assert abs(result['overall_score'] - rsi_score) < 1e-10
    
    def test_action_determination(self, evaluator):
        """Test that action determination follows score thresholds."""
        # Test different score scenarios
        test_cases = [
            (-0.8, 'buy'),   # Strong negative score -> buy
            (-0.1, 'hold'),  # Weak negative score -> hold
            (0.1, 'hold'),   # Weak positive score -> hold
            (0.8, 'sell'),   # Strong positive score -> sell
        ]
        
        for test_score, expected_action in test_cases:
            # Mock a simple evaluation that returns the test score
            signal_config = {
                "rsi": {
                    "enabled": True,
                    "weight": 1.0,
                    "period": 14,
                    "buy_threshold": 30,
                    "sell_threshold": 70
                }
            }
            
            bot = self.create_test_bot(signal_config)
            
            # Use the evaluator's action determination method directly
            action = evaluator._determine_action(test_score, bot)
            assert action == expected_action, f"Score {test_score} should give action {expected_action}, got {action}"
    
    def test_macd_signal_integration(self, evaluator):
        """Test MACD signal integration in bot evaluation."""
        signal_config = {
            "macd": {
                "enabled": True,
                "weight": 1.0,
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            }
        }
        
        bot = self.create_test_bot(signal_config)
        market_data = create_test_data("volatile", length=60)  # Need more data for MACD
        
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Should successfully evaluate MACD
        assert result['metadata']['enabled_signals'] == 1
        assert 'macd' in result['signal_results']
        assert 'macd_line' in result['signal_results']['macd']['metadata']
        assert -1.0 <= result['overall_score'] <= 1.0
    
    def test_insufficient_data_handling(self, evaluator):
        """Test handling of insufficient market data."""
        signal_config = {
            "rsi": {
                "enabled": True,
                "weight": 1.0,
                "period": 14,
                "buy_threshold": 30,
                "sell_threshold": 70
            }
        }
        
        bot = self.create_test_bot(signal_config)
        # Only 5 data points - insufficient for RSI
        market_data = create_test_data("uptrend", length=5)
        
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Should handle gracefully
        assert result['action'] == 'hold'
        assert result['overall_score'] == 0
        assert 'error' in result['metadata']
    
    def test_invalid_signal_config(self, evaluator):
        """Test handling of invalid signal configuration."""
        # Bot with invalid JSON
        bot = self.create_test_bot({})
        bot.signal_config = "invalid json"
        
        market_data = create_test_data("uptrend", length=30)
        
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Should return error result
        assert result['action'] == 'hold'
        assert result['overall_score'] == 0
        assert 'error' in result['metadata']
    
    def test_empty_signal_config(self, evaluator):
        """Test handling of empty signal configuration."""
        bot = self.create_test_bot({})
        market_data = create_test_data("uptrend", length=30)
        
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Should return error result
        assert result['action'] == 'hold'
        assert result['overall_score'] == 0
        assert 'error' in result['metadata']
    
    def test_signal_parameter_mapping(self, evaluator):
        """Test that bot config parameters are correctly mapped to signal parameters."""
        # Test RSI parameter mapping
        signal_config = {
            "rsi": {
                "enabled": True,
                "weight": 1.0,
                "period": 21,  # Non-default
                "buy_threshold": 25,  # Non-default  
                "sell_threshold": 75  # Non-default
            }
        }
        
        bot = self.create_test_bot(signal_config)
        market_data = create_test_data("downtrend", length=30)
        
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Check that custom parameters were used
        rsi_metadata = result['signal_results']['rsi']['metadata']
        assert rsi_metadata['period'] == 21
        assert rsi_metadata['oversold_threshold'] == 25
        assert rsi_metadata['overbought_threshold'] == 75
    
    def test_confidence_aggregation(self, evaluator):
        """Test that confidence values are properly aggregated."""
        signal_config = {
            "rsi": {
                "enabled": True,
                "weight": 0.5,
                "period": 14,
                "buy_threshold": 30,
                "sell_threshold": 70
            },
            "moving_average": {
                "enabled": True,
                "weight": 0.5,
                "fast_period": 10,
                "slow_period": 20
            }
        }
        
        bot = self.create_test_bot(signal_config)
        market_data = create_test_data("uptrend", length=40)
        
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Overall confidence should be average of individual confidences
        rsi_confidence = result['signal_results']['rsi']['confidence']
        ma_confidence = result['signal_results']['moving_average']['confidence']
        expected_confidence = (rsi_confidence + ma_confidence) / 2
        
        assert abs(result['confidence'] - expected_confidence) < 0.001
