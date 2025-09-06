#!/usr/bin/env python3
"""
Check order ID storage in database
"""

import sqlite3
import sys
import os

# Add backend to path for database access
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def main():
    # Check both root and backend databases
    databases = [
        ('Root DB (trader.db)', 'trader.db'),
        ('Backend DB (backend/trader.db)', 'backend/trader.db')
    ]
    
    for db_name, db_path in databases:
        print(f'\n=== {db_name} ===')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            check_database(cursor, db_name)
            conn.close()
        except Exception as e:
            print(f"Error accessing {db_path}: {e}")

def check_database(cursor, db_name):
    try:
        # Check if trades table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        if not cursor.fetchone():
            print(f"No 'trades' table found in {db_name}")
            return

        print('=== TRADE TABLE STRUCTURE ===')
        cursor.execute('PRAGMA table_info(trades)')
        columns = cursor.fetchall()
        for col in columns:
            print(f'{col[1]} ({col[2]}) - Nullable: {not col[3]}')

        print('\n=== RECENT TRADES WITH ORDER_ID STATUS ===')
        cursor.execute("""
            SELECT id, bot_id, side, size_usd, price, order_id, status, created_at 
            FROM trades 
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        trades = cursor.fetchall()

        if trades:
            print('ID | Bot | Side | Size | Price | Order_ID | Status | Created')
            print('-' * 80)
            for trade in trades:
                order_id = trade[5] if trade[5] else 'NULL'
                size_usd = trade[3] if trade[3] else 0
                price = trade[4] if trade[4] else 0
                print(f'{trade[0]} | {trade[1]} | {trade[2]} | ${size_usd:.2f} | ${price:.2f} | {order_id} | {trade[6]} | {trade[7]}')
        else:
            print('No trades found')

        print('\n=== ORDER_ID STATISTICS ===')
        cursor.execute('SELECT COUNT(*) as total_trades FROM trades')
        total = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) as trades_with_order_id FROM trades WHERE order_id IS NOT NULL AND order_id != ""')
        with_order_id = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) as trades_without_order_id FROM trades WHERE order_id IS NULL OR order_id = ""')
        without_order_id = cursor.fetchone()[0]

        print(f'Total trades: {total}')
        print(f'Trades with order_id: {with_order_id}')  
        print(f'Trades without order_id: {without_order_id}')

        if total > 0:
            print(f'Percentage with order_id: {(with_order_id/total)*100:.1f}%')

            # Check specific order_id examples
            print('\n=== SAMPLE ORDER_IDs (non-null) ===')
            cursor.execute("""
                SELECT id, order_id, status, created_at 
                FROM trades 
                WHERE order_id IS NOT NULL AND order_id != ""
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            order_samples = cursor.fetchall()
            
            for sample in order_samples:
                print(f'Trade {sample[0]}: {sample[1]} (status: {sample[2]}) - {sample[3]}')
    
    except Exception as e:
        print(f"Error checking database {db_name}: {e}")

if __name__ == "__main__":
    main()
