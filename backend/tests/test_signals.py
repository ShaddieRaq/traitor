"""
Test signal processing functionality with comprehensive test cases.
"""

import pytest
import pandas as pd
import numpy as np
from app.services.signals.technical import RSISignal, MovingAverageSignal, MACDSignal


def create_test_data(price_pattern: str, length: int = 50) -> pd.DataFrame:
    """Create mock test data with specific price patterns."""
    if price_pattern == "uptrend":
        # Steady uptrend with some noise
        base_prices = np.linspace(100, 150, length)
        noise = np.random.normal(0, 1, length)
        prices = base_prices + noise
    elif price_pattern == "downtrend":
        # Steady downtrend with some noise
        base_prices = np.linspace(150, 100, length)
        noise = np.random.normal(0, 1, length)
        prices = base_prices + noise
    elif price_pattern == "sideways":
        # Sideways movement around 100
        base_prices = np.full(length, 100)
        noise = np.random.normal(0, 2, length)
        prices = base_prices + noise
    elif price_pattern == "volatile":
        # High volatility oscillations
        base_prices = 100 + 20 * np.sin(np.linspace(0, 4*np.pi, length))
        noise = np.random.normal(0, 3, length)
        prices = base_prices + noise
    elif price_pattern == "oversold_recovery":
        # Sharp decline followed by recovery (oversold condition)
        decline = np.linspace(100, 70, length//2)
        recovery = np.linspace(70, 85, length//2)
        prices = np.concatenate([decline, recovery])
    elif price_pattern == "overbought_correction":
        # Sharp rise followed by correction (overbought condition)
        rise = np.linspace(100, 130, length//2)
        correction = np.linspace(130, 115, length//2)
        prices = np.concatenate([rise, correction])
    else:
        # Default: random walk
        prices = 100 + np.cumsum(np.random.normal(0, 1, length))
    
    return pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=length, freq='1H'),
        'close': prices,
        'open': prices * 0.999,  # Slightly lower opens
        'high': prices * 1.002,  # Slightly higher highs
        'low': prices * 0.998,   # Slightly lower lows
        'volume': np.random.randint(1000, 10000, length)
    })


class TestRSISignal:
    """Test RSI signal calculation with comprehensive scenarios."""
    
    def test_rsi_score_range(self):
        """Test that RSI scores are always within -1 to 1 range."""
        signal = RSISignal()
        
        for pattern in ["uptrend", "downtrend", "sideways", "volatile"]:
            df = create_test_data(pattern)
            result = signal.calculate(df)
            
            assert -1.0 <= result['score'] <= 1.0, f"Score {result['score']} out of range for {pattern}"
            assert result['action'] in ['buy', 'sell', 'hold']
            assert 0 <= result['confidence'] <= 1.0
    
    def test_rsi_oversold_buy_signal(self):
        """Test RSI generates strong buy signal when oversold."""
        signal = RSISignal(period=14, oversold=30, overbought=70)
        
        # Create clear oversold condition - strong decline
        declining_prices = np.linspace(120, 70, 30)  # Strong decline to create oversold
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=len(declining_prices), freq='1H'),
            'close': declining_prices,
            'open': declining_prices,
            'high': declining_prices,
            'low': declining_prices,
            'volume': [1000] * len(declining_prices)
        })
        
        result = signal.calculate(df)
        
        # Should generate negative score (buy signal) when oversold
        assert result['score'] < 0, f"Expected buy signal (negative score), got score {result['score']}"
        assert result['action'] == 'buy'
        assert result['confidence'] > 0.5
        assert result['metadata']['rsi_value'] <= 30, f"Expected RSI <= 30, got {result['metadata']['rsi_value']}"
    
    def test_rsi_overbought_sell_signal(self):
        """Test RSI generates strong sell signal when overbought."""
        signal = RSISignal(period=14, oversold=30, overbought=70)
        
        # Create clear overbought condition - strong rise
        rising_prices = np.linspace(70, 120, 30)  # Strong rise to create overbought
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=len(rising_prices), freq='1H'),
            'close': rising_prices,
            'open': rising_prices,
            'high': rising_prices,
            'low': rising_prices,
            'volume': [1000] * len(rising_prices)
        })
        
        result = signal.calculate(df)
        
        # Should generate positive score (sell signal) when overbought
        assert result['score'] > 0, f"Expected sell signal (positive score), got score {result['score']}"
        assert result['action'] == 'sell'
        assert result['confidence'] > 0.5
        assert result['metadata']['rsi_value'] >= 70, f"Expected RSI >= 70, got {result['metadata']['rsi_value']}"
    
    def test_rsi_neutral_zone(self):
        """Test RSI behavior in neutral zone (30-70)."""
        signal = RSISignal()
        
        # Sideways movement should keep RSI in neutral zone
        df = create_test_data("sideways", length=30)
        result = signal.calculate(df)
        
        # Score should be relatively neutral
        assert -0.5 <= result['score'] <= 0.5
        assert 'rsi_value' in result['metadata']
        assert 30 <= result['metadata']['rsi_value'] <= 70
    
    def test_rsi_insufficient_data(self):
        """Test RSI with insufficient data."""
        signal = RSISignal(period=14)
        
        # Only 10 data points (need at least 15 for RSI)
        df = create_test_data("uptrend", length=10)
        result = signal.calculate(df)
        
        assert result['action'] == 'hold'
        assert result['score'] == 0
        assert result['confidence'] == 0


