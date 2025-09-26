"""
Phase 3A: Signal Ensemble Intelligence - Performance Analytics
Track signal accuracy and effectiveness across market regimes and trading pairs

Core Components:
- SignalPerformanceTracker: Track signal prediction accuracy
- SignalAnalytics: Analyze performance patterns and trends
- RegimeSignalMapping: Map best signals to market regimes
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class SignalOutcome(Enum):
    """Signal prediction outcome classification"""
    TRUE_POSITIVE = "true_positive"    # Signal predicted correctly (buy before price up, sell before price down)
    FALSE_POSITIVE = "false_positive"  # Signal predicted incorrectly (buy before price down, sell before price up)
    TRUE_NEGATIVE = "true_negative"    # No signal when no significant price movement
    FALSE_NEGATIVE = "false_negative"  # Missed signal (should have predicted but didn't)


@dataclass
class SignalPrediction:
    """Individual signal prediction record"""
    timestamp: datetime
    pair: str
    regime: str
    signal_type: str  # RSI, MA_Crossover, MACD
    signal_score: float
    prediction: str   # buy, sell, hold
    confidence: float
    actual_price_change: Optional[float] = None
    outcome: Optional[SignalOutcome] = None
    trade_executed: bool = False
    trade_pnl: Optional[float] = None


@dataclass
class SignalPerformanceMetrics:
    """Performance metrics for a signal in specific conditions"""
    signal_type: str
    pair: str
    regime: str
    total_predictions: int
    accuracy: float  # % of correct predictions
    precision: float  # % of positive predictions that were correct
    recall: float    # % of actual opportunities that were caught
    avg_confidence: float
    avg_pnl: float   # Average P&L when trades executed
    last_updated: datetime


class SignalPerformanceTracker:
    """
    Track and analyze signal performance across different market regimes.
    
    This system continuously monitors how well each signal (RSI, MA, MACD) performs
    in different market conditions (TRENDING, RANGING, etc.) and for different pairs.
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        # In-memory storage for real-time tracking (could be moved to database/Redis)
        self.predictions: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.performance_cache: Dict[str, SignalPerformanceMetrics] = {}
        self.regime_signal_rankings: Dict[str, List[Tuple[str, float]]] = {}
        
    def record_signal_prediction(self, prediction: SignalPrediction) -> None:
        """
        Record a signal prediction for later performance evaluation.
        
        Args:
            prediction: SignalPrediction with signal details and prediction
        """
        # Store in memory for immediate access
        key = f"{prediction.pair}_{prediction.regime}_{prediction.signal_type}"
        self.predictions[key].append(prediction)
        
        # Persist to database for permanent storage
        if self.db:
            try:
                from ..models.models import SignalPredictionRecord
                
                db_record = SignalPredictionRecord(
                    timestamp=prediction.timestamp,
                    pair=prediction.pair,
                    regime=prediction.regime,
                    signal_type=prediction.signal_type,
                    signal_score=prediction.signal_score,
                    prediction=prediction.prediction,
                    confidence=prediction.confidence,
                    actual_price_change_pct=prediction.actual_price_change,
                    outcome=prediction.outcome.value if prediction.outcome else None,
                    evaluation_timestamp=None,  # To be filled when evaluated
                    trade_executed=prediction.trade_executed,
                    trade_pnl_usd=prediction.trade_pnl,
                    evaluation_period_minutes=60
                )
                
                self.db.add(db_record)
                self.db.commit()
                
                logger.debug(
                    f"📊 Recorded signal prediction to database: {prediction.signal_type} for {prediction.pair} "
                    f"in {prediction.regime} regime → {prediction.prediction} (confidence: {prediction.confidence:.3f})"
                )
                
            except Exception as db_error:
                logger.warning(f"Failed to persist signal prediction to database: {db_error}")
                # Continue with in-memory storage even if DB fails
        
        logger.debug(
            f"📊 Recorded signal prediction: {prediction.signal_type} for {prediction.pair} "
            f"in {prediction.regime} regime → {prediction.prediction} (confidence: {prediction.confidence:.3f})"
        )
    
    def evaluate_prediction_outcome(self, 
                                   prediction: SignalPrediction,
                                   actual_price_change_pct: float,
                                   lookhead_minutes: int = 60) -> SignalOutcome:
        """
        Evaluate whether a signal prediction was correct based on subsequent price movement.
        
        Args:
            prediction: Original signal prediction
            actual_price_change_pct: Actual price change % over lookhead period
            lookhead_minutes: Time horizon for evaluation (default 1 hour)
            
        Returns:
            SignalOutcome classification
        """
        threshold = 0.5  # 0.5% price movement threshold for significance
        
        prediction.actual_price_change = actual_price_change_pct
        
        if prediction.prediction == "buy":
            if actual_price_change_pct > threshold:
                outcome = SignalOutcome.TRUE_POSITIVE  # Correct buy signal
            else:
                outcome = SignalOutcome.FALSE_POSITIVE  # Wrong buy signal
        elif prediction.prediction == "sell":
            if actual_price_change_pct < -threshold:
                outcome = SignalOutcome.TRUE_POSITIVE  # Correct sell signal  
            else:
                outcome = SignalOutcome.FALSE_POSITIVE  # Wrong sell signal
        else:  # hold
            if abs(actual_price_change_pct) < threshold:
                outcome = SignalOutcome.TRUE_NEGATIVE   # Correct hold
            else:
                outcome = SignalOutcome.FALSE_NEGATIVE  # Missed opportunity
        
        prediction.outcome = outcome
        return outcome
    
    def load_evaluated_predictions_from_db(self, 
                                          pair: Optional[str] = None, 
                                          regime: Optional[str] = None, 
                                          signal_type: Optional[str] = None) -> List[SignalPrediction]:
        """
        Load evaluated signal predictions from database.
        
        Args:
            pair: Optional pair filter
            regime: Optional regime filter  
            signal_type: Optional signal type filter
            
        Returns:
            List of SignalPrediction objects loaded from database
        """
        if not self.db:
            return []
            
        try:
            from ..models.models import SignalPredictionRecord
            
            query = self.db.query(SignalPredictionRecord).filter(
                SignalPredictionRecord.outcome.isnot(None)  # Only evaluated predictions
            )
            
            # Apply filters
            if pair:
                query = query.filter(SignalPredictionRecord.pair == pair)
            if regime:
                query = query.filter(SignalPredictionRecord.regime == regime)
            if signal_type:
                query = query.filter(SignalPredictionRecord.signal_type == signal_type)
            
            db_records = query.all()
            
            # Convert to SignalPrediction objects
            predictions = []
            for record in db_records:
                prediction = SignalPrediction(
                    timestamp=record.timestamp,
                    pair=record.pair,
                    regime=record.regime,
                    signal_type=record.signal_type,
                    signal_score=record.signal_score,
                    prediction=record.prediction,
                    confidence=record.confidence,
                    actual_price_change=record.actual_price_change_pct,
                    outcome=SignalOutcome(record.outcome) if record.outcome else None,
                    trade_executed=record.trade_executed or False,
                    trade_pnl=record.trade_pnl_usd
                )
                predictions.append(prediction)
                
                # Also add to in-memory cache
                key = f"{prediction.pair}_{prediction.regime}_{prediction.signal_type}"
                if prediction not in self.predictions[key]:  # Avoid duplicates
                    self.predictions[key].append(prediction)
            
            logger.info(f"📊 Loaded {len(predictions)} evaluated predictions from database")
            return predictions
            
        except Exception as e:
            logger.warning(f"Failed to load predictions from database: {e}")
            return []

    def calculate_signal_metrics(self, 
                                pair: str, 
                                regime: str, 
                                signal_type: str,
                                min_samples: int = 5) -> Optional[SignalPerformanceMetrics]:
        """
        Calculate comprehensive performance metrics for a signal in specific conditions.
        
        Args:
            pair: Trading pair (e.g., BTC-USD)
            regime: Market regime (TRENDING, RANGING, etc.)
            signal_type: Signal type (RSI, MA_Crossover, MACD)
            min_samples: Minimum predictions needed for reliable metrics (lowered to 5)
            
        Returns:
            SignalPerformanceMetrics or None if insufficient data
        """
        # First load any evaluated predictions from database
        self.load_evaluated_predictions_from_db(pair=pair, regime=regime, signal_type=signal_type)
        
        key = f"{pair}_{regime}_{signal_type}"
        predictions = list(self.predictions[key])
        
        # Filter predictions with outcome evaluations
        evaluated_predictions = [p for p in predictions if p.outcome is not None]
        
        if len(evaluated_predictions) < min_samples:
            logger.debug(f"Insufficient data for {key}: {len(evaluated_predictions)} < {min_samples}")
            return None
        
        # Calculate metrics
        total = len(evaluated_predictions)
        correct = sum(1 for p in evaluated_predictions if p.outcome in [SignalOutcome.TRUE_POSITIVE, SignalOutcome.TRUE_NEGATIVE])
        positive_predictions = [p for p in evaluated_predictions if p.prediction in ['buy', 'sell']]
        correct_positives = [p for p in positive_predictions if p.outcome == SignalOutcome.TRUE_POSITIVE]
        
        accuracy = correct / total if total > 0 else 0.0
        precision = len(correct_positives) / len(positive_predictions) if positive_predictions else 0.0
        
        # Calculate recall (need to track missed opportunities - complex, simplified for now)
        recall = precision  # Simplified - would need more sophisticated tracking
        
        avg_confidence = np.mean([p.confidence for p in evaluated_predictions])
        
        # Calculate average P&L from executed trades
        trade_predictions = [p for p in evaluated_predictions if p.trade_executed and p.trade_pnl is not None]
        avg_pnl = np.mean([p.trade_pnl for p in trade_predictions]) if trade_predictions else 0.0
        
        metrics = SignalPerformanceMetrics(
            signal_type=signal_type,
            pair=pair,
            regime=regime,
            total_predictions=total,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            avg_confidence=avg_confidence,
            avg_pnl=avg_pnl,
            last_updated=datetime.utcnow()
        )
        
        # Cache the metrics
        self.performance_cache[key] = metrics
        
        logger.info(
            f"📈 Signal metrics for {key}: {accuracy:.1%} accuracy, "
            f"{precision:.1%} precision, avg P&L: ${avg_pnl:.2f} ({total} samples)"
        )
        
        return metrics
    
    def get_best_signals_for_regime(self, regime: str, min_accuracy: float = 0.6) -> List[Tuple[str, float]]:
        """
        Get the best performing signals for a specific market regime.
        
        Args:
            regime: Market regime (TRENDING, RANGING, etc.)
            min_accuracy: Minimum accuracy threshold
            
        Returns:
            List of (signal_type, accuracy_score) tuples sorted by performance
        """
        regime_signals = []
        
        for key, metrics in self.performance_cache.items():
            if regime in key and metrics.accuracy >= min_accuracy:
                # Composite score: accuracy weighted by confidence and sample size
                score = (metrics.accuracy * metrics.avg_confidence * 
                        min(metrics.total_predictions / 50.0, 1.0))  # Cap at 50 samples
                regime_signals.append((metrics.signal_type, score))
        
        # Sort by performance score
        regime_signals.sort(key=lambda x: x[1], reverse=True)
        
        self.regime_signal_rankings[regime] = regime_signals
        
        logger.info(
            f"🎯 Best signals for {regime} regime: " + 
            ", ".join([f"{signal}({score:.3f})" for signal, score in regime_signals[:3]])
        )
        
        return regime_signals
    
    def get_adaptive_signal_weights(self, 
                                   pair: str, 
                                   regime: str,
                                   default_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate adaptive signal weights based on performance in current conditions.
        
        Args:
            pair: Trading pair
            regime: Current market regime  
            default_weights: Default signal weights as fallback
            
        Returns:
            Optimized signal weights dictionary
        """
        adaptive_weights = default_weights.copy()
        
        # Get performance metrics for each signal
        signal_performances = {}
        for signal_type in default_weights.keys():
            key = f"{pair}_{regime}_{signal_type}"
            if key in self.performance_cache:
                metrics = self.performance_cache[key]
                # Composite performance score
                performance_score = (metrics.accuracy * metrics.precision * 
                                   (1 + metrics.avg_pnl / 10.0))  # Boost for profitable signals
                signal_performances[signal_type] = performance_score
            else:
                signal_performances[signal_type] = 0.5  # Neutral score for unknown performance
        
        if signal_performances:
            # Normalize and apply adaptive weighting
            total_performance = sum(signal_performances.values())
            if total_performance > 0:
                for signal_type in adaptive_weights:
                    performance_ratio = signal_performances[signal_type] / total_performance
                    # Blend with default weights (70% performance, 30% default)
                    adaptive_weights[signal_type] = (0.7 * performance_ratio + 
                                                   0.3 * default_weights[signal_type])
        
        # Normalize weights to sum to 1.0
        total_weight = sum(adaptive_weights.values())
        if total_weight > 0:
            adaptive_weights = {k: v/total_weight for k, v in adaptive_weights.items()}
        
        logger.info(
            f"🔧 Adaptive weights for {pair} in {regime}: " +
            ", ".join([f"{k}:{v:.2f}" for k, v in adaptive_weights.items()])
        )
        
        return adaptive_weights
    
    def generate_performance_report(self, regime: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive performance report for analysis.
        
        Args:
            regime: Optional regime filter
            
        Returns:
            Performance report dictionary
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "regime_filter": regime,
            "signal_performance": {},
            "regime_rankings": dict(self.regime_signal_rankings),
            "summary": {
                "total_cached_metrics": len(self.performance_cache),
                "total_predictions": sum(len(predictions) for predictions in self.predictions.values())
            }
        }
        
        # Add detailed signal performance
        for key, metrics in self.performance_cache.items():
            if regime is None or regime in key:
                report["signal_performance"][key] = {
                    "signal_type": metrics.signal_type,
                    "pair": metrics.pair,
                    "regime": metrics.regime,
                    "accuracy": metrics.accuracy,
                    "precision": metrics.precision,
                    "avg_pnl": metrics.avg_pnl,
                    "total_predictions": metrics.total_predictions,
                    "last_updated": metrics.last_updated.isoformat()
                }
        
        return report


# Singleton instance for global access
_signal_performance_tracker = None

def get_signal_performance_tracker(db_session=None) -> SignalPerformanceTracker:
    """Get or create the global signal performance tracker instance."""
    global _signal_performance_tracker
    if _signal_performance_tracker is None:
        _signal_performance_tracker = SignalPerformanceTracker(db_session)
    return _signal_performance_tracker