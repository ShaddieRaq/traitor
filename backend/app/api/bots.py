from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging
from ..core.database import get_db
from ..models.models import Bot
from ..api.schemas import BotCreate, BotUpdate, BotResponse, BotStatusResponse, EnhancedBotStatusResponse, TradingThresholds
from ..utils.temperature import calculate_bot_temperature

logger = logging.getLogger(__name__)

router = APIRouter()


def extract_trading_thresholds(signal_config: dict) -> Optional[TradingThresholds]:
    """Extract trading thresholds from signal_config for UI display."""
    try:
        if not signal_config or 'trading_thresholds' not in signal_config:
            # Return default thresholds
            return TradingThresholds(
                buy_threshold=-0.05,
                sell_threshold=0.05
            )
        
        thresholds_data = signal_config['trading_thresholds']
        return TradingThresholds(
            buy_threshold=thresholds_data.get('buy_threshold', -0.05),
            sell_threshold=thresholds_data.get('sell_threshold', 0.05),
            optimization_applied=thresholds_data.get('optimization_applied'),
            applied_date=thresholds_data.get('applied_date')
        )
    except Exception as e:
        logger.warning(f"Error extracting trading thresholds: {e}")
        return TradingThresholds(
            buy_threshold=-0.05,
            sell_threshold=0.05
        )


def prepare_bot_response(bot: Bot) -> dict:
    """Prepare bot for response by converting signal_config and adding trading_thresholds."""
    # Convert signal_config from JSON string to dict
    try:
        signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
    except json.JSONDecodeError:
        signal_config = {}
    
    # Extract trading thresholds for UI
    trading_thresholds = extract_trading_thresholds(signal_config)
    
    # Return a dictionary instead of modifying the SQLAlchemy model
    # Provide default values for required fields that might be None in the database
    return {
        'id': bot.id,
        'name': bot.name,
        'description': bot.description or f"Trading bot for {bot.pair}",  # Default description
        'pair': bot.pair,
        'status': bot.status,
        'position_size_usd': bot.position_size_usd,
        'max_positions': bot.max_positions,
        'stop_loss_pct': bot.stop_loss_pct,
        'take_profit_pct': bot.take_profit_pct,
        'confirmation_minutes': bot.confirmation_minutes,
        'trade_step_pct': bot.trade_step_pct,
        'cooldown_minutes': bot.cooldown_minutes,
        'signal_config': signal_config,
        'trading_thresholds': trading_thresholds,
        'current_position_size': bot.current_position_size or 0.0,  # Default to 0.0
        'current_position_entry_price': bot.current_position_entry_price,
        'current_combined_score': bot.current_combined_score or 0.0,  # Default to 0.0
        'signal_confirmation_start': bot.signal_confirmation_start,
        'created_at': bot.created_at,
        'updated_at': bot.updated_at,
        'use_trend_detection': bot.use_trend_detection,
        'use_position_sizing': bot.use_position_sizing,
    }


@router.get("/", response_model=List[BotResponse])
def get_bots(db: Session = Depends(get_db)):
    """Get all bots."""
    bots = db.query(Bot).all()
    
    # Prepare bots for response with trading thresholds
    return [prepare_bot_response(bot) for bot in bots]


@router.post("/", response_model=BotResponse)
def create_bot(bot: BotCreate, db: Session = Depends(get_db)):
    """Create a new bot."""
    try:
        # Check if bot name already exists
        existing_bot = db.query(Bot).filter(Bot.name == bot.name).first()
        if existing_bot:
            raise HTTPException(status_code=400, detail="Bot name already exists")
        
        # Create default signal configuration if none provided
        if bot.signal_config:
            if hasattr(bot.signal_config, 'dict'):
                signal_config_json = bot.signal_config.model_dump()
            else:
                signal_config_json = bot.signal_config
        else:
            # Default signal configuration for new bots (matches working bots)
            signal_config_json = {
                "rsi": {
                    "enabled": True,
                    "weight": 0.4,
                    "period": 14,
                    "buy_threshold": 30,
                    "sell_threshold": 70
                },
                "moving_average": {
                    "enabled": True,
                    "weight": 0.35,
                    "fast_period": 12,
                    "slow_period": 26
                },
                "macd": {
                    "enabled": True,
                    "weight": 0.25,
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                },
                "trading_thresholds": {
                    "buy_threshold": -0.05,
                    "sell_threshold": 0.05
                }
            }

        # Create new bot with intelligence features enabled by default
        db_bot = Bot(
            name=bot.name,
            description=bot.description,
            pair=bot.pair,
            position_size_usd=bot.position_size_usd,
            max_positions=bot.max_positions,
            stop_loss_pct=bot.stop_loss_pct,
            take_profit_pct=bot.take_profit_pct,
            confirmation_minutes=bot.confirmation_minutes,
            trade_step_pct=bot.trade_step_pct,
            cooldown_minutes=bot.cooldown_minutes,
            signal_config=json.dumps(signal_config_json),
            # Enable 4-phase intelligence framework by default
            use_trend_detection=True,  # Phase 1: Market Regime Intelligence
            use_position_sizing=True   # Phase 2: Dynamic Position Sizing
        )
        
        db.add(db_bot)
        db.commit()
        db.refresh(db_bot)
        
        # Use prepare_bot_response to add computed fields like trading_thresholds
        return prepare_bot_response(db_bot)
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 Bad Request) without wrapping
        raise
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR in create_bot: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()  # Rollback the transaction
        raise HTTPException(status_code=500, detail=f"Failed to create bot: {type(e).__name__}: {str(e)}")


