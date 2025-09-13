"""
DEPRECATED: Coinbase sync endpoints that used the Trade model.
The Trade model has been eliminated in favor of raw_trades.
Use /api/v1/raw-trades/ endpoints instead.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()


@router.post("/sync-coinbase-trades")
def sync_coinbase_trades(days_back: int = 1) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Use raw_trades sync instead.
    The Trade model has been eliminated.
    """
    raise HTTPException(
        status_code=410,
        detail={
            "error": "Endpoint deprecated - Trade model eliminated",
            "message": "Use /api/v1/raw-trades/ endpoints instead",
            "replacement": "/api/v1/raw-trades/",
            "reason": "Trade model eliminated in favor of clean raw_trades system"
        }
    )


@router.get("/sync-status")
def get_sync_status() -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Use raw_trades status instead.
    """
    raise HTTPException(
        status_code=410,
        detail={
            "error": "Endpoint deprecated - Trade model eliminated",
            "message": "Use /api/v1/raw-trades/stats instead",
            "replacement": "/api/v1/raw-trades/stats"
        }
    )


@router.get("/production-trades-summary")
def get_production_trades_summary() -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Use raw_trades summary instead.
    """
    raise HTTPException(
        status_code=410,
        detail={
            "error": "Endpoint deprecated - Trade model eliminated", 
            "message": "Use /api/v1/raw-trades/stats instead",
            "replacement": "/api/v1/raw-trades/stats"
        }
    )
