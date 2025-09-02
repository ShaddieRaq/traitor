import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.models import MarketData
from ..services.coinbase_service import coinbase_service
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def fetch_market_data_task(product_ids: list = None, timeframes: list = None):
    """Fetch market data for specified products and timeframes."""
    if product_ids is None:
        product_ids = ["BTC-USD", "ETH-USD"]
    
    if timeframes is None:
        timeframes = ["1h"]  # Start with 1-hour timeframe
    
    db = SessionLocal()
    try:
        for product_id in product_ids:
            for timeframe in timeframes:
                logger.info(f"Fetching {timeframe} data for {product_id}")
                
                # Convert timeframe to granularity in seconds
                granularity = timeframe_to_seconds(timeframe)
                
                # Fetch historical data from Coinbase
                df = coinbase_service.get_historical_data(
                    product_id=product_id,
                    granularity=granularity,
                    limit=100
                )
                
                if df.empty:
                    logger.warning(f"No data received for {product_id} {timeframe}")
                    continue
                
                # Save to database
                saved_count = 0
                for timestamp, row in df.iterrows():
                    # Check if data already exists
                    existing = db.query(MarketData).filter(
                        MarketData.product_id == product_id,
                        MarketData.timeframe == timeframe,
                        MarketData.timestamp == timestamp
                    ).first()
                    
                    if not existing:
                        market_data = MarketData(
                            product_id=product_id,
                            timestamp=timestamp,
                            timeframe=timeframe,
                            open_price=row['open'],
                            high_price=row['high'],
                            low_price=row['low'],
                            close_price=row['close'],
                            volume=row['volume']
                        )
                        db.add(market_data)
                        saved_count += 1
                
                if saved_count > 0:
                    db.commit()
                    logger.info(f"Saved {saved_count} new candles for {product_id} {timeframe}")
                
    except Exception as e:
        logger.error(f"Error in market data fetch task: {e}")
        db.rollback()
    finally:
        db.close()


def timeframe_to_seconds(timeframe: str) -> int:
    """Convert timeframe string to seconds."""
    timeframe_map = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "1h": 3600,
        "4h": 14400,
        "1d": 86400
    }
    return timeframe_map.get(timeframe, 3600)


@celery_app.task
def cleanup_old_data(days_to_keep: int = 30):
    """Clean up old market data and signal results."""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Delete old market data
        deleted_market = db.query(MarketData).filter(
            MarketData.timestamp < cutoff_date
        ).delete()
        
        # Delete old signal results
        from ..models.models import SignalResult
        deleted_signals = db.query(SignalResult).filter(
            SignalResult.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted_market} market data records and {deleted_signals} signal results")
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        db.rollback()
    finally:
        db.close()
