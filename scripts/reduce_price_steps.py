#!/usr/bin/env python3
"""
Temporary fix for reduced trading activity due to restrictive price step requirements.

Current issue: 6 out of 11 bots blocked by 2% price step requirement while having strong signals.
Solution: Temporarily reduce price step to 0.8% to allow more trading in current market conditions.
"""

import sys
import os
import json
import logging
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reduce_price_steps_temporarily():
    """Reduce price step requirements to improve trading activity."""
    
    try:
        from app.core.database import engine, get_db
        from app.models.models import Bot
        from sqlalchemy.orm import sessionmaker
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Target the bots that are currently blocked by price step
            blocked_pairs = ['BTC-USD', 'DOGE-USD', 'SUI-USD', 'AVAX-USD', 'TOSHI-USD', 'PENGU-USD']
            bots = db.query(Bot).filter(Bot.pair.in_(blocked_pairs)).all()
            
            logger.info(f"Found {len(bots)} bots with price step blocking issues")
            
            updated_bots = []
            
            for bot in bots:
                if bot.trade_step_pct == 2.0:  # Only update if currently at 2%
                    logger.info(f"🔧 Reducing price step for {bot.name} ({bot.pair}): 2.0% → 0.8%")
                    
                    bot.trade_step_pct = 0.8  # Reduce from 2% to 0.8%
                    
                    updated_bots.append({
                        'name': bot.name,
                        'pair': bot.pair,
                        'old_step': 2.0,
                        'new_step': 0.8
                    })
                else:
                    logger.info(f"✅ {bot.name} ({bot.pair}) already has custom step: {bot.trade_step_pct}%")
            
            if updated_bots:
                # Commit changes
                db.commit()
                logger.info(f"🎉 Successfully reduced price step for {len(updated_bots)} bots:")
                for bot_info in updated_bots:
                    print(f"  - {bot_info['name']} ({bot_info['pair']}) - {bot_info['old_step']}% → {bot_info['new_step']}%")
                
                logger.info("💡 This change should allow more trading in current market conditions")
                logger.info("💡 Monitor trading activity and revert if needed using restore script")
            else:
                logger.info("✅ No bots needed price step adjustments")
            
            return updated_bots
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            db.close()
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure you're running this from the project root directory")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

def create_restore_script(updated_bots: List[Dict[str, Any]]):
    """Create a script to restore original price steps if needed."""
    
    restore_script = '''#!/usr/bin/env python3
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
'''
    
    for bot_info in updated_bots:
        restore_script += f'            {{"pair": "{bot_info["pair"]}", "original_step": {bot_info["old_step"]}}},\n'
    
    restore_script += '''        ]
        
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
'''
    
    with open('/Users/lazy_genius/Projects/trader/scripts/restore_price_steps.py', 'w') as f:
        f.write(restore_script)
    
    logger.info("📝 Created restore script: scripts/restore_price_steps.py")

if __name__ == "__main__":
    logger.info("🔧 Starting price step reduction for improved trading activity...")
    updated_bots = reduce_price_steps_temporarily()
    
    if updated_bots:
        create_restore_script(updated_bots)
        logger.info(f"✅ Price step reduction completed! {len(updated_bots)} bots updated.")
        logger.info("🚀 Trading activity should improve within minutes")
    else:
        logger.info("ℹ️ No changes needed or operation failed.")