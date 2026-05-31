# Tool Catalog

This document defines the available tools in the PrismCorp Advisor Core system, their purpose, inputs, outputs, and expected behavior.

## Overview
The tool catalog is the core set of pre-vetted tool operations that the incident decision engine can call. Each tool is designed to provide a structured response, avoid free-form output, and support safe orchestration.

## Tools

### `get_shipment_status`
- Purpose: Retrieve current shipment status and metadata from the supply chain source system.
- Inputs:
  - `shipment_id` (str) — Unique shipment or purchase order identifier.
- Outputs:
  - `status` (success|error)
  - `data`:
    - `shipment_id` (str)
    - `port` (str)
    - `status` (str) — e.g. `delayed`, `on_time`, `at_risk`
    - `delay_hours` (int)
    - `estimated_arrival` (str)
    - `product` (str)
    - `quantity` (int)
    - `contract_value` (float)
- Behavior:
  - Returns valid shipment details when the shipment exists.
  - Returns an error if the shipment cannot be found.

### `find_alt_suppliers`
- Purpose: Identify alternate suppliers that can fulfill the product demand within a maximum lead time.
- Inputs:
  - `product_id` (str)
  - `lead_time_days` (int)
- Outputs:
  - `status` (success|error)
  - `data`:
    - `product_id` (str)
    - `suppliers` (list)
    - `count` (int)
  - Each supplier item includes:
    - `supplier_id` (str)
    - `name` (str)
    - `location` (str)
    - `lead_time_days` (int)
    - `cost_per_unit` (float)
    - `reliability_score` (float)
- Behavior:
  - Filters supplier candidates by the requested lead-time constraint.
  - Sorts candidates by cost ascending.

### `calc_sla_penalty`
- Purpose: Compute the contract SLA penalty associated with the shipment delay.
- Inputs:
  - `delay_hours` (int)
  - `contract_id` (str, optional)
- Outputs:
  - `status` (success|error)
  - `data`:
    - `contract_id` (str|None)
    - `delay_hours` (int)
    - `penalty_rate_per_hour` (int)
    - `total_penalty` (int)
    - `threshold_hours` (int)
    - `exceeds_threshold` (bool)
- Behavior:
  - Returns a computed penalty and threshold indication.

### `get_internal_stock`
- Purpose: Determine internal inventory availability for the product and support internal transfer decisions.
- Inputs:
  - `product_id` (str)
- Outputs:
  - `status` (success|error)
  - `data`:
    - `product_id` (str)
    - `location` (str)
    - `quantity_available` (int)
    - `cost_per_unit` (float)
    - `total_value` (float)
- Behavior:
  - Provides internal stock details when available.
  - Returns an error if the product is not found in internal inventory.

### `query_vector_store`
- Purpose: Retrieve similar historical incidents from the long-term memory vector store.
- Inputs:
  - `query` (str)
- Outputs:
  - `status` (success|error)
  - `data`:
    - `query` (str)
    - `similar_incidents` (list)
    - `count` (int)
- Behavior:
  - Performs a semantic search or similarity lookup against resolved incident history.
  - Returns structured historical incidents for reasoning context.

## Integration Guidelines
- All tool responses must adhere to the `status`/`data` contract.
- Tools should not return unstructured text as the main result payload.
- The decision engine relies on these tools to make recommendations, validate schema, and decide escalation routing.

## Future tool candidates
- `get_port_capacity` — estimate current port throughput for congestion scoring.
- `evaluate_risk_profile` — compute supplier/route risk using live external data.
- `notify_stakeholders` — send alerts to specific operational roles.
