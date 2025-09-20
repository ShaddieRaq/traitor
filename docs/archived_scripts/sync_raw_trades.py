#!/usr/bin/env python3
"""
Raw Coinbase Sync Service - Stores ONLY raw Coinbase payload data.
NO CALCULATIONS. NO TRANSFORMATIONS. JUST RAW DATA.
"""

import sqlite3
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.coinbase_service import CoinbaseService
from app.core.database import get_db

class RawCoinbaseSyncService:
    """Syncs raw Coinbase fill data with ZERO calculations."""
    
    def __init__(self):
        self.coinbase_service = CoinbaseService()
        self.db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    
    def sync_raw_fills(self, limit: int = 100) -> Dict[str, Any]:
        """Sync raw Coinbase fills to raw_trades table."""
        
        print(f"🔄 Starting raw Coinbase fills sync (limit: {limit})")
        
        try:
            # Get fills from Coinbase
            fills_response = self.coinbase_service.get_fills(limit=limit)
            fills = fills_response.get('fills', [])
            
            print(f"📥 Retrieved {len(fills)} fills from Coinbase")
            
            # Store raw fills
            stored_count = 0
            skipped_count = 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for fill in fills:
                try:
                    # Check if already exists
                    fill_id = fill.get('trade_id')
                    cursor.execute("SELECT id FROM raw_trades WHERE fill_id = ?", (fill_id,))
                    if cursor.fetchone():
                        skipped_count += 1
                        continue
                    
                    # Store RAW Coinbase data - NO CALCULATIONS
                    cursor.execute("""
                        INSERT INTO raw_trades (
                            fill_id, order_id, product_id, side,
                            size, size_in_quote, price, size_usd, commission,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        fill.get('trade_id'),
                        fill.get('order_id'),
                        fill.get('product_id'),
                        fill.get('side'),
                        float(fill.get('size', 0)),                    # RAW size from Coinbase
                        bool(fill.get('size_in_quote', False)),        # RAW boolean from Coinbase
                        float(fill.get('price', 0)),                   # RAW price from Coinbase
                        float(fill.get('size_usd', 0)) if fill.get('size_usd') else None,  # RAW USD from Coinbase
                        float(fill.get('commission', 0)) if fill.get('commission') else None,  # RAW commission
                        fill.get('trade_time')                         # RAW timestamp
                    ))
                    
                    stored_count += 1
                    print(f"✅ Stored raw fill: {fill_id} - {fill.get('side')} {fill.get('size')} {fill.get('product_id')} (size_in_quote: {fill.get('size_in_quote')}, size_usd: {fill.get('size_usd')})")
                    
                except Exception as e:
                    print(f"❌ Error storing fill {fill.get('trade_id', 'unknown')}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            result = {
                'status': 'success',
                'stored_count': stored_count,
                'skipped_count': skipped_count,
                'total_processed': len(fills),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"🎉 Raw sync completed: {stored_count} stored, {skipped_count} skipped")
            return result
            
        except Exception as e:
            print(f"💥 Raw sync failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_raw_trades_summary(self) -> Dict[str, Any]:
        """Get summary of raw trades data."""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM raw_trades")
        total_count = cursor.fetchone()[0]
        
        # By product
        cursor.execute("""
            SELECT product_id, COUNT(*), 
                   SUM(CASE WHEN side = 'BUY' THEN size_usd ELSE 0 END) as buy_usd,
                   SUM(CASE WHEN side = 'SELL' THEN size_usd ELSE 0 END) as sell_usd
            FROM raw_trades 
            WHERE size_usd IS NOT NULL
            GROUP BY product_id 
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        products = cursor.fetchall()
        
        # Size in quote analysis
        cursor.execute("""
            SELECT size_in_quote, COUNT(*), 
                   AVG(size_usd) as avg_usd,
                   SUM(size_usd) as total_usd
            FROM raw_trades 
            WHERE size_usd IS NOT NULL
            GROUP BY size_in_quote
        """)
        size_in_quote_analysis = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_raw_trades': total_count,
            'top_products': [
                {
                    'product_id': p[0],
                    'count': p[1], 
                    'buy_usd': p[2],
                    'sell_usd': p[3]
                } for p in products
            ],
            'size_in_quote_analysis': [
                {
                    'size_in_quote': bool(s[0]),
                    'count': s[1],
                    'avg_usd': s[2],
                    'total_usd': s[3]
                } for s in size_in_quote_analysis
            ]
        }

def main():
    """Run the raw sync."""
    sync_service = RawCoinbaseSyncService()
    
    print("🚀 Starting Raw Coinbase Sync")
    
    # Sync fills
    result = sync_service.sync_raw_fills(limit=200)
    print(f"\n📊 Sync Result: {json.dumps(result, indent=2)}")
    
    # Show summary
    summary = sync_service.get_raw_trades_summary()
    print(f"\n📈 Raw Trades Summary: {json.dumps(summary, indent=2)}")

if __name__ == "__main__":
    main()