@router.get("/{bot_id}", response_model=BotResponse)
def get_bot(bot_id: int, db: Session = Depends(get_db)):
    """Get a specific bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return prepare_bot_response(bot)


@router.put("/{bot_id}", response_model=BotResponse)
def update_bot(bot_id: int, bot_update: BotUpdate, db: Session = Depends(get_db)):
    """Update a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Update fields
    update_data = bot_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "signal_config" and value is not None:
            setattr(bot, field, json.dumps(value))
        else:
            setattr(bot, field, value)
    
    db.commit()
    db.refresh(bot)
    
    # Use prepare_bot_response to add computed fields
    return prepare_bot_response(bot)


@router.delete("/{bot_id}")
def delete_bot(bot_id: int, liquidate: bool = False, db: Session = Depends(get_db)):
    """
    Delete a bot. 
    
    Args:
        bot_id: ID of the bot to delete
        liquidate: If True, sells all holdings before deleting. If False, just deletes the bot.
    """
    logger.info(f"🗑️ DELETE REQUEST RECEIVED for bot {bot_id}, liquidate={liquidate}")
    try:
        from ..services.coinbase_service import coinbase_service
        from ..services.raw_trade_service import RawTradeService
        
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        liquidation_result = None
        
        # Liquidate holdings if requested
        if liquidate:
            raw_trade_service = RawTradeService(db)
            
            try:
                # Get current holdings for this product
                accounts = coinbase_service.get_accounts()
                product_id = bot.pair
                base_currency = product_id.split('-')[0]
                
                # Find ALL accounts with this currency and sum holdings (Coinbase can have multiple accounts per currency)
                holdings = 0.0
                account_count = 0
                for account in accounts:
                    if account.get('currency') == base_currency:
                        available_balance = account.get('available_balance', 0)
                        hold_balance = account.get('hold', 0)
                        
                        # Handle both dict format {"value": x} and direct float format
                        if isinstance(available_balance, dict):
                            available = float(available_balance.get('value', 0))
                        else:
                            available = float(available_balance)
                            
                        # Add hold balance (funds in pending orders)
                        if isinstance(hold_balance, dict):
                            hold = float(hold_balance.get('value', 0))
                        else:
                            hold = float(hold_balance)
                        
                        # Sum across all accounts for this currency
                        account_total = available + hold
                        holdings += account_total
                        account_count += 1
                        
                        if account_total > 0:
                            logger.info(f"💰 {base_currency} account #{account_count}: {available} available + {hold} on hold = {account_total}")
                
                if account_count > 0:
                    logger.info(f"💰 Total {base_currency} across {account_count} account(s): {holdings}")
                
                liquidation_result = {
                    "product_id": product_id,
                    "holdings_liquidated": holdings,
                    "trade_executed": False,
                    "error": None
                }
                
                # Only execute sell if there are holdings
                if holdings > 0:
                    try:
                        # Place market sell order to liquidate
                        order_result = coinbase_service.place_market_order(
                            product_id=product_id,
                            side='SELL',
                            size=holdings
                        )
                        
                        # Check if order was placed (order_result returns dict with order_id, not 'success' key)
                        if order_result and order_result.get('order_id'):
                            liquidation_result['trade_executed'] = True
                            liquidation_result['order_id'] = order_result.get('order_id')
                            
                            # Note: Sync will happen automatically via scheduled Celery task
                            # No need to sync immediately - avoid blocking the delete request
                            
                            logger.info(f"✅ Liquidated {holdings} {base_currency} for bot {bot.name}")
                        else:
                            liquidation_result['error'] = "Order placement failed - no order ID returned"
                            logger.warning(f"⚠️ Failed to liquidate holdings for {product_id}: {order_result}")
                            
                    except Exception as e:
                        liquidation_result['error'] = str(e)
                        logger.error(f"❌ Error liquidating {product_id}: {e}")
                else:
                    logger.info(f"ℹ️ No holdings to liquidate for {product_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error during liquidation: {e}")
                liquidation_result = {
                    "error": str(e),
                    "trade_executed": False
                }
        
        # Delete the bot and related records
        # Delete related records first to avoid foreign key constraints
        from ..models.models import Trade, SignalPredictionRecord, BotSignalHistory, AdaptiveSignalWeights
        
        # Delete all records with foreign keys to this bot
        trades_deleted = db.query(Trade).filter(Trade.bot_id == bot_id).delete()
        logger.info(f"🗑️ Deleted {trades_deleted} Trade records for bot {bot_id}")
        
        history_deleted = db.query(BotSignalHistory).filter(BotSignalHistory.bot_id == bot_id).delete()
        logger.info(f"🗑️ Deleted {history_deleted} BotSignalHistory records for bot {bot_id}")
        
        weights_deleted = db.query(AdaptiveSignalWeights).filter(AdaptiveSignalWeights.bot_id == bot_id).delete()
        logger.info(f"🗑️ Deleted {weights_deleted} AdaptiveSignalWeights records for bot {bot_id}")
        
        # Delete signal predictions (stored by pair, not bot_id)
        predictions_deleted = db.query(SignalPredictionRecord).filter(SignalPredictionRecord.pair == bot.pair).delete()
        logger.info(f"🗑️ Deleted {predictions_deleted} SignalPredictionRecord records for pair {bot.pair}")
        
        # CRITICAL: Flush deletions to database BEFORE deleting bot
        # This ensures foreign key constraints are satisfied
        db.flush()
        logger.info(f"🗑️ Flushed child record deletions to database")
        
        # Now delete the bot
        logger.info(f"🗑️ Now deleting bot {bot_id} ({bot.name})")
        db.delete(bot)
        db.commit()
        logger.info(f"✅ Bot {bot_id} deleted successfully")
        
        response = {"message": f"Bot deleted successfully"}
        if liquidation_result:
            response["liquidation"] = liquidation_result
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR in delete_bot: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()  # Rollback any partial changes
        raise HTTPException(status_code=500, detail=f"Failed to delete bot: {type(e).__name__}: {str(e)}")


