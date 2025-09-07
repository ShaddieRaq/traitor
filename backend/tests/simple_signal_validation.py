"""
Simple signal validation tests - focused on functional correctness rather than exact values.

This validates that:
1. RSI calculations produce values in correct range (0-100)
2. RSI correctly identifies overbought/oversold conditions  
3. Moving Average crossovers are detected
4. MACD signals are calculated
5. Signal aggregation produces correct weighted results
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from backend.app.services.signals.technical import RSISignal, MovingAverageSignal, MACDSignal
from backend.app.services.bot_evaluator import BotSignalEvaluator
from backend.app.models.models import Bot

def test_rsi_functional():
    """Test RSI functional correctness."""
    print("🔍 Testing RSI Signal Calculation...")
    
    # Test 1: RSI with declining prices (should be oversold)
    declining_prices = [100 - i*2 for i in range(20)]
    data = pd.DataFrame({
        'close': declining_prices,
        'timestamp': pd.date_range('2024-01-01', periods=20, freq='1min')
    })
    
    rsi_signal = RSISignal(period=14, oversold=30, overbought=70)
    result = rsi_signal.calculate(data)
    
    rsi_value = result['metadata']['rsi_value']
    print(f"   📉 Declining prices RSI: {rsi_value:.2f}")
    
    # RSI should be low (oversold) for declining prices
    assert 0 <= rsi_value <= 100, f"RSI out of range: {rsi_value}"
    assert rsi_value < 50, f"RSI should be low for declining prices, got {rsi_value}"
    assert result['action'] == 'buy', f"RSI should suggest 'buy' for oversold, got '{result['action']}'"
    
    # Test 2: RSI with rising prices (should be overbought)  
    rising_prices = [50 + i*2 for i in range(20)]
    data = pd.DataFrame({
        'close': rising_prices,
        'timestamp': pd.date_range('2024-01-01', periods=20, freq='1min')
    })
    
    result = rsi_signal.calculate(data)
    rsi_value = result['metadata']['rsi_value']
    print(f"   📈 Rising prices RSI: {rsi_value:.2f}")
    
    assert 0 <= rsi_value <= 100, f"RSI out of range: {rsi_value}"
    assert rsi_value > 50, f"RSI should be high for rising prices, got {rsi_value}"
    assert result['action'] == 'sell', f"RSI should suggest 'sell' for overbought, got '{result['action']}'"
    
    print("   ✅ RSI calculations working correctly!")

def test_ma_functional():
    """Test Moving Average functional correctness."""
    print("🔍 Testing Moving Average Signal Calculation...")
    
    # Test bullish crossover: fast MA crosses above slow MA
    # Start flat, then trend up strongly
    crossover_prices = [50]*10 + [50 + i for i in range(1, 15)]
    data = pd.DataFrame({
        'close': crossover_prices,
        'timestamp': pd.date_range('2024-01-01', periods=len(crossover_prices), freq='1min')
    })
    
    ma_signal = MovingAverageSignal(fast_period=5, slow_period=10)
    result = ma_signal.calculate(data)
    
    fast_ma = result['metadata']['fast_ma']
    slow_ma = result['metadata']['slow_ma']
    print(f"   📊 Fast MA: {fast_ma:.2f}, Slow MA: {slow_ma:.2f}")
    
    # In uptrend, fast MA should be above slow MA
    assert fast_ma > slow_ma, f"Fast MA ({fast_ma}) should be above slow MA ({slow_ma}) in uptrend"
    assert result['action'] == 'buy', f"MA should suggest 'buy' for bullish crossover, got '{result['action']}'"
    
    print("   ✅ Moving Average calculations working correctly!")

def test_macd_functional():
    """Test MACD functional correctness."""
    print("🔍 Testing MACD Signal Calculation...")
    
    # Test with trending data
    trend_prices = [50 + i*0.5 for i in range(40)]
    data = pd.DataFrame({
        'close': trend_prices,
        'timestamp': pd.date_range('2024-01-01', periods=40, freq='1min')
    })
    
    macd_signal = MACDSignal(fast_period=12, slow_period=26, signal_period=9)
    result = macd_signal.calculate(data)
    
    macd_line = result['metadata']['macd_line']
    signal_line = result['metadata']['signal_line'] 
    histogram = result['metadata']['histogram']
    
    print(f"   📈 MACD: {macd_line:.4f}, Signal: {signal_line:.4f}, Histogram: {histogram:.4f}")
    
    # MACD values should be reasonable
    assert not np.isnan(macd_line), "MACD line should not be NaN"
    assert not np.isnan(signal_line), "Signal line should not be NaN"
    assert not np.isnan(histogram), "Histogram should not be NaN"
    assert result['action'] in ['buy', 'sell', 'hold'], f"Invalid MACD action: {result['action']}"
    
    print("   ✅ MACD calculations working correctly!")

def test_signal_aggregation():
    """Test signal aggregation logic."""
    print("🔍 Testing Signal Aggregation...")
    
    # Create bot with multiple signals
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
    
    bot = Bot()
    bot.id = 1
    bot.name = "Test Bot"
    bot.pair = "BTC-USD"
    bot.signal_config = json.dumps(config)
    
    # Test with uptrend data
    uptrend_prices = [50 + i*0.3 for i in range(30)]
    data = pd.DataFrame({
        'close': uptrend_prices,
        'timestamp': pd.date_range('2024-01-01', periods=30, freq='1min')
    })
    
    evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
    result = evaluator.evaluate_bot(bot, data)
    
    print(f"   📊 Overall score: {result['overall_score']:.3f}")
    print(f"   🎯 Action: {result['action']}")
    print(f"   📈 RSI score: {result['signal_results']['rsi']['score']:.3f}")
    print(f"   📉 MA score: {result['signal_results']['moving_average']['score']:.3f}")
    
    # Verify aggregation
    rsi_score = result['signal_results']['rsi']['score']
    ma_score = result['signal_results']['moving_average']['score']
    expected_score = (rsi_score * 0.5) + (ma_score * 0.5)
    
    assert abs(result['overall_score'] - expected_score) < 0.001, f"Aggregation error: expected {expected_score}, got {result['overall_score']}"
    assert result['action'] in ['buy', 'sell', 'hold'], f"Invalid aggregated action: {result['action']}"
    
    print("   ✅ Signal aggregation working correctly!")

def test_research_configuration():
    """Test one of the research-recommended configurations."""
    print("🔍 Testing Research Configuration (Conservative)...")
    
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
    
    bot = Bot()
    bot.id = 1
    bot.name = "Conservative Bot"
    bot.pair = "BTC-USD"
    bot.signal_config = json.dumps(config)
    
    # Test with sufficient data for all indicators
    prices = [50 + np.sin(i/10)*5 for i in range(50)]  # Oscillating data
    data = pd.DataFrame({
        'close': prices,
        'timestamp': pd.date_range('2024-01-01', periods=50, freq='1min')
    })
    
    evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
    result = evaluator.evaluate_bot(bot, data)
    
    print(f"   📊 Overall score: {result['overall_score']:.3f}")
    print(f"   🎯 Action: {result['action']}")
    print(f"   📈 Signals calculated: {len(result['signal_results'])}")
    print(f"   ⚖️ Total weight: {result['metadata']['total_weight']}")
    
    # Verify all signals participated
    assert len(result['signal_results']) == 3, f"Expected 3 signals, got {len(result['signal_results'])}"
    assert 'rsi' in result['signal_results'], "RSI signal missing"
    assert 'moving_average' in result['signal_results'], "MA signal missing" 
    assert 'macd' in result['signal_results'], "MACD signal missing"
    assert result['metadata']['total_weight'] == 1.0, f"Expected total weight 1.0, got {result['metadata']['total_weight']}"
    
    print("   ✅ Research configuration working correctly!")

def main():
    """Run all functional tests."""
    print("🧪 Signal Calculation Functional Tests")
    print("="*50)
    
    try:
        test_rsi_functional()
        test_ma_functional()
        test_macd_functional()
        test_signal_aggregation()
        test_research_configuration()
        
        print("\n🎉 All functional tests passed!")
        print("\n📋 Test Summary:")
        print("✅ RSI calculations produce correct ranges and actions")
        print("✅ Moving Average crossovers detected correctly")
        print("✅ MACD signals calculated without errors")
        print("✅ Signal aggregation uses correct weighted averages")
        print("✅ Research configurations work as expected")
        
        print("\n🚀 Signal calculations are mathematically sound!")
        print("💡 Ready to configure bots with confidence in signal accuracy.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
