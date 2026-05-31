"""KPI service for dashboard metrics and incident summaries."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from src.db.database import get_active_incidents, get_incident, get_recent_incidents


DEMO_INCIDENTS = [
    {
        "incident_id": "INC-2026-05-31-001",
        "shipment_id": "PO-789456",
        "port": "Singapore",
        "severity": "critical",
        "status": "open",
        "created_at": datetime.utcnow() - timedelta(minutes=30),
        "cost_exposure": 45000,
        "resolution_hours": None,
        "product": "Microchip A3",
        "summary": "Singapore port congestion causing major delay and SLA risk.",
    },
    {
        "incident_id": "INC-2026-05-31-002",
        "shipment_id": "PO-654321",
        "port": "Shanghai",
        "severity": "medium",
        "status": "resolved",
        "created_at": datetime.utcnow() - timedelta(minutes=18),
        "cost_exposure": 0,
        "resolution_hours": 2.2,
        "product": "Capacitor XL",
        "summary": "On-time shipment being monitored for value chain continuity.",
    },
]


class KPIService:
    """Compute KPI metrics for dashboard display."""

    def __init__(self):
        pass

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return get_incident(incident_id)

    def get_active_incidents(self) -> List[Dict[str, Any]]:
        return get_active_incidents()

    def compute_kpis(self, audit_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        window_minutes = 30
        recent_incidents = get_recent_incidents(window_minutes)

        active_recent_incidents = [
            incident
            for incident in recent_incidents
            if incident.get("status") not in ["approved", "rejected"]
        ]

        total_incidents = len(active_recent_incidents)
        open_incidents = sum(
            1 for incident in active_recent_incidents if incident["status"] != "resolved"
        )
        high_severity_incidents = sum(
            1 for incident in active_recent_incidents if incident["severity"] in ["high", "critical"]
        )
        resolved_incidents = [
            incident for incident in recent_incidents if incident["resolution_hours"] is not None
        ]

        approved_resolved = [
            incident for incident in recent_incidents
            if incident["status"] == "approved" and incident["resolution_hours"] is not None
        ]
        rejected_resolved = [
            incident for incident in recent_incidents
            if incident["status"] == "rejected" and incident["resolution_hours"] is not None
        ]

        avg_resolution_hours = (
            sum(incident["resolution_hours"] for incident in resolved_incidents) / len(resolved_incidents)
            if resolved_incidents
            else 0.0
        )
        avg_resolution_approved = (
            sum(incident["resolution_hours"] for incident in approved_resolved) / len(approved_resolved)
            if approved_resolved
            else 0.0
        )
        avg_resolution_rejected = (
            sum(incident["resolution_hours"] for incident in rejected_resolved) / len(rejected_resolved)
            if rejected_resolved
            else 0.0
        )

        total_cost_exposure = sum(incident["cost_exposure"] for incident in active_recent_incidents)
        total_cost_saved = sum(
            incident.get("cost_saved", 0) or 0 for incident in recent_incidents if incident.get("status") == "approved"
        )

        # Exclude pending approvals (e.g. 'pending_approval') from the approval rate calculation.
        decision_entries = [
            entry
            for entry in audit_log
            if entry.get("status") and "pending" not in str(entry.get("status")).lower()
        ]
        approval_count = sum(1 for entry in decision_entries if entry.get("status") == "approved")
        decision_count = len(decision_entries)
        approval_rate = (approval_count / decision_count) if decision_count else 0.0

        return {
            "window_minutes": window_minutes,
            "total_incidents": total_incidents,
            "open_incidents": open_incidents,
            "high_severity_incidents": high_severity_incidents,
            "avg_resolution_hours": round(avg_resolution_hours, 2),
            "avg_resolution_approved": round(avg_resolution_approved, 2),
            "avg_resolution_rejected": round(avg_resolution_rejected, 2),
            "total_cost_exposure": total_cost_exposure,
            "total_cost_saved": round(total_cost_saved, 2),
            "approval_rate": round(approval_rate * 100, 1),
            "recent_incidents": [
                {
                    "incident_id": incident["incident_id"],
                    "shipment_id": incident["shipment_id"],
                    "port": incident["port"],
                    "severity": incident["severity"],
                    "status": incident["status"],
                    "cost_exposure": incident["cost_exposure"],
                    "summary": incident["summary"],
                    "created_at": incident["created_at"],
                }
                for incident in active_recent_incidents
            ],
        }

    def get_summary(self) -> Dict[str, Any]:
        return {
            "active_incidents": len(self.get_active_incidents()),
            "incident_snapshots": [
                {
                    "incident_id": incident["incident_id"],
                    "severity": incident["severity"],
                    "status": incident["status"],
                    "summary": incident["summary"],
                }
                for incident in self.get_active_incidents()
            ],
        }
