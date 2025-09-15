#!/usr/bin/env python3
import os
import sys
import json
sys.path.insert(0, '/Users/lazy_genius/Projects/trader/backend')

from app.core.database import SessionLocal
from app.models.models import Bot, Trade
from datetime import datetime, timedelta

db = SessionLocal()

print('📊 Bot Configuration Analysis')
print('=' * 60)

all_bots = db.query(Bot).order_by(Bot.id).all()
print(f'Total active bots: {len(all_bots)}')

for bot in all_bots:
    print(f'\n🤖 Bot {bot.id}: {bot.name}')
    print(f'   Pair: {bot.pair}')
    print(f'   Status: {bot.status}')
    print(f'   Position Size: ${bot.position_size_usd}')
    print(f'   Current Position: {bot.current_position_size}')
    
    # Parse signal configuration
    if bot.signal_config:
        try:
            config = json.loads(bot.signal_config)
            print(f'   📈 Signal Configuration:')
            
            for signal_name, signal_config in config.items():
                if signal_config.get('enabled'):
                    weight = signal_config.get('weight', 0)
                    print(f'      {signal_name.upper()}: Weight {weight:.2f} ({weight*100:.0f}%)')
                    
                    if signal_name == 'rsi':
                        print(f'         Period: {signal_config.get("period", 14)}')
                        print(f'         Buy threshold: {signal_config.get("buy_threshold", 30)}')
                        print(f'         Sell threshold: {signal_config.get("sell_threshold", 70)}')
                    elif signal_name == 'moving_average':
                        print(f'         Fast period: {signal_config.get("fast_period", 12)}')
                        print(f'         Slow period: {signal_config.get("slow_period", 26)}')
                    elif signal_name == 'macd':
                        print(f'         Fast: {signal_config.get("fast_period", 12)}')
                        print(f'         Slow: {signal_config.get("slow_period", 26)}')
                        print(f'         Signal: {signal_config.get("signal_period", 9)}')
        except Exception as e:
            print(f'   ⚠️  Invalid signal config: {e}')
    
    # Recent performance
    recent_trades = db.query(Trade).filter(
        Trade.bot_id == bot.id,
        Trade.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).order_by(Trade.timestamp.desc()).limit(10).all()
    
    print(f'   📈 Recent Activity (7 days): {len(recent_trades)} trades')
    
    if recent_trades:
        print(f'   💰 Recent trades:')
        
        latest_trades = recent_trades[:5]
        for i, trade in enumerate(latest_trades):
            hours_ago = (datetime.utcnow() - trade.timestamp).total_seconds() / 3600
            print(f'      {i+1}. {trade.side} {trade.quantity} @ ${trade.price} ({hours_ago:.1f}h ago)')

print(f'\n🎯 Analysis Summary:')
print(f'Review AVNT bot configuration vs others for performance insights...')

db.close()
