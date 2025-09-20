#!/usr/bin/env python3
"""
Data Integrity Fix Script
Clean up phantom trades and ensure trades table matches raw Coinbase data.
"""

import sqlite3
import sys
from datetime import datetime

def analyze_data_corruption():
    """Analyze the extent of data corruption across all products."""
    
    db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Analyzing Data Corruption Across All Products...")
        print("=" * 60)
        
        # Check corruption by product
        cursor.execute("""
            SELECT 
                COALESCE(t.product_id, rt.product_id) as product_id,
                COUNT(DISTINCT t.order_id) as trades_count,
                COUNT(DISTINCT rt.order_id) as raw_trades_count,
                COUNT(DISTINCT t.order_id) - COUNT(DISTINCT rt.order_id) as phantom_trades,
                SUM(CASE WHEN t.side = 'BUY' AND rt.order_id IS NOT NULL THEN t.size ELSE 0 END) as verified_bought,
                SUM(CASE WHEN t.side = 'SELL' AND rt.order_id IS NOT NULL THEN t.size ELSE 0 END) as verified_sold,
                SUM(CASE WHEN rt.side = 'BUY' THEN rt.size ELSE 0 END) as actual_bought,
                SUM(CASE WHEN rt.side = 'SELL' THEN rt.size ELSE 0 END) as actual_sold
            FROM trades t
            FULL OUTER JOIN raw_trades rt ON t.order_id = rt.order_id
            WHERE COALESCE(t.product_id, rt.product_id) IN ('XRP-USD', 'BONK-USD', 'AVNT-USD', 'BTC-USD', 'ETH-USD', 'SOL-USD')
            GROUP BY COALESCE(t.product_id, rt.product_id)
            ORDER BY phantom_trades DESC
        """)
        
        results = cursor.fetchall()
        
        print(f"{'Product':<10} {'Trades':<8} {'Raw':<8} {'Phantom':<8} {'Status'}")
        print("-" * 50)
        
        total_phantom = 0
        corrupted_products = []
        
        for row in results:
            product_id, trades_count, raw_count, phantom, verified_bought, verified_sold, actual_bought, actual_sold = row
            total_phantom += phantom
            
            status = "✅ CLEAN" if phantom == 0 else "❌ CORRUPT"
            if phantom > 0:
                corrupted_products.append(product_id)
            
            print(f"{product_id:<10} {trades_count:<8} {raw_count:<8} {phantom:<8} {status}")
        
        print(f"\\n📊 Summary:")
        print(f"   Total Phantom Trades: {total_phantom}")
        print(f"   Corrupted Products: {len(corrupted_products)}")
        print(f"   Affected: {', '.join(corrupted_products) if corrupted_products else 'None'}")
        
        # Check specific XRP discrepancy
        if 'XRP-USD' in corrupted_products:
            print(f"\\n🔍 XRP-USD Detailed Analysis:")
            
            # Get current balance calculation
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN side = 'BUY' THEN size ELSE -size END) as net_from_trades,
                    SUM(CASE WHEN rt.side = 'BUY' THEN rt.size ELSE -rt.size END) as net_from_raw
                FROM trades t
                LEFT JOIN raw_trades rt ON t.order_id = rt.order_id  
                WHERE t.product_id = 'XRP-USD'
            """)
            
            net_trades, net_raw = cursor.fetchone()
            
            print(f"   Net from trades table: {net_trades:.2f} XRP")
            print(f"   Net from raw Coinbase: {net_raw:.2f} XRP") 
            print(f"   Difference: {(net_trades or 0) - (net_raw or 0):.2f} XRP")
        
        conn.close()
        return corrupted_products
        
    except Exception as e:
        print(f"💥 Error analyzing data: {e}")
        return []

def fix_data_corruption(dry_run=True):
    """Fix data corruption by removing phantom trades."""
    
    db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\\n🔧 {'DRY RUN: ' if dry_run else ''}Fixing Data Corruption...")
        print("=" * 50)
        
        # Find phantom trades (trades without corresponding raw_trades)
        cursor.execute("""
            SELECT t.id, t.product_id, t.side, t.size, t.order_id, t.created_at
            FROM trades t
            LEFT JOIN raw_trades rt ON t.order_id = rt.order_id
            WHERE rt.order_id IS NULL
            ORDER BY t.product_id, t.created_at
        """)
        
        phantom_trades = cursor.fetchall()
        
        if not phantom_trades:
            print("✅ No phantom trades found!")
            return True
        
        print(f"Found {len(phantom_trades)} phantom trades:")
        
        # Group by product for summary
        by_product = {}
        for trade in phantom_trades:
            product = trade[1]
            if product not in by_product:
                by_product[product] = []
            by_product[product].append(trade)
        
        for product, trades in by_product.items():
            print(f"\\n{product}: {len(trades)} phantom trades")
            for trade in trades[:5]:  # Show first 5
                trade_id, product_id, side, size, order_id, created_at = trade
                print(f"  Trade {trade_id}: {side} {size} @ {created_at[:19]}")
            if len(trades) > 5:
                print(f"  ... and {len(trades) - 5} more")
        
        if not dry_run:
            # Ask for confirmation
            confirm = input(f"\\n⚠️  DELETE {len(phantom_trades)} phantom trades? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Operation cancelled")
                return False
            
            # Delete phantom trades
            phantom_ids = [str(trade[0]) for trade in phantom_trades]
            cursor.execute(f"DELETE FROM trades WHERE id IN ({','.join(phantom_ids)})")
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"✅ Deleted {deleted_count} phantom trades")
        else:
            print(f"\\n🔍 DRY RUN: Would delete {len(phantom_trades)} phantom trades")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"💥 Error fixing data: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Data Integrity Analysis & Fix")
    print("=" * 40)
    
    # Analyze corruption
    corrupted_products = analyze_data_corruption()
    
    if not corrupted_products:
        print("\\n🎉 No data corruption found!")
        sys.exit(0)
    
    # Offer to fix
    print(f"\\n🤔 Run data cleanup? (dry run first)")
    response = input("Enter 'dry' for dry run, 'fix' to actually fix, or 'n' to skip: ")
    
    if response.lower() == 'dry':
        fix_data_corruption(dry_run=True)
    elif response.lower() == 'fix':
        success = fix_data_corruption(dry_run=False)
        if success:
            print("\\n🔄 Re-analyzing after cleanup...")
            analyze_data_corruption()
    else:
        print("❌ Skipping data cleanup")
