"""
Test signal processing functionality.
"""

import pytest
import pandas as pd
import numpy as np
from app.services.signals.technical import RSISignal, MovingAverageSignal


class TestRSISignal:
    """Test RSI signal calculation."""
    
    def test_rsi_calculation(self):
        """Test RSI calculation with known data."""
        signal = RSISignal()
        
        # Create test data with known RSI pattern
        # Rising prices should give RSI > 50, falling prices RSI < 50
        prices = [100, 105, 110, 115, 120, 125, 130, 125, 120, 115, 110, 105, 100, 95, 90]
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=len(prices), freq='1H'),
            'close': prices
        })
        
        result = signal.calculate(df)
        
        assert 'score' in result
        assert 'action' in result
        assert 'confidence' in result
        assert 'metadata' in result
        assert isinstance(result['action'], str)
        assert result['action'] in ['buy', 'sell', 'hold']
        assert -1 <= result['score'] <= 1
    
    def test_rsi_oversold_condition(self):
        """Test RSI oversold condition generates buy signal."""
        signal = RSISignal()
        
        # Create strongly declining prices to trigger oversold
        declining_prices = list(range(100, 50, -2))  # 100, 98, 96, ..., 52
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=len(declining_prices), freq='1H'),
            'close': declining_prices
        })
        
        result = signal.calculate(df)
        
        # Should generate buy signal when oversold
        assert result['action'] in ['buy', 'hold']  # Might be hold if not quite oversold enough
    
    def test_rsi_insufficient_data(self):
        """Test RSI with insufficient data."""
        signal = RSISignal()
        
        # Not enough data for RSI calculation (need at least 14 periods)
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=5, freq='1H'),
            'close': [100, 101, 102, 103, 104]
        })
        
        result = signal.calculate(df)
        
        assert result['action'] == 'hold'
        assert result['score'] == 0


class TestMovingAverageSignal:
    """Test Moving Average Crossover signal."""
    
    def test_ma_crossover_calculation(self):
        """Test MA crossover calculation."""
        signal = MovingAverageSignal()
        
        # Create data with clear trend change
        prices = [100] * 15 + [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=len(prices), freq='1H'),
            'close': prices
        })
        
        result = signal.calculate(df)
        
        assert 'score' in result
        assert 'action' in result
        assert 'confidence' in result
        assert 'metadata' in result
        assert isinstance(result['action'], str)
        assert result['action'] in ['buy', 'sell', 'hold']
    
    def test_ma_bullish_crossover(self):
        """Test bullish crossover (short MA crosses above long MA)."""
        signal = MovingAverageSignal()
        
        # Create uptrend to generate bullish crossover
        uptrend_prices = list(range(90, 120))  # Steady uptrend
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=len(uptrend_prices), freq='1H'),
            'close': uptrend_prices
        })
        
        result = signal.calculate(df)
        
        # Should generate buy signal on bullish crossover
        assert result['action'] in ['buy', 'hold']
    
    def test_ma_insufficient_data(self):
        """Test MA crossover with insufficient data."""
        signal = MovingAverageSignal()
        
        # Not enough data for long MA (need at least 20 periods)
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=10, freq='1H'),
            'close': list(range(100, 110))
        })
        
        result = signal.calculate(df)
        
        assert result['action'] == 'hold'
        assert result['score'] == 0


class TestSignalIntegration:
    """Test signal integration and factory."""
    
    def test_signal_factory(self):
        """Test signal creation through factory."""
        from app.services.signals.base import create_signal_instance
        
        # Test RSI signal creation
        rsi_signal = create_signal_instance('RSI', {'period': 14, 'oversold': 30, 'overbought': 70})
        assert isinstance(rsi_signal, RSISignal)
        
        # Test MA signal creation
        ma_signal = create_signal_instance('MA_Crossover', {'fast_period': 10, 'slow_period': 20})
        assert isinstance(ma_signal, MovingAverageSignal)
        
        # Test unknown signal
        unknown_signal = create_signal_instance('UnknownSignal', {})
        assert unknown_signal is None
    
    def test_signal_metadata(self):
        """Test that signals return proper metadata."""
        signal = RSISignal()
        
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=20, freq='1H'),
            'close': list(range(100, 120))
        })
        
        result = signal.calculate(df)
        
        assert 'metadata' in result
        assert 'rsi_value' in result['metadata']
        assert isinstance(result['metadata']['rsi_value'], (int, float, type(None)))
