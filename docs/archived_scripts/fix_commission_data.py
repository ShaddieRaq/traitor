#!/usr/bin/env python3
"""
One-time script to update existing trades with commission data from raw_trades table.
This fixes the historical trades that were synced before the commission bug was fixed.
"""

import sqlite3
import sys
from datetime import datetime

def fix_commission_data():
    """Update trades table with commission data from raw_trades table."""
    
    db_path = "/Users/lazy_genius/Projects/trader/backend/trader.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Finding trades with missing commission data...")
        
        # Find trades with NULL commission that have matching data in raw_trades
        cursor.execute("""
            SELECT t.id, t.order_id, t.product_id, t.side, t.price, t.size,
                   SUM(rt.commission) as total_commission,
                   COUNT(rt.commission) as fill_count
            FROM trades t 
            JOIN raw_trades rt ON t.order_id = rt.order_id
            WHERE (t.commission IS NULL OR t.commission = 0)
              AND rt.commission IS NOT NULL 
              AND rt.commission > 0
            GROUP BY t.id, t.order_id, t.product_id, t.side, t.price, t.size
            ORDER BY t.id
        """)
        
        trades_to_update = cursor.fetchall()
        
        if not trades_to_update:
            print("✅ No trades found that need commission updates")
            return
        
        print(f"📊 Found {len(trades_to_update)} trades that need commission updates")
        
        # Show what we're about to update
        print("\\nUpdates to be made:")
        for trade in trades_to_update[:10]:  # Show first 10
            trade_id, order_id, product_id, side, price, size, total_commission, fill_count = trade
            print(f"  Trade {trade_id}: {side} {product_id} -> commission: {total_commission:.8f} (from {fill_count} fills)")
        
        if len(trades_to_update) > 10:
            print(f"  ... and {len(trades_to_update) - 10} more")
        
        # Ask for confirmation
        confirm = input(f"\\n🤔 Update {len(trades_to_update)} trades with commission data? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Operation cancelled")
            return
        
        # Update trades with commission data
        updated_count = 0
        for trade in trades_to_update:
            trade_id, order_id, product_id, side, price, size, total_commission, fill_count = trade
            
            try:
                cursor.execute("""
                    UPDATE trades 
                    SET commission = ?
                    WHERE id = ?
                """, (total_commission, trade_id))
                
                updated_count += 1
                
                if updated_count % 50 == 0:
                    print(f"  Updated {updated_count}/{len(trades_to_update)} trades...")
                    
            except Exception as e:
                print(f"❌ Error updating trade {trade_id}: {e}")
                continue
        
        # Commit all changes
        conn.commit()
        
        print(f"\\n✅ Successfully updated {updated_count} trades with commission data")
        
        # Verify the updates
        print("\\n🔍 Verifying updates...")
        cursor.execute("""
            SELECT product_id, 
                   COUNT(*) as total_trades,
                   COUNT(CASE WHEN commission IS NOT NULL AND commission > 0 THEN 1 END) as trades_with_commission,
                   SUM(CASE WHEN commission IS NOT NULL THEN commission ELSE 0 END) as total_commission
            FROM trades 
            WHERE product_id IN ('BONK-USD', 'BTC-USD', 'ETH-USD', 'SOL-USD')
            GROUP BY product_id
            ORDER BY total_trades DESC
        """)
        
        verification = cursor.fetchall()
        print("\\nCommission status by product:")
        for product_id, total, with_commission, total_comm in verification:
            percentage = (with_commission / total * 100) if total > 0 else 0
            print(f"  {product_id}: {with_commission}/{total} trades ({percentage:.1f}%) - Total fees: ${total_comm:.4f}")
        
        conn.close()
        
    except Exception as e:
        print(f"💥 Error fixing commission data: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Commission Data Fix Script")
    print("=" * 40)
    
    success = fix_commission_data()
    
    if success:
        print("\\n🎉 Commission data fix completed successfully!")
    else:
        print("\\n❌ Commission data fix failed!")
        sys.exit(1)
