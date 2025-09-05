# Position Reconciliation Service
# Reconciles bot position tracking with actual Coinbase holdings

import logging
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from decimal import Decimal
from datetime import datetime

from ..models.models import Bot, Trade
from .coinbase_service import CoinbaseService

logger = logging.getLogger(__name__)

class PositionReconciliationService:
    """Service for reconciling bot positions with actual Coinbase holdings."""
    
    def __init__(self, db: Session):
        self.db = db
        self.coinbase_service = CoinbaseService()
    
    def reconcile_all_bot_positions(self) -> Dict[str, any]:
        """
        Reconcile all bot positions with actual Coinbase holdings.
        
        Returns:
            Summary of reconciliation results
        """
        try:
            results = {
                "reconciled_bots": [],
                "errors": [],
                "summary": {
                    "total_bots": 0,
                    "successful_reconciliations": 0,
                    "failed_reconciliations": 0,
                    "total_adjustments_usd": 0.0
                }
            }
            
            # Get all bots
            bots = self.db.query(Bot).all()
            results["summary"]["total_bots"] = len(bots)
            
            # Get current account balances
            accounts = self.coinbase_service.get_accounts()
            account_balances = {}
            for account in accounts:
                currency = account.get('currency', '')
                total_balance = account.get('available_balance', 0) + account.get('hold', 0)
                account_balances[currency] = total_balance
                
            logger.info(f"Current Coinbase balances: {account_balances}")
            
            # Reconcile each bot
            for bot in bots:
                try:
                    reconcile_result = self._reconcile_single_bot(bot, account_balances)
                    results["reconciled_bots"].append(reconcile_result)
                    
                    if reconcile_result["success"]:
                        results["summary"]["successful_reconciliations"] += 1
                        results["summary"]["total_adjustments_usd"] += abs(reconcile_result["adjustment_usd"])
                    else:
                        results["summary"]["failed_reconciliations"] += 1
                        results["errors"].append(f"Bot {bot.id}: {reconcile_result['error']}")
                        
                except Exception as e:
                    error_msg = f"Failed to reconcile bot {bot.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    results["summary"]["failed_reconciliations"] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to reconcile bot positions: {e}")
            return {"error": str(e)}
    
    def _reconcile_single_bot(self, bot: Bot, account_balances: Dict[str, float]) -> Dict[str, any]:
        """
        Reconcile a single bot's position with actual Coinbase holdings.
        
        Args:
            bot: Bot to reconcile
            account_balances: Current Coinbase account balances
            
        Returns:
            Reconciliation result for the bot
        """
        try:
            # Extract base currency from trading pair (e.g., BTC from BTC-USD)
            base_currency = bot.pair.split('-')[0]
            
            # Get current market price for the currency
            ticker = self.coinbase_service.get_product_ticker(bot.pair)
            current_price = float(ticker.get('price', 0)) if ticker else 0
            
            # Get actual holdings for this currency
            actual_holdings = account_balances.get(base_currency, 0.0)
            actual_position_usd = actual_holdings * current_price
            
            # Get bot's tracked position
            tracked_position_usd = bot.current_position_size
            
            # Calculate difference
            adjustment_usd = actual_position_usd - tracked_position_usd
            
            result = {
                "bot_id": bot.id,
                "bot_name": bot.name,
                "pair": bot.pair,
                "base_currency": base_currency,
                "current_price": current_price,
                "actual_holdings": actual_holdings,
                "actual_position_usd": round(actual_position_usd, 2),
                "tracked_position_usd": round(tracked_position_usd, 2),
                "adjustment_usd": round(adjustment_usd, 2),
                "success": True,
                "updated": False
            }
            
            # If there's a significant difference (>$1), update the bot position
            if abs(adjustment_usd) > 1.0:
                logger.info(f"Updating bot {bot.id} position from ${tracked_position_usd:.2f} to ${actual_position_usd:.2f}")
                
                # Update the bot's position size
                bot.current_position_size = actual_position_usd
                self.db.commit()
                
                result["updated"] = True
                result["message"] = f"Updated position from ${tracked_position_usd:.2f} to ${actual_position_usd:.2f}"
            else:
                result["message"] = f"Position is accurate (difference: ${adjustment_usd:.2f})"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to reconcile bot {bot.id}: {e}")
            return {
                "bot_id": bot.id,
                "bot_name": bot.name,
                "success": False,
                "error": str(e)
            }
    
    def get_position_discrepancies(self) -> List[Dict[str, any]]:
        """
        Get position discrepancies without updating them.
        
        Returns:
            List of position discrepancies for review
        """
        try:
            discrepancies = []
            
            # Get all bots
            bots = self.db.query(Bot).all()
            
            # Get current account balances
            accounts = self.coinbase_service.get_accounts()
            account_balances = {}
            for account in accounts:
                currency = account.get('currency', '')
                total_balance = account.get('available_balance', 0) + account.get('hold', 0)
                account_balances[currency] = total_balance
            
            # Check each bot for discrepancies
            for bot in bots:
                try:
                    base_currency = bot.pair.split('-')[0]
                    ticker = self.coinbase_service.get_product_ticker(bot.pair)
                    current_price = float(ticker.get('price', 0)) if ticker else 0
                    
                    actual_holdings = account_balances.get(base_currency, 0.0)
                    actual_position_usd = actual_holdings * current_price
                    tracked_position_usd = bot.current_position_size
                    
                    difference = actual_position_usd - tracked_position_usd
                    
                    # Only report significant discrepancies (>$1)
                    if abs(difference) > 1.0:
                        discrepancies.append({
                            "bot_id": bot.id,
                            "bot_name": bot.name,
                            "pair": bot.pair,
                            "base_currency": base_currency,
                            "current_price": current_price,
                            "actual_holdings": actual_holdings,
                            "actual_position_usd": round(actual_position_usd, 2),
                            "tracked_position_usd": round(tracked_position_usd, 2),
                            "difference_usd": round(difference, 2),
                            "percentage_diff": round((difference / max(tracked_position_usd, 1)) * 100, 1)
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to check discrepancy for bot {bot.id}: {e}")
                    discrepancies.append({
                        "bot_id": bot.id,
                        "bot_name": bot.name,
                        "error": str(e)
                    })
            
            return discrepancies
            
        except Exception as e:
            logger.error(f"Failed to get position discrepancies: {e}")
            return [{"error": str(e)}]
    
    def calculate_position_from_trades(self, bot_id: int) -> Dict[str, any]:
        """
        Calculate position based on recorded trades (alternative method).
        
        Args:
            bot_id: Bot ID to calculate position for
            
        Returns:
            Position calculated from trade history
        """
        try:
            bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
            if not bot:
                return {"error": "Bot not found"}
            
            # Get all trades for this bot, ordered by execution time
            trades = self.db.query(Trade).filter(
                Trade.bot_id == bot_id,
                Trade.status == "filled"
            ).order_by(Trade.executed_at).all()
            
            total_position_usd = 0.0
            total_crypto_amount = 0.0
            trade_count = 0
            
            for trade in trades:
                if trade.side.lower() == "buy":
                    total_position_usd += trade.size_usd or 0.0
                    total_crypto_amount += trade.filled_size or 0.0
                else:  # sell
                    total_position_usd -= trade.size_usd or 0.0
                    total_crypto_amount -= trade.filled_size or 0.0
                
                trade_count += 1
            
            # Get current price for validation
            ticker = self.coinbase_service.get_product_ticker(bot.pair)
            current_price = float(ticker.get('price', 0)) if ticker else 0
            current_value_usd = total_crypto_amount * current_price
            
            return {
                "bot_id": bot_id,
                "bot_name": bot.name,
                "pair": bot.pair,
                "trade_count": trade_count,
                "calculated_position_usd": round(total_position_usd, 2),
                "calculated_crypto_amount": round(total_crypto_amount, 8),
                "current_price": current_price,
                "current_value_usd": round(current_value_usd, 2),
                "tracked_position_usd": round(bot.current_position_size, 2),
                "last_trade": trades[-1].executed_at.isoformat() if trades else None
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate position from trades for bot {bot_id}: {e}")
            return {"error": str(e)}
