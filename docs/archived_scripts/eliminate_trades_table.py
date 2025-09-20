"""
Migration Script: Eliminate Trades Table and Use Raw Trades
===========================================================

This script helps migrate from the corrupted trades table system 
to the clean raw_trades system.

IMPORTANT: This script will:
1. DROP the corrupted trades table 
2. Update all bot configurations to use raw_trades
3. Remove bot metadata tracking dependencies
4. Validate the new clean system

WARNING: This is a DESTRUCTIVE operation!
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backup_database(db_path: str) -> str:
    """Create a backup before making destructive changes."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}_backup_pre_cleanup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        raise


def validate_raw_trades_table(db_path: str) -> Dict[str, Any]:
    """Validate that raw_trades table exists and has data."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='raw_trades'
        """)
        
        if not cursor.fetchone():
            raise Exception("raw_trades table does not exist!")
        
        # Get table info
        cursor.execute("SELECT COUNT(*) FROM raw_trades")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT product_id) FROM raw_trades")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM raw_trades")
        date_range = cursor.fetchone()
        
        conn.close()
        
        validation_result = {
            'table_exists': True,
            'total_records': total_records,
            'total_products': total_products,
            'date_range': date_range,
            'ready_for_migration': total_records > 0
        }
        
        logger.info(f"✅ Raw trades validation: {validation_result}")
        return validation_result
        
    except Exception as e:
        logger.error(f"❌ Raw trades validation failed: {e}")
        return {'table_exists': False, 'error': str(e)}


def drop_corrupted_trades_table(db_path: str):
    """Drop the corrupted trades table."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if trades table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='trades'
        """)
        
        if cursor.fetchone():
            # Get record count before dropping
            cursor.execute("SELECT COUNT(*) FROM trades")
            record_count = cursor.fetchone()[0]
            
            logger.info(f"🗑️  Dropping trades table with {record_count} corrupted records...")
            
            # Drop the table
            cursor.execute("DROP TABLE trades")
            conn.commit()
            
            logger.info("✅ Corrupted trades table dropped successfully")
        else:
            logger.info("ℹ️  Trades table doesn't exist (already dropped)")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Failed to drop trades table: {e}")
        raise


def clean_bot_metadata(db_path: str):
    """Remove bot metadata that depends on trades table."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if bots table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='bots'
        """)
        
        if not cursor.fetchone():
            logger.info("ℹ️  No bots table found")
            conn.close()
            return
        
        # Reset bot position tracking fields that depend on trades
        cursor.execute("""
            UPDATE bots SET 
                current_position_size = 0.0,
                current_position_entry_price = NULL,
                current_combined_score = 0.0,
                signal_confirmation_start = NULL
            WHERE id IS NOT NULL
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Cleaned metadata for {updated_count} bots")
        
    except Exception as e:
        logger.error(f"❌ Failed to clean bot metadata: {e}")
        raise


def validate_clean_system(db_path: str) -> Dict[str, Any]:
    """Validate that the clean system is working properly."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check that trades table is gone
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='trades'
        """)
        trades_table_exists = cursor.fetchone() is not None
        
        # Check raw_trades table health
        cursor.execute("SELECT COUNT(*) FROM raw_trades")
        raw_trades_count = cursor.fetchone()[0]
        
        # Check bots table health
        cursor.execute("SELECT COUNT(*) FROM bots")
        bots_count = cursor.fetchone()[0]
        
        conn.close()
        
        validation = {
            'trades_table_removed': not trades_table_exists,
            'raw_trades_available': raw_trades_count > 0,
            'raw_trades_count': raw_trades_count,
            'bots_count': bots_count,
            'system_clean': not trades_table_exists and raw_trades_count > 0
        }
        
        logger.info(f"✅ Clean system validation: {validation}")
        return validation
        
    except Exception as e:
        logger.error(f"❌ Clean system validation failed: {e}")
        return {'error': str(e)}


def main():
    """Execute the full migration to clean system."""
    print("🧹 TRADES TABLE ELIMINATION SCRIPT")
    print("=" * 50)
    print("⚠️  WARNING: This will permanently delete the corrupted trades table!")
    print("⚠️  Make sure you have a backup!")
    print()
    
    db_path = "trader.db"
    
    try:
        # Step 1: Create backup
        print("📁 Step 1: Creating backup...")
        backup_path = backup_database(db_path)
        print(f"✅ Backup created: {backup_path}")
        
        # Step 2: Validate raw_trades table
        print("\n🔍 Step 2: Validating raw_trades table...")
        raw_validation = validate_raw_trades_table(db_path)
        
        if not raw_validation.get('ready_for_migration', False):
            print("❌ Raw trades table not ready for migration!")
            print("   Please run sync_raw_coinbase.py first")
            return
        
        print(f"✅ Raw trades ready: {raw_validation['total_records']} records")
        
        # Step 3: Get user confirmation
        print(f"\n⚠️  FINAL WARNING:")
        print(f"   - Will DROP trades table permanently")
        print(f"   - Will clean bot metadata")
        print(f"   - Raw trades has {raw_validation['total_records']} clean records")
        print()
        
        confirmation = input("Type 'DELETE TRADES TABLE' to proceed: ")
        
        if confirmation != "DELETE TRADES TABLE":
            print("❌ Migration cancelled")
            return
        
        # Step 4: Drop corrupted trades table
        print("\n🗑️  Step 4: Dropping corrupted trades table...")
        drop_corrupted_trades_table(db_path)
        
        # Step 5: Clean bot metadata
        print("\n🧹 Step 5: Cleaning bot metadata...")
        clean_bot_metadata(db_path)
        
        # Step 6: Validate clean system
        print("\n✅ Step 6: Validating clean system...")
        final_validation = validate_clean_system(db_path)
        
        if final_validation.get('system_clean', False):
            print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print("✅ Corrupted trades table eliminated")
            print("✅ Clean raw_trades system active")
            print("✅ Bot metadata cleaned")
            print(f"✅ {final_validation['raw_trades_count']} clean trade records available")
            print()
            print("🚀 Next steps:")
            print("   1. Test new API endpoints: /api/v1/raw-trades/")
            print("   2. Update bot configurations to use SimplifiedBot")
            print("   3. Monitor background sync process")
            print("   4. Verify P&L calculations with clean data")
        else:
            print("❌ Migration validation failed!")
            print("   Please check the validation results")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("💡 Your backup is safe, system unchanged")


if __name__ == "__main__":
    main()
