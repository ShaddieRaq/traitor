#!/usr/bin/env python3
"""
Enhanced Threshold Test Monitoring
=================================

Monitors performance of threshold testing on selected pairs.
Test Threshold: ±0.05
Default Threshold: ±0.1
Test Pairs: ETH-USD, AVAX-USD, TOSHI-USD
"""

import requests
import json
from datetime import datetime

def monitor_threshold_test():
    base_url = "http://localhost:8000/api/v1"
    
    print(f"\n🔬 THRESHOLD TEST MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Get enhanced bot status
    response = requests.get(f"{base_url}/bots/status/enhanced")
    if response.status_code == 200:
        bots = response.json()
        
        test_pairs = ['ETH-USD', 'AVAX-USD', 'TOSHI-USD']
        
        print(f"\n🧪 TEST BOTS (±0.05 threshold):")
        print("   Pair        | Score     | Action    | Temp | Status  | Trade Ready")
        print("   " + "-" * 70)
        
        for bot in bots:
            if bot['pair'] in test_pairs:
                score = bot['current_combined_score']
                intent = bot.get('trading_intent', {})
                action = intent.get('next_action', 'unknown')
                temp = bot['temperature']
                status = bot['status']
                can_trade = bot.get('trade_readiness', {}).get('can_trade', False)
                
                print(f"   {bot['pair']:<11} | {score:>8.4f} | {action:<8} | {temp:<4} | {status:<7} | {can_trade}")
        
        # Show signals that would be different with default thresholds
        print(f"\n📊 THRESHOLD IMPACT ANALYSIS:")
        print("   Pair        | Score     | ±0.05 Action | ±0.10 Action | Impact")
        print("   " + "-" * 70)
        
        for bot in bots:
            if bot['pair'] in test_pairs:
                score = bot['current_combined_score']
                
                # Calculate actions for both thresholds
                action_005 = 'buy' if score <= -0.05 else ('sell' if score >= 0.05 else 'hold')
                action_010 = 'buy' if score <= -0.10 else ('sell' if score >= 0.10 else 'hold')
                
                impact = "🔄 DIFFERENT" if action_005 != action_010 else "⏸️  SAME"
                
                print(f"   {bot['pair']:<11} | {score:>8.4f} | {action_005:<11} | {action_010:<11} | {impact}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    monitor_threshold_test()
