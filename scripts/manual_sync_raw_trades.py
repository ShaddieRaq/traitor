#!/usr/bin/env python3
"""
Manual sync script for raw trades from Coinbase.
This fills the gap where the deprecated sync endpoints were removed 
but no replacement was created.
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Change to project root directory to ensure proper path resolution
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.coinbase_service import CoinbaseService
from app.models.models import RawTrade


def sync_raw_trades_from_coinbase(days_back: int = 7):
    """Sync raw trades from Coinbase API to database."""
    print(f"🔄 Syncing raw trades from last {days_back} days...")
    
    # Initialize services
    db = SessionLocal()
    coinbase_service = CoinbaseService()
    
    try:
        # Get raw fills from Coinbase
        print("📥 Fetching fills from Coinbase...")
        raw_fills = coinbase_service.get_raw_fills(days_back=days_back)
        print(f"📊 Found {len(raw_fills)} fills from Coinbase")
        
        new_trades_count = 0
        skipped_count = 0
        
        for fill in raw_fills:
            try:
                # Check if this fill already exists
                existing = db.query(RawTrade).filter(
                    RawTrade.fill_id == fill['trade_id']
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Create new RawTrade record
                raw_trade = RawTrade(
                    fill_id=fill['trade_id'],
                    order_id=fill['order_id'],
                    product_id=fill['product_id'],
                    side=fill['side'].upper(),
                    size=float(fill['size']),
                    size_in_quote=bool(fill['size_in_quote']),
                    price=float(fill['price']),
                    commission=float(fill['fee']) if fill['fee'] else 0.0,
                    created_at=fill['trade_time'],
                    synced_at=datetime.utcnow()
                )
                
                db.add(raw_trade)
                new_trades_count += 1
                
                print(f"✅ Added {fill['product_id']} {fill['side']} - {fill['size']} @ {fill['price']}")
                
            except Exception as e:
                print(f"❌ Error processing fill {fill.get('trade_id', 'unknown')}: {e}")
                continue
        
        # Commit all changes
        db.commit()
        
        print(f"\n🎉 Sync completed!")
        print(f"   📈 New trades added: {new_trades_count}")
        print(f"   ⏭️  Existing trades skipped: {skipped_count}")
        print(f"   📊 Total fills processed: {len(raw_fills)}")
        
        return {
            'success': True,
            'new_trades': new_trades_count,
            'skipped': skipped_count,
            'total_processed': len(raw_fills)
        }
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        db.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()


def check_sui_trades():
    """Check specifically for SUI-USD trades."""
    print("\n🔍 Checking SUI-USD trades in database...")
    
    db = SessionLocal()
    try:
        # Debug: Check which database file we're using
        print(f"🔍 Database connection: {db.bind.url}")
        
        sui_trades = db.query(RawTrade).filter(
            RawTrade.product_id == 'SUI-USD'
        ).order_by(RawTrade.created_at.desc()).limit(10).all()
        
        # Debug: Check total raw trades count
        total_trades = db.query(RawTrade).count()
        print(f"🔍 Total raw trades in database: {total_trades}")
        
        # Debug: Check what products exist
        products = db.query(RawTrade.product_id).distinct().all()
        product_list = [p[0] for p in products]
        print(f"🔍 Products in database: {product_list}")
        
        if sui_trades:
            print(f"✅ Found {len(sui_trades)} SUI-USD trades:")
            for trade in sui_trades[:5]:  # Show first 5
                print(f"   {trade.side} {trade.size} @ ${trade.price} - {trade.created_at}")
        else:
            print("❌ No SUI-USD trades found in database")
        
        return len(sui_trades)
        
    except Exception as e:
        print(f"❌ Error checking SUI trades: {e}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Manual Raw Trades Sync")
    print("=" * 40)
    
    # Check current SUI trades
    sui_count_before = check_sui_trades()
    
    # Run sync
    result = sync_raw_trades_from_coinbase(days_back=7)
    
    if result['success']:
        # Check SUI trades again
        sui_count_after = check_sui_trades()
        
        if sui_count_after > sui_count_before:
            print(f"\n🎯 SUI-USD trades increased from {sui_count_before} to {sui_count_after}")
        else:
            print(f"\n⚠️  SUI-USD trade count unchanged: {sui_count_after}")
            
        print("\n💡 Tip: Refresh the UI to see updated trade data")
    else:
        print(f"\n💥 Sync failed: {result.get('error', 'Unknown error')}")
