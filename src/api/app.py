"""
Flask backend API for PrismCorp Advisor Core
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from src.llm_orchestrator.decision_engine import IncidentDecisionEngine

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize decision engine
decision_engine = IncidentDecisionEngine()


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "PrismCorp Advisor Core"}), 200


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
        audit_log = decision_engine.get_audit_history()
        return (
            jsonify({"status": "success", "audit_log": audit_log, "count": len(audit_log)}),
            200,
        )

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Server error: {str(e)}"}),
            500,
        )


@app.route("/api/demo/incidents", methods=["GET"])
def get_demo_incidents():
    """Get available demo incidents for testing"""
    return (
        jsonify(
            {
                "status": "success",
                "incidents": [
                    {
                        "incident_id": "INC-2026-05-31-001",
                        "shipment_id": "PO-789456",
                        "description": "Singapore Port Congestion - Microchip A3",
                        "sla_penalty_risk": "$45,000",
                        "time_remaining": "36 hours",
                    },
                    {
                        "incident_id": "INC-2026-05-31-002",
                        "shipment_id": "PO-654321",
                        "description": "Shanghai On-Time - Capacitor XL (test incident)",
                        "sla_penalty_risk": "$0",
                        "time_remaining": "N/A",
                    },
                ],
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
