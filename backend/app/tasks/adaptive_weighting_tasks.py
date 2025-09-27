"""
Phase 3B: Adaptive Signal Weighting Tasks
Celery tasks for automated signal weight updates
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from ..models.models import Bot
from ..core.database import SessionLocal
from ..services.adaptive_signal_weighting import get_adaptive_weighting_service
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="adaptive_weighting.update_bot_weights")
def update_bot_weights_task(bot_id: int) -> Dict[str, Any]:
    """
    Celery task to update signal weights for a specific bot.
    
    Args:
        bot_id: ID of bot to update
        
    Returns:
        Dict with update results
    """
    logger.info(f"🔄 Starting adaptive weight update for bot {bot_id}")
    
    try:
        weighting_service = get_adaptive_weighting_service()
        result = weighting_service.process_bot_weight_update(bot_id)
        
        if result['success']:
            logger.info(f"✅ Adaptive weight update completed for bot {bot_id}: {result['message']}")
        else:
            logger.info(f"ℹ️ Adaptive weight update skipped for bot {bot_id}: {result['message']}")
            
        return result
        
    except Exception as e:
        error_msg = f"Failed to update weights for bot {bot_id}: {e}"
        logger.error(error_msg)
        return {
            'bot_id': bot_id,
            'success': False,
            'message': error_msg,
            'timestamp': datetime.utcnow().isoformat()
        }


@celery_app.task(name="adaptive_weighting.update_all_eligible_bots")
def update_all_eligible_bots_weights_task() -> Dict[str, Any]:
    """
    Celery task to check and update weights for all eligible bots.
    
    This task runs periodically to identify bots that need weight updates
    and processes them automatically.
    
    Returns:
        Dict with summary of updates processed
    """
    logger.info("🔄 Starting adaptive weight update scan for all bots")
    
    results = {
        'total_bots_checked': 0,
        'bots_updated': 0,
        'bots_skipped': 0,
        'bots_failed': 0,
        'update_details': [],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        weighting_service = get_adaptive_weighting_service()
        
        db = SessionLocal()
        try:
            # Get all active bots
            active_bots = db.query(Bot).filter(Bot.status == 'RUNNING').all()
            results['total_bots_checked'] = len(active_bots)
            
            for bot in active_bots:
                try:
                    logger.info(f"🔍 Checking bot {bot.id} ({bot.pair}) for weight updates")
                    
                    # Check if this bot should be updated
                    should_update, reason = weighting_service.should_update_weights(bot, db)
                    
                    if should_update:
                        # Process the update
                        update_result = weighting_service.process_bot_weight_update(bot.id)
                        results['update_details'].append(update_result)
                        
                        if update_result['success']:
                            results['bots_updated'] += 1
                            logger.info(f"✅ Updated weights for bot {bot.id} ({bot.pair})")
                        else:
                            results['bots_skipped'] += 1
                            logger.info(f"⚠️ Weight update failed for bot {bot.id}: {update_result['message']}")
                    else:
                        results['bots_skipped'] += 1
                        logger.debug(f"⏭️ Skipping bot {bot.id} ({bot.pair}): {reason}")
                        
                except Exception as bot_error:
                    results['bots_failed'] += 1
                    error_msg = f"Error processing bot {bot.id}: {bot_error}"
                    logger.error(error_msg)
            results['update_details'].append(update_result)
        
        except Exception as bot_error:
            results['bots_failed'] += 1
            error_msg = f"Error processing bot {bot.id}: {bot_error}"
            logger.error(error_msg)
            results['update_details'].append({
                'bot_id': bot.id,
                'success': False,
                'message': error_msg
            })
        
        finally:
            db.close()        # Log summary
        logger.info(f"📊 Adaptive weight update scan complete: "
                   f"{results['total_bots_checked']} checked, "
                   f"{results['bots_updated']} updated, "
                   f"{results['bots_skipped']} skipped, "
                   f"{results['bots_failed']} failed")
        
        return results
        
    except Exception as e:
        error_msg = f"Failed to complete adaptive weight update scan: {e}"
        logger.error(error_msg)
        results.update({
            'success': False,
            'message': error_msg
        })
        return results


@celery_app.task(name="adaptive_weighting.calculate_performance_metrics")
def calculate_performance_metrics_task(pair: str = None, regime: str = None) -> Dict[str, Any]:
    """
    Celery task to calculate and populate performance metrics table.
    
    This addresses the gap where signal_performance_metrics table is empty.
    
    Args:
        pair: Optional pair filter
        regime: Optional regime filter
        
    Returns:
        Dict with calculation results
    """
    logger.info(f"📊 Starting performance metrics calculation (pair={pair}, regime={regime})")
    
    try:
        from ..services.signal_performance_tracker import get_signal_performance_tracker
        
        db = SessionLocal()
        try:
            performance_tracker = get_signal_performance_tracker(db)
            
            # Trigger performance metrics calculation
            # This will populate the empty signal_performance_metrics table
            calculated_count = performance_tracker.calculate_and_store_performance_metrics(
                pair_filter=pair,
                regime_filter=regime
            )
            
            result = {
                'success': True,
                'metrics_calculated': calculated_count,
                'pair_filter': pair,
                'regime_filter': regime,
                'timestamp': datetime.utcnow().isoformat(),
                'message': f"Successfully calculated {calculated_count} performance metrics"
            }
            
            logger.info(f"✅ Performance metrics calculation complete: {calculated_count} metrics calculated")
            return result
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Failed to calculate performance metrics: {e}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'timestamp': datetime.utcnow().isoformat()
        }


# Schedule periodic tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks for adaptive signal weighting."""
    
    # Update weights for all eligible bots every 6 hours
    sender.add_periodic_task(
        6 * 60 * 60,  # 6 hours in seconds
        update_all_eligible_bots_weights_task.s(),
        name='adaptive-weight-updates-all-bots'
    )
    
    # Calculate performance metrics every 2 hours
    sender.add_periodic_task(
        2 * 60 * 60,  # 2 hours in seconds
        calculate_performance_metrics_task.s(),
        name='calculate-performance-metrics'
    )