"""
Cache monitoring and statistics API endpoints.
Provides real-time insights into cache performance and API call reduction.
"""

from fastapi import APIRouter
from typing import Dict, Any
import time
import logging
from ..services.market_data_service import get_market_data_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/cache/stats")
async def get_cache_statistics() -> Dict[str, Any]:
    """Get comprehensive cache performance statistics."""
    try:
        # Get market data service stats
        market_data_service = get_market_data_service()
        cache_stats = market_data_service.get_cache_stats()
        
        return {
            "cache_performance": {
                "cache_hit_rate": cache_stats.get('hit_rate', 0),
                "total_requests": cache_stats.get('total_requests', 0),
                "cache_hits": cache_stats.get('hits', 0),
                "cache_misses": cache_stats.get('misses', 0),
                "cache_size": cache_stats.get('cache_size', 0),
                "status": "active"
            },
            "service_info": {
                "service": "MarketDataService",
                "version": "Phase 7",
                "redis_connected": market_data_service.redis is not None,
                "last_updated": time.time()
            }
        }
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        return {
            "cache_performance": {
                "cache_hit_rate": 0,
                "status": "error",
                "error": str(e)
            },
            "service_info": {
                "service": "MarketDataService", 
                "status": "error"
            }
        }


@router.get("/cache/health")
async def get_cache_health() -> Dict[str, Any]:
    """Get cache system health status."""
    try:
        market_data_service = get_market_data_service()
        
        # Test cache functionality
        test_key = f"health_check_{int(time.time())}"
        test_value = {"test": "data", "timestamp": time.time()}
        
        # Test set/get operations
        market_data_service.set_cache(test_key, test_value, ttl=60)
        retrieved = market_data_service.get_cache(test_key)
        
        cache_healthy = retrieved is not None and retrieved.get("test") == "data"
        
        return {
            "status": "healthy" if cache_healthy else "unhealthy",
            "redis_connected": market_data_service.redis is not None,
            "cache_operations": "working" if cache_healthy else "failed",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@router.post("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """Clear cache (admin operation)."""
    try:
        market_data_service = get_market_data_service()
        
        # Clear market data cache
        cleared = market_data_service.clear_cache()
        
        return {
            "status": "success",
            "cleared_items": cleared,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }