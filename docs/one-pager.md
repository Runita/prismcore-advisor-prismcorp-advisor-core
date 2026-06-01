# PrismCorp — Data & AI Transformation
### One-Page Executive Brief · SAP BTP APJ RIG

---

**Problem.** PrismCorp's Supply Chain unit suffers SLA-breaching order-fulfilment delays driven by three root causes: (1) **no real-time data** across 5 ERPs + non-SAP systems, (2) **manual cross-team coordination**, (3) **decision latency** — alternatives surface too late.

**Paradox.** SAP BTP, SAP Business Data Cloud, and SAP Integration Suite are already contracted but inactive. *The infrastructure to solve the problem exists; it is not connected.*

---

### Recommendation — Hybrid, not pure agentic

| Pain | Solution layer | Why |
|---|---|---|
| No real-time data | Deterministic — Integration Suite + BDC | Plumbing, not intelligence |
| Manual coordination | Hybrid | Known sub-steps via workflow; novel diagnosis via agent |
| Surfacing ranked alternatives | **Agentic AI** | Multi-criteria reasoning over heterogeneous signals |

> **Agents propose; system-of-record disposes.** Execution always flows back through governed integration APIs.

---

### Architecture (4 layers, all SAP-native)

```
Layer 4  •  Joule / SAP Build Apps             — UI + approvals
Layer 3  •  Generative AI Hub + AI Core        — orchestrator + 5 sub-agents
Layer 2  •  Integration Suite (iFlows + Event Mesh + APIM)
Layer 1  •  SAP Business Data Cloud (Datasphere + Data Products + Vector Store)
```

Zero net-new vendors. Every component pre-approved across the 5 EA boards.

---

### Phased plan

| Phase | Duration | Outcome |
|---|---|---|
| **0 — Foundation** | 6 weeks | BDC + IS active for 1 entity (APAC). 7 data products. SAC dashboard. Read-only. |
| **1 — POC** | 6–8 weeks | Single decision class ("shipment delayed — options?"). Propose-only. |
| **2 — Scale** | 16 weeks | Expand to 5 entities; learning loop from resolved cases. |
| **3 — Autonomy** | 24 weeks | Selective autonomy for low-risk decisions only. |

---

### Phase 0 acceptance gates *(no Phase 1 until all are green)*

- E2E latency (event → BDC) ≤ **5 min p95**
- Replication completeness ≥ **99.9%** / 7 days
- Data-quality pass rate ≥ **99%** per product
- Pipeline uptime ≥ **99.5%** / 30 days
- Dashboard response ≤ **3 sec p95**
- Audit-log coverage of reads **100%**

---

### POC success targets

| Metric | Baseline | Target |
|---|---|---|
| Time-to-recommendation | ~4 hours (manual) | **< 90 sec** |
| Recommendation acceptance | n/a | **≥ 70%** |
| Incidents resolved without escalation | ~40% | **≥ 65%** |
| Explainability | partial | **100% (agent trace logged)** |

---

### EA-board mitigations *(per-entity governance preserved)*

- No new vendor
- Read-only design
- Per-entity data ownership
- Reversible in hours
- **Per-entity opt-in** — other 4 entities choose to join based on APAC results

---

### Closing line

> *PrismCorp does not have a data problem or an AI problem. It has a **decision-latency problem**. The data layer is integration; the decision layer is agentic AI. Use both — in that order.*

---

*Full design pack: `README.md` · Live talk-track: `talk-track.md` · Diagrams: `diagrams/`*
