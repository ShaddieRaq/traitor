from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from ..core.database import get_db
from ..models.models import Signal, SignalResult
from ..api.schemas import SignalCreate, SignalUpdate, SignalResponse, SignalResultResponse

router = APIRouter()


@router.get("/", response_model=List[SignalResponse])
def get_signals(db: Session = Depends(get_db)):
    """Get all signals."""
    signals = db.query(Signal).all()
    
    # Convert parameters from JSON string to dict
    for signal in signals:
        try:
            signal.parameters = json.loads(signal.parameters) if signal.parameters else {}
        except json.JSONDecodeError:
            signal.parameters = {}
    
    return signals


@router.post("/", response_model=SignalResponse)
def create_signal(signal: SignalCreate, db: Session = Depends(get_db)):
    """Create a new signal."""
    # Check if signal name already exists
    existing = db.query(Signal).filter(Signal.name == signal.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Signal with this name already exists")
    
    db_signal = Signal(
        name=signal.name,
        description=signal.description,
        weight=signal.weight,
        parameters=json.dumps(signal.parameters)
    )
    
    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)
    
    # Convert parameters back to dict for response
    db_signal.parameters = signal.parameters
    return db_signal


@router.get("/{signal_id}", response_model=SignalResponse)
def get_signal(signal_id: int, db: Session = Depends(get_db)):
    """Get a specific signal."""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    # Convert parameters from JSON string to dict
    try:
        signal.parameters = json.loads(signal.parameters) if signal.parameters else {}
    except json.JSONDecodeError:
        signal.parameters = {}
    
    return signal


@router.put("/{signal_id}", response_model=SignalResponse)
def update_signal(signal_id: int, signal_update: SignalUpdate, db: Session = Depends(get_db)):
    """Update a signal."""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    update_data = signal_update.dict(exclude_unset=True)
    
    # Handle parameters conversion
    if "parameters" in update_data:
        update_data["parameters"] = json.dumps(update_data["parameters"])
    
    for field, value in update_data.items():
        setattr(signal, field, value)
    
    db.commit()
    db.refresh(signal)
    
    # Convert parameters back to dict for response
    try:
        signal.parameters = json.loads(signal.parameters) if signal.parameters else {}
    except json.JSONDecodeError:
        signal.parameters = {}
    
    return signal


@router.delete("/{signal_id}")
def delete_signal(signal_id: int, db: Session = Depends(get_db)):
    """Delete a signal."""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    db.delete(signal)
    db.commit()
    return {"message": "Signal deleted successfully"}


@router.get("/{signal_id}/results", response_model=List[SignalResultResponse])
def get_signal_results(
    signal_id: int, 
    product_id: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get signal calculation results."""
    query = db.query(SignalResult).filter(SignalResult.signal_id == signal_id)
    
    if product_id:
        query = query.filter(SignalResult.product_id == product_id)
    
    results = query.order_by(SignalResult.timestamp.desc()).limit(limit).all()
    
    # Convert metadata from JSON string to dict
    for result in results:
        try:
            result.metadata = json.loads(result.metadata) if result.metadata else {}
        except json.JSONDecodeError:
            result.metadata = {}
    
    return results


@router.post("/{signal_id}/toggle")
def toggle_signal(signal_id: int, db: Session = Depends(get_db)):
    """Toggle signal enabled/disabled status."""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    signal.enabled = not signal.enabled
    db.commit()
    
    return {"message": f"Signal {'enabled' if signal.enabled else 'disabled'}", "enabled": signal.enabled}
