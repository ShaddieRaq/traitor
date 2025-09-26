#!/usr/bin/env python3
"""
Enable trend detection on ALL bots for system-wide Market Regime Intelligence.
Phase 1 deployment across all 12 trading pairs.
"""

import sqlite3
import sys
from pathlib import Path

def enable_all_bots_trend_detection():
    """Enable trend detection on all bots via direct database update."""
    
    # Path to the database
    db_path = Path(__file__).parent.parent / "trader.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all bots
        cursor.execute("SELECT id, name, pair, use_trend_detection FROM bots ORDER BY pair;")
        all_bots = cursor.fetchall()
        
        if not all_bots:
            print("❌ No bots found in database")
            return False
        
        print(f"📍 Found {len(all_bots)} bots:")
        
        enabled_count = 0
        already_enabled = 0
        
        for bot_id, bot_name, pair, current_status in all_bots:
            if current_status == 1:  # Already enabled
                print(f"  ✅ {pair}: {bot_name} (already enabled)")
                already_enabled += 1
            else:
                print(f"  🔄 {pair}: {bot_name} (enabling...)")
                cursor.execute("UPDATE bots SET use_trend_detection = 1 WHERE id = ?;", (bot_id,))
                enabled_count += 1
        
        # Commit all changes
        conn.commit()
        
        # Verify the updates
        cursor.execute("SELECT COUNT(*) FROM bots WHERE use_trend_detection = 1;")
        total_enabled = cursor.fetchone()[0]
        
        print(f"\n📊 Results:")
        print(f"  🔥 Newly enabled: {enabled_count}")
        print(f"  ✅ Already enabled: {already_enabled}")  
        print(f"  🎯 Total enabled: {total_enabled}/{len(all_bots)}")
        
        if total_enabled == len(all_bots):
            print(f"\n🎉 SUCCESS: All {len(all_bots)} bots now have Market Regime Intelligence enabled!")
            
            # Show final status
            cursor.execute("SELECT pair, name FROM bots WHERE use_trend_detection = 1 ORDER BY pair;")
            enabled_bots = cursor.fetchall()
            print(f"\n🚀 Regime-Intelligent Bots:")
            for pair, name in enabled_bots:
                print(f"  • {pair}: {name}")
                
            return True
        else:
            print(f"\n⚠️  Warning: Only {total_enabled}/{len(all_bots)} bots enabled")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Enabling Market Regime Intelligence on ALL bots...")
    print("=" * 60)
    success = enable_all_bots_trend_detection()
    
    if success:
        print("\n🎉 PHASE 1 DEPLOYMENT COMPLETE!")
        print("🧠 All 12 bots now use regime-adaptive trading thresholds")
        print("📝 Next: Restart application and validate system-wide deployment")
    else:
        print("\n💥 Phase 1 deployment failed!")
        sys.exit(1)