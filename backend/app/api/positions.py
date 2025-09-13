"""
Position Tracking API - Realistic position and P&L endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal

from app.core.database import get_db
from app.services.position_tracking_service import PositionTrackingService, PositionSummary
from app.services.coinbase_service import CoinbaseService

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify router is working"""
    return {"message": "Positions router is working!"}

def serialize_decimal(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    return obj

@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_positions(db: Session = Depends(get_db)):
    """Get all current positions with realistic P&L"""
    try:
        service = PositionTrackingService(db)
        summaries = service.get_position_summaries()
        
        result = []
        for summary in summaries:
            result.append({
                "product_id": summary.product_id,
                "current_quantity": serialize_decimal(summary.current_quantity),
                "average_cost_basis": serialize_decimal(summary.average_cost_basis),
                "realized_pnl": serialize_decimal(summary.realized_pnl),
                "unrealized_pnl": serialize_decimal(summary.unrealized_pnl),
                "total_pnl": serialize_decimal(summary.total_pnl),
                "total_fees": serialize_decimal(summary.total_fees),
                "trade_count": summary.trade_count,
                "buy_count": summary.buy_count,
                "sell_count": summary.sell_count,
                "position_status": "open" if summary.current_quantity > 0 else "closed"
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating positions: {str(e)}")

@router.get("/summary", response_model=Dict[str, Any])
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """Get overall portfolio summary"""
    try:
        service = PositionTrackingService(db)
        summaries = service.get_position_summaries()
        
        total_realized_pnl = sum(s.realized_pnl for s in summaries)
        total_unrealized_pnl = sum(s.unrealized_pnl for s in summaries)
        total_fees = sum(s.total_fees for s in summaries)
        total_trades = sum(s.trade_count for s in summaries)
        
        open_positions = [s for s in summaries if s.current_quantity > 0]
        closed_positions = [s for s in summaries if s.current_quantity == 0]
        
        return {
            "total_realized_pnl": serialize_decimal(total_realized_pnl),
            "total_unrealized_pnl": serialize_decimal(total_unrealized_pnl),
            "total_pnl": serialize_decimal(total_realized_pnl + total_unrealized_pnl),
            "total_fees": serialize_decimal(total_fees),
            "total_trades": total_trades,
            "open_positions_count": len(open_positions),
            "closed_positions_count": len(closed_positions),
            "products_traded": len(summaries)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating portfolio summary: {str(e)}")

@router.get("/{product_id}", response_model=Dict[str, Any])
async def get_position_by_product(product_id: str, db: Session = Depends(get_db)):
    """Get position details for a specific trading pair"""
    try:
        service = PositionTrackingService(db)
        position = service.get_position_by_product(product_id)
        
        if not position:
            raise HTTPException(status_code=404, detail=f"No position found for {product_id}")
        
        return {
            "product_id": position.product_id,
            "total_quantity": serialize_decimal(position.total_quantity),
            "average_cost_basis": serialize_decimal(position.average_cost_basis),
            "realized_pnl": serialize_decimal(position.realized_pnl),
            "unrealized_pnl": serialize_decimal(position.unrealized_pnl),
            "total_fees": serialize_decimal(position.total_fees),
            "lots": [
                {
                    "quantity": serialize_decimal(lot.quantity),
                    "cost_basis": serialize_decimal(lot.cost_basis),
                    "purchase_date": lot.purchase_date.isoformat(),
                    "fill_id": lot.fill_id
                }
                for lot in position.lots
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting position: {str(e)}")

@router.post("/positions/update-unrealized")
async def update_unrealized_pnl(db: Session = Depends(get_db)):
    """Update unrealized P&L with current market prices"""
    try:
        coinbase_service = CoinbaseService()
        position_service = PositionTrackingService(db)
        
        # Get current positions
        summaries = position_service.get_position_summaries()
        
        # Get current prices for products with open positions
        current_prices = {}
        for summary in summaries:
            if summary.current_quantity > 0:
                try:
                    # Get current price from Coinbase
                    ticker = coinbase_service.get_product_ticker(summary.product_id)
                    if ticker and 'price' in ticker:
                        current_prices[summary.product_id] = Decimal(str(ticker['price']))
                except Exception as e:
                    print(f"Could not get price for {summary.product_id}: {e}")
        
        # Calculate unrealized P&L with current prices
        positions = position_service.calculate_unrealized_pnl(current_prices)
        
        result = []
        for product_id, position in positions.items():
            if position.total_quantity > 0:  # Only include open positions
                result.append({
                    "product_id": product_id,
                    "current_quantity": serialize_decimal(position.total_quantity),
                    "average_cost_basis": serialize_decimal(position.average_cost_basis),
                    "current_price": serialize_decimal(current_prices.get(product_id, Decimal('0'))),
                    "unrealized_pnl": serialize_decimal(position.unrealized_pnl),
                    "unrealized_pnl_percentage": serialize_decimal(
                        (position.unrealized_pnl / (position.total_quantity * position.average_cost_basis)) * 100
                        if position.total_quantity > 0 and position.average_cost_basis > 0 else Decimal('0')
                    )
                })
        
        return {
            "updated_positions": result,
            "timestamp": "now"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating unrealized P&L: {str(e)}")
