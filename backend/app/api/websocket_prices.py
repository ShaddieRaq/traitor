"""
WebSocket Price Streaming API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..models.models import Bot
from ..services.coinbase_service import coinbase_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/start-price-streaming")
async def start_price_streaming(db: Session = Depends(get_db)):
    """Start WebSocket price streaming for all active bot products."""
    try:
        # Get all running bots
        active_bots = db.query(Bot).filter(Bot.status == "RUNNING").all()
        
        if not active_bots:
            return {
                "success": False,
                "message": "No running bots found - no products to stream",
                "products": []
            }
        
        # Extract unique product IDs (using 'pair' field which contains product_id)
        product_ids = list(set([bot.pair for bot in active_bots if bot.pair]))
        
        if not product_ids:
            return {
                "success": False,
                "message": "No valid product IDs found in running bots",
                "products": []
            }
        
        # Start WebSocket streaming
        result = coinbase_service.start_price_websocket_streaming(product_ids)
        
        logger.info(f"🚀 WebSocket price streaming started for {len(product_ids)} products: {product_ids}")
        
        return {
            **result,
            "active_bots_count": len(active_bots),
            "streaming_products": product_ids
        }
        
    except Exception as e:
        logger.error(f"Error starting price streaming: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start price streaming: {str(e)}")


@router.post("/start-price-streaming-custom")
async def start_price_streaming_custom(product_ids: List[str]):
    """Start WebSocket price streaming for custom product list."""
    try:
        if not product_ids:
            raise HTTPException(status_code=400, detail="Product IDs list cannot be empty")
        
        # Start WebSocket streaming
        result = coinbase_service.start_price_websocket_streaming(product_ids)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
        
        logger.info(f"🚀 Custom WebSocket price streaming started for: {product_ids}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting custom price streaming: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start custom price streaming: {str(e)}")


@router.get("/price-streaming-status")
async def get_price_streaming_status():
    """Get WebSocket price streaming status and statistics."""
    try:
        status = coinbase_service.get_websocket_price_status()
        
        return {
            "success": True,
            "status": status,
            "timestamp": status.get("last_updates", {})
        }
        
    except Exception as e:
        logger.error(f"Error getting price streaming status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get streaming status: {str(e)}")


@router.post("/stop-price-streaming")
async def stop_price_streaming():
    """Stop WebSocket price streaming."""
    try:
        from ..services.websocket_price_cache import stop_price_websocket
        
        await stop_price_websocket()
        
        logger.info("🛑 WebSocket price streaming stopped")
        return {
            "success": True,
            "message": "WebSocket price streaming stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping price streaming: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop price streaming: {str(e)}")


@router.get("/cached-prices")
async def get_cached_prices():
    """Get all cached price data from WebSocket."""
    try:
        from ..services.websocket_price_cache import get_price_cache
        
        price_cache = get_price_cache()
        cached_prices = price_cache.get_all_cached_prices()
        
        return {
            "success": True,
            "cached_prices": cached_prices,
            "cache_count": len(cached_prices),
            "connection_status": price_cache.get_connection_status()
        }
        
    except Exception as e:
        logger.error(f"Error getting cached prices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cached prices: {str(e)}")
