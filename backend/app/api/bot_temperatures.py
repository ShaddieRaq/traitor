"""
Bot temperature API endpoints for Phase 3.2.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import logging

from ..core.database import get_db
from ..models.models import Bot
from ..services.bot_evaluator import get_bot_evaluator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
def get_all_bot_temperatures(db: Session = Depends(get_db)):
    """Get temperature status for all bots."""
    evaluator = get_bot_evaluator(db)
    
    # Get market data for all running bots using centralized utility
    from ..utils.market_data_helper import create_market_data_cache
    bots = db.query(Bot).filter(Bot.status == 'RUNNING').all()
    
    # Fetch market data for each unique trading pair
    unique_pairs = list(set(bot.pair for bot in bots))
    market_data_cache = create_market_data_cache(unique_pairs, granularity=3600, limit=100)
    
    temperatures = evaluator.get_all_bot_temperatures(market_data_cache)
    
    return {
        "timestamp": pd.Timestamp.now().isoformat(),
        "bot_count": len(temperatures),
        "temperatures": temperatures
    }


@router.get("/dashboard")
def get_bot_dashboard_summary(db: Session = Depends(get_db)):
    """Get summary data for bot dashboard including temperatures."""
    evaluator = get_bot_evaluator(db)
    
    # Get all bots
    bots = db.query(Bot).all()
    bot_count = len(bots)
    running_count = len([b for b in bots if b.status == 'RUNNING'])
    
    # Get market data for running bots using centralized utility  
    from ..utils.market_data_helper import create_market_data_cache
    running_bots = [b for b in bots if b.status == 'RUNNING']
    
    # Fetch market data for each unique trading pair
    unique_pairs = list(set(bot.pair for bot in running_bots))
    market_data_cache = create_market_data_cache(unique_pairs, granularity=3600, limit=100)
    
    # Get temperatures for running bots with real market data
    temperatures = evaluator.get_all_bot_temperatures(market_data_cache)
    
    # Categorize by temperature
    temp_counts = {
        'hot': len([t for t in temperatures if t.get('temperature') == 'HOT']),
        'warm': len([t for t in temperatures if t.get('temperature') == 'WARM']),
        'cool': len([t for t in temperatures if t.get('temperature') == 'COOL']),
        'frozen': len([t for t in temperatures if t.get('temperature') == 'FROZEN']),
        'error': len([t for t in temperatures if t.get('temperature') == 'error'])
    }
    
    return {
        "timestamp": pd.Timestamp.now().isoformat(),
        "total_bots": bot_count,
        "running_bots": running_count,
        "stopped_bots": bot_count - running_count,
        "temperature_breakdown": temp_counts,
        "bot_temperatures": temperatures
    }


@router.get("/{bot_id}")
def get_bot_temperature(bot_id: int, db: Session = Depends(get_db)):
    """Get bot temperature status based on signal proximity to thresholds."""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    evaluator = get_bot_evaluator(db)
    
    # Get real market data from Coinbase
    try:
        from ..services.coinbase_service import coinbase_service
        market_data = coinbase_service.get_historical_data(bot.pair, granularity=3600, limit=100)
        
        if market_data.empty:
            # Use fallback data if API returns empty result
            market_data = pd.DataFrame({
                'close': [100.0],
                'high': [101.0],
                'low': [99.0], 
                'open': [100.5],
                'volume': [1000]
            })
    except Exception as e:
        # Use fallback data if API unavailable
        logger.warning(f"Failed to get market data for {bot.pair}: {e}")
        market_data = pd.DataFrame({
            'close': [100.0],
            'high': [101.0],
            'low': [99.0], 
            'open': [100.5],
            'volume': [1000]
        })
    
    temperature_data = evaluator.calculate_bot_temperature(bot, market_data)
    
    return {
        "bot_id": bot.id,
        "bot_name": bot.name,
        "pair": bot.pair,
        "status": bot.status,
        **temperature_data
    }
