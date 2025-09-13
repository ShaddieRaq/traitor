#!/usr/bin/env python3
"""
Calculate P&L by trading pair using clean raw Coinbase data.
This uses the raw_trades table to avoid any processing corruption.
"""

import sqlite3
from collections import defaultdict

def calculate_pnl_by_pair():
    conn = sqlite3.connect('trader.db')
    cursor = conn.cursor()
    
    # Get all raw trades data
    cursor.execute('''
    SELECT fill_id, product_id, side, size, price, size_in_quote, commission, created_at
    FROM raw_trades 
    ORDER BY created_at ASC
    ''')
    
    trades = cursor.fetchall()
    
    # Group by product_id and calculate P&L
    pair_data = defaultdict(lambda: {
        'trades': [],
        'buy_volume_usd': 0,
        'sell_volume_usd': 0,
        'total_commission': 0,
        'trade_count': 0,
        'buy_count': 0,
        'sell_count': 0
    })
    
    print("🔍 Processing trades by pair...")
    
    for trade in trades:
        fill_id, product_id, side, size, price, size_in_quote, commission, created_at = trade
        
        # Calculate USD amount based on size_in_quote flag
        if size_in_quote:
            # size field represents USD amount spent/received
            usd_amount = size
            asset_quantity = size / price
        else:
            # size field represents asset quantity
            asset_quantity = size
            usd_amount = size * price
        
        # Store trade data
        pair_data[product_id]['trades'].append({
            'fill_id': fill_id,
            'side': side,
            'asset_quantity': asset_quantity,
            'usd_amount': usd_amount,
            'price': price,
            'commission': commission or 0,
            'created_at': created_at
        })
        
        # Update aggregates
        pair_data[product_id]['trade_count'] += 1
        pair_data[product_id]['total_commission'] += commission or 0
        
        if side == 'BUY':
            pair_data[product_id]['buy_volume_usd'] += usd_amount
            pair_data[product_id]['buy_count'] += 1
        else:
            pair_data[product_id]['sell_volume_usd'] += usd_amount
            pair_data[product_id]['sell_count'] += 1
    
    # Calculate P&L for each pair
    print("\n📊 P&L BY TRADING PAIR")
    print("=" * 80)
    
    total_pnl = 0
    total_commission = 0
    
    for product_id in sorted(pair_data.keys()):
        data = pair_data[product_id]
        
        # Calculate net P&L (money out - money in)
        net_pnl = data['sell_volume_usd'] - data['buy_volume_usd']
        
        # Calculate net P&L after commissions
        net_pnl_after_fees = net_pnl - data['total_commission']
        
        print(f"\n🪙 {product_id}")
        print(f"   Trades: {data['trade_count']} ({data['buy_count']} BUY, {data['sell_count']} SELL)")
        print(f"   Buy Volume:  ${data['buy_volume_usd']:,.2f}")
        print(f"   Sell Volume: ${data['sell_volume_usd']:,.2f}")
        print(f"   Gross P&L:   ${net_pnl:,.6f}")
        print(f"   Commissions: ${data['total_commission']:,.6f}")
        print(f"   Net P&L:     ${net_pnl_after_fees:,.6f}")
        
        # Show recent trades for context
        recent_trades = sorted(data['trades'], key=lambda x: x['created_at'])[-3:]
        print(f"   Recent trades:")
        for trade in recent_trades:
            print(f"     {trade['created_at'][:16]} {trade['side']} {trade['asset_quantity']:.8f} @ ${trade['price']:.2f} = ${trade['usd_amount']:.2f}")
        
        total_pnl += net_pnl_after_fees
        total_commission += data['total_commission']
    
    print("\n" + "=" * 80)
    print(f"🎯 OVERALL PORTFOLIO")
    print(f"   Total Pairs: {len(pair_data)}")
    print(f"   Total Trades: {sum(d['trade_count'] for d in pair_data.values())}")
    print(f"   Total Commissions: ${total_commission:,.6f}")
    print(f"   TOTAL NET P&L: ${total_pnl:,.6f}")
    
    # Compare with corrupted data
    cursor.execute('''
    SELECT SUM(CASE WHEN side = 'BUY' THEN -size_usd ELSE size_usd END) as corrupted_pnl
    FROM trades WHERE status = 'filled'
    ''')
    corrupted_pnl = cursor.fetchone()[0]
    
    print(f"\n🔍 VALIDATION")
    print(f"   Clean Raw Data P&L: ${total_pnl:,.6f}")
    print(f"   Corrupted DB P&L:   ${corrupted_pnl:,.6f}")
    print(f"   Difference:         ${abs(total_pnl - corrupted_pnl):,.6f}")
    
    conn.close()
    
    return pair_data, total_pnl

if __name__ == "__main__":
    calculate_pnl_by_pair()
