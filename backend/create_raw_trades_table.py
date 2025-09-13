#!/usr/bin/env python3
"""
Create a new raw_trades table that stores actual Coinbase payload data.
Store the ACTUAL VALUES, not strings.
"""

import sqlite3

def create_raw_trades_table():
    """Create a new table that stores actual Coinbase fill payload data."""
    
    db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing table if it exists
    cursor.execute("DROP TABLE IF EXISTS raw_trades")
    
    # Create new table with actual Coinbase payload fields
    cursor.execute("""
        CREATE TABLE raw_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Coinbase fill payload data (ACTUAL VALUES)
            fill_id TEXT UNIQUE NOT NULL,           -- Coinbase fill ID
            order_id TEXT NOT NULL,                 -- Coinbase order ID
            product_id TEXT NOT NULL,               -- e.g. "BTC-USD"
            side TEXT NOT NULL,                     -- "BUY" or "SELL"
            
            -- Actual numeric values from Coinbase
            size REAL NOT NULL,                     -- Actual size number
            size_in_quote BOOLEAN NOT NULL,         -- Coinbase's boolean flag
            price REAL NOT NULL,                    -- Actual price number
            size_usd REAL,                          -- Actual USD value from Coinbase
            
            -- Actual fee value
            commission REAL,                        -- Actual commission number
            
            -- Timestamp
            created_at TEXT NOT NULL,               -- ISO timestamp
            
            -- Metadata
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_raw_trades_fill_id ON raw_trades(fill_id)")
    cursor.execute("CREATE INDEX idx_raw_trades_order_id ON raw_trades(order_id)")
    cursor.execute("CREATE INDEX idx_raw_trades_product_id ON raw_trades(product_id)")
    
    conn.commit()
    conn.close()
    
    print("✅ Created raw_trades table with actual Coinbase payload values")

if __name__ == "__main__":
    create_raw_trades_table()