@router.post("/{bot_id}/start")
def start_bot(bot_id: int, db: Session = Depends(get_db)):
    """Start a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    bot.status = "RUNNING"
    db.commit()
    
    return {"message": f"Bot '{bot.name}' started successfully", "status": bot.status}


@router.post("/{bot_id}/stop")
def stop_bot(bot_id: int, db: Session = Depends(get_db)):
    """Stop a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    bot.status = "STOPPED"
    db.commit()
    
    return {"message": f"Bot '{bot.name}' stopped successfully", "status": bot.status}


@router.post("/stop-all")
def stop_all_bots(db: Session = Depends(get_db)):
    """Stop all running bots."""
    running_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
    
    for bot in running_bots:
        bot.status = "STOPPED"
    
    db.commit()
    
    return {"message": f"Stopped {len(running_bots)} running bots"}


@router.get("/status/summary", response_model=List[BotStatusResponse])
def get_bots_status_summary(db: Session = Depends(get_db)):
    """Get lightweight status summary of all bots for dashboard with fresh evaluations."""
    from ..services.bot_evaluator import get_bot_evaluator
    from ..utils.market_data_helper import create_market_data_cache
    from ..services.coinbase_service import coinbase_service
    import pandas as pd
    
    bots = db.query(Bot).all()
    evaluator = get_bot_evaluator(db)
    
    # Get fresh market data for all unique trading pairs using centralized utility
    unique_pairs = list(set(bot.pair for bot in bots))
    market_data_cache = create_market_data_cache(unique_pairs, granularity=3600, limit=100)
    
    status_list = []
    for bot in bots:
        try:
            # Get fresh evaluation for this bot (full evaluation)
            market_data = market_data_cache.get(bot.pair)
            optimization_status = {"skipped": False, "reason": ""}
            if market_data is not None and not market_data.empty:
                # Use full evaluation to get accurate signals (automatic trading handled by confirmation system)
                evaluation_result = evaluator.evaluate_bot(bot, market_data)
                fresh_score = evaluation_result.get('overall_score', 0.0)
                temperature = evaluation_result.get('temperature', 'FROZEN')
                distance_to_signal = abs(fresh_score) if fresh_score != 0 else 1.0
                
                # Check if signals were skipped due to optimization
                if evaluation_result.get('metadata', {}).get('optimization_skipped', False):
                    optimization_status = {
                        "skipped": True, 
                        "reason": "Insufficient balance - signals skipped for performance"
                    }
            else:
                # Fallback to cached data if no market data available
                fresh_score = bot.current_combined_score
                temperature = calculate_bot_temperature(bot.current_combined_score)
                distance_to_signal = calculate_distance_to_signal(bot.current_combined_score)
                
            # Balance validation removed from enhanced status to prevent rate limiting
            # This endpoint is polled every 5 seconds - balance checks are too expensive
            # Balance is validated when actual trades are executed
            balance_status = {"valid": True, "message": ""}
                
            status_list.append({
                "id": bot.id,
                "name": bot.name,
                "pair": bot.pair,
                "status": bot.status,
                "current_combined_score": fresh_score,
                "current_position_size": bot.current_position_size,
                "temperature": temperature,
                "distance_to_signal": distance_to_signal,
                "balance_status": balance_status,
                "optimization_status": optimization_status
            })
        except Exception as e:
            logger.error(f"Error evaluating bot {bot.id}: {e}")
            # Fallback to cached data for this bot
            status_list.append({
                "id": bot.id,
                "name": bot.name,
                "pair": bot.pair,
                "status": bot.status,
                "current_combined_score": bot.current_combined_score,
                "current_position_size": bot.current_position_size,
                "temperature": calculate_bot_temperature(bot.current_combined_score),
                "distance_to_signal": calculate_distance_to_signal(bot.current_combined_score)
            })
    
    return status_list


