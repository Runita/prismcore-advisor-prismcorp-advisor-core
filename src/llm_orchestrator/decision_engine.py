"""
LLM Decision Engine for supply chain incident resolution
"""

from typing import Dict, Any, List
import random
from src.safety_gates.gates import (
    BudgetLimiter,
    SchemaValidator,
    ConfidenceThreshold,
    AuditLogger,
)
from src.tools.tool_registry import execute_tool


class IncidentDecisionEngine:
    """Main orchestrator for incident resolution"""

    def __init__(self):
        self.budget_limiter = BudgetLimiter(max_calls=5)
        self.schema_validator = SchemaValidator()
        self.confidence_threshold = ConfidenceThreshold(threshold=0.75)
        self.audit_logger = AuditLogger()

    def reset_for_incident(self):
        """Reset budget and logs for a new incident"""
        self.budget_limiter = BudgetLimiter(max_calls=5)

    def analyze_incident(self, incident_id: str, shipment_id: str) -> Dict[str, Any]:
        """Analyze an incident and generate recommendation"""

        self.reset_for_incident()
        tools_called = []

        # Tool Call 1: Get shipment status
        result = self.budget_limiter.record_call("get_shipment_status")
        if result["status"] != "ok":
            return {"status": "error", "message": "Budget exhausted", "data": result}

        shipment_result = execute_tool("get_shipment_status", {"shipment_id": shipment_id})
        tools_called.append("get_shipment_status")

        if shipment_result["status"] != "success":
            return {
                "status": "error",
                "message": "Could not retrieve shipment status",
                "data": shipment_result,
            }

        shipment_data = shipment_result["data"]

        # Tool Call 2: Calculate SLA penalty
        result = self.budget_limiter.record_call("calc_sla_penalty")
        if result["status"] != "ok":
            return {"status": "error", "message": "Budget exhausted", "data": result}

        penalty_result = execute_tool(
            "calc_sla_penalty",
            {"delay_hours": shipment_data["delay_hours"], "contract_id": incident_id},
        )
        tools_called.append("calc_sla_penalty")

        penalty_data = penalty_result["data"]

        # Tool Call 3: Check internal stock
        result = self.budget_limiter.record_call("get_internal_stock")
        if result["status"] != "ok":
            return {"status": "error", "message": "Budget exhausted", "data": result}

        stock_result = execute_tool(
            "get_internal_stock", {"product_id": shipment_data["product"]}
        )
        tools_called.append("get_internal_stock")

        has_internal_stock = stock_result["status"] == "success"
        internal_stock_data = stock_result.get("data", {})

        # Tool Call 4: Find alternative suppliers
        result = self.budget_limiter.record_call("find_alt_suppliers")
        if result["status"] != "ok":
            return {"status": "error", "message": "Budget exhausted", "data": result}

        suppliers_result = execute_tool(
            "find_alt_suppliers",
            {"product_id": shipment_data["product"], "lead_time_days": 3},
        )
        tools_called.append("find_alt_suppliers")

        suppliers_data = suppliers_result.get("data", {})

        # Generate recommendation (simulated LLM logic)
        recommendation = self._generate_recommendation(
            shipment_data,
            penalty_data,
            internal_stock_data,
            suppliers_data,
            has_internal_stock,
        )

        # Validate schema
        validation_result = self.schema_validator.validate_recommendation(recommendation)
        if validation_result["status"] != "valid":
            return {
                "status": "error",
                "message": "Invalid recommendation schema",
                "errors": validation_result["errors"],
            }

        # Check confidence threshold
        confidence_score = recommendation["confidence_score"]
        routing = self.confidence_threshold.get_routing(confidence_score)

        # Log decision
        # Include incident-level meta (penalty, cost exposure) in the audit log
        incident_meta = {"penalty": penalty_data}
        log_result = self.audit_logger.log_decision(
            incident_id=incident_id,
            tool_calls=tools_called,
            recommendation=recommendation,
            confidence_score=confidence_score,
            route=routing["route"],
            incident_meta=incident_meta,
        )

        return {
            "status": "success",
            "incident_id": incident_id,
            "incident_data": {
                "shipment": shipment_data,
                "penalty": penalty_data,
                "internal_stock": internal_stock_data if has_internal_stock else None,
                "suppliers": suppliers_data.get("suppliers", []),
            },
            "recommendation": recommendation,
            "routing": routing,
            "tools_called": tools_called,
            "budget_info": self.budget_limiter.get_budget_info(),
            "audit_log_id": log_result.get("log_id"),
        }

    @staticmethod
    def _generate_recommendation(
        shipment_data: Dict[str, Any],
        penalty_data: Dict[str, Any],
        internal_stock_data: Dict[str, Any],
        suppliers_data: Dict[str, Any],
        has_internal_stock: bool,
    ) -> Dict[str, Any]:
        """Simulate LLM recommendation generation"""

        # Logic: If internal stock available and sufficient quantity, recommend internal transfer
        if has_internal_stock:
            quantity_available = internal_stock_data.get("quantity_available", 0)
            quantity_needed = shipment_data.get("quantity", 0)

            if quantity_available >= quantity_needed * 0.5:  # At least 50% available
                cost_per_unit_internal = internal_stock_data.get("cost_per_unit", 0)
                cost_delta = (
                    quantity_needed * cost_per_unit_internal
                    - shipment_data.get("contract_value", 0)
                )

                return {
                    "recommended_option": "Option 2",
                    "confidence_score": 0.87,
                    "reasoning": f"Internal stock transfer available for {quantity_needed} units. Faster delivery (3-4 hours vs 48+ hour delay) and cost-effective at ${cost_per_unit_internal}/unit. Eliminates SLA penalty risk.",
                    "cost_delta": int(cost_delta),
                    "risk_level": "low",
                }

        # Default: Recommend alternate supplier (more expensive but safe)
        if suppliers_data.get("suppliers"):
            best_supplier = suppliers_data["suppliers"][0]  # Cheapest option
            cost_delta = (
                shipment_data.get("quantity", 0)
                * best_supplier.get("cost_per_unit", 0)
                - shipment_data.get("contract_value", 0)
            )

            return {
                "recommended_option": "Option 1",
                "confidence_score": 0.92,
                "reasoning": f"Use alternate supplier {best_supplier.get('name')} with lead time {best_supplier.get('lead_time_days')} days. Highest reliability score ({best_supplier.get('reliability_score')}). Mitigates SLA penalty of ${penalty_data.get('total_penalty', 0)}.",
                "cost_delta": int(cost_delta),
                "risk_level": "medium",
            }

        # Fallback: Request extension
        return {
            "recommended_option": "Option 3",
            "confidence_score": 0.62,
            "reasoning": "Request delivery date extension from customer. Current options limited due to inventory constraints. Requires negotiation with buyer.",
            "cost_delta": 0,
            "risk_level": "high",
        }

    def approve_decision(
        self, log_id: int, shipment_id: str, notes: str = ""
    ) -> Dict[str, Any]:
        """Approve and execute a decision"""
        # Log approval
        approval_result = self.audit_logger.log_approval(
            log_id=log_id, approved=True, notes=notes
        )

        if approval_result["status"] == "error":
            return {"status": "error", "message": approval_result["message"]}

        # In production: trigger S/4HANA update, send notifications, etc.
        return {
            "status": "executed",
            "message": f"Decision approved and executed for shipment {shipment_id}",
            "log_id": log_id,
            "approval_entry": approval_result.get("entry"),
        }

    def reject_decision(self, log_id: int, notes: str = "") -> Dict[str, Any]:
        """Reject a decision and request rethink"""
        rejection_result = self.audit_logger.log_approval(
            log_id=log_id, approved=False, notes=notes
        )

        return {
            "status": "rejected",
            "message": f"Decision rejected. Recommendation needs revision.",
            "log_id": log_id,
            "rejection_entry": rejection_result.get("entry"),
        }

    def get_audit_history(self) -> List[Dict[str, Any]]:
        """Retrieve full audit log"""
        return self.audit_logger.get_audit_log()
