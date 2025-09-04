"""
Position Management Service for Enhanced Single Position with Tranche Support

This service handles the sophisticated position management system that allows
a single logical position per bot to be built through multiple entry tranches
and reduced through partial exits.

Phase 4.1.3 Day 2 Enhancements:
- Advanced dollar-cost averaging algorithms
- Position building strategies
- Partial exit support
- Dynamic position sizing
- Tranche optimization
"""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from enum import Enum

from ..models.models import Bot, Trade
from ..core.database import get_db

logger = logging.getLogger(__name__)


class TrancheStrategy(Enum):
    """Tranche building strategies."""
    EQUAL_SIZE = "equal_size"  # Equal USD amounts
    PYRAMID_UP = "pyramid_up"  # Increasing size with price
    PYRAMID_DOWN = "pyramid_down"  # Decreasing size with price
    ADAPTIVE = "adaptive"  # Adaptive based on market conditions


class PositionDirection(Enum):
    """Position direction for calculations."""
    LONG = "long"
    SHORT = "short"


class PositionService:
    """Service for managing enhanced single positions with tranche support."""
    
    MAX_TRANCHES_PER_POSITION = 3  # Maximum tranches per position
    MIN_TRANCHE_SIZE_USD = 10.0  # Minimum tranche size
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_position_summary(self, bot_id: int) -> Dict:
        """
        Get comprehensive position summary for a bot including all tranches.
        
        Returns:
        {
            "position_status": "OPEN",
            "total_tranches": 2,
            "total_size_usd": 250.0,
            "average_entry_price": 51333.33,
            "unrealized_pnl": 450.00,
            "tranches": [
                {"id": 1, "entry_price": 50000.0, "size_usd": 100.0, "timestamp": "..."},
                {"id": 2, "entry_price": 52000.0, "size_usd": 150.0, "timestamp": "..."}
            ]
        }
        """
        try:
            bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                return {"error": "Bot not found"}
            
            # Get all open buy trades for this bot (representing tranches)
            open_trades = self.db.query(Trade).filter(
                Trade.bot_id == bot_id,
                Trade.side == "buy",
                Trade.status == "filled",
                Trade.position_status.in_(["BUILDING", "OPEN"])
            ).order_by(Trade.created_at).all()
            
            if not open_trades:
                return {
                    "position_status": "CLOSED",
                    "total_tranches": 0,
                    "total_size_usd": 0.0,
                    "average_entry_price": None,
                    "unrealized_pnl": 0.0,
                    "tranches": []
                }
            
            # Calculate position summary
            total_size_usd = sum(trade.size_usd or 0 for trade in open_trades)
            weighted_price_sum = sum((trade.price * (trade.size_usd or 0)) for trade in open_trades)
            average_entry_price = weighted_price_sum / total_size_usd if total_size_usd > 0 else 0
            
            # Get current market price for P&L calculation
            # For now, use the last trade price as approximation
            current_price = open_trades[-1].price if open_trades else 0
            unrealized_pnl = (current_price - average_entry_price) * total_size_usd / average_entry_price if average_entry_price > 0 else 0
            
            # Build tranches list
            tranches = []
            for i, trade in enumerate(open_trades, 1):
                tranches.append({
                    "id": i,
                    "trade_id": trade.id,
                    "entry_price": float(trade.price),
                    "size_usd": float(trade.size_usd or 0),
                    "timestamp": trade.created_at.isoformat(),
                    "status": "open"
                })
            
            # Determine position status
            position_status = "OPEN"
            if len(open_trades) == 1 and open_trades[0].position_status == "BUILDING":
                position_status = "BUILDING"
            
            return {
                "position_status": position_status,
                "total_tranches": len(open_trades),
                "total_size_usd": round(total_size_usd, 2),
                "average_entry_price": round(average_entry_price, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "tranches": tranches
            }
            
        except Exception as e:
            logger.error(f"Error getting position summary for bot {bot_id}: {e}")
            return {"error": str(e)}
    
    def calculate_optimal_tranche_size(
        self, 
        bot_id: int, 
        current_price: float, 
        strategy: TrancheStrategy = TrancheStrategy.ADAPTIVE,
        market_conditions: Optional[Dict] = None
    ) -> Tuple[float, str]:
        """
        Calculate optimal tranche size based on strategy and market conditions.
        
        Args:
            bot_id: Bot identifier
            current_price: Current market price
            strategy: Tranche sizing strategy
            market_conditions: Market volatility, trend, etc.
            
        Returns:
            (optimal_size_usd, reasoning)
        """
        try:
            bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                return 0.0, "Bot not found"
            
            position_summary = self.get_position_summary(bot_id)
            current_tranches = position_summary.get("total_tranches", 0)
            base_position_size = bot.position_size_usd
            
            # Strategy-based sizing
            if strategy == TrancheStrategy.EQUAL_SIZE:
                # Equal tranches
                target_size = base_position_size / self.MAX_TRANCHES_PER_POSITION
                reasoning = f"Equal size strategy: {base_position_size} / {self.MAX_TRANCHES_PER_POSITION} tranches"
                
            elif strategy == TrancheStrategy.PYRAMID_UP:
                # Increasing size with each tranche (1x, 1.5x, 2x)
                multipliers = [1.0, 1.5, 2.0]
                total_multiplier = sum(multipliers)
                tranche_multiplier = multipliers[current_tranches] if current_tranches < len(multipliers) else 1.0
                target_size = (base_position_size / total_multiplier) * tranche_multiplier
                reasoning = f"Pyramid up strategy: tranche {current_tranches + 1} with {tranche_multiplier}x multiplier"
                
            elif strategy == TrancheStrategy.PYRAMID_DOWN:
                # Decreasing size with each tranche (2x, 1.5x, 1x)
                multipliers = [2.0, 1.5, 1.0]
                total_multiplier = sum(multipliers)
                tranche_multiplier = multipliers[current_tranches] if current_tranches < len(multipliers) else 1.0
                target_size = (base_position_size / total_multiplier) * tranche_multiplier
                reasoning = f"Pyramid down strategy: tranche {current_tranches + 1} with {tranche_multiplier}x multiplier"
                
            else:  # ADAPTIVE
                # Adaptive sizing based on market conditions and position performance
                if current_tranches == 0:
                    # First tranche: conservative entry
                    target_size = base_position_size * 0.4
                    reasoning = "Adaptive strategy: conservative first entry (40%)"
                else:
                    # Subsequent tranches: based on performance and volatility
                    avg_price = position_summary.get("average_entry_price", current_price)
                    unrealized_pnl = position_summary.get("unrealized_pnl", 0)
                    
                    if unrealized_pnl >= 0:
                        # Position profitable: smaller additional tranche
                        target_size = base_position_size * 0.25
                        reasoning = "Adaptive strategy: profitable position, smaller add (25%)"
                    else:
                        # Position at loss: larger tranche for averaging down
                        price_decline = (avg_price - current_price) / avg_price
                        if price_decline > 0.05:  # >5% decline
                            target_size = base_position_size * 0.4
                            reasoning = f"Adaptive strategy: {price_decline:.1%} decline, larger add (40%)"
                        else:
                            target_size = base_position_size * 0.3
                            reasoning = f"Adaptive strategy: {price_decline:.1%} decline, moderate add (30%)"
            
            # Apply constraints
            target_size = max(target_size, self.MIN_TRANCHE_SIZE_USD)
            target_size = min(target_size, base_position_size)  # Never exceed base position size
            
            return round(target_size, 2), reasoning
            
        except Exception as e:
            logger.error(f"Error calculating optimal tranche size for bot {bot_id}: {e}")
            return 0.0, str(e)
    
    def calculate_dollar_cost_average_metrics(self, bot_id: int, new_price: float, new_size_usd: float) -> Dict:
        """
        Calculate dollar-cost averaging metrics for adding a new tranche.
        
        Returns detailed metrics about how the new tranche affects the position.
        """
        try:
            position_summary = self.get_position_summary(bot_id)
            
            if position_summary.get("total_tranches", 0) == 0:
                # First tranche
                return {
                    "current_average_price": 0.0,
                    "new_average_price": new_price,
                    "price_improvement": 0.0,
                    "position_size_increase": new_size_usd,
                    "new_total_size": new_size_usd,
                    "cost_basis_change": new_size_usd,
                    "risk_adjusted_return": 0.0
                }
            
            current_total_size = position_summary["total_size_usd"]
            current_avg_price = position_summary["average_entry_price"]
            
            # Calculate new weighted average price
            total_cost_current = current_total_size
            total_cost_new = new_size_usd
            new_total_size = current_total_size + new_size_usd
            
            new_average_price = ((current_avg_price * current_total_size) + (new_price * new_size_usd)) / new_total_size
            
            # Calculate metrics
            price_improvement = ((current_avg_price - new_average_price) / current_avg_price) * 100 if current_avg_price > 0 else 0
            position_size_increase = (new_size_usd / current_total_size) * 100 if current_total_size > 0 else 0
            
            return {
                "current_average_price": round(current_avg_price, 2),
                "new_average_price": round(new_average_price, 2),
                "price_improvement": round(price_improvement, 3),  # percentage
                "position_size_increase": round(position_size_increase, 1),  # percentage
                "new_total_size": round(new_total_size, 2),
                "cost_basis_change": round(new_size_usd, 2),
                "risk_adjusted_return": self._calculate_risk_adjusted_return(position_summary, new_price, new_size_usd)
            }
            
        except Exception as e:
            logger.error(f"Error calculating DCA metrics for bot {bot_id}: {e}")
            return {"error": str(e)}
    
    def _calculate_risk_adjusted_return(self, position_summary: Dict, new_price: float, new_size_usd: float) -> float:
        """Calculate risk-adjusted return potential for the new tranche."""
        try:
            current_avg_price = position_summary.get("average_entry_price", new_price)
            
            # Simple risk adjustment based on price deviation
            price_deviation = abs(new_price - current_avg_price) / current_avg_price if current_avg_price > 0 else 0
            
            # Risk factor: higher deviation = higher risk
            risk_factor = min(price_deviation * 2, 0.5)  # Cap at 50% risk
            
            # Potential return estimate (simplified)
            potential_return = 0.1 - risk_factor  # 10% base return minus risk
            
            return round(potential_return * 100, 2)  # Return as percentage
            
        except Exception as e:
            logger.error(f"Error calculating risk-adjusted return: {e}")
            return 0.0
    
    def can_add_tranche(self, bot_id: int) -> Tuple[bool, str]:
        """
        Check if bot can add another tranche to its position.
        
        Returns:
            (can_add, reason)
        """
        try:
            position_summary = self.get_position_summary(bot_id)
            
            if "error" in position_summary:
                return False, position_summary["error"]
            
            current_tranches = position_summary["total_tranches"]
            
            if current_tranches >= self.MAX_TRANCHES_PER_POSITION:
                return False, f"Maximum tranches ({self.MAX_TRANCHES_PER_POSITION}) already reached"
            
            return True, "Can add tranche"
            
        except Exception as e:
            logger.error(f"Error checking tranche capacity for bot {bot_id}: {e}")
            return False, str(e)
    
    def calculate_partial_exit_strategy(
        self, 
        bot_id: int, 
        exit_percentage: float, 
        current_price: float
    ) -> Dict:
        """
        Calculate optimal partial exit strategy for a position.
        
        Args:
            bot_id: Bot identifier
            exit_percentage: Percentage of position to exit (0.0-1.0)
            current_price: Current market price
            
        Returns:
            Detailed exit strategy with tranche-by-tranche breakdown
        """
        try:
            position_summary = self.get_position_summary(bot_id)
            
            if "error" in position_summary:
                return {"error": position_summary["error"]}
            
            if position_summary["total_tranches"] == 0:
                return {"error": "No position to exit"}
            
            total_size_usd = position_summary["total_size_usd"]
            avg_entry_price = position_summary["average_entry_price"]
            tranches = position_summary["tranches"]
            
            exit_size_usd = total_size_usd * exit_percentage
            
            # Calculate P&L
            total_pnl = ((current_price - avg_entry_price) / avg_entry_price) * total_size_usd if avg_entry_price > 0 else 0
            exit_pnl = total_pnl * exit_percentage
            
            # Strategy: Exit oldest tranches first (FIFO)
            exit_plan = []
            remaining_exit_size = exit_size_usd
            
            for tranche in tranches:
                if remaining_exit_size <= 0:
                    break
                
                tranche_size = tranche["size_usd"]
                tranche_entry_price = tranche["entry_price"]
                
                if remaining_exit_size >= tranche_size:
                    # Exit entire tranche
                    exit_size = tranche_size
                    remaining_exit_size -= tranche_size
                else:
                    # Partial tranche exit
                    exit_size = remaining_exit_size
                    remaining_exit_size = 0
                
                tranche_pnl = ((current_price - tranche_entry_price) / tranche_entry_price) * exit_size if tranche_entry_price > 0 else 0
                
                exit_plan.append({
                    "tranche_id": tranche["id"],
                    "exit_size_usd": round(exit_size, 2),
                    "entry_price": tranche_entry_price,
                    "exit_price": current_price,
                    "tranche_pnl": round(tranche_pnl, 2),
                    "exit_type": "full" if exit_size == tranche_size else "partial"
                })
            
            # Calculate remaining position after exit
            remaining_size_usd = total_size_usd - exit_size_usd
            remaining_tranches = len([t for t in tranches if t["size_usd"] > 0])  # Simplified
            
            return {
                "exit_strategy": "FIFO",
                "exit_percentage": round(exit_percentage * 100, 1),
                "exit_size_usd": round(exit_size_usd, 2),
                "exit_pnl": round(exit_pnl, 2),
                "exit_plan": exit_plan,
                "remaining_position": {
                    "size_usd": round(remaining_size_usd, 2),
                    "estimated_tranches": max(0, remaining_tranches - len([p for p in exit_plan if p["exit_type"] == "full"]))
                },
                "break_even_price": avg_entry_price,
                "profit_margin": round(((current_price - avg_entry_price) / avg_entry_price) * 100, 2) if avg_entry_price > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating partial exit strategy for bot {bot_id}: {e}")
            return {"error": str(e)}
    
    def optimize_position_scaling(self, bot_id: int, market_signal_strength: float) -> Dict:
        """
        Optimize position scaling based on market signal strength and current position.
        
        Args:
            bot_id: Bot identifier
            market_signal_strength: Signal strength (-1.0 to 1.0)
            
        Returns:
            Position scaling recommendations
        """
        try:
            position_summary = self.get_position_summary(bot_id)
            
            if "error" in position_summary:
                return {"error": position_summary["error"]}
            
            current_tranches = position_summary.get("total_tranches", 0)
            total_size_usd = position_summary.get("total_size_usd", 0)
            unrealized_pnl = position_summary.get("unrealized_pnl", 0)
            
            recommendations = {
                "action": "hold",
                "confidence": 0.5,
                "reasoning": "Neutral signal",
                "suggested_size_usd": 0.0,
                "risk_level": "medium"
            }
            
            # Strong buy signal (0.5 to 1.0)
            if market_signal_strength >= 0.5:
                can_add, reason = self.can_add_tranche(bot_id)
                if can_add:
                    recommendations.update({
                        "action": "add_tranche",
                        "confidence": min(market_signal_strength, 0.9),
                        "reasoning": f"Strong buy signal ({market_signal_strength:.2f}), add tranche",
                        "suggested_size_usd": self._calculate_scaling_size(bot_id, market_signal_strength),
                        "risk_level": "low" if market_signal_strength > 0.7 else "medium"
                    })
                else:
                    recommendations.update({
                        "action": "hold",
                        "confidence": 0.7,
                        "reasoning": f"Strong buy signal but {reason.lower()}",
                        "risk_level": "medium"
                    })
            
            # Strong sell signal (-1.0 to -0.5)
            elif market_signal_strength <= -0.5:
                if current_tranches > 0:
                    # Determine exit percentage based on signal strength and P&L
                    if unrealized_pnl >= 0:
                        # Profitable position: larger exit
                        exit_percentage = min(abs(market_signal_strength), 0.8)
                    else:
                        # Losing position: smaller exit or hold for recovery
                        exit_percentage = min(abs(market_signal_strength) * 0.5, 0.5)
                    
                    recommendations.update({
                        "action": "partial_exit",
                        "confidence": min(abs(market_signal_strength), 0.9),
                        "reasoning": f"Strong sell signal ({market_signal_strength:.2f}), reduce position",
                        "suggested_exit_percentage": round(exit_percentage * 100, 1),
                        "risk_level": "high"
                    })
                else:
                    recommendations.update({
                        "action": "avoid",
                        "confidence": 0.8,
                        "reasoning": "Strong sell signal, avoid new positions",
                        "risk_level": "high"
                    })
            
            # Weak signals (-0.5 to 0.5)
            else:
                recommendations.update({
                    "action": "hold",
                    "confidence": 0.6,
                    "reasoning": f"Weak signal ({market_signal_strength:.2f}), maintain current position",
                    "risk_level": "medium"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error optimizing position scaling for bot {bot_id}: {e}")
            return {"error": str(e)}
    
    def _calculate_scaling_size(self, bot_id: int, signal_strength: float) -> float:
        """Calculate appropriate scaling size based on signal strength."""
        try:
            bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                return 0.0
            
            base_size = bot.position_size_usd
            
            # Scale size based on signal strength
            # Strong signals (0.7-1.0): 30-50% of base
            # Medium signals (0.5-0.7): 20-30% of base
            if signal_strength >= 0.7:
                size_factor = 0.3 + (signal_strength - 0.7) * 0.67  # 0.3 to 0.5
            else:
                size_factor = 0.2 + (signal_strength - 0.5) * 0.5   # 0.2 to 0.3
            
            return round(base_size * size_factor, 2)
            
        except Exception as e:
            logger.error(f"Error calculating scaling size for bot {bot_id}: {e}")
            return 0.0
    
    def calculate_next_tranche_number(self, bot_id: int) -> int:
        """Calculate the next tranche number for a bot's position."""
        try:
            position_summary = self.get_position_summary(bot_id)
            return position_summary.get("total_tranches", 0) + 1
        except Exception as e:
            logger.error(f"Error calculating next tranche number for bot {bot_id}: {e}")
            return 1
    
    def analyze_position_performance(self, bot_id: int, current_price: float) -> Dict:
        """
        Comprehensive position performance analysis with advanced metrics.
        
        Returns detailed analytics including risk metrics, efficiency, and recommendations.
        """
        try:
            position_summary = self.get_position_summary(bot_id)
            
            if "error" in position_summary:
                return {"error": position_summary["error"]}
            
            if position_summary["total_tranches"] == 0:
                return {"error": "No position to analyze"}
            
            total_size_usd = position_summary["total_size_usd"]
            avg_entry_price = position_summary["average_entry_price"]
            tranches = position_summary["tranches"]
            
            # Calculate comprehensive metrics
            total_return_pct = ((current_price - avg_entry_price) / avg_entry_price) * 100 if avg_entry_price > 0 else 0
            total_return_usd = (total_return_pct / 100) * total_size_usd
            
            # Tranche-level analysis
            tranche_analysis = []
            best_tranche = {"return": float('-inf'), "id": None}
            worst_tranche = {"return": float('inf'), "id": None}
            
            for tranche in tranches:
                entry_price = tranche["entry_price"]
                size_usd = tranche["size_usd"]
                tranche_return_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                tranche_return_usd = (tranche_return_pct / 100) * size_usd
                
                tranche_data = {
                    "id": tranche["id"],
                    "entry_price": entry_price,
                    "size_usd": size_usd,
                    "return_pct": round(tranche_return_pct, 2),
                    "return_usd": round(tranche_return_usd, 2),
                    "weight": round((size_usd / total_size_usd) * 100, 1)
                }
                tranche_analysis.append(tranche_data)
                
                # Track best/worst performers
                if tranche_return_pct > best_tranche["return"]:
                    best_tranche = {"return": tranche_return_pct, "id": tranche["id"], "entry": entry_price}
                if tranche_return_pct < worst_tranche["return"]:
                    worst_tranche = {"return": tranche_return_pct, "id": tranche["id"], "entry": entry_price}
            
            # Risk metrics
            price_volatility = self._calculate_price_volatility(tranches, current_price)
            position_concentration = self._calculate_position_concentration(tranche_analysis)
            efficiency_score = self._calculate_efficiency_score(tranche_analysis, total_return_pct)
            
            # Performance grade
            performance_grade = self._assign_performance_grade(total_return_pct, efficiency_score, len(tranches))
            
            return {
                "position_summary": {
                    "total_return_pct": round(total_return_pct, 2),
                    "total_return_usd": round(total_return_usd, 2),
                    "average_entry_price": avg_entry_price,
                    "current_price": current_price,
                    "total_size_usd": total_size_usd,
                    "total_tranches": len(tranches)
                },
                "tranche_analysis": tranche_analysis,
                "performance_metrics": {
                    "best_tranche": {
                        "id": best_tranche["id"],
                        "return_pct": round(best_tranche["return"], 2),
                        "entry_price": best_tranche["entry"]
                    },
                    "worst_tranche": {
                        "id": worst_tranche["id"],
                        "return_pct": round(worst_tranche["return"], 2),
                        "entry_price": worst_tranche["entry"]
                    },
                    "price_volatility": round(price_volatility, 3),
                    "position_concentration": round(position_concentration, 2),
                    "efficiency_score": round(efficiency_score, 2),
                    "performance_grade": performance_grade
                },
                "recommendations": self._generate_performance_recommendations(
                    total_return_pct, efficiency_score, len(tranches), position_concentration
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing position performance for bot {bot_id}: {e}")
            return {"error": str(e)}
    
    def _calculate_price_volatility(self, tranches: List[Dict], current_price: float) -> float:
        """Calculate price volatility based on tranche entry prices."""
        if len(tranches) < 2:
            return 0.0
        
        prices = [tranche["entry_price"] for tranche in tranches] + [current_price]
        avg_price = sum(prices) / len(prices)
        variance = sum((price - avg_price) ** 2 for price in prices) / len(prices)
        volatility = (variance ** 0.5) / avg_price if avg_price > 0 else 0
        
        return volatility
    
    def _calculate_position_concentration(self, tranche_analysis: List[Dict]) -> float:
        """Calculate position concentration (how evenly distributed the tranches are)."""
        if not tranche_analysis:
            return 100.0
        
        weights = [tranche["weight"] for tranche in tranche_analysis]
        equal_weight = 100 / len(weights)
        
        # Herfindahl index adapted for position concentration
        concentration = sum((weight - equal_weight) ** 2 for weight in weights)
        max_concentration = (100 - equal_weight) ** 2 * len(weights)
        
        return (concentration / max_concentration) * 100 if max_concentration > 0 else 0
    
    def _calculate_efficiency_score(self, tranche_analysis: List[Dict], total_return: float) -> float:
        """Calculate position building efficiency score (0-100)."""
        if not tranche_analysis:
            return 0.0
        
        # Perfect DCA would have increasing returns for lower entry prices
        sorted_tranches = sorted(tranche_analysis, key=lambda x: x["entry_price"])
        
        efficiency_points = 0
        max_points = len(sorted_tranches) - 1
        
        for i in range(len(sorted_tranches) - 1):
            current_return = sorted_tranches[i]["return_pct"]
            next_return = sorted_tranches[i + 1]["return_pct"]
            
            # Award points if lower entry price has higher return (good DCA)
            if current_return >= next_return:
                efficiency_points += 1
        
        base_efficiency = (efficiency_points / max_points) * 100 if max_points > 0 else 100
        
        # Bonus for positive overall return
        return_bonus = min(total_return, 20) if total_return > 0 else max(total_return, -20)
        
        return max(0, min(100, base_efficiency + return_bonus))
    
    def _assign_performance_grade(self, total_return: float, efficiency: float, tranche_count: int) -> str:
        """Assign a letter grade to position performance."""
        # Weighted score: 60% return, 30% efficiency, 10% tranche utilization
        return_score = min(max(total_return + 10, 0), 20) * 3  # -10% to +10% maps to 0-60
        efficiency_score = efficiency * 0.3
        tranche_score = min(tranche_count / 3, 1) * 10  # Up to 3 tranches = 10 points
        
        total_score = return_score + efficiency_score + tranche_score
        
        if total_score >= 85:
            return "A+"
        elif total_score >= 80:
            return "A"
        elif total_score >= 75:
            return "A-"
        elif total_score >= 70:
            return "B+"
        elif total_score >= 65:
            return "B"
        elif total_score >= 60:
            return "B-"
        elif total_score >= 55:
            return "C+"
        elif total_score >= 50:
            return "C"
        elif total_score >= 45:
            return "C-"
        elif total_score >= 40:
            return "D"
        else:
            return "F"
    
    def _generate_performance_recommendations(
        self, total_return: float, efficiency: float, tranche_count: int, concentration: float
    ) -> List[str]:
        """Generate actionable recommendations based on performance analysis."""
        recommendations = []
        
        # Return-based recommendations
        if total_return < -5:
            recommendations.append("Consider partial exit to limit losses if trend continues downward")
        elif total_return > 10:
            recommendations.append("Strong performance - consider taking partial profits")
        
        # Efficiency-based recommendations
        if efficiency < 50:
            recommendations.append("Position building could be optimized - consider more strategic entry timing")
        elif efficiency > 80:
            recommendations.append("Excellent position building efficiency - maintain strategy")
        
        # Tranche utilization recommendations
        if tranche_count == 1:
            recommendations.append("Single tranche position - consider adding tranches for better dollar-cost averaging")
        elif tranche_count < 3:
            recommendations.append("Consider using remaining tranche capacity for better risk distribution")
        
        # Concentration recommendations
        if concentration > 70:
            recommendations.append("High position concentration - consider more balanced tranche sizing")
        elif concentration < 20:
            recommendations.append("Good position distribution across tranches")
        
        if not recommendations:
            recommendations.append("Position management is well-balanced - continue current strategy")
        
        return recommendations
    
    def update_position_status(self, bot_id: int, trade: Trade) -> None:
        """
        Update position status based on the new trade.
        
        Position Status Lifecycle:
        - CLOSED: No open positions
        - BUILDING: First tranche added, can add more
        - OPEN: Multiple tranches, position established
        - REDUCING: Partial exits happening
        """
        try:
            position_summary = self.get_position_summary(bot_id)
            total_tranches = position_summary.get("total_tranches", 0)
            
            if trade.side == "buy":
                # Adding to position
                if total_tranches == 1:
                    new_status = "BUILDING"
                elif total_tranches > 1:
                    new_status = "OPEN"
                else:
                    new_status = "BUILDING"  # First tranche
            else:  # sell
                # Reducing position
                if total_tranches > 1:
                    new_status = "REDUCING"
                else:
                    new_status = "CLOSED"  # Last tranche sold
            
            # Update the trade's position status
            trade.position_status = new_status
            
            # Update all related trades with the same status
            related_trades = self.db.query(Trade).filter(
                Trade.bot_id == bot_id,
                Trade.side == "buy",
                Trade.status == "filled"
            ).all()
            
            for related_trade in related_trades:
                if new_status == "CLOSED":
                    related_trade.position_status = "CLOSED"
                else:
                    related_trade.position_status = new_status
            
            self.db.commit()
            logger.info(f"Updated position status for bot {bot_id} to {new_status}")
            
        except Exception as e:
            logger.error(f"Error updating position status for bot {bot_id}: {e}")
            self.db.rollback()
    
    def calculate_average_entry_price(self, bot_id: int) -> Optional[float]:
        """Calculate weighted average entry price across all open tranches."""
        try:
            position_summary = self.get_position_summary(bot_id)
            return position_summary.get("average_entry_price")
        except Exception as e:
            logger.error(f"Error calculating average entry price for bot {bot_id}: {e}")
            return None
    
    def create_position_tranches_json(self, bot_id: int) -> str:
        """
        Create JSON representation of position tranches for storage.
        
        Returns JSON string like:
        {
            "tranches": [...],
            "average_entry": 51333.33,
            "total_size_usd": 250.0,
            "created_at": "2025-09-03T20:30:00Z",
            "last_updated": "2025-09-03T20:30:00Z"
        }
        """
        try:
            position_summary = self.get_position_summary(bot_id)
            
            if "error" in position_summary:
                return json.dumps({"error": position_summary["error"]})
            
            tranches_data = {
                "tranches": position_summary.get("tranches", []),
                "average_entry": position_summary.get("average_entry_price", 0),
                "total_size_usd": position_summary.get("total_size_usd", 0),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            return json.dumps(tranches_data)
            
        except Exception as e:
            logger.error(f"Error creating position tranches JSON for bot {bot_id}: {e}")
            return json.dumps({"error": str(e)})
