#!/usr/bin/env python3
"""
Add TradingPair table for new pair detection.

This script adds the new trading_pairs table to track newly listed pairs on Coinbase.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_trading_pairs_table():
    """Add the trading_pairs table to the database."""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS trading_pairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id VARCHAR(20) NOT NULL UNIQUE,
        base_currency_id VARCHAR(10) NOT NULL,
        quote_currency_id VARCHAR(10) NOT NULL,
        base_name VARCHAR(100),
        status VARCHAR(20) DEFAULT 'online',
        trading_disabled BOOLEAN DEFAULT 0,
        is_disabled BOOLEAN DEFAULT 0,
        first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_new_listing BOOLEAN DEFAULT 1,
        initial_price REAL,
        initial_volume_24h REAL
    );
    """
    
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_trading_pairs_product_id ON trading_pairs(product_id);
    CREATE INDEX IF NOT EXISTS idx_trading_pairs_quote_currency ON trading_pairs(quote_currency_id);
    CREATE INDEX IF NOT EXISTS idx_trading_pairs_first_seen ON trading_pairs(first_seen);
    CREATE INDEX IF NOT EXISTS idx_trading_pairs_is_new ON trading_pairs(is_new_listing);
    """
    
    try:
        with engine.connect() as conn:
            # Create the table
            logger.info("Creating trading_pairs table...")
            conn.execute(text(create_table_sql))
            
            # Create indexes
            logger.info("Creating indexes...")
            for index_sql in create_index_sql.split(';'):
                if index_sql.strip():
                    conn.execute(text(index_sql))
            
            conn.commit()
            logger.info("✅ Successfully added trading_pairs table and indexes")
            
    except Exception as e:
        logger.error(f"❌ Error adding trading_pairs table: {e}")
        raise

def populate_existing_pairs():
    """Populate the table with existing trading pairs to establish baseline."""
    try:
        from app.services.new_pair_detector import get_new_pair_detector
        from app.core.database import get_db
        
        logger.info("Populating with existing trading pairs...")
        
        db = next(get_db())
        try:
            detector = get_new_pair_detector()
            results = detector.scan_for_new_pairs(db)
            
            if "error" in results:
                logger.error(f"Initial scan failed: {results['error']}")
                return False
            
            total_pairs = results.get("total_products_scanned", 0)
            new_pairs = results.get("new_pairs_found", 0)
            
            logger.info(f"✅ Initial population complete: {total_pairs} total pairs, {new_pairs} tracked as new")
            
            # Mark all existing pairs as processed since they're not "new"
            if new_pairs > 0:
                with engine.connect() as conn:
                    conn.execute(text("UPDATE trading_pairs SET is_new_listing = 0"))
                    conn.commit()
                logger.info("✅ Marked all existing pairs as processed")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error populating existing pairs: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Adding new pair detection table...")
    
    # Add the table
    add_trading_pairs_table()
    
    # Populate with existing pairs
    if populate_existing_pairs():
        logger.info("🎉 New pair detection system ready!")
        logger.info("📝 Summary:")
        logger.info("   • trading_pairs table created")
        logger.info("   • Existing pairs populated as baseline")
        logger.info("   • Future scans will detect truly new listings")
        logger.info("   • API endpoints available at /api/v1/new-pairs/")
    else:
        logger.error("❌ Failed to populate existing pairs - manual intervention may be needed")
