"""
Trading Safety Service - Phase 4.1.1
Provides hardcoded limits and circuit breakers for maximum safety during real trading.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models.models import Bot, Trade

logger = logging.getLogger(__name__)


class TradingSafetyLimits:
    """Hardcoded safety limits - never exceed these values."""
    
    # Daily limits
    MAX_DAILY_LOSS_USD = 100.00  # Maximum daily loss across all bots
    MAX_DAILY_TRADES = 10        # Maximum trades per day across all bots
    MAX_TRADES_PER_BOT_DAILY = 5 # Maximum trades per bot per day
    
    # Position limits  
    MAX_POSITION_SIZE_USD = 25.00    # Maximum single trade size
    MIN_POSITION_SIZE_USD = 5.00     # Minimum trade size (avoid dust trades)
    
    # Bot limits
    MAX_ACTIVE_POSITIONS = 5         # Maximum concurrent positions across all bots
    
    # Temperature requirements
    MIN_TEMPERATURE_FOR_TRADING = "WARM"  # Minimum temperature to allow trading
    
    # Emergency circuit breakers
    MAX_CONSECUTIVE_LOSSES = 3       # Stop bot after 3 consecutive losses
    EMERGENCY_STOP_LOSS_USD = 50.00  # Emergency stop if single bot loses this much


class TradingSafetyService:
    """
    Core trading safety service with hardcoded limits and circuit breakers.
    NO TRADING IS ALLOWED WITHOUT PASSING ALL SAFETY CHECKS.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.limits = TradingSafetyLimits()
    
    def validate_trade_request(self, bot: Bot, side: str, size_usd: float, 
                             current_temperature: str) -> Dict[str, Any]:
        """
        Comprehensive trade validation with all safety checks.
        
        Args:
            bot: Bot requesting to trade
            side: "buy" or "sell"
            size_usd: Trade size in USD
            current_temperature: Bot's current temperature
            
        Returns:
            Dict with validation result:
            {
                "allowed": bool,
                "reason": str,
                "safety_checks": Dict[str, bool]
            }
        """
        logger.info(f"Validating trade request: Bot {bot.id} ({bot.name}) - {side} ${size_usd} - Temp: {current_temperature}")
        
        safety_checks = {}
        reasons = []
        
        # 1. Position size limits
        safety_checks["position_size_valid"] = self._check_position_size(size_usd)
        if not safety_checks["position_size_valid"]:
            reasons.append(f"Position size ${size_usd} exceeds limits (${self.limits.MIN_POSITION_SIZE_USD}-${self.limits.MAX_POSITION_SIZE_USD})")
        
        # 2. Daily trade limits
        safety_checks["daily_trade_limit"] = self._check_daily_trade_limits(bot)
        if not safety_checks["daily_trade_limit"]:
            reasons.append("Daily trade limits exceeded")
        
        # 3. Daily loss limits
        safety_checks["daily_loss_limit"] = self._check_daily_loss_limits()
        if not safety_checks["daily_loss_limit"]:
            reasons.append(f"Daily loss limit exceeded (${self.limits.MAX_DAILY_LOSS_USD})")
        
        # 4. Temperature requirements
        safety_checks["temperature_check"] = self._check_temperature_requirements(current_temperature)
        if not safety_checks["temperature_check"]:
            reasons.append(f"Temperature {current_temperature} below minimum {self.limits.MIN_TEMPERATURE_FOR_TRADING}")
        
        # 5. Active position limits
        safety_checks["active_position_limit"] = self._check_active_position_limits()
        if not safety_checks["active_position_limit"]:
            reasons.append(f"Too many active positions (max: {self.limits.MAX_ACTIVE_POSITIONS})")
        
        # 6. Consecutive loss protection
        safety_checks["consecutive_loss_check"] = self._check_consecutive_losses(bot)
        if not safety_checks["consecutive_loss_check"]:
            reasons.append(f"Bot has {self.limits.MAX_CONSECUTIVE_LOSSES}+ consecutive losses")
        
        # 7. Emergency circuit breaker
        safety_checks["emergency_circuit_breaker"] = self._check_emergency_circuit_breaker(bot)
        if not safety_checks["emergency_circuit_breaker"]:
            reasons.append(f"Emergency circuit breaker triggered (>${self.limits.EMERGENCY_STOP_LOSS_USD} loss)")
        
        # Overall validation result
        all_checks_passed = all(safety_checks.values())
        
        result = {
            "allowed": all_checks_passed,
            "reason": "; ".join(reasons) if reasons else "All safety checks passed",
            "safety_checks": safety_checks,
            "validated_at": datetime.utcnow(),
            "limits_applied": {
                "max_daily_loss": self.limits.MAX_DAILY_LOSS_USD,
                "max_position_size": self.limits.MAX_POSITION_SIZE_USD,
                "max_daily_trades": self.limits.MAX_DAILY_TRADES
            }
        }
        
        if all_checks_passed:
            logger.info(f"✅ Trade APPROVED: Bot {bot.id} - {side} ${size_usd}")
        else:
            logger.warning(f"❌ Trade REJECTED: Bot {bot.id} - {result['reason']}")
        
        return result
    
    def _check_position_size(self, size_usd: float) -> bool:
        """Check if position size is within limits."""
        return (self.limits.MIN_POSITION_SIZE_USD <= size_usd <= self.limits.MAX_POSITION_SIZE_USD)
    
    def _check_daily_trade_limits(self, bot: Bot) -> bool:
        """Check daily trade count limits (global and per-bot)."""
        today = datetime.utcnow().date()
        
        # Check global daily trades - ONLY COUNT BOT-MADE TRADES
        # External Coinbase trades should not count toward daily limits
        global_trades_today = self.db.query(Trade).filter(
            and_(
                func.date(Trade.created_at) == today,
                Trade.bot_id.isnot(None)  # Only count bot-made trades
            )
        ).count()
        
        if global_trades_today >= self.limits.MAX_DAILY_TRADES:
            return False
        
        # Check per-bot daily trades
        bot_trades_today = self.db.query(Trade).filter(
            and_(
                Trade.bot_id == bot.id,
                func.date(Trade.created_at) == today
            )
        ).count()
        
        return bot_trades_today < self.limits.MAX_TRADES_PER_BOT_DAILY
    
    def _check_daily_loss_limits(self) -> bool:
        """Check if daily loss limits would be exceeded."""
        today = datetime.utcnow().date()
        
        # Calculate today's P&L from filled trades
        trades_today = self.db.query(Trade).filter(
            and_(
                func.date(Trade.created_at) == today,
                Trade.status == "filled"
            )
        ).all()
        
        total_loss = 0.0
        for trade in trades_today:
            # Simple P&L calculation - more sophisticated calculation will come in Phase 4.3
            # For now, just track if we're losing too much on fees and slippage
            if trade.fee:
                total_loss += trade.fee
        
        # Conservative approach: if we have any significant losses today, be cautious
        return total_loss < self.limits.MAX_DAILY_LOSS_USD
    
    def _check_temperature_requirements(self, current_temperature: str) -> bool:
        """Check if bot temperature meets minimum trading requirements."""
        temperature_hierarchy = {
            "FROZEN": 0,
            "COOL": 1, 
            "WARM": 2,
            "HOT": 3
        }
        
        current_level = temperature_hierarchy.get(current_temperature, 0)
        required_level = temperature_hierarchy.get(self.limits.MIN_TEMPERATURE_FOR_TRADING, 2)
        
        return current_level >= required_level
    
    def _check_active_position_limits(self) -> bool:
        """Check if we have too many active positions."""
        # Count bots with non-zero positions
        active_positions = self.db.query(Bot).filter(
            Bot.current_position_size != 0.0
        ).count()
        
        return active_positions < self.limits.MAX_ACTIVE_POSITIONS
    
    def _check_consecutive_losses(self, bot: Bot) -> bool:
        """Check for consecutive losses that would trigger protection."""
        # Get last few trades for this bot
        recent_trades = self.db.query(Trade).filter(
            and_(
                Trade.bot_id == bot.id,
                Trade.status == "filled"
            )
        ).order_by(Trade.created_at.desc()).limit(self.limits.MAX_CONSECUTIVE_LOSSES).all()
        
        if len(recent_trades) < self.limits.MAX_CONSECUTIVE_LOSSES:
            return True  # Not enough trades to trigger protection
        
        # For now, simplified loss detection based on fees
        # More sophisticated P&L calculation in Phase 4.3
        consecutive_losses = 0
        for trade in recent_trades:
            if trade.fee and trade.fee > 0:  # Any fee is considered a loss for safety
                consecutive_losses += 1
            else:
                break  # Non-loss breaks the streak
        
        return consecutive_losses < self.limits.MAX_CONSECUTIVE_LOSSES
    
    def _check_emergency_circuit_breaker(self, bot: Bot) -> bool:
        """Emergency circuit breaker for catastrophic losses."""
        # Check if this bot has lost too much recently
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_trades = self.db.query(Trade).filter(
            and_(
                Trade.bot_id == bot.id,
                Trade.created_at >= week_ago,
                Trade.status == "filled"
            )
        ).all()
        
        total_fees = sum(trade.fee or 0 for trade in recent_trades)
        
        # Emergency stop if fees alone exceed limit (conservative approach)
        return total_fees < self.limits.EMERGENCY_STOP_LOSS_USD
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status and limits."""
        today = datetime.utcnow().date()
        
        # Daily trade count - ONLY COUNT BOT-MADE TRADES
        # External Coinbase trades should not count toward daily limits
        trades_today = self.db.query(Trade).filter(
            and_(
                func.date(Trade.created_at) == today,
                Trade.bot_id.isnot(None)  # Only count bot-made trades
            )
        ).count()
        
        # Active positions
        active_positions = self.db.query(Bot).filter(
            Bot.current_position_size != 0.0
        ).count()
        
        return {
            "limits": {
                "max_daily_loss_usd": self.limits.MAX_DAILY_LOSS_USD,
                "max_daily_trades": self.limits.MAX_DAILY_TRADES,
                "max_position_size_usd": self.limits.MAX_POSITION_SIZE_USD,
                "min_position_size_usd": self.limits.MIN_POSITION_SIZE_USD,
                "max_active_positions": self.limits.MAX_ACTIVE_POSITIONS,
                "min_temperature": self.limits.MIN_TEMPERATURE_FOR_TRADING
            },
            "current_status": {
                "trades_today": trades_today,
                "trades_remaining": max(0, self.limits.MAX_DAILY_TRADES - trades_today),
                "active_positions": active_positions,
                "positions_available": max(0, self.limits.MAX_ACTIVE_POSITIONS - active_positions)
            },
            "safety_enabled": True,
            "last_updated": datetime.utcnow()
        }
