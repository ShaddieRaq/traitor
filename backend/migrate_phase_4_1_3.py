#!/usr/bin/env python3
"""
Database migration script for Phase 4.1.3 enhanced position management.
Adds new columns to the trades table for tranche support.
"""

import sqlite3
import os
import sys

def migrate_database():
    """Add new columns to trades table for Phase 4.1.3 tranche support."""
    
    # Database path
    db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    print("🔄 Starting Phase 4.1.3 database migration...")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(trades)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Current trades table columns: {columns}")
        
        new_columns = [
            ("position_tranches", "TEXT"),
            ("average_entry_price", "REAL"),
            ("tranche_number", "INTEGER"),
            ("position_status", "TEXT"),
            ("size_usd", "REAL")
        ]
        
        # Add new columns if they don't exist
        for column_name, column_type in new_columns:
            if column_name not in columns:
                print(f"➕ Adding column: {column_name} ({column_type})")
                cursor.execute(f"ALTER TABLE trades ADD COLUMN {column_name} {column_type}")
            else:
                print(f"✅ Column already exists: {column_name}")
        
        # Commit changes
        conn.commit()
        
        # Verify new schema
        cursor.execute("PRAGMA table_info(trades)")
        updated_columns = [row[1] for row in cursor.fetchall()]
        print(f"✅ Updated trades table columns: {updated_columns}")
        
        # Close connection
        conn.close()
        
        print("🎉 Phase 4.1.3 database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
