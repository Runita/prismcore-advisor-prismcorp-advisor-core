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

    def alert_recipients_for_severity(self, severity: str) -> List[str]:
        if severity.lower() in ["critical", "high"]:
            return ["VP of Operations", "Supply Chain Head"]
        if severity.lower() == "medium":
            return ["Supply Chain Manager"]
        return ["Operations Analyst"]

    def send_incident_notification(
        self,
        incident_id: str,
        severity: str,
        message: str,
        title: str = "Incident Alert",
        channel: str = "email",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        recipients = self.alert_recipients_for_severity(severity)
        payload = {
            "incident_id": incident_id,
            "severity": severity,
            "recipients": recipients,
            "metadata": metadata or {},
        }
        if metadata:
            payload["metadata"].update(metadata)

        return self.send_notification(
            title=title,
            message=message,
            channel=channel,
            severity=severity,
            metadata=payload,
        )

    def get_notifications(self, page: int = 1, per_page: int = 5) -> Dict[str, Any]:
        total = len(self.notifications)
        page = max(page, 1)
        per_page = max(per_page, 1)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = self.notifications[start:end]
        total_pages = max(1, (total + per_page - 1) // per_page)

        return {
            "status": "success",
            "notifications": page_items,
            "count": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }

    def clear_notifications(self) -> Dict[str, Any]:
        self.notifications = []
        return {"status": "cleared", "count": 0}
