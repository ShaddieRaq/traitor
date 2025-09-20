#!/usr/bin/env python3
"""
System-Wide Threshold Monitoring
===============================

Monitors all bots after system-wide ±0.05 threshold optimization.
"""

import requests
import json
from datetime import datetime

def monitor_system_optimization():
    base_url = "http://localhost:8000/api/v1"
    
    print(f"\n🌟 SYSTEM-WIDE OPTIMIZATION MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)
    
    # Get enhanced bot status
    response = requests.get(f"{base_url}/bots/status/enhanced")
    if response.status_code == 200:
        bots = response.json()
        
        # Categorize bots by trading activity
        active_signals = []
        confirmation_pending = []
        hold_signals = []
        blocked_bots = []
        
        print(f"\n📊 ALL BOTS STATUS (±0.05 thresholds):")
        print("   Pair        | Score     | Action | Temp | Status  | Trade Ready | Confirmation")
        print("   " + "-" * 85)
        
        for bot in bots:
            score = bot['current_combined_score']
            intent = bot.get('trading_intent', {})
            action = intent.get('next_action', 'unknown')
            temp = bot['temperature']
            status = bot['status']
            can_trade = bot.get('trade_readiness', {}).get('can_trade', False)
            
            confirmation = bot.get('confirmation', {})
            is_confirming = confirmation.get('is_active', False)
            conf_status = "CONFIRMING" if is_confirming else "READY" if can_trade else "BLOCKED"
            
            print(f"   {bot['pair']:<11} | {score:>8.4f} | {action:<6} | {temp:<4} | {status:<7} | {can_trade:<11} | {conf_status}")
            
            # Categorize for summary
            if action in ['buy', 'sell'] and is_confirming:
                confirmation_pending.append(bot['pair'])
            elif action in ['buy', 'sell'] and can_trade:
                active_signals.append(bot['pair'])
            elif not can_trade:
                blocked_bots.append(bot['pair'])
            else:
                hold_signals.append(bot['pair'])
        
        # Summary
        print(f"\n📈 OPTIMIZATION IMPACT SUMMARY:")
        print(f"   🔥 Active Signals: {len(active_signals)} pairs")
        if active_signals:
            print(f"      {', '.join(active_signals)}")
        print(f"   ⏳ Confirming Signals: {len(confirmation_pending)} pairs")
        if confirmation_pending:
            print(f"      {', '.join(confirmation_pending)}")
        print(f"   ⏸️  Hold Signals: {len(hold_signals)} pairs")
        print(f"   🚫 Blocked: {len(blocked_bots)} pairs")
        if blocked_bots:
            print(f"      {', '.join(blocked_bots)}")
        
        # Calculate improvement estimate
        total_trading_activity = len(active_signals) + len(confirmation_pending)
        improvement_estimate = (total_trading_activity / len(bots)) * 100
        
        print(f"\n🎯 TRADING ACTIVITY: {total_trading_activity}/{len(bots)} bots ({improvement_estimate:.1f}% active)")
        print("=" * 90)

if __name__ == "__main__":
    monitor_system_optimization()
