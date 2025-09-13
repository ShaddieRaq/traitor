"""
Coinbase Trade Synchronization Service
DEPRECATED: This service is deprecated in favor of raw_trades system.
Use raw_trade_service.py instead for clean Coinbase data synchronization.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.models import Bot  # Trade model removed - using raw_trades system
# from ..models.models import Trade, Bot  # DEPRECATED: Trade model disabled
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class CoinbaseSyncService:
    """
    DEPRECATED: This service is deprecated in favor of raw_trades system.
    Use RawTradeService instead for clean Coinbase data synchronization.
    """
    
    def __init__(self, db: Session = None):
        raise DeprecationWarning(
            "CoinbaseSyncService is deprecated. Use RawTradeService instead."
        )
    
    def sync_coinbase_trades(self, days_back: int = 1) -> Dict[str, Any]:
        """DEPRECATED: Use RawTradeService.sync_raw_fills() instead."""
        return {
            "success": False,
            "error": "Service deprecated - use RawTradeService instead",
            "replacement": "app.services.raw_trade_service.RawTradeService"
        }
# Global instance for backward compatibility
# coinbase_sync_service = CoinbaseSyncService()  # DISABLED: Use RawTradeService instead
