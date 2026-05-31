# System Architecture

## Overview

PrismCorp Advisor Core is a production-grade LLM orchestration system designed for high-stakes supply chain decisions. It combines three layers: bounded tool execution, dual memory (short + long-term), and safety gates.

## Layer 1: Tool-Bounded LLM

### Why Not Raw LLM?

| Risk | Tool-Bounded Solution |
|------|----------------------|
| SQL injection attacks | Pre-built, validated SQL queries |
| Unauthorized data access | Row-level security baked into tools |
| Unpredictable API costs | Explicit tool budget (≤5 calls/incident) |
| Non-auditable decisions | Every tool call is logged + versioned |

### Tool Catalog

```python
# Example tool definitions
get_shipment_status(port: str, status: str) -> ShipmentData
find_alt_suppliers(product_id: str, lead_time_days: int) -> List[Supplier]
calc_sla_penalty(delay_hours: int, contract_id: str) -> float
get_internal_stock(product_id: str) -> InventoryLevel
```

**Design principle**: Each tool returns a fixed schema, not arbitrary data. LLM cannot invent new tools or modify queries.

## Layer 2: Dual Memory System

### Short-Term: Incident Scratchpad

```
┌─────────────────────────────────┐
│ Current Incident Context        │
├─────────────────────────────────┤
│ incident_id: INC-2026-05-31-001 │
│ port: Singapore                 │
│ shipment_id: PO-789456          │
│ penalty_risk: $45,000           │
│ time_remaining: 36 hours        │
│ tool_calls_used: 3/5            │
│ decision_state: PENDING         │
└─────────────────────────────────┘
      Lifetime: ~10 minutes
      (cleared after resolution)
```

### Long-Term: Vector Store in S/4HANA

```sql
CREATE TABLE resolved_incidents (
  incident_id STRING PRIMARY KEY,
  port_location STRING,
  cost_impact DECIMAL,
  chosen_option STRING,
  outcome STRING,
  resolution_time_hours INT,
  embedding NCLOB,  -- Vector: 384-dim sentence-transformer
  created_date TIMESTAMP,
  INDEX idx_vector ON embedding
);
```

**Query example**:
```
Vector search: "Find incidents with port delays >$40k penalty + >24 hour window"
Returns: [INC-2026-03-15, INC-2025-11-22, INC-2025-07-08]
```

### Learning Loop

```
New Incident
  ↓
Query: "Similar port congestion cases?"
  ↓
Vector DB returns: 7 past incidents
  ↓
LLM sees: "In 5 of 7 similar cases, Option 2 (internal transfer) worked best"
  ↓
LLM recommends: Option 2 (informed by history)
  ↓
Human approves
  ↓
Store in Vector DB (next incident learns from this one)
```

## Layer 3: Safety Gates

### Gate 1: Tool-Call Budget

```python
class BudgetLimiter:
    def __init__(self, max_calls: int = 5):
        self.max_calls = max_calls
        self.calls_used = 0
    
    def call_tool(self, tool_name: str, args: dict):
        if self.calls_used >= self.max_calls:
            raise BudgetExhausted(f"Used {self.calls_used}/{self.max_calls}")
        result = tool_registry.execute(tool_name, args)
        self.calls_used += 1
        return result
```

**Effect**: Forces LLM to decide with limited data, prevents infinite loops.

### Gate 2: Schema Validation

```python
@dataclass
class LLMRecommendation:
    recommended_option: str  # Must be in ["Option 1", "Option 2", "Option 3"]
    confidence_score: float  # 0.0 - 1.0
    reasoning: str           # Max 500 chars
    cost_delta: int          # Calculated field
    risk_level: str          # Must be in ["low", "medium", "high"]

# Validation
try:
    rec = LLMRecommendation(**llm_output)
except ValidationError as e:
    # Reject malformed output, request retry
    log_error(f"Invalid recommendation: {e}")
    raise
```

**Effect**: No free-form text, structured data only, easy to audit and act on.

### Gate 3: Confidence Threshold

