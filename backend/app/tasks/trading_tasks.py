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
                continue
            
            df.set_index('timestamp', inplace=True)
            
            # Evaluate each signal
            for signal_config in enabled_signals:
                try:
                    # Create signal instance based on name
                    signal_instance = create_signal_instance(signal_config)
                    if not signal_instance:
                        continue
                    
                    # Calculate signal
                    result = signal_instance.calculate(df)
                    
                    # Save result to database
                    signal_result = SignalResult(
                        signal_id=signal_config.id,
                        product_id=product_id,
                        timestamp=df.index[-1],
                        score=result["score"],
                        action=result["action"],
                        confidence=result["confidence"],
                        metadata=str(result["metadata"])
                    )
                    
                    db.add(signal_result)
                    
                except Exception as e:
                    logger.error(f"Error evaluating signal {signal_config.name}: {e}")
        
        db.commit()
        logger.info("Signal evaluation completed")
        
    except Exception as e:
        logger.error(f"Error in signal evaluation task: {e}")
        db.rollback()
    finally:
        db.close()


def create_signal_instance(signal_config: Signal):
    """Create signal instance from database configuration."""
    try:
        import json
        parameters = json.loads(signal_config.parameters) if signal_config.parameters else {}
        
        if signal_config.name == "RSI":
            return RSISignal(weight=signal_config.weight, **parameters)
        elif signal_config.name == "MA_Crossover":
            return MovingAverageSignal(weight=signal_config.weight, **parameters)
        else:
            logger.warning(f"Unknown signal type: {signal_config.name}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating signal instance for {signal_config.name}: {e}")
        return None


@celery_app.task
def process_trading_signals():
    """Process aggregated signals and make trading decisions."""
    db = SessionLocal()
    try:
        # This is where you would implement your trading logic
        # For now, just log that we're processing signals
        logger.info("Processing trading signals - implementation pending")
        
        # TODO: Implement trading logic based on signal aggregation
        # 1. Get latest signal results for each product
        # 2. Apply signal aggregation logic (voting, weighting, etc.)
        # 3. Make trading decisions based on risk management rules
        # 4. Execute trades via Coinbase API
        
    except Exception as e:
        logger.error(f"Error in trading signal processing: {e}")
    finally:
        db.close()
