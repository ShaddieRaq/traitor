"""
Bot signal evaluation service for aggregating multiple signals.
"""

from typing import Dict, List, Any, Optional
import json
import pandas as pd
from sqlalchemy.orm import Session

from ..models.models import Bot, BotSignalHistory
from ..services.signals.base import create_signal_instance
from ..core.database import get_db


class BotSignalEvaluator:
    """Service for evaluating bot signals and making trading decisions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def evaluate_bot(self, bot: Bot, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate all enabled signals for a bot and return aggregated decision.
        
        Args:
            bot: Bot instance with signal configuration
            market_data: DataFrame with OHLCV data
            
        Returns:
            Dict containing:
            - overall_score: Combined weighted score (-1 to 1)
            - action: buy/sell/hold decision
            - confidence: Overall confidence (0 to 1)
            - signal_results: Individual signal results
            - metadata: Evaluation metadata
        """
        # Parse signal configuration
        try:
            signal_config = json.loads(bot.signal_config) if isinstance(bot.signal_config, str) else bot.signal_config
        except (json.JSONDecodeError, TypeError):
            return self._error_result("Invalid signal configuration")
        
        if not signal_config:
            return self._error_result("No signal configuration found")
        
        # Evaluate individual signals
        signal_results = {}
        total_weight = 0
        weighted_score_sum = 0
        confidence_values = []
        
        for signal_name, config in signal_config.items():
            if not config.get('enabled', False):
                continue
                
            # Create signal instance
            signal_instance = self._create_signal_instance(signal_name, config)
            if not signal_instance:
                continue
            
            # Calculate signal
            signal_result = signal_instance.calculate(market_data)
            if signal_result['action'] == 'hold' and signal_result['score'] == 0:
                # Skip signals that couldn't calculate (insufficient data, etc.)
                continue
            
            # Store individual result
            signal_results[signal_name] = signal_result
            
            # Aggregate weighted score
            weight = config.get('weight', 0)
            total_weight += weight
            weighted_score_sum += signal_result['score'] * weight
            confidence_values.append(signal_result['confidence'])
        
        # Calculate aggregated results
        if total_weight == 0:
            return self._error_result("No enabled signals with valid weights")
        
        overall_score = weighted_score_sum / total_weight
        overall_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
        
        # Determine action based on overall score and bot thresholds
        action = self._determine_action(overall_score, bot)
        
        return {
            'overall_score': overall_score,
            'action': action,
            'confidence': overall_confidence,
            'signal_results': signal_results,
            'metadata': {
                'bot_id': bot.id,
                'bot_name': bot.name,
                'pair': bot.pair,
                'total_weight': total_weight,
                'enabled_signals': len(signal_results),
                'evaluation_timestamp': pd.Timestamp.now().isoformat()
            }
        }
    
    def _create_signal_instance(self, signal_name: str, config: Dict[str, Any]):
        """Create signal instance from configuration."""
        # Map bot config signal names to signal factory names
        signal_type_map = {
            'rsi': 'RSI',
            'moving_average': 'MA_Crossover',
            'macd': 'MACD'
        }
        
        signal_type = signal_type_map.get(signal_name.lower())
        if not signal_type:
            return None
        
        # Extract parameters (exclude 'enabled' and 'weight')
        parameters = {k: v for k, v in config.items() if k not in ['enabled', 'weight']}
        
        # Map bot config parameter names to signal parameter names
        if signal_name.lower() == 'rsi':
            parameters = {
                'period': parameters.get('period', 14),
                'oversold': parameters.get('buy_threshold', 30),
                'overbought': parameters.get('sell_threshold', 70)
            }
        elif signal_name.lower() == 'moving_average':
            parameters = {
                'fast_period': parameters.get('fast_period', 10),
                'slow_period': parameters.get('slow_period', 20)
            }
        elif signal_name.lower() == 'macd':
            parameters = {
                'fast_period': parameters.get('fast_period', 12),
                'slow_period': parameters.get('slow_period', 26),
                'signal_period': parameters.get('signal_period', 9)
            }
        
        return create_signal_instance(signal_type, parameters)
    
    def _determine_action(self, overall_score: float, bot: Bot) -> str:
        """
        Determine trading action based on overall score and bot configuration.
        
        Uses configurable thresholds for buy/sell decisions.
        Default thresholds: buy <= -0.3, sell >= 0.3, hold otherwise
        """
        # TODO: Phase 2.3 - Add configurable action thresholds to bot model
        # Currently using fixed thresholds: buy when score <= -0.5, sell when score >= 0.5
        # Future: Add buy_threshold and sell_threshold fields to Bot model for per-bot customization
        # For now, use reasonable defaults
        buy_threshold = -0.3
        sell_threshold = 0.3
        
        if overall_score <= buy_threshold:
            return 'buy'
        elif overall_score >= sell_threshold:
            return 'sell'
        else:
            return 'hold'
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Return standardized error result."""
        return {
            'overall_score': 0,
            'action': 'hold',
            'confidence': 0,
            'signal_results': {},
            'metadata': {
                'error': error_message,
                'evaluation_timestamp': pd.Timestamp.now().isoformat()
            }
        }
    
    def save_signal_history(self, bot: Bot, evaluation_result: Dict[str, Any]) -> None:
        """Save signal evaluation result to history."""
        history_entry = BotSignalHistory(
            bot_id=bot.id,
            overall_score=evaluation_result['overall_score'],
            action=evaluation_result['action'],
            confidence=evaluation_result['confidence'],
            signal_results=json.dumps(evaluation_result['signal_results']),
            metadata=json.dumps(evaluation_result['metadata'])
        )
        
        self.db.add(history_entry)
        self.db.commit()


def get_bot_evaluator(db: Session = None) -> BotSignalEvaluator:
    """Get bot signal evaluator instance."""
    if db is None:
        db = next(get_db())
    return BotSignalEvaluator(db)
