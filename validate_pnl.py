#!/usr/bin/env python3
import sqlite3

def validate_pnl():
    conn = sqlite3.connect('backend/trader.db')
    cursor = conn.cursor()
    
    print('🔍 COMPREHENSIVE P&L VALIDATION')
    print('=' * 60)
    
    # 1. Check data integrity
    print('1. DATA INTEGRITY CHECK:')
    cursor.execute('''
        SELECT COUNT(*) 
        FROM trades 
        WHERE ABS((size * price) - size_usd) > 0.01
        AND order_id IS NOT NULL
    ''')
    corrupt_count = cursor.fetchone()[0]
    print(f'   Corrupt trades: {corrupt_count}')
    
    if corrupt_count > 0:
        print('   🚨 ERROR: Database still has corrupted data!')
        return False
    else:
        print('   ✅ All trades have consistent size×price = size_usd')
    
    print()
    
    # 2. Manual position calculations
    print('2. MANUAL POSITION CALCULATIONS:')
    cursor.execute('''
        SELECT 
            product_id,
            COUNT(*) as trades,
            SUM(CASE WHEN side='BUY' THEN size ELSE -size END) as position,
            SUM(CASE WHEN side='BUY' THEN size_usd ELSE -size_usd END) as net_cash,
            SUM(CASE WHEN side='BUY' THEN size_usd ELSE 0 END) as spent,
            SUM(CASE WHEN side='SELL' THEN size_usd ELSE 0 END) as received
        FROM trades 
        WHERE order_id IS NOT NULL AND order_id != ''
        GROUP BY product_id
        HAVING COUNT(*) >= 20
        ORDER BY COUNT(*) DESC
        LIMIT 8
    ''')
    
    results = cursor.fetchall()
    for row in results:
        product_id, trades, position, net_cash, spent, received = row
        realized_pnl = received - spent
        
        print(f'   {product_id}:')
        print(f'     {trades} trades, {position:.6f} position')
        print(f'     Spent: ${spent:.2f}, Received: ${received:.2f}')
        print(f'     Net cash: ${net_cash:.2f}, Realized P&L: ${realized_pnl:.2f}')
        
        # Validation checks
        issues = []
        if position < -0.001:  # Allow for small rounding
            issues.append('NEGATIVE POSITION')
        if abs(net_cash) > 50000:  # Unreasonably large
            issues.append('EXCESSIVE CASH FLOW')
        if spent == 0 and received > 0:
            issues.append('RECEIVED WITHOUT SPENDING')
        
        if issues:
            print(f'     🚨 ISSUES: {" | ".join(issues)}')
        else:
            print(f'     ✅ Looks reasonable')
        print()
    
    # 3. Specific DOGE validation
    print('3. SPECIFIC DOGE VALIDATION:')
    cursor.execute('''
        SELECT 
            COUNT(*) as trades,
            SUM(CASE WHEN side='BUY' THEN size ELSE -size END) as position,
            SUM(CASE WHEN side='BUY' THEN size_usd ELSE -size_usd END) as net_cash,
            SUM(CASE WHEN side='BUY' THEN size_usd ELSE 0 END) as spent,
            SUM(CASE WHEN side='SELL' THEN size_usd ELSE 0 END) as received
        FROM trades 
        WHERE product_id = 'DOGE-USD' AND order_id IS NOT NULL
    ''')
    
    doge_data = cursor.fetchone()
    trades, position, net_cash, spent, received = doge_data
    
    print(f'   Manual DOGE calculation:')
    print(f'     Trades: {trades}')
    print(f'     Position: {position:.6f} DOGE')
    print(f'     Spent: ${spent:.2f}')
    print(f'     Received: ${received:.2f}')
    print(f'     Net cash: ${net_cash:.2f}')
    
    # Expected values from previous analysis
    expected_position = 118.6
    expected_net_cash = -29.2  # Negative because we spent more than received
    expected_trades = 110
    
    position_ok = abs(position - expected_position) < 1.0
    cash_ok = abs(net_cash - expected_net_cash) < 5.0
    trades_ok = trades == expected_trades
    
    if position_ok and cash_ok and trades_ok:
        print('   ✅ DOGE validation PASSED - matches expected values')
    else:
        print('   ❌ DOGE validation FAILED:')
        if not position_ok:
            print(f'      Position: got {position:.6f}, expected ~{expected_position}')
        if not cash_ok:
            print(f'      Net cash: got ${net_cash:.2f}, expected ~${expected_net_cash}')
        if not trades_ok:
            print(f'      Trades: got {trades}, expected {expected_trades}')
    
    print()
    
    # 4. Compare with API
    print('4. FINAL VALIDATION:')
    if corrupt_count == 0:
        print('   ✅ Database integrity: PASSED')
    else:
        print('   ❌ Database integrity: FAILED')
    
    if position_ok and cash_ok:
        print('   ✅ DOGE calculations: PASSED')
        print('   ✅ Overall P&L validation: SUCCESSFUL')
        return True
    else:
        print('   ❌ DOGE calculations: FAILED')
        print('   ❌ Overall P&L validation: FAILED')
        return False
    
    conn.close()

if __name__ == '__main__':
    validate_pnl()
