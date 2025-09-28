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
                buy_threshold=-0.1,
                sell_threshold=0.1
            )
        
        thresholds_data = signal_config['trading_thresholds']
        return TradingThresholds(
            buy_threshold=thresholds_data.get('buy_threshold', -0.1),
            sell_threshold=thresholds_data.get('sell_threshold', 0.1),
            optimization_applied=thresholds_data.get('optimization_applied'),
            applied_date=thresholds_data.get('applied_date')
        )
    except Exception as e:
        logger.warning(f"Error extracting trading thresholds: {e}")
        return TradingThresholds(
            buy_threshold=-0.1,
            sell_threshold=0.1
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
    # Check if bot name already exists
    existing_bot = db.query(Bot).filter(Bot.name == bot.name).first()
    if existing_bot:
        raise HTTPException(status_code=400, detail="Bot name already exists")
    
    # Convert signal config to JSON
    signal_config_json = {}
    if bot.signal_config:
        if hasattr(bot.signal_config, 'dict'):
            signal_config_json = bot.signal_config.model_dump()
        else:
            signal_config_json = bot.signal_config
    
    # Create new bot
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
        signal_config=json.dumps(signal_config_json)
    )
    
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    
    # Convert signal_config back to dict for response
    db_bot.signal_config = json.loads(db_bot.signal_config) if db_bot.signal_config else {}
    
    return db_bot


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
    
    # Convert signal_config back to dict for response
    bot.signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
    
    return bot


@router.delete("/{bot_id}")
def delete_bot(bot_id: int, db: Session = Depends(get_db)):
    """Delete a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    db.delete(bot)
    db.commit()
    
    return {"message": "Bot deleted successfully"}


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
    from ..services.coinbase_service import coinbase_service
    import pandas as pd
    
    bots = db.query(Bot).all()
    evaluator = get_bot_evaluator(db)
    
    # Get fresh market data for all unique trading pairs
    market_data_cache = {}
    unique_pairs = set(bot.pair for bot in bots)
    for pair in unique_pairs:
        try:
            market_data_cache[pair] = coinbase_service.get_historical_data(pair, granularity=3600, limit=100)
        except Exception as e:
            logger.warning(f"Failed to get market data for {pair}: {e}")
            # Use fallback data if API unavailable
            market_data_cache[pair] = pd.DataFrame({
                'close': [100.0],
                'high': [101.0],
                'low': [99.0], 
                'open': [100.5],
                'volume': [1000]
            })
    
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
                
            # Check balance status for UI display
            balance_status = {"valid": True, "message": ""}
            try:
                # Get current market price for balance validation
                ticker = coinbase_service.get_product_ticker(bot.pair)
                if ticker and 'price' in ticker:
                    current_price = float(ticker['price'])
                    # Check both buy and sell scenarios
                    buy_balance = coinbase_service.validate_trade_balance(bot.pair, "BUY", bot.position_size_usd, current_price)
                    sell_balance = coinbase_service.validate_trade_balance(bot.pair, "SELL", bot.position_size_usd, current_price)
                    
                    if not buy_balance["valid"] and not sell_balance["valid"]:
                        balance_status = {"valid": False, "message": f"⚠️ Cannot buy or sell: {buy_balance['message']}"}
                    elif not buy_balance["valid"]:
                        balance_status = {"valid": False, "message": f"⚠️ Cannot buy: {buy_balance['message']}"}
                    elif not sell_balance["valid"]:
                        balance_status = {"valid": False, "message": f"⚠️ Cannot sell: {sell_balance['message']}"}
                    else:
                        balance_status = {"valid": True, "message": "✅ Sufficient balance for trading"}
            except Exception as balance_error:
                logger.warning(f"Balance check failed for bot {bot.id}: {balance_error}")
                balance_status = {"valid": False, "message": "⚠️ Unable to verify balance"}
                
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
    
    # Get cached market data for all unique trading pairs (avoid rate limits)
    from ..services.market_data_cache import MarketDataCache
    market_cache = MarketDataCache()
    market_data_cache = {}
    unique_pairs = set(bot.pair for bot in bots)
    
    for pair in unique_pairs:
        try:
            # Use cached market data with proper fetch function
            def fetch_func():
                return coinbase_service.get_historical_data(pair, granularity=3600, limit=100)
                
            cached_data = market_cache.get_or_fetch(pair, granularity=3600, limit=100, fetch_func=fetch_func)
            if cached_data is not None and not cached_data.empty:
                market_data_cache[pair] = cached_data
                logger.debug(f"✅ Using cached market data for {pair} ({len(cached_data)} candles)")
            else:
                # Fallback data if cache returns empty
                logger.warning(f"⚠️ Empty data for {pair}, using fallback data")
                market_data_cache[pair] = pd.DataFrame({
                    'close': [100.0], 'high': [101.0], 'low': [99.0], 
                    'open': [100.5], 'volume': [1000]
                })
        except Exception as e:
            logger.error(f"❌ Failed to get cached data for {pair}: {e}")
            # Use fallback data if cache unavailable
            market_data_cache[pair] = pd.DataFrame({
                'close': [100.0], 'high': [101.0], 'low': [99.0], 
                'open': [100.5], 'volume': [1000]
            })
    
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
            if next_action != "hold" and bot.status == 'RUNNING':
                try:
                    from ..services.trading_safety import TradingSafetyService
                    safety_service = TradingSafetyService(db)
                    price_step_ok = safety_service._check_price_step(bot, next_action.upper(), bot.position_size_usd)
                    if not price_step_ok:
                        price_step_blocking_reason = f"Price step requirement not met ({bot.trade_step_pct or 2.0}%)"
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
                position_size_usd=actual_position_usd,  # Provide both fields for compatibility
                temperature=temperature,
                distance_to_signal=distance_to_signal,
                trading_intent=trading_intent,
                confirmation=confirmation,
                trade_readiness=trade_readiness,
                last_trade=last_trade,
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
                trading_intent=TradingIntent(next_action="hold", signal_strength=0.0, confidence=0.0, distance_to_threshold=1.0),
                confirmation=ConfirmationStatus(is_active=False),
                trade_readiness=TradeReadiness(status="no_signal", can_trade=False),
                last_trade=None,
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
