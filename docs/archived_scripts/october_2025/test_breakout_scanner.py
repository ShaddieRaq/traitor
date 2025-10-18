#!/usr/bin/env python3
"""
Test the breakout scanner

Usage:
    python test_breakout_scanner.py              # Just scan (no bot creation)
    python test_breakout_scanner.py --create     # Scan and create bots
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import logging
from app.services.breakout_detector import get_breakout_detector
from app.core.database import SessionLocal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    create_bots = "--create" in sys.argv
    
    logger.info("=" * 80)
    logger.info("🔍 BREAKOUT SCANNER TEST")
    logger.info("=" * 80)
    
    if create_bots:
        logger.warning("⚠️  BOT CREATION ENABLED - Will create real trading bots!")
    else:
        logger.info("📋 SCAN ONLY MODE - No bots will be created")
    
    logger.info("")
    
    # Get detector
    detector = get_breakout_detector()
    
    # Scan for breakouts
    breakouts = detector.scan_all_products()
    
    if not breakouts:
        logger.info("❌ No breakouts detected")
        return
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"🚀 FOUND {len(breakouts)} BREAKOUT OPPORTUNITIES")
    logger.info("=" * 80)
    logger.info("")
    
    # Display results
    for i, breakout in enumerate(breakouts, 1):
        logger.info(f"#{i} {breakout.product_id}")
        logger.info(f"   Score: {breakout.score:.1f}/100 ({breakout.confidence} confidence)")
        logger.info(f"   Price Change: +{breakout.price_change_24h:.2f}%")
        logger.info(f"   Volume Change: +{breakout.volume_change_24h:.2f}%")
        logger.info(f"   Signals: {', '.join(breakout.signals)}")
        logger.info(f"   Price: ${breakout.price}")
        logger.info("")
    
    # Check for existing bots
    db = SessionLocal()
    try:
        existing_pairs = detector.get_existing_bot_pairs(db)
        new_opportunities = detector.filter_new_opportunities(breakouts, existing_pairs)
        
        logger.info(f"📊 Existing bots: {len(existing_pairs)}")
        logger.info(f"🆕 New opportunities (no existing bot): {len(new_opportunities)}")
        logger.info("")
        
        if new_opportunities:
            logger.info("🆕 NEW OPPORTUNITIES (no existing bots):")
            for i, opp in enumerate(new_opportunities[:10], 1):
                logger.info(f"   #{i} {opp.product_id} (score={opp.score:.1f}, {opp.confidence})")
            logger.info("")
        
        # Create bots if requested
        if create_bots and new_opportunities:
            from app.services.bot_creator import create_breakout_bot
            
            logger.info("=" * 80)
            logger.info("🤖 CREATING BREAKOUT BOTS")
            logger.info("=" * 80)
            logger.info("")
            
            # Create bots for top 3 opportunities
            created = []
            for opportunity in new_opportunities[:3]:
                try:
                    bot = create_breakout_bot(
                        db=db,
                        product_id=opportunity.product_id,
                        breakout_score=opportunity.score,
                        signals=opportunity.signals,
                        initial_investment=15.0
                    )
                    created.append(bot)
                    logger.info(f"✅ Created bot #{bot.id} for {bot.pair}")
                except Exception as e:
                    logger.error(f"❌ Failed to create bot for {opportunity.product_id}: {e}")
            
            db.commit()
            
            logger.info("")
            logger.info(f"✅ Successfully created {len(created)} breakout bots")
            logger.info("")
            
            # Show created bots
            for bot in created:
                logger.info(f"   Bot #{bot.id}: {bot.pair}")
                logger.info(f"      Stop Loss: {bot.stop_loss_pct}%")
                logger.info(f"      Take Profit: {bot.take_profit_pct}%")
                logger.info(f"      Mode: {bot.trading_mode}")
                logger.info("")
        
    finally:
        db.close()
    
    logger.info("=" * 80)
    logger.info("✅ BREAKOUT SCANNER TEST COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
