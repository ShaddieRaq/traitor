"""
Phase 3B: Dynamic Signal Weighting Service
Automated signal weight optimization based on performance data

Key Features:
- Performance-based weight calculation
- Safety controls and gradual adjustments
- Bot signal_config JSON updates
- Automated trigger system
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json
import numpy as np
from ..models.models import Bot, SignalPredictionRecord, SignalPerformanceMetrics, AdaptiveSignalWeights
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class AdaptiveSignalWeightingService:
    """
    Service for automatically updating signal weights based on performance data.
    
    Moderate Safety Approach:
    - Max 15% weight change per update
    - Min 30 evaluated predictions per signal
    - 12-hour minimum between updates
    """
    
    def __init__(self):
        # Moderate safety controls (adjusted for initial deployment)
        self.max_weight_change_percent = 15  # Maximum 15% change per update  
        self.min_predictions_required = 1   # Minimum 1 for initial testing (will increase over time)
        self.cooldown_hours = 12  # 12-hour cooldown between updates
        self.min_weight_threshold = 0.05  # Minimum weight to prevent signal elimination
        self.max_weight_threshold = 0.8   # Maximum weight for any single signal
        
    def should_update_weights(self, bot: Bot, db: Session) -> Tuple[bool, str]:
        """
        Determine if bot weights should be updated based on data availability and timing.
        
        Returns:
            Tuple of (should_update, reason)
        """
        try:
            # Check if enough time has passed since last update
            last_update_query = db.query(AdaptiveSignalWeights).filter(
                AdaptiveSignalWeights.bot_id == bot.id
            ).order_by(AdaptiveSignalWeights.created_at.desc()).first()
            
            if last_update_query:
                hours_since_update = (datetime.utcnow() - last_update_query.created_at).total_seconds() / 3600
                if hours_since_update < self.min_hours_between_updates:
                    return False, f"Only {hours_since_update:.1f} hours since last update (min {self.min_hours_between_updates}h)"
            
            # Check available prediction data
            signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
            enabled_signals = [name for name, config in signal_config.items() 
                             if config and config.get('enabled', False)]
            
            if not enabled_signals:
                return False, "No enabled signals found"
            
            # Count evaluated predictions for each enabled signal
            insufficient_signals = []
            for signal_type in enabled_signals:
                prediction_count = db.query(SignalPredictionRecord).filter(
                    and_(
                        SignalPredictionRecord.pair == bot.pair,
                        SignalPredictionRecord.signal_type == signal_type,
                        SignalPredictionRecord.outcome.isnot(None)
                    )
                ).count()
                
                if prediction_count < self.min_predictions_required:
                    insufficient_signals.append(f"{signal_type}: {prediction_count}")
            
            if insufficient_signals:
                return False, f"Insufficient predictions: {', '.join(insufficient_signals)} (min {self.min_predictions_required})"
            
            return True, f"Ready for update: {len(enabled_signals)} signals with sufficient data"
            
        except Exception as e:
            logger.error(f"Error checking update eligibility for bot {bot.id}: {e}")
            return False, f"Error checking eligibility: {e}"
    
    def calculate_performance_metrics(self, bot: Bot, db: Session) -> Dict[str, Dict[str, float]]:
        """
        Calculate performance metrics for each signal type and regime.
        
        Returns:
            Dict[signal_type][metric] = value
        """
        signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
        enabled_signals = [name for name, config in signal_config.items() 
                         if config and config.get('enabled', False)]
        
        metrics = {}
        
        for signal_type in enabled_signals:
            # Get all evaluated predictions for this signal
            predictions = db.query(SignalPredictionRecord).filter(
                and_(
                    SignalPredictionRecord.pair == bot.pair,
                    SignalPredictionRecord.signal_type == signal_type,
                    SignalPredictionRecord.outcome.isnot(None)
                )
            ).all()
            
            if not predictions:
                continue
                
            # Calculate accuracy metrics
            total_predictions = len(predictions)
            correct_predictions = sum(1 for p in predictions 
                                    if p.outcome in ['true_positive', 'true_negative'])
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
            
            # Calculate precision for buy/sell signals
            positive_predictions = [p for p in predictions if p.prediction in ['buy', 'sell']]
            correct_positive = sum(1 for p in positive_predictions if p.outcome == 'true_positive')
            precision = correct_positive / len(positive_predictions) if positive_predictions else 0.0
            
            # Calculate average confidence and PnL
            avg_confidence = np.mean([p.confidence for p in predictions]) if predictions else 0.0
            pnl_predictions = [p for p in predictions if p.trade_pnl is not None]
            avg_pnl = np.mean([p.trade_pnl for p in pnl_predictions]) if pnl_predictions else 0.0
            
            metrics[signal_type] = {
                'accuracy': accuracy,
                'precision': precision,
                'total_predictions': total_predictions,
                'avg_confidence': avg_confidence,
                'avg_pnl': avg_pnl,
                'performance_score': self._calculate_performance_score(accuracy, precision, avg_confidence, avg_pnl)
            }
            
        return metrics
    
    def _calculate_performance_score(self, accuracy: float, precision: float, 
                                   confidence: float, avg_pnl: float) -> float:
        """
        Calculate composite performance score for signal weighting.
        
        Formula: (accuracy * 0.4) + (precision * 0.3) + (confidence * 0.2) + (pnl_factor * 0.1)
        """
        # Normalize PnL to 0-1 range (assuming typical range -0.05 to +0.05)
        pnl_factor = max(0, min(1, (avg_pnl + 0.05) / 0.1)) if avg_pnl != 0 else 0.5
        
        score = (accuracy * 0.4) + (precision * 0.3) + (confidence * 0.2) + (pnl_factor * 0.1)
        return max(0, min(1, score))  # Ensure 0-1 range
    
    def calculate_adaptive_weights(self, bot: Bot, performance_metrics: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Calculate new adaptive weights based on performance metrics.
        
        Args:
            bot: Bot instance with current signal_config
            performance_metrics: Performance data for each signal type
            
        Returns:
            Dict of new signal weights
        """
        signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
        current_weights = {}
        
        # Get current weights
        for signal_name, config in signal_config.items():
            if config and config.get('enabled', False):
                current_weights[signal_name] = config.get('weight', 0.0)
        
        if not current_weights or not performance_metrics:
            return current_weights
        
        # Calculate performance-based weights
        performance_scores = {}
        for signal_type, metrics in performance_metrics.items():
            if signal_type in current_weights:
                performance_scores[signal_type] = metrics['performance_score']
        
        if not performance_scores:
            return current_weights
        
        # Normalize performance scores to weights
        total_score = sum(performance_scores.values())
        if total_score == 0:
            return current_weights
        
        new_weights = {}
        for signal_type in current_weights:
            if signal_type in performance_scores:
                # Base weight on performance score
                performance_weight = performance_scores[signal_type] / total_score
                
                # Apply safety controls - gradual adjustment
                current_weight = current_weights[signal_type]
                max_change = self.max_weight_change
                
                # Calculate bounded new weight
                if performance_weight > current_weight:
                    new_weight = min(performance_weight, current_weight + max_change)
                else:
                    new_weight = max(performance_weight, current_weight - max_change)
                
                # Apply min/max thresholds
                new_weight = max(self.min_weight_threshold, min(self.max_weight_threshold, new_weight))
                new_weights[signal_type] = new_weight
            else:
                # Keep current weight if no performance data
                new_weights[signal_type] = current_weights[signal_type]
        
        # Normalize to sum to 1.0
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            new_weights = {k: v / total_weight for k, v in new_weights.items()}
        
        return new_weights
    
    def update_bot_signal_weights(self, bot: Bot, new_weights: Dict[str, float], db: Session) -> bool:
        """
        Safely update bot's signal_config with new weights.
        
        Args:
            bot: Bot instance to update
            new_weights: New signal weights
            db: Database session
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Parse current config
            signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
            
            # Update weights while preserving other signal parameters
            for signal_name, new_weight in new_weights.items():
                if signal_name in signal_config and signal_config[signal_name]:
                    signal_config[signal_name]['weight'] = round(new_weight, 4)
            
            # Save updated config
            bot.signal_config = json.dumps(signal_config, indent=2)
            db.commit()
            
            # Log the update
            weight_changes = []
            for signal_name, new_weight in new_weights.items():
                if signal_name in signal_config:
                    old_weight = signal_config[signal_name].get('weight', 0.0)
                    change = new_weight - old_weight
                    weight_changes.append(f"{signal_name}: {old_weight:.3f}→{new_weight:.3f} ({change:+.3f})")
            
            logger.info(f"✅ Updated weights for bot {bot.id} ({bot.pair}): {', '.join(weight_changes)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update bot {bot.id} signal weights: {e}")
            db.rollback()
            return False
    
    def record_weight_update(self, bot: Bot, old_weights: Dict[str, float], 
                           new_weights: Dict[str, float], performance_metrics: Dict[str, Dict[str, float]], 
                           db: Session) -> None:
        """Record the weight update for audit and analysis purposes."""
        try:
            # Get current regime for context
            current_regime = "UNKNOWN"
            try:
                from .trend_detection_engine import get_trend_engine
                if getattr(bot, 'use_trend_detection', False):
                    trend_engine = get_trend_engine()
                    regime_data = trend_engine.analyze_trend(bot.pair)
                    current_regime = regime_data.get('regime', 'UNKNOWN')
            except:
                pass
            
            # Calculate summary metrics
            total_predictions = sum(metrics.get('total_predictions', 0) for metrics in performance_metrics.values())
            avg_performance_score = np.mean([metrics.get('performance_score', 0) for metrics in performance_metrics.values()])
            
            # Create weight update record
            weight_record = AdaptiveSignalWeights(
                bot_id=bot.id,
                pair=bot.pair,
                regime=current_regime,
                signal_weights=new_weights,
                default_weights=old_weights,
                performance_period_days=30,
                confidence_score=float(avg_performance_score),
                weight_calculation_method="performance_weighted"
            )
            
            db.add(weight_record)
            db.commit()
            
            logger.info(f"📊 Recorded weight update for bot {bot.id}: {total_predictions} predictions analyzed, "
                       f"avg performance: {avg_performance_score:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to record weight update for bot {bot.id}: {e}")
    
    def process_bot_weight_update(self, bot_id: int) -> Dict[str, Any]:
        """
        Main method to process weight update for a specific bot.
        
        Returns:
            Dict with update status and details
        """
        result = {
            'bot_id': bot_id,
            'success': False,
            'message': '',
            'old_weights': {},
            'new_weights': {},
            'performance_metrics': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            db = SessionLocal()
            try:
                # Get bot
                bot = db.query(Bot).filter(Bot.id == bot_id).first()
                if not bot:
                    result['message'] = f"Bot {bot_id} not found"
                    return result
                
                # Check if update should proceed
                should_update, reason = self.should_update_weights(bot, db)
                if not should_update:
                    result['message'] = f"Update skipped: {reason}"
                    return result
                
                # Calculate performance metrics
                performance_metrics = self.calculate_performance_metrics(bot, db)
                if not performance_metrics:
                    result['message'] = "No performance metrics available"
                    return result
                
                # Get current weights
                signal_config = json.loads(bot.signal_config) if bot.signal_config else {}
                old_weights = {}
                for signal_name, config in signal_config.items():
                    if config and config.get('enabled', False):
                        old_weights[signal_name] = config.get('weight', 0.0)
                
                # Calculate new weights
                new_weights = self.calculate_adaptive_weights(bot, performance_metrics)
                
                # Check if weights actually changed significantly
                significant_change = any(
                    abs(new_weights.get(k, 0) - old_weights.get(k, 0)) > 0.01 
                    for k in set(list(old_weights.keys()) + list(new_weights.keys()))
                )
                
                if not significant_change:
                    result['message'] = "No significant weight changes needed"
                    result['old_weights'] = old_weights
                    result['new_weights'] = new_weights
                    result['performance_metrics'] = performance_metrics
                    return result
                
                # Update bot weights
                update_success = self.update_bot_signal_weights(bot, new_weights, db)
                if not update_success:
                    result['message'] = "Failed to update bot signal weights"
                    return result
                
                # Record the update
                self.record_weight_update(bot, old_weights, new_weights, performance_metrics, db)
                
                # Success!
                result.update({
                    'success': True,
                    'message': f"Successfully updated weights for bot {bot.name} ({bot.pair})",
                    'old_weights': old_weights,
                    'new_weights': new_weights,
                    'performance_metrics': performance_metrics
                })
                
                return result
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing weight update for bot {bot_id}: {e}")
            result['message'] = f"Error: {str(e)}"
            return result


# Global instance
_adaptive_weighting_service = None

def get_adaptive_weighting_service() -> AdaptiveSignalWeightingService:
    """Get global adaptive weighting service instance."""
    global _adaptive_weighting_service
    if _adaptive_weighting_service is None:
        _adaptive_weighting_service = AdaptiveSignalWeightingService()
    return _adaptive_weighting_service