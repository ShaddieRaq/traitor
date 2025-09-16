"""
Trading Service - Phase 4.1.2
Real trade execution with comprehensive safety integration.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json
import redis
from sqlalchemy.orm import Session

from ..models.models import Bot, Trade
from ..services.coinbase_service import CoinbaseService
from ..services.trading_safety import TradingSafetyService
from ..services.bot_evaluator import BotSignalEvaluator
from ..services.position_service import PositionService
from ..services.raw_trade_service import RawTradeService
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
        self.raw_trade_service = RawTradeService(db)  # Clean data tracking
    
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
        
        # Redis lock management
        redis_lock_key = f"bot_trade_lock:{bot_id}"
        redis_client = None
        
        try:
            # 1. Get bot information with exclusive lock to prevent race conditions
            bot = self._get_bot_with_trade_lock(bot_id)
            
            # Store Redis client for cleanup
            from ..core.config import settings
            redis_client = redis.from_url(settings.redis_url)
            
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
                # Distinguish between normal blocking conditions and actual errors
                reason = safety_result['reason']
                normal_blocks = [
                    'Price step requirement not met',
                    'cooldown period',
                    'confirmation required'
                ]
                
                is_normal_block = any(block_reason in reason for block_reason in normal_blocks)
                
                if is_normal_block:
                    # Return success response with blocked status for normal conditions
                    if redis_client:
                        redis_client.delete(redis_lock_key)
                        logger.info(f"🔓 Bot {bot_id} Redis trade lock released (normal block)")
                    
                    return {
                        "success": True,
                        "status": "blocked",
                        "blocking_reason": reason,
                        "bot_id": bot_id,
                        "message": f"Trade blocked: {reason}",
                        "blocked_at": datetime.utcnow().isoformat() + "Z"
                    }
                else:
                    # Actual safety errors still throw exceptions
                    raise TradeExecutionError(f"Trade rejected by safety system: {reason}")
            
            # 5. Get current market price for calculations
            market_price = self._get_current_price(bot.pair)
            
            # 6. Validate account balance before proceeding
            balance_validation = self._validate_account_balance(bot.pair, side, size_usd, market_price)
            if not balance_validation["valid"]:
                # Balance issues are normal blocking conditions too
                if redis_client:
                    redis_client.delete(redis_lock_key)
                    logger.info(f"🔓 Bot {bot_id} Redis trade lock released (insufficient balance)")
                
                return {
                    "success": True,
                    "status": "blocked", 
                    "blocking_reason": f"insufficient_balance: {balance_validation['message']}",
                    "bot_id": bot_id,
                    "message": f"Trade blocked: {balance_validation['message']}",
                    "blocked_at": datetime.utcnow().isoformat() + "Z"
                }
            
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
            
            trade_record = self._record_trade(bot, side, size_usd, base_size, market_price, order_result, current_temperature)
            
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
            
            # Release Redis lock on success
            if redis_client:
                redis_client.delete(redis_lock_key)
                logger.info(f"🔓 Bot {bot_id} Redis trade lock released (success)")
            
            return success_result
            
        except TradeExecutionError as e:
            # Check if this is a race condition block vs actual error
            is_race_condition_block = "Another trade is currently in progress" in str(e)
            
            if is_race_condition_block:
                # This is a protective mechanism, not an actual error
                logger.warning(f"❌ Trade execution blocked due to race condition: {e}")
                # Don't broadcast race condition blocks to UI - they're protective, not errors
            else:
                # This is an actual error that should be shown to user
                logger.error(f"❌ Trade execution failed: {e}")
                
                # Broadcast actual trade failures via WebSocket
                self._emit_trade_update({
                    "stage": "trade_failed",
                    "bot_id": bot_id,
                    "bot_name": bot.name if 'bot' in locals() else f"Bot {bot_id}",
                    "side": side,
                    "size_usd": size_usd,
                    "status": "failed",
                    "error": str(e),
                    "message": f"Trade failed: {str(e)}"
                })
            
            # Determine error result based on error type
            if is_race_condition_block:
                error_result = {
                    "success": False,
                    "status": "blocked",
                    "blocking_reason": "Another trade in progress (race condition protection)",
                    "error": str(e),
                    "error_type": "race_condition_block",
                    "bot_id": bot_id,
                    "request": {
                        "side": side,
                        "size_usd": size_usd,
                        "temperature": current_temperature,
                        "auto_size": auto_size
                    },
                    "blocked_at": datetime.utcnow().isoformat() + "Z"
                }
            else:
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
            
            # Release Redis lock on error
            if redis_client:
                redis_client.delete(redis_lock_key)
                logger.info(f"🔓 Bot {bot_id} Redis trade lock released (error)")
            
            return error_result
            
        except Exception as e:
            logger.error(f"💥 Unexpected error during trade execution: {e}")
            
            # Broadcast system error via WebSocket  
            self._emit_trade_update({
                "stage": "system_error",
                "bot_id": bot_id,
                "bot_name": bot.name if 'bot' in locals() else f"Bot {bot_id}",
                "side": side,
                "size_usd": size_usd,
                "status": "failed",
                "error": f"System error: {str(e)}",
                "message": f"System error during trade execution: {str(e)}"
            })
            
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
            
            # Release Redis lock on unexpected error
            if redis_client:
                redis_client.delete(redis_lock_key)
                logger.info(f"🔓 Bot {bot_id} Redis trade lock released (unexpected error)")
            
            return error_result
    
    def _get_bot(self, bot_id: int) -> Bot:
        """Get bot from database with validation."""
        bot = self.db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise TradeExecutionError(f"Bot {bot_id} not found")
        
        if bot.status != "RUNNING":
            raise TradeExecutionError(f"Bot {bot.name} is not running (status: {bot.status})")
        
        return bot
    
    def _get_bot_with_trade_lock(self, bot_id: int) -> Bot:
        """
        Get bot with Redis-based distributed lock for trade execution to prevent race conditions.
        
        SQLite doesn't support true SELECT...FOR UPDATE locking, so we use Redis
        for distributed locking across multiple processes/workers.
        """
        import time
        from ..models.models import Trade
        
        # Get bot with validation first
        bot = self._get_bot(bot_id)
        
        # Redis-based distributed lock using existing configuration
        from ..core.config import settings
        redis_client = redis.from_url(settings.redis_url)
        lock_key = f"bot_trade_lock:{bot_id}"
        lock_timeout = 30  # 30 seconds max lock time
        
        # Try to acquire lock with timeout
        lock_acquired = redis_client.set(lock_key, "locked", nx=True, ex=lock_timeout)
        
        if not lock_acquired:
            logger.warning(f"❌ Bot {bot_id} trade blocked: Another trade in progress")
            raise TradeExecutionError("Another trade is currently in progress for this bot")
        
        try:
            logger.info(f"🔒 Bot {bot_id} Redis trade lock acquired")
            
            # Get the most recent trade for cooldown validation
            last_trade = (
                self.db.query(Trade)
                .filter(Trade.bot_id == bot_id)
                .order_by(Trade.created_at.desc())
                .first()
            )
            
            # Validate cooldown while holding the distributed lock
            if last_trade:
                now = datetime.utcnow()
                last_trade_time = last_trade.filled_at if last_trade.filled_at else last_trade.created_at
                time_since_trade = (now - last_trade_time).total_seconds() / 60  # minutes
                cooldown_minutes = getattr(bot, 'cooldown_minutes', None) or 15
                
                if time_since_trade < cooldown_minutes:
                    remaining_cooldown = cooldown_minutes - time_since_trade
                    redis_client.delete(lock_key)  # Release lock before failing
                    logger.warning(f"❌ Bot {bot_id} trade blocked: {remaining_cooldown:.1f}m cooldown remaining")
                    raise TradeExecutionError(f"Bot is in cooldown period: {remaining_cooldown:.1f} minutes remaining")
            
            logger.info(f"✅ Bot {bot_id} cooldown validation passed - trade approved")
            return bot
            
        except Exception as e:
            # Always release lock on error
            redis_client.delete(lock_key)
            raise
    
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
        """Place the actual order on Coinbase with immediate status verification."""
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
            
            order_id = order_result.get('order_id')
            if not order_id:
                raise TradeExecutionError("Order placement failed - no order ID returned")
            
            # CRITICAL FIX: Immediate status check for market orders (they often fill instantly)
            import time
            max_checks = 10  # Check up to 10 times
            check_interval = 0.5  # 500ms between checks
            
            logger.info(f"🔍 Checking immediate status for order {order_id}")
            
            for attempt in range(max_checks):
                time.sleep(check_interval)
                
                try:
                    status = self.coinbase_service.get_order_status(order_id)
                    if status and status.get('status', '').lower() in ['filled', 'done', 'settled']:
                        logger.info(f"✅ Order {order_id} filled immediately (attempt {attempt + 1})")
                        order_result['status'] = 'completed'  # Override status
                        order_result['filled_immediately'] = True
                        
                        # Emit immediate completion update
                        if bot_id:
                            self._emit_trade_update({
                                "stage": "order_filled_immediately",
                                "bot_id": bot_id,
                                "order_id": order_id,
                                "status": "completed",
                                "message": f"Order filled immediately in {(attempt + 1) * check_interval:.1f}s"
                            })
                        break
                    elif status and status.get('status', '').lower() in ['cancelled', 'rejected']:
                        logger.warning(f"❌ Order {order_id} failed immediately: {status.get('status')}")
                        order_result['status'] = 'failed'
                        order_result['failed_immediately'] = True
                        break
                        
                except Exception as status_check_error:
                    logger.warning(f"Status check attempt {attempt + 1} failed: {status_check_error}")
                    continue
            
            else:
                # Reached max attempts without completion
                logger.info(f"⏳ Order {order_id} still pending after {max_checks * check_interval}s - will monitor")
                order_result['requires_monitoring'] = True
                
                if bot_id:
                    self._emit_trade_update({
                        "stage": "order_pending",
                        "bot_id": bot_id,
                        "order_id": order_id,
                        "status": "pending",
                        "message": f"Order pending - monitoring enabled"
                    })
            
            # Phase 2: Emit successful order placement
            if bot_id:
                self._emit_trade_update({
                    "stage": "order_placed",
                    "bot_id": bot_id,
                    "order_id": order_id,
                    "status": "order_placed",
                    "message": f"Order placed successfully: {order_id}"
                })
            
            logger.info(f"📋 Order placed: {order_id} - {side} {base_size} {product_id}")
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
    
    def _record_trade(self, bot: Bot, side: str, size_usd: float, base_size: float, price: float, 
                     order_result: Dict[str, Any], current_temperature: str) -> Trade:
        """Record trade with intelligent status based on order placement results."""
        try:
            # Get current signal scores for recording
            signal_scores = self._get_current_signal_scores(bot)
            
            # Phase 4.1.3: Calculate tranche information
            tranche_number = self.position_service.calculate_next_tranche_number(bot.id)
            average_entry_price = self.position_service.calculate_average_entry_price(bot.id)
            position_tranches_json = self.position_service.create_position_tranches_json(bot.id)
            
            # CRITICAL FIX: Determine initial status based on order placement result
            initial_status = "pending"
            filled_at = None
            
            if order_result.get('filled_immediately'):
                initial_status = "completed"
                filled_at = datetime.utcnow()
                logger.info(f"🎯 Recording as completed - order filled immediately")
            elif order_result.get('failed_immediately'):
                initial_status = "failed"
                logger.info(f"❌ Recording as failed - order failed immediately")
            elif order_result.get('status') == 'completed':
                initial_status = "completed"
                filled_at = datetime.utcnow()
                logger.info(f"✅ Recording as completed - order status confirmed")
            elif order_result.get('status') == 'failed':
                initial_status = "failed"
                logger.info(f"❌ Recording as failed - order status confirmed")
            else:
                logger.info(f"⏳ Recording as pending - order requires monitoring")
            
            trade = Trade(
                bot_id=bot.id,
                product_id=bot.pair,
                side=side,
                size=base_size,  # Store crypto quantity (FIXED: was size_usd)
                price=price,
                order_id=order_result["order_id"],
                status=initial_status,  # Smart initial status
                combined_signal_score=bot.current_combined_score,
                signal_scores=json.dumps(signal_scores),
                # Phase 4.1.3: Enhanced position fields
                size_usd=size_usd,
                tranche_number=tranche_number,
                average_entry_price=average_entry_price,
                position_tranches=position_tranches_json,
                position_status="BUILDING",  # Will be updated by position service

                created_at=datetime.utcnow(),
                filled_at=filled_at  # Set immediately if order filled, None otherwise
            )
            
            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)
            
            # Phase 4.1.3: Update position status based on new trade
            self.position_service.update_position_status(bot.id, trade)
            
            # If marked for monitoring, schedule immediate follow-up
            if order_result.get('requires_monitoring'):
                self._schedule_order_monitoring(trade.order_id, trade.id)
            
            # Broadcast pending order creation via WebSocket if order is pending
            if initial_status == "pending":
                self._broadcast_pending_order_created(trade)
            
            logger.info(f"💾 Trade recorded: ID {trade.id}, Status: {initial_status}, Tranche #{tranche_number}")
            return trade
            
            # If marked for monitoring, schedule immediate follow-up
            if order_result.get('requires_monitoring'):
                self._schedule_order_monitoring(trade.order_id, trade.id)
                logger.info(f"� Scheduled monitoring for order {trade.order_id}")
            
            logger.info(f"💾 Trade recorded: ID {trade.id}, Status: {initial_status}, Tranche #{tranche_number}")
            return trade
            
        except Exception as e:
            self.db.rollback()
            raise TradeExecutionError(f"Failed to record trade: {e}")
    
    def _broadcast_pending_order_created(self, trade: Trade):
        """Broadcast new pending order creation via WebSocket."""
        try:
            from ..api.websocket import manager
            import asyncio
            
            pending_order_data = {
                "trade_id": trade.id,
                "bot_id": trade.bot_id,
                "order_id": trade.order_id,
                "side": trade.side,
                "size": float(trade.size) if trade.size else 0.0,
                "size_usd": float(trade.size_usd) if trade.size_usd else 0.0,
                "price": float(trade.price) if trade.price else 0.0,
                "product_id": trade.product_id,
                "status": "pending",
                "created_at": trade.created_at.isoformat() if trade.created_at else None,
                "time_elapsed_seconds": 0
            }
            
            # Use asyncio to run the async broadcast in a sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If there's already a running loop, create a task
                asyncio.create_task(manager.broadcast_pending_order_update(pending_order_data))
            else:
                # If no loop is running, run directly
                asyncio.run(manager.broadcast_pending_order_update(pending_order_data))
                
            logger.info(f"📡 Broadcasted pending order creation for order {trade.order_id}")
            
        except Exception as e:
            logger.warning(f"Failed to broadcast pending order creation: {e}")
    
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
    
    def _schedule_order_monitoring(self, order_id: str, trade_id: int):
        """Schedule real-time monitoring for an order that requires follow-up."""
        try:
            # Use the new dedicated monitoring task
            from ..tasks.trading_tasks import monitor_order_status
            monitor_order_status.delay(order_id, trade_id)
            logger.info(f"📅 Scheduled real-time monitoring for order {order_id} (trade {trade_id})")
            
        except Exception as e:
            logger.error(f"Failed to schedule order monitoring: {e}")
            # Don't fail the trade if monitoring scheduling fails
    
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
        Enhanced trade status update with comprehensive logging and error handling.
        This should be called periodically to keep trade statuses current.
        """
        try:
            # Get all pending trades
            pending_trades = self.db.query(Trade).filter(
                Trade.status.in_(["pending", "open", "active"])
            ).all()
            
            updated_count = 0
            completed_count = 0
            failed_count = 0
            sync_issues = []
            
            logger.info(f"🔄 Enhanced reconciliation: checking {len(pending_trades)} pending trades")
            
            for trade in pending_trades:
                if not trade.order_id:
                    # No order ID means trade failed to place - mark as failed
                    old_status = trade.status
                    trade.status = "failed"
                    trade.filled_at = datetime.utcnow()
                    updated_count += 1
                    failed_count += 1
                    sync_issues.append({
                        "trade_id": trade.id,
                        "issue": "no_order_id",
                        "old_status": old_status,
                        "new_status": "failed"
                    })
                    continue
                
                try:
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
                            
                            # Log sync issue if this order was stuck
                            if old_status == "pending":
                                sync_issues.append({
                                    "trade_id": trade.id,
                                    "order_id": trade.order_id,
                                    "issue": "stale_pending_order",
                                    "old_status": old_status,
                                    "new_status": "completed",
                                    "created_at": trade.created_at.isoformat() if trade.created_at else None
                                })
                            
                            # Sync completed trade to raw_trades table using clean Coinbase data
                            try:
                                self._sync_completed_trade_to_raw_table(trade)
                            except Exception as sync_error:
                                logger.warning(f"Failed to sync trade {trade.id} to raw_trades: {sync_error}")
                                
                        elif new_status.lower() in ["cancelled", "rejected"]:
                            trade.status = "failed"
                            # Don't set filled_at for failed orders - they weren't filled
                            trade.filled_at = None
                            failed_count += 1
                            
                            if old_status == "pending":
                                sync_issues.append({
                                    "trade_id": trade.id,
                                    "order_id": trade.order_id,
                                    "issue": "stale_pending_failed",
                                    "old_status": old_status,
                                    "new_status": "failed"
                                })
                                
                        elif new_status.lower() in ["open", "active", "pending"]:
                            trade.status = "pending"
                            # Keep filled_at as None for pending orders
                            trade.filled_at = None
                        else:
                            trade.status = new_status.lower()
                        
                        if old_status != trade.status:
                            updated_count += 1
                            logger.info(f"📊 Trade {trade.id} status: {old_status} → {trade.status}")
                    
                    else:
                        # Could not get status from Coinbase
                        logger.warning(f"⚠️ Could not get status for order {trade.order_id}")
                        sync_issues.append({
                            "trade_id": trade.id,
                            "order_id": trade.order_id,
                            "issue": "coinbase_status_unavailable",
                            "old_status": trade.status,
                            "new_status": "unchanged"
                        })
                        
                except Exception as trade_error:
                    logger.error(f"Error checking trade {trade.id} (order {trade.order_id}): {trade_error}")
                    sync_issues.append({
                        "trade_id": trade.id,
                        "order_id": trade.order_id,
                        "issue": "api_error",
                        "error": str(trade_error)
                    })
            
            # Commit all updates
            self.db.commit()
            
            result = {
                "total_checked": len(pending_trades),
                "updated_count": updated_count,
                "completed_count": completed_count,
                "failed_count": failed_count,
                "sync_issues_count": len(sync_issues),
                "sync_issues": sync_issues,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Enhanced logging and alerting
            if updated_count > 0:
                logger.warning(f"⚠️ SYNC ISSUE DETECTED: {updated_count} orders required manual sync")
                logger.info(f"✅ Reconciliation complete: {completed_count} completed, {failed_count} failed")
                
                # Alert about persistent sync issues
                if len(sync_issues) > 0:
                    self._alert_sync_issues(result)
            else:
                logger.info("✅ All orders in sync - no stale statuses found")
            
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error in enhanced trade status reconciliation: {e}")
            return {"error": str(e), "total_checked": 0, "updated_count": 0}
    
    def _alert_sync_issues(self, reconciliation_result: Dict[str, Any]):
        """Alert about persistent sync issues."""
        updated_count = reconciliation_result.get('updated_count', 0)
        sync_issues = reconciliation_result.get('sync_issues', [])
        
        if updated_count > 0:
            logger.error(f"🚨 SYNC ISSUE ALERT: {updated_count} orders required manual sync")
            
            # Log details for investigation
            for issue in sync_issues:
                if issue.get('issue') == 'stale_pending_order':
                    logger.error(f"   STALE ORDER: {issue['order_id']} was pending but actually completed")
                elif issue.get('issue') == 'no_order_id':
                    logger.error(f"   MISSING ORDER ID: Trade {issue['trade_id']} has no order_id")
                elif issue.get('issue') == 'api_error':
                    logger.error(f"   API ERROR: {issue['order_id']} - {issue.get('error')}")
            
            # TODO: Add Slack/email alerts for production
            # send_slack_alert(f"Order sync issue: {updated_count} stale orders found")
    
    def _sync_completed_trade_to_raw_table(self, trade: Trade):
        """
        Sync a completed trade to the raw_trades table using clean Coinbase data.
        This ensures we have clean, unprocessed data for accurate analysis.
        """
        try:
            if not trade.order_id:
                logger.warning(f"Cannot sync trade {trade.id} - no order_id")
                return
            
            # Get the actual fill data from Coinbase for this order
            fills = self.coinbase_service.get_raw_fills(days_back=7)  # Get recent fills
            
            # Find fills matching this order_id
            order_fills = [
                fill for fill in fills 
                if fill.get('order_id') == trade.order_id
            ]
            
            if not order_fills:
                logger.warning(f"No Coinbase fills found for order {trade.order_id}")
                return
            
            # Store each fill as a raw trade record
            for fill in order_fills:
                try:
                    self.raw_trade_service.store_raw_trade(fill)
                    logger.info(f"✅ Synced fill {fill.get('trade_id')} to raw_trades table")
                except Exception as fill_error:
                    logger.error(f"Failed to store raw fill {fill.get('trade_id')}: {fill_error}")
            
        except Exception as e:
            logger.error(f"Error syncing trade {trade.id} to raw_trades: {e}")

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
            
            # Final safety bounds - use bot's configured minimum, not hard-coded $10
            min_size = max(bot.position_size_usd * 0.1, 1.0)  # At least 10% of bot's position size, minimum $1
            max_size = bot.position_size_usd * 10.0  # Maximum 10x bot's position size
            intelligent_size = max(min_size, min(intelligent_size, max_size))
            
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
