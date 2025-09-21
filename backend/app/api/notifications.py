"""
Notifications API endpoints.
Manage system notifications for market opportunities and alerts.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from ..core.database import get_db
from ..services.notification_service import get_notification_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def get_notifications(
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to retrieve"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    db: Session = Depends(get_db)
):
    """
    Get recent notifications.
    """
    try:
        from ..services.notification_service import NotificationService
        notification_service = NotificationService(db)
        notifications = notification_service.get_recent_notifications(
            limit=limit,
            unread_only=unread_only
        )
        
        return {
            "notifications": notifications,
            "total_count": len(notifications),
            "unread_count": notification_service.get_unread_count()
        }
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark a notification as read.
    """
    try:
        from ..services.notification_service import NotificationService
        notification_service = NotificationService(db)
        success = notification_service.mark_as_read(notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        return {"message": "Notification marked as read", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")


@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db)):
    """
    Get count of unread notifications.
    """
    try:
        from ..services.notification_service import NotificationService
        notification_service = NotificationService(db)
        count = notification_service.get_unread_count()
        
        return {"unread_count": count}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get unread count: {str(e)}")


@router.post("/test")
def create_test_notification(db: Session = Depends(get_db)):
    """
    Create a test notification for development purposes.
    """
    try:
        from ..services.notification_service import NotificationService
        notification_service = NotificationService(db)
        
        # Create a test market opportunity notification
        test_opportunities = [
            {
                "product_id": "TEST-USD",
                "base_name": "Test Token",
                "price": 1.234,
                "total_score": 16.5,
                "recommendation": "GOOD_CANDIDATE",
                "price_change_24h": 15.5,
                "volume_24h_million": 25.0,
                "volume_change_24h": 125.0
            }
        ]
        
        notification_service.create_market_opportunity_notification(
            test_opportunities,
            {"test": True}
        )
        
        return {"success": True, "message": "Test notification created"}
        
    except Exception as e:
        logger.error(f"Error creating test notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create test notification: {str(e)}")