@router.get("/{bot_id}/confirmation-status")
def get_bot_confirmation_status(bot_id: int, db: Session = Depends(get_db)):
    """Get the current signal confirmation status for a bot."""
    from ..services.bot_evaluator import get_bot_evaluator
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    evaluator = get_bot_evaluator(db)
    confirmation_status = evaluator.get_confirmation_status(bot)
    
    return {
        "bot_id": bot.id,
        "bot_name": bot.name,
        "confirmation_status": confirmation_status
    }


@router.get("/status/enhanced", response_model=List[EnhancedBotStatusResponse])
def get_enhanced_bots_status(db: Session = Depends(get_db)):
    """Get enhanced bot status with trading visibility for Phase 4.3 + Phase 1 trend detection."""
    from ..services.bot_evaluator import get_bot_evaluator
    from ..services.coinbase_service import coinbase_service
    from ..services.trend_detection_engine import get_trend_engine  # Phase 1 addition
    from ..models.models import Trade
    from ..api.schemas import EnhancedBotStatusResponse, TradingIntent, ConfirmationStatus, TradeReadiness, LastTradeInfo
    from ..utils.temperature import calculate_bot_temperature
    import pandas as pd
    from datetime import datetime, timedelta
    
    bots = db.query(Bot).all()
    evaluator = get_bot_evaluator(db)
    trend_engine = get_trend_engine()  # Phase 1: Initialize trend detection engine
    
    # Get cached market data for all unique trading pairs using centralized utility
    from ..utils.market_data_helper import create_market_data_cache
    from ..utils.service_registry import get_market_cache
    
    # Use proper singleton pattern for MarketDataCache
    market_cache = get_market_cache()
    unique_pairs = list(set(bot.pair for bot in bots))
    market_data_cache = create_market_data_cache(unique_pairs, granularity=3600, limit=100)
    
    enhanced_status_list = []
    
    for bot in bots:
        try:
            # Get REAL evaluation for this bot - same as trading logic uses
            try:
                # Get market data for this bot's pair
                market_data = market_data_cache.get(bot.pair)
                if market_data is not None and not market_data.empty:
                    evaluation_result = evaluator.evaluate_bot(bot, market_data)
                    fresh_score = evaluation_result.get('overall_score', 0.0)
                    next_action = evaluation_result.get('action', 'hold')
                    confidence = evaluation_result.get('confidence', 0.0)
                    logger.info(f"✅ Real evaluation for bot {bot.id}: {next_action} | {fresh_score:.3f}")
                else:
                    logger.warning(f"⚠️  No market data for {bot.pair}, using stored score")
                    fresh_score = bot.current_combined_score or 0.0
                    next_action = "hold"
                    confidence = 0.0
            except Exception as eval_error:
                logger.error(f"❌ Evaluation failed for bot {bot.id}: {eval_error}")
                # Fallback to stored score
                fresh_score = bot.current_combined_score or 0.0
                next_action = "hold"
                confidence = 0.0
            
            # Calculate temperature from real score
            temperature = calculate_bot_temperature(fresh_score)
            distance_to_signal = abs(fresh_score) / 0.3 if fresh_score != 0 else 1.0
            
            # Calculate signal strength (0-1 scale) from real evaluation
            abs_score = abs(fresh_score)
            signal_strength = min(abs_score / 0.3, 1.0)  # Normalize to production threshold
            
            # Get confirmation status
            confirmation_status = evaluator.get_confirmation_status(bot)
            
            # Calculate distance to threshold
            threshold = 0.08  # Testing threshold for immediate visibility
            abs_score = abs(fresh_score)
            distance_to_threshold = max(0, threshold - abs_score) if abs_score < threshold else 0
            
            # Create trading intent
            trading_intent = TradingIntent(
                next_action=next_action,
                signal_strength=signal_strength,
                confidence=confidence,
                distance_to_threshold=distance_to_threshold
            )
            
            # Calculate cooldown remaining FIRST (needed for confirmation logic)
            cooldown_remaining_minutes = 0
            last_successful_trade = db.query(Trade).filter(
                Trade.bot_id == bot.id
            ).order_by(Trade.created_at.desc()).first()
            
            if last_successful_trade:
                time_since_trade = (datetime.utcnow() - last_successful_trade.created_at).total_seconds() / 60
                cooldown_minutes = getattr(bot, 'cooldown_minutes', None) or 15
                cooldown_remaining_minutes = max(0, cooldown_minutes - time_since_trade)
            
            # Create confirmation status object - FIXED: Proper cooldown handling
            if cooldown_remaining_minutes > 0:
                # During cooldown, confirmation should show as suspended/blocked
                confirmation = ConfirmationStatus(
                    is_active=False,
                    action="suspended_cooldown",  # Special action to indicate cooldown suspension
                    progress=0.0,
                    time_remaining_seconds=0,
                    started_at=None,
                    required_duration_minutes=bot.confirmation_minutes
                )
            else:
                # Normal confirmation status when not in cooldown
                confirmation = ConfirmationStatus(
                    is_active=confirmation_status.get('needs_confirmation', False),
                    action=confirmation_status.get('action_being_confirmed'),
                    progress=confirmation_status.get('confirmation_progress', 0.0),
                    time_remaining_seconds=int(confirmation_status.get('time_remaining_minutes', 0) * 60),
                    started_at=datetime.fromisoformat(confirmation_status['confirmation_start'].replace('Z', '+00:00')) if confirmation_status.get('confirmation_start') else None,
                    required_duration_minutes=bot.confirmation_minutes
                )
            
            # Check balance validation for trade readiness
            has_sufficient_balance = True
            balance_blocking_reason = None
            if next_action != "hold":
                try:
                    # Get current market price for balance validation
                    ticker = coinbase_service.get_product_ticker(bot.pair)
                    if ticker and 'price' in ticker:
                        current_price = float(ticker['price'])
                        balance_result = coinbase_service.validate_trade_balance(
                            product_id=bot.pair,
                            side=next_action.upper(),
                            size_usd=bot.position_size_usd,
                            current_price=current_price
                        )
                        has_sufficient_balance = balance_result["valid"]
                        if not has_sufficient_balance:
                            balance_blocking_reason = f"insufficient_balance: {balance_result['message']}"
                    else:
                        has_sufficient_balance = False
                        balance_blocking_reason = "cannot_get_price"
                except Exception as e:
                    logger.warning(f"Balance check failed for bot {bot.id}: {e}")
                    has_sufficient_balance = False
                    balance_blocking_reason = "balance_check_error"
            
            # Determine trade readiness - FIXED LOGIC: Cooldown takes priority over confirmation
            confirmation_required = confirmation_status.get('needs_confirmation', False)
            confirmation_complete = confirmation_status.get('is_confirmed', False) if confirmation_required else True
            
            # Check price step requirement using safety service
            price_step_ok = True
            price_step_blocking_reason = None
            price_step_info = {}
            if next_action != "hold" and bot.status == 'RUNNING':
                try:
                    from ..services.trading_safety import TradingSafetyService
                    safety_service = TradingSafetyService(db)
                    price_step_ok, price_step_info = safety_service._check_price_step(bot, next_action.upper(), bot.position_size_usd)
                    if not price_step_ok:
                        price_step_blocking_reason = f"Price step requirement not met ({price_step_info['current_change_pct']:.2f}% < {price_step_info['required_step_pct']:.1f}%)"
                except Exception as e:
                    logger.warning(f"Price step check failed for bot {bot.id}: {e}")
                    price_step_ok = True  # Allow trade if check fails
            
            # FIXED: Single unified logic for trade readiness
            can_trade = (bot.status == 'RUNNING' and 
                        cooldown_remaining_minutes == 0 and 
                        has_sufficient_balance and 
                        price_step_ok and
                        confirmation_complete)
            
            # Determine status and blocking reason with proper priority
            readiness_status = "no_signal"
            blocking_reason = None
            
            if next_action != "hold":
                # Priority 1: Cooldown (overrides everything)
                if cooldown_remaining_minutes > 0:
                    readiness_status = "cooling_down"
                    blocking_reason = "cooldown"
                # Priority 2: Bot not running
                elif bot.status != 'RUNNING':
                    readiness_status = "blocked"
                    blocking_reason = "bot_stopped"
                # Priority 3: Insufficient balance
                elif not has_sufficient_balance:
                    readiness_status = "blocked"
                    blocking_reason = balance_blocking_reason
                # Priority 4: Price step requirement
                elif not price_step_ok:
                    readiness_status = "blocked"
                    blocking_reason = price_step_blocking_reason
                # Priority 5: Confirmation required but not complete
                elif confirmation_required and not confirmation_complete:
                    readiness_status = "confirming"
                    blocking_reason = "awaiting_confirmation"
                # Priority 6: Ready to trade
                elif can_trade:
                    readiness_status = "ready"
                    blocking_reason = None
                else:
                    readiness_status = "blocked"
                    blocking_reason = "unknown"
            
            trade_readiness = TradeReadiness(
                status=readiness_status,
                can_trade=can_trade,
                blocking_reason=blocking_reason,
                cooldown_remaining_minutes=int(cooldown_remaining_minutes)
            )
            
            # Calculate actual position from trades (fix for stale bot.current_position_size)
            trades = db.query(Trade).filter(Trade.bot_id == bot.id).all()
            # Calculate position in token units first
            token_position = sum(trade.size if trade.side == 'BUY' else -trade.size for trade in trades)
            
            # Convert token position to USD value using current market price
            try:
                if token_position != 0 and market_data_cache.get(bot.pair) is not None:
                    latest_market_data = market_data_cache[bot.pair]
                    if not latest_market_data.empty:
                        current_price = latest_market_data.iloc[-1]['close']
                        actual_position_usd = token_position * current_price
                    else:
                        actual_position_usd = 0.0  # No market data available
                else:
                    actual_position_usd = 0.0  # No position or no market data
            except Exception as e:
                logger.warning(f"Failed to calculate USD position for {bot.pair}: {e}")
                actual_position_usd = 0.0
            
            # Get last trade info
            last_trade_query = db.query(Trade).filter(Trade.bot_id == bot.id).order_by(Trade.created_at.desc()).first()
            last_trade = None
            if last_trade_query:
                minutes_ago = int((datetime.utcnow() - last_trade_query.created_at).total_seconds() / 60)
                last_trade = LastTradeInfo(
                    side=last_trade_query.side,
                    price=last_trade_query.price,
                    size=last_trade_query.size,
                    status=last_trade_query.status,
                    executed_at=last_trade_query.created_at,
                    minutes_ago=minutes_ago
                )
            
            # Phase 1: Add trend analysis if enabled for this bot
            trend_analysis = None
            if getattr(bot, 'use_trend_detection', False):
                try:
                    trend_data = trend_engine.analyze_trend(bot.pair)
                    trend_analysis = trend_data  # trend_data is already a dict matching TrendAnalysisResponse
                    logger.info(f"✅ Trend analysis for {bot.pair}: {trend_data['regime']} ({trend_data['trend_strength']:.3f})")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to get trend analysis for {bot.pair}: {e}")
            
            # Phase 2: Add position sizing analysis if enabled for this bot
            position_sizing = None
            if getattr(bot, 'use_position_sizing', False):
                try:
                    from ..services.position_sizing_engine import get_position_sizing_engine
                    sizing_engine = get_position_sizing_engine()
                    
                    position_sizing_data = sizing_engine.calculate_position_size(
                        base_position_size=bot.position_size_usd,
                        product_id=bot.pair,
                        signal_confidence=confidence,
                        override_regime=trend_analysis if trend_analysis else None
                    )
                    position_sizing = position_sizing_data
                    logger.info(f"💰 Position sizing for {bot.pair}: ${position_sizing_data['final_position_size']:.2f} ({position_sizing_data['total_multiplier']:.2f}x)")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to get position sizing for {bot.pair}: {e}")
            
            enhanced_status_list.append(EnhancedBotStatusResponse(
                id=bot.id,
                name=bot.name,
                pair=bot.pair,
                status=bot.status,
                current_combined_score=fresh_score,
                current_position_size=actual_position_usd,
                position_size_usd=bot.position_size_usd,  # Use configured max position size, not current position value
                temperature=temperature,
                distance_to_signal=distance_to_signal,
                signal_confidence=confidence,
                trading_intent=trading_intent,
                confirmation=confirmation,
                trade_readiness=trade_readiness,
                last_trade=last_trade,
                cooldown_minutes=bot.cooldown_minutes,
                trend_analysis=trend_analysis,
                use_trend_detection=getattr(bot, 'use_trend_detection', False),
                position_sizing=position_sizing,
                use_position_sizing=getattr(bot, 'use_position_sizing', False)
            ))
            
        except Exception as e:
            logger.error(f"Error creating enhanced status for bot {bot.id}: {e}")
            # Create basic status on error
            enhanced_status_list.append(EnhancedBotStatusResponse(
                id=bot.id,
                name=bot.name,
                pair=bot.pair,
                status=bot.status,
                current_combined_score=bot.current_combined_score,
                current_position_size=bot.current_position_size,
                position_size_usd=bot.current_position_size,  # Provide both fields for compatibility
                temperature=calculate_bot_temperature(bot.current_combined_score),
                distance_to_signal=1.0,
                signal_confidence=0.0,
                trading_intent=TradingIntent(next_action="hold", signal_strength=0.0, confidence=0.0, distance_to_threshold=1.0),
                confirmation=ConfirmationStatus(is_active=False),
                trade_readiness=TradeReadiness(status="no_signal", can_trade=False),
                last_trade=None,
                cooldown_minutes=bot.cooldown_minutes,
                trend_analysis=None,
                use_trend_detection=getattr(bot, 'use_trend_detection', False),
                position_sizing=None,
                use_position_sizing=getattr(bot, 'use_position_sizing', False)
            ))
    
    return enhanced_status_list


