"""
System Diagnostics API
Exposes critical system parameters that users need to understand why bots aren't trading
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.models import Bot
from ...services.bot_evaluator import BotSignalEvaluator
from ...services.market_data_service import get_market_data_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system-diagnostics", tags=["System Diagnostics"])


@router.get("/trading-parameters")
def get_trading_parameters() -> Dict[str, Any]:
    """
    Get critical system parameters that affect trading decisions.
    These are the hidden values users need to understand why bots aren't trading.
    """
    return {
        "signal_quality": {
            "min_confidence_threshold": 0.2,
            "description": "Minimum confidence required for any trade (20%)",
            "impact": "Signals below this confidence are rejected and default to 'hold'"
        },
        "trading_thresholds": {
            "default_buy_threshold": -0.05,
            "default_sell_threshold": 0.05,
            "description": "Default signal score thresholds for triggering trades",
            "impact": "Scores must exceed these values to trigger buy/sell actions"
        },
        "regime_adaptive_thresholds": {
            "strong_trending": {"buy": -0.12, "sell": 0.12},
            "trending": {"buy": -0.08, "sell": 0.08},
            "ranging": {"buy": -0.05, "sell": 0.05},
            "choppy": {"buy": -0.03, "sell": 0.03},
            "description": "Dynamic thresholds based on market regime (for trend-enabled bots)",
            "impact": "Choppy markets require stronger signals to avoid false trades"
        },
        "balance_requirements": {
            "description": "Minimum balances required for trading",
            "buy_trades": "Sufficient USD balance for position_size_usd amount",
            "sell_trades": "Sufficient crypto holdings for the trade size",
            "impact": "All trades blocked if insufficient balances"
        },
        "confirmation_system": {
            "default_confirmation_minutes": "Varies by bot (typically 1-5 minutes)",
            "description": "Signal must persist for confirmation period before trading",
            "impact": "Prevents trading on brief signal spikes"
        }
    }


@router.get("/threshold-transparency")
def get_threshold_transparency() -> Dict[str, Any]:
    """
    Get all system thresholds that affect trading decisions for transparency.
    Shows hidden parameters that users should understand.
    """
    return {
        "critical_thresholds": {
            "signal_confidence": {
                "minimum": 0.2,
                "description": "20% minimum confidence required for any trade",
                "impact": "Bots with lower confidence show 'hold' regardless of signal strength",
                "visibility": "Now shown on bot cards with red/green color coding"
            },
            "trading_thresholds": {
                "default_buy": -0.05,
                "default_sell": 0.05,
                "description": "Default signal score thresholds",
                "impact": "Signal must exceed these values to trigger trades",
                "visibility": "Shown in advanced bot cards and diagnostics"
            }
        },
        "balance_requirements": {
            "minimum_usd_buy": 5.0,
            "description": "Absolute minimum USD balance for any buy order",
            "actual_requirement": "Usually $20-50 based on bot position size",
            "impact": "All buy orders blocked if below this threshold",
            "visibility": "Now shown on blocked bot cards",
            "per_crypto_minimums": {
                "BTC": 0.00001,
                "ETH": 0.001,
                "SOL": 0.01,
                "DOGE": 1.0,
                "XRP": 1.0,
                "other": 0.001
            }
        },
        "position_sizing_limits": {
            "risk_multiplier_min": 0.2,
            "risk_multiplier_max": 3.0,
            "description": "Position sizes are scaled by risk multipliers",
            "impact": "Actual trade size can be 20%-300% of configured position_size_usd",
            "visibility": "Hidden - should be shown to users"
        },
        "coinbase_limits": {
            "minimum_trade_usd": 10.0,
            "description": "Coinbase minimum order size",
            "impact": "Trades below $10 are rejected by exchange",
            "visibility": "Users see error messages but not preventive warnings"
        },
        "emergency_controls": {
            "emergency_stop_loss": 50.0,
            "description": "System emergency stop if any bot loses this amount",
            "impact": "All trading halted if single bot loses $50+",
            "visibility": "Hidden - users should be aware of this limit"
        },
        "dynamic_regime_thresholds": {
            "choppy": {"buy": -0.03, "sell": 0.03},
            "ranging": {"buy": -0.05, "sell": 0.05},
            "trending": {"buy": -0.08, "sell": 0.08},
            "strong_trending": {"buy": -0.12, "sell": 0.12},
            "description": "Thresholds automatically adjust based on market conditions",
            "impact": "Same signal strength may or may not trigger trades in different market regimes",
            "visibility": "Partially visible - regime shown but not active thresholds"
        },
        "confirmation_requirements": {
            "default_minutes": 1,
            "range": "1-5 minutes depending on bot configuration",
            "description": "Signals must persist for confirmation period",
            "impact": "Prevents trading on brief signal spikes",
            "visibility": "Shown in trade readiness status"
        }
    }


@router.get("/bot-diagnostics/{bot_id}")
def get_bot_diagnostics(bot_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get detailed diagnostics for why a specific bot isn't trading.
    Includes real-time signal evaluation with all decision factors.
    """
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    try:
        # Get market data and evaluate bot in real-time
        market_service = get_market_data_service()
        market_data = market_service.get_candles(bot.pair, granularity='ONE_HOUR', limit=30)
        
        evaluator = BotSignalEvaluator(db)
        result = evaluator.evaluate_bot(bot, market_data)
        
        # Determine why bot isn't trading
        blocking_factors = []
        
        # Check confidence threshold
        min_confidence = 0.2
        if result['confidence'] < min_confidence:
            blocking_factors.append({
                "factor": "low_confidence",
                "description": f"Signal confidence {result['confidence']:.1%} < {min_confidence:.0%} required",
                "severity": "high",
                "current_value": result['confidence'],
                "required_value": min_confidence
            })
        
        # Check action determination
        if result['action'] == 'hold':
            if result['overall_score'] > -0.05 and result['overall_score'] < 0.05:
                blocking_factors.append({
                    "factor": "weak_signal",
                    "description": f"Signal score {result['overall_score']:.3f} within hold range (±0.05)",
                    "severity": "medium",
                    "current_value": result['overall_score'],
                    "required_value": "< -0.05 (buy) or > 0.05 (sell)"
                })
        
        # Check if confirmation is needed
        confirmation_status = result.get('confirmation_status', {})
        if confirmation_status.get('needs_confirmation'):
            blocking_factors.append({
                "factor": "awaiting_confirmation",
                "description": f"Signal needs {confirmation_status.get('time_remaining_minutes', 0):.1f} more minutes of confirmation",
                "severity": "low",
                "current_value": confirmation_status.get('confirmation_progress', 0),
                "required_value": 1.0
            })
        
        return {
            "bot_info": {
                "id": bot.id,
                "pair": bot.pair,
                "status": bot.status,
                "position_size_usd": bot.position_size_usd
            },
            "real_time_evaluation": {
                "overall_score": result['overall_score'],
                "action": result['action'],
                "confidence": result['confidence'],
                "individual_signals": {
                    signal: {
                        "score": data['score'],
                        "action": data['action'],
                        "confidence": data['confidence']
                    }
                    for signal, data in result['signal_results'].items()
                }
            },
            "trading_eligibility": {
                "can_trade": len(blocking_factors) == 0,
                "blocking_factors": blocking_factors
            },
            "system_parameters": {
                "min_confidence_threshold": min_confidence,
                "trading_thresholds": {
                    "buy": -0.05,
                    "sell": 0.05
                },
                "trend_detection_enabled": getattr(bot, 'use_trend_detection', False),
                "position_sizing_enabled": getattr(bot, 'use_position_sizing', False)
            }
        }
        
    except Exception as e:
        logger.error(f"Error evaluating bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error evaluating bot: {str(e)}")


