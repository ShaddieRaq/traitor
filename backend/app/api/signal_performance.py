"""
Phase 3A: Signal Performance Analytics API
Endpoints for analyzing signal performance across different market regimes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from ..core.database import get_db
from ..services.signal_performance_tracker import get_signal_performance_tracker
from ..api.schemas import BaseModel
from pydantic import Field

router = APIRouter()
logger = logging.getLogger(__name__)


class SignalPerformanceResponse(BaseModel):
    """Response model for signal performance metrics"""
    signal_type: str
    pair: str
    regime: str
    accuracy: float = Field(..., ge=0, le=1, description="Prediction accuracy (0-1)")
    precision: float = Field(..., ge=0, le=1, description="Positive prediction precision (0-1)")
    total_predictions: int = Field(..., ge=0, description="Total number of predictions")
    avg_confidence: float = Field(..., ge=0, le=1, description="Average confidence score")
    avg_pnl_usd: float = Field(..., description="Average P&L when trades executed")
    last_updated: datetime


class AdaptiveWeightsResponse(BaseModel):
    """Response model for adaptive signal weights"""
    pair: str
    regime: str
    signal_weights: Dict[str, float]
    default_weights: Dict[str, float]
    confidence_score: float = Field(..., ge=0, le=1)
    performance_period_days: int


class SignalRankingResponse(BaseModel):
    """Response model for signal rankings by regime"""
    regime: str
    signal_rankings: List[tuple] = Field(..., description="List of (signal_type, performance_score) tuples")


@router.get("/performance/signals", response_model=List[SignalPerformanceResponse])
def get_signal_performance_metrics(
    pair: Optional[str] = Query(None, description="Filter by trading pair"),
    regime: Optional[str] = Query(None, description="Filter by market regime"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    min_samples: int = Query(20, ge=10, description="Minimum predictions for reliable metrics"),
    db: Session = Depends(get_db)
):
    """
    Get signal performance metrics across different conditions.
    
    Returns comprehensive performance analytics for signals including accuracy,
    precision, confidence, and P&L metrics.
    """
    try:
        performance_tracker = get_signal_performance_tracker(db)
        
        # Get all cached metrics
        metrics_list = []
        for key, metrics in performance_tracker.performance_cache.items():
            # Apply filters
            if pair and pair not in key:
                continue
            if regime and regime not in key:
                continue
            if signal_type and signal_type not in key:
                continue
            if metrics.total_predictions < min_samples:
                continue
                
            metrics_list.append(SignalPerformanceResponse(
                signal_type=metrics.signal_type,
                pair=metrics.pair,
                regime=metrics.regime,
                accuracy=metrics.accuracy,
                precision=metrics.precision,
                total_predictions=metrics.total_predictions,
                avg_confidence=metrics.avg_confidence,
                avg_pnl_usd=metrics.avg_pnl,
                last_updated=metrics.last_updated
            ))
        
        return metrics_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signal performance metrics: {str(e)}")


@router.get("/performance/rankings", response_model=List[SignalRankingResponse])
def get_signal_rankings_by_regime(
    min_accuracy: float = Query(0.6, ge=0, le=1, description="Minimum accuracy threshold"),
    db: Session = Depends(get_db)
):
    """
    Get signal performance rankings for each market regime.
    
    Returns the best performing signals for each market regime,
    helping identify which signals work best in different conditions.
    """
    try:
        performance_tracker = get_signal_performance_tracker(db)
        
        # Get unique regimes from cached metrics
        regimes = set()
        for key in performance_tracker.performance_cache.keys():
            # Extract regime from key format: "pair_regime_signal_type"
            parts = key.split('_')
            if len(parts) >= 2:
                regime = parts[-2]  # Assumes regime is second-to-last part
                regimes.add(regime)
        
        rankings = []
        for regime in regimes:
            signal_rankings = performance_tracker.get_best_signals_for_regime(regime, min_accuracy)
            rankings.append(SignalRankingResponse(
                regime=regime,
                signal_rankings=signal_rankings
            ))
        
        return rankings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signal rankings: {str(e)}")


@router.get("/performance/adaptive-weights/{bot_id}", response_model=AdaptiveWeightsResponse)
def get_adaptive_signal_weights(
    bot_id: int,
    regime: Optional[str] = Query(None, description="Market regime for weights"),
    db: Session = Depends(get_db)
):
    """
    Get adaptive signal weights for a specific bot based on performance.
    
    Returns dynamically calculated signal weights that optimize for
    performance in the current market regime.
    """
    try:
        from ..models.models import Bot
        
        # Get bot information
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Use current regime if not specified
        if not regime:
            if getattr(bot, 'use_trend_detection', False):
                try:
                    from ..services.trend_detection_engine import get_trend_engine
                    trend_engine = get_trend_engine()
                    regime_data = trend_engine.analyze_trend(bot.pair)
                    regime = regime_data.get('regime', 'UNKNOWN')
                except:
                    regime = 'UNKNOWN'
            else:
                regime = 'STATIC'
        
        # Get default signal weights
        import json
        signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
        default_weights = {}
        for signal_name, config in signal_config.items():
            if config and config.get('enabled', False):
                default_weights[signal_name] = config.get('weight', 0.0)
        
        if not default_weights:
            raise HTTPException(status_code=400, detail="No enabled signals found for bot")
        
        # Calculate adaptive weights
        performance_tracker = get_signal_performance_tracker(db)
        adaptive_weights = performance_tracker.get_adaptive_signal_weights(
            pair=bot.pair,
            regime=regime,
            default_weights=default_weights
        )
        
        # Calculate confidence based on available performance data
        confidence_score = 0.0
        for signal_type in adaptive_weights.keys():
            key = f"{bot.pair}_{regime}_{signal_type}"
            if key in performance_tracker.performance_cache:
                metrics = performance_tracker.performance_cache[key]
                # Confidence based on sample size and accuracy
                sample_confidence = min(metrics.total_predictions / 50.0, 1.0)
                accuracy_confidence = metrics.accuracy
                confidence_score += (sample_confidence * accuracy_confidence)
        
        confidence_score = confidence_score / len(adaptive_weights) if adaptive_weights else 0.0
        
        return AdaptiveWeightsResponse(
            pair=bot.pair,
            regime=regime,
            signal_weights=adaptive_weights,
            default_weights=default_weights,
            confidence_score=confidence_score,
            performance_period_days=30  # Default period
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get adaptive weights: {str(e)}")


@router.post("/performance/calculate-metrics")
def calculate_performance_metrics(
    pair: Optional[str] = Query(None, description="Calculate for specific pair"),
    regime: Optional[str] = Query(None, description="Calculate for specific regime"),
    min_samples: int = Query(5, ge=1, description="Minimum samples for reliable metrics"),
    db: Session = Depends(get_db)
):
    """
    Trigger calculation of signal performance metrics.
    
    This endpoint recalculates performance metrics from recorded predictions.
    Useful for updating metrics after new trading data is available.
    """
    try:
        from ..models.models import SignalPredictionRecord
        performance_tracker = get_signal_performance_tracker(db)
        
        # Query database directly for unique combinations with evaluated predictions
        query = db.query(
            SignalPredictionRecord.pair,
            SignalPredictionRecord.regime, 
            SignalPredictionRecord.signal_type
        ).filter(
            SignalPredictionRecord.outcome.isnot(None)  # Only evaluated predictions
        ).distinct()
        
        # Apply filters if specified
        if pair:
            query = query.filter(SignalPredictionRecord.pair == pair)
        if regime:
            query = query.filter(SignalPredictionRecord.regime == regime)
        
        combinations = query.all()
        
        calculated_metrics = []
        for combo in combinations:
            pair_key = combo.pair
            regime_key = combo.regime  
            signal_type_key = combo.signal_type
            
            metrics = performance_tracker.calculate_signal_metrics(
                pair=pair_key,
                regime=regime_key,
                signal_type=signal_type_key,
                min_samples=min_samples
            )
            if metrics:
                calculated_metrics.append({
                    'pair': metrics.pair,
                    'regime': metrics.regime,
                    'signal_type': metrics.signal_type,
                    'accuracy': metrics.accuracy,
                    'precision': metrics.precision,
                    'total_predictions': metrics.total_predictions
                })
                
                # Cache the metrics
                key = f"{metrics.pair}_{metrics.regime}_{metrics.signal_type}"
                performance_tracker.performance_cache[key] = metrics
        
        return {
            "message": f"Calculated metrics for {len(calculated_metrics)} signal combinations",
            "metrics": calculated_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")


@router.get("/performance/report")
def get_performance_report(
    regime: Optional[str] = Query(None, description="Filter by regime"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive signal performance report.
    
    Returns a detailed report including performance metrics, rankings,
    and summary statistics for analysis and debugging.
    """
    try:
        performance_tracker = get_signal_performance_tracker(db)
        report = performance_tracker.generate_performance_report(regime)
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")