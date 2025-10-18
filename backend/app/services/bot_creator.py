"""
Breakout Bot Creator

Automatically creates trading bots for detected breakout opportunities.

Created: October 12, 2025
"""

import json
import logging
from typing import List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.models import Bot
from app.services.risk_adjustment_service import RiskAdjustmentService

logger = logging.getLogger(__name__)


def create_breakout_bot(
    db: Session,
    product_id: str,
    breakout_score: float,
    signals: List[str],
    initial_investment: float = 15.0
) -> Bot:
    """
    Create a breakout bot for an opportunity.
    
    Args:
        db: Database session
        product_id: Trading pair (e.g., "DASH-USD")
        breakout_score: Breakout detection score (0-100)
        signals: List of detected signals
        initial_investment: Starting capital (default $15)
    
    Returns:
        Created Bot instance
    """
    
    # Breakout-specific signal configuration
    # More aggressive than core bots for quick entries/exits
    signal_config = {
        "rsi": {
            "enabled": True,
            "weight": 0.5,  # Higher RSI weight for momentum
            "period": 14,
            "buy_threshold": 40,  # Less strict (catch momentum earlier)
            "sell_threshold": 65  # Tighter (exit faster)
        },
        "moving_average": {
            "enabled": True,
            "weight": 0.3,
            "fast_period": 8,  # Faster MA for quick signals
            "slow_period": 20
        },
        "macd": {
            "enabled": True,
            "weight": 0.2,
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        }
    }
    
    # Calculate appropriate stop loss and take profit based on score
    # Higher scores = more aggressive (wider stops, higher targets)
    if breakout_score >= 70:
        # HIGH confidence - let it run
        stop_loss_pct = 8.0  # Wider stop
        take_profit_pct = 30.0  # Higher target
    elif breakout_score >= 50:
        # MEDIUM confidence - moderate
        stop_loss_pct = 6.0
        take_profit_pct = 20.0
    else:
        # LOW confidence - tight
        stop_loss_pct = 5.0
        take_profit_pct = 15.0
    
    # Create bot
    bot = Bot(
        name=f"Breakout-{product_id}",
        description=f"Auto-created breakout bot for {product_id} (score={breakout_score:.1f}, signals={', '.join(signals)})",
        pair=product_id,
        status="RUNNING",  # Auto-start for breakout opportunities
        trading_mode="BREAKOUT",  # Mark as breakout bot
        position_size_usd=initial_investment,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        signal_config=json.dumps(signal_config),
        created_at=datetime.utcnow()
    )
    
    db.add(bot)
    db.flush()  # Get bot.id
    
    logger.info(
        f"🚀 Created BREAKOUT bot #{bot.id} for {product_id} "
        f"(score={breakout_score}, TP={take_profit_pct}%, SL={stop_loss_pct}%)"
    )
    logger.info(f"   Signals: {', '.join(signals)}")
    
    return bot


def cleanup_stale_breakout_bots(db: Session, max_age_hours: int = 72):
    """
    Delete breakout bots that are too old or have lost momentum.
    
    Breakout bots should be short-lived (24-72 hours max).
    If they haven't profited or exited by then, delete them.
    
    Args:
        db: Database session
        max_age_hours: Maximum age in hours (default 72 = 3 days)
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
    
    # Find stale breakout bots
    stale_bots = db.query(Bot).filter(
        Bot.trading_mode == "BREAKOUT",
        Bot.is_active == True,
        Bot.created_at < cutoff_time,
        Bot.current_position_size == 0  # No open position
    ).all()
    
    if not stale_bots:
        logger.info("No stale breakout bots to cleanup")
        return 0
    
    deleted_count = 0
    for bot in stale_bots:
        age_hours = (datetime.utcnow() - bot.created_at).total_seconds() / 3600
        logger.info(
            f"🗑️ Deleting stale breakout bot #{bot.id} ({bot.pair}) "
            f"- age={age_hours:.1f}h, no position"
        )
        db.delete(bot)
        deleted_count += 1
    
    db.commit()
    logger.info(f"✅ Cleaned up {deleted_count} stale breakout bots")
    
    return deleted_count