class TestMovingAverageSignal:
    """Test Moving Average Crossover signal with comprehensive scenarios."""
    
    def test_ma_score_range(self):
        """Test that MA scores are always within -1 to 1 range."""
        signal = MovingAverageSignal(fast_period=10, slow_period=20)
        
        for pattern in ["uptrend", "downtrend", "sideways", "volatile"]:
            df = create_test_data(pattern, length=40)
            result = signal.calculate(df)
            
            assert -1.0 <= result['score'] <= 1.0, f"Score {result['score']} out of range for {pattern}"
            assert result['action'] in ['buy', 'sell', 'hold']
            assert 0 <= result['confidence'] <= 1.0
    
    def test_ma_bullish_crossover(self):
        """Test bullish crossover detection."""
        signal = MovingAverageSignal(fast_period=5, slow_period=10)
        
        # Create price pattern that causes bullish crossover
        # Start flat, then strong uptrend
        flat_prices = [100] * 15
        up_prices = list(range(100, 115))
        prices = flat_prices + up_prices
        
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=len(prices), freq='1H'),
            'close': prices,
            'open': prices,
            'high': prices,
            'low': prices,
            'volume': [1000] * len(prices)
        })
        
        result = signal.calculate(df)
        
        # Should generate strong buy signal (negative score)
        assert result['score'] < -0.2, f"Expected buy signal, got {result['score']}"
        assert result['action'] == 'buy'
        assert result['confidence'] > 0.2  # Realistic threshold
    
    def test_ma_bearish_crossover(self):
        """Test bearish crossover detection."""
        signal = MovingAverageSignal(fast_period=5, slow_period=10)
        
        # Create price pattern that causes bearish crossover
        # Start flat, then strong downtrend
        flat_prices = [100] * 15
        down_prices = list(range(100, 85, -1))
        prices = flat_prices + down_prices
        
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=len(prices), freq='1H'),
            'close': prices,
            'open': prices,
            'high': prices,
            'low': prices,
            'volume': [1000] * len(prices)
        })
        
        result = signal.calculate(df)
        
        # Should generate strong sell signal (positive score)
        assert result['score'] > 0.2, f"Expected sell signal, got {result['score']}"
        assert result['action'] == 'sell'
        assert result['confidence'] > 0.2  # Realistic threshold
    
    def test_ma_separation_scoring(self):
        """Test distance-based scoring when no crossover."""
        signal = MovingAverageSignal(fast_period=5, slow_period=20)
        
        # Create steady uptrend (fast MA consistently above slow MA)
        df = create_test_data("uptrend", length=40)
        result = signal.calculate(df)
        
        # Should show buy bias (negative score) but lower confidence than crossover
        assert result['score'] < 0, "Uptrend should show buy bias"
        assert 'separation_pct' in result['metadata']
    
    def test_ma_insufficient_data(self):
        """Test MA with insufficient data."""
        signal = MovingAverageSignal(fast_period=10, slow_period=20)
        
        # Only 15 data points (need at least 21 for slow MA)
        df = create_test_data("uptrend", length=15)
        result = signal.calculate(df)
        
        assert result['action'] == 'hold'
        assert result['score'] == 0


