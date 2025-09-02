from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
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


@router.post("/fetch-data/{product_id}")
def fetch_market_data(product_id: str, timeframe: str = "1h"):
    """Manually trigger market data fetch for a product."""
    from ..tasks.data_tasks import fetch_market_data_task
    
    # Trigger async task
    task = fetch_market_data_task.delay([product_id], [timeframe])
    
    return {"message": f"Market data fetch initiated for {product_id}", "task_id": task.id}
