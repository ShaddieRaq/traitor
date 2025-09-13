#!/usr/bin/env python3
"""
RAW Coinbase Sync - Stores ONLY raw Coinbase data with ZERO calculations.
"""

import sqlite3
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.coinbase_service import CoinbaseService

def sync_raw_coinbase_data():
    """Sync RAW Coinbase fills to raw_trades table with ZERO processing."""
    
    print("🚀 Starting RAW Coinbase sync - NO CALCULATIONS, NO PROCESSING")
    
    coinbase_service = CoinbaseService()
    db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    
    try:
        # Get RAW fills from Coinbase
        raw_fills = coinbase_service.get_raw_fills(days_back=30)
        print(f"📥 Retrieved {len(raw_fills)} RAW fills from Coinbase")
        
        # Store RAW data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        stored_count = 0
        skipped_count = 0
        
        for fill in raw_fills:
            try:
                # Check if already exists
                fill_id = fill.get('trade_id')
                if not fill_id:
                    continue
                    
                cursor.execute("SELECT id FROM raw_trades WHERE fill_id = ?", (fill_id,))
                if cursor.fetchone():
                    skipped_count += 1
                    continue
                
                # Store EXACTLY what Coinbase gives us
                cursor.execute("""
                    INSERT INTO raw_trades (
                        fill_id, order_id, product_id, side,
                        size, size_in_quote, price, commission,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fill.get('trade_id'),
                    fill.get('order_id'),
                    fill.get('product_id'),
                    fill.get('side'),
                    float(fill.get('size')) if fill.get('size') else None,
                    bool(fill.get('size_in_quote')) if fill.get('size_in_quote') is not None else None,
                    float(fill.get('price')) if fill.get('price') else None,
                    float(fill.get('commission')) if fill.get('commission') else None,
                    fill.get('trade_time')
                ))
                
                stored_count += 1
                print(f"✅ Stored RAW: {fill_id} - {fill.get('side')} {fill.get('product_id')} "
                      f"size={fill.get('size')}, size_in_quote={fill.get('size_in_quote')}, "
                      f"price={fill.get('price')}")
                
            except Exception as e:
                print(f"❌ Error storing fill {fill.get('trade_id', 'unknown')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"🎉 RAW sync completed: {stored_count} stored, {skipped_count} skipped")
        
        # Show summary
        show_raw_data_summary()
        
    except Exception as e:
        print(f"💥 RAW sync failed: {e}")

def show_raw_data_summary():
    """Show summary of the raw data we just stored."""
    
    db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 RAW DATA SUMMARY:")
    
    # Total count
    cursor.execute("SELECT COUNT(*) FROM raw_trades")
    total = cursor.fetchone()[0]
    print(f"Total raw trades: {total}")
    
    # Size in quote analysis
    cursor.execute("""
        SELECT 
            size_in_quote,
            COUNT(*) as count
        FROM raw_trades 
        GROUP BY size_in_quote
    """)
    
    print("\nSize in quote analysis:")
    for row in cursor.fetchall():
        size_in_quote, count = row
        print(f"  size_in_quote={bool(size_in_quote)}: {count} trades")
    
    # Sample BTC trades
    cursor.execute("""
        SELECT fill_id, side, size, price, size_in_quote
        FROM raw_trades 
        WHERE product_id = 'BTC-USD' 
        ORDER BY price DESC 
        LIMIT 5
    """)
    
    print("\nSample BTC trades (highest prices):")
    for row in cursor.fetchall():
        fill_id, side, size, price, size_in_quote = row
        print(f"  {fill_id}: {side} {size} BTC @ ${price} (size_in_quote={bool(size_in_quote)})")
    
    conn.close()

if __name__ == "__main__":
    sync_raw_coinbase_data()