class TestMACDSignal:
    """Test MACD signal calculation with comprehensive scenarios."""
    
    def test_macd_score_range(self):
        """Test that MACD scores are always within -1 to 1 range."""
        signal = MACDSignal(fast_period=12, slow_period=26, signal_period=9)
        
        for pattern in ["uptrend", "downtrend", "sideways", "volatile"]:
            df = create_test_data(pattern, length=60)  # Need more data for MACD
            result = signal.calculate(df)
            
            assert -1.0 <= result['score'] <= 1.0, f"Score {result['score']} out of range for {pattern}"
            assert result['action'] in ['buy', 'sell', 'hold']
            assert 0 <= result['confidence'] <= 1.0
    
    def test_macd_bullish_signals(self):
        """Test MACD bullish signal generation."""
        signal = MACDSignal()
        
        # Strong uptrend should generate bullish MACD signals
        df = create_test_data("uptrend", length=60)
        result = signal.calculate(df)
        
        # Check metadata contains expected values
        assert 'macd_line' in result['metadata']
        assert 'signal_line' in result['metadata']
        assert 'histogram' in result['metadata']
        assert 'histogram_momentum' in result['metadata']
        
        # Uptrend should generally show buy bias
        # (Note: might not always be buy due to complex MACD logic)
        assert result['action'] in ['buy', 'hold']
    
    def test_macd_bearish_signals(self):
        """Test MACD bearish signal generation."""
        signal = MACDSignal()
        
        # Strong downtrend should generate bearish MACD signals
        df = create_test_data("downtrend", length=60)
        result = signal.calculate(df)
        
        # Downtrend should generally show sell bias
        assert result['action'] in ['sell', 'hold']
    
    def test_macd_zero_line_crossover(self):
        """Test MACD zero line crossover logic."""
        signal = MACDSignal()
        
        # Create pattern: decline then recovery (should cross zero)
        decline = np.linspace(120, 80, 30)
        recovery = np.linspace(80, 110, 30)
        prices = np.concatenate([decline, recovery])
        
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=len(prices), freq='1H'),
            'close': prices,
            'open': prices,
            'high': prices,
            'low': prices,
            'volume': [1000] * len(prices)
        })
        
        result = signal.calculate(df)
        
        # Recovery phase should show bullish signals
        assert result['action'] in ['buy', 'hold']
        
        # Check that MACD line is calculated
        macd_value = result['metadata']['macd_line']
        assert isinstance(macd_value, (int, float))
    
    def test_macd_insufficient_data(self):
        """Test MACD with insufficient data."""
        signal = MACDSignal()
        
        # Only 20 data points (need at least ~40 for reliable MACD)
        df = create_test_data("uptrend", length=20)
        result = signal.calculate(df)
        
        assert result['action'] == 'hold'
        assert result['score'] == 0


