"""
Bot Lifecycle Management Service

Handles bot state transitions:
- ACTIVE → CLOSING → CLOSED → ARCHIVED → (DELETED or RESURRECTED)

Created: October 12, 2025
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.models import Bot, SignalPredictionRecord

logger = logging.getLogger(__name__)


class BotLifecycleService:
    """
    Manages bot lifecycle state transitions and resurrection logic.
    """
    
    # Lifecycle stage constants
    ACTIVE = "ACTIVE"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"
    
    # Resurrection criteria
    MIN_PREDICTIONS_FOR_RESURRECTION = 100  # Need meaningful learning history
    MAX_LOSS_FOR_RESURRECTION = 50.0  # Won't resurrect bots that lost > $50
    MAX_ARCHIVED_DAYS = 30  # Won't resurrect if archived > 30 days
    MIN_COOLDOWN_HOURS = 24  # Must be archived at least 24h before resurrection
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== State Transitions ==========
    
    def transition_to_closing(self, bot: Bot, reason: str = "position_exit") -> Dict:
        """
        Transition bot from ACTIVE to CLOSING.
        Called when P/L exit triggers (take profit, stop loss, time limit).
        
        Args:
            bot: Bot instance
            reason: Why position is being closed
        
        Returns:
            Transition result dictionary
        """
        if bot.lifecycle_stage != self.ACTIVE:
            logger.warning(
                f"Bot {bot.id} ({bot.pair}) not ACTIVE (current: {bot.lifecycle_stage}), "
                f"skipping transition to CLOSING"
            )
            return {"transitioned": False, "reason": "not_active"}
        
        bot.lifecycle_stage = self.CLOSING
        self.db.commit()
        
        logger.info(
            f"🔄 Bot {bot.id} ({bot.pair}) → CLOSING | "
            f"Reason: {reason} | Position: {bot.current_position_size}"
        )
        
        return {
            "transitioned": True,
            "from_stage": self.ACTIVE,
            "to_stage": self.CLOSING,
            "reason": reason,
            "bot_id": bot.id,
            "pair": bot.pair
        }
    
    def transition_to_closed(self, bot: Bot) -> Dict:
        """
        Transition bot from CLOSING to CLOSED.
        Called after position is fully liquidated (position_size = 0).
        
        Args:
            bot: Bot instance
        
        Returns:
            Transition result dictionary
        """
        if bot.lifecycle_stage != self.CLOSING:
            logger.warning(
                f"Bot {bot.id} ({bot.pair}) not CLOSING (current: {bot.lifecycle_stage}), "
                f"skipping transition to CLOSED"
            )
            return {"transitioned": False, "reason": "not_closing"}
        
        if bot.current_position_size > 0:
            logger.warning(
                f"Bot {bot.id} ({bot.pair}) still has position ({bot.current_position_size}), "
                f"cannot transition to CLOSED"
            )
            return {"transitioned": False, "reason": "position_open"}
        
        bot.lifecycle_stage = self.CLOSED
        bot.status = "STOPPED"  # Stop signal evaluation
        self.db.commit()
        
        logger.info(
            f"✅ Bot {bot.id} ({bot.pair}) → CLOSED | "
            f"Position liquidated, awaiting archival (6 hours)"
        )
        
        return {
            "transitioned": True,
            "from_stage": self.CLOSING,
            "to_stage": self.CLOSED,
            "bot_id": bot.id,
            "pair": bot.pair,
            "archival_eligible_at": datetime.utcnow() + timedelta(hours=6)
        }
    
    def transition_to_archived(self, bot: Bot) -> Dict:
        """
        Transition bot from CLOSED to ARCHIVED.
        Called by hourly cleanup task after 6-hour cooling period.
        
        Args:
            bot: Bot instance
        
        Returns:
            Transition result dictionary with freed capital
        """
        if bot.lifecycle_stage != self.CLOSED:
            logger.warning(
                f"Bot {bot.id} ({bot.pair}) not CLOSED (current: {bot.lifecycle_stage}), "
                f"skipping transition to ARCHIVED"
            )
            return {"transitioned": False, "reason": "not_closed"}
        
        # Check 6-hour cooling period
        if bot.updated_at and bot.updated_at > datetime.utcnow() - timedelta(hours=6):
            logger.debug(
                f"Bot {bot.id} ({bot.pair}) not ready for archival "
                f"(updated {bot.updated_at}, need 6 hours)"
            )
            return {"transitioned": False, "reason": "cooling_period"}
        
        # Archive the bot
        bot.lifecycle_stage = self.ARCHIVED
        bot.archived_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(
            f"📦 Bot {bot.id} ({bot.pair}) → ARCHIVED | "
            f"Freed capital: ${bot.position_size_usd:.2f} | "
            f"Learning preserved"
        )
        
        return {
            "transitioned": True,
            "from_stage": self.CLOSED,
            "to_stage": self.ARCHIVED,
            "bot_id": bot.id,
            "pair": bot.pair,
            "freed_capital": bot.position_size_usd,
            "archived_at": bot.archived_at
        }
    
    # ========== Resurrection Logic ==========
    
    def can_resurrect(self, bot: Bot) -> tuple[bool, Optional[str]]:
        """
        Check if bot is eligible for resurrection.
        
        Args:
            bot: Bot instance
        
        Returns:
            (can_resurrect, reason) tuple
        """
        # Must be archived
        if bot.lifecycle_stage != self.ARCHIVED:
            return False, f"not_archived (current: {bot.lifecycle_stage})"
        
        # Must have archival timestamp
        if not bot.archived_at:
            return False, "no_archived_timestamp"
        
        # Check cooling period (24h minimum)
        hours_archived = (datetime.utcnow() - bot.archived_at).total_seconds() / 3600
        if hours_archived < self.MIN_COOLDOWN_HOURS:
            return False, f"cooling_period ({hours_archived:.1f}h < {self.MIN_COOLDOWN_HOURS}h)"
        
        # Check max archived time (30 days)
        if hours_archived > self.MAX_ARCHIVED_DAYS * 24:
            return False, f"too_stale ({hours_archived/24:.1f} days > {self.MAX_ARCHIVED_DAYS} days)"
        
        # Check learning data
        prediction_count = self.db.query(func.count(SignalPredictionRecord.id)).filter(
            SignalPredictionRecord.bot_id == bot.id
        ).scalar() or 0
        
        if prediction_count < self.MIN_PREDICTIONS_FOR_RESURRECTION:
            return False, f"insufficient_learning ({prediction_count} < {self.MIN_PREDICTIONS_FOR_RESURRECTION})"
        
        # Check performance (don't resurrect terrible performers)
        # Note: Would query RawTrade P&L here, but for now use basic check
        # TODO: Add total_pnl column to Bot model or query RawTrade
        
        return True, None
    
    def resurrect_bot(
        self, 
        bot: Bot, 
        reason: str,
        breakout_score: float,
        breakout_confidence: str
    ) -> Dict:
        """
        Resurrect archived bot back to ACTIVE trading.
        Preserves all learning data.
        
        Args:
            bot: Bot instance
            reason: Why bot is being resurrected
            breakout_score: Breakout detection score
            breakout_confidence: HIGH, MEDIUM, LOW
        
        Returns:
            Resurrection result dictionary
        
        Raises:
            ValueError: If bot not eligible for resurrection
        """
        can_resurrect, fail_reason = self.can_resurrect(bot)
        
        if not can_resurrect:
            raise ValueError(
                f"Bot {bot.id} ({bot.pair}) not eligible for resurrection: {fail_reason}"
            )
        
        # Get prediction count for logging
        prediction_count = self.db.query(func.count(SignalPredictionRecord.id)).filter(
            SignalPredictionRecord.bot_id == bot.id
        ).scalar() or 0
        
        # Resurrect the bot
        bot.lifecycle_stage = self.ACTIVE
        bot.status = "RUNNING"
        bot.archived_at = None
        
        # Reset position state (clean slate)
        bot.current_position_size = 0.0
        bot.current_position_entry_price = None
        bot.last_trade_reason = f"RESURRECTED:{reason}"
        
        self.db.commit()
        
        logger.info(
            f"🔄 RESURRECTED bot {bot.id} ({bot.pair}) → ACTIVE | "
            f"Reason: {reason} | Score: {breakout_score:.1f} ({breakout_confidence}) | "
            f"Learning preserved: {prediction_count} predictions"
        )
        
        return {
            "resurrected": True,
            "bot_id": bot.id,
            "pair": bot.pair,
            "lifecycle_stage": self.ACTIVE,
            "status": "RUNNING",
            "reason": reason,
            "breakout_score": breakout_score,
            "breakout_confidence": breakout_confidence,
            "learning_preserved": True,
            "predictions_available": prediction_count
        }
    
    def should_resurrect(
        self, 
        bot: Bot, 
        breakout_confidence: str
    ) -> tuple[bool, Optional[str]]:
        """
        Smart decision: should bot be resurrected vs creating new?
        
        Args:
            bot: Bot instance
            breakout_confidence: HIGH, MEDIUM, LOW
        
        Returns:
            (should_resurrect, reason) tuple
        """
        # Check basic eligibility first
        can_resurrect, fail_reason = self.can_resurrect(bot)
        
        if not can_resurrect:
            return False, fail_reason
        
        # Don't resurrect for LOW confidence breakouts
        if breakout_confidence == "LOW":
            return False, "breakout_confidence_too_low"
        
        # TODO: Check historical P&L when available
        # For now, allow resurrection if basic checks pass
        
        return True, None
    
    # ========== Query Helpers ==========
    
    def get_bots_ready_for_archival(self) -> List[Bot]:
        """
        Get all CLOSED bots ready for archival (6+ hours old).
        
        Returns:
            List of Bot instances
        """
        cutoff = datetime.utcnow() - timedelta(hours=6)
        
        return self.db.query(Bot).filter(
            Bot.lifecycle_stage == self.CLOSED,
            Bot.updated_at < cutoff
        ).all()
    
    def get_archived_bots_by_pair(self, pair: str) -> List[Bot]:
        """
        Get all archived bots for a specific trading pair.
        
        Args:
            pair: Trading pair (e.g., "BTC-USD")
        
        Returns:
            List of Bot instances
        """
        return self.db.query(Bot).filter(
            Bot.pair == pair,
            Bot.lifecycle_stage == self.ARCHIVED
        ).all()
    
    def get_freed_capital(self) -> float:
        """
        Calculate total capital freed from archived bots.
        
        Returns:
            Total USD freed
        """
        total = self.db.query(func.sum(Bot.position_size_usd)).filter(
            Bot.lifecycle_stage == self.ARCHIVED
        ).scalar() or 0.0
        
        return float(total)


# Singleton pattern
_lifecycle_service_instance = None

def get_lifecycle_service(db: Session) -> BotLifecycleService:
    """Get or create lifecycle service instance."""
    return BotLifecycleService(db)
