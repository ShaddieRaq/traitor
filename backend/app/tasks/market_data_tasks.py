"""
Market Data Tasks - Phase 7.2
Celery tasks for scheduled market data refresh to eliminate rate limiting.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from .celery_app import celery_app
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.market_data_tasks.refresh_all_market_data")
def refresh_all_market_data(product_ids: List[str] = None) -> Dict[str, Any]:
    """
    Celery task to refresh all market data in a single batch operation.
    
    This is the KEY task that eliminates rate limiting:
    - Runs every 30 seconds
    - Fetches ALL trading pairs in 1-2 API calls
    - Caches results for all bots to use
    - Reduces API calls from 25+ per minute to 2 per minute
    
    Args:
        product_ids: Optional list of specific products to refresh.
                    If None, refreshes all active trading pairs.
    
    Returns:
        Dict with refresh statistics and results.
    """
    try:
        logger.info("🔄 Starting scheduled market data refresh task")
        
        # Import here to avoid circular dependencies
        from ..services.market_data_service import get_market_data_service
        
        market_service = get_market_data_service()
        
        # If no specific products provided, get all active bot pairs
        if product_ids is None:
            db = SessionLocal()
            try:
                from ..models.models import Bot
                # Get all unique trading pairs from active bots
                active_bots = db.query(Bot).filter(Bot.status == 'RUNNING').all()
                product_ids = list(set(bot.pair for bot in active_bots if bot.pair))
                logger.info(f"📊 Refreshing market data for {len(product_ids)} active bot pairs")
            finally:
                db.close()
        
        # Perform batch refresh
        result = market_service.refresh_all_market_data(product_ids)
        
        # Log success metrics
        logger.info(f"✅ Market data refresh completed: {result['success_count']}/{result['products_processed']} products")
        
        # Add task metadata
        result.update({
            'task_name': 'refresh_all_market_data',
            'task_id': refresh_all_market_data.request.id if refresh_all_market_data.request else None,
            'completed_at': datetime.now(timezone.utc).isoformat()
        })
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Market data refresh task failed: {e}"
        logger.error(error_msg)
        
        # Report error to system health monitoring
        try:
            from ..api.system_errors import report_bot_error, ErrorType
            report_bot_error(
                error_type=ErrorType.MARKET_DATA,
                message=f"Market data refresh task failed: {str(e)}",
                details={
                    "task_name": "refresh_all_market_data",
                    "product_ids": product_ids,
                    "error_type": "celery_task_failure"
                }
            )
        except Exception as report_error:
            logger.error(f"Failed to report task error: {report_error}")
        
        return {
            'success': False,
            'error': str(e),
            'task_name': 'refresh_all_market_data',
            'completed_at': datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(name="app.tasks.market_data_tasks.refresh_products_list")
def refresh_products_list() -> Dict[str, Any]:
    """
    Celery task to refresh the list of available trading products.
    Runs less frequently since products don't change often.
    
    Returns:
        Dict with refresh results.
    """
    try:
        logger.info("🔄 Starting products list refresh task")
        
        from ..services.market_data_service import get_market_data_service
        
        market_service = get_market_data_service()
        
        # Clear products cache and refresh
        market_service.clear_cache("market_data:products")
        products = market_service.get_all_products()
        
        result = {
            'success': True,
            'products_count': len(products),
            'task_name': 'refresh_products_list',
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"✅ Products list refresh completed: {len(products)} products")
        return result
        
    except Exception as e:
        error_msg = f"❌ Products list refresh task failed: {e}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'error': str(e),
            'task_name': 'refresh_products_list',
            'completed_at': datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(name="app.tasks.market_data_tasks.cache_stats_logger")
def cache_stats_logger() -> Dict[str, Any]:
    """
    Celery task to log cache performance statistics.
    Helps monitor the effectiveness of the market data service.
    
    Returns:
        Dict with cache statistics.
    """
    try:
        from ..services.market_data_service import get_market_data_service
        
        market_service = get_market_data_service()
        stats = market_service.get_cache_stats()
        
        # Log key metrics
        logger.info(f"📊 Market Data Cache Stats: {stats['hit_rate_percent']:.1f}% hit rate, "
                   f"{stats['cache_hits']} hits, {stats['cache_misses']} misses, "
                   f"{stats['api_calls']} API calls")
        
        # Log warning if hit rate is low
        if stats['hit_rate_percent'] < 80:
            logger.warning(f"⚠️ Cache hit rate is low: {stats['hit_rate_percent']:.1f}% "
                          f"(target: >90%). Consider increasing cache TTL or checking refresh frequency.")
        
        # Add task metadata
        stats.update({
            'task_name': 'cache_stats_logger',
            'logged_at': datetime.now(timezone.utc).isoformat()
        })
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Cache stats logging failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'task_name': 'cache_stats_logger',
            'logged_at': datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(name="app.tasks.market_data_tasks.health_check")
def market_data_health_check() -> Dict[str, Any]:
    """
    Celery task to perform market data service health checks.
    Monitors Redis connectivity and Coinbase API availability.
    
    Returns:
        Dict with health check results.
    """
    try:
        from ..services.market_data_service import get_market_data_service
        
        market_service = get_market_data_service()
        health = market_service.health_check()
        
        # Log any health issues
        issues = []
        if health['redis'] != 'healthy':
            issues.append(f"Redis: {health['redis']}")
        if health['coinbase'] != 'healthy':
            issues.append(f"Coinbase: {health['coinbase']}")
        
        if issues:
            logger.warning(f"⚠️ Market Data Service Health Issues: {', '.join(issues)}")
        else:
            logger.debug("✅ Market Data Service health check passed")
        
        # Add task metadata
        health.update({
            'task_name': 'market_data_health_check',
            'checked_at': datetime.now(timezone.utc).isoformat()
        })
        
        return health
        
    except Exception as e:
        logger.error(f"❌ Market data health check failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'task_name': 'market_data_health_check',
            'checked_at': datetime.now(timezone.utc).isoformat()
        }