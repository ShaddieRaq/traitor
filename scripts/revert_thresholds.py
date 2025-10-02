#!/usr/bin/env python3
"""
Script to revert bot trading thresholds from ±0.1 back to ±0.05
This reverts the extreme settings back to the proven optimized thresholds.
"""

import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Change to project root directory to ensure proper path resolution
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Bot

def revert_bot_thresholds():
    """Revert bot thresholds from ±0.1 back to proven ±0.05 settings."""
    print("🔄 Reverting bot thresholds from ±0.1 to ±0.05...")
    
    db = SessionLocal()
    try:
        # Get all bots
        bots = db.query(Bot).all()
        print(f"📊 Found {len(bots)} bots total")
        
        updated_count = 0
        
        for bot in bots:
            try:
                # Parse current signal config
                signal_config = json.loads(bot.signal_config)
                
                # Check current thresholds
                trading_thresholds = signal_config.get('trading_thresholds', {})
                current_buy = trading_thresholds.get('buy_threshold', 0)
                current_sell = trading_thresholds.get('sell_threshold', 0)
                
                # Also check 'thresholds' field (legacy format)
                thresholds = signal_config.get('thresholds', {})
                threshold_buy = thresholds.get('buy_threshold', 0)
                threshold_sell = thresholds.get('sell_threshold', 0)
                
                # Check if this bot needs updating (has ±0.1 thresholds)
                needs_update = False
                if abs(current_buy - (-0.1)) < 0.001 and abs(current_sell - 0.1) < 0.001:
                    needs_update = True
                    print(f"  📈 {bot.pair}: trading_thresholds ±0.1 → ±0.05")
                elif abs(threshold_buy - (-0.1)) < 0.001 and abs(threshold_sell - 0.1) < 0.001:
                    needs_update = True
                    print(f"  📈 {bot.pair}: thresholds ±0.1 → ±0.05")
                
                if needs_update:
                    # Update to ±0.05
                    signal_config['trading_thresholds'] = {
                        'buy_threshold': -0.05,
                        'sell_threshold': 0.05
                    }
                    signal_config['thresholds'] = {
                        'buy_threshold': -0.05,
                        'sell_threshold': 0.05
                    }
                    
                    # Save back to database
                    bot.signal_config = json.dumps(signal_config)
                    updated_count += 1
                else:
                    current_display = f"buy: {current_buy or threshold_buy}, sell: {current_sell or threshold_sell}"
                    print(f"  ✅ {bot.pair}: already optimized ({current_display})")
                    
            except Exception as e:
                print(f"  ❌ Error updating {bot.pair}: {e}")
                continue
        
        # Commit all changes
        if updated_count > 0:
            db.commit()
            print(f"✅ Successfully updated {updated_count} bots to ±0.05 thresholds")
        else:
            print("✅ No bots needed threshold updates")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    revert_bot_thresholds()