#!/usr/bin/env python3
"""
Script to add ADA-USD trading bot to the system.
"""
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Change to project root directory to ensure proper path resolution
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Bot

def add_ada_bot():
    """Add ADA-USD trading bot with standard configuration."""
    
    # Standard signal configuration used by other bots
    signal_config = {
        "RSI": {
            "weight": 0.4,
            "period": 14,
            "oversold": 30,
            "overbought": 70
        },
        "MA_Crossover": {
            "weight": 0.3,
            "short_period": 10,
            "long_period": 30
        },
        "MACD": {
            "weight": 0.3,
            "fast": 12,
            "slow": 26,
            "signal": 9
        }
    }
    
    # Create ADA bot configuration
    ada_bot = Bot(
        name="Auto-Cardano-USD Bot",
        description="Automated trading bot for ADA-USD pair using RSI, MA, and MACD signals",
        pair="ADA-USD",
        status="STOPPED",  # Start stopped, user can enable manually
        position_size_usd=20.0,  # Same as other bots
        max_positions=5,
        stop_loss_pct=5.0,
        take_profit_pct=10.0,
        confirmation_minutes=5,
        trade_step_pct=0.05,  # Using optimized threshold
        cooldown_minutes=15,
        signal_config=json.dumps(signal_config),
        skip_signals_on_low_balance=True  # Enable balance pre-check optimization
    )
    
    # Add to database
    db = SessionLocal()
    try:
        # Check if ADA bot already exists
        existing_bot = db.query(Bot).filter(Bot.pair == "ADA-USD").first()
        if existing_bot:
            print(f"❌ ADA-USD bot already exists: {existing_bot.name}")
            return False
            
        db.add(ada_bot)
        db.commit()
        db.refresh(ada_bot)
        
        print(f"✅ Successfully added ADA-USD bot:")
        print(f"   Name: {ada_bot.name}")
        print(f"   Pair: {ada_bot.pair}")
        print(f"   Position Size: ${ada_bot.position_size_usd}")
        print(f"   Status: {ada_bot.status}")
        print(f"   ID: {ada_bot.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding ADA bot: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Adding ADA-USD Trading Bot...")
    success = add_ada_bot()
    if success:
        print("\n🎉 ADA-USD bot added successfully!")
        print("   You can now start it from the dashboard or API")
    else:
        print("\n❌ Failed to add ADA-USD bot")
        sys.exit(1)