#!/usr/bin/env python3
"""
Script to configure ADA bot with optimized settings like other bots.
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Change to project root directory to ensure proper path resolution
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Bot

def configure_ada_bot():
    """Configure ADA bot with the same optimized settings as other bots."""
    
    db = SessionLocal()
    try:
        # Find the ADA bot
        ada_bot = db.query(Bot).filter(Bot.pair == "ADA-USD").first()
        if not ada_bot:
            print("❌ ADA-USD bot not found!")
            return False
            
        print(f"🔧 Configuring ADA bot: {ada_bot.name}")
        print(f"   Current trade_step_pct: {ada_bot.trade_step_pct}")
        print(f"   Current skip_signals_on_low_balance: {ada_bot.skip_signals_on_low_balance}")
        
        # According to copilot instructions, all bots should use ±0.05 thresholds for optimal performance
        # But let me check what the other running bots actually use
        running_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
        if running_bots:
            sample_bot = running_bots[0]
            print(f"\n📋 Sample running bot ({sample_bot.name}) configuration:")
            print(f"   trade_step_pct: {sample_bot.trade_step_pct}")
            print(f"   skip_signals_on_low_balance: {sample_bot.skip_signals_on_low_balance}")
            
            # Update ADA bot to match the running bots
            ada_bot.trade_step_pct = sample_bot.trade_step_pct
            ada_bot.skip_signals_on_low_balance = sample_bot.skip_signals_on_low_balance
        else:
            print("\n⚠️  No running bots found. Using standard configuration:")
            # Use the standard configuration
            ada_bot.trade_step_pct = 2.0
            ada_bot.skip_signals_on_low_balance = False
        
        # Start the bot to match others
        ada_bot.status = "RUNNING"
        
        db.commit()
        db.refresh(ada_bot)
        
        print(f"\n✅ ADA bot updated successfully:")
        print(f"   trade_step_pct: {ada_bot.trade_step_pct}")
        print(f"   skip_signals_on_low_balance: {ada_bot.skip_signals_on_low_balance}")
        print(f"   status: {ada_bot.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring ADA bot: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Configuring ADA-USD Bot...")
    success = configure_ada_bot()
    if success:
        print("\n🎉 ADA-USD bot configured and started successfully!")
        print("   It now matches the configuration of your other running bots")
    else:
        print("\n❌ Failed to configure ADA-USD bot")
        sys.exit(1)