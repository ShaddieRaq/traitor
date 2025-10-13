#!/usr/bin/env python3
"""
Preview P/L Protection Triggers

Shows which positions will trigger P/L exits on next bot evaluation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import requests

def main():
    print("=" * 80)
    print("🎯 P/L PROTECTION PREVIEW - What Will Happen Next")
    print("=" * 80)
    print("")
    
    # Get bots and P/L data
    bots_response = requests.get("http://localhost:8000/api/v1/bots/")
    bots = bots_response.json()
    
    pnl_response = requests.get("http://localhost:8000/api/v1/raw-trades/pnl-by-product")
    pnl_data = pnl_response.json()
    
    # Create P/L lookup
    pnl_lookup = {p['product_id']: p for p in pnl_data['products']}
    
    # Analyze each bot with open position
    will_take_profit = []
    will_stop_loss = []
    will_hold = []
    no_entry_price = []
    
    for bot in bots:
        if bot.get('current_position_size', 0) <= 0:
            continue
        
        entry_price = bot.get('current_position_entry_price')
        if not entry_price:
            no_entry_price.append(bot)
            continue
        
        pnl_info = pnl_lookup.get(bot['pair'])
        if not pnl_info:
            continue
        
        current_price = pnl_info['current_price']
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        take_profit_pct = bot.get('take_profit_pct', 10.0)
        stop_loss_pct = bot.get('stop_loss_pct', 5.0)
        
        bot_info = {
            'pair': bot['pair'],
            'name': bot['name'],
            'entry': entry_price,
            'current': current_price,
            'pnl_pct': pnl_pct,
            'pnl_usd': pnl_info['unrealized_pnl_usd'],
            'take_profit': take_profit_pct,
            'stop_loss': stop_loss_pct
        }
        
        if pnl_pct >= take_profit_pct:
            will_take_profit.append(bot_info)
        elif pnl_pct <= -stop_loss_pct:
            will_stop_loss.append(bot_info)
        else:
            will_hold.append(bot_info)
    
    # Display results
    if will_take_profit:
        print("🎯 WILL TAKE PROFIT (Next Evaluation):")
        print("-" * 80)
        for bot in sorted(will_take_profit, key=lambda x: x['pnl_pct'], reverse=True):
            print(f"  ✅ {bot['pair']:15} {bot['name']:30}")
            print(f"     Entry: ${bot['entry']:.4f} → Current: ${bot['current']:.4f}")
            print(f"     P&L: {bot['pnl_pct']:+.2f}% (${bot['pnl_usd']:+.2f}) >= Target: +{bot['take_profit']:.0f}%")
            print(f"     🚨 WILL SELL: Locking in profit!")
            print("")
    else:
        print("ℹ️  No positions above take profit threshold\n")
    
    if will_stop_loss:
        print("🛑 WILL STOP LOSS (Next Evaluation):")
        print("-" * 80)
        for bot in sorted(will_stop_loss, key=lambda x: x['pnl_pct']):
            print(f"  ❌ {bot['pair']:15} {bot['name']:30}")
            print(f"     Entry: ${bot['entry']:.4f} → Current: ${bot['current']:.4f}")
            print(f"     P&L: {bot['pnl_pct']:+.2f}% (${bot['pnl_usd']:+.2f}) <= Limit: -{bot['stop_loss']:.0f}%")
            print(f"     🚨 WILL SELL: Cutting losses!")
            print("")
    else:
        print("ℹ️  No positions below stop loss threshold\n")
    
    if will_hold:
        print(f"⏸️  WILL HOLD ({len(will_hold)} positions within thresholds):")
        print("-" * 80)
        for bot in sorted(will_hold, key=lambda x: x['pnl_pct'], reverse=True):
            status = "🟢 Winning" if bot['pnl_pct'] > 0 else "🔴 Losing"
            print(f"  {status} {bot['pair']:15} {bot['pnl_pct']:+.2f}% (${bot['pnl_usd']:+.2f})")
        print("")
    
    if no_entry_price:
        print(f"⚠️  NO ENTRY PRICE ({len(no_entry_price)} positions):")
        print("-" * 80)
        for bot in no_entry_price:
            print(f"  ❓ {bot['pair']:15} {bot.get('name', 'Unknown')}")
        print("  Note: These positions won't have P/L protection until entry price is set\n")
    
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"  🎯 Will take profit: {len(will_take_profit)} positions")
    print(f"  🛑 Will stop loss: {len(will_stop_loss)} positions")
    print(f"  ⏸️  Will hold: {len(will_hold)} positions")
    print(f"  ⚠️  No protection: {len(no_entry_price)} positions")
    print("")
    print("⏰ TIMING: P/L checks run on every bot evaluation (every 10 minutes)")
    print("🔒 NO CONFIRMATION: P/L exits are immediate (override signal confirmation)")
    print("")

if __name__ == "__main__":
    main()
