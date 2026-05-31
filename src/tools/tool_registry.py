"""
Tool registry and implementations for PrismCorp Advisor Core
Simulates real supply chain data for demo purposes
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum
import json
from datetime import datetime, timedelta
import random


class ShipmentStatus(str, Enum):
    DELAYED = "delayed"
    ON_TIME = "on_time"
    AT_RISK = "at_risk"


@dataclass
class ShipmentData:
    shipment_id: str
    port: str
    status: ShipmentStatus
    delay_hours: int
    estimated_arrival: str
    product: str
    quantity: int
    contract_value: float


@dataclass
class Supplier:
    supplier_id: str
    name: str
    location: str
    lead_time_days: int
    cost_per_unit: float
    reliability_score: float  # 0-1


@dataclass
class InventoryLevel:
    product_id: str
    location: str
    quantity_available: int
    cost_per_unit: float


# ==================== IN-MEMORY DATA ====================

DEMO_SHIPMENTS = {
    "PO-789456": ShipmentData(
        shipment_id="PO-789456",
        port="Singapore",
        status=ShipmentStatus.DELAYED,
        delay_hours=48,
        estimated_arrival="2026-06-02T14:00:00Z",
        product="Microchip A3",
        quantity=5000,
        contract_value=250000,
    ),
    "PO-654321": ShipmentData(
        shipment_id="PO-654321",
        port="Shanghai",
        status=ShipmentStatus.ON_TIME,
        delay_hours=0,
        estimated_arrival="2026-05-31T10:00:00Z",
        product="Capacitor XL",
        quantity=10000,
        contract_value=150000,
    ),
}

DEMO_SUPPLIERS = {
    "SUP-001": Supplier(
        supplier_id="SUP-001",
        name="Asia Electronics Ltd",
        location="Taiwan",
        lead_time_days=7,
        cost_per_unit=52.5,
        reliability_score=0.95,
    ),
    "SUP-002": Supplier(
        supplier_id="SUP-002",
        name="Global Components Inc",
        location="Singapore",
        lead_time_days=3,
        cost_per_unit=55.0,
        reliability_score=0.92,
    ),
    "SUP-003": Supplier(
        supplier_id="SUP-003",
        name="Eastern Precision Co",
        location="Vietnam",
        lead_time_days=10,
        cost_per_unit=48.0,
        reliability_score=0.88,
    ),
}

DEMO_INTERNAL_STOCK = {
    "Microchip A3": InventoryLevel(
        product_id="Microchip A3",
        location="Entity B Warehouse",
        quantity_available=3000,
        cost_per_unit=50.0,
    ),
    "Capacitor XL": InventoryLevel(
        product_id="Capacitor XL",
        location="Regional Hub",
        quantity_available=8000,
        cost_per_unit=15.0,
    ),
}

DEMO_RESOLVED_INCIDENTS = [
    {
        "incident_id": "INC-2026-03-15",
        "port": "Singapore",
        "cost_impact": 42000,
        "chosen_option": "internal_transfer",
        "outcome": "success",
        "resolution_time_hours": 3.5,
        "embedding": [0.1, 0.2, 0.15, 0.05],  # Mock embedding
    },
    {
        "incident_id": "INC-2025-11-22",
        "port": "Singapore",
        "cost_impact": 38000,
        "chosen_option": "internal_transfer",
        "outcome": "success",
        "resolution_time_hours": 2.8,
        "embedding": [0.12, 0.18, 0.14, 0.06],
    },
    {
        "incident_id": "INC-2025-07-08",
        "port": "Shanghai",
        "cost_impact": 35000,
        "chosen_option": "alternate_supplier",
        "outcome": "success",
        "resolution_time_hours": 4.2,
        "embedding": [0.08, 0.25, 0.12, 0.04],
    },
]


# ==================== TOOL IMPLEMENTATIONS ====================


def get_shipment_status(shipment_id: str) -> Dict[str, Any]:
    """Get shipment status from S/4HANA"""
    if shipment_id in DEMO_SHIPMENTS:
        shipment = DEMO_SHIPMENTS[shipment_id]
        return {
            "status": "success",
            "data": {
                "shipment_id": shipment.shipment_id,
                "port": shipment.port,
                "status": shipment.status.value,
                "delay_hours": shipment.delay_hours,
                "estimated_arrival": shipment.estimated_arrival,
                "product": shipment.product,
                "quantity": shipment.quantity,
                "contract_value": shipment.contract_value,
            },
        }
    return {
        "status": "error",
        "message": f"Shipment {shipment_id} not found",
    }


def find_alt_suppliers(product_id: str, lead_time_days: int) -> Dict[str, Any]:
    """Find alternative suppliers for a product"""
    candidates = []
    for supplier in DEMO_SUPPLIERS.values():
        if supplier.lead_time_days <= lead_time_days:
            candidates.append(
                {
                    "supplier_id": supplier.supplier_id,
                    "name": supplier.name,
                    "location": supplier.location,
                    "lead_time_days": supplier.lead_time_days,
                    "cost_per_unit": supplier.cost_per_unit,
                    "reliability_score": supplier.reliability_score,
                }
            )

    # Sort by cost (ascending)
    candidates.sort(key=lambda x: x["cost_per_unit"])

    return {
        "status": "success",
        "data": {
            "product_id": product_id,
            "suppliers": candidates,
            "count": len(candidates),
        },
    }


def calc_sla_penalty(delay_hours: int, contract_id: str = None) -> Dict[str, Any]:
    """Calculate SLA penalty for a delayed shipment"""
    # Mock penalty calculation: $1,250 per hour of delay
    penalty_rate = 1250
    penalty = delay_hours * penalty_rate

    return {
        "status": "success",
        "data": {
            "contract_id": contract_id,
            "delay_hours": delay_hours,
            "penalty_rate_per_hour": penalty_rate,
            "total_penalty": penalty,
            "threshold_hours": 36,
            "exceeds_threshold": delay_hours > 36,
        },
    }


def get_internal_stock(product_id: str) -> Dict[str, Any]:
    """Check internal stock levels"""
    if product_id in DEMO_INTERNAL_STOCK:
        stock = DEMO_INTERNAL_STOCK[product_id]
        return {
            "status": "success",
            "data": {
                "product_id": stock.product_id,
                "location": stock.location,
                "quantity_available": stock.quantity_available,
                "cost_per_unit": stock.cost_per_unit,
                "total_value": stock.quantity_available * stock.cost_per_unit,
            },
        }
    return {
        "status": "error",
        "message": f"Product {product_id} not in internal inventory",
    }


def query_vector_store(query: str) -> Dict[str, Any]:
    """Query vector store for similar resolved incidents"""
    # Mock semantic search - return all incidents for demo
    return {
        "status": "success",
        "data": {
            "query": query,
            "similar_incidents": DEMO_RESOLVED_INCIDENTS,
            "count": len(DEMO_RESOLVED_INCIDENTS),
        },
    }


# ==================== TOOL REGISTRY ====================

TOOL_REGISTRY = {
    "get_shipment_status": get_shipment_status,
    "find_alt_suppliers": find_alt_suppliers,
    "calc_sla_penalty": calc_sla_penalty,
    "get_internal_stock": get_internal_stock,
    "query_vector_store": query_vector_store,
}


def execute_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool from the registry"""
    if tool_name not in TOOL_REGISTRY:
        return {
            "status": "error",
            "message": f"Tool {tool_name} not found in registry",
        }

    try:
        tool_func = TOOL_REGISTRY[tool_name]
        return tool_func(**args)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Tool execution failed: {str(e)}",
        }
