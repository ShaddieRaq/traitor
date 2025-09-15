"""
Order monitoring service for real-time order status tracking.
"""

import asyncio
import logging
from typing import Dict, Any, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.models import Trade

logger = logging.getLogger(__name__)


class OrderMonitoringService:
    """Real-time order status monitoring service."""
    
    def __init__(self, db_session: Session = None):
        self.monitored_orders: Set[str] = set()
        self.monitoring_active = False
        self.db_session = db_session
    
    async def monitor_order(self, order_id: str, trade_id: int, max_duration_minutes: int = 5):
        """Monitor a specific order until it completes or times out."""
        if order_id in self.monitored_orders:
            logger.warning(f"Order {order_id} already being monitored")
            return
        
        self.monitored_orders.add(order_id)
        logger.info(f"🔍 Starting real-time monitoring for order {order_id}")
        
        try:
            # Import here to avoid circular imports
            from .coinbase_service import coinbase_service
            
            start_time = datetime.utcnow()
            check_interval = 2.0  # Check every 2 seconds
            
            while (datetime.utcnow() - start_time).total_seconds() < (max_duration_minutes * 60):
                # Check order status
                try:
                    status = coinbase_service.get_order_status(order_id)
                    
                    if status and status.get('status', '').lower() in ['filled', 'done', 'settled']:
                        # Order completed - update database immediately
                        await self._update_trade_status(trade_id, 'completed')
                        logger.info(f"✅ Order {order_id} completed - database updated")
                        break
                    elif status and status.get('status', '').lower() in ['cancelled', 'rejected']:
                        # Order failed - update database
                        await self._update_trade_status(trade_id, 'failed')
                        logger.info(f"❌ Order {order_id} failed - database updated")
                        break
                        
                except Exception as status_check_error:
                    logger.warning(f"Status check failed for order {order_id}: {status_check_error}")
                    # Continue monitoring despite status check errors
                
                # Wait before next check
                await asyncio.sleep(check_interval)
            
            else:
                # Timeout reached
                logger.warning(f"⏰ Order {order_id} monitoring timed out after {max_duration_minutes}m")
                # Don't update status - let background task handle it
        
        finally:
            self.monitored_orders.discard(order_id)
    
    async def _update_trade_status(self, trade_id: int, new_status: str):
        """Update trade status in database."""
        try:
            # Use passed session if available, otherwise create new one
            if self.db_session:
                db = self.db_session
                should_close = False
            else:
                db = SessionLocal()
                should_close = True
                
            try:
                trade = db.query(Trade).filter(Trade.id == trade_id).first()
                if trade:
                    old_status = trade.status
                    trade.status = new_status
                    if new_status == 'completed' and not trade.filled_at:
                        trade.filled_at = datetime.utcnow()
                    
                    db.commit()
                    logger.info(f"📝 Trade {trade_id} status: {old_status} → {new_status}")
                    
                    # Broadcast update via WebSocket
                    await self._broadcast_status_update(trade)
                    
            finally:
                if should_close:
                    db.close()
                
        except Exception as e:
            logger.error(f"Failed to update trade {trade_id} status: {e}")
    
    async def _broadcast_status_update(self, trade: Trade):
        """Broadcast trade status update via WebSocket."""
        try:
            from ..api.websocket import manager
            
            update_data = {
                "type": "trade_status_update",
                "trade_id": trade.id,
                "bot_id": trade.bot_id,
                "order_id": trade.order_id,
                "status": trade.status,
                "filled_at": trade.filled_at.isoformat() if trade.filled_at else None,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await manager.broadcast_trade_update(update_data)
            logger.info(f"📡 Broadcasted status update for trade {trade.id}")
            
        except Exception as e:
            logger.warning(f"Failed to broadcast status update: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "monitoring_active": self.monitoring_active,
            "monitored_orders_count": len(self.monitored_orders),
            "monitored_orders": list(self.monitored_orders),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance
order_monitor = OrderMonitoringService()
