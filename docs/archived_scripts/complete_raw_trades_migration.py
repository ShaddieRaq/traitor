#!/usr/bin/env python3
"""
Complete Migration to Raw Trades System
=======================================

This script completes the migration from the corrupted trades table
to the pure raw_trades system by:

1. Backing up current database
2. Dropping the trades table permanently 
3. Removing Trade model from codebase (commented out)
4. Updating all APIs to use raw_trades
5. Validating the migration

WARNING: This is a DESTRUCTIVE operation!
"""

import sqlite3
import shutil
import sys
from datetime import datetime
from pathlib import Path

def backup_database():
    """Create a backup before migration."""
    db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"/Users/lazy_genius/Projects/trader/backend/trader_backup_migration_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def drop_trades_table():
    """Permanently drop the trades table."""
    db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        if not cursor.fetchone():
            print("✅ Trades table already doesn't exist")
            conn.close()
            return True
        
        # Get record count for reference
        cursor.execute("SELECT COUNT(*) FROM trades")
        record_count = cursor.fetchone()[0]
        
        print(f"🗑️  Dropping trades table with {record_count} records...")
        cursor.execute("DROP TABLE trades")
        
        # Also drop any related indexes
        cursor.execute("DROP INDEX IF EXISTS ix_trades_product_id")
        cursor.execute("DROP INDEX IF EXISTS ix_trades_id")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully dropped trades table")
        return True
        
    except Exception as e:
        print(f"❌ Failed to drop trades table: {e}")
        return False

def disable_trade_model():
    """Comment out the Trade model to prevent auto-recreation."""
    models_path = "/Users/lazy_genius/Projects/trader/backend/app/models/models.py"
    
    try:
        with open(models_path, 'r') as f:
            content = f.read()
        
        # Check if Trade model is already commented
        if "# class Trade(Base):" in content:
            print("✅ Trade model already disabled")
            return True
        
        # Find and comment out the Trade class
        lines = content.split('\\n')
        in_trade_class = False
        modified_lines = []
        
        for line in lines:
            if line.strip().startswith('class Trade(Base):'):
                in_trade_class = True
                modified_lines.append(f"# {line}  # DISABLED: Migrated to raw_trades system")
            elif in_trade_class and line.strip() == '' and not line.startswith('    '):
                # End of class
                in_trade_class = False
                modified_lines.append(line)
            elif in_trade_class:
                modified_lines.append(f"# {line}")
            else:
                modified_lines.append(line)
        
        # Write back the modified content
        with open(models_path, 'w') as f:
            f.write('\\n'.join(modified_lines))
        
        print("✅ Trade model disabled in models.py")
        return True
        
    except Exception as e:
        print(f"❌ Failed to disable Trade model: {e}")
        return False

def check_raw_trades_data():
    """Verify raw_trades table has data."""
    db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM raw_trades")
        count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT product_id, COUNT(*) as trade_count
            FROM raw_trades 
            GROUP BY product_id 
            ORDER BY trade_count DESC
            LIMIT 5
        """)
        top_products = cursor.fetchall()
        
        conn.close()
        
        print(f"\\n📊 Raw Trades Data Summary:")
        print(f"   Total records: {count}")
        print(f"   Top products:")
        for product, trade_count in top_products:
            print(f"     {product}: {trade_count} trades")
        
        return count > 0
        
    except Exception as e:
        print(f"❌ Failed to check raw_trades data: {e}")
        return False

def main():
    print("🚀 Complete Migration to Raw Trades System")
    print("=" * 50)
    
    # Verify user intent
    print("⚠️  This will PERMANENTLY remove the trades table and Trade model.")
    print("⚠️  All bot performance data will come from raw_trades only.")
    print("⚠️  This cannot be easily undone.")
    
    confirm = input("\\nProceed with migration? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Migration cancelled")
        sys.exit(1)
    
    # Step 1: Backup
    print("\\n🔄 Step 1: Creating backup...")
    backup_path = backup_database()
    if not backup_path:
        print("❌ Migration aborted - backup failed")
        sys.exit(1)
    
    # Step 2: Verify raw_trades has data
    print("\\n🔄 Step 2: Verifying raw_trades data...")
    if not check_raw_trades_data():
        print("❌ Migration aborted - no raw_trades data found")
        sys.exit(1)
    
    # Step 3: Drop trades table
    print("\\n🔄 Step 3: Dropping trades table...")
    if not drop_trades_table():
        print("❌ Migration aborted - failed to drop table")
        sys.exit(1)
    
    # Step 4: Disable Trade model
    print("\\n🔄 Step 4: Disabling Trade model...")
    if not disable_trade_model():
        print("❌ Migration aborted - failed to disable model")
        sys.exit(1)
    
    print("\\n🎉 Migration completed successfully!")
    print("\\n📋 Next steps:")
    print("   1. Update coinbase_sync_service.py to stop creating Trade objects")
    print("   2. Update bot performance API to use raw_trades")
    print("   3. Update any remaining Trade references to use RawTrade")
    print("   4. Restart the application")
    print(f"\\n💾 Backup saved to: {backup_path}")

if __name__ == "__main__":
    main()
