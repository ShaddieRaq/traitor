"""
Market Data Cache API endpoints for monitoring and management.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import logging
from ..services.coinbase_service import coinbase_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats")
def get_cache_stats() -> Dict[str, Any]:
    """
    Get market data cache performance statistics.
    
    Returns cache hit rates, API call savings, and other performance metrics.
    """
    try:
        stats = coinbase_service.get_cache_stats()
        return {
            "status": "success",
            "cache_stats": stats,
            "performance_analysis": {
                "api_calls_saved": stats["api_calls_saved"],
                "efficiency_gain": f"{stats['hit_rate_percent']}% requests served from cache",
                "memory_usage": f"{stats['cache_size']}/{stats['max_cache_size']} entries",
                "cache_health": "excellent" if stats["hit_rate_percent"] > 80 else 
                               "good" if stats["hit_rate_percent"] > 60 else 
                               "poor" if stats["hit_rate_percent"] > 40 else "critical"
            }
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.get("/info")
def get_cache_info() -> Dict[str, Any]:
    """
    Get detailed cache information for debugging.
    
    Returns information about each cached entry including age and expiration.
    """
    try:
        cache_info = coinbase_service.get_cache_info()
        return {
            "status": "success",
            "cache_entries": cache_info,
            "summary": {
                "total_entries": len(cache_info),
                "expired_entries": sum(1 for entry in cache_info.values() if entry["is_expired"]),
                "product_pairs": list(set(key.split(":")[0] for key in cache_info.keys()))
            }
        }
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache info: {str(e)}")


@router.post("/invalidate")
def invalidate_cache(product_id: Optional[str] = None) -> Dict[str, str]:
    """
    Invalidate market data cache entries.
    
    Args:
        product_id: If provided, only invalidate cache for this product.
                   If not provided, invalidate all cache entries.
    """
    try:
        invalidated_count = coinbase_service.invalidate_cache(product_id)
        
        return {
            "status": "success",
            "message": f"Invalidated {invalidated_count} cache entries" + 
                      (f" for {product_id}" if product_id else " (all products)"),
            "invalidated_count": invalidated_count,
            "product_id": product_id
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


@router.get("/rate-limiting-status")
def get_rate_limiting_status() -> Dict[str, Any]:
    """
    Get current rate limiting status and API usage analysis.
    """
    try:
        cache_stats = coinbase_service.get_cache_stats()
        
        # Calculate estimated API usage
        total_requests = cache_stats["hits"] + cache_stats["misses"]
        api_calls_made = cache_stats["misses"]
        api_calls_saved = cache_stats["api_calls_saved"]
        
        # Estimate API calls per minute (rough calculation)
        estimated_calls_per_minute = api_calls_made / max(1, total_requests / 60) if total_requests > 0 else 0
        
        return {
            "status": "success",
            "rate_limiting_analysis": {
                "estimated_api_calls_per_minute": round(estimated_calls_per_minute, 2),
                "api_calls_saved": api_calls_saved,
                "cache_hit_rate": f"{cache_stats['hit_rate_percent']}%",
                "risk_level": "low" if estimated_calls_per_minute < 20 else
                             "medium" if estimated_calls_per_minute < 40 else
                             "high" if estimated_calls_per_minute < 60 else "critical",
                "recommendation": "Cache working effectively" if cache_stats["hit_rate_percent"] > 70 else
                                "Consider increasing cache TTL or investigating cache misses"
            },
            "cache_performance": cache_stats
        }
    except Exception as e:
        logger.error(f"Error getting rate limiting status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rate limiting status: {str(e)}")