```python
if recommendation.confidence_score > 0.75:
    # Auto-approve (v2+), or route to dashboard (v1)
    route_to_dashboard(recommendation)
else:
    # Escalate to Supply Chain Head
    escalate_to_human(
        recommendation=recommendation,
        reason="Low confidence",
        data_provided=[...]
    )
```

**Effect**: Human reviews edge cases; LLM handles routine decisions.

### Gate 4: Propose-Only (v1)

```
LLM output: {
  "recommended_option": "Option 2",
  "confidence_score": 0.87,
  "reasoning": "Internal transfer faster + cheaper than alternate supplier..."
}
  ↓
Dashboard displays to Supply Chain Head
  ↓
Supply Chain Head clicks [APPROVE]
  ↓
System executes (transfers inventory, cancels POs, etc.)
  ↓
NOT: LLM directly modifies S/4HANA
```

**Effect**: Human in the loop, audit trail, compliance ready.

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   INCIDENT DETECTION                            │
│           (Port congestion alert, SLA risk, etc.)               │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   SCRATCHPAD INITIALIZATION                     │
│    Load current shipment data into incident context             │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              QUERY VECTOR STORE (Long-term Memory)              │
│  "Find similar past incidents" → Returns embeddings + metadata  │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              LLM DECISION ENGINE (Tool-Bounded)                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tool Call 1: get_shipment_status()  [Budget: 1/5]      │   │
│  │ Tool Call 2: find_alt_suppliers()   [Budget: 2/5]      │   │
│  │ Tool Call 3: calc_sla_penalty()     [Budget: 3/5]      │   │
│  │ Tool Call 4: get_internal_stock()   [Budget: 4/5]      │   │
│  │                                                         │   │
│  │ Generate recommendation + confidence_score              │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SAFETY GATES (Serial)                        │
│  1. Schema Validation → Valid? Yes ✓                            │
│  2. Confidence Threshold → 0.87 > 0.75? Yes ✓                  │
│  3. Audit Logging → Recorded ✓                                 │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              HUMAN APPROVAL DASHBOARD (v1 Propose-Only)         │
│  Display recommendation + reasoning + past similar cases        │
│  Human clicks [APPROVE] or [REJECT & RETHINK]                 │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   EXECUTION (S/4HANA Updates)                   │
│  - Update inventory transfers                                   │
│  - Cancel/modify POs                                            │
│  - Send notifications                                           │
│  - Log all changes                                              │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│         STORE RESOLVED INCIDENT (Update Vector Store)           │
│  - incident_id, outcome, cost_savings                           │
│  - Generate embedding from incident details                     │
│  - Index for future queries                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling

### Budget Exceeded
```
Tool calls used: 5/5
LLM asks to call 6th tool
  ↓
BudgetLimiter throws exception
  ↓
Fallback: Route to human with current data
  ↓
"System ran out of data-gathering budget. Human review required."
```

### Invalid Recommendation
```
LLM output: {"recommended_option": "Option 5", ...}  ← Invalid enum
  ↓
SchemaValidator throws ValidationError
  ↓
Log error, request retry
  ↓
If retry fails: Escalate to human
```

### Low Confidence
```
Recommendation: confidence_score = 0.62  ← Below threshold (0.75)
  ↓
ConfidenceGate flags as uncertain
  ↓
Route to Supply Chain Head for manual review
  ↓
Collect feedback: Did human approve? Why/why not?
  ↓
Use feedback to recalibrate threshold
```

## Performance Targets

| Metric | Target |
|--------|--------|
| End-to-end decision time | <5 min (vs 36 hr manual) |
| Tool execution latency | <500ms per call |
| Vector search latency | <100ms (similarity search) |
| Human review time | 2-5 min (glance + click) |
| System uptime | 99.9% |
| Audit log completeness | 100% |

## Deployment Considerations

- **Stateless LLM service** (can scale horizontally)
- **S/4HANA integration** (vector indexing on HANA DB)
- **Async execution** (incident resolution doesn't block port operations)
- **Monitoring**: Budget usage, confidence scores, human approval rates
- **Rollback capability**: Versioned tool definitions, easy to revert

---

Next: See [`adr/0001-llm-decision-system.md`](adr/0001-llm-decision-system.md) for decision context and alternatives.