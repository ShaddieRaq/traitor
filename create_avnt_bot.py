#!/usr/bin/env python3
"""
Create AVNT Bot with Optimal Configuration
Based on PROFITABLE_SIGNAL_RESEARCH.md recommendations
"""
import json
import sys
import os

# Add backend to path
sys.path.insert(0, '/Users/lazy_genius/Projects/trader/backend')

from app.core.database import SessionLocal
from app.models.models import Bot

def create_avnt_bot():
    """Create AVNT bot with market-adaptive configuration."""
    
    print("🚀 Creating AVNT Trading Bot")
    print("=" * 50)
    
    # Market-Adaptive Configuration (from research)
    signal_config = {
        "rsi": {
            "enabled": True,
            "weight": 0.35,
            "period": 14,
            "buy_threshold": 30,
            "sell_threshold": 70
        },
        "moving_average": {
            "enabled": True,
            "weight": 0.35,
            "fast_period": 20,
            "slow_period": 50
        },
        "macd": {
            "enabled": True,
            "weight": 0.3,
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        }
    }
    
    db = SessionLocal()
    
    try:
        # Check if AVNT bot already exists
        existing_bot = db.query(Bot).filter(Bot.pair == "AVNT-USD").first()
        if existing_bot:
            print(f"❌ AVNT bot already exists (ID: {existing_bot.id})")
            print(f"   Name: {existing_bot.name}")
            print(f"   Status: {existing_bot.status}")
            return existing_bot.id
        
        # Create new AVNT bot
        avnt_bot = Bot(
            name="AVNT Trading Bot",
            description="Avantis (AVNT) trading bot with market-adaptive multi-signal configuration",
            pair="AVNT-USD",
            status="STOPPED",  # Start stopped for safety
            
            # Position sizing (based on AVNT being around $0.78)
            position_size_usd=25.0,  # $25 per trade (reasonable for AVNT price)
            max_positions=5,         # Allow up to 5 concurrent positions
            
            # Risk management
            stop_loss_pct=5.0,       # 5% stop loss
            take_profit_pct=10.0,    # 10% take profit
            confirmation_minutes=5,   # 5 minute signal confirmation
            trade_step_pct=2.0,      # 2% price change between trades
            cooldown_minutes=15,     # 15 minute cooldown
            
            # Signal configuration
            signal_config=json.dumps(signal_config),
            
            # Initialize state
            current_position_size=0.0,
            current_position_entry_price=None,
            current_combined_score=0.0,
            signal_confirmation_start=None
        )
        
        db.add(avnt_bot)
        db.commit()
        db.refresh(avnt_bot)
        
        print(f"✅ AVNT bot created successfully!")
        print(f"   Bot ID: {avnt_bot.id}")
        print(f"   Name: {avnt_bot.name}")
        print(f"   Pair: {avnt_bot.pair}")
        print(f"   Status: {avnt_bot.status}")
        print(f"   Position Size: ${avnt_bot.position_size_usd}")
        print(f"   Signal Config: Market-adaptive (RSI:35%, MA:35%, MACD:30%)")
        
        print(f"\n🎯 Next Steps:")
        print(f"1. Start the bot: Update status to 'RUNNING'")
        print(f"2. Monitor via dashboard")
        print(f"3. Check logs for trading activity")
        
        return avnt_bot.id
        
    except Exception as e:
        print(f"❌ Error creating AVNT bot: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_avnt_bot()
