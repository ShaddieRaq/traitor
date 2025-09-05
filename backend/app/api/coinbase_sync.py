"""
Coinbase Sync API endpoints for syncing real trades.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from datetime import datetime
from ..core.database import get_db
from ..services.coinbase_sync_service import coinbase_sync_service
from ..models.models import Trade

router = APIRouter()


@router.post("/sync-coinbase-trades")
def sync_coinbase_trades(days_back: int = 1, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Sync actual Coinbase trades into our database as production trades.
    
    Args:
        days_back: Number of days to look back for trades (default: 1)
    """
    try:
        # Use global service instance with current DB session
        sync_service = coinbase_sync_service
        sync_service.db = db  # Use current session
        
        result = sync_service.sync_coinbase_trades(days_back)
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Synced {result['new_trades_synced']} new trades from Coinbase",
                "coinbase_fills_found": result.get("coinbase_fills_found", 0),
                "new_trades_synced": result.get("new_trades_synced", 0),
                "existing_trades_skipped": result.get("existing_trades_skipped", 0),
                "details": result
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Sync failed"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/sync-status")
def get_sync_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get current sync status and trade counts."""
    try:
        sync_service = coinbase_sync_service
        sync_service.db = db
        
        status = sync_service.get_sync_status()
        return {
            "status": "success",
            "sync_status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@router.get("/production-trades-summary")
def get_production_trades_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get summary of all production trades."""
    try:
        # Count production trades
        total_production = db.query(Trade).filter(Trade.trading_mode == "production").count()
        
        # Count production trades today
        today = datetime.utcnow().date()
        production_today = db.query(Trade).filter(
            Trade.trading_mode == "production",
            func.date(Trade.created_at) == today
        ).count()
        
        # Get recent production trades
        recent_trades = db.query(Trade).filter(
            Trade.trading_mode == "production"
        ).order_by(Trade.created_at.desc()).limit(5).all()
        
        recent_trade_data = []
        for trade in recent_trades:
            recent_trade_data.append({
                "id": trade.id,
                "product_id": trade.product_id,
                "side": trade.side,
                "size_usd": trade.size_usd,
                "price": trade.price,
                "created_at": trade.created_at.isoformat(),
                "bot_id": trade.bot_id,
                "order_id": trade.order_id,
                "source": "bot" if trade.bot_id else "external"
            })
        
        return {
            "status": "success",
            "total_production_trades": total_production,
            "production_trades_today": production_today,
            "recent_trades": recent_trades
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get production trades summary: {str(e)}")
