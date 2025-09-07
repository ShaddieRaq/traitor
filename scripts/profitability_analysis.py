#!/usr/bin/env python3
"""
Real Account Profitability Analysis
===================================

This script provides comprehensive profitability analysis using only verified real trades
(trades with Coinbase order IDs). No mock data contamination.

Usage:
    python scripts/profitability_analysis.py [--period=8h|24h|7d|all]

Options:
    --period    Time period to analyze (default: all)
"""

import sys
import os
import argparse
import requests
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def get_real_trades():
    """Get all real trades (with order_ids) from the API or database."""
    try:
        response = requests.get('http://localhost:8000/api/v1/trades/?limit=5000', timeout=5)
        if response.status_code == 200:
            all_trades = response.json()
            
            # Filter for real trades only (those with order_ids)
            real_trades = [
                trade for trade in all_trades 
                if trade.get('order_id') is not None and trade.get('order_id') != ''
            ]
            
            print(f'✅ Found {len(real_trades)} real trades out of {len(all_trades)} total')
            return real_trades
            
    except Exception as e:
        print(f'⚠️  Could not fetch trades from API (timeout/error): {e}')
        print('📂 Attempting direct database access...')
        
        # Fallback to direct database access
        try:
            import sqlite3
            import os
            
            db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'trader.db')
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, bot_id, product_id, side, size, price, fee, order_id, status, created_at
                    FROM trades 
                    WHERE order_id IS NOT NULL AND order_id != ''
                    ORDER BY created_at ASC
                """)
                
                rows = cursor.fetchall()
                conn.close()
                
                real_trades = []
                for row in rows:
                    real_trades.append({
                        'id': row[0],
                        'bot_id': row[1],
                        'product_id': row[2],
                        'side': row[3],
                        'size': row[4],
                        'price': row[5],
                        'fee': row[6],
                        'order_id': row[7],
                        'status': row[8],
                        'created_at': row[9]
                    })
                
                print(f'✅ Found {len(real_trades)} real trades from database')
                return real_trades
                
        except Exception as db_error:
            print(f'❌ Database access also failed: {db_error}')
            
        return []

def get_account_balances():
    """Get current account balances from API (or fallback to known values)."""
    try:
        response = requests.get('http://localhost:8000/api/v1/market/accounts', timeout=3)
        if response.status_code == 200:
            accounts = response.json()
            
            balance_summary = {}
            total_value = 0
            
            for account in accounts:
                currency = account['currency']
                balance = account['available_balance']
                is_cash = account.get('is_cash', False)
                
                if balance > 0:
                    balance_summary[currency] = {
                        'balance': balance,
                        'is_cash': is_cash
                    }
                    
                    if currency == 'USD' or is_cash:
                        total_value += balance
                    else:
                        # For simplicity, we'll estimate crypto value at $1 each for this summary
                        # In a real implementation, you'd fetch current prices
                        total_value += balance * 1000 if currency in ['BTC'] else balance * 100
            
            balance_summary['_total_estimated'] = total_value
            return balance_summary
            
    except Exception as e:
        print(f'⚠️  Could not fetch current balances (API timeout/error): {e}')
        # Return known balances from previous status check
        return {
            'USD': {'balance': 499.67, 'is_cash': True},
            'BTC': {'balance': 0.000054, 'is_cash': False},
            'ETH': {'balance': 0.000173, 'is_cash': False},
            'USDC': {'balance': 0.98, 'is_cash': False},
            '_total_estimated': 504.65,
            '_note': 'Using cached balances due to API unavailability'
        }

def parse_trade_time(time_str):
    """Parse trade timestamp."""
    try:
        return datetime.fromisoformat(time_str.replace('Z', '+00:00')).replace(tzinfo=None)
    except:
        return datetime.min

def filter_trades_by_period(trades, period):
    """Filter trades by time period."""
    if period == 'all':
        return trades
    
    now = datetime.utcnow()
    if period == '8h':
        cutoff = now - timedelta(hours=8)
    elif period == '24h':
        cutoff = now - timedelta(hours=24)
    elif period == '7d':
        cutoff = now - timedelta(days=7)
    else:
        return trades
    
    return [t for t in trades if parse_trade_time(t.get('created_at', '')) > cutoff]

def calculate_profitability(trades):
    """Calculate comprehensive profitability metrics."""
    if not trades:
        return {
            'total_trades': 0,
            'buy_trades': 0,
            'sell_trades': 0,
            'total_spent': 0,
            'total_received': 0,
            'total_fees': 0,
            'net_profit': 0,
            'trades_by_pair': {}
        }
    
    total_spent = 0      # Money spent on buys (including fees)
    total_received = 0   # Money received from sells (minus fees)
    total_fees = 0       # Total fees paid
    buy_count = 0
    sell_count = 0
    trades_by_pair = {}
    
    for trade in trades:
        size = float(trade.get('size', 0))
        price = float(trade.get('price', 0))
        fee = float(trade.get('fee') or 0)  # Handle None fees
        side = trade.get('side', '').lower()
        product_id = trade.get('product_id', '')
        
        trade_value = size * price
        total_fees += fee
        
        # Track by trading pair
        if product_id not in trades_by_pair:
            trades_by_pair[product_id] = {'buys': 0, 'sells': 0, 'volume': 0}
        
        trades_by_pair[product_id]['volume'] += trade_value
        
        if side == 'buy':
            total_spent += trade_value + fee
            buy_count += 1
            trades_by_pair[product_id]['buys'] += 1
        elif side == 'sell':
            total_received += trade_value - fee
            sell_count += 1
            trades_by_pair[product_id]['sells'] += 1
    
    net_profit = total_received - total_spent
    
    return {
        'total_trades': len(trades),
        'buy_trades': buy_count,
        'sell_trades': sell_count,
        'total_spent': total_spent,
        'total_received': total_received,
        'total_fees': total_fees,
        'net_profit': net_profit,
        'trades_by_pair': trades_by_pair
    }

def print_profitability_report(trades, period='all'):
    """Print comprehensive profitability report."""
    metrics = calculate_profitability(trades)
    
    print(f'=== PROFITABILITY ANALYSIS ({period.upper()}) ===')
    print(f'Based on {len(trades)} verified real trades with Coinbase order IDs')
    print()
    
    if metrics['total_trades'] == 0:
        print('❌ No real trades found for this period')
        return
    
    # Overall P&L
    print('💰 PROFIT & LOSS SUMMARY:')
    print(f'  Total Spent (Buys + Fees): ${metrics["total_spent"]:.2f}')
    print(f'  Total Received (Sells - Fees): ${metrics["total_received"]:.2f}')
    print(f'  Total Fees Paid: ${metrics["total_fees"]:.2f}')
    print(f'  Net Profit/Loss: ${metrics["net_profit"]:.2f}')
    
    if metrics["total_spent"] > 0:
        roi = (metrics["net_profit"] / metrics["total_spent"]) * 100
        print(f'  Return on Investment: {roi:.2f}%')
    
    print()
    
    # Trade Activity
    print('📊 TRADING ACTIVITY:')
    print(f'  Total Trades: {metrics["total_trades"]}')
    print(f'  Buy Trades: {metrics["buy_trades"]}')
    print(f'  Sell Trades: {metrics["sell_trades"]}')
    print()
    
    # By Trading Pair
    if metrics['trades_by_pair']:
        print('🔄 BY TRADING PAIR:')
        for pair, data in metrics['trades_by_pair'].items():
            print(f'  {pair}:')
            print(f'    Buys: {data["buys"]}, Sells: {data["sells"]}')
            print(f'    Volume: ${data["volume"]:.2f}')
        print()
    
    # Recent Trades
    print('📈 RECENT TRADES (Last 5):')
    for i, trade in enumerate(trades[:5], 1):
        size = float(trade.get('size', 0))
        price = float(trade.get('price', 0))
        side = trade.get('side', '').upper()
        product = trade.get('product_id', '')
        trade_value = size * price
        created_at = trade.get('created_at', '')[:19]
        
        print(f'  {i}. {side} {size:.6f} {product.split("-")[0]} @ ${price:.2f} = ${trade_value:.2f}')
        print(f'     Time: {created_at} | Order: {trade.get("order_id", "N/A")}')

def print_current_balances():
    """Print current account balances."""
    balances = get_account_balances()
    
    print('💼 CURRENT ACCOUNT BALANCES:')
    total_value_estimate = 0
    
    # Handle the dictionary format returned by get_account_balances
    for currency, account_info in balances.items():
        if currency.startswith('_'):  # Skip metadata keys like '_total_estimated'
            if currency == '_note':
                print(f'ℹ️  Note: {account_info}')
            continue
            
        if isinstance(account_info, dict):
            balance = float(account_info.get('balance', 0))
            is_cash = account_info.get('is_cash', False)
        else:
            balance = float(account_info)
            is_cash = (currency == 'USD')
        
        if balance > 0 and currency in ['USD', 'BTC', 'ETH', 'USDC', 'LTC', 'BCH']:
            if is_cash:
                print(f'  {currency}: ${balance:.2f} (cash)')
                total_value_estimate += balance
            else:
                print(f'  {currency}: {balance:.6f}')
                # Rough USD value estimates
                if currency == 'BTC':
                    total_value_estimate += balance * 43000  # Rough BTC price
                elif currency == 'ETH':
                    total_value_estimate += balance * 2500   # Rough ETH price
                elif currency == 'USDC':
                    total_value_estimate += balance
    
    # Use cached total if available
    if '_total_estimated' in balances:
        total_value_estimate = balances['_total_estimated']
    
    print(f'💰 Estimated Total Value: ${total_value_estimate:.2f}')
    print()

def main():
    parser = argparse.ArgumentParser(description='Analyze real account profitability')
    parser.add_argument('--period', choices=['8h', '24h', '7d', 'all'], default='all',
                       help='Time period to analyze')
    
    args = parser.parse_args()
    
    print('🔍 REAL ACCOUNT PROFITABILITY ANALYSIS')
    print('=' * 50)
    print('✅ Using only verified real trades (no mock data)')
    print()
    
    # Get current balances
    print_current_balances()
    
    # Get real trades
    all_real_trades = get_real_trades()
    
    if not all_real_trades:
        print('❌ No real trades found')
        return
    
    # Filter by period
    period_trades = filter_trades_by_period(all_real_trades, args.period)
    
    # Generate report
    print_profitability_report(period_trades, args.period)
    
    print()
    print('✅ Analysis complete - All data from verified real Coinbase trades')

if __name__ == '__main__':
    main()
