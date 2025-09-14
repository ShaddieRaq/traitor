#!/usr/bin/env python3

import sqlite3

def main():
    conn = sqlite3.connect('trader.db')
    cursor = conn.cursor()

    # Check total P&L using the corrupted size_usd values
    cursor.execute("""
    SELECT 
        SUM(CASE WHEN side = 'BUY' THEN -size_usd ELSE size_usd END) as total_pnl_corrupted,
        COUNT(*) as total_trades
    FROM trades 
    WHERE status = 'filled'
    """)

    result = cursor.fetchone()
    corrupted_pnl, total_trades = result[0], result[1]

    # Check what the correct P&L should be using raw data logic
    cursor.execute("""
    SELECT 
        SUM(CASE 
            WHEN r.side = 'BUY' THEN 
                CASE WHEN r.size_in_quote = 1 THEN -r.size ELSE -(r.size * r.price) END
            ELSE 
                CASE WHEN r.size_in_quote = 1 THEN r.size ELSE (r.size * r.price) END
        END) as correct_pnl,
        COUNT(*) as raw_trades
    FROM raw_trades r
    WHERE r.fill_id IN (SELECT order_id FROM trades WHERE status = 'filled')
    """)

    result2 = cursor.fetchone()
    correct_pnl, raw_trades = result2[0], result2[1]

    print(f"CORRUPTED P&L (using size_usd): ${corrupted_pnl:.6f}")
    print(f"CORRECT P&L (using raw logic): ${correct_pnl:.6f}")
    print(f"DIFFERENCE: ${abs(correct_pnl - corrupted_pnl):.6f}")
    print(f"Trades: {total_trades} processed, {raw_trades} raw")

    # Show the problematic trades
    print("\n=== PROBLEMATIC TRADES (size_in_quote=True) ===")
    cursor.execute("""
    SELECT r.fill_id, r.side, r.product_id, r.size as raw_size, r.price, r.size_in_quote,
           t.size as processed_size, t.size_usd, t.size_in_quote as processed_size_in_quote
    FROM raw_trades r
    LEFT JOIN trades t ON r.fill_id = t.order_id
    WHERE r.size_in_quote = 1
    """)

    for row in cursor.fetchall():
        fill_id, side, product_id, raw_size, price, raw_size_in_quote, processed_size, size_usd, processed_size_in_quote = row
        if raw_size_in_quote == 1:  # USD amount, not asset quantity
            correct_usd = raw_size  # For size_in_quote=True, size IS the USD amount
            correct_asset_qty = raw_size / price  # Convert USD to asset quantity
        else:
            correct_usd = raw_size * price
            correct_asset_qty = raw_size
        
        print(f"{fill_id}: {side} {product_id}")
        print(f"  Raw: size={raw_size} (USD amount since size_in_quote=True), price=${price}")
        print(f"  Should be: asset_qty={correct_asset_qty:.8f}, usd_amount=${correct_usd}")
        print(f"  Stored as: size={processed_size}, size_usd=${size_usd}, size_in_quote={processed_size_in_quote}")
        print(f"  ERROR: USD amount wrong by ${abs(correct_usd - size_usd):.6f}")
        print()

    conn.close()

if __name__ == "__main__":
    main()
