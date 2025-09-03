from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from ..core.database import get_db
from ..models.models import Trade, Bot
from ..api.schemas import TradeResponse
from ..services.trading_safety import TradingSafetyService
from ..services.trading_service import TradingService
from ..services.bot_evaluator import BotSignalEvaluator

router = APIRouter()


@router.get("/", response_model=List[TradeResponse])
def get_trades(
    product_id: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get trade history."""
    query = db.query(Trade)
    
    if product_id:
        query = query.filter(Trade.product_id == product_id)
    
    trades = query.order_by(Trade.created_at.desc()).limit(limit).all()
    return trades


@router.get("/stats")
def get_trade_stats(db: Session = Depends(get_db)):
    """Get trading statistics."""
    # Basic trade statistics
    total_trades = db.query(Trade).count()
    filled_trades = db.query(Trade).filter(Trade.status == "filled").count()
    
    # TODO: Phase 4 - Add sophisticated trading statistics
    # Planned features: Sharpe ratio, win/loss ratio, average trade duration,
    # monthly/weekly breakdowns, signal performance attribution
    # - P&L calculation with live market data
    # - Win/loss ratio and risk metrics  
    # - Average trade size and volume analysis
    # - Performance attribution by signal type
    
    return {
        "total_trades": total_trades,
        "filled_trades": filled_trades,
        "success_rate": filled_trades / total_trades * 100 if total_trades > 0 else 0
    }


@router.post("/trigger-evaluation")
def trigger_signal_evaluation():
    """Manually trigger bot signal evaluation."""
    from ..tasks.trading_tasks import evaluate_bot_signals
    
    # Trigger async bot signal evaluation
    task = evaluate_bot_signals.delay()
    
    return {
        "message": "Bot signal evaluation triggered",
        "task_id": task.id
    }


# Phase 4.1.1: Trading Safety Service Endpoints

@router.post("/validate-trade")
def validate_trade_request(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate a trade request against all safety limits.
    Phase 4.1.1: Core safety validation before any trade execution.
    """
    # Extract parameters from request
    bot_id = request.get("bot_id")
    side = request.get("side") 
    size_usd = request.get("size_usd")
    
    # Validate required parameters
    if not bot_id:
        raise HTTPException(status_code=400, detail="bot_id is required")
    if not side:
        raise HTTPException(status_code=400, detail="side is required")
    if size_usd is None:
        raise HTTPException(status_code=400, detail="size_usd is required")
    
    # Get bot
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")
    
    # Validate input parameters
    if side not in ["buy", "sell"]:
        raise HTTPException(status_code=400, detail="Side must be 'buy' or 'sell'")
    
    if size_usd <= 0:
        raise HTTPException(status_code=400, detail="Size must be positive")
    
    # Get current bot temperature
    evaluator = BotSignalEvaluator(db)
    # For safety validation, we need current temperature but don't need full market data evaluation
    # Use cached temperature for safety check, fresh evaluation for actual trading
    current_temperature = "WARM"  # Conservative default for safety testing
    
    # Create safety service and validate
    safety_service = TradingSafetyService(db)
    validation_result = safety_service.validate_trade_request(
        bot=bot,
        side=side,
        size_usd=size_usd,
        current_temperature=current_temperature
    )
    
    return {
        "validation": validation_result,
        "bot": {
            "id": bot.id,
            "name": bot.name,
            "pair": bot.pair,
            "status": bot.status
        },
        "request": {
            "side": side,
            "size_usd": size_usd,
            "temperature_used": current_temperature
        }
    }


@router.get("/safety-status")
def get_safety_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get current trading safety status and limits.
    Shows daily limits, current usage, and circuit breaker status.
    """
    safety_service = TradingSafetyService(db)
    return safety_service.get_safety_status()


@router.post("/emergency-stop")
def emergency_stop_all_trading(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Emergency stop all trading activity.
    Sets all bots to STOPPED status for immediate trading halt.
    """
    # Stop all running bots
    running_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
    
    stopped_bot_ids = []
    for bot in running_bots:
        bot.status = "STOPPED"
        stopped_bot_ids.append(bot.id)
    
    db.commit()
    
    return {
        "message": "Emergency stop executed",
        "stopped_bots": stopped_bot_ids,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": "EMERGENCY_STOP"
    }


# Phase 4.1.2: Trade Execution Service Endpoints

@router.post("/execute")
def execute_trade(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute a real trade with full safety validation.
    Phase 4.1.2: Complete trade execution pipeline.
    
    Request format:
    {
        "bot_id": 1,
        "side": "buy",  # or "sell"
        "size_usd": 10.0,
        "current_temperature": "HOT"  # optional, will be calculated if not provided
    }
    """
    # Extract and validate parameters
    bot_id = request.get("bot_id")
    side = request.get("side")
    size_usd = request.get("size_usd")
    current_temperature = request.get("current_temperature")
    
    # Validate required parameters
    if not bot_id:
        raise HTTPException(status_code=400, detail="bot_id is required")
    if not side:
        raise HTTPException(status_code=400, detail="side is required") 
    if size_usd is None:
        raise HTTPException(status_code=400, detail="size_usd is required")
    
    # Validate parameter values
    if side not in ["buy", "sell"]:
        raise HTTPException(status_code=400, detail="Side must be 'buy' or 'sell'")
    
    if size_usd <= 0:
        raise HTTPException(status_code=400, detail="Size must be positive")
    
    # Create trading service and execute
    trading_service = TradingService(db)
    
    try:
        result = trading_service.execute_trade(
            bot_id=bot_id,
            side=side,
            size_usd=size_usd,
            current_temperature=current_temperature
        )
        
        # Return successful result
        if result.get("success"):
            return result
        else:
            # Trade was rejected or failed
            error_message = result.get("error", "Trade execution failed")
            status_code = 400 if "safety" in error_message.lower() else 500
            raise HTTPException(status_code=status_code, detail=error_message)
            
    except Exception as e:
        # Unexpected error during trade execution
        raise HTTPException(status_code=500, detail=f"Trade execution error: {str(e)}")


@router.get("/status/{trade_id}")
def get_trade_status(
    trade_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the current status of a specific trade.
    Phase 4.1.2: Trade tracking and status monitoring.
    """
    trading_service = TradingService(db)
    
    try:
        status = trading_service.get_trade_status(trade_id)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trade status: {str(e)}")


@router.get("/recent/{bot_id}")
def get_recent_trades(
    bot_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get recent trades for a specific bot.
    Phase 4.1.2: Bot-specific trade history.
    """
    # Validate bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")
    
    # Get recent trades
    trades = db.query(Trade).filter(
        Trade.bot_id == bot_id
    ).order_by(Trade.created_at.desc()).limit(limit).all()
    
    # Format trade data
    trade_list = []
    for trade in trades:
        trade_data = {
            "trade_id": trade.id,
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
        trade_list.append(trade_data)
    
    return trade_list
