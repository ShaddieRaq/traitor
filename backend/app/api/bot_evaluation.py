"""
Bot evaluation API endpoints for testing signal aggregation.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from ..core.database import get_db
from ..models.models import Bot
from ..services.bot_evaluator import BotSignalEvaluator
from ..services.coinbase_service import coinbase_service

router = APIRouter(tags=["Bot Evaluation"])


@router.post("/{bot_id}/evaluate")
def evaluate_bot_signals(
    bot_id: int,
    timeframe: str = "1h",
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Evaluate a bot's signals using recent market data.
    
    Args:
        bot_id: ID of bot to evaluate
        timeframe: Timeframe for market data (1h, 4h, 1d)
        limit: Number of data points to retrieve
        
    Returns:
        Signal evaluation result with aggregated scores
    """
    # Get bot
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Get market data for bot's trading pair
    try:
        # Map timeframe to seconds for Coinbase API
        timeframe_map = {
            "1h": 3600,
            "4h": 14400, 
            "1d": 86400
        }
        granularity = timeframe_map.get(timeframe, 3600)
        
        market_data = coinbase_service.get_historical_data(
            product_id=bot.pair,
            granularity=granularity,
            limit=limit
        )
        
        if market_data.empty:
            raise HTTPException(status_code=400, detail="No market data available")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")
    
    # Evaluate bot signals
    evaluator = BotSignalEvaluator(db)
    try:
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Add market data context to result
        result['market_context'] = {
            'pair': bot.pair,
            'timeframe': timeframe,
            'data_points': len(market_data),
            'price_range': {
                'current': float(market_data['close'].iloc[-1]),
                'high': float(market_data['close'].max()),
                'low': float(market_data['close'].min()),
                'change_pct': float((market_data['close'].iloc[-1] - market_data['close'].iloc[0]) / market_data['close'].iloc[0] * 100)
            }
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal evaluation failed: {str(e)}")


@router.get("/test/{bot_id}")
async def test_bot_evaluation(bot_id: int, db: Session = Depends(get_db)):
    """Test signal evaluation for a specific bot with sample market data."""
    # Get bot
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Get market data from Coinbase
    try:
        from ..services.coinbase_service import CoinbaseService
        coinbase = CoinbaseService()
        
        # Convert time interval to seconds for Coinbase API
        granularity_seconds = 60  # 1 minute intervals
        market_data = coinbase.get_historical_data(bot.pair, granularity_seconds, 50)
        
        if market_data.empty:
            raise HTTPException(status_code=503, detail="Unable to fetch market data")
        
        # Evaluate bot signals
        evaluator = BotSignalEvaluator(db)
        result = evaluator.evaluate_bot(bot, market_data)
        
        return {
            "bot_id": bot_id,
            "bot_name": bot.name,
            "pair": bot.pair,
            "market_data_points": len(market_data),
            "latest_price": float(market_data['close'].iloc[-1]),
            "evaluation": {
                "overall_score": result["overall_score"],
                "action": result["action"],
                "confidence": result["confidence"],
                "signal_results": result["signal_results"],
                "metadata": result["metadata"]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error evaluating bot signals: {str(e)}"
        )


@router.post("/{bot_id}/simulate-automatic-trade")
def simulate_automatic_trade(
    bot_id: int,
    action: str,  # 'buy' or 'sell'
    db: Session = Depends(get_db)
):
    """
    Simulate automatic trade execution for testing Phase 4.2.1 functionality.
    
    Args:
        bot_id: ID of bot to test
        action: Trade action to simulate ('buy' or 'sell')
    """
    # Validate action
    if action not in ['buy', 'sell']:
        raise HTTPException(status_code=400, detail="Action must be 'buy' or 'sell'")
    
    # Get bot
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    try:
        # Create evaluator with confirmation disabled for testing
        evaluator = BotSignalEvaluator(db, enable_confirmation=False)
        
        # Get current market data for temperature calculation
        try:
            market_data = coinbase_service.get_historical_data(bot.pair, timeframe="1h", limit=100)
        except Exception as e:
            # Create minimal market data if service fails
            market_data = pd.DataFrame({
                'close': [50000, 50100, 50200],
                'volume': [100, 100, 100]
            })
        
        # Create simulated evaluation result that would trigger automatic trade
        simulated_evaluation = {
            'overall_score': 0.5 if action == 'sell' else -0.5,
            'action': action,
            'confidence': 0.8,
            'signal_results': {},
            'confirmation_status': {
                'is_confirmed': True,  # Simulate confirmed signal
                'needs_confirmation': True,
                'status': 'confirmed',
                'action_being_confirmed': action,
                'confirmation_start': None,
                'confirmation_progress': 1.0,
                'time_remaining_minutes': 0
            },
            'metadata': {
                'bot_id': bot.id,
                'bot_name': bot.name,
                'simulation': True
            },
            'market_data': market_data  # Include market data for temperature calculation
        }
        
        # Test automatic trade execution
        if evaluator._should_execute_automatic_trade(bot, simulated_evaluation):
            trade_result = evaluator._execute_automatic_trade(bot, simulated_evaluation)
            return {
                "message": f"Simulated automatic {action} trade for bot {bot.name}",
                "bot_id": bot_id,
                "action": action,
                "trade_result": trade_result,
                "status": "executed" if trade_result.get('executed') else "failed"
            }
        else:
            return {
                "message": f"Automatic trade not triggered for bot {bot.name}",
                "bot_id": bot_id,
                "action": action,
                "status": "not_triggered",
                "reason": "Conditions not met for automatic trade"
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error simulating automatic trade: {str(e)}"
        )
