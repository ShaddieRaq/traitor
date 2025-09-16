#!/usr/bin/env python3
"""
Signal Lock Fix Script
=====================

Detects and clears stuck signal confirmation states that block trading.

Usage:
    python scripts/fix_signal_locks.py --check    # Check for locks only
    python scripts/fix_signal_locks.py --fix      # Fix detected locks
    python scripts/fix_signal_locks.py --monitor  # Continuous monitoring
"""

import sys
import os
import time
import argparse
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import get_db
from app.models.models import Bot
from sqlalchemy.orm import Session

def check_signal_locks():
    """Check for bots with stuck signal confirmation states."""
    db = next(get_db())
    
    try:
        stuck_bots = []
        current_time = datetime.now()
        
        # Check for bots with confirmation states older than 10 minutes
        bots = db.query(Bot).filter(Bot.signal_confirmation_start.isnot(None)).all()
        
        for bot in bots:
            if bot.signal_confirmation_start:
                time_stuck = current_time - bot.signal_confirmation_start.replace(tzinfo=None)
                
                # If stuck for more than 10 minutes, it's likely a lock
                if time_stuck > timedelta(minutes=10):
                    stuck_bots.append({
                        'bot': bot,
                        'stuck_duration': time_stuck,
                        'confirmation_start': bot.signal_confirmation_start
                    })
        
        return stuck_bots
        
    finally:
        db.close()

def fix_signal_locks(stuck_bots):
    """Clear stuck signal confirmation states."""
    db = next(get_db())
    
    try:
        fixed_count = 0
        
        for stuck_info in stuck_bots:
            bot = stuck_info['bot']
            
            print(f"🔧 Fixing Bot {bot.id} ({bot.name}):")
            print(f"   Stuck since: {stuck_info['confirmation_start']}")
            print(f"   Duration: {stuck_info['stuck_duration']}")
            
            # Clear the confirmation state
            bot.signal_confirmation_start = None
            bot.current_combined_score = 0.0
            
            db.commit()
            fixed_count += 1
            
            print(f"   ✅ Signal lock cleared")
            print()
        
        return fixed_count
        
    finally:
        db.close()

def monitor_signal_locks(interval_minutes=5):
    """Continuously monitor for signal locks."""
    print(f"🔍 Starting signal lock monitoring (checking every {interval_minutes} minutes)")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            stuck_bots = check_signal_locks()
            
            if stuck_bots:
                print(f"⚠️  Found {len(stuck_bots)} stuck signal confirmation(s) at {datetime.now()}")
                for stuck_info in stuck_bots:
                    bot = stuck_info['bot']
                    print(f"   Bot {bot.id} ({bot.name}) stuck for {stuck_info['stuck_duration']}")
                
                # Auto-fix if stuck for more than 15 minutes
                auto_fix_bots = [s for s in stuck_bots if s['stuck_duration'] > timedelta(minutes=15)]
                if auto_fix_bots:
                    print(f"🚨 Auto-fixing {len(auto_fix_bots)} bot(s) stuck for >15 minutes")
                    fix_signal_locks(auto_fix_bots)
            else:
                print(f"✅ No signal locks detected at {datetime.now()}")
            
            time.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description='Fix stuck signal confirmation states')
    parser.add_argument('--check', action='store_true', help='Check for signal locks only')
    parser.add_argument('--fix', action='store_true', help='Fix detected signal locks')
    parser.add_argument('--monitor', action='store_true', help='Continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=5, help='Monitor interval in minutes (default: 5)')
    
    args = parser.parse_args()
    
    if args.monitor:
        monitor_signal_locks(args.interval)
        return
    
    # Check for stuck bots
    stuck_bots = check_signal_locks()
    
    if not stuck_bots:
        print("✅ No signal confirmation locks detected")
        return
    
    print(f"🚨 Found {len(stuck_bots)} bot(s) with stuck signal confirmation states:")
    print()
    
    for stuck_info in stuck_bots:
        bot = stuck_info['bot']
        print(f"❌ Bot {bot.id} ({bot.name}):")
        print(f"   Pair: {bot.pair}")
        print(f"   Status: {bot.status}")
        print(f"   Stuck since: {stuck_info['confirmation_start']}")
        print(f"   Duration: {stuck_info['stuck_duration']}")
        print(f"   Current score: {bot.current_combined_score}")
        print()
    
    if args.fix:
        print("🔧 Fixing signal locks...")
        fixed_count = fix_signal_locks(stuck_bots)
        print(f"✅ Fixed {fixed_count} signal confirmation lock(s)")
    elif args.check:
        print("ℹ️  Use --fix to clear these locks")
    else:
        print("Use --check to inspect or --fix to clear these locks")

if __name__ == "__main__":
    main()
