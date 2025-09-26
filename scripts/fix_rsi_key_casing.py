#!/usr/bin/env python3
"""
Fix RSI key casing inconsistency in bot signal configurations.

Some auto-created bots have "RSI" (uppercase) instead of "rsi" (lowercase),
causing the RSI signal to not be recognized by the backend.
"""

import sys
import os
import json
import logging
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_rsi_key_casing():
    """Fix RSI key casing in bot configurations."""
    
    try:
        from app.core.database import engine, get_db
        from app.models.models import Bot
        from sqlalchemy.orm import sessionmaker
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Get all bots
            bots = db.query(Bot).all()
            logger.info(f"Found {len(bots)} bots to check")
            
            fixed_bots = []
            
            for bot in bots:
                try:
                    # Parse signal config
                    signal_config = json.loads(bot.signal_config) if isinstance(bot.signal_config, str) else bot.signal_config
                    
                    # Check if RSI key needs fixing
                    if "RSI" in signal_config and "rsi" not in signal_config:
                        logger.info(f"🔧 Fixing RSI key casing for {bot.name} ({bot.pair})")
                        
                        # Move RSI config to lowercase key
                        signal_config["rsi"] = signal_config["RSI"]
                        del signal_config["RSI"]
                        
                        # Update bot configuration
                        bot.signal_config = json.dumps(signal_config) if isinstance(bot.signal_config, str) else signal_config
                        
                        # Log the fix
                        rsi_config = signal_config["rsi"]
                        logger.info(f"  ✅ Fixed: RSI enabled={rsi_config['enabled']}, weight={rsi_config['weight']}, thresholds={rsi_config['buy_threshold']}/{rsi_config['sell_threshold']}")
                        
                        fixed_bots.append({
                            'name': bot.name,
                            'pair': bot.pair,
                            'rsi_config': rsi_config
                        })
                    
                    elif "rsi" in signal_config:
                        rsi_config = signal_config["rsi"]
                        logger.info(f"✅ {bot.name} ({bot.pair}) already has correct 'rsi' key: thresholds={rsi_config['buy_threshold']}/{rsi_config['sell_threshold']}")
                    
                    else:
                        logger.warning(f"⚠️ {bot.name} ({bot.pair}) has no RSI configuration at all!")
                
                except Exception as e:
                    logger.error(f"Error processing {bot.name} ({bot.pair}): {e}")
                    continue
            
            if fixed_bots:
                # Commit changes
                db.commit()
                logger.info(f"🎉 Successfully fixed RSI key casing for {len(fixed_bots)} bots:")
                for bot_info in fixed_bots:
                    print(f"  - {bot_info['name']} ({bot_info['pair']}) - RSI {bot_info['rsi_config']['buy_threshold']}/{bot_info['rsi_config']['sell_threshold']}")
            else:
                logger.info("✅ No RSI key casing issues found - all bots already use correct 'rsi' key")
            
            return fixed_bots
            
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

if __name__ == "__main__":
    logger.info("🔧 Starting RSI key casing fix...")
    fixed_bots = fix_rsi_key_casing()
    
    if fixed_bots:
        logger.info(f"✅ Fix completed! {len(fixed_bots)} bots updated.")
    else:
        logger.info("ℹ️ No fixes needed or fix failed.")