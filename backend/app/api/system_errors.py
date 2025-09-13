"""
System Error Tracking API - Make code errors visible to users
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.core.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

class ErrorType(str, Enum):
    SIGNAL_CALCULATION = "signal_calculation"
    MARKET_DATA = "market_data" 
    CONFIGURATION = "configuration"
    TRADING_LOGIC = "trading_logic"
    SYSTEM = "system"

class ErrorStore:
    """In-memory error store (could be moved to DB later)"""
    _errors: List[Dict[str, Any]] = []
    _max_errors = 100

    @classmethod
    def add_error(
        cls, 
        error_type: ErrorType, 
        message: str, 
        bot_id: Optional[int] = None,
        bot_name: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """Add a new error to the store"""
        error_id = f"{datetime.now().isoformat()}_{len(cls._errors)}"
        
        error = {
            "id": error_id,
            "bot_id": bot_id,
            "bot_name": bot_name,
            "error_type": error_type.value,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "resolved": False
        }
        
        cls._errors.append(error)
        
        # Keep only recent errors
        if len(cls._errors) > cls._max_errors:
            cls._errors = cls._errors[-cls._max_errors:]
        
        # Log to backend as well
        logger.error(f"Bot Error [{error_type.value}] {bot_name or 'Unknown'}: {message}")
        
        return error_id

    @classmethod
    def get_errors(cls, include_resolved: bool = True, last_hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent errors"""
        cutoff = datetime.now() - timedelta(hours=last_hours)
        
        filtered_errors = []
        for error in cls._errors:
            error_time = datetime.fromisoformat(error["timestamp"])
            if error_time >= cutoff:
                if include_resolved or not error["resolved"]:
                    filtered_errors.append(error)
        
        return sorted(filtered_errors, key=lambda x: x["timestamp"], reverse=True)

    @classmethod
    def resolve_error(cls, error_id: str) -> bool:
        """Mark an error as resolved"""
        for error in cls._errors:
            if error["id"] == error_id:
                error["resolved"] = True
                return True
        return False

    @classmethod
    def get_active_count(cls) -> int:
        """Get count of unresolved errors"""
        return len([e for e in cls._errors if not e["resolved"]])

@router.get("/errors", response_model=List[Dict[str, Any]])
async def get_system_errors(
    include_resolved: bool = True,
    last_hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get recent system errors"""
    try:
        errors = ErrorStore.get_errors(include_resolved, last_hours)
        return errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching system errors: {str(e)}")

@router.post("/errors/{error_id}/resolve")
async def resolve_error(error_id: str, db: Session = Depends(get_db)):
    """Mark an error as resolved"""
    try:
        success = ErrorStore.resolve_error(error_id)
        if not success:
            raise HTTPException(status_code=404, detail="Error not found")
        return {"message": "Error marked as resolved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving error: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(db: Session = Depends(get_db)):
    """Get overall system health status"""
    try:
        active_errors = ErrorStore.get_active_count()
        total_errors_24h = len(ErrorStore.get_errors(include_resolved=True, last_hours=24))
        
        status = "healthy" if active_errors == 0 else "issues"
        
        return {
            "status": status,
            "active_errors": active_errors,
            "total_errors_24h": total_errors_24h,
            "last_checked": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking system health: {str(e)}")

# Utility function for other services to report errors
def report_bot_error(
    error_type: ErrorType,
    message: str,
    bot_id: Optional[int] = None,
    bot_name: Optional[str] = None,
    details: Optional[Dict] = None
):
    """Utility function for other services to report errors"""
    return ErrorStore.add_error(error_type, message, bot_id, bot_name, details)
