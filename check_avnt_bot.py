#!/usr/bin/env python3
from backend.app.core.database import SessionLocal
from backend.app.models.models import Bot, Trade
from datetime import datetime, timedelta

db = SessionLocal()

print("All Trading Bots:")
print("=" * 50)

all_bots = db.query(Bot).order_by(Bot.id).all()
print(f"Total bots: {len(all_bots)}")

avnt_bot = None

for bot in all_bots:
    print(f"Bot {bot.id}: {bot.name} ({bot.pair}) - Status: {bot.status}")
    
    # Check recent activity for each bot
    recent_trades = db.query(Trade).filter(
        Trade.bot_id == bot.id,
        Trade.timestamp >= datetime.utcnow() - timedelta(hours=6)
    ).count()
    
    total_trades = db.query(Trade).filter(Trade.bot_id == bot.id).count()
    
    print(f"    Recent trades (6h): {recent_trades}, Total: {total_trades}")
    
    if bot.pair == "AVNT-USD":
        avnt_bot = bot
        print("    >>> THIS IS THE AVNT BOT <<<")
        
        # Get last few trades for AVNT bot
        last_trades = db.query(Trade).filter(Trade.bot_id == bot.id).order_by(Trade.timestamp.desc()).limit(5).all()
        
        if last_trades:
            print("    Recent AVNT trades:")
            for trade in last_trades:
                hours_ago = (datetime.utcnow() - trade.timestamp).total_seconds() / 3600
                print(f"      {trade.timestamp} - {trade.side} {trade.quantity} @ ${trade.price} ({trade.status}) [{hours_ago:.1f}h ago]")
        else:
            print("    No trades found!")
        
        # Check pending orders
        pending = db.query(Trade).filter(Trade.bot_id == bot.id, Trade.status == "pending").all()
        if pending:
            print(f"    PENDING ORDERS: {len(pending)}")
            for p in pending:
                age_hours = (datetime.utcnow() - p.timestamp).total_seconds() / 3600
                print(f"      {p.side} {p.quantity} @ ${p.price} (Age: {age_hours:.1f}h)")
        else:
            print("    No pending orders")

print("\n" + "="*50)
if avnt_bot:
    print(f"AVNT Bot Found: {avnt_bot.name} (ID: {avnt_bot.id})")
    print(f"Status: {avnt_bot.status}")
    print(f"Current position: {avnt_bot.current_position_size}")
    print(f"Last updated: {avnt_bot.updated_at}")
else:
    print("AVNT Bot NOT FOUND!")

db.close()
