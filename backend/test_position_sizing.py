#!/usr/bin/env python3
"""
Test Position Sizing Engine - Phase 2B Validation
Test the dynamic position sizing calculations across different market scenarios.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, '/Users/lazy_genius/Projects/trader/backend')

def test_position_sizing_engine():
    """Test position sizing calculations with various scenarios."""
    try:
        print("🚀 Testing Position Sizing Engine...")
        print("=" * 60)
        
        # Test import
        from app.services.position_sizing_engine import get_position_sizing_engine
        print("✅ Position Sizing Engine imported successfully")
        
        # Initialize engine
        sizing_engine = get_position_sizing_engine()
        print(f"✅ Engine initialized: {type(sizing_engine)}")
        
        # Test scenarios
        base_position = 100.0
        
        print(f"\n📊 Testing with base position: ${base_position}")
        print("-" * 40)
        
        # Scenario 1: Strong Trending Market (like current BTC)
        print("\n🔥 Scenario 1: STRONG TRENDING Market")
        strong_trend_regime = {
            'regime': 'STRONG_TRENDING',
            'trend_strength': -0.45,
            'confidence': 0.9,
            'timeframe_analysis': {
                'short_term': {'volatility': 0.12},
                'medium_term': {'volatility': 0.52}, 
                'long_term': {'volatility': 1.84}
            }
        }
        
        result1 = sizing_engine.calculate_position_size(
            base_position_size=base_position,
            product_id="TEST-STRONG",
            signal_confidence=0.9,
            override_regime=strong_trend_regime
        )
        
        print(f"  Base Size: ${result1['base_position_size']}")
        print(f"  Final Size: ${result1['final_position_size']}")
        print(f"  Total Multiplier: {result1['total_multiplier']}x")
        print(f"  Rationale: {result1['sizing_rationale']}")
        
        # Scenario 2: Ranging Market  
        print("\n📊 Scenario 2: RANGING Market")
        ranging_regime = {
            'regime': 'RANGING',
            'trend_strength': -0.08,
            'confidence': 0.6,
            'timeframe_analysis': {
                'short_term': {'volatility': 0.08},
                'medium_term': {'volatility': 0.15},
                'long_term': {'volatility': 0.25}
            }
        }
        
        result2 = sizing_engine.calculate_position_size(
            base_position_size=base_position,
            product_id="TEST-RANGING",
            signal_confidence=0.6,
            override_regime=ranging_regime
        )
        
        print(f"  Base Size: ${result2['base_position_size']}")
        print(f"  Final Size: ${result2['final_position_size']}")
        print(f"  Total Multiplier: {result2['total_multiplier']}x")
        print(f"  Rationale: {result2['sizing_rationale']}")
        
        # Scenario 3: Choppy Market (high volatility, low confidence)
        print("\n⚡ Scenario 3: CHOPPY Market")
        choppy_regime = {
            'regime': 'CHOPPY',
            'trend_strength': -0.05,
            'confidence': 0.4,
            'timeframe_analysis': {
                'short_term': {'volatility': 0.25},
                'medium_term': {'volatility': 0.45},
                'long_term': {'volatility': 0.60}
            }
        }
        
        result3 = sizing_engine.calculate_position_size(
            base_position_size=base_position,
            product_id="TEST-CHOPPY", 
            signal_confidence=0.3,
            override_regime=choppy_regime
        )
        
        print(f"  Base Size: ${result3['base_position_size']}")
        print(f"  Final Size: ${result3['final_position_size']}")
        print(f"  Total Multiplier: {result3['total_multiplier']}x")
        print(f"  Rationale: {result3['sizing_rationale']}")
        
        # Scenario 4: Live BTC-USD test
        print("\n₿ Scenario 4: Live BTC-USD Analysis")
        result4 = sizing_engine.calculate_position_size(
            base_position_size=base_position,
            product_id="BTC-USD",
            signal_confidence=0.85
        )
        
        print(f"  Base Size: ${result4['base_position_size']}")
        print(f"  Final Size: ${result4['final_position_size']}")
        print(f"  Total Multiplier: {result4['total_multiplier']}x")
        print(f"  Live Regime: {result4.get('regime_analysis', {}).get('regime', 'N/A')}")
        print(f"  Rationale: {result4['sizing_rationale']}")
        
        # Summary comparison
        print(f"\n📈 Scenario Comparison:")
        print(f"  Strong Trending: ${result1['final_position_size']} ({result1['total_multiplier']}x)")
        print(f"  Ranging Market: ${result2['final_position_size']} ({result2['total_multiplier']}x)")
        print(f"  Choppy Market: ${result3['final_position_size']} ({result3['total_multiplier']}x)")
        print(f"  Live BTC-USD: ${result4['final_position_size']} ({result4['total_multiplier']}x)")
        
        return True
        
    except Exception as e:
        print(f"❌ Position sizing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Position Sizing Engine Test Suite")
    print("=" * 50)
    
    success = test_position_sizing_engine()
    
    if success:
        print(f"\n🎉 Position Sizing Engine test completed successfully!")
        print("📝 Ready for Phase 2C integration")
    else:
        print(f"\n💥 Position Sizing Engine test failed!")
        sys.exit(1)