@router.get("/{bot_id}/signal-history")
def get_bot_signal_history(bot_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Get recent signal evaluation history for a bot."""
    from ..services.bot_evaluator import get_bot_evaluator
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    evaluator = get_bot_evaluator(db)
    history = evaluator.get_signal_history(bot, limit)
    
    return {
        "bot_id": bot.id,
        "bot_name": bot.name,
        "signal_history": history,
        "total_entries": len(history)
    }


@router.post("/{bot_id}/reset-confirmation")
def reset_bot_confirmation(bot_id: int, db: Session = Depends(get_db)):
    """Reset the signal confirmation timer for a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Reset confirmation start time
    bot.signal_confirmation_start = None
    db.commit()
    
    return {
        "bot_id": bot.id,
        "bot_name": bot.name,
        "message": "Confirmation timer reset successfully"
    }



def calculate_distance_to_signal(combined_score: float) -> float:
    """Calculate how far the bot is from a trading signal."""
    # Assuming buy threshold is 0.7 and sell threshold is -0.7
    buy_threshold = 0.7
    sell_threshold = -0.7
    
    if combined_score > 0:
        # Distance to buy signal
        return max(0, buy_threshold - combined_score)
    else:
        # Distance to sell signal
        return max(0, abs(sell_threshold) - abs(combined_score))
