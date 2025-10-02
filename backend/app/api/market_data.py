"""
Market Data API - Phase 7.6
REST API endpoints for the centralized Market Data Service.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

from ..core.database import get_db
from ..services.market_data_service import get_market_data_service, TickerData, ProductInfo

logger = logging.getLogger(__name__)
router = APIRouter(tags=["market-data"])


@router.post("/refresh")
async def refresh_market_data(
    product_ids: Optional[List[str]] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually trigger market data refresh for all or specific trading pairs.
    
    Args:
        product_ids: Optional list of specific products to refresh.
                    If None, refreshes all active bot pairs.
    
    Returns:
        Refresh results and statistics.
    """
    try:
        logger.info(f"🔄 Manual market data refresh requested for {len(product_ids) if product_ids else 'all'} products")
        
        market_service = get_market_data_service()
        
        # If no specific products provided, get all active bot pairs
        if product_ids is None:
            from ..models.models import Bot
            active_bots = db.query(Bot).filter(Bot.status == 'RUNNING').all()
            product_ids = list(set(bot.pair for bot in active_bots if bot.pair))
            logger.info(f"📊 Refreshing market data for {len(product_ids)} active bot pairs")
        
        result = market_service.refresh_all_market_data(product_ids)
        
        return {
            "success": True,
            "message": f"Market data refreshed for {result['products_processed']} products",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Manual market data refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"Market data refresh failed: {str(e)}")


@router.get("/ticker/{product_id}")
async def get_ticker(product_id: str) -> Dict[str, Any]:
    """
    Get current ticker data for a specific trading pair from cache.
    
    Args:
        product_id: Trading pair (e.g., "BTC-USD")
    
    Returns:
        Ticker data with price, volume, and metadata.
    """
    try:
        market_service = get_market_data_service()
        ticker = market_service.get_ticker(product_id)
        
        if not ticker:
            raise HTTPException(status_code=404, detail=f"Ticker data not found for {product_id}")
        
        return {
            "success": True,
            "data": ticker.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get ticker for {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ticker data: {str(e)}")


@router.get("/tickers")
async def get_all_tickers(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get ticker data for multiple trading pairs.
    
    Args:
        limit: Maximum number of tickers to return
    
    Returns:
        List of ticker data for active trading pairs.
    """
    try:
        market_service = get_market_data_service()
        
        # Get active bot pairs
        from ..models.models import Bot
        active_bots = db.query(Bot).filter(Bot.status == 'RUNNING').limit(limit).all()
        product_ids = [bot.pair for bot in active_bots if bot.pair]
        
        tickers = []
        for product_id in product_ids:
            ticker = market_service.get_ticker(product_id)
            if ticker:
                tickers.append(ticker.to_dict())
        
        return {
            "success": True,
            "count": len(tickers),
            "data": tickers
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get tickers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get ticker data: {str(e)}")


@router.get("/products")
async def get_products() -> Dict[str, Any]:
    """
    Get all available trading products from cache.
    
    Returns:
        List of all available trading products.
    """
    try:
        market_service = get_market_data_service()
        products = market_service.get_all_products()
        
        products_dict = [product.to_dict() for product in products]
        
        return {
            "success": True,
            "count": len(products_dict),
            "data": products_dict
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get products: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get products: {str(e)}")


@router.get("/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get market data service cache performance statistics.
    
    Returns:
        Cache performance metrics and statistics.
    """
    try:
        market_service = get_market_data_service()
        stats = market_service.get_cache_stats()
        
        return {
            "success": True,
            "message": f"Cache hit rate: {stats['hit_rate_percent']:.1f}%",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(pattern: str = "market_data:*") -> Dict[str, Any]:
    """
    Clear market data cache entries.
    
    Args:
        pattern: Redis key pattern to clear (default: all market data)
    
    Returns:
        Cache clearing results.
    """
    try:
        logger.info(f"🧹 Manual cache clear requested for pattern: {pattern}")
        
        market_service = get_market_data_service()
        result = market_service.clear_cache(pattern)
        
        if result['success']:
            return {
                "success": True,
                "message": f"Cleared {result['deleted_count']} cache entries",
                "data": result
            }
        else:
            raise HTTPException(status_code=500, detail=result['error'])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Check market data service health.
    
    Returns:
        Health status of service components.
    """
    try:
        market_service = get_market_data_service()
        health = market_service.health_check()
        
        # Determine overall health
        overall_healthy = (
            health['service'] == 'healthy' and
            health['redis'] == 'healthy' and
            health['coinbase'] == 'healthy'
        )
        
        return {
            "success": True,
            "healthy": overall_healthy,
            "message": "All systems healthy" if overall_healthy else "Some systems have issues",
            "data": health
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/historical/{product_id}")
async def get_historical_data(
    product_id: str,
    granularity: int = 3600,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get historical candlestick data for a trading pair.
    
    Args:
        product_id: Trading pair (e.g., "BTC-USD")
        granularity: Candlestick granularity in seconds (default: 3600 = 1 hour)
        limit: Number of candles to fetch (default: 100)
    
    Returns:
        Historical candlestick data.
    """
    try:
        market_service = get_market_data_service()
        df = market_service.get_historical_data(product_id, granularity, limit)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for {product_id}")
        
        # Convert DataFrame to list of dictionaries
        data = []
        for timestamp, row in df.iterrows():
            data.append({
                "timestamp": timestamp.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row['volume'])
            })
        
        return {
            "success": True,
            "product_id": product_id,
            "granularity": granularity,
            "count": len(data),
            "data": data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get historical data for {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get historical data: {str(e)}")


@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get market data service performance metrics.
    
    Returns:
        Performance metrics including API call reduction statistics.
    """
    try:
        market_service = get_market_data_service()
        stats = market_service.get_cache_stats()
        
        # Calculate API call reduction metrics
        total_requests = stats['cache_hits'] + stats['cache_misses']
        api_call_reduction = (stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        performance_metrics = {
            "api_call_reduction_percent": round(api_call_reduction, 2),
            "cache_efficiency": "Excellent" if api_call_reduction > 90 else "Good" if api_call_reduction > 80 else "Needs Improvement",
            "total_requests_served": total_requests,
            "api_calls_saved": stats['cache_hits'],
            "actual_api_calls": stats['api_calls'],
            "uptime_info": {
                "last_refresh": stats['last_refresh'],
                "last_batch_size": stats['last_batch_size']
            },
            "cache_configuration": {
                "ttl_seconds": stats['cache_ttl_seconds'],
                "hit_rate_target": "90%+",
                "current_hit_rate": f"{stats['hit_rate_percent']:.1f}%"
            }
        }
        
        return {
            "success": True,
            "message": f"API calls reduced by {api_call_reduction:.1f}% through caching",
            "data": performance_metrics
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")