#!/usr/bin/env python3
"""
Fix system-wide threshold optimization by updating signal_config JSON properly
"""

import sqlite3
import json
import sys
from datetime import datetime

# Database path
DB_PATH = '/Users/lazy_genius/Projects/trader/trader.db'

def update_signal_config_thresholds():
    """Update signal_config JSON with new thresholds"""
    
    print("🔧 Fixing System-Wide Threshold Configuration")
    print("=" * 60)
    print("Target: Update signal_config JSON with ±0.05 thresholds")
    print()
    
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    
    # Get all bots
    cursor.execute("SELECT id, name, signal_config FROM bots ORDER BY name")
    bots = cursor.fetchall()
    
    updated_count = 0
    
    for bot_id, name, config_str in bots:
        # Parse existing config
        if config_str:
            config = json.loads(config_str)
        else:
            config = {}
        
        # Add/update thresholds
        if 'thresholds' not in config:
            config['thresholds'] = {}
        
        config['thresholds']['buy_threshold'] = -0.05
        config['thresholds']['sell_threshold'] = 0.05
        
        # Update database
        new_config_str = json.dumps(config, indent=2)
        cursor.execute(
            "UPDATE bots SET signal_config = ? WHERE id = ?",
            (new_config_str, bot_id)
        )
        
        print(f"✅ Updated {name}: ±0.05 thresholds")
        updated_count += 1
    
    db.commit()
    db.close()
    
    print()
    print(f"🎉 System-Wide Threshold Fix Complete!")
    print(f"   Updated: {updated_count}/{len(bots)} bots")
    print(f"   New thresholds: ±0.05 (50% more sensitive)")
    print()
    print("🚀 NEXT STEPS:")
    print("1. Monitor activity: python scripts/monitor_system_optimization.py")
    print("2. System health: ./scripts/status.sh")
    print("3. Expected: Major increase in trading frequency!")

if __name__ == "__main__":
    update_signal_config_thresholds()
