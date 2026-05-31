"""Notification service for alerting and event delivery."""

from datetime import datetime
from typing import Any, Dict, List, Optional


class NotificationService:
    """Simple notification manager for alerts and system messages."""

    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []

    def send_notification(
        self,
        title: str,
        message: str,
        channel: str = "dashboard",
        severity: str = "info",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        notification = {
            "id": len(self.notifications) + 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "title": title,
            "message": message,
            "channel": channel,
            "severity": severity,
            "metadata": metadata or {},
        }
        self.notifications.append(notification)

        return {"status": "sent", "notification": notification}

    def get_notifications(self) -> Dict[str, Any]:
        return {
            "status": "success",
            "notifications": self.notifications,
            "count": len(self.notifications),
        }

    def clear_notifications(self) -> Dict[str, Any]:
        self.notifications = []
        return {"status": "cleared", "count": 0}
