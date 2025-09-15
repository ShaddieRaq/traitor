from typing import List
import logging
from datetime import datetime
from ..core.database import SessionLocal
from ..models.models import Bot, MarketData
from ..services.coinbase_service import coinbase_service
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.trading_tasks.evaluate_bot_signals")
def evaluate_bot_signals(enable_automatic_trading: bool = False):
    """
    Evaluate trading signals for all active bots and execute automatic trades if enabled.
    
    Args:
        enable_automatic_trading: If True, enables automatic trade execution 
    """
    logger.info(f"Bot signal evaluation task triggered (auto_trading={enable_automatic_trading})")
    
    try:
        db = SessionLocal()
        try:
            # Import here to avoid circular imports
            from ..services.bot_evaluator import BotSignalEvaluator
            
            # Get all running bots
            active_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
            logger.info(f"Found {len(active_bots)} running bots for evaluation")
            
            if not active_bots:
                return {
                    "status": "no_bots", 
                    "running_bots": 0,
                    "message": "No running bots found for evaluation"
                }
            
            # Initialize evaluator
            evaluator = BotSignalEvaluator(db)
            evaluation_results = []
            
            # Cache for market data to avoid duplicate API calls
            market_data_cache = {}
            
            for i, bot in enumerate(active_bots):
                try:
                    logger.info(f"Evaluating bot {bot.id} ({bot.name}) - {i+1}/{len(active_bots)}")
                    
                    # Add delay between API calls to prevent rate limiting (except for first bot)
                    if i > 0:
                        import time
                        delay = 3  # 3 second delay between each bot evaluation
                        logger.info(f"⏳ Waiting {delay}s before next API call to prevent rate limiting...")
                        time.sleep(delay)
                    
                    # Check cache first
                    if bot.pair in market_data_cache:
                        logger.info(f"📋 Using cached market data for {bot.pair}")
                        market_data = market_data_cache[bot.pair]
                    else:
                        # Get market data for this bot's pair
                        logger.info(f"📡 Fetching fresh market data for {bot.pair}")
                        market_data = coinbase_service.get_historical_data(bot.pair)
                        market_data_cache[bot.pair] = market_data
                    
                    if market_data.empty:
                        logger.warning(f"No market data available for {bot.pair}, skipping bot {bot.id}")
                        continue
                    
                    # Evaluate bot (includes automatic trading if enabled)
                    result = evaluator.evaluate_bot(bot, market_data)
                    
                    # Store evaluation results back to the bot for UI display
                    try:
                        import json
                        from datetime import datetime
                        
                        evaluation_data = {
                            "action": result.get("action"),
                            "overall_score": result.get("overall_score"),
                            "confidence": result.get("confidence"),
                            "signal_results": result.get("signal_results"),
                            "evaluation_timestamp": datetime.now().isoformat(),
                            "market_context": result.get("market_context")
                        }
                        
                        bot.evaluation_metadata = json.dumps(evaluation_data)
                        db.commit()
                        logger.info(f"💾 Stored evaluation results for bot {bot.id}")
                        
                    except Exception as store_error:
                        logger.error(f"Failed to store evaluation results for bot {bot.id}: {store_error}")
                    
                    evaluation_results.append({
                        "bot_id": bot.id,
                        "bot_name": bot.name,
                        "action": result.get("action"),
                        "score": result.get("overall_score"),
                        "automatic_trade": result.get("automatic_trade")
                    })
                    
                    logger.info(f"Bot {bot.id} evaluation complete: action={result.get('action')}, score={result.get('overall_score'):.3f}")
                    
                except Exception as e:
                    logger.error(f"Error evaluating bot {bot.id}: {str(e)}")
                    evaluation_results.append({
                        "bot_id": bot.id,
                        "error": str(e)
                    })
            
            return {
                "status": "evaluation_complete", 
                "running_bots": len(active_bots),
                "evaluated_bots": len(evaluation_results),
                "results": evaluation_results,
                "automatic_trading": enable_automatic_trading
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in evaluate_bot_signals task: {str(e)}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.trading_tasks.fast_trading_evaluation")
def fast_trading_evaluation():
    """
    Fast trading evaluation loop - runs every 500ms for responsive trading decisions.
    Only executes trades when cooldown periods allow.
    """
    try:
        db = SessionLocal()
        try:
            # Import here to avoid circular imports
            from ..services.bot_evaluator import BotSignalEvaluator
            
            # Get all running bots
            active_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
            
            if not active_bots:
                return {"status": "no_active_bots", "running_bots": 0}
            
            # Initialize evaluator
            evaluator = BotSignalEvaluator(db)
            trade_attempts = 0
            successful_trades = 0
            
            # Cache market data to avoid redundant API calls
            market_data_cache = {}
            unique_pairs = set(bot.pair for bot in active_bots)
            for pair in unique_pairs:
                try:
                    market_data_cache[pair] = coinbase_service.get_historical_data(pair, granularity=3600, limit=100)
                except Exception as e:
                    logger.warning(f"Failed to get market data for {pair}: {e}")
                    continue
            
            for bot in active_bots:
                try:
                    # Get market data for this bot's pair
                    market_data = market_data_cache.get(bot.pair)
                    if market_data is None or market_data.empty:
                        continue
                    
                    # Evaluate bot with automatic trading enabled
                    result = evaluator.evaluate_bot(bot, market_data)
                    
                    # Store evaluation results back to the bot for UI display
                    try:
                        import json
                        from datetime import datetime
                        
                        evaluation_data = {
                            "action": result.get("action"),
                            "overall_score": result.get("overall_score"),
                            "confidence": result.get("confidence"),
                            "signal_results": result.get("signal_results"),
                            "evaluation_timestamp": datetime.now().isoformat(),
                            "market_context": result.get("market_context")
                        }
                        
                        bot.evaluation_metadata = json.dumps(evaluation_data)
                        db.commit()
                        logger.debug(f"💾 Stored evaluation results for bot {bot.id}: {result.get('action')} (score: {result.get('overall_score', 0):.3f})")
                        
                    except Exception as store_error:
                        logger.error(f"Failed to store evaluation results for bot {bot.id}: {store_error}")
                    
                    # Check if trade was attempted
                    automatic_trade = result.get("automatic_trade")
                    if automatic_trade:
                        trade_attempts += 1
                        if automatic_trade.get("executed"):
                            successful_trades += 1
                    
                except Exception as e:
                    logger.error(f"Error in fast evaluation for bot {bot.id}: {str(e)}")
                    continue
            
            return {
                "status": "fast_evaluation_complete",
                "evaluated_bots": len(active_bots),
                "trade_attempts": trade_attempts,
                "successful_trades": successful_trades,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in fast_trading_evaluation task: {str(e)}")
        return {"status": "error", "message": str(e)}


# Legacy task names for backward compatibility


@celery_app.task(name="fetch_market_data") 
def fetch_market_data(product_id: str = "BTC-USD"):
    """
    Fetch and store market data for specified product.
    """
    try:
        logger.info(f"Fetching market data for {product_id}")
        
        db = SessionLocal()
        try:
            # Get historical data from Coinbase
            df = coinbase_service.get_historical_data(product_id, granularity=3600, limit=100)
            
            if df.empty:
                logger.warning(f"No market data received for {product_id}")
                return {"status": "error", "message": "No data received"}
            
            # Store market data (implementation depends on your MarketData model structure)
            logger.info(f"Successfully fetched {len(df)} candles for {product_id}")
            return {"status": "success", "candles": len(df)}
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error fetching market data for {product_id}: {str(e)}")
        return {"status": "error", "message": str(e)}


# Legacy task names for backward compatibility
@celery_app.task(name="evaluate_signals")
def evaluate_signals():
    """Legacy task name - redirects to evaluate_bot_signals."""
    return evaluate_bot_signals()


@celery_app.task(name="fetch_data")
def fetch_data(product_id: str = "BTC-USD"):
    """Legacy task name - redirects to fetch_market_data."""
    return fetch_market_data(product_id)


@celery_app.task(name="app.tasks.trading_tasks.update_trade_statuses")
def update_trade_statuses():
    """
    Periodic task to update the status of pending trades.
    This fixes the issue where trades remain "pending" forever.
    """
    logger.info("🔄 Starting periodic trade status update task")
    
    try:
        db = SessionLocal()
        try:
            # Import here to avoid circular imports
            from ..services.trading_service import TradingService
            
            # Initialize trading service and update statuses
            trading_service = TradingService(db)
            result = trading_service.update_pending_trade_statuses()
            
            logger.info(f"✅ Trade status update completed: {result}")
            return {
                "status": "success",
                "message": f"Updated {result['updated_count']} trade statuses",
                "details": result
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error in trade status update task: {str(e)}")
        return {
            "status": "error", 
            "message": str(e)
        }


@celery_app.task(name="app.tasks.trading_tasks.monitor_order_status")
def monitor_order_status(order_id: str, trade_id: int):
    """Monitor a specific order until completion using real-time monitoring service."""
    import asyncio
    
    logger.info(f"🔍 Background monitoring started for order {order_id} (trade {trade_id})")
    
    try:
        # Import here to avoid circular imports
        from ..services.order_monitoring_service import order_monitor
        
        # Run async monitoring in task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(order_monitor.monitor_order(order_id, trade_id))
        loop.close()
        
        logger.info(f"✅ Monitoring completed for order {order_id}")
        return {"status": "completed", "order_id": order_id, "trade_id": trade_id}
        
    except Exception as e:
        logger.error(f"❌ Order monitoring task failed for {order_id}: {e}")
        return {"status": "error", "error": str(e), "order_id": order_id, "trade_id": trade_id}
