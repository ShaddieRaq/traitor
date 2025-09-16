#!/usr/bin/env python3
"""
Script to add the skip_signals_on_low_balance field to existing bots.
This field enables the balance pre-check optimization.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from app.models.models import Base, Bot
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Add the skip_signals_on_low_balance field to existing bots."""
    
    # Create tables if they don't exist (this will add the new column)
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema updated with new fields")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get all bots
        bots = db.query(Bot).all()
        logger.info(f"Found {len(bots)} bots")
        
        # Set default value for existing bots
        updated_count = 0
        for bot in bots:
            # Check if the field exists and set default if needed
            if not hasattr(bot, 'skip_signals_on_low_balance') or bot.skip_signals_on_low_balance is None:
                bot.skip_signals_on_low_balance = True  # Enable optimization by default
                updated_count += 1
        
        # Commit changes
        if updated_count > 0:
            db.commit()
            logger.info(f"Updated {updated_count} bots with balance optimization enabled")
        else:
            logger.info("All bots already have the balance optimization field configured")
        
        # Verify the update
        for bot in bots:
            logger.info(f"Bot {bot.id} ({bot.name}): skip_signals_on_low_balance = {getattr(bot, 'skip_signals_on_low_balance', 'NOT SET')}")
            
    except Exception as e:
        logger.error(f"Error updating bots: {e}")
        db.rollback()
        return 1
    finally:
        db.close()
    
    logger.info("Balance optimization field setup complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
