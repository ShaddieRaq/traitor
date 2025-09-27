"""
Bot signal evaluation service for aggregating multiple signals with Phase 2.3 confirmation system.
"""

from typing import Dict, List, Any
import json
import pandas as pd
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.models import Bot, BotSignalHistory
from ..services.signals.base import create_signal_instance
from ..core.database import get_db
from ..utils.temperature import calculate_bot_temperature, get_temperature_emoji
from ..utils.error_reporting import report_bot_error, ErrorType

logger = logging.getLogger(__name__)


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
        # Performance optimization: Skip signal processing if balance is insufficient
        if hasattr(bot, 'skip_signals_on_low_balance') and bot.skip_signals_on_low_balance:
            balance_check = self._has_minimum_balance_for_any_trade(bot)
            if not balance_check.get('can_trade', True):
                logger.debug(f"Skipping signal processing for bot {bot.id} ({bot.pair}) due to insufficient balance: {balance_check.get('reason', 'unknown')}")
                return {
                    'overall_score': 0.0,
                    'action': 'hold',
                    'confidence': 0.0,
                    'signal_results': {},
                    'confirmation_status': {
                        'confirmed': False,
                        'consecutive_signals': 0,
                        'required_signals': bot.confirmation_minutes,
                        'last_signal_time': None,
                        'message': f'Skipped: {balance_check.get("reason", "Insufficient balance for trading")}'
                    },
                    'metadata': {
                        'evaluation_time': pd.Timestamp.now().isoformat(),
                        'data_points_evaluated': len(market_data),
                        'optimization_skipped': True,
                        'balance_details': balance_check
                    },
                    'automatic_trade': False
                }
        
        # Get current price from market data
        current_price = market_data['close'].iloc[-1] if len(market_data) > 0 else 0
        
        # Parse signal configuration
        try:
            signal_config = json.loads(bot.signal_config) if isinstance(bot.signal_config, str) else bot.signal_config
        except (json.JSONDecodeError, TypeError):
            return self._error_result("Invalid signal configuration", bot)
        
        if not signal_config:
            return self._error_result("No signal configuration found", bot)
        
        # Evaluate individual signals
        signal_results = {}
        total_weight = 0
        weighted_score_sum = 0
        confidence_values = []
        
        for signal_name, config in signal_config.items():
            if not config or not config.get('enabled', False):
                continue
                
            try:
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
                
            except Exception as e:
                # Report signal calculation error
                report_bot_error(
                    error_type=ErrorType.SIGNAL_CALCULATION,
                    message=f"Error calculating {signal_name} signal: {str(e)}",
                    bot_id=bot.id,
                    bot_name=bot.name,
                    details={
                        "signal_name": signal_name,
                        "signal_config": config,
                        "error_type": type(e).__name__
                    }
                )
                logger.warning(f"Error calculating {signal_name} for bot {bot.id}: {e}")
                continue
        
        # Calculate aggregated results
        if total_weight == 0:
            return self._error_result("No enabled signals with valid weights", bot)
        
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
        
        # Phase 3A: Signal Performance Tracking - Record individual signal predictions
        logger.info(f"📊 Starting signal performance tracking for {bot.pair}, signals: {list(signal_results.keys())}")
        try:
            from .signal_performance_tracker import get_signal_performance_tracker
            from .trend_detection_engine import get_trend_engine
            
            # Get current market regime (if trend detection enabled)
            regime = "UNKNOWN"
            if getattr(bot, 'use_trend_detection', False):
                try:
                    trend_engine = get_trend_engine()
                    regime_data = trend_engine.analyze_trend(bot.pair)
                    regime = regime_data.get('regime', 'UNKNOWN')
                except Exception as e:
                    logger.debug(f"Failed to get regime for performance tracking: {e}")
            
            # Record predictions for each signal
            performance_tracker = get_signal_performance_tracker(self.db)
            for signal_name, signal_result in signal_results.items():
                try:
                    from .signal_performance_tracker import SignalPrediction
                    
                    # Create prediction record
                    prediction = SignalPrediction(
                        timestamp=pd.Timestamp.now().to_pydatetime(),
                        pair=bot.pair,
                        regime=regime,
                        signal_type=signal_name,
                        signal_score=signal_result['score'],
                        prediction=signal_result['action'],
                        confidence=signal_result['confidence']
                    )
                    
                    # Record the prediction for later performance evaluation
                    performance_tracker.record_signal_prediction(prediction)
                    
                    logger.info(
                        f"📊 Recorded signal prediction: {signal_name} → {signal_result['action']} "
                        f"(score: {signal_result['score']:.3f}, confidence: {signal_result['confidence']:.3f})"
                    )
                    
                except Exception as prediction_error:
                    logger.warning(f"Failed to record signal prediction for {signal_name}: {prediction_error}")
                    
        except Exception as tracking_error:
            logger.warning(f"Signal performance tracking failed: {tracking_error}")
        
        # Save signal history for confirmation tracking
        if self.enable_confirmation:
            self.save_signal_history(bot, evaluation_result, current_price)
        
        # Phase 2: Position Sizing Intelligence - Calculate dynamic position sizes
        if getattr(bot, 'use_position_sizing', False) and action in ['buy', 'sell']:
            try:
                from .position_sizing_engine import get_position_sizing_engine
                sizing_engine = get_position_sizing_engine()
                
                position_sizing_analysis = sizing_engine.calculate_position_size(
                    base_position_size=bot.position_size_usd,
                    product_id=bot.pair,
                    signal_confidence=overall_confidence
                )
                
                evaluation_result['position_sizing'] = position_sizing_analysis
                logger.info(
                    f"💰 Position sizing for {bot.pair}: ${bot.position_size_usd} → "
                    f"${position_sizing_analysis['final_position_size']} "
                    f"({position_sizing_analysis['total_multiplier']:.2f}x)"
                )
                
            except Exception as e:
                logger.warning(f"Position sizing calculation failed for {bot.pair}: {e}")
                evaluation_result['position_sizing'] = {
                    'error': str(e),
                    'base_position_size': bot.position_size_usd,
                    'final_position_size': bot.position_size_usd,  # Fallback to base size
                    'total_multiplier': 1.0
                }
        else:
            # Static position sizing for non-position-sizing bots or hold actions
            use_position_sizing = getattr(bot, 'use_position_sizing', False)
            if use_position_sizing:
                rationale = f'Static position sizing (action={action}, position sizing only applies to buy/sell)'
            else:
                rationale = 'Static position sizing (use_position_sizing=False)'
            
            evaluation_result['position_sizing'] = {
                'base_position_size': bot.position_size_usd,
                'final_position_size': bot.position_size_usd,
                'total_multiplier': 1.0,
                'sizing_rationale': rationale
            }
        
        # Phase 4.2.1: Automatic trade execution on confirmed signals
        if self._should_execute_automatic_trade(bot, evaluation_result):
            automatic_trade_result = self._execute_automatic_trade(bot, evaluation_result)
            evaluation_result['automatic_trade'] = automatic_trade_result
            
            # CRITICAL: Reset confirmation state after trade execution (success or failure)
            # This prevents bots from getting stuck in confirmation state
            logger.info(f"🔄 Resetting confirmation state for bot {bot.id} after trade execution")
            bot.signal_confirmation_start = None
            self.db.commit()
            
        else:
            evaluation_result['automatic_trade'] = None
        
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
        Determine trading action based on overall score and bot-specific thresholds.
        
        Phase 1D: Market Regime Intelligence - Dynamic thresholds based on trend regime.
        Supports per-bot threshold configuration via signal_config.trading_thresholds
        Falls back to default thresholds if not configured.
        """
        
        # Phase 1D: Check if this bot uses trend-adaptive thresholds
        if getattr(bot, 'use_trend_detection', False):
            try:
                from .trend_detection_engine import get_trend_engine
                trend_engine = get_trend_engine()
                regime_data = trend_engine.analyze_trend(bot.pair)
                
                # Dynamic thresholds based on market regime
                if regime_data['regime'] == 'STRONG_TRENDING':
                    # Very tight thresholds for strong trends - most responsive
                    buy_threshold = -0.02
                    sell_threshold = 0.02
                    regime_reason = f"STRONG_TRENDING ({regime_data['trend_strength']:.3f})"
                elif regime_data['regime'] == 'TRENDING':
                    # Tight thresholds for trending markets - more responsive
                    buy_threshold = -0.03
                    sell_threshold = 0.03
                    regime_reason = f"TRENDING ({regime_data['trend_strength']:.3f})"
                elif regime_data['regime'] == 'RANGING':
                    # Loose thresholds for ranging markets - less noise
                    buy_threshold = -0.08
                    sell_threshold = 0.08
                    regime_reason = f"RANGING ({regime_data['trend_strength']:.3f})"
                elif regime_data['regime'] == 'CHOPPY':
                    # Very loose thresholds for choppy markets - avoid false signals
                    buy_threshold = -0.12
                    sell_threshold = 0.12
                    regime_reason = f"CHOPPY ({regime_data['trend_strength']:.3f})"
                else:
                    # Fallback to moderate thresholds
                    buy_threshold = -0.05
                    sell_threshold = 0.05
                    regime_reason = f"UNKNOWN ({regime_data['trend_strength']:.3f})"
                
                logger.info(f"🎯 Regime-adaptive thresholds for {bot.pair}: {regime_reason} → buy={buy_threshold}, sell={sell_threshold}")
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to get trend regime for {bot.pair}, using static thresholds: {e}")
                # Fallback to static threshold logic
                buy_threshold = -0.05
                sell_threshold = 0.05
        else:
            # Original static threshold logic for non-regime bots
            # Check for bot-specific thresholds in signal_config
            try:
                signal_config = json.loads(bot.signal_config) if isinstance(bot.signal_config, str) else bot.signal_config
                if signal_config and 'trading_thresholds' in signal_config:
                    thresholds = signal_config['trading_thresholds']
                    buy_threshold = thresholds.get('buy_threshold', -0.1)
                    sell_threshold = thresholds.get('sell_threshold', 0.1)
                    logger.info(f"Using custom thresholds for {bot.pair}: buy={buy_threshold}, sell={sell_threshold}")
                else:
                    # Default thresholds for static bots
                    buy_threshold = -0.05  # System-wide optimized threshold
                    sell_threshold = 0.05   # System-wide optimized threshold
            except Exception as e:
                # Fallback to default if any error
                buy_threshold = -0.05
                sell_threshold = 0.05
                logger.warning(f"Error reading thresholds for {bot.pair}, using defaults: {e}")
        
        if overall_score <= buy_threshold:
            return 'buy'
        elif overall_score >= sell_threshold:
            return 'sell'
        else:
            return 'hold'
    
    def _error_result(self, error_message: str, bot: Bot = None) -> Dict[str, Any]:
        """Return standardized error result and report to error tracking."""
        # Report the error to our tracking system
        if bot:
            report_bot_error(
                error_type=ErrorType.CONFIGURATION,
                message=error_message,
                bot_id=bot.id,
                bot_name=bot.name,
                details={
                    "signal_config": bot.signal_config,
                    "trading_pair": bot.pair,
                    "evaluation_timestamp": pd.Timestamp.now().isoformat()
                }
            )
        
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
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'tolist'):  # pandas/numpy objects with tolist method
            return obj.tolist()
        elif hasattr(obj, 'item'):  # numpy scalars
            return obj.item()
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
    
    def calculate_bot_temperature_light(self, bot: Bot, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate bot temperature WITHOUT triggering automatic trading.
        Used for status displays and dashboard to prevent performance issues.
        """
        try:
            # Use the same signal evaluation logic as the full evaluation but without automatic trading
            signal_results = {}
            total_score = 0.0
            total_weight = 0.0
            
            # Parse signal configuration (handle JSON string from database)
            if isinstance(bot.signal_config, str):
                signal_config = json.loads(bot.signal_config)
            else:
                signal_config = bot.signal_config
            
            # RSI Signal
            rsi_config = signal_config.get('rsi')
            if rsi_config and rsi_config.get('enabled', False):
                try:
                    rsi_signal = self._create_signal_instance('rsi', rsi_config)
                    if rsi_signal:
                        rsi_result = rsi_signal.calculate(market_data)  # Fixed: use calculate() not evaluate()
                        if rsi_result and 'score' in rsi_result:
                            signal_results['rsi'] = rsi_result
                            weight = rsi_config.get('weight', 1.0)
                            total_score += rsi_result['score'] * weight
                            total_weight += weight
                except Exception as e:
                    logger.warning(f"RSI calculation failed in lightweight mode: {e}")
            
            # Moving Average Signal
            ma_config = signal_config.get('moving_average')
            if ma_config and ma_config.get('enabled', False):
                try:
                    ma_signal = self._create_signal_instance('moving_average', ma_config)
                    if ma_signal:
                        ma_result = ma_signal.calculate(market_data)  # Fixed: use calculate() not evaluate()
                        if ma_result and 'score' in ma_result:
                            signal_results['moving_average'] = ma_result
                            weight = ma_config.get('weight', 1.0)
                            total_score += ma_result['score'] * weight
                            total_weight += weight
                except Exception as e:
                    logger.warning(f"MA calculation failed in lightweight mode: {e}")
            
            # MACD Signal
            macd_config = signal_config.get('macd')
            if macd_config and macd_config.get('enabled', False):
                try:
                    macd_signal = self._create_signal_instance('macd', macd_config)
                    if macd_signal:
                        macd_result = macd_signal.calculate(market_data)  # Fixed: use calculate() not evaluate()
                        if macd_result and 'score' in macd_result:
                            signal_results['macd'] = macd_result
                            weight = macd_config.get('weight', 1.0)
                            total_score += macd_result['score'] * weight
                            total_weight += weight
                except Exception as e:
                    logger.warning(f"MACD calculation failed in lightweight mode: {e}")
                    if macd_signal:
                        macd_result = macd_signal.calculate(market_data)  # Fixed: use calculate() not evaluate()
                        if macd_result and 'score' in macd_result:
                            signal_results['macd'] = macd_result
                            weight = macd_config.get('weight', 1.0)
                            total_score += macd_result['score'] * weight
                            total_weight += weight
                except Exception as e:
                    logger.warning(f"MACD calculation failed in lightweight mode: {e}")
            
            # Calculate final score and temperature
            overall_score = total_score / max(total_weight, 1.0) if total_weight > 0 else 0.0
            temperature = calculate_bot_temperature(overall_score)
            
            # Calculate distance to thresholds (match full evaluation logic)
            buy_threshold = -0.3
            sell_threshold = 0.3
            
            if overall_score > 0:  # Bullish territory
                distance_to_sell = sell_threshold - overall_score
                distance_to_action = max(0, distance_to_sell)
            else:  # Bearish territory
                distance_to_buy = abs(buy_threshold) - abs(overall_score)
                distance_to_action = max(0, distance_to_buy)
            
            return {
                'score': overall_score,
                'temperature': temperature,
                'distance_to_action': distance_to_action,
                'signal_results': signal_results
            }
            
        except Exception as e:
            logger.error(f"Error in lightweight temperature calculation: {e}")
            return {
                'score': 0.0,
                'temperature': 'FROZEN',
                'distance_to_action': 1.0,
                'signal_results': {}
            }

    def calculate_bot_temperature(self, bot: Bot, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate bot temperature based on signal proximity to trading thresholds.
        
        Temperature levels:
        - Hot 🔥: Very close to trading (score > 0.3 or < -0.3)
        - Warm 🌡️: Moderately close (score > 0.15 or < -0.15)  
        - Cool ❄️: Some interest (score > 0.05 or < -0.05)
        - Frozen 🧊: No trading interest (score between -0.05 and 0.05)
        
        Args:
            bot: Bot instance
            market_data: Current market data
            
        Returns:
            Dict containing:
            - temperature: hot/warm/cool/frozen
            - temperature_emoji: 🔥/🌡️/❄️/🧊
            - score: Current combined score
            - distance_to_action: How close to buy/sell threshold
            - next_action: What action would be taken if threshold crossed
            - threshold_info: Details about thresholds
        """
        # Get current evaluation
        evaluation = self.evaluate_bot(bot, market_data)
        score = evaluation['overall_score']
        action = evaluation['action']
        
        # Calculate temperature based on absolute score
        abs_score = abs(score)
        temperature = calculate_bot_temperature(score)
        temperature_emoji = get_temperature_emoji(temperature)
        
        # Calculate distance to action thresholds
        buy_threshold = -0.3  # Default buy threshold
        sell_threshold = 0.3  # Default sell threshold
        
        if score > 0:  # Bullish territory
            distance_to_sell = sell_threshold - score
            distance_to_action = max(0, distance_to_sell)
            next_action = "sell" if distance_to_action <= 0 else "approaching_sell"
        else:  # Bearish territory
            distance_to_buy = abs(buy_threshold) - abs(score)
            distance_to_action = max(0, distance_to_buy)
            next_action = "buy" if distance_to_action <= 0 else "approaching_buy"
        
        result = {
            'temperature': temperature,
            'temperature_emoji': temperature_emoji,
            'score': score,
            'abs_score': abs_score,
            'distance_to_action': round(distance_to_action, 3),
            'next_action': next_action,
            'current_action': action,
            'threshold_info': {
                'buy_threshold': buy_threshold,
                'sell_threshold': sell_threshold,
                'in_buy_zone': score <= buy_threshold,
                'in_sell_zone': score >= sell_threshold,
                'in_neutral_zone': buy_threshold < score < sell_threshold
            },
            'confirmation_status': evaluation['confirmation_status'],
            'signal_breakdown': evaluation['signal_results']
        }
        
        # Ensure all values are JSON serializable
        return self._convert_to_json_serializable(result)
    
    def get_all_bot_temperatures(self, market_data_cache: Dict[str, pd.DataFrame] = None) -> List[Dict[str, Any]]:
        """
        Get temperature status for all active bots.
        
        Args:
            market_data_cache: Optional cache of market data by trading pair
            
        Returns:
            List of bot temperature data
        """
        bots = self.db.query(Bot).filter(Bot.status == 'RUNNING').all()
        temperatures = []
        
        for bot in bots:
            try:
                # Use cached market data if available, otherwise create fallback data
                if market_data_cache and bot.pair in market_data_cache:
                    market_data = market_data_cache[bot.pair]
                else:
                    # Create minimal fallback data for temperature calculation
                    market_data = pd.DataFrame({
                        'close': [100.0],  # Fallback price
                        'high': [101.0],
                        'low': [99.0],
                        'open': [100.5],
                        'volume': [1000]
                    })
                
                temp_data = self.calculate_bot_temperature(bot, market_data)
                
                # Update the bot's current_combined_score in the database
                try:
                    bot.current_combined_score = temp_data.get('score', 0.0)
                    self.db.commit()
                except Exception as e:
                    self.db.rollback()
                    logger.warning(f"Failed to update bot score in database: {e}")
                
                temp_data.update({
                    'bot_id': bot.id,
                    'bot_name': bot.name,
                    'pair': bot.pair,
                    'status': bot.status
                })
                temperatures.append(temp_data)
                
            except Exception as e:
                # Add error entry for debugging
                temperatures.append({
                    'bot_id': bot.id,
                    'bot_name': bot.name,
                    'pair': bot.pair,
                    'status': bot.status,
                    'temperature': 'error',
                    'temperature_emoji': '❌',
                    'error': str(e)
                })
        
        return temperatures

    # Phase 4.2.1: Automatic Trading Integration Methods
    
    def _should_execute_automatic_trade(self, bot: Bot, evaluation_result: Dict[str, Any]) -> bool:
        """
        Determine if automatic trade should be executed based on bot status and signal confirmation.
        
        Args:
            bot: Bot instance
            evaluation_result: Signal evaluation result with confirmation status
            
        Returns:
            bool: True if automatic trade should be executed
        """
        # Check basic prerequisites for automatic trading
        if bot.status != 'RUNNING':
            logger.debug(f"Bot {bot.id} not running - no automatic trade")
            return False
        
        # Check if signal is confirmed
        confirmation_status = evaluation_result.get('confirmation_status', {})
        if not confirmation_status.get('is_confirmed', False):
            logger.debug(f"Bot {bot.id} signal not confirmed - no automatic trade")
            return False
        
        # Check if action requires trading (not 'hold')
        action = evaluation_result.get('action')
        if action not in ['buy', 'sell']:
            logger.debug(f"Bot {bot.id} action '{action}' - no automatic trade needed")
            return False
        
        # Check for existing pending orders FIRST (critical fix)
        if not self._check_no_pending_orders(bot):
            logger.debug(f"Bot {bot.id} has pending orders - no automatic trade")
            return False
        
        # NOTE: Cooldown check moved to TradingService for atomic transaction handling
        # This prevents race conditions where multiple requests bypass cooldown simultaneously
        
        # Check balance validation before attempting trade
        if not self._check_balance_for_automatic_trade(bot, action):
            logger.warning(f"Bot {bot.id} insufficient balance for {action} trade - no automatic trade")
            return False
        
        logger.info(f"Bot {bot.id} ready for automatic {action} trade")
        return True
    
    # DEPRECATED: Cooldown check moved to TradingService for atomic transaction handling
    # This prevents race conditions where multiple requests bypass cooldown simultaneously
    def _check_trade_cooldown(self, bot: Bot) -> bool:
        """
        DEPRECATED: Cooldown validation moved to TradingService._get_bot_with_trade_lock()
        
        This method is kept for backward compatibility but always returns True.
        The actual cooldown validation is now done atomically within the trading
        service transaction to prevent race conditions.
        """
        logger.debug(f"Bot {bot.id} cooldown check delegated to TradingService")
        return True
    
    def _check_no_pending_orders(self, bot: Bot) -> bool:
        """
        Check that bot has no pending orders before placing a new one.
        Critical fix to prevent multiple open orders for same bot.
        
        Args:
            bot: Bot instance
            
        Returns:
            bool: True if no pending orders exist
        """
        try:
            # Import here to avoid circular dependency
            from ..models.models import Trade
            
            # Check for any pending orders for this bot
            pending_orders = (
                self.db.query(Trade)
                .filter(Trade.bot_id == bot.id)
                .filter(Trade.status.in_(["pending", "open", "active"]))
                .filter(Trade.order_id.isnot(None))  # Only real orders with order_ids
                .count()
            )
            
            if pending_orders > 0:
                logger.warning(f"Bot {bot.id} has {pending_orders} pending orders - blocking new trade")
                return False
            
            logger.debug(f"Bot {bot.id} has no pending orders - can place new trade")
            return True
                
        except Exception as e:
            logger.error(f"Error checking pending orders for bot {bot.id}: {str(e)}")
            # On error, block trade (fail safe)
            return False
    
    def _check_balance_for_automatic_trade(self, bot: Bot, action: str) -> bool:
        """
        Check if bot has sufficient balance for automatic trade execution.
        
        Args:
            bot: Bot instance
            action: Trade action ('buy' or 'sell')
            
        Returns:
            bool: True if sufficient balance exists
        """
        try:
            from ..services.coinbase_service import coinbase_service
            
            # Get current market price
            ticker = coinbase_service.get_product_ticker(bot.pair)
            if not ticker or 'price' not in ticker:
                logger.error(f"Could not get price for {bot.pair} - blocking automatic trade")
                return False
            
            current_price = float(ticker['price'])
            trade_size_usd = bot.position_size_usd
            
            # Validate balance for the specific action
            balance_result = coinbase_service.validate_trade_balance(
                product_id=bot.pair,
                side=action.upper(),
                size_usd=trade_size_usd,
                current_price=current_price
            )
            
            if balance_result["valid"]:
                logger.debug(f"Bot {bot.id} balance check passed for {action}: {balance_result['message']}")
                return True
            else:
                logger.warning(f"Bot {bot.id} balance check failed for {action}: {balance_result['message']}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking balance for bot {bot.id} {action} trade: {str(e)}")
            # On error, block trade (fail safe)
            return False
    
    def _execute_automatic_trade(self, bot: Bot, evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute automatic trade based on confirmed signal evaluation.
        
        Args:
            bot: Bot instance
            evaluation_result: Signal evaluation result with confirmed action
            
        Returns:
            Dict with trade execution result
        """
        try:
            # Import here to avoid circular dependency
            from ..services.trading_service import TradingService
            
            action = evaluation_result.get('action')
            logger.info(f"Executing automatic {action} trade for bot {bot.id} ({bot.name})")
            
            # Initialize trading service with database session
            trading_service = TradingService(db=self.db)
            
            # Get current temperature from the evaluation result score (no fresh data needed)
            current_score = evaluation_result.get('overall_score', 0.0)
            from ..utils.temperature import calculate_bot_temperature
            current_temperature = calculate_bot_temperature(current_score)
            logger.info(f"🌡️ Using temperature: {current_temperature} (score: {current_score})")
            
            # Execute trade with intelligent sizing (Phase 2 + 4.1.3 integration)
            # Use calculated position size if available, otherwise fall back to auto-sizing
            calculated_size = None
            if 'position_sizing' in evaluation_result and evaluation_result['position_sizing'].get('final_position_size'):
                calculated_size = evaluation_result['position_sizing']['final_position_size']
                logger.info(f"💰 Using Phase 2 calculated position size: ${calculated_size}")
            
            trade_result = trading_service.execute_trade(
                bot_id=bot.id,
                side=action.upper(),  # Convert to uppercase ('BUY' or 'SELL')
                size_usd=calculated_size,  # Use Phase 2 calculated size or None for auto-sizing
                current_temperature=current_temperature,  # Pass current temperature
                auto_size=(calculated_size is None)  # Only use auto-sizing if we don't have calculated size
            )
            
            # Log trade execution result with proper classification
            if trade_result.get('success'):
                if trade_result.get('status') == 'blocked':
                    # Normal blocking condition - not an error
                    logger.info(
                        f"📋 Automatic {action} trade blocked for bot {bot.id}: "
                        f"{trade_result.get('blocking_reason', 'unknown condition')} (normal trading condition)"
                    )
                else:
                    # Actual successful trade execution
                    logger.info(
                        f"✅ Automatic {action} trade executed successfully for bot {bot.id}: "
                        f"Trade ID {trade_result.get('trade_id')}"
                    )
            else:
                # Actual system errors
                error_message = trade_result.get('message', 'Unknown error')
                logger.warning(
                    f"⚠️ Automatic {action} trade failed for bot {bot.id}: "
                    f"{error_message} (actual system error)"
                )
            
            return {
                'executed': trade_result.get('success', False),
                'trade_id': trade_result.get('trade_id'),
                'action': action,
                'message': trade_result.get('message', ''),
                'execution_timestamp': datetime.utcnow().isoformat(),
                'bot_id': bot.id,
                'bot_name': bot.name,
                'full_trade_result': trade_result  # Include full result for debugging
            }
            
        except Exception as e:
            error_msg = f"Error executing automatic trade for bot {bot.id}: {str(e)}"
            logger.error(error_msg)
            
            return {
                'executed': False,
                'trade_id': None,
                'action': evaluation_result.get('action'),
                'message': error_msg,
                'execution_timestamp': datetime.utcnow().isoformat(),
                'bot_id': bot.id,
                'bot_name': bot.name,
                'error': str(e)
            }

    def _has_minimum_balance_for_any_trade(self, bot: Bot) -> Dict[str, Any]:
        """
        Quick balance check to determine if bot can potentially trade.
        Much faster than full trade validation - checks basic thresholds only.
        
        This method uses cached account data when available to minimize API calls
        and provides a fast way to skip expensive signal processing when balance
        is clearly insufficient for any trading activity.
        
        Args:
            bot: Bot instance
            
        Returns:
            Dict with 'can_trade', 'reason', 'details', and 'balances'
        """
        try:
            from ..services.coinbase_service import coinbase_service
            
            # Parse trading pair for currency identification
            base_currency, quote_currency = bot.pair.split('-')
            
            # Get basic account balances (uses cache when available)
            usd_balance = coinbase_service.get_available_balance('USD')
            crypto_balance = coinbase_service.get_available_balance(base_currency)
            
            # Define conservative minimum thresholds (much looser than exact trade validation)
            # These are designed to catch obvious insufficient balance cases early
            min_usd_for_buy = 5.0    # Conservative minimum for any USD buy order
            min_crypto_for_sell = {   # Minimum crypto amounts for sell orders
                'BTC': 0.00001,      # ~$0.50 worth
                'ETH': 0.001,        # ~$2-3 worth
                'SOL': 0.01,         # ~$1-2 worth
                'DOGE': 1.0,         # ~$0.10 worth
                'XRP': 1.0,          # ~$0.50 worth
                'AVNT': 1.0,         # ~$0.80 worth
                'AERO': 0.1,         # ~$0.10 worth
                'SUI': 0.1           # ~$1-2 worth
            }
            
            min_crypto_threshold = min_crypto_for_sell.get(base_currency, 0.001)
            
            # Check if bot can potentially buy (needs USD)
            can_buy = usd_balance >= min_usd_for_buy
            
            # Check if bot can potentially sell (needs crypto)
            can_sell = crypto_balance >= min_crypto_threshold
            
            # Determine overall trading capability
            if not can_buy and not can_sell:
                return {
                    'can_trade': False,
                    'reason': 'insufficient_balance_all',
                    'details': f'Cannot buy (${usd_balance:.2f} < ${min_usd_for_buy}) or sell ({crypto_balance:.6f} {base_currency} < {min_crypto_threshold})',
                    'balances': {
                        'usd': usd_balance,
                        'crypto': crypto_balance,
                        'crypto_currency': base_currency
                    },
                    'thresholds': {
                        'min_usd': min_usd_for_buy,
                        'min_crypto': min_crypto_threshold
                    }
                }
            elif not can_buy:
                return {
                    'can_trade': True,
                    'reason': 'sell_only',
                    'details': f'Can sell {base_currency} but cannot buy (${usd_balance:.2f} < ${min_usd_for_buy})',
                    'balances': {
                        'usd': usd_balance,
                        'crypto': crypto_balance,
                        'crypto_currency': base_currency
                    }
                }
            elif not can_sell:
                return {
                    'can_trade': True,
                    'reason': 'buy_only',
                    'details': f'Can buy with USD but cannot sell {base_currency} ({crypto_balance:.6f} < {min_crypto_threshold})',
                    'balances': {
                        'usd': usd_balance,
                        'crypto': crypto_balance,
                        'crypto_currency': base_currency
                    }
                }
            else:
                return {
                    'can_trade': True,
                    'reason': 'sufficient_balance',
                    'details': f'Can both buy (${usd_balance:.2f}) and sell ({crypto_balance:.6f} {base_currency})',
                    'balances': {
                        'usd': usd_balance,
                        'crypto': crypto_balance,
                        'crypto_currency': base_currency
                    }
                }
                
        except Exception as e:
            # On error, allow signal processing (fail safe approach)
            logger.warning(f"Balance pre-check failed for bot {bot.id}: {str(e)} - allowing signal processing")
            return {
                'can_trade': True,
                'reason': 'error_assume_yes',
                'details': f'Balance check failed: {str(e)}',
                'balances': None,
                'error': str(e)
            }


def get_bot_evaluator(db: Session = None) -> BotSignalEvaluator:
    """Get bot signal evaluator instance."""
    if db is None:
        db = next(get_db())
    return BotSignalEvaluator(db)
