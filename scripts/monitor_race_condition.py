#!/usr/bin/env python3
"""
Race Condition Monitoring Script
Monitors for duplicate trades in real-time to verify the fix is working.
"""

import requests
import time
from datetime import datetime
from collections import defaultdict

def check_for_duplicates():
    """Check recent trades for duplicates within 30 seconds of each other."""
    try:
        response = requests.get("http://localhost:8000/api/v1/trades/?limit=20")
        trades = response.json()
        
        # Group by bot_id and check for close timing
        bot_trades = defaultdict(list)
        
        for trade in trades:
            if trade.get('bot_id'):
                bot_trades[trade['bot_id']].append({
                    'id': trade['id'],
                    'created_at': trade['created_at'],
                    'side': trade['side'],
                    'size': trade['size']
                })
        
        # Check each bot for duplicate trades
        duplicates_found = []
        
        for bot_id, trades_list in bot_trades.items():
            # Sort by creation time (newest first)
            sorted_trades = sorted(trades_list, key=lambda x: x['created_at'], reverse=True)
            
            # Check consecutive trades for timing
            for i in range(len(sorted_trades) - 1):
                trade1 = sorted_trades[i]
                trade2 = sorted_trades[i + 1]
                
                # Parse timestamps
                time1 = datetime.fromisoformat(trade1['created_at'].replace('Z', '+00:00'))
                time2 = datetime.fromisoformat(trade2['created_at'].replace('Z', '+00:00'))
                
                # Check if within 30 seconds
                time_diff = abs((time1 - time2).total_seconds())
                
                if time_diff < 30:  # Potential duplicate
                    duplicates_found.append({
                        'bot_id': bot_id,
                        'trade1': trade1,
                        'trade2': trade2,
                        'time_diff_seconds': time_diff
                    })
        
        return duplicates_found
        
    except Exception as e:
        print(f"❌ Error checking trades: {e}")
        return []

def main():
    """Monitor for duplicate trades."""
    print("🔍 Race Condition Monitor - Checking for duplicate trades...")
    print("Press Ctrl+C to stop\n")
    
    last_check_time = datetime.now()
    duplicate_count = 0
    
    try:
        while True:
            duplicates = check_for_duplicates()
            current_time = datetime.now()
            
            if duplicates:
                duplicate_count += len(duplicates)
                print(f"🚨 {current_time.strftime('%H:%M:%S')} - DUPLICATES DETECTED:")
                for dup in duplicates:
                    print(f"  Bot {dup['bot_id']}: Trades {dup['trade1']['id']} & {dup['trade2']['id']}")
                    print(f"    Time diff: {dup['time_diff_seconds']:.2f} seconds")
                    print(f"    Trade 1: {dup['trade1']['side']} {dup['trade1']['size']} at {dup['trade1']['created_at']}")
                    print(f"    Trade 2: {dup['trade2']['side']} {dup['trade2']['size']} at {dup['trade2']['created_at']}")
                print()
            else:
                # Only print status every 30 seconds to avoid spam
                if (current_time - last_check_time).total_seconds() >= 30:
                    print(f"✅ {current_time.strftime('%H:%M:%S')} - No duplicates detected (Total found: {duplicate_count})")
                    last_check_time = current_time
            
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print(f"\n🛑 Monitoring stopped. Total duplicates found: {duplicate_count}")
        if duplicate_count == 0:
            print("🎉 Race condition fix appears to be working!")
        else:
            print("⚠️ Race condition may still be present.")

if __name__ == "__main__":
    main()
