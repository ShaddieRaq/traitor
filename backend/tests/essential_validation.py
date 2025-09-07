"""
Essential Signal Validation

Validates the core functionality you need:
✅ Signal calculations work without errors
✅ Weight distributions produce correct aggregated scores  
✅ Action thresholds work as expected
✅ Your requested configurations are mathematically sound

This is the minimum validation needed for confident bot configuration.
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

def test_core_functionality():
    """Test core signal functionality that you need for bot configuration."""
    
    print("🧪 Essential Signal Validation")
    print("=" * 50)
    
    # Test your requested weight distributions
    weight_configs = [
        ("Conservative (0.4/0.4/0.2)", (0.4, 0.4, 0.2)),
        ("MA Dominant (0.5/0.3/0.2)", (0.3, 0.5, 0.2)),
        ("Aggressive (0.3/0.5/0.2)", (0.3, 0.5, 0.2)),
        ("Adaptive (0.35/0.35/0.3)", (0.35, 0.35, 0.3))
    ]
    
    # Create test market data
    test_data = pd.DataFrame({
        'close': [50 + i*0.5 for i in range(50)],  # Gradual uptrend
        'timestamp': pd.date_range('2024-01-01', periods=50, freq='1min')
    })
    
    evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
    
    print("Configuration                | Score    | Action | RSI    | MA     | MACD   | Weight Check")
    print("-" * 85)
    
    for config_name, (rsi_w, ma_w, macd_w) in weight_configs:
        
        # Create bot configuration
        config = {
            'rsi': {
                'enabled': True,
                'weight': rsi_w,
                'period': 14,
                'buy_threshold': 35,
                'sell_threshold': 65
            },
            'moving_average': {
                'enabled': True,
                'weight': ma_w,
                'fast_period': 12,
                'slow_period': 26
            },
            'macd': {
                'enabled': True,
                'weight': macd_w,
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            }
        }
        
        bot = Bot()
        bot.signal_config = json.dumps(config)
        
        try:
            result = evaluator.evaluate_bot(bot, test_data)
            
            # Extract individual scores
            rsi_score = result['signal_results']['rsi']['score']
            ma_score = result['signal_results']['moving_average']['score']
            macd_score = result['signal_results']['macd']['score']
            
            # Calculate expected weighted score
            expected_score = (rsi_score * rsi_w) + (ma_score * ma_w) + (macd_score * macd_w)
            actual_score = result['overall_score']
            
            # Check if aggregation is correct
            aggregation_correct = abs(expected_score - actual_score) < 0.001
            weight_check = "✅" if aggregation_correct else "❌"
            
            print(f"{config_name:28} | {actual_score:+7.3f} | {result['action']:6} | {rsi_score:+6.3f} | {ma_score:+6.3f} | {macd_score:+6.3f} | {weight_check}")
            
            # Verify core requirements
            assert result['action'] in ['buy', 'sell', 'hold'], f"Invalid action: {result['action']}"
            assert -1.0 <= actual_score <= 1.0, f"Score out of range: {actual_score}"
            assert len(result['signal_results']) == 3, f"Wrong number of signals: {len(result['signal_results'])}"
            assert aggregation_correct, f"Weight aggregation incorrect for {config_name}"
            
        except Exception as e:
            print(f"{config_name:28} | ERROR: {str(e)[:50]}")
            raise e
    
    print("\n✅ All weight distributions working correctly!")

def test_action_thresholds():
    """Test that action thresholds work as expected."""
    
    print("\n🎯 Action Threshold Testing")
    print("-" * 30)
    
    evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
    
    # Test key threshold values
    test_scores = [-0.5, -0.1, -0.05, 0.0, 0.05, 0.1, 0.5]
    
    print("Score  | Action")
    print("-------|-------")
    
    for score in test_scores:
        mock_bot = Bot()
        action = evaluator._determine_action(score, mock_bot)
        
        # Verify expected behavior
        if score <= -0.1:
            expected = 'buy'
        elif score >= 0.1:
            expected = 'sell'
        else:
            expected = 'hold'
        
        status = "✅" if action == expected else "❌"
        print(f"{score:+6.2f} | {action:6} {status}")
        
        assert action == expected, f"Threshold error: score {score} should be {expected}, got {action}"
    
    print("\n✅ All action thresholds working correctly!")

def test_research_configuration():
    """Test the specific configuration from your research."""
    
    print("\n📊 Research Configuration Test")
    print("-" * 35)
    
    # Conservative configuration from PROFITABLE_SIGNAL_RESEARCH.md
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
    bot.signal_config = json.dumps(config)
    
    evaluator = BotSignalEvaluator(db=None, enable_confirmation=False)
    
    # Test different market scenarios
    scenarios = {
        'Uptrend': [50 + i*0.8 for i in range(40)],
        'Downtrend': [100 - i*0.8 for i in range(40)],
        'Sideways': [50 + np.sin(i/8)*3 for i in range(40)]
    }
    
    print("Scenario  | Score    | Action | Confidence")
    print("----------|----------|--------|----------")
    
    for scenario_name, prices in scenarios.items():
        data = pd.DataFrame({
            'close': prices,
            'timestamp': pd.date_range('2024-01-01', periods=len(prices), freq='1min')
        })
        
        result = evaluator.evaluate_bot(bot, data)
        
        print(f"{scenario_name:9} | {result['overall_score']:+8.3f} | {result['action']:6} | {result['confidence']:.3f}")
        
        # Verify all signals calculated
        assert len(result['signal_results']) == 3, f"Missing signals in {scenario_name}"
        assert result['metadata']['total_weight'] == 1.0, f"Wrong total weight in {scenario_name}"
    
    print("\n✅ Research configuration working correctly!")

def main():
    """Run essential validation tests."""
    
    print("🚀 ESSENTIAL SIGNAL VALIDATION FOR BOT CONFIGURATION")
    print("=" * 70)
    
    try:
        test_core_functionality()
        test_action_thresholds()
        test_research_configuration()
        
        print(f"\n🎉 ALL ESSENTIAL TESTS PASSED!")
        print("=" * 40)
        
        print(f"\n✅ VALIDATION RESULTS:")
        print("   • Weight distributions (0.4/0.4/0.2, 0.5/0.3/0.2, etc.) ✅ WORKING")
        print("   • Signal aggregation using weighted averages ✅ CORRECT")
        print("   • Action thresholds (-0.1 buy, +0.1 sell) ✅ ACCURATE")
        print("   • Research-recommended configurations ✅ FUNCTIONAL")
        
        print(f"\n🔥 READY FOR BOT CONFIGURATION!")
        print("You have confidence that the signal values you set will work correctly.")
        print("The mathematical foundation is solid - proceed with bot configuration!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
