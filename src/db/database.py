import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "prismcore.db")

INITIAL_INCIDENTS = [
    {
        "incident_id": "INC-2026-05-31-001",
        "shipment_id": "PO-789456",
        "port": "Singapore",
        "severity": "critical",
        "status": "open",
        "created_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat() + "Z",
        "cost_exposure": 45000.0,
        "resolution_hours": None,
        "product": "Microchip A3",
        "summary": "Singapore port congestion causing major delay and SLA risk.",
        "approved_at": None,
        "cost_saved": 0.0,
    },
    {
        "incident_id": "INC-2026-05-31-002",
        "shipment_id": "PO-654321",
        "port": "Shanghai",
        "severity": "medium",
        "status": "resolved",
        "created_at": (datetime.utcnow() - timedelta(minutes=18)).isoformat() + "Z",
        "cost_exposure": 0.0,
        "resolution_hours": 2.2,
        "product": "Capacitor XL",
        "summary": "On-time shipment being monitored for value chain continuity.",
        "approved_at": None,
        "cost_saved": 0.0,
    },
]


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY,
            shipment_id TEXT,
            port TEXT,
            severity TEXT,
            status TEXT,
            created_at TEXT,
            cost_exposure REAL,
            resolution_hours REAL,
            product TEXT,
            summary TEXT,
            approved_at TEXT,
            cost_saved REAL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT,
            tool_calls TEXT,
            recommended_option TEXT,
            confidence_score REAL,
            reasoning TEXT,
            risk_level TEXT,
            cost_delta REAL,
            route TEXT,
            status TEXT,
            incident_meta TEXT,
            approval_notes TEXT,
            approval_timestamp TEXT,
            created_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()
    seed_initial_incidents()


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    if row is None:
        return {}
    item = dict(row)
    if 'tool_calls' in item and item['tool_calls'] is not None:
        try:
            item['tool_calls'] = json.loads(item['tool_calls'])
        except Exception:
            item['tool_calls'] = []
    if 'incident_meta' in item and item['incident_meta'] is not None:
        try:
            item['incident_meta'] = json.loads(item['incident_meta'])
        except Exception:
            item['incident_meta'] = {}
    return item


def seed_initial_incidents() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(1) as count FROM incidents")
    result = cursor.fetchone()
    if result and result[0] == 0:
        for incident in INITIAL_INCIDENTS:
            create_incident(incident)
    conn.close()


def create_incident(incident: Dict[str, Any]) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO incidents (incident_id, shipment_id, port, severity, status, created_at, cost_exposure, resolution_hours, product, summary, approved_at, cost_saved) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            incident.get('incident_id'),
            incident.get('shipment_id'),
            incident.get('port'),
            incident.get('severity'),
            incident.get('status'),
            incident.get('created_at'),
            float(incident.get('cost_exposure') or 0),
            incident.get('resolution_hours'),
            incident.get('product'),
            incident.get('summary'),
            incident.get('approved_at'),
            float(incident.get('cost_saved') or 0),
        ),
    )
    conn.commit()
    conn.close()


def get_incident(incident_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)


def get_incidents(status_exclude: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if status_exclude:
        placeholders = ','.join('?' for _ in status_exclude)
        cursor.execute(f"SELECT * FROM incidents WHERE status NOT IN ({placeholders}) ORDER BY created_at DESC", status_exclude)
    else:
        cursor.execute("SELECT * FROM incidents ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]


def get_active_incidents() -> List[Dict[str, Any]]:
    return get_incidents(status_exclude=["resolved", "approved", "rejected"])


def get_recent_incidents(window_minutes: int = 30) -> List[Dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    incidents = get_incidents()
    recent = []
    for incident in incidents:
        try:
            created_at = datetime.fromisoformat(incident['created_at'].replace('Z', '+00:00'))
        except Exception:
            continue
        #if created_at >= cutoff:
        recent.append(incident)
    return recent


def update_incident(incident_id: str, updates: Dict[str, Any]) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    for key, value in updates.items():
        fields.append(f"{key} = ?")
        values.append(value)
    values.append(incident_id)
    cursor.execute(f"UPDATE incidents SET {', '.join(fields)} WHERE incident_id = ?", tuple(values))
    conn.commit()
    conn.close()


def save_audit_entry(entry: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_log (incident_id, tool_calls, recommended_option, confidence_score, reasoning, risk_level, cost_delta, route, status, incident_meta, approval_notes, approval_timestamp, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            entry.get('incident_id'),
            json.dumps(entry.get('tool_calls', [])),
            entry.get('recommended_option'),
            entry.get('confidence_score'),
            entry.get('reasoning'),
            entry.get('risk_level'),
            float(entry.get('cost_delta') or 0),
            entry.get('route'),
            entry.get('status'),
            json.dumps(entry.get('incident_meta', {})),
            entry.get('approval_notes'),
            entry.get('approval_timestamp'),
            entry.get('created_at') or (datetime.utcnow().isoformat() + 'Z'),
        ),
    )
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id


def update_audit_entry(log_id: int, updates: Dict[str, Any]) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    for key, value in updates.items():
        if key in ['tool_calls', 'incident_meta']:
            value = json.dumps(value or {})
        fields.append(f"{key} = ?")
        values.append(value)
    values.append(log_id)
    cursor.execute(f"UPDATE audit_log SET {', '.join(fields)} WHERE log_id = ?", tuple(values))
    conn.commit()
    conn.close()


def get_audit_log() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_log ORDER BY log_id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]


def get_rejected_incidents() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_log WHERE status = 'rejected' ORDER BY approval_timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    rejected = []
    for row in rows:
        entry = row_to_dict(row)
        incident = get_incident(entry.get('incident_id'))
        rejected.append({
            'audit': entry,
            'incident': incident,
        })
    return rejected
