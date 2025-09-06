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
from ..services.position_service import PositionService
from ..core.config import settings

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
        self.position_service = PositionService(db)  # Phase 4.1.3: Enhanced position management
    
    def execute_trade(self, bot_id: int, side: str, size_usd: float = None, 
                     current_temperature: str = None, auto_size: bool = True) -> Dict[str, Any]:
        """
        PHASE 4.1.3 DAY 3: INTELLIGENT TRADE EXECUTION
        Execute a trade with smart sizing, advanced algorithms, and comprehensive validation.
        
        Args:
            bot_id: Database ID of the bot executing the trade
            side: "BUY" or "SELL"
            size_usd: Size of trade in USD (optional if auto_size=True)
            current_temperature: Optional bot temperature override
            auto_size: Use intelligent sizing algorithms (default: True)
        
        Returns:
            Dict with trade execution result including order details and advanced analytics
            
        Raises:
            TradeExecutionError: If trade fails safety validation or execution
        """
        logger.info(f"🚀 INTELLIGENT TRADE EXECUTION: Bot {bot_id} - {side} (auto_size: {auto_size})")
        
        try:
            # 1. Get bot information
            bot = self._get_bot(bot_id)
            
            # 2. Get current temperature if not provided
            if current_temperature is None:
                current_temperature = self._get_bot_temperature(bot)
            
            # 3. PHASE 4.1.3: INTELLIGENT TRADE SIZING 🧠
            if auto_size or size_usd is None:
                smart_sizing = self._calculate_intelligent_trade_size(bot, side, current_temperature, size_usd)
                size_usd = smart_sizing["recommended_size"]
                logger.info(f"🎯 Smart sizing: ${size_usd:.2f} (reasoning: {smart_sizing['reasoning']})")
            
            # 4. Enhanced safety validation with intelligent context
            safety_result = self._validate_trade_safety(bot, side, size_usd, current_temperature)
            if not safety_result["allowed"]:
                raise TradeExecutionError(f"Trade rejected by safety system: {safety_result['reason']}")
            
            # 5. Get current market price for calculations
            market_price = self._get_current_price(bot.pair)
            
            # 6. Validate account balance before proceeding
            balance_validation = self._validate_account_balance(bot.pair, side, size_usd, market_price)
            if not balance_validation["valid"]:
                raise TradeExecutionError(f"Insufficient balance: {balance_validation['message']}")
            
            # 7. Calculate position size in base currency
            base_size = self._calculate_base_size(side, size_usd, market_price)
            
            # 8. PHASE 4.1.3: PRE-EXECUTION ANALYTICS 📊
            pre_execution_analytics = self._generate_pre_execution_analytics(bot, side, size_usd, market_price, current_temperature)
            
            # 9. Execute the order on Coinbase with real-time updates
            self._emit_trade_update({
                "stage": "trade_starting",
                "bot_id": bot_id,
                "bot_name": bot.name,
                "side": side,
                "size_usd": size_usd,
                "status": "starting",
                "message": f"Starting {side} trade for ${size_usd:.2f}..."
            })
            
            order_result = self._place_order(bot.pair, side, base_size, bot_id)
            if not order_result:
                raise TradeExecutionError("Failed to place order on Coinbase")
            
            # 10. Record trade with enhanced analytics
            self._emit_trade_update({
                "stage": "recording_trade",
                "bot_id": bot_id,
                "order_id": order_result.get('order_id'),
                "status": "recording",
                "message": "Recording trade in database..."
            })
            
            trade_record = self._record_trade(bot, side, size_usd, market_price, order_result, current_temperature)
            
            # 11. Update bot position (if this was a successful order)
            self._update_bot_position(bot, side, size_usd)
            
            # 12. PHASE 4.1.3: POST-EXECUTION ANALYTICS & POSITION SUMMARY 🎯
            position_summary = self.position_service.get_position_summary(bot.id)
            post_execution_analytics = self._generate_post_execution_analytics(bot, trade_record, position_summary)
            
            # Phase 2: Emit successful completion
            self._emit_trade_update({
                "stage": "trade_completed",
                "bot_id": bot_id,
                "trade_id": trade_record.id,
                "order_id": order_result.get('order_id'),
                "status": "completed",
                "message": f"✅ Trade completed successfully! {side} ${size_usd:.2f}",
                "execution_details": {
                    "side": side,
                    "amount": size_usd,
                    "price": market_price,
                    "order_id": order_result.get('order_id')
                }
            })
            
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
                    "temperature": current_temperature,
                    "tranche_number": trade_record.tranche_number,
                    "auto_sized": auto_size
                },
                "position": position_summary,
                "analytics": {
                    "pre_execution": pre_execution_analytics,
                    "post_execution": post_execution_analytics,
                    "intelligent_sizing": smart_sizing if auto_size else None
                },
                "safety_validation": safety_result,
                "order_details": order_result,
                "executed_at": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(f"✅ INTELLIGENT TRADE COMPLETED: {order_result['order_id']} (Tranche #{trade_record.tranche_number})")
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
                    "temperature": current_temperature,
                    "auto_size": auto_size
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
                    "temperature": current_temperature,
                    "auto_size": auto_size
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
        """Get current bot temperature from evaluator using fresh market data."""
        logger.info(f"🔍 Getting temperature for bot {bot.id} ({bot.name})")
        try:
            # Use fresh market data evaluation like status API does
            logger.info(f"🔍 Fetching market data for {bot.pair}")
            market_data = self.coinbase_service.get_historical_data(bot.pair)
            logger.info(f"🔍 Market data fetched, calculating temperature...")
            temp_data = self.bot_evaluator.calculate_bot_temperature(bot, market_data)
            temperature = temp_data.get('temperature', 'FROZEN')
            score = temp_data.get('score', 0.0)
            logger.info(f"🌡️ Temperature calculation for bot {bot.id}: score={score:.3f}, temp={temperature}")
            return temperature
        except Exception as e:
            logger.error(f"❌ Exception in _get_bot_temperature for bot {bot.id}: {e}", exc_info=True)
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
    
    def _validate_account_balance(self, product_id: str, side: str, size_usd: float, 
                                current_price: float) -> Dict[str, Any]:
        """Validate that account has sufficient balance for the trade."""
        try:
            balance_result = self.coinbase_service.validate_trade_balance(
                product_id=product_id,
                side=side,
                size_usd=size_usd,
                current_price=current_price
            )
            
            if balance_result["valid"]:
                logger.info(f"✅ Balance validation passed: {balance_result['message']}")
            else:
                logger.warning(f"❌ Balance validation failed: {balance_result['message']}")
            
            return balance_result
            
        except Exception as e:
            logger.error(f"Error validating account balance: {e}")
            return {
                "valid": False,
                "message": f"Balance validation error: {str(e)}",
                "available": 0.0,
                "required": 0.0,
                "currency": "UNKNOWN"
            }
    
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
    
    def _emit_trade_update(self, update_data: dict):
        """Emit real-time trade execution updates via WebSocket (Phase 2)."""
        try:
            # Import here to avoid circular imports
            from ..api.websocket import manager
            import asyncio
            
            # Emit update in background (non-blocking)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(manager.broadcast_trade_update(update_data))
            loop.close()
        except Exception as e:
            logger.warning(f"Failed to emit trade update: {e}")
            # Don't fail the trade if WebSocket emission fails
    
    def _place_order(self, product_id: str, side: str, base_size: float, bot_id: int = None) -> Optional[Dict[str, Any]]:
        """Place the actual order on Coinbase with real-time WebSocket updates."""
        try:
            # Phase 2: Emit trade execution start
            if bot_id:
                self._emit_trade_update({
                    "stage": "order_placing",
                    "bot_id": bot_id,
                    "product_id": product_id,
                    "side": side,
                    "size": base_size,
                    "status": "placing_order",
                    "message": f"Placing {side} order for {base_size} {product_id}..."
                })
            
            order_result = self.coinbase_service.place_market_order(
                product_id=product_id,
                side=side,
                size=base_size
            )
            
            if not order_result:
                if bot_id:
                    self._emit_trade_update({
                        "stage": "order_failed",
                        "bot_id": bot_id,
                        "status": "failed",
                        "message": "Order placement returned no result"
                    })
                raise TradeExecutionError("Coinbase order placement returned None")
            
            # Phase 2: Emit successful order placement
            if bot_id:
                self._emit_trade_update({
                    "stage": "order_placed",
                    "bot_id": bot_id,
                    "order_id": order_result.get('order_id'),
                    "status": "order_placed",
                    "message": f"Order placed successfully: {order_result.get('order_id')}"
                })
            
            logger.info(f"📋 Order placed: {order_result.get('order_id')} - {side} {base_size} {product_id}")
            return order_result
            
        except Exception as e:
            # Phase 2: Emit error update
            if bot_id:
                self._emit_trade_update({
                    "stage": "order_failed",
                    "bot_id": bot_id,
                    "status": "failed",
                    "error": str(e),
                    "message": f"Order placement failed: {e}"
                })
            raise TradeExecutionError(f"Order placement failed: {e}")
    
    def _record_trade(self, bot: Bot, side: str, size_usd: float, price: float, 
                     order_result: Dict[str, Any], current_temperature: str) -> Trade:
        """Record the trade in the database with enhanced position management."""
        try:
            # Get current signal scores for recording
            signal_scores = self._get_current_signal_scores(bot)
            
            # Phase 4.1.3: Calculate tranche information
            tranche_number = self.position_service.calculate_next_tranche_number(bot.id)
            average_entry_price = self.position_service.calculate_average_entry_price(bot.id)
            position_tranches_json = self.position_service.create_position_tranches_json(bot.id)
            
            trade = Trade(
                bot_id=bot.id,
                product_id=bot.pair,
                side=side,
                size=size_usd,  # Store USD size for simplicity in Phase 4.1.2
                price=price,
                order_id=order_result["order_id"],
                status=order_result.get("status", "pending"),  # Start as pending
                combined_signal_score=bot.current_combined_score,
                signal_scores=json.dumps(signal_scores),
                # Phase 4.1.3: Enhanced position fields
                size_usd=size_usd,
                tranche_number=tranche_number,
                average_entry_price=average_entry_price,
                position_tranches=position_tranches_json,
                position_status="BUILDING",  # Will be updated by position service

                created_at=datetime.utcnow(),
                # filled_at will be set when order actually fills (not immediately)
                filled_at=None
            )
            
            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)
            
            # Phase 4.1.3: Update position status based on new trade
            self.position_service.update_position_status(bot.id, trade)
            
            logger.info(f"💾 Trade recorded with tranche support: ID {trade.id}, Tranche #{tranche_number}")
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

    def update_pending_trade_statuses(self) -> Dict[str, Any]:
        """
        Update the status of all pending trades by checking with Coinbase.
        This should be called periodically to keep trade statuses current.
        """
        try:
            # Get all pending trades
            pending_trades = self.db.query(Trade).filter(
                Trade.status.in_(["pending", "open", "active"])
            ).all()
            
            updated_count = 0
            completed_count = 0
            
            logger.info(f"🔄 Checking status of {len(pending_trades)} pending trades")
            
            for trade in pending_trades:
                if not trade.order_id:
                    # No order ID means trade failed to place - mark as failed
                    trade.status = "failed"
                    trade.filled_at = datetime.utcnow()
                    updated_count += 1
                    continue
                    
                # Check order status with Coinbase
                order_status = self.coinbase_service.get_order_status(trade.order_id)
                
                if order_status:
                    old_status = trade.status
                    new_status = order_status.get("status", "pending")
                    
                    # Map Coinbase statuses to our statuses
                    if new_status.lower() in ["filled", "done", "settled"]:
                        trade.status = "completed"
                        # CRITICAL: Only set filled_at when order actually fills
                        if not trade.filled_at:  # Don't overwrite if already set
                            trade.filled_at = datetime.utcnow()
                        completed_count += 1
                    elif new_status.lower() in ["cancelled", "rejected"]:
                        trade.status = "failed"
                        # Don't set filled_at for failed orders - they weren't filled
                        trade.filled_at = None
                    elif new_status.lower() in ["open", "active", "pending"]:
                        trade.status = "pending"
                        # Keep filled_at as None for pending orders
                        trade.filled_at = None
                    else:
                        trade.status = new_status.lower()
                    
                    if old_status != trade.status:
                        updated_count += 1
                        logger.info(f"📊 Trade {trade.id} status: {old_status} → {trade.status}")
            
            # Commit all updates
            self.db.commit()
            
            result = {
                "total_checked": len(pending_trades),
                "updated_count": updated_count,
                "completed_count": completed_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if updated_count > 0:
                logger.info(f"✅ Updated {updated_count} trade statuses, {completed_count} completed")
            
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating trade statuses: {e}")
            return {"error": str(e), "total_checked": 0, "updated_count": 0}

    # =================================================================================
    # PHASE 4.1.3 DAY 3: INTELLIGENT TRADING ALGORITHMS 🧠
    # =================================================================================
    
    def _calculate_intelligent_trade_size(self, bot: Bot, side: str, current_temperature: str, 
                                        manual_size: float = None) -> Dict[str, Any]:
        """
        Calculate intelligent trade size using advanced algorithms from Day 2.
        Combines temperature-based scaling, optimal tranche sizing, and signal strength.
        """
        try:
            # Get current position summary
            position_summary = self.position_service.get_position_summary(bot.id)
            
            # Base size from position service (optimal tranche sizing)
            # Get current market price for calculation - FIXED: Use real market price
            current_price = self._get_current_price(bot.pair)
            optimal_tranche_result = self.position_service.calculate_optimal_tranche_size(
                bot.id, 
                current_price
            )
            # Extract the size from the tuple return (size, reasoning)
            if isinstance(optimal_tranche_result, tuple):
                base_size = optimal_tranche_result[0]
                tranche_reasoning = optimal_tranche_result[1]
            else:
                # Fallback in case it's not a tuple
                base_size = float(optimal_tranche_result)
                tranche_reasoning = "Standard calculation"
            
            # Temperature-based position scaling multiplier
            temp_multipliers = {
                "HOT": 1.8,      # Aggressive sizing on strong signals
                "WARM": 1.3,     # Moderate increase
                "COOL": 1.0,     # Standard sizing
                "FROZEN": 0.5    # Conservative sizing
            }
            temp_multiplier = temp_multipliers.get(current_temperature, 1.0)
            
            # Signal strength adaptive scaling (stronger signals = larger positions)
            signal_strength = abs(bot.current_combined_score)
            signal_multiplier = 0.8 + (signal_strength * 0.4)  # Range: 0.8 to 1.2
            
            # Position building progression (larger positions as we build confidence)
            tranche_count = position_summary.get("total_tranches", 0)
            if tranche_count == 0:
                progression_multiplier = 0.7  # Start smaller
            elif tranche_count <= 2:
                progression_multiplier = 1.0  # Standard
            else:
                progression_multiplier = 1.2  # Larger as position develops
            
            # Calculate final intelligent size
            intelligent_size = base_size * temp_multiplier * signal_multiplier * progression_multiplier
            
            # Respect manual override if provided
            if manual_size is not None:
                # Use manual size but apply safety cap
                intelligent_size = min(manual_size, intelligent_size * 1.5)
                reasoning = f"Manual override ${manual_size:.2f}, capped by intelligent limit"
            else:
                reasoning = f"Temp:{current_temperature}({temp_multiplier:.1f}x) × Signal:{signal_strength:.2f}({signal_multiplier:.1f}x) × Progress:{tranche_count}tx({progression_multiplier:.1f}x)"
            
            # Final safety bounds (Phase 4.1.2 limits)
            intelligent_size = max(10.0, min(intelligent_size, 100.0))
            
            return {
                "recommended_size": round(intelligent_size, 2),
                "base_calculation": base_size,
                "multipliers": {
                    "temperature": temp_multiplier,
                    "signal_strength": signal_multiplier, 
                    "progression": progression_multiplier
                },
                "reasoning": reasoning,
                "tranche_info": {"base_size": base_size, "method": "optimal_tranche"}
            }
            
        except Exception as e:
            logger.warning(f"Intelligent sizing failed, using fallback: {e}")
            fallback_size = manual_size if manual_size else 25.0
            return {
                "recommended_size": fallback_size,
                "base_calculation": fallback_size,
                "multipliers": {"fallback": 1.0},
                "reasoning": f"Fallback due to error: {str(e)}",
                "error": str(e)
            }
    
    def _generate_pre_execution_analytics(self, bot: Bot, side: str, size_usd: float, 
                                        market_price: float, current_temperature: str) -> Dict[str, Any]:
        """Generate comprehensive analytics before trade execution."""
        try:
            position_summary = self.position_service.get_position_summary(bot.id)
            
            # Analyze DCA impact for this trade
            dca_analysis = self.position_service.calculate_dollar_cost_average_metrics(
                bot.id, 
                market_price,
                size_usd
            )
            
            # Calculate position health metrics
            current_exposure = position_summary.get("total_invested", 0.0)
            new_exposure = current_exposure + size_usd if side.lower() == "buy" else current_exposure - size_usd
            exposure_ratio = new_exposure / 1000.0  # Assuming $1000 max exposure for demo
            
            return {
                "market_conditions": {
                    "current_price": market_price,
                    "bot_temperature": current_temperature,
                    "signal_strength": abs(bot.current_combined_score),
                    "signal_direction": "bullish" if bot.current_combined_score > 0 else "bearish"
                },
                "position_impact": {
                    "current_exposure": current_exposure,
                    "new_exposure": new_exposure,
                    "exposure_ratio": round(exposure_ratio, 3),
                    "tranche_number": position_summary.get("total_tranches", 0) + 1
                },
                "dca_analysis": dca_analysis,
                "risk_assessment": {
                    "risk_level": "HIGH" if exposure_ratio > 0.8 else "MEDIUM" if exposure_ratio > 0.5 else "LOW",
                    "temperature_risk": "HIGH" if current_temperature in ["HOT", "FROZEN"] else "NORMAL"
                }
            }
            
        except Exception as e:
            logger.warning(f"Pre-execution analytics failed: {e}")
            return {"error": str(e), "status": "analytics_unavailable"}
    
    def _generate_post_execution_analytics(self, bot: Bot, trade_record: Trade, 
                                         position_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analytics after trade execution."""
        try:
            # Analyze position performance
            performance_analysis = self.position_service.analyze_position_performance(bot.id)
            
            # Calculate updated DCA metrics
            dca_metrics = self.position_service.calculate_dollar_cost_average_metrics(bot.id)
            
            # Position scaling optimization insights
            scaling_analysis = self.position_service.optimize_position_scaling(
                bot.id,
                signal_strength=abs(bot.current_combined_score)
            )
            
            return {
                "trade_execution": {
                    "trade_id": trade_record.id,
                    "tranche_number": trade_record.tranche_number,
                    "execution_price": trade_record.price,
                    "size_usd": trade_record.size_usd
                },
                "position_summary": position_summary,
                "performance_analysis": performance_analysis,
                "dca_metrics": dca_metrics,
                "scaling_optimization": scaling_analysis,
                "next_action_recommendations": self._generate_action_recommendations(bot, performance_analysis, scaling_analysis)
            }
            
        except Exception as e:
            logger.warning(f"Post-execution analytics failed: {e}")
            return {"error": str(e), "status": "analytics_unavailable"}
    
    def _generate_action_recommendations(self, bot: Bot, performance_analysis: Dict[str, Any], 
                                       scaling_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent recommendations for next actions."""
        try:
            recommendations = []
            priority = "NORMAL"
            
            # Check performance grade
            performance_grade = performance_analysis.get("performance_grade", "C")
            if performance_grade in ["A", "A+"]:
                recommendations.append("Position performing excellently - consider scaling up on next signal")
                priority = "POSITIVE"
            elif performance_grade in ["D", "F"]:
                recommendations.append("Position underperforming - consider partial exit strategy")
                priority = "CAUTION"
            
            # Check optimal scaling recommendation
            scaling_recommendation = scaling_analysis.get("recommendation")
            if scaling_recommendation == "INCREASE":
                recommendations.append("Market conditions favor position increase")
            elif scaling_recommendation == "DECREASE":
                recommendations.append("Consider reducing position size on next trade")
            elif scaling_recommendation == "HOLD":
                recommendations.append("Current position size appears optimal")
            
            # Temperature-based recommendations
            current_temp = self._get_bot_temperature(bot)
            if current_temp == "HOT":
                recommendations.append("Strong signals detected - good time for position building")
            elif current_temp == "FROZEN":
                recommendations.append("Weak signals - consider waiting for better entry")
            
            return {
                "priority": priority,
                "recommendations": recommendations,
                "next_optimal_size": scaling_analysis.get("next_optimal_size", 25.0),
                "confidence_level": performance_analysis.get("confidence_score", 0.5)
            }
            
        except Exception as e:
            return {"error": str(e), "recommendations": ["Unable to generate recommendations"]}

    # =================================================================================
    # END PHASE 4.1.3 DAY 3 INTELLIGENT ALGORITHMS
    # =================================================================================
    
    def execute_automated_position_building(self, bot_id: int, strategy: str = "ADAPTIVE") -> Dict[str, Any]:
        """
        PHASE 4.1.3 DAY 3: AUTOMATED POSITION BUILDING 🤖
        Automatically execute intelligent position building based on current conditions.
        """
        logger.info(f"🤖 AUTOMATED POSITION BUILDING: Bot {bot_id} - Strategy: {strategy}")
        
        try:
            # 1. Get bot and validate it's ready for automation
            bot = self._get_bot(bot_id)
            current_temperature = self._get_bot_temperature(bot)
            
            # 2. Analyze current position and market conditions
            position_summary = self.position_service.get_position_summary(bot.id)
            automation_analysis = self._analyze_automation_readiness(bot, position_summary, current_temperature)
            
            if not automation_analysis["ready"]:
                return {
                    "success": False,
                    "reason": automation_analysis["reason"],
                    "analysis": automation_analysis,
                    "bot_id": bot_id
                }
            
            # 3. Determine optimal trade based on strategy and conditions
            trade_decision = self._calculate_automated_trade_decision(bot, position_summary, strategy, current_temperature)
            
            if trade_decision["action"] == "HOLD":
                return {
                    "success": True,
                    "action": "HOLD",
                    "reason": trade_decision["reasoning"],
                    "analysis": automation_analysis,
                    "next_check_in": "300s"  # Check again in 5 minutes
                }
            
            # 4. Execute the automated trade
            automated_trade_result = self.execute_trade(
                bot_id=bot_id,
                side=trade_decision["side"],
                size_usd=None,  # Let intelligent sizing handle it
                current_temperature=current_temperature,
                auto_size=True
            )
            
            # 5. Enhanced automation results
            return {
                "success": True,
                "action": "TRADE_EXECUTED",
                "automation_strategy": strategy,
                "trade_result": automated_trade_result,
                "decision_analysis": trade_decision,
                "readiness_analysis": automation_analysis,
                "executed_at": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"❌ Automated position building failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "bot_id": bot_id,
                "strategy": strategy,
                "failed_at": datetime.utcnow().isoformat() + "Z"
            }
    
    def _analyze_automation_readiness(self, bot: Bot, position_summary: Dict[str, Any], 
                                    current_temperature: str) -> Dict[str, Any]:
        """Analyze if bot is ready for automated position building."""
        try:
            readiness_checks = []
            overall_ready = True
            
            # Check 1: Bot status
            if bot.status != "RUNNING":
                readiness_checks.append({"check": "bot_status", "passed": False, "details": f"Bot status: {bot.status}"})
                overall_ready = False
            else:
                readiness_checks.append({"check": "bot_status", "passed": True, "details": "Bot is running"})
            
            # Check 2: Signal strength (avoid trading on weak signals)
            signal_strength = abs(bot.current_combined_score)
            if signal_strength < 0.1:
                readiness_checks.append({"check": "signal_strength", "passed": False, "details": f"Weak signal: {signal_strength:.3f}"})
                overall_ready = False
            else:
                readiness_checks.append({"check": "signal_strength", "passed": True, "details": f"Strong signal: {signal_strength:.3f}"})
            
            # Check 3: Temperature sanity (avoid FROZEN)
            if current_temperature == "FROZEN":
                readiness_checks.append({"check": "temperature", "passed": False, "details": "Bot temperature FROZEN"})
                overall_ready = False
            else:
                readiness_checks.append({"check": "temperature", "passed": True, "details": f"Temperature: {current_temperature}"})
            
            # Check 4: Position exposure limits
            total_invested = position_summary.get("total_invested", 0.0)
            if total_invested > 800.0:  # Conservative limit for automation
                readiness_checks.append({"check": "exposure_limit", "passed": False, "details": f"High exposure: ${total_invested:.2f}"})
                overall_ready = False
            else:
                readiness_checks.append({"check": "exposure_limit", "passed": True, "details": f"Exposure: ${total_invested:.2f}"})
            
            return {
                "ready": overall_ready,
                "reason": "All checks passed" if overall_ready else "Failed readiness checks",
                "checks": readiness_checks,
                "position_summary": position_summary,
                "signal_data": {
                    "score": bot.current_combined_score,
                    "strength": signal_strength,
                    "temperature": current_temperature
                }
            }
            
        except Exception as e:
            return {
                "ready": False,
                "reason": f"Analysis error: {str(e)}",
                "error": str(e)
            }
    
    def _calculate_automated_trade_decision(self, bot: Bot, position_summary: Dict[str, Any], 
                                          strategy: str, current_temperature: str) -> Dict[str, Any]:
        """Calculate intelligent automated trade decision based on strategy and conditions."""
        try:
            signal_score = bot.current_combined_score
            signal_strength = abs(signal_score)
            total_tranches = position_summary.get("total_tranches", 0)
            
            # Strategy-based decision making
            if strategy == "ADAPTIVE":
                return self._adaptive_strategy_decision(signal_score, signal_strength, total_tranches, current_temperature)
            elif strategy == "AGGRESSIVE":
                return self._aggressive_strategy_decision(signal_score, signal_strength, total_tranches, current_temperature)
            elif strategy == "CONSERVATIVE":
                return self._conservative_strategy_decision(signal_score, signal_strength, total_tranches, current_temperature)
            else:
                # Default to adaptive
                return self._adaptive_strategy_decision(signal_score, signal_strength, total_tranches, current_temperature)
                
        except Exception as e:
            return {
                "action": "HOLD",
                "side": None,
                "reasoning": f"Decision calculation error: {str(e)}",
                "error": str(e)
            }
    
    def _adaptive_strategy_decision(self, signal_score: float, signal_strength: float, 
                                  total_tranches: int, current_temperature: str) -> Dict[str, Any]:
        """Adaptive strategy - balanced approach based on conditions."""
        
        # Strong buy signal
        if signal_score > 0.3 and current_temperature in ["HOT", "WARM"]:
            return {
                "action": "TRADE",
                "side": "BUY",
                "reasoning": f"Strong buy signal ({signal_score:.3f}) with favorable temperature ({current_temperature})"
            }
        
        # Strong sell signal  
        elif signal_score < -0.3 and total_tranches > 0:
            return {
                "action": "TRADE", 
                "side": "SELL",
                "reasoning": f"Strong sell signal ({signal_score:.3f}) with existing position to reduce"
            }
        
        # Moderate signals - be more selective
        elif 0.15 < signal_score < 0.3 and total_tranches < 3 and current_temperature != "COOL":
            return {
                "action": "TRADE",
                "side": "BUY", 
                "reasoning": f"Moderate buy signal ({signal_score:.3f}) for position building (tranches: {total_tranches})"
            }
        
        else:
            return {
                "action": "HOLD",
                "side": None,
                "reasoning": f"Conditions not optimal: signal={signal_score:.3f}, temp={current_temperature}, tranches={total_tranches}"
            }
    
    def _aggressive_strategy_decision(self, signal_score: float, signal_strength: float,
                                    total_tranches: int, current_temperature: str) -> Dict[str, Any]:
        """Aggressive strategy - more frequent trading on weaker signals."""
        
        if signal_score > 0.1:  # Lower threshold
            return {
                "action": "TRADE",
                "side": "BUY",
                "reasoning": f"Aggressive buy on signal {signal_score:.3f}"
            }
        elif signal_score < -0.1 and total_tranches > 0:
            return {
                "action": "TRADE",
                "side": "SELL", 
                "reasoning": f"Aggressive sell on signal {signal_score:.3f}"
            }
        else:
            return {
                "action": "HOLD",
                "side": None,
                "reasoning": f"Signal too weak even for aggressive strategy: {signal_score:.3f}"
            }
    
    def _conservative_strategy_decision(self, signal_score: float, signal_strength: float,
                                      total_tranches: int, current_temperature: str) -> Dict[str, Any]:
        """Conservative strategy - only trade on very strong signals."""
        
        if signal_score > 0.5 and current_temperature == "HOT":  # High threshold
            return {
                "action": "TRADE",
                "side": "BUY",
                "reasoning": f"Conservative buy on very strong signal {signal_score:.3f} and HOT temperature"
            }
        elif signal_score < -0.5 and total_tranches > 2:  # Only sell with established position
            return {
                "action": "TRADE",
                "side": "SELL",
                "reasoning": f"Conservative sell on very strong signal {signal_score:.3f} with {total_tranches} tranches"
            }
        else:
            return {
                "action": "HOLD", 
                "side": None,
                "reasoning": f"Conservative strategy requires stronger signals (current: {signal_score:.3f})"
            }
