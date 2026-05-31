"""
Safety gates for LLM-driven decision system
"""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum
import json


class BudgetStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    EXHAUSTED = "exhausted"


@dataclass
class LLMRecommendation:
    recommended_option: str
    confidence_score: float
    reasoning: str
    cost_delta: int
    risk_level: str


class BudgetLimiter:
    """Gate 1: Tool-call budget enforcement"""

    def __init__(self, max_calls: int = 5):
        self.max_calls = max_calls
        self.calls_used = 0
        self.call_log = []

    def can_call(self) -> bool:
        return self.calls_used < self.max_calls

    def record_call(self, tool_name: str) -> Dict[str, Any]:
        if not self.can_call():
            return {
                "status": "error",
                "message": f"Budget exhausted: {self.calls_used}/{self.max_calls}",
                "budget_status": BudgetStatus.EXHAUSTED.value,
            }

        self.calls_used += 1
        self.call_log.append(
            {"tool": tool_name, "call_number": self.calls_used, "timestamp": "now"}
        )

        return {
            "status": "ok",
            "calls_used": self.calls_used,
            "calls_remaining": self.max_calls - self.calls_used,
            "budget_status": (
                BudgetStatus.WARNING.value
                if self.calls_used >= self.max_calls - 1
                else BudgetStatus.OK.value
            ),
        }

    def get_budget_info(self) -> Dict[str, Any]:
        return {
            "calls_used": self.calls_used,
            "max_calls": self.max_calls,
            "calls_remaining": self.max_calls - self.calls_used,
            "call_log": self.call_log,
        }


class SchemaValidator:
    """Gate 2: Output schema validation"""

    VALID_OPTIONS = ["Option 1", "Option 2", "Option 3"]
    VALID_RISK_LEVELS = ["low", "medium", "high"]

    @staticmethod
    def validate_recommendation(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate LLM recommendation against schema"""
        errors = []

        # Check required fields
        required_fields = [
            "recommended_option",
            "confidence_score",
            "reasoning",
            "cost_delta",
            "risk_level",
        ]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validate recommended_option
        if data.get("recommended_option") not in SchemaValidator.VALID_OPTIONS:
            errors.append(
                f"Invalid option. Must be one of: {SchemaValidator.VALID_OPTIONS}"
            )

        # Validate confidence_score
        try:
            score = float(data.get("confidence_score", -1))
            if not (0.0 <= score <= 1.0):
                errors.append("Confidence score must be between 0.0 and 1.0")
        except (TypeError, ValueError):
            errors.append("Confidence score must be a float")

        # Validate reasoning length
        reasoning = data.get("reasoning", "")
        if len(reasoning) > 500:
            errors.append("Reasoning must be <= 500 characters")
        if len(reasoning) < 10:
            errors.append("Reasoning must be >= 10 characters")

        # Validate cost_delta
        try:
            int(data.get("cost_delta", None))
        except (TypeError, ValueError):
            errors.append("Cost delta must be an integer")

        # Validate risk_level
        if data.get("risk_level") not in SchemaValidator.VALID_RISK_LEVELS:
            errors.append(
                f"Invalid risk level. Must be one of: {SchemaValidator.VALID_RISK_LEVELS}"
            )

        if errors:
            return {"status": "invalid", "errors": errors}

        return {"status": "valid", "data": data}


class ConfidenceThreshold:
    """Gate 3: Confidence threshold for human escalation"""

    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold

    def should_escalate(self, confidence_score: float) -> bool:
        """Return True if recommendation should be escalated to human"""
        return confidence_score < self.threshold

    def get_routing(self, confidence_score: float) -> Dict[str, Any]:
        """Determine where to route the recommendation"""
        should_escalate = self.should_escalate(confidence_score)

        if should_escalate:
            return {
                "route": "human_review",
                "reason": f"Confidence score {confidence_score} below threshold {self.threshold}",
                "reviewer": "Supply Chain Head",
                "priority": "high",
            }
        else:
            return {
                "route": "dashboard",
                "reason": f"Confidence score {confidence_score} meets threshold",
                "priority": "normal",
            }


class AuditLogger:
    """Gate 4 (v1): Audit logging for all decisions"""

    def __init__(self):
        self.audit_log = []

    def log_decision(
        self,
        incident_id: str,
        tool_calls: List[str],
        recommendation: Dict[str, Any],
        confidence_score: float,
        route: str,
    ) -> Dict[str, Any]:
        """Log a decision for audit trail"""
        log_entry = {
            "timestamp": "2026-05-31T12:00:00Z",  # Mock timestamp
            "incident_id": incident_id,
            "tool_calls_used": tool_calls,
            "tool_calls_count": len(tool_calls),
            "recommended_option": recommendation.get("recommended_option"),
            "confidence_score": confidence_score,
            "reasoning": recommendation.get("reasoning"),
            "risk_level": recommendation.get("risk_level"),
            "cost_delta": recommendation.get("cost_delta"),
            "route": route,
            "status": "pending_approval",
        }

        self.audit_log.append(log_entry)

        return {
            "status": "logged",
            "log_id": len(self.audit_log),
            "entry": log_entry,
        }

    def log_approval(self, log_id: int, approved: bool, notes: str = "") -> Dict[str, Any]:
        """Log human approval/rejection"""
        if log_id <= 0 or log_id > len(self.audit_log):
            return {"status": "error", "message": "Invalid log ID"}

        self.audit_log[log_id - 1]["status"] = "approved" if approved else "rejected"
        self.audit_log[log_id - 1]["approval_notes"] = notes
        self.audit_log[log_id - 1]["approval_timestamp"] = "2026-05-31T12:05:00Z"

        return {
            "status": "logged",
            "log_id": log_id,
            "entry": self.audit_log[log_id - 1],
        }

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Retrieve audit log"""
        return self.audit_log
