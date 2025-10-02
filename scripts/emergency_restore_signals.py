#!/usr/bin/env python3
"""
EMERGENCY RECOVERY: Restore corrupted signal configurations
My previous script overwrote signal_config with just thresholds, losing all signal weights.
This script restores the full signal configuration while preserving the ±0.05 thresholds.
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

def restore_signal_configurations():
    """Restore corrupted signal configurations with full signal setup."""
    print("🚨 EMERGENCY RECOVERY: Restoring corrupted signal configurations...")
    
    # Default signal configuration from bots.py
    default_signal_config = {
        "rsi": {
            "enabled": True,
            "weight": 0.4,
            "period": 14,
            "buy_threshold": 30,
            "sell_threshold": 70
        },
        "moving_average": {
            "enabled": True,
            "weight": 0.35,
            "fast_period": 12,
            "slow_period": 26
        },
        "macd": {
            "enabled": True,
            "weight": 0.25,
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        },
        "trading_thresholds": {
            "buy_threshold": -0.05,
            "sell_threshold": 0.05
        }
    }
    
    db = SessionLocal()
    try:
        # Get all bots
        bots = db.query(Bot).all()
        print(f"📊 Found {len(bots)} bots to restore")
        
        restored_count = 0
        
        for bot in bots:
            try:
                # Parse current signal config
                current_config = json.loads(bot.signal_config) if bot.signal_config else {}
                
                # Check if this bot needs restoration (missing signal definitions)
                needs_restoration = False
                if not current_config.get('rsi') or not current_config.get('moving_average') or not current_config.get('macd'):
                    needs_restoration = True
                
                if needs_restoration:
                    # Restore full configuration with ±0.05 thresholds
                    restored_config = default_signal_config.copy()
                    
                    # Preserve any existing trading thresholds if they exist
                    if current_config.get('trading_thresholds'):
                        existing_thresholds = current_config['trading_thresholds']
                        print(f"  📈 {bot.pair}: Preserving existing thresholds: {existing_thresholds}")
                        restored_config['trading_thresholds'] = existing_thresholds
                    else:
                        print(f"  📈 {bot.pair}: Using default ±0.05 thresholds")
                    
                    # Also add legacy 'thresholds' field for compatibility
                    restored_config['thresholds'] = restored_config['trading_thresholds'].copy()
                    
                    # Save restored configuration
                    bot.signal_config = json.dumps(restored_config)
                    restored_count += 1
                    print(f"  ✅ {bot.pair}: Signal configuration restored")
                else:
                    print(f"  ✅ {bot.pair}: Signal configuration intact")
                    
            except Exception as e:
                print(f"  ❌ Error restoring {bot.pair}: {e}")
                continue
        
        # Commit all changes
        if restored_count > 0:
            db.commit()
            print(f"✅ Successfully restored {restored_count} bot signal configurations")
        else:
            print("✅ No bots needed signal configuration restoration")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    restore_signal_configurations()