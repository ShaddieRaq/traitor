#!/usr/bin/env python3
"""
Backfill Entry Prices for Existing Positions

This script updates Bot.current_position_entry_price from RawTrade data
so P/L protection can work on existing open positions.

NO DATA LOSS - Preserves all learning data and bot history.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import SessionLocal
from app.models.models import Bot
import requests

def main():
    print("=" * 80)
    print("🔧 BACKFILLING ENTRY PRICES FOR EXISTING POSITIONS")
    print("=" * 80)
    print("")
    print("This will update Bot.current_position_entry_price from RawTrade data")
    print("so P/L protection works on existing open positions.")
    print("")
    
    # Get P/L data from API
    print("📊 Fetching P/L data from RawTrade table...")
    response = requests.get("http://localhost:8000/api/v1/raw-trades/pnl-by-product")
    pnl_data = response.json()
    
    # Create lookup dict: product_id -> average_buy_price
    product_prices = {}
    for product in pnl_data['products']:
        if product['current_holdings'] > 0:
            product_prices[product['product_id']] = product['average_buy_price']
    
    print(f"✅ Found {len(product_prices)} products with open positions")
    print("")
    
    # Update bots
    db = SessionLocal()
    try:
        bots = db.query(Bot).filter(Bot.current_position_size > 0).all()
        print(f"🤖 Found {len(bots)} bots with open positions")
        print("")
        
        updated_count = 0
        skipped_count = 0
        
        for bot in bots:
            avg_price = product_prices.get(bot.pair)
            
            if avg_price:
                old_price = bot.current_position_entry_price
                bot.current_position_entry_price = avg_price
                
                if old_price is None:
                    print(f"✅ {bot.pair} ({bot.name}): Set entry price to ${avg_price:.4f}")
                else:
                    print(f"🔄 {bot.pair} ({bot.name}): Updated entry ${old_price:.4f} → ${avg_price:.4f}")
                
                updated_count += 1
            else:
                print(f"⚠️  {bot.pair} ({bot.name}): No RawTrade data found, skipping")
                skipped_count += 1
        
        # Commit changes
        if updated_count > 0:
            print("")
            print(f"💾 Committing {updated_count} updates to database...")
            db.commit()
            print("✅ Database updated successfully!")
        else:
            print("")
            print("ℹ️  No updates needed")
        
        print("")
        print("=" * 80)
        print("📊 BACKFILL SUMMARY")
        print("=" * 80)
        print(f"  ✅ Updated: {updated_count} bots")
        print(f"  ⏭️  Skipped: {skipped_count} bots")
        print("")
        print("🎯 P/L protection will now work on existing positions!")
        print("")
        print("Next bot evaluation will check:")
        print("  • Take profit: Lock gains at +10%")
        print("  • Stop loss: Cut losses at -5%")
        print("  • Time limit: Exit BREAKOUT bots after 72h")
        print("")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
