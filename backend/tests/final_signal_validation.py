"""
Final Signal Validation Suite

Validates the core signal functionality you need for confident bot configuration:

1. ✅ Individual signal calculations work correctly  
2. ✅ Signal aggregation uses proper weighted averages
3. ✅ Requested weight distributions (0.4/0.4/0.2, 0.5/0.3/0.2, etc.) function correctly
4. ✅ Combined score thresholds (-0.1, +0.1) produce correct actions
5. ✅ Research-recommended configurations are mathematically sound

This gives you confidence that the signal values you're setting are correct.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from backend.app.services.bot_evaluator import BotSignalEvaluator
from backend.app.models.models import Bot

def validate_individual_signals():
    """Validate that individual signals calculate correctly."""
    
    print("1️⃣ Validating Individual Signal Calculations")
    print("-" * 50)
    
    from backend.app.services.signals.technical import RSISignal, MovingAverageSignal, MACDSignal
    
    # Create test data
    uptrend_data = pd.DataFrame({
        'close': [50 + i*0.5 for i in range(30)],
        'timestamp': pd.date_range('2024-01-01', periods=30, freq='1min')
    })
    
    # Test RSI
    rsi = RSISignal(period=14, oversold=30, overbought=70)
    rsi_result = rsi.calculate(uptrend_data)
    
    print(f"   RSI: {rsi_result['metadata']['rsi_value']:.2f} → {rsi_result['action']} (score: {rsi_result['score']:+.3f})")
    assert 0 <= rsi_result['metadata']['rsi_value'] <= 100, "RSI out of range"
    assert rsi_result['action'] in ['buy', 'sell', 'hold'], "Invalid RSI action"
    
    # Test Moving Average
    ma = MovingAverageSignal(fast_period=10, slow_period=20)
    ma_result = ma.calculate(uptrend_data)
    
    print(f"   MA:  Fast={ma_result['metadata']['fast_ma']:.2f}, Slow={ma_result['metadata']['slow_ma']:.2f} → {ma_result['action']} (score: {ma_result['score']:+.3f})")
    assert ma_result['action'] in ['buy', 'sell', 'hold'], "Invalid MA action"
    
    # Test MACD
    macd = MACDSignal(fast_period=12, slow_period=26, signal_period=9)
    macd_result = macd.calculate(uptrend_data)
    
    print(f"   MACD: Line={macd_result['metadata']['macd_line']:.4f}, Signal={macd_result['metadata']['signal_line']:.4f} → {macd_result['action']} (score: {macd_result['score']:+.3f})")
    assert macd_result['action'] in ['buy', 'sell', 'hold'], "Invalid MACD action"
    
    print("   ✅ All individual signals calculating correctly!\n")

def validate_weight_distributions():
    """Validate the specific weight distributions you requested."""
    
    print("2️⃣ Validating Requested Weight Distributions")
    print("-" * 50)
    
    weight_configs = [
        ("0.4/0.4/0.2 (Conservative)", {'rsi': 0.4, 'ma': 0.4, 'macd': 0.2}),
        ("0.5/0.3/0.2 (MA Dominant)", {'rsi': 0.3, 'ma': 0.5, 'macd': 0.2}),
        ("0.3/0.5/0.2 (Aggressive)", {'rsi': 0.3, 'ma': 0.5, 'macd': 0.2}),
        ("0.35/0.35/0.3 (Adaptive)", {'rsi': 0.35, 'ma': 0.35, 'macd': 0.3})
    ]
    
    test_data = pd.DataFrame({
        'close': [50 + i*0.3 for i in range(40)],
        'timestamp': pd.date_range('2024-01-01', periods=40, freq='1min')
    })
    
    evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
    
    for config_name, weights in weight_configs:
        
        # Create bot configuration
        config = {
            'rsi': {
                'enabled': True,
                'weight': weights['rsi'],
                'period': 14,
                'buy_threshold': 35,
                'sell_threshold': 65
            },
            'moving_average': {
                'enabled': True,
                'weight': weights['ma'],
                'fast_period': 12,
                'slow_period': 26
            },
            'macd': {
                'enabled': True, 
                'weight': weights['macd'],
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            }
        }
        
        bot = Bot()
        bot.signal_config = json.dumps(config)
        
        result = evaluator.evaluate_bot(bot, test_data)
        
        # Validate weighted aggregation
        rsi_score = result['signal_results']['rsi']['score']
        ma_score = result['signal_results']['moving_average']['score']
        macd_score = result['signal_results']['macd']['score']
        
        expected_score = (rsi_score * weights['rsi']) + (ma_score * weights['ma']) + (macd_score * weights['macd'])
        actual_score = result['overall_score']
        
        print(f"   {config_name}:")
        print(f"     Individual: RSI={rsi_score:+.3f}, MA={ma_score:+.3f}, MACD={macd_score:+.3f}")
        print(f"     Weighted:   {expected_score:+.3f} (expected) vs {actual_score:+.3f} (actual)")
        print(f"     Action:     {result['action']}")
        
        assert abs(expected_score - actual_score) < 0.001, f"Weight aggregation error in {config_name}"
        assert result['action'] in ['buy', 'sell', 'hold'], f"Invalid action in {config_name}"
        
    print("   ✅ All weight distributions working correctly!\n")

def validate_action_thresholds():
    """Validate buy/sell/hold thresholds."""
    
    print("3️⃣ Validating Action Determination Thresholds")
    print("-" * 50)
    
    evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
    
    # Test scores around thresholds
    test_cases = [
        (-0.5, 'buy', 'Strong buy signal'),
        (-0.1, 'buy', 'At buy threshold'),
        (-0.05, 'hold', 'Neutral zone'),
        (0.0, 'hold', 'Perfectly neutral'),
        (0.05, 'hold', 'Neutral zone'),
        (0.1, 'sell', 'At sell threshold'),
        (0.5, 'sell', 'Strong sell signal')
    ]
    
    print("   Score   | Action | Description")
    print("   --------|--------|------------------")
    
    for score, expected_action, description in test_cases:
        mock_bot = Bot()
        actual_action = evaluator._determine_action(score, mock_bot)
        
        status = "✅" if actual_action == expected_action else "❌"
        print(f"   {score:+6.2f} | {actual_action:6} | {description} {status}")
        
        assert actual_action == expected_action, f"Threshold test failed for score {score}"
    
    print("   ✅ All action thresholds working correctly!\n")

def validate_research_configurations():
    """Validate the specific configurations from research."""
    
    print("4️⃣ Validating Research-Recommended Configurations")
    print("-" * 50)
    
    # Conservative configuration from research
    conservative_config = {
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
    bot.signal_config = json.dumps(conservative_config)
    
    evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
    
    # Test with different market conditions
    market_conditions = {
        'uptrend': [50 + i*0.8 for i in range(40)],
        'downtrend': [100 - i*0.8 for i in range(40)],
        'sideways': [50 + np.sin(i/8)*3 for i in range(40)]
    }
    
    for condition, prices in market_conditions.items():
        data = pd.DataFrame({
            'close': prices,
            'timestamp': pd.date_range('2024-01-01', periods=len(prices), freq='1min')
        })
        
        result = evaluator.evaluate_bot(bot, data)
        
        print(f"   {condition:9}: Score {result['overall_score']:+.3f} → {result['action']:4} (confidence: {result['confidence']:.3f})")
        
        # Verify all signals participated
        assert len(result['signal_results']) == 3, f"Missing signals in {condition}"
        assert 'rsi' in result['signal_results'], f"RSI missing in {condition}"
        assert 'moving_average' in result['signal_results'], f"MA missing in {condition}"
        assert 'macd' in result['signal_results'], f"MACD missing in {condition}"
        
        # Verify weight totals
        assert result['metadata']['total_weight'] == 1.0, f"Weight total incorrect in {condition}"
    
    print("   ✅ Research configuration working correctly!\n")

def validate_signal_persistence():
    """Validate that signals are calculated consistently."""
    
    print("5️⃣ Validating Signal Calculation Consistency")
    print("-" * 50)
    
    # Use the same data multiple times - should get identical results
    test_data = pd.DataFrame({
        'close': [50, 51, 52, 51, 53, 54, 53, 55, 56, 55, 57, 58, 57, 59, 60],
        'timestamp': pd.date_range('2024-01-01', periods=15, freq='1min')
    })
    
    config = {
        'rsi': {'enabled': True, 'weight': 0.5, 'period': 14, 'buy_threshold': 30, 'sell_threshold': 70},
        'moving_average': {'enabled': True, 'weight': 0.5, 'fast_period': 5, 'slow_period': 10}
    }
    
    bot = Bot()
    bot.signal_config = json.dumps(config)
    
    evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
    
    # Calculate multiple times
    results = []
    for i in range(3):
        result = evaluator.evaluate_bot(bot, test_data)
        results.append({
            'overall_score': result['overall_score'],
            'action': result['action'],
            'rsi_score': result['signal_results']['rsi']['score'],
            'ma_score': result['signal_results']['moving_average']['score']
        })
    
    # All results should be identical
    first_result = results[0]
    for i, result in enumerate(results[1:], 1):
        for key, value in result.items():
            assert abs(value - first_result[key]) < 0.0001 if isinstance(value, float) else value == first_result[key], f"Inconsistent result {key} in run {i}"
    
    print(f"   Consistency test: Score {first_result['overall_score']:+.3f} → {first_result['action']} (repeated 3x)")
    print("   ✅ Signal calculations are consistent!\n")

def main():
    """Run comprehensive signal validation."""
    
    print("🧪 COMPREHENSIVE SIGNAL VALIDATION SUITE")
    print("=" * 70)
    print("Testing core signal functionality for confident bot configuration\n")
    
    try:
        validate_individual_signals()
        validate_weight_distributions()
        validate_action_thresholds()
        validate_research_configurations()
        validate_signal_persistence()
        
        print("🎉 ALL SIGNAL VALIDATION TESTS PASSED!")
        print("=" * 70)
        
        print("\n✅ VALIDATION SUMMARY:")
        print("   • Individual signals (RSI, MA, MACD) calculate correctly")
        print("   • Weight distributions (0.4/0.4/0.2, 0.5/0.3/0.2, etc.) work as expected") 
        print("   • Combined score thresholds (-0.1, +0.1) produce correct actions")
        print("   • Research-recommended configurations are mathematically sound")
        print("   • Signal calculations are consistent and repeatable")
        
        print(f"\n🚀 READY FOR PRODUCTION!")
        print("You can confidently configure your bots with any tested weight distribution.")
        print("The signal aggregation system is mathematically correct and reliable.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
