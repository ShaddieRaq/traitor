#!/usr/bin/env python3
"""
Mock Data Identification Script
==============================

This script identifies and reports potentially corrupted mock trade data
that may exist in the database from previous testing.

Usage:
    python scripts/identify_mock_data.py [--cleanup]

Options:
    --cleanup       Actually delete identified mock/corrupted data
"""

import sys
import os
import argparse
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.models.models import Bot, Trade
from app.services.coinbase_service import CoinbaseService

def identify_mock_data(cleanup=False):
    """Identify potentially corrupted mock trade data."""
    db = SessionLocal()
    coinbase_service = CoinbaseService()
    
    try:
        print('🔍 Mock Data Identification Report')
        print('=' * 50)
        
        if cleanup:
            print('⚠️  CLEANUP MODE - Suspicious data will be DELETED')
            print()
        
        # Check for trades with unrealistic sizes (likely from hardcoded price bug)
        print('1. Checking for oversized trades...')
        oversized_trades = []
        
        all_trades = db.query(Trade).order_by(Trade.created_at.desc()).limit(100).all()
        
        for trade in all_trades:
            trade_value_usd = float(trade.size) * float(trade.price)
            
            # Flag trades larger than $1000 as suspicious (normal trades should be ~$10)
            if trade_value_usd > 1000:
                oversized_trades.append({
                    'id': trade.id,
                    'product_id': trade.product_id,
                    'size': trade.size,
                    'price': trade.price,
                    'value_usd': trade_value_usd,
                    'created_at': trade.created_at,
                    'order_id': trade.order_id
                })
        
        if oversized_trades:
            print(f'❌ Found {len(oversized_trades)} suspicious oversized trades:')
            for trade in oversized_trades:
                print(f'  - Trade {trade["id"]}: {trade["size"]} {trade["product_id"].split("-")[0]} @ ${trade["price"]:,.2f} = ${trade["value_usd"]:,.2f}')
                if not trade["order_id"]:
                    print(f'    ⚠️  No order_id (likely mock data)')
        else:
            print('✅ No oversized trades found')
        
        print()
        
        # Check for trades without order IDs (likely mock trades)
        print('2. Checking for trades without Coinbase order IDs...')
        no_order_trades = db.query(Trade).filter(Trade.order_id.is_(None)).all()
        
        if no_order_trades:
            print(f'⚠️  Found {len(no_order_trades)} trades without order IDs:')
            for trade in no_order_trades:
                trade_value = float(trade.size) * float(trade.price)
                print(f'  - Trade {trade.id}: ${trade_value:,.2f} on {trade.created_at}')
        else:
            print('✅ All trades have order IDs')
        
        print()
        
        # Check for unrealistic price patterns
        print('3. Checking for hardcoded price patterns...')
        hardcoded_price_trades = []
        
        # Look for trades at exactly $50,000 (the old hardcoded price)
        suspicious_prices = [50000.0, 50000.00]
        
        for price in suspicious_prices:
            trades_at_price = db.query(Trade).filter(Trade.price == price).all()
            hardcoded_price_trades.extend(trades_at_price)
        
        if hardcoded_price_trades:
            print(f'⚠️  Found {len(hardcoded_price_trades)} trades at suspicious hardcoded prices:')
            for trade in hardcoded_price_trades:
                print(f'  - Trade {trade.id}: {trade.product_id} @ ${trade.price} on {trade.created_at}')
        else:
            print('✅ No hardcoded price patterns found')
        
        print()
        
        # Summary
        total_suspicious = len(oversized_trades) + len(no_order_trades) + len(hardcoded_price_trades)
        
        if total_suspicious > 0:
            print(f'📊 SUMMARY: Found {total_suspicious} potentially corrupted trades')
            
            if cleanup:
                print('\n🗑️  CLEANING UP SUSPICIOUS DATA...')
                
                # Delete oversized trades
                for trade in oversized_trades:
                    trade_obj = db.query(Trade).filter(Trade.id == trade['id']).first()
                    if trade_obj:
                        db.delete(trade_obj)
                        print(f'   Deleted oversized trade {trade["id"]}')
                
                # Delete trades without order IDs
                for trade in no_order_trades:
                    db.delete(trade)
                    print(f'   Deleted orderless trade {trade.id}')
                
                # Delete hardcoded price trades
                for trade in hardcoded_price_trades:
                    db.delete(trade)
                    print(f'   Deleted hardcoded price trade {trade.id}')
                
                db.commit()
                print(f'\n✅ Cleanup complete: Removed {total_suspicious} suspicious trades')
            else:
                print('\n💡 Run with --cleanup to remove suspicious data')
                print('   WARNING: This will permanently delete the identified trades')
        else:
            print('✅ No suspicious mock data found - database looks clean!')
        
    except Exception as e:
        print(f'❌ Error during analysis: {str(e)}')
        if cleanup:
            db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Identify mock/corrupted trade data')
    parser.add_argument('--cleanup', action='store_true', 
                       help='Actually delete identified mock data')
    
    args = parser.parse_args()
    identify_mock_data(cleanup=args.cleanup)
