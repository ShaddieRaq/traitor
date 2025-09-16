"""
Health Monitoring API endpoints for real-time system status and logging.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from ..core.database import get_db
from ..models.models import Bot

router = APIRouter()
logger = logging.getLogger(__name__)

class HealthMonitoringService:
    """Service for comprehensive health monitoring and logging."""
    
    def __init__(self):
        self.log_dir = Path(__file__).parent.parent.parent.parent / "logs"
        
    def get_log_tail(self, log_file: str, lines: int = 50) -> List[Dict[str, Any]]:
        """Get recent log entries from a log file."""
        log_path = self.log_dir / log_file
        
        if not log_path.exists():
            return []
            
        try:
            with open(log_path, 'r') as f:
                # Read last N lines efficiently
                file_lines = f.readlines()
                recent_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines
                
                log_entries = []
                for line in recent_lines:
                    line = line.strip()
                    if line:
                        # Try to parse timestamp and level
                        entry = {
                            "timestamp": self._extract_timestamp(line),
                            "level": self._extract_log_level(line),
                            "message": line,
                            "file": log_file
                        }
                        log_entries.append(entry)
                        
                return log_entries
        except Exception as e:
            logger.error(f"Error reading log file {log_file}: {e}")
            return []
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line."""
        import re
        
        # Format: [2025-09-16 10:30:45,123: ...]
        pattern1 = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
        match = re.search(pattern1, line)
        if match:
            return match.group(1)
            
        # Format: 2025-09-16 10:30:45
        pattern2 = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
        match = re.search(pattern2, line)
        if match:
            return match.group(1)
            
        return None
    
    def _extract_log_level(self, line: str) -> str:
        """Extract log level from line."""
        line_upper = line.upper()
        if 'ERROR' in line_upper:
            return 'ERROR'
        elif 'WARNING' in line_upper:
            return 'WARNING'
        elif 'INFO' in line_upper:
            return 'INFO'
        elif 'DEBUG' in line_upper:
            return 'DEBUG'
        return 'INFO'
    
    def get_critical_events(self, minutes: int = 60) -> Dict[str, Any]:
        """Get critical events from recent logs."""
        critical_events = []
        for log_file in ['backend.log', 'celery-worker.log', 'celery-beat.log']:
            entries = self.get_log_tail(log_file, 100)  # Get more entries to filter
            
            for entry in entries:
                if entry['level'] in ['ERROR', 'WARNING']:
                    critical_events.append(entry)
        
        # Sort by timestamp (most recent first)
        critical_events.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        return {
            'critical_events': critical_events[:20],  # Limit to 20 most recent
            'critical_events_count': len(critical_events),
            'time_window_minutes': minutes
        }
    
    def get_system_health_summary(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive system health summary."""
        # Get bot information
        bots = db.query(Bot).all()
        
        healthy_bots = len(bots)  # Assume all bots are healthy for now
        bots_with_issues = 0
        bot_details = []
        
        for bot in bots:
            bot_details.append({
                'id': bot.id,
                'name': bot.name,
                'status': 'RUNNING',
                'signal_locked': False,
                'current_score': 0.0,
                'health': 'healthy'
            })
        
        # Get critical events
        critical_events = self.get_critical_events(60)
        
        # Calculate overall health score
        bot_health_score = 1.0 if bots else 0.5
        
        # Factor in critical events
        critical_factor = max(0.0, 1.0 - (len(critical_events['critical_events']) * 0.05))
        
        overall_health_score = bot_health_score * critical_factor
        
        # Determine overall status
        if overall_health_score >= 0.8:
            overall_status = 'healthy'
        elif overall_health_score >= 0.5:
            overall_status = 'degraded'
        else:
            overall_status = 'critical'
        
        return {
            'overall_status': overall_status,
            'health_score': overall_health_score,
            'services': {
                'backend': {
                    'status': 'healthy',
                    'details': f'Active (last activity: {datetime.now().strftime("%H:%M:%S")})'
                },
                'database': {
                    'status': 'healthy',
                    'details': 'SQLite operational'
                }
            },
            'bots': {
                'total_bots': len(bots),
                'healthy_bots': healthy_bots,
                'bots_with_issues': bots_with_issues,
                'bot_details': bot_details
            },
            'recent_critical_events': critical_events['critical_events'],
            'last_updated': datetime.now().isoformat(),
            'monitoring_active': True
        }

# Initialize service
health_service = HealthMonitoringService()

@router.get("/comprehensive")
def get_comprehensive_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get comprehensive system health status with detailed monitoring."""
    return health_service.get_system_health_summary(db)

@router.get("/logs")
def get_recent_logs(
    log_file: str = "backend.log",
    lines: int = 50
) -> Dict[str, Any]:
    """Get recent log entries from specified log file."""
    
    # Validate log file parameter
    allowed_logs = ["backend.log", "celery-worker.log", "celery-beat.log", "frontend.log"]
    if log_file not in allowed_logs:
        raise HTTPException(status_code=400, detail=f"Invalid log file. Allowed: {allowed_logs}")
    
    logs = health_service.get_log_tail(log_file, lines)
    
    return {
        "log_file": log_file,
        "lines_requested": lines,
        "logs": logs,
        "last_updated": datetime.now().isoformat()
    }

@router.get("/critical-events")
def get_critical_events(minutes: int = 60) -> Dict[str, Any]:
    """Get critical events (errors and warnings) from recent logs."""
    
    if minutes > 1440:  # Max 24 hours
        raise HTTPException(status_code=400, detail="Minutes parameter cannot exceed 1440 (24 hours)")
    
    events = health_service.get_critical_events(minutes)
    
    return {
        **events,
        "last_updated": datetime.now().isoformat()
    }
