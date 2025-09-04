from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import logging
from datetime import datetime
from ..core.database import get_db
from ..models.models import Bot, BotSignalHistory
from ..api.schemas import BotCreate, BotUpdate, BotResponse, BotStatusResponse
from ..utils.temperature import calculate_bot_temperature

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[BotResponse])
def get_bots(db: Session = Depends(get_db)):
    """Get all bots."""
    bots = db.query(Bot).all()
    
    # Convert signal_config from JSON string to dict
    for bot in bots:
        try:
            bot.signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
        except json.JSONDecodeError:
            bot.signal_config = {}
    
    return bots


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
    
    # Convert signal_config from JSON string to dict
    try:
        bot.signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
    except json.JSONDecodeError:
        bot.signal_config = {}
    
    return bot


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
            # Use mock data as fallback
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
            # Get fresh evaluation for this bot
            market_data = market_data_cache.get(bot.pair)
            if market_data is not None and not market_data.empty:
                temp_data = evaluator.calculate_bot_temperature(bot, market_data)
                fresh_score = temp_data.get('score', 0.0)
                temperature = temp_data.get('temperature', 'FROZEN')
                distance_to_signal = temp_data.get('distance_to_action', 1.0)
            else:
                # Fallback to cached data if no market data available
                fresh_score = bot.current_combined_score
                temperature = calculate_bot_temperature(bot.current_combined_score)
                distance_to_signal = calculate_distance_to_signal(bot.current_combined_score)
                
            status_list.append({
                "id": bot.id,
                "name": bot.name,
                "pair": bot.pair,
                "status": bot.status,
                "current_combined_score": fresh_score,
                "current_position_size": bot.current_position_size,
                "temperature": temperature,
                "distance_to_signal": distance_to_signal
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
