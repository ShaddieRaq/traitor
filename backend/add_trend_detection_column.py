#!/usr/bin/env python3
"""
Add use_trend_detection column to bots table for Phase 1 Market Regime Intelligence.
This script safely adds the new column with proper error handling.
"""

import os
import sys
import sqlite3
from pathlib import Path

def add_trend_detection_column():
    """Add use_trend_detection column to bots table."""
    
    # Path to the database
    db_path = Path(__file__).parent.parent / "trader.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(bots);")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'use_trend_detection' in columns:
            print("✅ Column 'use_trend_detection' already exists in bots table")
            return True
        
        # Add the column
        print("🔄 Adding 'use_trend_detection' column to bots table...")
        cursor.execute("ALTER TABLE bots ADD COLUMN use_trend_detection BOOLEAN DEFAULT FALSE;")
        
        # Commit the changes
        conn.commit()
        print("✅ Successfully added 'use_trend_detection' column")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(bots);")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'use_trend_detection' in columns:
            print("✅ Column addition verified")
            return True
        else:
            print("❌ Column addition failed - not found in table info")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Adding use_trend_detection column to bots table...")
    success = add_trend_detection_column()
    
    if success:
        print("\n🎉 Database migration completed successfully!")
        print("📝 Next step: Restart the application to test the integration")
    else:
        print("\n💥 Database migration failed!")
        sys.exit(1)