@router.get("/trading-blocks-summary")
def get_trading_blocks_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get summary of why bots across the system aren't trading.
    Useful for understanding overall system constraints.
    """
    # Get all active bots
    bots = db.query(Bot).filter(Bot.status == 'RUNNING').all()
    
    # Categorize blocking reasons
    blocking_summary = {
        "total_bots": len(bots),
        "bots_with_strong_signals": 0,
        "blocking_reasons": {
            "low_confidence": 0,
            "insufficient_balance": 0,
            "weak_signals": 0,
            "awaiting_confirmation": 0,
            "system_errors": 0
        },
        "examples": []
    }
    
    try:
        market_service = get_market_data_service()
        evaluator = BotSignalEvaluator(db)
        
        for bot in bots[:10]:  # Sample first 10 bots for performance
            try:
                market_data = market_service.get_candles(bot.pair, granularity='ONE_HOUR', limit=30)
                result = evaluator.evaluate_bot(bot, market_data)
                
                # Check if bot has strong signal
                if abs(result['overall_score']) > 0.05:
                    blocking_summary["bots_with_strong_signals"] += 1
                    
                    # Determine primary blocking reason
                    if result['confidence'] < 0.2:
                        blocking_summary["blocking_reasons"]["low_confidence"] += 1
                        primary_block = "low_confidence"
                    elif result['action'] == 'hold':
                        blocking_summary["blocking_reasons"]["weak_signals"] += 1
                        primary_block = "weak_signals"
                    else:
                        # Would need balance check here
                        blocking_summary["blocking_reasons"]["insufficient_balance"] += 1
                        primary_block = "insufficient_balance"
                    
                    # Add example
                    if len(blocking_summary["examples"]) < 5:
                        blocking_summary["examples"].append({
                            "bot_id": bot.id,
                            "pair": bot.pair,
                            "score": result['overall_score'],
                            "confidence": result['confidence'],
                            "action": result['action'],
                            "primary_blocking_reason": primary_block
                        })
                        
            except Exception as e:
                logger.warning(f"Error evaluating bot {bot.id} in summary: {e}")
                blocking_summary["blocking_reasons"]["system_errors"] += 1
                
    except Exception as e:
        logger.error(f"Error in trading blocks summary: {e}")
        
    return blocking_summary