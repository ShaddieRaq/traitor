"""
Bot signal evaluation service for aggregating multiple signals with Phase 2.3 confirmation system.
"""

from typing import Dict, List, Any, Optional
import json
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.models import Bot, BotSignalHistory
from ..services.signals.base import create_signal_instance
from ..core.database import get_db


class BotSignalEvaluator:
    """Service for evaluating bot signals and making trading decisions with confirmation tracking."""
    
    def __init__(self, db: Session, enable_confirmation: bool = True):
        self.db = db
        self.enable_confirmation = enable_confirmation
    
    def evaluate_bot(self, bot: Bot, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate all enabled signals for a bot and return aggregated decision with confirmation.
        
        Args:
            bot: Bot instance with signal configuration
            market_data: DataFrame with OHLCV data
            
        Returns:
            Dict containing:
            - overall_score: Combined weighted score (-1 to 1)
            - action: buy/sell/hold decision
            - confidence: Overall confidence (0 to 1)
            - signal_results: Individual signal results
            - confirmation_status: Confirmation tracking info
            - metadata: Evaluation metadata
        """
        # Get current price from market data
        current_price = market_data['close'].iloc[-1] if len(market_data) > 0 else 0
        
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
            if not config or not config.get('enabled', False):
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
        
        # Prepare evaluation result
        evaluation_result = {
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
        
        # Check signal confirmation status (only if enabled)
        if self.enable_confirmation:
            confirmation_status = self._check_signal_confirmation(bot, action, overall_score)
        else:
            # Return minimal confirmation status for tests
            confirmation_status = {
                'is_confirmed': True,  # Always confirmed in test mode
                'needs_confirmation': False,
                'status': 'test_mode_always_confirmed',
                'action_being_confirmed': None,
                'confirmation_start': None,
                'confirmation_progress': 1.0,
                'time_remaining_minutes': 0
            }
        
        evaluation_result['confirmation_status'] = confirmation_status
        
        # Save signal history for confirmation tracking
        if self.enable_confirmation:
            self.save_signal_history(bot, evaluation_result, current_price)
        
        return evaluation_result
    
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
    
    def _check_signal_confirmation(self, bot: Bot, current_action: str, current_score: float) -> Dict[str, Any]:
        """Check and update signal confirmation status for Phase 2.3."""
        now = datetime.utcnow()
        confirmation_minutes = bot.confirmation_minutes if bot.confirmation_minutes else 5
        
        # If action is hold, no confirmation needed
        if current_action == 'hold':
            # Reset any active confirmation
            if bot.signal_confirmation_start:
                bot.signal_confirmation_start = None
                self.db.commit()
            
            return {
                'is_confirmed': False,
                'needs_confirmation': False,
                'status': 'hold_no_confirmation_needed',
                'action_being_confirmed': None,
                'confirmation_start': None,
                'confirmation_progress': 0.0,
                'time_remaining_minutes': 0
            }
        
        # Check recent signal history for consistency
        recent_history = (
            self.db.query(BotSignalHistory)
            .filter(BotSignalHistory.bot_id == bot.id)
            .filter(BotSignalHistory.timestamp >= now - timedelta(minutes=confirmation_minutes + 5))
            .order_by(desc(BotSignalHistory.timestamp))
            .all()
        )
        
        # Check if we need to start or reset confirmation
        if not bot.signal_confirmation_start:
            # No active confirmation - start new one
            bot.signal_confirmation_start = now
            self.db.commit()
            
            return {
                'is_confirmed': False,
                'needs_confirmation': True,
                'status': 'confirmation_started',
                'action_being_confirmed': current_action,
                'confirmation_start': now.isoformat(),
                'confirmation_progress': 0.0,
                'time_remaining_minutes': confirmation_minutes
            }
        
        # Check if action has changed since confirmation started
        if recent_history:
            latest_action = recent_history[0].action
            if latest_action != current_action:
                # Action changed - reset confirmation
                bot.signal_confirmation_start = now
                self.db.commit()
                
                return {
                    'is_confirmed': False,
                    'needs_confirmation': True,
                    'status': 'confirmation_reset_action_changed',
                    'action_being_confirmed': current_action,
                    'confirmation_start': now.isoformat(),
                    'confirmation_progress': 0.0,
                    'time_remaining_minutes': confirmation_minutes
                }
        
        # Calculate confirmation progress
        elapsed_minutes = (now - bot.signal_confirmation_start).total_seconds() / 60
        progress = min(elapsed_minutes / confirmation_minutes, 1.0)
        time_remaining = max(confirmation_minutes - elapsed_minutes, 0)
        
        if progress >= 1.0:
            return {
                'is_confirmed': True,
                'needs_confirmation': True,
                'status': 'confirmed',
                'action_being_confirmed': current_action,
                'confirmation_start': bot.signal_confirmation_start.isoformat(),
                'confirmation_progress': 1.0,
                'time_remaining_minutes': 0
            }
        else:
            return {
                'is_confirmed': False,
                'needs_confirmation': True,
                'status': 'confirming',
                'action_being_confirmed': current_action,
                'confirmation_start': bot.signal_confirmation_start.isoformat(),
                'confirmation_progress': progress,
                'time_remaining_minutes': time_remaining
            }
    
    def _determine_action(self, overall_score: float, bot: Bot) -> str:
        """
        Determine trading action based on overall score and bot configuration.
        
        Uses configurable thresholds for buy/sell decisions.
        Default thresholds: buy <= -0.3, sell >= 0.3, hold otherwise
        """
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
            'confirmation_status': {
                'is_confirmed': False,
                'needs_confirmation': False,
                'status': 'error',
                'action_being_confirmed': None,
                'confirmation_start': None,
                'confirmation_progress': 0.0,
                'time_remaining_minutes': 0
            },
            'metadata': {
                'error': error_message,
                'evaluation_timestamp': pd.Timestamp.now().isoformat()
            }
        }
    
    def _convert_to_json_serializable(self, obj):
        """Convert numpy/pandas types to JSON serializable Python types."""
        import numpy as np
        
        if isinstance(obj, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    def save_signal_history(self, bot: Bot, evaluation_result: Dict[str, Any], price: float):
        """Save signal evaluation result to history for confirmation tracking."""
        history_entry = BotSignalHistory(
            bot_id=bot.id,
            timestamp=datetime.utcnow(),
            combined_score=evaluation_result['overall_score'],
            action=evaluation_result['action'],
            confidence=evaluation_result['confidence'],
            signal_scores=json.dumps(self._convert_to_json_serializable(evaluation_result['signal_results'])),
            evaluation_metadata=json.dumps(self._convert_to_json_serializable(evaluation_result['metadata'])),
            price=price
        )
        
        self.db.add(history_entry)
        self.db.commit()
    
    def get_confirmation_status(self, bot: Bot) -> Dict[str, Any]:
        """Get current confirmation status for a bot without running evaluation."""
        if not self.enable_confirmation:
            return {
                'is_confirmed': True,
                'needs_confirmation': False,
                'status': 'test_mode_always_confirmed',
                'action_being_confirmed': None,
                'confirmation_start': None,
                'confirmation_progress': 1.0,
                'time_remaining_minutes': 0
            }
        
        if not bot.signal_confirmation_start:
            return {
                'is_confirmed': False,
                'needs_confirmation': False,
                'status': 'no_active_confirmation',
                'action_being_confirmed': None,
                'confirmation_start': None,
                'confirmation_progress': 0.0,
                'time_remaining_minutes': 0
            }
        
        now = datetime.utcnow()
        confirmation_minutes = bot.confirmation_minutes if bot.confirmation_minutes else 5
        elapsed_minutes = (now - bot.signal_confirmation_start).total_seconds() / 60
        progress = min(elapsed_minutes / confirmation_minutes, 1.0)
        time_remaining = max(confirmation_minutes - elapsed_minutes, 0)
        
        # Get the most recent signal action to know what's being confirmed
        recent_signal = (
            self.db.query(BotSignalHistory)
            .filter(BotSignalHistory.bot_id == bot.id)
            .order_by(desc(BotSignalHistory.timestamp))
            .first()
        )
        
        action_being_confirmed = recent_signal.action if recent_signal else None
        
        if progress >= 1.0:
            status = 'confirmed'
            is_confirmed = True
        else:
            status = 'confirming'
            is_confirmed = False
        
        return {
            'is_confirmed': is_confirmed,
            'needs_confirmation': True,
            'status': status,
            'action_being_confirmed': action_being_confirmed,
            'confirmation_start': bot.signal_confirmation_start.isoformat(),
            'confirmation_progress': progress,
            'time_remaining_minutes': time_remaining
        }
    
    def get_signal_history(self, bot: Bot, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent signal evaluation history for a bot."""
        history_entries = (
            self.db.query(BotSignalHistory)
            .filter(BotSignalHistory.bot_id == bot.id)
            .order_by(desc(BotSignalHistory.timestamp))
            .limit(limit)
            .all()
        )
        
        return [
            {
                'timestamp': entry.timestamp.isoformat(),
                'combined_score': entry.combined_score,
                'action': entry.action,
                'confidence': entry.confidence,
                'signal_scores': json.loads(entry.signal_scores) if entry.signal_scores else {},
                'metadata': json.loads(entry.evaluation_metadata) if entry.evaluation_metadata else {},
                'price': entry.price
            }
            for entry in history_entries
        ]


def get_bot_evaluator(db: Session = None) -> BotSignalEvaluator:
    """Get bot signal evaluator instance."""
    if db is None:
        db = next(get_db())
    return BotSignalEvaluator(db)