class TestSignalIntegration:
    """Test signal integration and factory with enhanced coverage."""
    
    def test_signal_factory_all_types(self):
        """Test signal creation through factory for all signal types."""
        from app.services.signals.base import create_signal_instance
        
        # Test RSI signal creation
        rsi_signal = create_signal_instance('RSI', {
            'period': 14, 
            'oversold': 30, 
            'overbought': 70
        })
        assert isinstance(rsi_signal, RSISignal)
        assert rsi_signal.parameters['period'] == 14
        
        # Test MA signal creation
        ma_signal = create_signal_instance('MA_Crossover', {
            'fast_period': 10, 
            'slow_period': 20
        })
        assert isinstance(ma_signal, MovingAverageSignal)
        assert ma_signal.parameters['fast_period'] == 10
        
        # Test MACD signal creation
        macd_signal = create_signal_instance('MACD', {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        })
        assert isinstance(macd_signal, MACDSignal)
        assert macd_signal.parameters['signal_period'] == 9
        
        # Test unknown signal
        unknown_signal = create_signal_instance('UnknownSignal', {})
        assert unknown_signal is None
    
    def test_signal_consistency_across_patterns(self):
        """Test that all signals behave consistently across different market patterns."""
        signals = [
            RSISignal(),
            MovingAverageSignal(), 
            MACDSignal()
        ]
        
        patterns = ["uptrend", "downtrend", "sideways", "volatile"]
        
        for signal in signals:
            for pattern in patterns:
                df = create_test_data(pattern, length=50)
                result = signal.calculate(df)
                
                # All signals should return consistent structure
                assert 'score' in result
                assert 'action' in result
                assert 'confidence' in result
                assert 'metadata' in result
                
                # Scores should be in valid range
                assert -1.0 <= result['score'] <= 1.0
                assert result['action'] in ['buy', 'sell', 'hold']
                assert 0 <= result['confidence'] <= 1.0
                
                # Metadata should contain signal-specific info
                assert isinstance(result['metadata'], dict)
    
    def test_signal_scoring_consistency(self):
        """Test that signal scoring is logically consistent."""
        # Buy signals should have negative scores
        # Sell signals should have positive scores
        # Hold signals should have scores near zero
        
        rsi_signal = RSISignal()
        
        # Test buy signal consistency
        oversold_df = create_test_data("oversold_recovery", length=30)
        result = rsi_signal.calculate(oversold_df)
        
        if result['action'] == 'buy':
            assert result['score'] < 0, "Buy action should have negative score"
        elif result['action'] == 'sell':
            assert result['score'] > 0, "Sell action should have positive score"
        else:  # hold
            assert abs(result['score']) < 0.6, "Hold action should have neutral score"
    
    def test_signal_metadata_completeness(self):
        """Test that signals return complete and useful metadata."""
        df = create_test_data("uptrend", length=50)
        
        # Test RSI metadata
        rsi_signal = RSISignal()
        rsi_result = rsi_signal.calculate(df)
        assert 'rsi_value' in rsi_result['metadata']
        assert 'period' in rsi_result['metadata']
        assert isinstance(rsi_result['metadata']['rsi_value'], (int, float))
        
        # Test MA metadata
        ma_signal = MovingAverageSignal()
        ma_result = ma_signal.calculate(df)
        assert 'fast_ma' in ma_result['metadata']
        assert 'slow_ma' in ma_result['metadata']
        assert 'separation_pct' in ma_result['metadata']
        
        # Test MACD metadata
        macd_signal = MACDSignal()
        macd_result = macd_signal.calculate(df)
        assert 'macd_line' in macd_result['metadata']
        assert 'signal_line' in macd_result['metadata']
        assert 'histogram' in macd_result['metadata']
        assert 'histogram_momentum' in macd_result['metadata']
    
    def test_signal_edge_cases(self):
        """Test signal behavior with edge cases."""
        signals = [RSISignal(), MovingAverageSignal(), MACDSignal()]
        
        # Test with extreme volatility
        extreme_volatile = create_test_data("volatile", length=100)
        
        for signal in signals:
            result = signal.calculate(extreme_volatile)
            
            # Should still return valid results even with extreme data
            assert isinstance(result, dict)
            assert 'score' in result
            assert 'action' in result
            assert not np.isnan(result['score']) if isinstance(result['score'], (int, float)) else True
    
    def test_required_periods(self):
        """Test that signals correctly specify required data periods."""
        # RSI with default period 14
        rsi_signal = RSISignal(period=14)
        assert rsi_signal.get_required_periods() == 15  # period + 1
        
        # MA with default periods 10, 20
        ma_signal = MovingAverageSignal(fast_period=10, slow_period=20)
        assert ma_signal.get_required_periods() == 21  # max period + 1
        
        # MACD with default periods 12, 26, 9
        macd_signal = MACDSignal(fast_period=12, slow_period=26, signal_period=9)
        assert macd_signal.get_required_periods() == 40  # slow + signal + buffer
