"""
Bot temperature API endpoints for Phase 3.2.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

from ..core.database import get_db
from ..models.models import Bot
from ..services.bot_evaluator import get_bot_evaluator

router = APIRouter()


@router.get("/")
def get_all_bot_temperatures(db: Session = Depends(get_db)):
    """Get temperature status for all bots."""
    evaluator = get_bot_evaluator(db)
    temperatures = evaluator.get_all_bot_temperatures()
    
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
    
    # Get temperatures for running bots
    temperatures = evaluator.get_all_bot_temperatures()
    
    # Categorize by temperature
    temp_counts = {
        'hot': len([t for t in temperatures if t.get('temperature') == 'hot']),
        'warm': len([t for t in temperatures if t.get('temperature') == 'warm']),
        'cool': len([t for t in temperatures if t.get('temperature') == 'cool']),
        'frozen': len([t for t in temperatures if t.get('temperature') == 'frozen']),
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
    
    # Create mock market data for temperature calculation
    # In real implementation, this would come from live market data
    market_data = pd.DataFrame({
        'close': [100.0],  # Mock current price
        'high': [101.0],
        'low': [99.0], 
        'open': [100.5],
        'volume': [1000]
    })
    
    evaluator = get_bot_evaluator(db)
    temperature_data = evaluator.calculate_bot_temperature(bot, market_data)
    
    return {
        "bot_id": bot.id,
        "bot_name": bot.name,
        "pair": bot.pair,
        "status": bot.status,
        **temperature_data
    }
