"""
Add 5 New Trading Pairs Script
Adds LINK, MATIC, LTC, DOT, and UNI trading bots with full AI capabilities
"""

import sys
import os
sys.path.append('/Users/lazy_genius/Projects/trader/backend')

from app.models.models import Bot
from app.core.database import get_db
from sqlalchemy.orm import Session

def add_bot(db: Session, pair: str, name: str, base_position_size: float = 25):
    """Add a new bot with AI features enabled"""
    
    # Check if bot already exists
    existing_bot = db.query(Bot).filter(Bot.pair == pair).first()
    if existing_bot:
        print(f"❌ Bot for {pair} already exists!")
        return False
    
    # Create new bot
    new_bot = Bot(
        name=name,
        pair=pair,
        status="RUNNING",
        base_position_size=base_position_size,
        current_position_size=0,
        last_trade_price=None,
        last_trade_time=None,
        trade_step_pct=2.0,  # Standard 2% price step
        trading_thresholds={"buy_threshold": -0.05, "sell_threshold": 0.05},
        balance_threshold_usd=10.0,
        signal_config={
            "signals": [
                {
                    "name": "RSI",
                    "type": "RSI", 
                    "weight": 1.0,
                    "parameters": {"period": 14, "overbought": 70, "oversold": 30}
                },
                {
                    "name": "MACD",
                    "type": "MACD",
                    "weight": 1.0, 
                    "parameters": {"fast_period": 12, "slow_period": 26, "signal_period": 9}
                },
                {
                    "name": "Moving Average",
                    "type": "MOVING_AVERAGE",
                    "weight": 1.0,
                    "parameters": {"short_window": 10, "long_window": 20}
                }
            ]
        },
        # Enable AI features
        use_trend_detection=True,
        use_position_sizing=True,
        ai_enabled=True
    )
    
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    
    print(f"✅ Added {name} (ID: {new_bot.id}) with AI features enabled")
    return True

def main():
    """Add 5 new trading pairs"""
    
    # New bots to add
    new_bots = [
        ("LINK-USD", "Auto-Chainlink-USD Bot", 25),
        ("MATIC-USD", "Auto-Polygon-USD Bot", 25), 
        ("LTC-USD", "Auto-Litecoin-USD Bot", 25),
        ("DOT-USD", "Auto-Polkadot-USD Bot", 25),
        ("UNI-USD", "Auto-Uniswap-USD Bot", 25)
    ]
    
    print("🚀 Adding 5 new trading pairs with AI features...")
    
    db = next(get_db())
    
    success_count = 0
    for pair, name, position_size in new_bots:
        if add_bot(db, pair, name, position_size):
            success_count += 1
    
    db.close()
    
    print(f"\n🎉 Successfully added {success_count}/5 new trading bots!")
    print("All bots have AI features enabled:")
    print("  ✅ Trend Detection")
    print("  ✅ Dynamic Position Sizing") 
    print("  ✅ Signal Performance Tracking")
    print("  ✅ Adaptive Weight Updates")

if __name__ == "__main__":
    main()