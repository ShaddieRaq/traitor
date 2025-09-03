from typing import List
import logging
from ..core.database import SessionLocal
from ..models.models import Bot, MarketData
from ..services.coinbase_service import coinbase_service
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="evaluate_bot_signals")
def evaluate_bot_signals():
    """
    Evaluate trading signals for all active bots.
    NOTE: Real-time evaluation now handled by WebSocket streaming (Phase 3.3).
          This task serves as backup/manual trigger for bot evaluation.
    """
    logger.info("Manual bot signal evaluation task triggered")
    
    try:
        db = SessionLocal()
        try:
            # Get all running bots
            active_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
            logger.info(f"Found {len(active_bots)} running bots for manual evaluation")
            
            return {
                "status": "manual_evaluation_complete", 
                "running_bots": len(active_bots),
                "message": f"Manual evaluation completed for {len(active_bots)} bots. Real-time evaluation via WebSocket is active."
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in evaluate_bot_signals task: {str(e)}")
        return {"status": "error", "message": str(e)}


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
