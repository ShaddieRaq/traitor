from typing import List
import logging
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.models import Signal, MarketData, SignalResult
from ..services.signals import RSISignal, MovingAverageSignal
from ..services.coinbase_service import coinbase_service
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def evaluate_signals_task(product_ids: List[str] = None):
    """Evaluate all enabled signals for given products."""
    if product_ids is None:
        product_ids = ["BTC-USD", "ETH-USD"]  # Default products
    
    db = SessionLocal()
    try:
        # Get enabled signals
        enabled_signals = db.query(Signal).filter(Signal.enabled == True).all()
        
        for product_id in product_ids:
            logger.info(f"Evaluating signals for {product_id}")
            
            # Get recent market data
            market_data = db.query(MarketData).filter(
                MarketData.product_id == product_id,
                MarketData.timeframe == "1h"
            ).order_by(MarketData.timestamp.desc()).limit(200).all()
            
            if not market_data:
                logger.warning(f"No market data found for {product_id}")
                continue
            
            # Convert to DataFrame
            import pandas as pd
            df_data = []
            for data in reversed(market_data):  # Reverse to get chronological order
                df_data.append({
                    'timestamp': data.timestamp,
                    'open': data.open_price,
                    'high': data.high_price,
                    'low': data.low_price,
                    'close': data.close_price,
                    'volume': data.volume
                })
            
            df = pd.DataFrame(df_data)
            if df.empty:
                logger.warning(f"No valid market data for {product_id}")
                continue
            
            # Process each enabled signal
            for signal in enabled_signals:
                try:
                    signal_instance = create_signal_instance(signal)
                    if signal_instance:
                        result = signal_instance.evaluate(df)
                        if result:
                            # Store result
                            signal_result = SignalResult(
                                signal_id=signal.id,
                                product_id=product_id,
                                timestamp=result['timestamp'],
                                signal_type=result['action'],
                                strength=result['strength'],
                                price=result['price'],
                                metadata=result.get('metadata', {})
                            )
                            db.add(signal_result)
                            
                            logger.info(f"Signal generated: {signal.name} - {result['action']} at {result['price']}")
                            
                except Exception as e:
                    logger.error(f"Error evaluating signal {signal.name}: {str(e)}")
                    continue
        
        db.commit()
        logger.info("Signal evaluation completed")
        return True
        
    except Exception as e:
        logger.error(f"Error in evaluate_signals_task: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def create_signal_instance(signal_config: Signal):
    """Create a signal instance based on the signal configuration."""
    try:
        signal_type = signal_config.signal_type
        parameters = signal_config.parameters or {}
        
        if signal_type == "rsi":
            return RSISignal(weight=signal_config.weight, **parameters)
        elif signal_type == "moving_average":
            return MovingAverageSignal(weight=signal_config.weight, **parameters)
        else:
            logger.error(f"Unknown signal type: {signal_type}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating signal instance: {str(e)}")
        return None


@celery_app.task 
def fetch_market_data_task(product_id: str = "BTC-USD", timeframe: str = "1h"):
    """Fetch market data from Coinbase Pro API."""
    logger.info(f"Fetching market data for {product_id}")
    
    try:
        # Map timeframe to granularity (in seconds)
        granularity_map = {
            "1m": 60,
            "5m": 300, 
            "15m": 900,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400
        }
        granularity = granularity_map.get(timeframe, 3600)
        
        # Fetch data from Coinbase
        df = coinbase_service.get_historical_data(product_id, granularity=granularity, limit=200)
        
        if df.empty:
            logger.warning(f"No market data received for {product_id}")
            return False
        
        # Store in database
        db = SessionLocal()
        try:
            for _, row in df.iterrows():
                market_data = MarketData(
                    product_id=product_id,
                    timeframe=timeframe,
                    timestamp=row['timestamp'],
                    open_price=row['open'],
                    high_price=row['high'],
                    low_price=row['low'],
                    close_price=row['close'],
                    volume=row['volume']
                )
                
                # Use merge to avoid duplicates
                existing = db.query(MarketData).filter(
                    MarketData.product_id == product_id,
                    MarketData.timestamp == row['timestamp'],
                    MarketData.timeframe == timeframe
                ).first()
                
                if not existing:
                    db.add(market_data)
            
            db.commit()
            logger.info(f"Stored {len(df)} candles for {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing market data: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error fetching market data for {product_id}: {str(e)}")
        return False
