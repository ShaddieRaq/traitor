#!/usr/bin/env python3
"""
Restore script to revert price step changes if needed.
Generated automatically by reduce_price_steps.py
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app.core.database import engine
from app.models.models import Bot
from sqlalchemy.orm import sessionmaker

def restore_price_steps():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Restore original values
        updates = [
            {"pair": "AVAX-USD", "original_step": 2.0},
            {"pair": "BTC-USD", "original_step": 2.0},
            {"pair": "DOGE-USD", "original_step": 2.0},
            {"pair": "PENGU-USD", "original_step": 2.0},
            {"pair": "SUI-USD", "original_step": 2.0},
            {"pair": "TOSHI-USD", "original_step": 2.0},
        ]
        
        for update in updates:
            bot = db.query(Bot).filter(Bot.pair == update["pair"]).first()
            if bot:
                bot.trade_step_pct = update["original_step"]
                print(f"Restored {bot.name} ({bot.pair}) to {update['original_step']}%")
        
        db.commit()
        print("Price steps restored successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    restore_price_steps()
