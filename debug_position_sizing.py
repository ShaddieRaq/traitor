#!/usr/bin/env python3
"""Debug script to test position sizing logic"""

import sys
import os
sys.path.append('/Users/lazy_genius/Projects/trader/backend')

from app.core.database import SessionLocal
from app.models.models import Bot
from app.services.bot_evaluator import BotSignalEvaluator
from app.services.coinbase_service import CoinbaseService

def debug_position_sizing():
    db = SessionLocal()
    try:
        # Get bot 3 (BTC)
        bot = db.query(Bot).filter(Bot.id == 3).first()
        if not bot:
            print("Bot 3 not found")
            return
        
        print(f"Bot: {bot.name}")
        print(f"use_position_sizing: {bot.use_position_sizing}")
        print(f"getattr result: {getattr(bot, 'use_position_sizing', False)}")
        
        # Get some market data
        coinbase_service = CoinbaseService()
        market_data = coinbase_service.get_historical_data(
            product_id=bot.pair,
            granularity=3600,
            limit=100
        )
        
        # Evaluate bot
        evaluator = BotSignalEvaluator(db)
        result = evaluator.evaluate_bot(bot, market_data)
        
        print(f"\nEvaluation result:")
        print(f"Action: {result['action']}")
        print(f"use_position_sizing check: {getattr(bot, 'use_position_sizing', False)}")
        print(f"Action check: {result['action'] in ['buy', 'sell']}")
        print(f"Combined condition: {getattr(bot, 'use_position_sizing', False) and result['action'] in ['buy', 'sell']}")
        print(f"Position sizing: {result.get('position_sizing', 'NOT FOUND')}")
        
    finally:
        db.close()

if __name__ == '__main__':
    debug_position_sizing()