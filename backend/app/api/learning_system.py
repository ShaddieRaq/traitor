"""
Phase 8.1: Learning System API
API endpoints to activate and monitor the profit-focused learning system
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from ..core.database import get_db
from ..models.models import Bot, SignalPredictionRecord
from ..services.adaptive_signal_weighting import get_adaptive_weighting_service
from ..tasks.prediction_evaluation import evaluate_prediction_outcomes

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/learning/evaluate-predictions")
def trigger_prediction_evaluation(
    hours_lookback: int = Query(2, ge=1, le=24, description="Hours back to look for unevaluated predictions"),
    batch_size: int = Query(100, ge=10, le=1000, description="Number of predictions to evaluate per batch"),
    db: Session = Depends(get_db)
):
    """
    Trigger evaluation of prediction outcomes to feed the learning system.
    
    This is the missing piece - we have 6.4M predictions but only 30 with outcomes.
    This endpoint evaluates whether past predictions were correct based on actual price movements.
    """
    try:
        # Check current state
        total_predictions = db.query(SignalPredictionRecord).count()
        unevaluated_predictions = db.query(SignalPredictionRecord).filter(
            SignalPredictionRecord.outcome.is_(None)
        ).count()
        
        logger.info(f"🔍 Starting prediction evaluation: {unevaluated_predictions:,} of {total_predictions:,} predictions need evaluation")
        
        # Trigger the evaluation task
        task_result = evaluate_prediction_outcomes.delay(hours_lookback, batch_size)
        
        return {
            "success": True,
            "message": f"Prediction evaluation started for {unevaluated_predictions:,} unevaluated predictions",
            "task_id": task_result.id,
            "current_stats": {
                "total_predictions": total_predictions,
                "unevaluated_predictions": unevaluated_predictions,
                "evaluation_rate": f"{((total_predictions - unevaluated_predictions) / total_predictions * 100):.1f}%" if total_predictions > 0 else "0%"
            },
            "parameters": {
                "hours_lookback": hours_lookback,
                "batch_size": batch_size
            }
        }
        
    except Exception as e:
        logger.error(f"Error triggering prediction evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger evaluation: {str(e)}")


@router.get("/learning/status")
def get_learning_system_status(db: Session = Depends(get_db)):
    """
    Get comprehensive status of the learning system including prediction data and bot eligibility.
    """
    try:
        # Prediction data stats
        total_predictions = db.query(SignalPredictionRecord).count()
        evaluated_predictions = db.query(SignalPredictionRecord).filter(
            SignalPredictionRecord.outcome.isnot(None)
        ).count()
        
        # Bot eligibility for learning
        adaptive_service = get_adaptive_weighting_service()
        eligible_bots = []
        ineligible_bots = []
        
        all_bots = db.query(Bot).filter(Bot.is_active == True).all()
        
        for bot in all_bots:
            should_update, reason = adaptive_service.should_update_weights(bot, db)
            if should_update:
                eligible_bots.append({
                    "id": bot.id,
                    "pair": bot.pair,
                    "reason": reason
                })
            else:
                ineligible_bots.append({
                    "id": bot.id,
                    "pair": bot.pair,
                    "reason": reason
                })
        
        return {
            "prediction_data": {
                "total_predictions": total_predictions,
                "evaluated_predictions": evaluated_predictions,
                "unevaluated_predictions": total_predictions - evaluated_predictions,
                "evaluation_rate": f"{(evaluated_predictions / total_predictions * 100):.1f}%" if total_predictions > 0 else "0%"
            },
            "bot_eligibility": {
                "eligible_count": len(eligible_bots),
                "ineligible_count": len(ineligible_bots),
                "eligible_bots": eligible_bots[:5],  # Show first 5
                "ineligible_bots": ineligible_bots[:5],  # Show first 5
                "total_active_bots": len(all_bots)
            },
            "learning_system_ready": len(eligible_bots) > 0 and evaluated_predictions > 0,
            "next_steps": _get_next_steps(evaluated_predictions, len(eligible_bots))
        }
        
    except Exception as e:
        logger.error(f"Error getting learning system status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/learning/activate-for-bot/{bot_id}")
def activate_learning_for_bot(
    bot_id: int,
    force: bool = Query(False, description="Force activation even if safety checks fail"),
    db: Session = Depends(get_db)
):
    """
    Activate learning system for a specific bot (for testing/manual activation).
    """
    try:
        # Get bot
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Check if bot is eligible
        adaptive_service = get_adaptive_weighting_service()
        should_update, reason = adaptive_service.should_update_weights(bot, db)
        
        if not should_update and not force:
            raise HTTPException(
                status_code=400, 
                detail=f"Bot not eligible for learning update: {reason}. Use force=true to override."
            )
        
        # Trigger learning update
        result = adaptive_service.process_bot_weight_update(bot_id)
        
        if result.get('success'):
            logger.info(f"✅ Learning system activated for bot {bot_id} ({bot.pair})")
            return {
                "success": True,
                "message": f"Learning system activated for {bot.pair}",
                "bot_id": bot_id,
                "update_result": result
            }
        else:
            return {
                "success": False,
                "message": result.get('message', 'Learning update failed'),
                "bot_id": bot_id,
                "update_result": result
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating learning for bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate learning: {str(e)}")


@router.post("/learning/update-all-eligible")
def update_all_eligible_bots(
    max_bots: int = Query(10, ge=1, le=50, description="Maximum number of bots to update"),
    db: Session = Depends(get_db)
):
    """
    Trigger learning system updates for all eligible bots.
    """
    try:
        adaptive_service = get_adaptive_weighting_service()
        active_bots = db.query(Bot).filter(Bot.is_active == True).all()
        
        eligible_bots = []
        for bot in active_bots:
            should_update, reason = adaptive_service.should_update_weights(bot, db)
            if should_update:
                eligible_bots.append(bot)
                if len(eligible_bots) >= max_bots:
                    break
        
        if not eligible_bots:
            return {
                "success": True,
                "message": "No bots currently eligible for learning updates",
                "eligible_count": 0,
                "updated_count": 0
            }
        
        # Update eligible bots
        update_results = []
        successful_updates = 0
        
        for bot in eligible_bots:
            try:
                result = adaptive_service.process_bot_weight_update(bot.id)
                update_results.append({
                    "bot_id": bot.id,
                    "pair": bot.pair,
                    "success": result.get('success', False),
                    "message": result.get('message', 'Unknown result')
                })
                
                if result.get('success'):
                    successful_updates += 1
                    
            except Exception as e:
                update_results.append({
                    "bot_id": bot.id,
                    "pair": bot.pair,
                    "success": False,
                    "message": f"Error: {str(e)}"
                })
        
        logger.info(f"🎯 Learning system batch update: {successful_updates}/{len(eligible_bots)} successful")
        
        return {
            "success": True,
            "message": f"Updated {successful_updates} of {len(eligible_bots)} eligible bots",
            "eligible_count": len(eligible_bots),
            "updated_count": successful_updates,
            "results": update_results
        }
        
    except Exception as e:
        logger.error(f"Error updating all eligible bots: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update bots: {str(e)}")


def _get_next_steps(evaluated_predictions: int, eligible_bots: int) -> list:
    """Generate next steps recommendations based on current system state."""
    steps = []
    
    if evaluated_predictions < 100:
        steps.append("1. Run prediction evaluation to create outcome data for learning")
    
    if eligible_bots == 0:
        steps.append("2. Wait for more prediction data to accumulate (need 1+ evaluated predictions per signal)")
    else:
        steps.append(f"2. Activate learning for {eligible_bots} eligible bots")
    
    if evaluated_predictions > 0 and eligible_bots > 0:
        steps.append("3. Monitor learning system weight updates and profit improvements")
    
    return steps