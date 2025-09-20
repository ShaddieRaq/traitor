#!/usr/bin/env python3
"""
24-Hour Optimization Impact Assessment
Monitor the effectiveness of system-wide ±0.05 threshold optimization
"""

import requests
import sqlite3
from datetime import datetime, timedelta
import json

def assess_optimization_impact():
    """Comprehensive 24-hour impact assessment"""
    
    print("📊 24-HOUR OPTIMIZATION IMPACT ASSESSMENT")
    print("=" * 50)
    print(f"Assessment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Database connection
    db = sqlite3.connect('/Users/lazy_genius/Projects/trader/trader.db')
    cursor = db.cursor()
    
    # 1. Trading Frequency Analysis
    print("🔥 TRADING FREQUENCY IMPACT:")
    
    # Before optimization (use last 24h before today as baseline)
    baseline_start = datetime.now() - timedelta(days=2)
    baseline_end = datetime.now() - timedelta(days=1)
    
    cursor.execute('''
        SELECT COUNT(*) FROM trades 
        WHERE created_at BETWEEN ? AND ?
    ''', (baseline_start.isoformat(), baseline_end.isoformat()))
    baseline_trades = cursor.fetchone()[0]
    
    # After optimization (last 24 hours)
    optimized_start = datetime.now() - timedelta(days=1)
    cursor.execute('''
        SELECT COUNT(*) FROM trades 
        WHERE created_at > ?
    ''', (optimized_start.isoformat(),))
    optimized_trades = cursor.fetchone()[0]
    
    if baseline_trades > 0:
        frequency_change = ((optimized_trades - baseline_trades) / baseline_trades) * 100
        print(f"   📈 Baseline (24h ago): {baseline_trades} trades")
        print(f"   🚀 Optimized (24h): {optimized_trades} trades")
        print(f"   📊 Change: {frequency_change:+.1f}%")
    else:
        print(f"   🚀 Trades (24h): {optimized_trades}")
        print("   📊 No baseline data available")
    
    print()
    
    # 2. Current Bot Activity Status
    print("🤖 CURRENT BOT STATUS:")
    try:
        r = requests.get('http://localhost:8000/api/v1/bots/')
        bots = r.json()
        
        active_bots = []
        total_activity_score = 0
        
        for bot in bots:
            score = bot.get('current_combined_score', 0)
            name = bot.get('name', 'Unknown')
            status = bot.get('status', 'unknown')
            
            total_activity_score += abs(score)
            
            if abs(score) >= 0.05:
                action = 'BUY' if score < 0 else 'SELL'
                temp = '🔥HOT' if abs(score) >= 0.15 else '🌡️WARM'
                active_bots.append(f"   🎯 {name}: {score:.4f} ({action}) {temp}")
        
        print(f"   📊 Active Signals: {len(active_bots)}/{len(bots)} bots")
        print(f"   🌡️ Average Activity: {total_activity_score/len(bots):.4f}")
        
        if active_bots:
            print("   🔥 Currently Active:")
            for bot_info in active_bots:
                print(bot_info)
        
    except Exception as e:
        print(f"   ❌ API Error: {e}")
    
    print()
    
    # 3. Performance Recommendations
    print("🎯 NEXT STEPS BASED ON ASSESSMENT:")
    print()
    
    if optimized_trades > baseline_trades:
        print("   ✅ OPTIMIZATION SUCCESSFUL - Higher trading frequency detected")
        print("   📈 Recommended: Continue monitoring for P&L impact")
        print("   🎯 Next Phase: Capital allocation optimization")
    else:
        print("   ⏳ OPTIMIZATION SETTLING - Allow more time for signal accumulation")
        print("   📊 Recommended: Monitor for next 12-24 hours")
    
    print()
    print("📋 MONITORING SCHEDULE:")
    print("   • Every 2 hours: python scripts/monitor_system_optimization.py")
    print("   • Daily: python scripts/24_hour_impact_assessment.py")
    print("   • Weekly: python scripts/7_day_signal_analysis.py")
    
    db.close()

if __name__ == "__main__":
    assess_optimization_impact()
