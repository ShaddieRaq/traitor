"""
Cache monitoring and statistics API endpoints.
Provides real-time insights into cache performance and API call reduction.
"""

from fastapi import APIRouter
from typing import Dict, Any
import time
import logging
from ..services.shared_cache_service import shared_cache_manager, data_distribution_service
from ..services.api_coordinator import api_coordinator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/cache/stats")
async def get_cache_statistics() -> Dict[str, Any]:
    """Get comprehensive cache performance statistics."""
    try:
        # Get cache manager stats
        cache_stats = await shared_cache_manager.get_cache_stats()
        
        # Get API coordinator stats  
        coordinator_stats = api_coordinator.get_stats()
        
        # Extract actual values from cache stats
        total_cache_keys = cache_stats.get('total_keys', 0)
        keys_by_type = cache_stats.get('keys_by_type', {})
        redis_memory = cache_stats.get('redis_memory_used', 'unknown')
        
        # Calculate basic metrics with available data
        total_requests = coordinator_stats.get('total_requests', 0)
        successful_requests = coordinator_stats.get('successful_requests', 0)
        
        # Calculate API call reduction (approximation based on coordinator stats)
        api_call_reduction = (successful_requests / max(1, total_requests)) * 100 if total_requests > 0 else 0
        
        return {
            "cache_performance": {
                "total_cache_keys": total_cache_keys,
                "cache_keys_by_type": keys_by_type,
                "redis_memory_usage": redis_memory,
                "cache_status": cache_stats.get('status', 'unknown'),
                "api_call_efficiency_percent": round(api_call_reduction, 2)
            },
            "api_coordination": {
                "total_requests": total_requests,
                "successful_requests": coordinator_stats.get('successful_requests', 0),
                "failed_requests": coordinator_stats.get('failed_requests', 0),
                "rate_limit_errors": coordinator_stats.get('rate_limit_errors', 0),
                "success_rate_percent": round(coordinator_stats.get('success_rate', 0), 2),
                "calls_per_minute": coordinator_stats.get('calls_per_minute', 0),
                "max_calls_per_minute": coordinator_stats.get('max_calls_per_minute', 10),
                "queue_size": coordinator_stats.get('queue_size', 0),
                "circuit_breaker_open": coordinator_stats.get('circuit_breaker_open', False)
            },
            "cache_configurations": cache_stats.get('cache_configs', {}),
            "recent_performance": {
                "last_request_time": coordinator_stats.get('last_request_time'),
                "time_since_last_call": coordinator_stats.get('time_since_last_call', 0),
                "redis_connected_clients": cache_stats.get('redis_connected_clients', 0)
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        return {
            "error": f"Failed to get cache statistics: {str(e)}",
            "timestamp": time.time()
        }


@router.get("/cache/health")
async def get_cache_health() -> Dict[str, Any]:
    """Get cache system health status."""
    try:
        # Test cache connectivity
        cache_healthy = shared_cache_manager.redis_client is not None
        
        if cache_healthy:
            try:
                # Test basic operations using valid data type
                from ..services.shared_cache_service import DataType
                
                await shared_cache_manager.set(
                    data_type=DataType.TICKER, 
                    data={"test": "health_check", "price": 999.99}, 
                    product_id="HEALTH-CHECK"
                )
                result = await shared_cache_manager.get(
                    data_type=DataType.TICKER,
                    product_id="HEALTH-CHECK"
                )
                cache_operations_healthy = result is not None and result.get("test") == "health_check"
            except Exception as e:
                logger.warning(f"Cache health check failed: {e}")
                cache_operations_healthy = False
        else:
            cache_operations_healthy = False
            
        # Get coordinator health
        coordinator_healthy = api_coordinator.is_running
        circuit_breaker_open = api_coordinator.stats.circuit_breaker_open
        
        overall_health = cache_healthy and cache_operations_healthy and coordinator_healthy and not circuit_breaker_open
        
        return {
            "status": "healthy" if overall_health else "degraded",
            "components": {
                "redis_connection": "healthy" if cache_healthy else "failed",
                "cache_operations": "healthy" if cache_operations_healthy else "failed", 
                "api_coordinator": "healthy" if coordinator_healthy else "stopped",
                "circuit_breaker": "closed" if not circuit_breaker_open else "open"
            },
            "overall_healthy": overall_health,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error checking cache health: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }


@router.post("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """Clear all cache entries (admin operation)."""
    try:
        cleared_count = await shared_cache_manager.invalidate()
        
        return {
            "status": "success",
            "message": f"Cleared {cleared_count} cache entries",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {
            "status": "error", 
            "message": f"Failed to clear cache: {str(e)}",
            "timestamp": time.time()
        }