#!/usr/bin/env python3
"""
Database Wipe and Resync Script
1. Backup current database
2. Wipe all trades
3. Resync from Coinbase
"""

import sys
import os
import sqlite3
import shutil
from datetime import datetime
import requests
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def backup_database():
    """Create a backup of the current database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backend/trader_backup_{timestamp}.db"
    
    try:
        shutil.copy2("backend/trader.db", backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def wipe_trades():
    """Wipe all trades from the database."""
    try:
        conn = sqlite3.connect('backend/trader.db')
        cursor = conn.cursor()
        
        # Count trades before deletion
        cursor.execute('SELECT COUNT(*) FROM trades')
        before_count = cursor.fetchone()[0]
        print(f"📊 Trades before wipe: {before_count}")
        
        # Delete all trades
        cursor.execute('DELETE FROM trades')
        deleted_count = cursor.rowcount
        
        # Reset auto-increment counter
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="trades"')
        
        conn.commit()
        conn.close()
        
        print(f"🗑️  Wiped {deleted_count} trades from database")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Wipe failed: {e}")
        return 0

def resync_trades(days_back=30):
    """Resync trades from Coinbase."""
    try:
        print(f"🔄 Starting resync for last {days_back} days...")
        
        # Call the sync API endpoint
        response = requests.post(
            f"http://localhost:8000/api/v1/coinbase-sync/sync-coinbase-trades?days_back={days_back}",
            timeout=120  # Give it 2 minutes to complete
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Resync successful!")
            print(f"   Coinbase fills found: {result.get('coinbase_fills_found', 0)}")
            print(f"   New trades synced: {result.get('new_trades_synced', 0)}")
            print(f"   Existing trades skipped: {result.get('existing_trades_skipped', 0)}")
            return result
        else:
            print(f"❌ Resync failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Resync failed: {e}")
        return None

def verify_results():
    """Verify the results after wipe and resync."""
    try:
        conn = sqlite3.connect('backend/trader.db')
        cursor = conn.cursor()
        
        # Count total trades
        cursor.execute('SELECT COUNT(*) FROM trades')
        total_trades = cursor.fetchone()[0]
        
        # Count trades with order_ids
        cursor.execute('SELECT COUNT(*) FROM trades WHERE order_id IS NOT NULL AND order_id != ""')
        with_order_id = cursor.fetchone()[0]
        
        # Count trades without order_ids
        cursor.execute('SELECT COUNT(*) FROM trades WHERE order_id IS NULL OR order_id = ""')
        without_order_id = cursor.fetchone()[0]
        
        print(f"📊 RESULTS AFTER WIPE AND RESYNC:")
        print(f"   Total trades: {total_trades}")
        print(f"   Trades with order_id: {with_order_id} ({(with_order_id/total_trades)*100:.1f}%)" if total_trades > 0 else "   Trades with order_id: 0")
        print(f"   Trades without order_id: {without_order_id}")
        
        if total_trades > 0:
            # Show recent trades
            print(f"\\n📋 SAMPLE RECENT TRADES:")
            cursor.execute('''
                SELECT id, side, size_usd, order_id, status, created_at
                FROM trades 
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
            trades = cursor.fetchall()
            
            print("ID | Side | Size | Order_ID | Status | Created")
            print("-" * 60)
            for trade in trades:
                order_id = trade[3] if trade[3] else 'NULL'
                size_usd = trade[2] if trade[2] else 0
                print(f"{trade[0]} | {trade[1]} | ${size_usd:.2f} | {order_id} | {trade[4]} | {trade[5]}")
        
        conn.close()
        
        # Validate results
        if total_trades == 0:
            print("⚠️  No trades found after resync - may indicate API issues")
        elif without_order_id > 0:
            print("⚠️  Some trades still lack order_ids - investigate sync logic")
        else:
            print("✅ All trades have order_ids - sync successful!")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")

def main():
    print("=== DATABASE WIPE AND RESYNC ===")
    print()
    
    # Step 1: Backup
    print("STEP 1: Creating backup...")
    backup_path = backup_database()
    if not backup_path:
        print("❌ Cannot proceed without successful backup")
        return
    
    # Step 2: Wipe
    print("\\nSTEP 2: Wiping trades...")
    deleted_count = wipe_trades()
    if deleted_count == 0:
        print("❌ No trades to wipe or wipe failed")
    
    # Step 3: Resync
    print("\\nSTEP 3: Resyncing from Coinbase...")
    resync_result = resync_trades(days_back=30)  # Get last 30 days
    
    # Step 4: Verify
    print("\\nSTEP 4: Verifying results...")
    verify_results()
    
    print("\\n=== SUMMARY ===")
    print(f"✅ Backup created: {backup_path}")
    print(f"✅ Trades wiped: {deleted_count}")
    if resync_result:
        print(f"✅ Resync completed: {resync_result.get('new_trades_synced', 0)} trades")
    else:
        print("❌ Resync failed")
    
    print("\\n🎯 Result: Database now contains only real Coinbase trades with order_ids")

if __name__ == "__main__":
    main()
