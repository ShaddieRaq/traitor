# Position Reconciliation API Endpoints

from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.position_reconciliation_service import PositionReconciliationService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["position-reconciliation"])

@router.get("/discrepancies")
def get_position_discrepancies(db: Session = Depends(get_db)):
    """
    Get position discrepancies between bot tracking and actual Coinbase holdings.
    
    Returns list of bots with significant position differences (>$1).
    """
    try:
        reconciliation_service = PositionReconciliationService(db)
        discrepancies = reconciliation_service.get_position_discrepancies()
        
        return {
            "discrepancies": discrepancies,
            "total_discrepancies": len([d for d in discrepancies if "error" not in d]),
            "checked_at": "2025-09-04T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get position discrepancies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reconcile")
def reconcile_all_positions(db: Session = Depends(get_db)):
    """
    Reconcile all bot positions with actual Coinbase holdings.
    
    Updates bot.current_position_size to match actual Coinbase balances.
    """
    try:
        reconciliation_service = PositionReconciliationService(db)
        results = reconciliation_service.reconcile_all_bot_positions()
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return {
            "message": "Position reconciliation completed",
            "results": results,
            "reconciled_at": "2025-09-04T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to reconcile positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bot/{bot_id}/trade-calculation")
def calculate_position_from_trades(bot_id: int, db: Session = Depends(get_db)):
    """
    Calculate bot position based on recorded trade history.
    
    Alternative method to verify position accuracy.
    """
    try:
        reconciliation_service = PositionReconciliationService(db)
        calculation = reconciliation_service.calculate_position_from_trades(bot_id)
        
        if "error" in calculation:
            if calculation["error"] == "Bot not found":
                raise HTTPException(status_code=404, detail="Bot not found")
            else:
                raise HTTPException(status_code=500, detail=calculation["error"])
        
        return calculation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate position from trades for bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_reconciliation_status(db: Session = Depends(get_db)):
    """
    Get overall status of position reconciliation system.
    
    Provides summary without making changes.
    """
    try:
        reconciliation_service = PositionReconciliationService(db)
        discrepancies = reconciliation_service.get_position_discrepancies()
        
        # Calculate summary statistics
        total_bots_checked = len(discrepancies)
        bots_with_discrepancies = len([d for d in discrepancies if "error" not in d])
        total_discrepancy_usd = sum(abs(d.get("difference_usd", 0)) for d in discrepancies if "error" not in d)
        
        return {
            "status": "operational",
            "summary": {
                "total_bots_checked": total_bots_checked,
                "bots_with_discrepancies": bots_with_discrepancies,
                "total_discrepancy_usd": round(total_discrepancy_usd, 2),
                "needs_reconciliation": bots_with_discrepancies > 0
            },
            "last_checked": "2025-09-04T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get reconciliation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
