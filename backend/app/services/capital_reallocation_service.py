"""
Capital Reallocation Service

Manages dynamic capital allocation:
- Calculate available capital from archived bots
- Create new breakout bots with freed capital
- Smart resurrection logic for archived bots

Created: October 12, 2025
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.models import Bot
from ..services.bot_lifecycle_service import get_lifecycle_service
from ..services.breakout_detector import BreakoutOpportunity

logger = logging.getLogger(__name__)


class CapitalReallocationService:
    """
    Manages capital freed from archived bots and reallocates to new opportunities.
    """
    
    # Capital management settings
    DEFAULT_TOTAL_ALLOCATION = 500.0  # Total portfolio allocation (USD)
    MIN_BOT_CAPITAL = 15.0  # Minimum capital per bot
    MAX_BREAKOUT_BOTS = 10  # Maximum concurrent breakout bots
    
    def __init__(self, db: Session):
        self.db = db
        self.lifecycle_service = get_lifecycle_service(db)
    
    def get_available_capital(self) -> Dict:
        """
        Get ACTUAL available USD from Coinbase account.
        NO FAKE DATA - queries real USD balance (cached 5 min).
        
        Returns:
            Dict with capital info:
            - usd_balance: ACTUAL USD in Coinbase
            - can_create_bots: True if USD >= $15
        """
        from ..services.coinbase_service import coinbase_service
        
        try:
            # Get REAL Coinbase accounts (cached for 5 min, no rate limit issues)
            accounts = coinbase_service.get_accounts()
            
            usd_balance = 0.0
            for account in accounts:
                if account.get('currency') == 'USD':
                    # available_balance is a float, not a dict
                    usd_balance = float(account.get('available_balance', 0))
                    break
            
            logger.info(f"💰 Real USD balance: ${usd_balance:.2f}")
            
            return {
                "usd_balance": float(usd_balance),
                "available_capital": float(usd_balance),
                "can_create_bots": usd_balance >= self.MIN_BOT_CAPITAL
            }
            
        except Exception as e:
            logger.error(f"Failed to get Coinbase USD balance: {e}")
            return {
                "usd_balance": 0.0,
                "available_capital": 0.0,
                "can_create_bots": False,
                "error": str(e)
            }
    
    def handle_breakout_opportunity(
        self, 
        opportunity: BreakoutOpportunity
    ) -> Dict:
        """
        Smart decision: resurrect archived bot OR create new bot.
        
        Decision logic:
        1. Check if archived bot exists for this pair
        2. Evaluate if resurrection is beneficial (learning, performance)
        3. Resurrect if criteria met, otherwise create new bot
        
        Args:
            opportunity: BreakoutOpportunity instance
        
        Returns:
            Dict with action result (resurrected or created)
        """
        # Check for archived bot
        archived_bots = self.lifecycle_service.get_archived_bots_by_pair(opportunity.product_id)
        
        if not archived_bots:
            # No archived bot - create new
            logger.info(f"No archived bot for {opportunity.product_id}, creating new bot")
            return self._create_new_breakout_bot(opportunity)
        
        # Get best archived bot (most learning data)
        best_archived = max(archived_bots, key=lambda b: b.id)  # Most recent by ID
        
        # Check if resurrection is beneficial
        should_resurrect, reason = self.lifecycle_service.should_resurrect(
            best_archived,
            opportunity.confidence
        )
        
        if should_resurrect:
            # Resurrect existing bot (preserves learning)
            logger.info(
                f"Resurrecting archived bot {best_archived.id} for {opportunity.product_id} "
                f"(confidence: {opportunity.confidence})"
            )
            return self._resurrect_bot(best_archived, opportunity)
        else:
            # Create new bot (archived bot not worth resurrecting)
            logger.info(
                f"Not resurrecting archived bot {best_archived.id} for {opportunity.product_id}: {reason}. "
                f"Creating new bot instead."
            )
            return self._create_new_breakout_bot(opportunity)
    
    def _resurrect_bot(
        self, 
        bot: Bot, 
        opportunity: BreakoutOpportunity
    ) -> Dict:
        """
        Resurrect archived bot for new breakout opportunity.
        
        Args:
            bot: Archived bot instance
            opportunity: BreakoutOpportunity instance
        
        Returns:
            Dict with resurrection result
        """
        try:
            result = self.lifecycle_service.resurrect_bot(
                bot=bot,
                reason=f"{opportunity.confidence} breakout",
                breakout_score=opportunity.score,
                breakout_confidence=opportunity.confidence
            )
            
            return {
                "action": "resurrected",
                "bot_id": bot.id,
                "pair": bot.pair,
                "result": result,
                "opportunity": {
                    "product_id": opportunity.product_id,
                    "score": opportunity.score,
                    "confidence": opportunity.confidence,
                    "signals": opportunity.signals
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to resurrect bot {bot.id}: {e}")
            # Fall back to creating new bot
            return self._create_new_breakout_bot(opportunity)
    
    def _create_new_breakout_bot(
        self, 
        opportunity: BreakoutOpportunity
    ) -> Dict:
        """
        Create new breakout bot for opportunity.
        
        Args:
            opportunity: BreakoutOpportunity instance
        
        Returns:
            Dict with creation result
        """
        try:
            from ..services.bot_creator import create_breakout_bot
            
            # Check capital availability
            capital_info = self.get_available_capital()
            
            if not capital_info["can_create_bots"]:
                logger.warning(
                    f"Insufficient capital to create bot for {opportunity.product_id}: "
                    f"${capital_info['available_capital']:.2f} < ${self.MIN_BOT_CAPITAL}"
                )
                return {
                    "action": "skipped",
                    "reason": "insufficient_capital",
                    "available_capital": capital_info["available_capital"],
                    "required_capital": self.MIN_BOT_CAPITAL
                }
            
            # Check breakout bot limit
            breakout_count = self.db.query(func.count(Bot.id)).filter(
                Bot.trading_mode == "BREAKOUT",
                Bot.lifecycle_stage.in_(["ACTIVE", "CLOSING"])
            ).scalar() or 0
            
            if breakout_count >= self.MAX_BREAKOUT_BOTS:
                logger.warning(
                    f"Max breakout bots reached ({breakout_count}/{self.MAX_BREAKOUT_BOTS}), "
                    f"skipping {opportunity.product_id}"
                )
                return {
                    "action": "skipped",
                    "reason": "max_breakout_bots_reached",
                    "current_count": breakout_count,
                    "max_allowed": self.MAX_BREAKOUT_BOTS
                }
            
            # Create the bot
            bot = create_breakout_bot(
                db=self.db,
                product_id=opportunity.product_id,
                breakout_score=opportunity.score,
                signals=opportunity.signals,
                initial_investment=self.MIN_BOT_CAPITAL
            )
            
            logger.info(
                f"🚀 Created new breakout bot {bot.id} for {opportunity.product_id} "
                f"(score={opportunity.score:.1f}, confidence={opportunity.confidence})"
            )
            
            return {
                "action": "created",
                "bot_id": bot.id,
                "pair": bot.pair,
                "opportunity": {
                    "product_id": opportunity.product_id,
                    "score": opportunity.score,
                    "confidence": opportunity.confidence,
                    "signals": opportunity.signals
                },
                "capital_allocated": self.MIN_BOT_CAPITAL
            }
            
        except Exception as e:
            logger.error(f"Failed to create bot for {opportunity.product_id}: {e}")
            return {
                "action": "failed",
                "reason": str(e),
                "opportunity": {
                    "product_id": opportunity.product_id,
                    "score": opportunity.score,
                    "confidence": opportunity.confidence
                }
            }
    
    def reallocate_freed_capital(
        self, 
        max_new_bots: int = 2
    ) -> Dict:
        """
        Create new breakout bots using freed capital from archived bots.
        
        This is called by the daily cleanup task after bots are archived.
        
        Args:
            max_new_bots: Maximum number of new bots to create
        
        Returns:
            Dict with reallocation results
        """
        logger.info("💰 Starting capital reallocation from freed capital...")
        
        # Check available capital
        capital_info = self.get_available_capital()
        
        if not capital_info["can_create_bots"]:
            logger.info(
                f"Insufficient freed capital for new bots: "
                f"${capital_info['available_capital']:.2f} < ${self.MIN_BOT_CAPITAL}"
            )
            return {
                "status": "insufficient_capital",
                "available_capital": capital_info["available_capital"],
                "bots_created": 0
            }
        
        # Get breakout opportunities
        try:
            from ..services.breakout_detector import get_breakout_detector
            detector = get_breakout_detector()
            
            breakouts = detector.scan_all_products()
            
            if not breakouts:
                logger.info("No breakout opportunities found")
                return {
                    "status": "no_opportunities",
                    "bots_created": 0
                }
            
            # Get existing active/closing pairs to avoid duplicates
            existing_pairs = detector.get_existing_bot_pairs(self.db)
            new_opportunities = detector.filter_new_opportunities(breakouts, existing_pairs)
            
            if not new_opportunities:
                logger.info("No new breakout opportunities (all pairs already have active bots)")
                return {
                    "status": "no_new_opportunities",
                    "bots_created": 0
                }
            
            logger.info(f"Found {len(new_opportunities)} new breakout opportunities")
            
            # Calculate how many bots we can create
            available = capital_info["available_capital"]
            max_by_capital = int(available / self.MIN_BOT_CAPITAL)
            bots_to_create = min(max_new_bots, max_by_capital, len(new_opportunities))
            
            logger.info(f"Creating up to {bots_to_create} new bots")
            
            # Handle each opportunity (resurrect or create)
            results = []
            for opportunity in new_opportunities[:bots_to_create]:
                result = self.handle_breakout_opportunity(opportunity)
                results.append(result)
            
            # Count successes
            created_count = sum(1 for r in results if r.get('action') in ['created', 'resurrected'])
            
            logger.info(
                f"✅ Capital reallocation complete: {created_count} bots created/resurrected "
                f"from {len(results)} attempts"
            )
            
            return {
                "status": "success",
                "bots_created": created_count,
                "results": results,
                "capital_info": capital_info
            }
            
        except Exception as e:
            logger.error(f"Capital reallocation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "bots_created": 0
            }


# Singleton pattern
def get_capital_reallocation_service(db: Session) -> CapitalReallocationService:
    """Get capital reallocation service instance."""
    return CapitalReallocationService(db)
