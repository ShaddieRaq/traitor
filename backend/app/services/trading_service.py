"""
Trading Service - Phase 4.1.2
Real trade execution with comprehensive safety integration.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json
from sqlalchemy.orm import Session

from ..models.models import Bot, Trade
from ..services.coinbase_service import CoinbaseService
from ..services.trading_safety import TradingSafetyService
from ..services.bot_evaluator import BotSignalEvaluator

logger = logging.getLogger(__name__)


class TradeExecutionError(Exception):
    """Custom exception for trade execution errors."""
    pass


class TradingService:
    """
    Core trading service that orchestrates safe trade execution.
    Integrates safety validation, order placement, and trade recording.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.coinbase_service = CoinbaseService()
        self.safety_service = TradingSafetyService(db)
        self.bot_evaluator = BotSignalEvaluator(db)
    
    def execute_trade(self, bot_id: int, side: str, size_usd: float, 
                     current_temperature: str = None) -> Dict[str, Any]:
        """
        Execute a trade with full safety validation and error handling.
        
        Args:
            bot_id: ID of the bot requesting the trade
            side: "buy" or "sell"
            size_usd: Trade size in USD
            current_temperature: Bot's current temperature (optional, will fetch if not provided)
            
        Returns:
            Dict with trade execution result including order details and safety status
            
        Raises:
            TradeExecutionError: If trade fails safety validation or execution
        """
        logger.info(f"🚀 Starting trade execution: Bot {bot_id} - {side} ${size_usd}")
        
        try:
            # 1. Get bot information
            bot = self._get_bot(bot_id)
            
            # 2. Get current temperature if not provided
            if current_temperature is None:
                current_temperature = self._get_bot_temperature(bot)
            
            # 3. Safety validation - CRITICAL CHECKPOINT
            safety_result = self._validate_trade_safety(bot, side, size_usd, current_temperature)
            if not safety_result["allowed"]:
                raise TradeExecutionError(f"Trade rejected by safety system: {safety_result['reason']}")
            
            # 4. Get current market price for calculations
            market_price = self._get_current_price(bot.pair)
            
            # 5. Calculate position size in base currency
            base_size = self._calculate_base_size(side, size_usd, market_price)
            
            # 6. Execute the order on Coinbase
            order_result = self._place_order(bot.pair, side, base_size)
            if not order_result:
                raise TradeExecutionError("Failed to place order on Coinbase")
            
            # 7. Record trade in database
            trade_record = self._record_trade(bot, side, size_usd, market_price, order_result, current_temperature)
            
            # 8. Update bot position (if this was a successful order)
            self._update_bot_position(bot, side, size_usd)
            
            success_result = {
                "success": True,
                "trade_id": trade_record.id,
                "order_id": order_result["order_id"],
                "bot": {
                    "id": bot.id,
                    "name": bot.name,
                    "pair": bot.pair
                },
                "execution": {
                    "side": side,
                    "size_usd": size_usd,
                    "base_size": base_size,
                    "price": market_price,
                    "temperature": current_temperature
                },
                "safety_validation": safety_result,
                "order_details": order_result,
                "executed_at": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(f"✅ Trade executed successfully: {order_result['order_id']}")
            return success_result
            
        except TradeExecutionError as e:
            logger.error(f"❌ Trade execution failed: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "error_type": "trade_execution_error",
                "bot_id": bot_id,
                "request": {
                    "side": side,
                    "size_usd": size_usd,
                    "temperature": current_temperature
                },
                "failed_at": datetime.utcnow().isoformat() + "Z"
            }
            return error_result
            
        except Exception as e:
            logger.error(f"💥 Unexpected error during trade execution: {e}")
            error_result = {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "system_error",
                "bot_id": bot_id,
                "request": {
                    "side": side,
                    "size_usd": size_usd,
                    "temperature": current_temperature
                },
                "failed_at": datetime.utcnow().isoformat() + "Z"
            }
            return error_result
    
    def _get_bot(self, bot_id: int) -> Bot:
        """Get bot from database with validation."""
        bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise TradeExecutionError(f"Bot {bot_id} not found")
        
        if bot.status != "RUNNING":
            raise TradeExecutionError(f"Bot {bot.name} is not running (status: {bot.status})")
        
        return bot
    
    def _get_bot_temperature(self, bot: Bot) -> str:
        """Get current bot temperature from evaluator."""
        try:
            # For Phase 4.1.2, we'll use a simplified temperature check
            # Full market data evaluation will be enhanced in Phase 4.2
            from ..utils.temperature import calculate_bot_temperature
            return calculate_bot_temperature(bot.current_combined_score)
        except Exception as e:
            logger.warning(f"Could not get bot temperature: {e}, defaulting to COOL")
            return "COOL"  # Conservative default
    
    def _validate_trade_safety(self, bot: Bot, side: str, size_usd: float, 
                             current_temperature: str) -> Dict[str, Any]:
        """Validate trade against all safety limits."""
        return self.safety_service.validate_trade_request(
            bot=bot,
            side=side,
            size_usd=size_usd,
            current_temperature=current_temperature
        )
    
    def _get_current_price(self, product_id: str) -> float:
        """Get current market price for the trading pair."""
        try:
            ticker = self.coinbase_service.get_product_ticker(product_id)
            if ticker and 'price' in ticker:
                return float(ticker['price'])
            else:
                raise TradeExecutionError(f"Could not get current price for {product_id}")
        except Exception as e:
            raise TradeExecutionError(f"Failed to fetch market price: {e}")
    
    def _calculate_base_size(self, side: str, size_usd: float, market_price: float) -> float:
        """Calculate the base currency size for the order."""
        if side.lower() == "buy":
            # For buy orders, we're spending USD to get base currency
            base_size = size_usd / market_price
        else:
            # For sell orders, we need to specify how much base currency to sell
            # This is simplified - in production, we'd check current holdings
            base_size = size_usd / market_price
        
        return round(base_size, 8)  # Round to 8 decimal places for crypto precision
    
    def _place_order(self, product_id: str, side: str, base_size: float) -> Optional[Dict[str, Any]]:
        """Place the actual order on Coinbase."""
        try:
            order_result = self.coinbase_service.place_market_order(
                product_id=product_id,
                side=side,
                size=base_size
            )
            
            if not order_result:
                raise TradeExecutionError("Coinbase order placement returned None")
            
            logger.info(f"📋 Order placed: {order_result.get('order_id')} - {side} {base_size} {product_id}")
            return order_result
            
        except Exception as e:
            raise TradeExecutionError(f"Order placement failed: {e}")
    
    def _record_trade(self, bot: Bot, side: str, size_usd: float, price: float, 
                     order_result: Dict[str, Any], current_temperature: str) -> Trade:
        """Record the trade in the database."""
        try:
            # Get current signal scores for recording
            signal_scores = self._get_current_signal_scores(bot)
            
            trade = Trade(
                bot_id=bot.id,
                product_id=bot.pair,
                side=side,
                size=size_usd,  # Store USD size for simplicity in Phase 4.1.2
                price=price,
                order_id=order_result["order_id"],
                status=order_result.get("status", "pending"),
                combined_signal_score=bot.current_combined_score,
                signal_scores=json.dumps(signal_scores),
                created_at=datetime.utcnow()
            )
            
            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)
            
            logger.info(f"💾 Trade recorded: ID {trade.id}")
            return trade
            
        except Exception as e:
            self.db.rollback()
            raise TradeExecutionError(f"Failed to record trade: {e}")
    
    def _get_current_signal_scores(self, bot: Bot) -> Dict[str, Any]:
        """Get current individual signal scores for recording."""
        try:
            # Parse signal configuration
            signal_config = json.loads(bot.signal_config)
            
            # For Phase 4.1.2, we'll store the configuration and combined score
            # Phase 4.2 will enhance this with real-time signal evaluation
            return {
                "rsi_enabled": signal_config.get("RSI", {}).get("enabled", False),
                "ma_enabled": signal_config.get("MA", {}).get("enabled", False),
                "macd_enabled": signal_config.get("MACD", {}).get("enabled", False),
                "combined_score": bot.current_combined_score,
                "recorded_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.warning(f"Could not parse signal scores: {e}")
            return {"error": str(e), "combined_score": bot.current_combined_score}
    
    def _update_bot_position(self, bot: Bot, side: str, size_usd: float) -> None:
        """Update bot's current position size."""
        try:
            if side.lower() == "buy":
                # Increase position (buying adds to position)
                bot.current_position_size += size_usd
            else:
                # Decrease position (selling reduces position)
                bot.current_position_size -= size_usd
            
            # Ensure position doesn't go negative (safety check)
            if bot.current_position_size < 0:
                logger.warning(f"Bot {bot.id} position would go negative, setting to 0")
                bot.current_position_size = 0.0
            
            self.db.commit()
            logger.info(f"📊 Bot {bot.id} position updated: ${bot.current_position_size:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to update bot position: {e}")
            # Don't raise exception here - trade was successful, position update is secondary
    
    def get_trade_status(self, trade_id: int) -> Dict[str, Any]:
        """Get current status of a trade."""
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            return {"error": "Trade not found", "trade_id": trade_id}
        
        return {
            "trade_id": trade.id,
            "bot_id": trade.bot_id,
            "order_id": trade.order_id,
            "product_id": trade.product_id,
            "side": trade.side,
            "size": trade.size,
            "price": trade.price,
            "status": trade.status,
            "created_at": trade.created_at.isoformat() if trade.created_at else None,
            "filled_at": trade.filled_at.isoformat() if trade.filled_at else None,
            "combined_signal_score": trade.combined_signal_score
        }
