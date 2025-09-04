from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.database import get_db
from ..models.models import Trade, Bot
from ..api.schemas import TradeResponse
from ..services.trading_safety import TradingSafetyService
from ..services.trading_service import TradingService
from ..services.bot_evaluator import BotSignalEvaluator
from ..services.position_service import PositionService, TrancheStrategy

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
    
    # Note: Advanced trading statistics are available through dedicated endpoints:
    # - Position analysis: /api/v1/positions/analysis/{bot_id}
    # - Performance metrics: /api/v1/positions/performance/{bot_id}
    # - Safety status: /api/v1/trades/safety-status
    # - DCA metrics: /api/v1/positions/dca-impact/{bot_id}
    
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
            "combined_signal_score": trade.combined_signal_score,
            # Phase 4.1.3: Enhanced position fields
            "tranche_number": getattr(trade, 'tranche_number', None),
            "position_status": getattr(trade, 'position_status', None),
            "size_usd": getattr(trade, 'size_usd', None)
        }
        trade_list.append(trade_data)
    
    return trade_list


# Phase 4.1.3: Enhanced Position Management Endpoints

@router.get("/position/{bot_id}")
def get_bot_position(bot_id: int, db: Session = Depends(get_db)):
    """
    Get comprehensive position summary for a bot including all tranches.
    
    Returns position status, tranches, average entry price, and P&L.
    """
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    position_service = PositionService(db)
    position_summary = position_service.get_position_summary(bot_id)
    
    if "error" in position_summary:
        raise HTTPException(status_code=500, detail=position_summary["error"])
    
    return {
        "bot_id": bot_id,
        "bot_name": bot.name,
        "pair": bot.pair,
        "position": position_summary,
        "retrieved_at": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/position/{bot_id}/can-add-tranche")
def check_tranche_capacity(bot_id: int, db: Session = Depends(get_db)):
    """
    Check if bot can add another tranche to its position.
    
    Returns whether a new tranche can be added and the reason.
    """
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    position_service = PositionService(db)
    can_add, reason = position_service.can_add_tranche(bot_id)
    
    return {
        "bot_id": bot_id,
        "can_add_tranche": can_add,
        "reason": reason,
        "max_tranches": position_service.MAX_TRANCHES_PER_POSITION,
        "checked_at": datetime.utcnow().isoformat() + "Z"
    }


# Phase 4.1.3 Day 2: Advanced Position Management Endpoints

@router.post("/position/{bot_id}/calculate-tranche-size")
def calculate_optimal_tranche_size(
    bot_id: int,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Calculate optimal tranche size based on strategy and market conditions.
    
    Request body:
    {
        "current_price": 50000.0,
        "strategy": "adaptive",  // "equal_size", "pyramid_up", "pyramid_down", "adaptive"
        "market_conditions": {
            "volatility": 0.25,
            "trend": "bullish"
        }
    }
    """
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    current_price = request.get("current_price")
    if not current_price:
        raise HTTPException(status_code=400, detail="current_price is required")
    
    strategy_str = request.get("strategy", "adaptive")
    try:
        strategy = TrancheStrategy(strategy_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid strategy: {strategy_str}")
    
    market_conditions = request.get("market_conditions")
    
    position_service = PositionService(db)
    optimal_size, reasoning = position_service.calculate_optimal_tranche_size(
        bot_id, current_price, strategy, market_conditions
    )
    
    return {
        "bot_id": bot_id,
        "current_price": current_price,
        "strategy": strategy_str,
        "optimal_size_usd": optimal_size,
        "reasoning": reasoning,
        "calculated_at": datetime.utcnow().isoformat() + "Z"
    }


@router.post("/position/{bot_id}/analyze-dca-impact")
def analyze_dollar_cost_average_impact(
    bot_id: int,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Analyze the impact of adding a new tranche on dollar-cost averaging.
    
    Request body:
    {
        "new_price": 49000.0,
        "new_size_usd": 150.0
    }
    """
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    new_price = request.get("new_price")
    new_size_usd = request.get("new_size_usd")
    
    if new_price is None:
        raise HTTPException(status_code=400, detail="new_price is required")
    if new_size_usd is None:
        raise HTTPException(status_code=400, detail="new_size_usd is required")
    
    position_service = PositionService(db)
    dca_metrics = position_service.calculate_dollar_cost_average_metrics(
        bot_id, new_price, new_size_usd
    )
    
    if "error" in dca_metrics:
        raise HTTPException(status_code=500, detail=dca_metrics["error"])
    
    return {
        "bot_id": bot_id,
        "impact_analysis": dca_metrics,
        "analyzed_at": datetime.utcnow().isoformat() + "Z"
    }


@router.post("/position/{bot_id}/partial-exit-strategy")
def calculate_partial_exit_strategy(
    bot_id: int,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Calculate optimal partial exit strategy for a position.
    
    Request body:
    {
        "exit_percentage": 0.5,  // 50% of position
        "current_price": 52000.0
    }
    """
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    exit_percentage = request.get("exit_percentage")
    current_price = request.get("current_price")
    
    if exit_percentage is None:
        raise HTTPException(status_code=400, detail="exit_percentage is required")
    if current_price is None:
        raise HTTPException(status_code=400, detail="current_price is required")
    
    if not (0 < exit_percentage <= 1):
        raise HTTPException(status_code=400, detail="exit_percentage must be between 0 and 1")
    
    position_service = PositionService(db)
    exit_strategy = position_service.calculate_partial_exit_strategy(
        bot_id, exit_percentage, current_price
    )
    
    if "error" in exit_strategy:
        raise HTTPException(status_code=500, detail=exit_strategy["error"])
    
    return {
        "bot_id": bot_id,
        "exit_strategy": exit_strategy,
        "calculated_at": datetime.utcnow().isoformat() + "Z"
    }


@router.post("/position/{bot_id}/optimize-scaling")
def optimize_position_scaling(
    bot_id: int,
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Get position scaling recommendations based on market signal strength.
    
    Request body:
    {
        "market_signal_strength": 0.75  // -1.0 to 1.0
    }
    """
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    signal_strength = request.get("market_signal_strength")
    if signal_strength is None:
        raise HTTPException(status_code=400, detail="market_signal_strength is required")
    
    if not (-1.0 <= signal_strength <= 1.0):
        raise HTTPException(status_code=400, detail="market_signal_strength must be between -1.0 and 1.0")
    
    position_service = PositionService(db)
    scaling_recommendations = position_service.optimize_position_scaling(bot_id, signal_strength)
    
    if "error" in scaling_recommendations:
        raise HTTPException(status_code=500, detail=scaling_recommendations["error"])
    
    return {
        "bot_id": bot_id,
        "signal_strength": signal_strength,
        "recommendations": scaling_recommendations,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }


@router.get("/position/{bot_id}/performance-analysis")
def analyze_position_performance(
    bot_id: int,
    current_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive position performance analysis with advanced metrics.
    
    Query parameters:
    - current_price: Current market price for P&L calculations (optional, will use last trade price if not provided)
    """
    # Verify bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # If no current price provided, get the latest trade price
    if current_price is None:
        latest_trade = db.query(Trade).filter(
            Trade.bot_id == bot_id,
            Trade.status == "filled"
        ).order_by(Trade.created_at.desc()).first()
        
        if latest_trade:
            current_price = latest_trade.price
        else:
            raise HTTPException(status_code=400, detail="No price data available, please provide current_price")
    
    position_service = PositionService(db)
    performance_analysis = position_service.analyze_position_performance(bot_id, current_price)
    
    if "error" in performance_analysis:
        raise HTTPException(status_code=500, detail=performance_analysis["error"])
    
    return {
        "bot_id": bot_id,
        "bot_name": bot.name,
        "pair": bot.pair,
        "analysis": performance_analysis,
        "analyzed_at": datetime.utcnow().isoformat() + "Z"
    }


# =================================================================================
# PHASE 4.1.3 DAY 3: INTELLIGENT TRADING API ENDPOINTS 🧠
# =================================================================================

@router.post("/execute-intelligent")
def execute_intelligent_trade(
    bot_id: int,
    side: str,
    size_usd: Optional[float] = None,
    auto_size: bool = True,
    current_temperature: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    PHASE 4.1.3 DAY 3: Execute intelligent trade with advanced algorithms.
    Features smart sizing, temperature-based scaling, and comprehensive analytics.
    """
    # Validate inputs
    if side.upper() not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="Side must be 'BUY' or 'SELL'")
    
    if not auto_size and size_usd is None:
        raise HTTPException(status_code=400, detail="size_usd required when auto_size=False")
    
    # Initialize intelligent trading service
    trading_service = TradingService(db)
    
    try:
        result = trading_service.execute_trade(
            bot_id=bot_id,
            side=side.upper(),
            size_usd=size_usd,
            current_temperature=current_temperature,
            auto_size=auto_size
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Intelligent trade executed successfully",
                "result": result,
                "endpoint": "execute-intelligent"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Trade execution failed: {result['error']}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligent trade execution failed: {str(e)}")


@router.post("/execute-automated")
def execute_automated_position_building(
    bot_id: int,
    strategy: str = "ADAPTIVE",
    db: Session = Depends(get_db)
):
    """
    PHASE 4.1.3 DAY 3: Execute automated position building.
    Let the AI decide when and how to trade based on current conditions.
    """
    # Validate strategy
    valid_strategies = ["ADAPTIVE", "AGGRESSIVE", "CONSERVATIVE"]
    if strategy.upper() not in valid_strategies:
        raise HTTPException(
            status_code=400, 
            detail=f"Strategy must be one of: {', '.join(valid_strategies)}"
        )
    
    # Initialize intelligent trading service
    trading_service = TradingService(db)
    
    try:
        result = trading_service.execute_automated_position_building(
            bot_id=bot_id,
            strategy=strategy.upper()
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Automated {strategy} strategy executed",
                "result": result,
                "endpoint": "execute-automated"
            }
        else:
            return {
                "success": False,
                "message": f"Automation held: {result['reason']}",
                "result": result,
                "endpoint": "execute-automated"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Automated position building failed: {str(e)}")


@router.get("/intelligent-analysis/{bot_id}")
def get_intelligent_trading_analysis(
    bot_id: int,
    db: Session = Depends(get_db)
):
    """
    PHASE 4.1.3 DAY 3: Get comprehensive intelligent trading analysis.
    Provides insights on optimal sizing, strategies, and market conditions.
    """
    # Validate bot exists
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    try:
        # Initialize services
        trading_service = TradingService(db)
        position_service = PositionService(db)
        
        # Get current bot temperature
        current_temperature = trading_service._get_bot_temperature(bot)
        
        # Get position summary
        position_summary = position_service.get_position_summary(bot_id)
        
        # Analyze automation readiness
        automation_analysis = trading_service._analyze_automation_readiness(
            bot, position_summary, current_temperature
        )
        
        # Calculate intelligent sizing for both buy and sell
        buy_sizing = trading_service._calculate_intelligent_trade_size(
            bot, "BUY", current_temperature
        )
        
        sell_sizing = trading_service._calculate_intelligent_trade_size(
            bot, "SELL", current_temperature  
        )
        
        # Generate strategy recommendations
        adaptive_decision = trading_service._adaptive_strategy_decision(
            bot.current_combined_score, 
            abs(bot.current_combined_score),
            position_summary.get("total_tranches", 0),
            current_temperature
        )
        
        return {
            "bot_id": bot_id,
            "bot_name": bot.name,
            "pair": bot.pair,
            "analysis": {
                "current_conditions": {
                    "temperature": current_temperature,
                    "signal_score": bot.current_combined_score,
                    "signal_strength": abs(bot.current_combined_score)
                },
                "position_summary": position_summary,
                "automation_readiness": automation_analysis,
                "intelligent_sizing": {
                    "buy_recommendation": buy_sizing,
                    "sell_recommendation": sell_sizing
                },
                "strategy_recommendation": adaptive_decision
            },
            "analyzed_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligent analysis failed: {str(e)}")


@router.post("/batch-automated")
def execute_batch_automated_trading(
    strategy: str = "ADAPTIVE",
    bot_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """
    PHASE 4.1.3 DAY 3: Execute automated trading across multiple bots.
    Perfect for running automated strategies across entire portfolio.
    """
    # Validate strategy
    valid_strategies = ["ADAPTIVE", "AGGRESSIVE", "CONSERVATIVE"]
    if strategy.upper() not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Strategy must be one of: {', '.join(valid_strategies)}"
        )
    
    try:
        # Get bots to process
        if bot_ids:
            bots = db.query(Bot).filter(Bot.id.in_(bot_ids)).all()
        else:
            # Process all running bots
            bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
        
        if not bots:
            raise HTTPException(status_code=404, detail="No eligible bots found")
        
        # Initialize trading service
        trading_service = TradingService(db)
        
        # Execute automation for each bot
        batch_results = []
        successful_trades = 0
        held_decisions = 0
        
        for bot in bots:
            try:
                result = trading_service.execute_automated_position_building(
                    bot_id=bot.id,
                    strategy=strategy.upper()
                )
                
                batch_results.append({
                    "bot_id": bot.id,
                    "bot_name": bot.name,
                    "result": result
                })
                
                if result["success"] and result.get("action") == "TRADE_EXECUTED":
                    successful_trades += 1
                elif result["success"] and result.get("action") == "HOLD":
                    held_decisions += 1
                    
            except Exception as e:
                batch_results.append({
                    "bot_id": bot.id,
                    "bot_name": bot.name,
                    "result": {"success": False, "error": str(e)}
                })
        
        return {
            "success": True,
            "message": f"Batch automation completed: {successful_trades} trades, {held_decisions} holds",
            "strategy": strategy.upper(),
            "summary": {
                "total_bots": len(bots),
                "successful_trades": successful_trades,
                "held_decisions": held_decisions,
                "errors": len(batch_results) - successful_trades - held_decisions
            },
            "detailed_results": batch_results,
            "executed_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch automated trading failed: {str(e)}")

# =================================================================================
# END PHASE 4.1.3 DAY 3 INTELLIGENT TRADING API ENDPOINTS
# =================================================================================
