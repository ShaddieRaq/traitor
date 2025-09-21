"""
Notification System for Market Analysis and Trading Alerts.
Manages different notification channels for market opportunities and system events.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..core.database import get_db
from ..models.models import Bot, Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications across different channels."""
    
    def __init__(self, db=None):
        self.db = db or next(get_db())
    
    def create_market_opportunity_notification(self, 
                                             opportunities: List[Dict[str, Any]], 
                                             scan_summary: Dict[str, Any]) -> None:
        """
        Create notification for market opportunities found.
        
        Args:
            opportunities: List of opportunity candidates
            scan_summary: Summary of the market scan
        """
        try:
            if not opportunities:
                return
            
            # Create title based on number of opportunities
            count = len(opportunities)
            if count == 1:
                title = f"🎯 Market Opportunity: {opportunities[0]['product_id']}"
            else:
                title = f"🎯 {count} Market Opportunities Found"
            
            # Create detailed message
            message_parts = []
            message_parts.append(f"Market scan discovered {count} exceptional trading opportunities:")
            message_parts.append("")
            
            for i, opp in enumerate(opportunities[:5], 1):  # Show top 5
                message_parts.append(f"{i}. **{opp['product_id']}** ({opp['base_name']})")
                message_parts.append(f"   • Score: {opp['total_score']:.1f}/25 ({opp['recommendation']})")
                message_parts.append(f"   • Price: ${opp['price']:.4f} ({opp['price_change_24h']:+.1f}%)")
                message_parts.append(f"   • Volume: ${opp['volume_24h_million']:.1f}M ({opp['volume_change_24h']:+.1f}%)")
                message_parts.append("")
            
            if count > 5:
                message_parts.append(f"... and {count - 5} more opportunities")
            
            message = "\n".join(message_parts)
            
            # Determine priority based on scores
            max_score = max(opp['total_score'] for opp in opportunities)
            priority = "critical" if max_score >= 18 else "high" if max_score >= 15 else "normal"
            
            # Store notification in database
            notification = Notification(
                type="market_opportunity",
                title=title,
                message=message,
                priority=priority,
                data=str({"opportunities": opportunities, "summary": scan_summary})
            )
            
            self.db.add(notification)
            self.db.commit()
            
            # Log to system (existing behavior)
            logger.warning(f"📢 NOTIFICATION CREATED: {title}")
            for opp in opportunities[:3]:
                logger.warning(f"   💎 {opp['product_id']}: {opp['total_score']:.1f}/25")
            
        except Exception as e:
            logger.error(f"Error creating market opportunity notification: {e}")
            self.db.rollback()
    
    def create_system_alert(self, title: str, message: str, priority: str = "normal") -> None:
        """Create a system alert notification."""
        try:
            notification = Notification(
                type="system_alert",
                title=title,
                message=message,
                priority=priority
            )
            
            self.db.add(notification)
            self.db.commit()
            
            logger.info(f"📢 SYSTEM ALERT: {title}")
            
        except Exception as e:
            logger.error(f"Error creating system alert: {e}")
            self.db.rollback()
    
    def create_trade_alert(self, bot_pair: str, trade_info: Dict[str, Any]) -> None:
        """Create a trade execution alert."""
        try:
            title = f"💰 Trade Executed: {bot_pair}"
            
            message = f"""
Trade executed for {bot_pair}:
• Type: {trade_info.get('side', 'Unknown')}
• Amount: {trade_info.get('size', 'Unknown')}
• Price: ${trade_info.get('price', 'Unknown')}
• Status: {trade_info.get('status', 'Unknown')}
            """.strip()
            
            notification = Notification(
                type="trade_alert",
                title=title,
                message=message,
                priority="normal",
                data=str(trade_info)
            )
            
            self.db.add(notification)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating trade alert: {e}")
            self.db.rollback()
    
    def get_recent_notifications(self, limit: int = 20, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get recent notifications."""
        try:
            query = self.db.query(Notification).order_by(Notification.created_at.desc())
            
            if unread_only:
                query = query.filter(Notification.read == False)
            
            notifications = query.limit(limit).all()
            
            return [
                {
                    "id": n.id,
                    "type": n.type,
                    "title": n.title,
                    "message": n.message,
                    "priority": n.priority,
                    "read": n.read,
                    "created_at": n.created_at.isoformat() if n.created_at else datetime.utcnow().isoformat(),
                    "time_ago": self._time_ago(n.created_at) if n.created_at else "Unknown"
                }
                for n in notifications
            ]
            
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []
    
    def mark_as_read(self, notification_id: int) -> bool:
        """Mark a notification as read."""
        try:
            notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
            if notification:
                notification.read = True
                self.db.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            self.db.rollback()
            return False
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        try:
            return self.db.query(Notification).filter(Notification.read == False).count()
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    def _time_ago(self, dt: datetime) -> str:
        """Calculate human-readable time difference."""
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"


# Singleton instance
_notification_service = None

def get_notification_service() -> NotificationService:
    """Get the global notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
