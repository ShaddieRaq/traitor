#!/usr/bin/env python3
"""
Enable trend detection on BTC-USD bot for Phase 1C testing.
Direct database update to bypass the API issue.
"""

import sqlite3
import sys
from pathlib import Path

def enable_btc_trend_detection():
    """Enable trend detection on BTC-USD bot via direct database update."""
    
    # Path to the database
    db_path = Path(__file__).parent.parent / "trader.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Find BTC-USD bot
        cursor.execute("SELECT id, name, pair FROM bots WHERE pair = 'BTC-USD';")
        btc_bot = cursor.fetchone()
        
        if not btc_bot:
            print("❌ BTC-USD bot not found")
            return False
        
        bot_id, bot_name, pair = btc_bot
        print(f"📍 Found {bot_name} (ID: {bot_id}, Pair: {pair})")
        
        # Enable trend detection
        print("🔄 Enabling trend detection...")
        cursor.execute("UPDATE bots SET use_trend_detection = 1 WHERE id = ?;", (bot_id,))
        
        # Commit the changes
        conn.commit()
        
        # Verify the update
        cursor.execute("SELECT id, name, pair, use_trend_detection FROM bots WHERE id = ?;", (bot_id,))
        result = cursor.fetchone()
        
        if result and result[3] == 1:  # use_trend_detection column
            print(f"✅ Trend detection enabled for {result[1]} ({result[2]})")
            return True
        else:
            print("❌ Failed to enable trend detection")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Enabling trend detection on BTC-USD bot...")
    success = enable_btc_trend_detection()
    
    if success:
        print("\n🎉 BTC-USD bot trend detection enabled successfully!")
        print("📝 Next: Test the enhanced bot status to see trend analysis data")
    else:
        print("\n💥 Failed to enable trend detection!")
        sys.exit(1)