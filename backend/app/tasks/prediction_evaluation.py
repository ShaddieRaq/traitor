"""
Phase 8.1: Prediction Outcome Evaluation Task
Celery task to evaluate SignalPredictionRecord outcomes for learning system
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import and_
from ..models.models import SignalPredictionRecord
from ..core.database import SessionLocal
from ..services.sync_coordinated_coinbase_service import get_coordinated_coinbase_service
from ..services.signal_performance_tracker import SignalOutcome
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.prediction_evaluation.evaluate_prediction_outcomes")
def evaluate_prediction_outcomes(hours_lookback: int = 2, batch_size: int = 100) -> Dict[str, Any]:
    """
    Evaluate outcomes for SignalPredictionRecord entries that are ready for evaluation.
    
    This task finds predictions that:
    1. Were made 60+ minutes ago (evaluation_period_minutes has passed)
    2. Don't have outcomes set yet
    3. Evaluates them based on actual price movement
    
    Args:
        hours_lookback: How many hours back to look for unevaluated predictions
        batch_size: Number of predictions to evaluate per run
        
    Returns:
        Dict with evaluation results
    """
    db = SessionLocal()
    coinbase_service = get_coordinated_coinbase_service()
    
    try:
        # Find predictions ready for evaluation
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_lookback)
        evaluation_ready_time = datetime.utcnow() - timedelta(minutes=60)  # 1 hour evaluation period
        
        unevaluated_predictions = db.query(SignalPredictionRecord).filter(
            and_(
                SignalPredictionRecord.outcome.is_(None),  # No outcome yet
                SignalPredictionRecord.timestamp >= cutoff_time,  # Within lookback window
                SignalPredictionRecord.timestamp <= evaluation_ready_time,  # Ready for evaluation
                SignalPredictionRecord.prediction != 'hold'  # Only evaluate buy/sell signals
            )
        ).limit(batch_size).all()
        
        if not unevaluated_predictions:
            return {
                "status": "no_predictions_to_evaluate",
                "evaluated_count": 0,
                "total_found": 0
            }
        
        logger.info(f"🔍 Found {len(unevaluated_predictions)} predictions ready for outcome evaluation")
        
        evaluated_count = 0
        outcomes_assigned = {'true_positive': 0, 'false_positive': 0, 'true_negative': 0, 'false_negative': 0}
        
        for prediction in unevaluated_predictions:
            try:
                # Get price data for evaluation period (1 hour after prediction)
                start_time = prediction.timestamp
                end_time = start_time + timedelta(minutes=60)
                
                # Get market data for this period
                market_data = coinbase_service.get_historical_data(
                    product_id=prediction.pair,
                    granularity=300,  # 5-minute candles
                    start_time=start_time,
                    end_time=end_time
                )
                
                if market_data.empty:
                    logger.warning(f"No market data for {prediction.pair} at {start_time}")
                    continue
                
                # Calculate price change over evaluation period
                start_price = market_data['close'].iloc[0]
                end_price = market_data['close'].iloc[-1]
                price_change_pct = ((end_price - start_price) / start_price) * 100
                
                # Evaluate outcome using same logic as SignalPerformanceTracker
                threshold = 0.5  # 0.5% price movement threshold
                
                if prediction.prediction == "buy":
                    if price_change_pct > threshold:
                        outcome = SignalOutcome.TRUE_POSITIVE  # Correct buy signal
                    else:
                        outcome = SignalOutcome.FALSE_POSITIVE  # Wrong buy signal
                elif prediction.prediction == "sell":
                    if price_change_pct < -threshold:
                        outcome = SignalOutcome.TRUE_POSITIVE  # Correct sell signal
                    else:
                        outcome = SignalOutcome.FALSE_POSITIVE  # Wrong sell signal
                else:
                    continue  # Skip hold signals for now
                
                # Update prediction record with outcome
                prediction.actual_price_change_pct = price_change_pct
                prediction.outcome = outcome.value
                prediction.evaluation_timestamp = datetime.utcnow()
                
                outcomes_assigned[outcome.value] += 1
                evaluated_count += 1
                
                logger.debug(f"✅ Evaluated {prediction.signal_type} {prediction.pair} {prediction.prediction}: "
                           f"{price_change_pct:+.2f}% → {outcome.value}")
                
            except Exception as e:
                logger.error(f"Error evaluating prediction {prediction.id}: {e}")
                continue
        
        # Commit all updates
        db.commit()
        
        result = {
            "status": "evaluation_complete",
            "evaluated_count": evaluated_count,
            "total_found": len(unevaluated_predictions),
            "outcomes": outcomes_assigned,
            "evaluation_period_hours": hours_lookback,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"🎯 Prediction outcome evaluation complete: {evaluated_count} predictions evaluated")
        logger.info(f"   Outcomes: {outcomes_assigned}")
        
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in prediction outcome evaluation: {e}")
        return {
            "status": "error",
            "message": str(e),
            "evaluated_count": 0
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.prediction_evaluation.cleanup_old_predictions")
def cleanup_old_predictions(days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old SignalPredictionRecord entries to prevent database bloat.
    
    Args:
        days_to_keep: Number of days of prediction history to retain
        
    Returns:
        Dict with cleanup results
    """
    db = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count records to be deleted
        old_count = db.query(SignalPredictionRecord).filter(
            SignalPredictionRecord.timestamp < cutoff_date
        ).count()
        
        if old_count == 0:
            return {
                "status": "no_cleanup_needed",
                "deleted_count": 0,
                "cutoff_date": cutoff_date.isoformat()
            }
        
        # Delete old records
        deleted = db.query(SignalPredictionRecord).filter(
            SignalPredictionRecord.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"🧹 Cleaned up {deleted} old prediction records (older than {days_to_keep} days)")
        
        return {
            "status": "cleanup_complete",
            "deleted_count": deleted,
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in prediction cleanup: {e}")
        return {
            "status": "error",
            "message": str(e),
            "deleted_count": 0
        }
    finally:
        db.close()