#!/usr/bin/env python3
"""
Deep Analysis: Why do some bots win while others lose?
This script analyzes the actual trading mechanics, not just P&L.
"""

import requests
import json
from datetime import datetime, timedelta
import statistics

def get_api_data(endpoint, timeout=10):
    """Safe API call with timeout"""
    try:
        response = requests.get(f"http://localhost:8000{endpoint}", timeout=timeout)
        return response.json()
    except Exception as e:
        print(f"API Error for {endpoint}: {e}")
        return None

def analyze_bot_mechanics():
    print("🔍 DEEP DIVE: Why Winners Win & Losers Lose")
    print("=" * 60)
    
    # Get P&L data
    pnl_data = get_api_data("/api/v1/raw-trades/pnl-by-product")
    if not pnl_data:
        print("❌ Failed to get P&L data")
        return
    
    products = pnl_data.get('products', [])
    
    # Sort by performance
    products.sort(key=lambda x: x['net_pnl_usd'], reverse=True)
    
    # Identify winners and losers
    winners = products[:5]  # Top 5 performers
    losers = products[-5:]  # Bottom 5 performers
    
    print("\n🏆 TOP WINNERS:")
    for p in winners:
        print(f"  {p['product_id']}: ${p['net_pnl_usd']:.2f} ({p['trade_count']} trades)")
    
    print("\n💸 TOP LOSERS:")
    for p in losers:
        print(f"  {p['product_id']}: ${p['net_pnl_usd']:.2f} ({p['trade_count']} trades)")
    
    # Analysis 1: Trading Frequency vs Profitability
    print("\n📊 ANALYSIS 1: Trading Frequency vs Profitability")
    print("-" * 50)
    
    for category, bots in [("WINNERS", winners), ("LOSERS", losers)]:
        trade_counts = [p['trade_count'] for p in bots]
        avg_trades = statistics.mean(trade_counts)
        print(f"{category}: Avg {avg_trades:.1f} trades/bot (range: {min(trade_counts)}-{max(trade_counts)})")
    
    # Analysis 2: Buy/Sell Ratio Analysis
    print("\n📊 ANALYSIS 2: Buy/Sell Execution Patterns")
    print("-" * 50)
    
    for category, bots in [("WINNERS", winners), ("LOSERS", losers)]:
        buy_sell_ratios = []
        for p in bots:
            if p['sell_trades'] > 0:
                ratio = p['buy_trades'] / p['sell_trades']
                buy_sell_ratios.append(ratio)
                print(f"  {p['product_id']}: {p['buy_trades']}B/{p['sell_trades']}S = {ratio:.2f} ratio")
        
        if buy_sell_ratios:
            avg_ratio = statistics.mean(buy_sell_ratios)
            print(f"{category} Average Buy/Sell Ratio: {avg_ratio:.2f}")
    
    # Analysis 3: Fee Impact Analysis
    print("\n📊 ANALYSIS 3: Fee Impact on Profitability")
    print("-" * 50)
    
    for category, bots in [("WINNERS", winners), ("LOSERS", losers)]:
        fee_impacts = []
        for p in bots:
            total_volume = p['total_spent_usd'] + p['total_received_usd']
            if total_volume > 0:
                fee_percentage = (p['total_fees_usd'] / total_volume) * 100
                fee_impacts.append(fee_percentage)
                print(f"  {p['product_id']}: ${p['total_fees_usd']:.2f} fees ({fee_percentage:.3f}% of volume)")
        
        if fee_impacts:
            avg_fee_impact = statistics.mean(fee_impacts)
            print(f"{category} Average Fee Impact: {avg_fee_impact:.3f}%")
    
    # Analysis 4: Holdings vs Performance
    print("\n📊 ANALYSIS 4: Current Holdings Analysis")
    print("-" * 50)
    
    for category, bots in [("WINNERS", winners), ("LOSERS", losers)]:
        for p in bots:
            unrealized_pct = (p['unrealized_pnl_usd'] / p['current_value']) * 100 if p['current_value'] > 0 else 0
            print(f"  {p['product_id']}: ${p['current_value']:.2f} held, {unrealized_pct:.1f}% unrealized P&L")
    
    return winners, losers

def analyze_signal_patterns(winners, losers):
    """Analyze signal configurations of winners vs losers"""
    print("\n📊 ANALYSIS 5: Signal Configuration Patterns")
    print("-" * 50)
    
    # Get bot configurations (try one at a time to avoid timeouts)
    winner_configs = []
    loser_configs = []
    
    print("Fetching winner configurations...")
    for p in winners:
        bot_data = get_api_data(f"/api/v1/bots/?product_id={p['product_id']}", timeout=5)
        if bot_data and len(bot_data) > 0:
            winner_configs.append({
                'product_id': p['product_id'],
                'config': bot_data[0]
            })
            print(f"  ✅ {p['product_id']}: Got config")
        else:
            print(f"  ❌ {p['product_id']}: Failed to get config")
    
    print("Fetching loser configurations...")
    for p in losers:
        bot_data = get_api_data(f"/api/v1/bots/?product_id={p['product_id']}", timeout=5)
        if bot_data and len(bot_data) > 0:
            loser_configs.append({
                'product_id': p['product_id'],
                'config': bot_data[0]
            })
            print(f"  ✅ {p['product_id']}: Got config")
        else:
            print(f"  ❌ {p['product_id']}: Failed to get config")
    
    # Compare signal configurations
    print("\n🎯 SIGNAL CONFIGURATION COMPARISON:")
    print("-" * 40)
    
    for category, configs in [("WINNERS", winner_configs), ("LOSERS", loser_configs)]:
        print(f"\n{category}:")
        for c in configs:
            config = c['config']
            print(f"  {c['product_id']}:")
            print(f"    Current Score: {config.get('current_combined_score', 'N/A')}")
            print(f"    Temperature: {config.get('temperature', 'N/A')}")
            
            # Parse signal config if available
            signal_config = config.get('signal_config')
            if isinstance(signal_config, str):
                try:
                    signal_config = json.loads(signal_config)
                except:
                    signal_config = None
            
            if signal_config:
                print(f"    RSI Weight: {signal_config.get('rsi', {}).get('weight', 'N/A')}")
                print(f"    MA Weight: {signal_config.get('moving_average', {}).get('weight', 'N/A')}")
                print(f"    MACD Weight: {signal_config.get('macd', {}).get('weight', 'N/A')}")
            else:
                print(f"    Signal Config: Not available")

def main():
    try:
        winners, losers = analyze_bot_mechanics()
        analyze_signal_patterns(winners, losers)
        
        print("\n🎯 KEY INSIGHTS TO INVESTIGATE:")
        print("1. Do winners have different trading frequencies?")
        print("2. Are winners better at timing buy/sell decisions?")
        print("3. Do fee structures favor certain trading patterns?")
        print("4. Are signal weights optimized differently for winners?")
        print("5. Do winners trade in more favorable market conditions?")
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()