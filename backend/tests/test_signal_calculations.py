"""
Comprehensive unit tests for trading signal calculations.

This test suite validates the mathematical correctness of:
1. Individual signal calculations (RSI, MA, MACD) 
2. Signal aggregation logic
3. Action determination thresholds
4. Edge cases and boundary conditions

Focus: Mathematical accuracy, not backtesting performance.
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app.services.signals.technical import RSISignal, MovingAverageSignal, MACDSignal
from backend.app.services.bot_evaluator import BotSignalEvaluator
from backend.app.models.models import Bot


class TestRSISignalCalculations:
    """Test RSI signal calculation accuracy."""
    
    def create_test_data(self, prices: list) -> pd.DataFrame:
        """Create test market data with known price sequence."""
        return pd.DataFrame({
            'close': prices,
            'timestamp': pd.date_range('2024-01-01', periods=len(prices), freq='1min')
        })
    
    def test_rsi_calculation_known_values(self):
        """Test RSI calculation with manually verified values."""
        # Known RSI test case: 14-period RSI
        # This sequence should produce RSI ≈ 70.53 (calculated manually)
        prices = [44, 44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.85, 46.08, 
                 45.89, 46.03, 46.83, 47.69, 46.49, 46.26, 47.09, 47.37, 47.20]
        
        data = self.create_test_data(prices)
        signal = RSISignal(period=14, oversold=30, overbought=70)
        result = signal.calculate(data)
        
        # Verify RSI value is approximately correct (allow for floating point tolerance)
        rsi_value = result['metadata']['rsi_value']
        assert 69.5 <= rsi_value <= 71.5, f"Expected RSI ~70.53, got {rsi_value}"
        
        # Verify signal interpretation (RSI > 70 = overbought = sell signal)
        assert result['action'] == 'sell', f"Expected 'sell' action for RSI {rsi_value}"
        assert result['score'] > 0, f"Expected positive score for sell signal, got {result['score']}"
    
    def test_rsi_boundary_conditions(self):
        """Test RSI at exact threshold boundaries."""
        signal = RSISignal(period=14, oversold=30, overbought=70)
        
        # Test with prices that should produce RSI exactly at oversold threshold
        # Declining price sequence to hit RSI ~30
        declining_prices = [50] + [50 - i*0.5 for i in range(1, 20)]
        data = self.create_test_data(declining_prices)
        result = signal.calculate(data)
        
        rsi_value = result['metadata']['rsi_value']
        assert rsi_value < 40, f"Expected low RSI for declining prices, got {rsi_value}"
        assert result['action'] == 'buy', "Expected 'buy' action for oversold condition"
        assert result['score'] < 0, "Expected negative score for buy signal"
    
    def test_rsi_different_periods(self):
        """Test RSI calculation with different periods (7, 14, 21)."""
        prices = [50, 51, 52, 53, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37]
        data = self.create_test_data(prices)
        
        # Test different RSI periods
        for period in [7, 14, 21]:
            signal = RSISignal(period=period, oversold=30, overbought=70)
            result = signal.calculate(data)
            
            # All should calculate successfully
            assert 'error' not in result['metadata'], f"RSI calculation failed for period {period}"
            assert 0 <= result['metadata']['rsi_value'] <= 100, f"RSI out of range for period {period}"
            assert result['action'] in ['buy', 'sell', 'hold'], f"Invalid action for period {period}"
    
    def test_rsi_different_thresholds(self):
        """Test RSI with different buy/sell thresholds."""
        # Price sequence that should produce RSI around 50 (neutral)
        neutral_prices = [50, 51, 50, 51, 50, 51, 50, 51, 50, 51, 50, 51, 50, 51, 50]
        data = self.create_test_data(neutral_prices)
        
        # Test conservative thresholds (20/80)
        conservative = RSISignal(period=14, oversold=20, overbought=80)
        conservative_result = conservative.calculate(data)
        
        # Test aggressive thresholds (40/60)  
        aggressive = RSISignal(period=14, oversold=40, overbought=60)
        aggressive_result = aggressive.calculate(data)
        
        # Same RSI value, different interpretations
        assert conservative_result['metadata']['rsi_value'] == aggressive_result['metadata']['rsi_value']
        
        # Conservative should be 'hold', aggressive might be 'buy' or 'sell'
        assert conservative_result['action'] == 'hold', "Conservative thresholds should produce 'hold'"
        # Aggressive could be any action depending on exact RSI value around 50
    
    def test_rsi_insufficient_data(self):
        """Test RSI behavior with insufficient data."""
        # Only 5 data points for 14-period RSI
        insufficient_data = self.create_test_data([50, 51, 52, 53, 54])
        signal = RSISignal(period=14, oversold=30, overbought=70)
        result = signal.calculate(insufficient_data)
        
        # Should return neutral/hold result
        assert result['action'] == 'hold'
        assert result['score'] == 0
        assert result['confidence'] == 0
    
    def test_rsi_score_range(self):
        """Test that RSI scores are always within -1.0 to 1.0 range."""
        # Test extreme price movements
        extreme_up = [10] + [10 + i*5 for i in range(1, 20)]  # Strong uptrend
        extreme_down = [100] + [100 - i*5 for i in range(1, 20)]  # Strong downtrend
        
        signal = RSISignal(period=14, oversold=30, overbought=70)
        
        for prices in [extreme_up, extreme_down]:
            data = self.create_test_data(prices)
            result = signal.calculate(data)
            
            assert -1.0 <= result['score'] <= 1.0, f"RSI score {result['score']} out of range [-1, 1]"


class TestMovingAverageSignalCalculations:
    """Test Moving Average signal calculation accuracy."""
    
    def create_test_data(self, prices: list) -> pd.DataFrame:
        """Create test market data with known price sequence."""
        return pd.DataFrame({
            'close': prices,
            'timestamp': pd.date_range('2024-01-01', periods=len(prices), freq='1min')
        })
    
    def test_ma_crossover_bullish(self):
        """Test bullish MA crossover detection."""
        # Create price sequence where fast MA crosses above slow MA
        # Start low, then trend up to create crossover
        prices = [10, 10, 10, 10, 10,  # Initial period (both MAs equal)
                 11, 12, 13, 14, 15,  # Uptrend starts  
                 16, 17, 18, 19, 20]  # Continued uptrend
        
        data = self.create_test_data(prices)
        signal = MovingAverageSignal(fast_period=5, slow_period=10)
        result = signal.calculate(data)
        
        # Should detect bullish crossover
        assert result['action'] == 'buy', f"Expected 'buy' for bullish crossover, got '{result['action']}'"
        assert result['score'] < 0, f"Expected negative score for buy signal, got {result['score']}"
        assert result['confidence'] > 0.5, f"Expected high confidence for crossover, got {result['confidence']}"
    
    def test_ma_crossover_bearish(self):
        """Test bearish MA crossover detection."""
        # Create price sequence where fast MA crosses below slow MA
        prices = [20, 20, 20, 20, 20,  # Initial period (both MAs equal)
                 19, 18, 17, 16, 15,  # Downtrend starts
                 14, 13, 12, 11, 10]  # Continued downtrend
        
        data = self.create_test_data(prices)
        signal = MovingAverageSignal(fast_period=5, slow_period=10)
        result = signal.calculate(data)
        
        # Should detect bearish crossover
        assert result['action'] == 'sell', f"Expected 'sell' for bearish crossover, got '{result['action']}'"
        assert result['score'] > 0, f"Expected positive score for sell signal, got {result['score']}"
        assert result['confidence'] > 0.5, f"Expected high confidence for crossover, got {result['confidence']}"
    
    def test_ma_no_crossover(self):
        """Test MA behavior when no crossover occurs."""
        # Stable prices - no crossover
        stable_prices = [15] * 20
        data = self.create_test_data(stable_prices)
        signal = MovingAverageSignal(fast_period=5, slow_period=10)
        result = signal.calculate(data)
        
        # Should be neutral/hold
        assert result['action'] == 'hold', f"Expected 'hold' for no crossover, got '{result['action']}'"
        assert abs(result['score']) < 0.2, f"Expected near-zero score for no crossover, got {result['score']}"
    
    def test_ma_different_periods(self):
        """Test MA with different period combinations."""
        prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
        data = self.create_test_data(prices)
        
        period_combinations = [
            (5, 10),   # Fast crossover
            (10, 20),  # Medium crossover
            (12, 26),  # Standard periods
            (9, 21)    # Aggressive periods
        ]
        
        for fast, slow in period_combinations:
            if len(prices) > slow:  # Ensure sufficient data
                signal = MovingAverageSignal(fast_period=fast, slow_period=slow)
                result = signal.calculate(data)
                
                # All should calculate successfully
                assert 'error' not in result['metadata'], f"MA calculation failed for periods {fast}/{slow}"
                assert result['action'] in ['buy', 'sell', 'hold'], f"Invalid action for periods {fast}/{slow}"
                assert -1.0 <= result['score'] <= 1.0, f"Score out of range for periods {fast}/{slow}"
    
    def test_ma_metadata_accuracy(self):
        """Test that MA metadata contains correct calculated values."""
        prices = [10, 11, 12, 13, 14, 15]
        data = self.create_test_data(prices)
        signal = MovingAverageSignal(fast_period=3, slow_period=5)
        result = signal.calculate(data)
        
        # Manually calculate expected MAs
        fast_ma_expected = (prices[-3:])  # Last 3 prices
        slow_ma_expected = (prices[-5:])  # Last 5 prices
        
        fast_ma_actual = result['metadata']['fast_ma']
        slow_ma_actual = result['metadata']['slow_ma']
        
        # Verify MA calculations
        assert abs(fast_ma_actual - np.mean(fast_ma_expected)) < 0.01, "Fast MA calculation incorrect"
        assert abs(slow_ma_actual - np.mean(slow_ma_expected)) < 0.01, "Slow MA calculation incorrect"


class TestMACDSignalCalculations:
    """Test MACD signal calculation accuracy."""
    
    def create_test_data(self, prices: list) -> pd.DataFrame:
        """Create test market data with known price sequence."""
        return pd.DataFrame({
            'close': prices,
            'timestamp': pd.date_range('2024-01-01', periods=len(prices), freq='1min')
        })
    
    def test_macd_bullish_conditions(self):
        """Test MACD bullish signal conditions."""
        # Create uptrending price sequence
        prices = [50 + i*0.5 for i in range(50)]  # Steady uptrend
        data = self.create_test_data(prices)
        signal = MACDSignal(fast_period=12, slow_period=26, signal_period=9)
        result = signal.calculate(data)
        
        # In uptrend, MACD should be bullish
        macd_line = result['metadata']['macd_line']
        signal_line = result['metadata']['signal_line']
        histogram = result['metadata']['histogram']
        
        # MACD line should be above signal line in uptrend
        assert macd_line > signal_line, f"Expected MACD ({macd_line}) > Signal ({signal_line}) in uptrend"
        assert histogram > 0, f"Expected positive histogram ({histogram}) in uptrend"
        assert result['score'] < 0, f"Expected negative score (buy signal) in uptrend, got {result['score']}"
    
    def test_macd_bearish_conditions(self):
        """Test MACD bearish signal conditions."""
        # Create downtrending price sequence
        prices = [100 - i*0.5 for i in range(50)]  # Steady downtrend
        data = self.create_test_data(prices)
        signal = MACDSignal(fast_period=12, slow_period=26, signal_period=9)
        result = signal.calculate(data)
        
        # In downtrend, MACD should be bearish
        macd_line = result['metadata']['macd_line']
        signal_line = result['metadata']['signal_line']
        histogram = result['metadata']['histogram']
        
        # MACD line should be below signal line in downtrend
        assert macd_line < signal_line, f"Expected MACD ({macd_line}) < Signal ({signal_line}) in downtrend"
        assert histogram < 0, f"Expected negative histogram ({histogram}) in downtrend"
        assert result['score'] > 0, f"Expected positive score (sell signal) in downtrend, got {result['score']}"
    
    def test_macd_different_parameters(self):
        """Test MACD with different parameter sets."""
        prices = [50 + np.sin(i/10)*5 for i in range(100)]  # Oscillating prices
        data = self.create_test_data(prices)
        
        parameter_sets = [
            (12, 26, 9),   # Standard MACD
            (8, 17, 9),    # Faster MACD
            (19, 39, 9),   # Slower MACD
            (12, 26, 5)    # Faster signal
        ]
        
        for fast, slow, signal_period in parameter_sets:
            if len(prices) > slow + signal_period:  # Ensure sufficient data
                signal = MACDSignal(fast_period=fast, slow_period=slow, signal_period=signal_period)
                result = signal.calculate(data)
                
                # All should calculate successfully
                assert 'error' not in result['metadata'], f"MACD calculation failed for parameters {fast}/{slow}/{signal_period}"
                assert result['action'] in ['buy', 'sell', 'hold'], f"Invalid action for parameters {fast}/{slow}/{signal_period}"
                assert -1.0 <= result['score'] <= 1.0, f"Score out of range for parameters {fast}/{slow}/{signal_period}"
    
    def test_macd_score_range(self):
        """Test that MACD scores are always within -1.0 to 1.0 range."""
        # Test extreme price movements
        extreme_up = [10 + i*10 for i in range(50)]    # Very strong uptrend
        extreme_down = [500 - i*10 for i in range(50)] # Very strong downtrend
        
        signal = MACDSignal(fast_period=12, slow_period=26, signal_period=9)
        
        for prices in [extreme_up, extreme_down]:
            data = self.create_test_data(prices)
            result = signal.calculate(data)
            
            assert -1.0 <= result['score'] <= 1.0, f"MACD score {result['score']} out of range [-1, 1]"


class TestSignalAggregation:
    """Test signal aggregation and weighted scoring."""
    
    def create_mock_bot(self, signal_config: Dict[str, Any]) -> Bot:
        """Create mock bot with signal configuration."""
        bot = Bot()
        bot.id = 1
        bot.name = "Test Bot"
        bot.pair = "BTC-USD"
        bot.signal_config = json.dumps(signal_config)
        bot.confirmation_minutes = 5
        return bot
    
    def create_test_data(self, prices: list) -> pd.DataFrame:
        """Create test market data."""
        return pd.DataFrame({
            'close': prices,
            'timestamp': pd.date_range('2024-01-01', periods=len(prices), freq='1min')
        })
    
    def test_single_signal_aggregation(self):
        """Test aggregation with single enabled signal."""
        config = {
            'rsi': {
                'enabled': True,
                'weight': 1.0,
                'period': 14,
                'buy_threshold': 30,
                'sell_threshold': 70
            }
        }
        
        bot = self.create_mock_bot(config)
        # Create strongly overbought RSI scenario
        overbought_prices = [50] + [50 + i*2 for i in range(1, 20)]
        data = self.create_test_data(overbought_prices)
        
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        result = evaluator.evaluate_bot(bot, data)
        
        # Should match single RSI signal result
        assert result['action'] in ['buy', 'sell', 'hold']
        assert -1.0 <= result['overall_score'] <= 1.0
        assert 'rsi' in result['signal_results']
        assert result['overall_score'] == result['signal_results']['rsi']['score']
    
    def test_equal_weight_aggregation(self):
        """Test aggregation with equal-weight signals."""
        config = {
            'rsi': {
                'enabled': True,
                'weight': 0.5,
                'period': 14,
                'buy_threshold': 30,
                'sell_threshold': 70
            },
            'moving_average': {
                'enabled': True,
                'weight': 0.5,
                'fast_period': 10,
                'slow_period': 20
            }
        }
        
        bot = self.create_mock_bot(config)
        # Create scenario where both signals should agree (strong uptrend)
        uptrend_prices = [10 + i*0.5 for i in range(30)]
        data = self.create_test_data(uptrend_prices)
        
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        result = evaluator.evaluate_bot(bot, data)
        
        # Verify aggregation
        assert 'rsi' in result['signal_results']
        assert 'moving_average' in result['signal_results']
        
        rsi_score = result['signal_results']['rsi']['score']
        ma_score = result['signal_results']['moving_average']['score']
        expected_score = (rsi_score * 0.5) + (ma_score * 0.5)
        
        assert abs(result['overall_score'] - expected_score) < 0.001, f"Expected {expected_score}, got {result['overall_score']}"
    
    def test_unequal_weight_aggregation(self):
        """Test aggregation with different weight distributions."""
        # Test the recommended 0.4/0.4/0.2 weight distribution
        config = {
            'rsi': {
                'enabled': True,
                'weight': 0.4,
                'period': 14,
                'buy_threshold': 35,
                'sell_threshold': 65
            },
            'moving_average': {
                'enabled': True,
                'weight': 0.4,
                'fast_period': 12,
                'slow_period': 26
            },
            'macd': {
                'enabled': True,
                'weight': 0.2,
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            }
        }
        
        bot = self.create_mock_bot(config)
        # Use sufficient data for all signals
        prices = [50 + np.sin(i/10)*10 for i in range(50)]  # Oscillating with trend
        data = self.create_test_data(prices)
        
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        result = evaluator.evaluate_bot(bot, data)
        
        # Verify all signals calculated
        assert 'rsi' in result['signal_results']
        assert 'moving_average' in result['signal_results']
        assert 'macd' in result['signal_results']
        
        # Verify weighted aggregation
        rsi_score = result['signal_results']['rsi']['score']
        ma_score = result['signal_results']['moving_average']['score']
        macd_score = result['signal_results']['macd']['score']
        
        expected_score = (rsi_score * 0.4) + (ma_score * 0.4) + (macd_score * 0.2)
        
        assert abs(result['overall_score'] - expected_score) < 0.001, f"Expected {expected_score}, got {result['overall_score']}"
        assert result['metadata']['total_weight'] == 1.0, "Total weight should equal 1.0"
    
    def test_conflicting_signals(self):
        """Test aggregation when signals disagree."""
        # Create scenario where RSI says 'sell' but MA says 'buy'
        config = {
            'rsi': {
                'enabled': True,
                'weight': 0.6,
                'period': 14,
                'buy_threshold': 30,
                'sell_threshold': 70
            },
            'moving_average': {
                'enabled': True,
                'weight': 0.4,
                'fast_period': 5,
                'slow_period': 10
            }
        }
        
        bot = self.create_mock_bot(config)
        
        # Create conflicting scenario: recent uptrend (MA bullish) but high RSI (RSI bearish)
        base_prices = [45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55]  # Uptrend for MA
        # Add high-volatility end to push RSI high
        conflict_prices = base_prices + [65, 75, 85, 90, 85]  # Should make RSI overbought
        data = self.create_test_data(conflict_prices)
        
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        result = evaluator.evaluate_bot(bot, data)
        
        # Verify signals disagree
        rsi_score = result['signal_results']['rsi']['score']  
        ma_score = result['signal_results']['moving_average']['score']
        
        # RSI should be positive (sell), MA should be negative (buy) - they disagree
        # The aggregation should be weighted toward RSI (0.6 weight)
        expected_score = (rsi_score * 0.6) + (ma_score * 0.4)
        
        assert abs(result['overall_score'] - expected_score) < 0.001, "Conflicting signals not aggregated correctly"
    
    def test_weight_normalization(self):
        """Test that the system properly rejects invalid weight configurations."""
        # Configuration with weights that exceed 1.0 (should be rejected)
        config = {
            'RSI': {
                'enabled': True,
                'weight': 0.8,
                'period': 14,
                'oversold': 30,
                'overbought': 70
            },
            'MA': {
                'enabled': True,
                'weight': 0.8,  # Total weight = 1.6 (exceeds 1.0 limit)
                'fast_period': 10,
                'slow_period': 20
            }
        }
        
        bot = self.create_mock_bot(config)
        prices = [50] * 25  # Neutral prices
        data = self.create_test_data(prices)
        
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        result = evaluator.evaluate_bot(bot, data)
        
        # Should properly reject invalid weight configuration
        assert 'error' in result.get('metadata', {}), "System should reject weights exceeding 1.0"
        assert 'No enabled signals with valid weights' in result.get('metadata', {}).get('error', '')


class TestActionDetermination:
    """Test buy/sell/hold action determination from combined scores."""
    
    def test_buy_threshold(self):
        """Test buy action threshold (-0.1)."""
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        
        # Test scores around buy threshold
        test_cases = [
            (-1.0, 'buy'),    # Strong buy
            (-0.5, 'buy'),    # Moderate buy  
            (-0.11, 'buy'),   # Just above threshold
            (-0.1, 'buy'),    # Exactly at threshold
            (-0.09, 'hold'),  # Just below threshold
        ]
        
        for score, expected_action in test_cases:
            mock_bot = Bot()
            action = evaluator._determine_action(score, mock_bot)
            assert action == expected_action, f"Score {score} should produce '{expected_action}', got '{action}'"
    
    def test_sell_threshold(self):
        """Test sell action threshold (0.1)."""
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        
        # Test scores around sell threshold
        test_cases = [
            (1.0, 'sell'),    # Strong sell
            (0.5, 'sell'),    # Moderate sell
            (0.11, 'sell'),   # Just above threshold
            (0.1, 'sell'),    # Exactly at threshold
            (0.09, 'hold'),   # Just below threshold
        ]
        
        for score, expected_action in test_cases:
            mock_bot = Bot()
            action = evaluator._determine_action(score, mock_bot)
            assert action == expected_action, f"Score {score} should produce '{expected_action}', got '{action}'"
    
    def test_hold_zone(self):
        """Test hold zone between thresholds."""
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        
        # Scores in hold zone (-0.1 to 0.1)
        hold_scores = [-0.09, -0.05, 0, 0.05, 0.09]
        
        for score in hold_scores:
            mock_bot = Bot()
            action = evaluator._determine_action(score, mock_bot)
            assert action == 'hold', f"Score {score} should produce 'hold', got '{action}'"
    
    def test_threshold_configuration_impact(self):
        """Test how different thresholds would affect action determination."""
        # Note: Current implementation uses hardcoded thresholds
        # This test documents expected behavior and can guide future configurability
        
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        mock_bot = Bot()
        
        # Test edge cases with current thresholds (-0.1, 0.1)
        edge_cases = [
            (-0.1000001, 'buy'),
            (-0.1, 'buy'), 
            (-0.0999999, 'hold'),
            (0.0999999, 'hold'),
            (0.1, 'sell'),
            (0.1000001, 'sell')
        ]
        
        for score, expected in edge_cases:
            action = evaluator._determine_action(score, mock_bot)
            assert action == expected, f"Score {score} threshold test failed: expected {expected}, got {action}"


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""
    
    def test_empty_data(self):
        """Test signals with empty data."""
        empty_data = pd.DataFrame()
        
        signals = [
            RSISignal(period=14),
            MovingAverageSignal(fast_period=10, slow_period=20),
            MACDSignal(fast_period=12, slow_period=26, signal_period=9)
        ]
        
        for signal in signals:
            result = signal.calculate(empty_data)
            assert result['action'] == 'hold'
            assert result['score'] == 0
            assert result['confidence'] == 0
    
    def test_invalid_signal_configuration(self):
        """Test bot with invalid signal configuration."""
        bot = Bot()
        bot.signal_config = "invalid json"
        
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        data = pd.DataFrame({'close': [50, 51, 52], 'timestamp': pd.date_range('2024-01-01', periods=3)})
        
        result = evaluator.evaluate_bot(bot, data)
        assert result['action'] == 'hold'
        assert result['overall_score'] == 0
    
    def test_all_signals_disabled(self):
        """Test bot with all signals disabled."""
        config = {
            'rsi': {'enabled': False, 'weight': 0.5},
            'moving_average': {'enabled': False, 'weight': 0.5}
        }
        
        bot = Bot()
        bot.signal_config = json.dumps(config)
        
        evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
        data = pd.DataFrame({'close': [50, 51, 52], 'timestamp': pd.date_range('2024-01-01', periods=3)})
        
        result = evaluator.evaluate_bot(bot, data)
        assert result['action'] == 'hold'
        assert result['overall_score'] == 0
    
    def test_nan_handling_in_aggregation(self):
        """Test that NaN values are handled properly in aggregation."""
        # This would require mocking signals to return NaN, which is complex
        # For now, document expected behavior: NaN signals should be excluded from aggregation
        pass


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        __file__ + "::TestRSISignalCalculations",
        "-v"
    ])
