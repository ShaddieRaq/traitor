"""
Bot Lifecycle Management Tasks

Celery tasks for bot lifecycle automation:
- Daily cleanup (archive old closed bots)
- Capital reallocation (create new bots from freed capital)

Created: October 12, 2025
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import func

from ..core.database import SessionLocal
from ..models.models import Bot
from ..services.bot_lifecycle_service import get_lifecycle_service
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="lifecycle.daily_cleanup")
def daily_bot_lifecycle_cleanup() -> Dict:
    """
    Daily bot lifecycle management task.
    
    Responsibilities:
    1. Archive CLOSED bots after 7-day cooling period
    2. Calculate freed capital from archived bots
    3. Log lifecycle statistics
    
    Runs daily at 2:00 AM UTC (configured in celery_app.py beat_schedule).
    
    Returns:
        Dict with cleanup statistics
    """
    logger.info("🧹 Starting daily bot lifecycle cleanup...")
    
    db = SessionLocal()
    try:
        lifecycle_service = get_lifecycle_service(db)
        
        # Get bots ready for archival (CLOSED for 7+ days)
        bots_ready = lifecycle_service.get_bots_ready_for_archival()
        
        if not bots_ready:
            logger.info("✅ No bots ready for archival")
            return {
                "status": "success",
                "bots_archived": 0,
                "capital_freed": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        logger.info(f"Found {len(bots_ready)} bots ready for archival")
        
        # Archive each bot
        archived_bots = []
        total_freed_capital = 0.0
        
        for bot in bots_ready:
            try:
                result = lifecycle_service.transition_to_archived(bot)
                
                if result.get('transitioned'):
                    archived_bots.append({
                        "bot_id": bot.id,
                        "pair": bot.pair,
                        "trading_mode": bot.trading_mode,
                        "freed_capital": result.get('freed_capital', 0.0),
                        "archived_at": result.get('archived_at').isoformat() if result.get('archived_at') else None
                    })
                    total_freed_capital += result.get('freed_capital', 0.0)
                    
            except Exception as e:
                logger.error(f"Failed to archive bot {bot.id} ({bot.pair}): {e}")
        
        logger.info(
            f"📦 Daily cleanup complete: {len(archived_bots)} bots archived, "
            f"${total_freed_capital:.2f} capital freed"
        )
        
        # Log lifecycle statistics
        _log_lifecycle_statistics(db)
        
        # CAPITAL REALLOCATION: Create new bots from freed capital
        if total_freed_capital >= 15.0:  # Minimum for one bot
            logger.info(f"💰 Starting capital reallocation (${total_freed_capital:.2f} available)...")
            try:
                from ..services.capital_reallocation_service import get_capital_reallocation_service
                reallocation_service = get_capital_reallocation_service(db)
                
                # Create up to 2 new bots per day
                reallocation_result = reallocation_service.reallocate_freed_capital(max_new_bots=2)
                
                logger.info(
                    f"✅ Capital reallocation complete: {reallocation_result.get('bots_created', 0)} bots created"
                )
                
                # Add reallocation info to result
                result_with_reallocation = {
                    "status": "success",
                    "bots_archived": len(archived_bots),
                    "capital_freed": total_freed_capital,
                    "archived_bots": archived_bots,
                    "capital_reallocation": reallocation_result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return result_with_reallocation
                
            except Exception as reallocation_error:
                logger.error(f"Capital reallocation failed: {reallocation_error}")
                # Continue with normal result even if reallocation fails
        
        return {
            "status": "success",
            "bots_archived": len(archived_bots),
            "capital_freed": total_freed_capital,
            "archived_bots": archived_bots,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Daily cleanup task failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "bots_archived": 0,
            "capital_freed": 0.0,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


def _log_lifecycle_statistics(db: SessionLocal):
    """
    Log current bot lifecycle statistics.
    
    Args:
        db: Database session
    """
    try:
        # Count bots by lifecycle stage
        lifecycle_counts = db.query(
            Bot.lifecycle_stage,
            func.count(Bot.id).label('count')
        ).group_by(Bot.lifecycle_stage).all()
        
        logger.info("📊 Bot Lifecycle Statistics:")
        for stage, count in lifecycle_counts:
            logger.info(f"   {stage}: {count} bots")
        
        # Count active bots by trading mode
        active_by_mode = db.query(
            Bot.trading_mode,
            func.count(Bot.id).label('count')
        ).filter(
            Bot.lifecycle_stage == "ACTIVE"
        ).group_by(Bot.trading_mode).all()
        
        logger.info("📊 Active Bots by Mode:")
        for mode, count in active_by_mode:
            logger.info(f"   {mode or 'CORE'}: {count} bots")
        
        # Calculate total freed capital
        freed_capital = db.query(func.sum(Bot.position_size_usd)).filter(
            Bot.lifecycle_stage == "ARCHIVED"
        ).scalar() or 0.0
        
        logger.info(f"💰 Total Freed Capital: ${freed_capital:.2f}")
        
    except Exception as e:
        logger.warning(f"Failed to log lifecycle statistics: {e}")


@celery_app.task(name="lifecycle.check_pnl_triggers")
def check_pnl_triggers_task() -> Dict:
    """
    Check ACTIVE bots for P&L-based exit triggers.
    
    Triggers ACTIVE → CLOSING transition when:
    - Stop loss hit: -5% or worse
    - Take profit hit: +10% or better
    - Time limit (BREAKOUT only): 72 hours holding
    
    Runs every 10 minutes to catch exits quickly.
    
    Returns:
        Dict with trigger statistics
    """
    logger.info("🎯 Checking ACTIVE bots for P&L triggers...")
    
    db = SessionLocal()
    try:
        from ..api.raw_trades import get_pnl_by_product
        lifecycle_service = get_lifecycle_service(db)
        
        # Get all ACTIVE bots
        active_bots = db.query(Bot).filter(
            Bot.lifecycle_stage == "ACTIVE",
            Bot.status == "RUNNING"
        ).all()
        
        if not active_bots:
            logger.info("✅ No ACTIVE bots to check")
            return {
                "status": "success",
                "bots_checked": 0,
                "bots_triggered": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get P&L data for all products
        pnl_data = get_pnl_by_product(db)
        pnl_by_product = {p['product_id']: p for p in pnl_data['products']}
        
        logger.info(f"Checking {len(active_bots)} ACTIVE bots for P&L triggers...")
        
        triggered_bots = []
        
        for bot in active_bots:
            try:
                product_pnl = pnl_by_product.get(bot.pair)
                
                if not product_pnl or product_pnl['total_buy_usd'] is None:
                    continue  # Skip bots with no position data
                
                # Calculate P&L percentage
                buy_cost = product_pnl['total_buy_usd']
                if buy_cost <= 0:
                    continue
                
                pnl_percent = (product_pnl['net_pnl_usd'] / buy_cost) * 100
                
                # Check triggers
                trigger_reason = None
                
                # Stop loss: -5%
                if pnl_percent <= -5.0:
                    trigger_reason = f"stop_loss_{pnl_percent:.1f}%"
                    logger.warning(
                        f"🛑 STOP LOSS: Bot {bot.id} ({bot.pair}) at {pnl_percent:.1f}% "
                        f"(${product_pnl['net_pnl_usd']:.2f})"
                    )
                
                # Take profit: +10%
                elif pnl_percent >= 10.0:
                    trigger_reason = f"take_profit_{pnl_percent:.1f}%"
                    logger.info(
                        f"💰 TAKE PROFIT: Bot {bot.id} ({bot.pair}) at {pnl_percent:.1f}% "
                        f"(${product_pnl['net_pnl_usd']:.2f})"
                    )
                
                # Time limit (BREAKOUT only): 72 hours
                elif bot.trading_mode == "BREAKOUT" and bot.created_at:
                    hours_since_creation = (datetime.utcnow() - bot.created_at).total_seconds() / 3600
                    if hours_since_creation >= 72:
                        trigger_reason = f"time_limit_{hours_since_creation:.0f}h"
                        logger.info(
                            f"⏰ TIME LIMIT: Bot {bot.id} ({bot.pair}) held for {hours_since_creation:.0f}h "
                            f"(P&L: {pnl_percent:.1f}%)"
                        )
                
                # Trigger transition if any condition met
                if trigger_reason:
                    result = lifecycle_service.transition_to_closing(bot, reason=trigger_reason)
                    
                    if result.get('transitioned'):
                        triggered_bots.append({
                            "bot_id": bot.id,
                            "pair": bot.pair,
                            "trading_mode": bot.trading_mode,
                            "trigger_reason": trigger_reason,
                            "pnl_percent": round(pnl_percent, 2),
                            "pnl_usd": round(product_pnl['net_pnl_usd'], 2)
                        })
                        
                        # TODO: Execute sell order here (liquidation logic)
                        logger.info(f"📤 Bot {bot.id} transitioned to CLOSING - liquidation needed")
                    
            except Exception as e:
                logger.error(f"Failed to check bot {bot.id} ({bot.pair}): {e}")
        
        logger.info(
            f"✅ P&L check complete: {len(triggered_bots)} bots triggered "
            f"(out of {len(active_bots)} ACTIVE bots)"
        )
        
        return {
            "status": "success",
            "bots_checked": len(active_bots),
            "bots_triggered": len(triggered_bots),
            "triggered_bots": triggered_bots,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ P&L triggers task failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "bots_checked": 0,
            "bots_triggered": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(name="lifecycle.check_closing_bots")
def check_closing_bots_task() -> Dict:
    """
    Check CLOSING bots and transition to CLOSED if position fully liquidated.
    
    This task runs every hour to ensure bots move from CLOSING → CLOSED
    after trades execute and positions are confirmed closed.
    
    Returns:
        Dict with transition statistics
    """
    logger.info("🔍 Checking CLOSING bots for transition to CLOSED...")
    
    db = SessionLocal()
    try:
        lifecycle_service = get_lifecycle_service(db)
        
        # Get all CLOSING bots
        closing_bots = db.query(Bot).filter(
            Bot.lifecycle_stage == "CLOSING"
        ).all()
        
        if not closing_bots:
            logger.info("✅ No CLOSING bots found")
            return {
                "status": "success",
                "bots_checked": 0,
                "bots_closed": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        logger.info(f"Found {len(closing_bots)} CLOSING bots to check")
        
        closed_bots = []
        
        for bot in closing_bots:
            try:
                # Check if position is fully closed
                if bot.current_position_size == 0:
                    result = lifecycle_service.transition_to_closed(bot)
                    
                    if result.get('transitioned'):
                        closed_bots.append({
                            "bot_id": bot.id,
                            "pair": bot.pair,
                            "trading_mode": bot.trading_mode
                        })
                else:
                    logger.debug(
                        f"Bot {bot.id} ({bot.pair}) still has position: {bot.current_position_size}"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to check bot {bot.id} ({bot.pair}): {e}")
        
        logger.info(
            f"✅ Check complete: {len(closed_bots)} bots transitioned to CLOSED "
            f"(out of {len(closing_bots)} CLOSING bots)"
        )
        
        return {
            "status": "success",
            "bots_checked": len(closing_bots),
            "bots_closed": len(closed_bots),
            "closed_bots": closed_bots,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Check closing bots task failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "bots_checked": 0,
            "bots_closed": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()
