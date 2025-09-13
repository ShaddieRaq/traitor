"""
API endpoints for raw trade data.
These endpoints use clean, unprocessed data from Coinbase.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from ..core.database import get_db
from ..models.models import RawTrade
from ..services.raw_trade_service import RawTradeService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Dict[str, Any]])
def get_raw_trades(
    product_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get raw trade history from clean Coinbase data."""
    try:
        service = RawTradeService(db)
        
        if product_id:
            trades = service.get_raw_trades_by_product(product_id, limit)
        else:
            trades = service.get_all_raw_trades(limit)
        
        # Convert to dict format for API response
        trade_dicts = []
        for trade in trades:
            trade_dict = {
                "id": trade.id,
                "fill_id": trade.fill_id,
                "order_id": trade.order_id,
                "product_id": trade.product_id,
                "side": trade.side,
                "size": trade.size,
                "size_in_quote": trade.size_in_quote,
                "price": trade.price,
                "commission": trade.commission,
                "created_at": trade.created_at,
                "synced_at": trade.synced_at.isoformat() if trade.synced_at else None,
                # Calculated fields for convenience
                "usd_value": float(trade.size) if trade.size_in_quote else float(trade.size) * float(trade.price)
            }
            trade_dicts.append(trade_dict)
        
        return trade_dicts
        
    except Exception as e:
        logger.error(f"Error fetching raw trades: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching raw trades: {str(e)}")


@router.get("/stats")
def get_raw_trade_stats(db: Session = Depends(get_db)):
    """Get trading statistics from clean raw data."""
    try:
        service = RawTradeService(db)
        return service.get_trading_stats()
        
    except Exception as e:
        logger.error(f"Error calculating raw trade stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")


@router.get("/pnl-by-product")
def get_pnl_by_product(db: Session = Depends(get_db)):
    """Get P&L breakdown by trading pair using clean data."""
    try:
        service = RawTradeService(db)
        pnl_data = service.calculate_pnl_by_product()
        
        # Format for API response
        formatted_data = {
            "products": []
        }
        
        for product_id, data in pnl_data.items():
            formatted_data["products"].append({
                "product_id": product_id,
                "trade_count": data["total_trades"],
                "buy_trades": data["buy_trades"],
                "sell_trades": data["sell_trades"],
                "total_spent_usd": data["total_spent"],
                "total_received_usd": data["total_received"],
                "total_fees_usd": data["total_fees"],
                "net_pnl_usd": data["net_pnl"]
            })
        
        # Sort by net P&L descending
        formatted_data["products"].sort(key=lambda x: x["net_pnl_usd"], reverse=True)
        
        return formatted_data
        
    except Exception as e:
        logger.error(f"Error calculating P&L by product: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating P&L: {str(e)}")


@router.get("/by-order/{order_id}")
def get_raw_trades_by_order(order_id: str, db: Session = Depends(get_db)):
    """Get all raw trades for a specific order ID."""
    try:
        service = RawTradeService(db)
        trades = service.get_raw_trades_by_order_id(order_id)
        
        if not trades:
            raise HTTPException(status_code=404, detail=f"No trades found for order {order_id}")
        
        trade_dicts = []
        for trade in trades:
            trade_dict = {
                "id": trade.id,
                "fill_id": trade.fill_id,
                "order_id": trade.order_id,
                "product_id": trade.product_id,
                "side": trade.side,
                "size": trade.size,
                "size_in_quote": trade.size_in_quote,
                "price": trade.price,
                "commission": trade.commission,
                "created_at": trade.created_at,
                "usd_value": float(trade.size) if trade.size_in_quote else float(trade.size) * float(trade.price)
            }
            trade_dicts.append(trade_dict)
        
        return trade_dicts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trades for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching trades: {str(e)}")
