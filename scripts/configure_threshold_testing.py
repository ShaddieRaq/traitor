#!/usr/bin/env python3
"""
Direct Database Configuration for Threshold Testing
==================================================

Directly updates bot signal_config in the database to add threshold testing configuration.
This bypasses the API schema validation to implement the threshold testing.
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import get_db
from app.models.models import Bot

def update_bot_thresholds():
    """Update specific bots with threshold testing configuration."""
    
    test_pairs = {
        "ETH-USD": 4,
        "AVAX-USD": 14, 
        "TOSHI-USD": 15
    }
    
    db = next(get_db())
    
    for pair, bot_id in test_pairs.items():
        print(f"🔧 Configuring {pair} (Bot ID: {bot_id}) for ±0.05 threshold testing...")
        
        try:
            # Get the bot
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                print(f"❌ Bot {bot_id} not found")
                continue
            
            # Parse current signal config
            if isinstance(bot.signal_config, str):
                signal_config = json.loads(bot.signal_config)
            else:
                signal_config = bot.signal_config or {}
            
            # Add threshold configuration
            signal_config['trading_thresholds'] = {
                'buy_threshold': -0.05,
                'sell_threshold': 0.05,
                'test_mode': True,
                'test_start': datetime.now().isoformat(),
                'test_duration_hours': 72,
                'original_thresholds': {
                    'buy_threshold': -0.1,
                    'sell_threshold': 0.1
                }
            }
            
            # Update the bot
            bot.signal_config = json.dumps(signal_config)
            db.commit()
            
            print(f"✅ Updated {pair} with ±0.05 thresholds")
            
        except Exception as e:
            print(f"❌ Error updating {pair}: {e}")
            db.rollback()
    
    db.close()
    print("\n🎯 Threshold configuration completed!")

if __name__ == "__main__":
    update_bot_thresholds()
