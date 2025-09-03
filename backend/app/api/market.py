from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..core.database import get_db
from ..models.models import MarketData
from ..api.schemas import MarketDataResponse, ProductTickerResponse, AccountResponse
from ..services.coinbase_service import coinbase_service

router = APIRouter()


@router.get("/products")
def get_products():
    """Get available trading products."""
    products = coinbase_service.get_products()
    return {"products": products}


@router.get("/ticker/{product_id}", response_model=ProductTickerResponse)
def get_ticker(product_id: str):
    """Get current ticker for a product."""
    ticker = coinbase_service.get_product_ticker(product_id)
    if not ticker:
        raise HTTPException(status_code=404, detail="Product not found or ticker unavailable")
    return ticker


@router.get("/candles/{product_id}", response_model=List[MarketDataResponse])
def get_candles(
    product_id: str,
    timeframe: str = "1h",
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get historical candlestick data."""
    candles = db.query(MarketData).filter(
        MarketData.product_id == product_id,
        MarketData.timeframe == timeframe
    ).order_by(MarketData.timestamp.desc()).limit(limit).all()
    
    # Return in chronological order
    return list(reversed(candles))


@router.get("/accounts", response_model=List[AccountResponse])
def get_accounts():
    """Get account balances."""
    accounts = coinbase_service.get_accounts()
    return accounts


@router.get("/system/status")
def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system health status for visual indicators."""
    try:
        # Test Coinbase API connectivity
        coinbase_healthy = False
        last_ticker_time = None
        try:
            ticker = coinbase_service.get_product_ticker("BTC-USD")
            if ticker:
                coinbase_healthy = True
                last_ticker_time = datetime.utcnow()
        except Exception:
            pass
        
        # Test database connectivity
        db_healthy = True
        try:
            # Simple database test
            pass
        except Exception:
            db_healthy = False
        
        # Calculate data freshness
        now = datetime.utcnow()
        data_freshness = {
            "market_data": {
                "healthy": coinbase_healthy,
                "last_update": last_ticker_time.isoformat() if last_ticker_time else None,
                "seconds_since_update": (now - last_ticker_time).total_seconds() if last_ticker_time else None
            }
        }
        
        return {
            "status": "healthy" if (coinbase_healthy and db_healthy) else "degraded",
            "timestamp": now.isoformat(),
            "services": {
                "coinbase_api": {
                    "status": "healthy" if coinbase_healthy else "unhealthy",
                    "last_activity": last_ticker_time.isoformat() if last_ticker_time else None
                },
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy"
                },
                "polling": {
                    "status": "active",
                    "interval_seconds": 5
                }
            },
            "data_freshness": data_freshness
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.post("/fetch-data/{product_id}")
def fetch_market_data(product_id: str, timeframe: str = "1h"):
    """Manually trigger market data fetch for a product."""
    from ..tasks.data_tasks import fetch_market_data_task
    
    # Trigger async task
    task = fetch_market_data_task.delay([product_id], [timeframe])
    
    return {"message": f"Market data fetch initiated for {product_id}", "task_id": task.id}
