#!/usr/bin/env python3
"""
Initialize lifecycle_stage for existing bots.

This script sets lifecycle_stage = "ACTIVE" for all bots that currently have
lifecycle_stage = NULL. This is needed because SQLAlchemy DEFAULT only applies
to INSERT operations, not existing rows.

Run after add_lifecycle_columns.py migration.
"""
import sqlite3
import sys
from pathlib import Path

def initialize_lifecycle_stage():
    """Set lifecycle_stage = 'ACTIVE' for all NULL bots."""
    db_path = Path(__file__).parent / "trader.db"
    
    if not db_path.exists():
        print(f"❌ ERROR: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current state
        cursor.execute("SELECT COUNT(*) FROM bots WHERE lifecycle_stage IS NULL")
        null_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bots WHERE lifecycle_stage = 'ACTIVE'")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bots")
        total_count = cursor.fetchone()[0]
        
        print("\n📊 BEFORE INITIALIZATION:")
        print(f"   Total bots: {total_count}")
        print(f"   lifecycle_stage = NULL: {null_count}")
        print(f"   lifecycle_stage = ACTIVE: {active_count}")
        
        if null_count == 0:
            print("\n✅ All bots already initialized!")
            return True
        
        # Update NULL to ACTIVE
        print(f"\n🔄 Initializing {null_count} bots to ACTIVE...")
        cursor.execute("""
            UPDATE bots 
            SET lifecycle_stage = 'ACTIVE' 
            WHERE lifecycle_stage IS NULL
        """)
        
        rows_updated = cursor.rowcount
        conn.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM bots WHERE lifecycle_stage IS NULL")
        remaining_null = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bots WHERE lifecycle_stage = 'ACTIVE'")
        new_active_count = cursor.fetchone()[0]
        
        print(f"   ✅ Updated {rows_updated} bots")
        
        print("\n📊 AFTER INITIALIZATION:")
        print(f"   Total bots: {total_count}")
        print(f"   lifecycle_stage = NULL: {remaining_null}")
        print(f"   lifecycle_stage = ACTIVE: {new_active_count}")
        
        if remaining_null == 0:
            print("\n✅ SUCCESS: All bots initialized to ACTIVE!")
            print("   Lifecycle system is now operational.")
            return True
        else:
            print(f"\n⚠️  WARNING: {remaining_null} bots still NULL")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = initialize_lifecycle_stage()
    sys.exit(0 if success else 1)
