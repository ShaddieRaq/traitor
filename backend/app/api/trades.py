from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..models.models import Trade
from ..api.schemas import TradeResponse

router = APIRouter()


@router.get("/", response_model=List[TradeResponse])
def get_trades(
    product_id: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get trade history."""
    query = db.query(Trade)
    
    if product_id:
        query = query.filter(Trade.product_id == product_id)
    
    trades = query.order_by(Trade.created_at.desc()).limit(limit).all()
    return trades


@router.get("/stats")
def get_trade_stats(db: Session = Depends(get_db)):
    """Get trading statistics."""
    # Basic trade statistics
    total_trades = db.query(Trade).count()
    filled_trades = db.query(Trade).filter(Trade.status == "filled").count()
    
    # TODO: Add more sophisticated statistics
    # - P&L calculation
    # - Win/loss ratio
    # - Average trade size
    # - etc.
    
    return {
        "total_trades": total_trades,
        "filled_trades": filled_trades,
        "success_rate": filled_trades / total_trades * 100 if total_trades > 0 else 0
    }


@router.post("/trigger-evaluation")
def trigger_signal_evaluation():
    """Manually trigger bot signal evaluation."""
    from ..tasks.trading_tasks import evaluate_bot_signals
    
    # Trigger async bot signal evaluation
    task = evaluate_bot_signals.delay()
    
    return {"message": "Bot signal evaluation initiated", "task_id": task.id}
