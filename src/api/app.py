"""
Flask backend API for PrismCorp Advisor Core
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from src.llm_orchestrator.decision_engine import IncidentDecisionEngine
from src.metrics.kpi_service import KPIService
from src.notifications.notification_service import NotificationService
from src.tools.tool_registry import DEMO_SHIPMENTS, ShipmentData, ShipmentStatus
from src.db.database import init_db, create_incident, get_incident, get_incidents, update_incident, get_rejected_incidents as db_get_rejected_incidents, get_audit_log as db_get_audit_log
from datetime import datetime, timedelta
from src.api.seed_helper import make_recommendation, make_penalty

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize local SQLite database and services
init_db()
decision_engine = IncidentDecisionEngine()
notification_service = NotificationService()
kpi_service = KPIService()


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "PrismCorp Advisor Core"}), 200


@app.route("/api/kpi", methods=["GET"])
def get_kpis():
    metrics = kpi_service.compute_kpis(decision_engine.audit_logger.get_audit_log())
    return jsonify({"status": "success", "metrics": metrics}), 200


@app.route("/api/notifications", methods=["GET", "POST"])
def notifications():
    if request.method == "GET":
        page = request.args.get("page", 1)
        per_page = request.args.get("per_page", 5)
        try:
            page = int(page)
            per_page = int(per_page)
        except ValueError:
            page = 1
            per_page = 5
        return jsonify(notification_service.get_notifications(page=page, per_page=per_page)), 200

    data = request.get_json() or {}
    title = data.get("title", "User Notification")
    message = data.get("message", "User action triggered a notification.")
    channel = data.get("channel", "dashboard")
    severity = data.get("severity", "info")
    metadata = data.get("metadata", {})

    result = notification_service.send_notification(
        title=title,
        message=message,
        channel=channel,
        severity=severity,
        metadata=metadata,
    )
    return jsonify({"status": "success", "notification": result["notification"]}), 200


@app.route("/api/incidents/orchestrate", methods=["POST"])
def orchestrate_incidents():
    incidents = kpi_service.get_active_incidents()
    results = []

    for incident in incidents:
        result = decision_engine.analyze_incident(incident["incident_id"], incident["shipment_id"])
        results.append({
            "incident_id": incident["incident_id"],
            "shipment_id": incident["shipment_id"],
            "result": result,
        })

        if incident["severity"] in ["high", "critical"]:
            notification_service.send_incident_notification(
                incident_id=incident["incident_id"],
                severity=incident["severity"],
                title="High severity incident orchestrated",
                message=(
                    f"Incident {incident['incident_id']} from {incident['port']} is being orchestrated. "
                    f"Severity: {incident['severity']}."
                ),
                metadata={"shipment_id": incident["shipment_id"]},
            )

    return jsonify({"status": "success", "orchestrated": len(results), "results": results}), 200


@app.route("/api/incidents/orcheestate", methods=["POST"])
def orcheestate_create_incident():
    """Create a new incident and optionally start orchestration"""
    try:
        data = request.get_json() or {}
        incident_id = data.get("incident_id")
        shipment_id = data.get("shipment_id")
        port = data.get("port", "Unknown")
        severity = data.get("severity", "medium")
        cost_exposure = data.get("cost_exposure", 0)
        summary = data.get("summary", "New incident created by orchestate")

        if not incident_id or not shipment_id:
            return jsonify({"status": "error", "message": "Missing incident_id or shipment_id"}), 400

        new_incident = {
            "incident_id": incident_id,
            "shipment_id": shipment_id,
            "port": port,
            "severity": severity,
            "status": "open",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "cost_exposure": float(cost_exposure or 0),
            "resolution_hours": None,
            "product": data.get("product", "unknown"),
            "summary": summary,
            "approved_at": None,
            "cost_saved": 0.0,
        }

        # Persist new incident in SQLite
        create_incident(new_incident)

        # Seed mock shipment data if the requested shipment_id is not known
        if shipment_id not in DEMO_SHIPMENTS:
            DEMO_SHIPMENTS[shipment_id] = ShipmentData(
                shipment_id=shipment_id,
                port=port,
                status=ShipmentStatus.DELAYED if severity in ["high", "critical"] else ShipmentStatus.ON_TIME,
                delay_hours=48 if severity in ["high", "critical"] else 0,
                estimated_arrival=(datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                product=new_incident["product"],
                quantity=1000,
                contract_value=float(cost_exposure or 100000),
            )

        # Optionally trigger orchestration for this new incident
        if data.get("analyze", True):
            analyze_result = decision_engine.analyze_incident(incident_id, shipment_id)
            # Send notification for high severity
            if severity in ["high", "critical"]:
                notification_service.send_incident_notification(
                    incident_id=incident_id,
                    severity=severity,
                    title="New high severity incident created",
                    message=f"Incident {incident_id} created and orchestrated.",
                    metadata={"shipment_id": shipment_id},
                )
        else:
            analyze_result = {"status": "skipped"}

        return jsonify({"status": "success", "incident": new_incident, "analyze_result": analyze_result}), 200

    except Exception as e:
        return (jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500)


@app.route("/dashboard", methods=["GET"])
def serve_dashboard():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    return send_from_directory(frontend_dir, "dashboard.html")


@app.route("/", methods=["GET"])
def root():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    return send_from_directory(frontend_dir, "dashboard.html")


@app.route("/demo", methods=["GET"])
def serve_demo():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    return send_from_directory(frontend_dir, "index.html")


@app.route("/api/incidents/analyze", methods=["POST"])
def analyze_incident():
    """
    Analyze an incident and generate recommendation
    Request body:
    {
        "incident_id": "INC-2026-05-31-001",
        "shipment_id": "PO-789456"
    }
    """
    try:
        data = request.get_json()
        incident_id = data.get("incident_id")
        shipment_id = data.get("shipment_id")

        if not incident_id or not shipment_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing incident_id or shipment_id",
                    }
                ),
                400,
            )

        # Analyze incident
        result = decision_engine.analyze_incident(incident_id, shipment_id)

        incident_meta = kpi_service.get_incident(incident_id)
        severity = incident_meta.get("severity", "medium") if incident_meta else "medium"

        if severity in ["high", "critical"] or result.get("routing", {}).get("route") == "human_review":
            notification_service.send_incident_notification(
                incident_id=incident_id,
                severity=severity,
                title="Incident requires attention",
                message=(
                    f"Incident {incident_id} ({shipment_id}) requires review. "
                    f"Severity: {severity}. Route: {result.get('routing', {}).get('route')}"
                ),
                metadata={"shipment_id": shipment_id, "incident_route": result.get("routing", {}).get("route")},
            )

        return jsonify(result), 200 if result["status"] == "success" else 400

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Server error: {str(e)}"}),
            500,
        )


@app.route("/api/incidents/<incident_id>/approve", methods=["POST"])
def approve_incident(incident_id):
    """
    Approve a recommendation and execute
    Request body:
    {
        "log_id": 1,
        "notes": "Approved. Proceed with internal transfer."
    }
    """
    try:
        data = request.get_json()
        log_id = data.get("log_id")
        notes = data.get("notes", "")

        if not log_id:
            return jsonify({"status": "error", "message": "Missing log_id"}), 400

        result = decision_engine.approve_decision(log_id, incident_id, notes)

        # Post-process: mark incident as approved and compute cost saved
        try:
            # approval entry should be returned under result['approval_entry']
            approval_entry = result.get("approval_entry") or {}

            # Compute cost saved: penalty avoided minus cost delta (if available)
            incident_meta = approval_entry.get("incident_meta", {})
            penalty = 0.0
            if isinstance(incident_meta, dict):
                penalty_val = incident_meta.get("penalty", {})
                # penalty_val may be a dict with 'total_penalty' or a number
                if isinstance(penalty_val, dict):
                    penalty = float(penalty_val.get("total_penalty", 0) or 0)
                else:
                    try:
                        penalty = float(penalty_val)
                    except Exception:
                        penalty = 0.0

            cost_delta = approval_entry.get("cost_delta") or 0
            try:
                cost_delta_val = float(cost_delta)
            except Exception:
                cost_delta_val = 0.0

            # Ensure cost_saved is non-negative: penalty minus cost_delta
            cost_saved = max(0.0, penalty - cost_delta_val)

            incident_obj = kpi_service.get_incident(incident_id)
            if incident_obj:
                resolved_hours = None
                try:
                    created_at = incident_obj.get("created_at")
                    created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    resolved_hours = (datetime.utcnow() - created_dt).total_seconds() / 3600.0
                except Exception:
                    resolved_hours = incident_obj.get("resolution_hours")

                update_incident(
                    incident_id,
                    {
                        "status": "approved",
                        "approved_at": datetime.utcnow().isoformat() + "Z",
                        "cost_saved": cost_saved,
                        "resolution_hours": round(resolved_hours, 2) if resolved_hours is not None else None,
                    },
                )

        except Exception:
            pass

        return jsonify(result), 200

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Server error: {str(e)}"}),
            500,
        )


@app.route("/api/incidents/<incident_id>/reject", methods=["POST"])
def reject_incident(incident_id):
    """
    Reject a recommendation and request revision
    Request body:
    {
        "log_id": 1,
        "notes": "Cost delta too high. Explore alternative options."
    }
    """
    try:
        data = request.get_json()
        log_id = data.get("log_id")
        notes = data.get("notes", "")

        if not log_id:
            return jsonify({"status": "error", "message": "Missing log_id"}), 400

        result = decision_engine.reject_decision(log_id, notes)

        try:
            incident_obj = kpi_service.get_incident(incident_id)
            if incident_obj:
                resolved_hours = None
                try:
                    created_at = incident_obj.get("created_at")
                    created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    resolved_hours = (datetime.utcnow() - created_dt).total_seconds() / 3600.0
                except Exception:
                    resolved_hours = incident_obj.get("resolution_hours")

                update_incident(
                    incident_id,
                    {
                        "status": "rejected",
                        "resolution_hours": round(resolved_hours, 2) if resolved_hours is not None else None,
                    },
                )
        except Exception:
            pass

        return jsonify(result), 200

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Server error: {str(e)}"}),
            500,
        )


@app.route("/api/audit-log", methods=["GET"])
def get_audit_log():
    """Retrieve full audit log"""
    try:
        audit_log = db_get_audit_log()
        return (
            jsonify({"status": "success", "audit_log": audit_log, "count": len(audit_log)}),
            200,
        )

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Server error: {str(e)}"}),
            500,
        )


@app.route("/api/demo/seed_audit", methods=["POST"])
def seed_audit_entries():
    """Seed demo audit entries for testing pagination and KPI effects.
    Request body (optional): { "count": 15, "approved_ratio": 0.3 }
    """
    try:
        data = request.get_json() or {}
        count = int(data.get("count", 15))
        approved_ratio = float(data.get("approved_ratio", 0.3))
        created = []
        for i in range(count):
            inc_id = f"DEMO-AUD-{i+1:03d}"
            rec = make_recommendation()
            penalty = make_penalty()
            res = decision_engine.audit_logger.log_decision(
                incident_id=inc_id,
                tool_calls=["seed"],
                recommendation=rec,
                confidence_score=rec.get("confidence_score", 0.6),
                route="dashboard",
                incident_meta={"penalty": penalty},
            )
            created.append(res.get("entry"))

        # Approve a subset based on approved_ratio
        approved_count = int(round(count * approved_ratio))
        for idx in range(approved_count):
            decision_engine.audit_logger.log_approval(idx + 1, approved=True, notes="Auto-approved for demo")

        return jsonify({"status": "success", "created": len(created), "approved": approved_count}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/demo/incidents", methods=["GET"])
def get_demo_incidents():
    """Get dynamic incident list for the demo incident selector"""
    incidents = [
        {
            "incident_id": incident["incident_id"],
            "shipment_id": incident["shipment_id"],
            "port": incident.get("port", "Unknown"),
            "severity": incident.get("severity", "medium"),
            "status": incident.get("status", "open"),
            "cost_exposure": incident.get("cost_exposure", 0),
            "summary": incident.get("summary", ""),
            "created_at": incident.get("created_at"),
        }
        for incident in kpi_service.get_active_incidents()
    ]

    return (
        jsonify(
            {
                "status": "success",
                "incidents": incidents,
            }
        ),
        200,
    )


@app.route("/api/incidents/rejected", methods=["GET"])
def get_rejected_incidents_route():
    """Retrieve rejected incidents and rejection details"""
    rejected_data = db_get_rejected_incidents()
    return jsonify({"status": "success", "rejected_incidents": rejected_data}), 200


@app.route("/rejected", methods=["GET"])
def serve_rejected_incidents_page():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    return send_from_directory(frontend_dir, "rejected.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
