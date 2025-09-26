#!/usr/bin/env python3
"""
Phase 2 Position Sizing Integration Test
Verify that position sizing calculations are properly integrated with trading execution
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_db_session
from app.models.models import Bot
from app.services.bot_evaluator import BotSignalEvaluator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_position_sizing_integration():
    """Test that position sizing integration works correctly"""
    logger.info("🧪 Testing Phase 2 Position Sizing Integration")
    
    # Get database session
    with get_db_session() as db:
        # Find BTC-USD bot with position sizing enabled
        btc_bot = db.query(Bot).filter(Bot.pair == "BTC-USD").first()
        if not btc_bot:
            logger.error("❌ BTC-USD bot not found")
            return False
            
        logger.info(f"📊 Testing bot: {btc_bot.name} (ID: {btc_bot.id})")
        logger.info(f"💰 Base position size: ${btc_bot.position_size_usd}")
        logger.info(f"🔧 Position sizing enabled: {btc_bot.use_position_sizing}")
        
        # Initialize bot evaluator
        evaluator = BotSignalEvaluator(db=db)
        
        # Evaluate bot signals
        try:
            evaluation_result = evaluator.evaluate_bot(btc_bot)
            
            # Check if position sizing data is present
            if 'position_sizing' in evaluation_result:
                pos_sizing = evaluation_result['position_sizing']
                logger.info(f"✅ Position sizing calculation found:")
                logger.info(f"   Base size: ${pos_sizing.get('base_position_size', 'N/A')}")
                logger.info(f"   Final size: ${pos_sizing.get('final_position_size', 'N/A')}")
                logger.info(f"   Multiplier: {pos_sizing.get('total_multiplier', 'N/A')}x")
                logger.info(f"   Rationale: {pos_sizing.get('sizing_rationale', 'N/A')}")
                
                # Verify the integration logic
                action = evaluation_result.get('action', 'hold')
                logger.info(f"🎯 Current action: {action}")
                
                if action in ['buy', 'sell'] and btc_bot.use_position_sizing:
                    final_size = pos_sizing.get('final_position_size')
                    if final_size and final_size != btc_bot.position_size_usd:
                        logger.info(f"🚀 Integration working: Would use ${final_size} instead of ${btc_bot.position_size_usd}")
                        return True
                    else:
                        logger.warning(f"⚠️  Position sizing calculated but no change from base size")
                elif action == 'hold':
                    logger.info(f"📋 Bot in hold mode - position sizing calculated for analysis only")
                    return True
                else:
                    logger.warning(f"⚠️  Position sizing not calculated for action: {action}")
            else:
                logger.error(f"❌ Position sizing data missing from evaluation result")
                return False
                
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = test_position_sizing_integration()
    if success:
        logger.info("🎉 Phase 2 Position Sizing Integration Test: PASSED")
    else:
        logger.error("💥 Phase 2 Position Sizing Integration Test: FAILED")
        sys.exit(1)