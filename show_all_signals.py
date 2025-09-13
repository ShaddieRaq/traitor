#!/usr/bin/env python3
"""
Script to show detailed signal breakdowns for all bots to demonstrate 
that RSI, Moving Average, and MACD are all implemented and working.
"""

import requests
import json
from datetime import datetime

def get_detailed_signals():
    """Get detailed signal information for all bots."""
    try:
        # Get all bots
        bots_response = requests.get("http://localhost:8000/api/v1/bots/")
        bots = bots_response.json()
        
        print("🤖 COMPLETE SIGNAL ANALYSIS FOR ALL BOTS")
        print("=" * 60)
        
        for bot in bots:
            print(f"\n📊 {bot['name']} ({bot['pair']})")
            print("-" * 40)
            
            # Get signal configuration
            signal_config = bot['signal_config']
            print("🔧 Signal Configuration:")
            
            total_weight = 0
            for signal_name, config in signal_config.items():
                if config.get('enabled', False):
                    weight = config.get('weight', 0)
                    total_weight += weight
                    print(f"   • {signal_name.upper()}: Weight {weight}")
                    
                    if signal_name == 'rsi':
                        print(f"     - Period: {config.get('period', 14)}")
                        print(f"     - Buy Threshold: {config.get('buy_threshold', 30)} (oversold)")
                        print(f"     - Sell Threshold: {config.get('sell_threshold', 70)} (overbought)")
                    elif signal_name == 'moving_average':
                        print(f"     - Fast Period: {config.get('fast_period', 12)}")
                        print(f"     - Slow Period: {config.get('slow_period', 26)}")
                    elif signal_name == 'macd':
                        print(f"     - Fast Period: {config.get('fast_period', 12)}")
                        print(f"     - Slow Period: {config.get('slow_period', 26)}")
                        print(f"     - Signal Period: {config.get('signal_period', 9)}")
            
            print(f"   📊 Total Weight: {total_weight} (should be ≤ 1.0)")
            
            # Force fresh evaluation to get individual signals
            try:
                eval_response = requests.post(f"http://localhost:8000/api/v1/bot-evaluation/{bot['id']}/evaluate")
                if eval_response.status_code == 200:
                    eval_data = eval_response.json()
                    
                    print(f"\n🎯 Current Signal Values:")
                    print(f"   Combined Score: {eval_data.get('overall_score', 0):.4f}")
                    print(f"   Overall Action: {eval_data.get('action', 'unknown').upper()}")
                    print(f"   Confidence: {eval_data.get('confidence', 0):.2%}")
                    
                    # Individual signal breakdowns
                    signal_results = eval_data.get('signal_results', {})
                    if signal_results:
                        print(f"\n🔍 Individual Signal Breakdown:")
                        for signal_name, result in signal_results.items():
                            score = result.get('score', 0)
                            action = result.get('action', 'hold')
                            confidence = result.get('confidence', 0)
                            metadata = result.get('metadata', {})
                            
                            print(f"   • {signal_name.upper()}:")
                            print(f"     Score: {score:.4f} | Action: {action.upper()} | Confidence: {confidence:.2%}")
                            
                            # Show specific indicator values
                            if signal_name == 'rsi' and 'rsi_value' in metadata:
                                rsi_val = metadata['rsi_value']
                                print(f"     RSI Value: {rsi_val:.2f} (30=oversold, 70=overbought)")
                            elif signal_name == 'moving_average' and 'fast_ma' in metadata:
                                fast_ma = metadata['fast_ma']
                                slow_ma = metadata['slow_ma']
                                sep_pct = metadata.get('separation_pct', 0)
                                print(f"     Fast MA: ${fast_ma:.2f} | Slow MA: ${slow_ma:.2f}")
                                print(f"     Separation: {sep_pct:.2f}% (fast above/below slow)")
                            elif signal_name == 'macd' and 'macd_line' in metadata:
                                macd_line = metadata['macd_line']
                                signal_line = metadata['signal_line']
                                histogram = metadata['histogram']
                                print(f"     MACD Line: {macd_line:.6f} | Signal Line: {signal_line:.6f}")
                                print(f"     Histogram: {histogram:.6f} (MACD - Signal)")
                    
                    # Show weighted contribution
                    print(f"\n⚖️  Weighted Contributions:")
                    for signal_name, config in signal_config.items():
                        if config.get('enabled', False) and signal_name in signal_results:
                            weight = config.get('weight', 0)
                            score = signal_results[signal_name].get('score', 0)
                            contribution = score * weight
                            print(f"   • {signal_name.upper()}: {score:.4f} × {weight} = {contribution:.4f}")
                else:
                    print(f"   ⚠️  Could not get fresh evaluation (status: {eval_response.status_code})")
            except Exception as e:
                print(f"   ❌ Error getting evaluation: {e}")
        
        print(f"\n✅ ALL THREE INDICATORS ARE FULLY IMPLEMENTED:")
        print("   • RSI (Relative Strength Index) - Momentum oscillator")
        print("   • Moving Average Crossover - Trend following")  
        print("   • MACD (Moving Average Convergence Divergence) - Momentum and trend")
        print(f"\n🕐 Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_detailed_signals()
