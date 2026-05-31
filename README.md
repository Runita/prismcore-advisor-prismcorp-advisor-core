# PrismCorp Advisor Core

LLM-driven supply chain decision system with human oversight, tool-bounded execution, and continuous learning from historical incidents.

## Problem

Supply chain bottlenecks (e.g., port congestion) require fast, data-driven decisions. Current manual review is slow; pure automation is risky. Time-sensitive SLAs ($45k penalties) demand intelligent triage.

## Solution Architecture

### Three Core Components

#### 1. Tool-Bounded LLM
- LLM picks from typed catalog: `get_shipment_status`, `find_alt_suppliers`, `calc_sla_penalty`
- No SQL generation, no arbitrary API calls
- Each tool is pre-vetted, secure, auditable

#### 2. Dual Memory System
- **Short-term**: Incident scratchpad (working memory for current decision)
- **Long-term**: Vector store in S/4HANA or BDC (learn from historical incidents)
- Learning without fine-tuning: LLM queries past cases, applies patterns

#### 3. Safety Rails
| Component | Purpose |
|-----------|----------|
| Tool-call budget (e.g., ≤5 calls) | Prevents loops, controls cost |
| Schema-validated outputs | Structured decisions, no free-form text |
| Confidence threshold (e.g., >0.75) | Uncertain cases → human review |
| Propose-only in v1 | Human approves before execution |

## Workflow

```
Incident detected (e.g., $45k SLA penalty risk)
  ↓
Scratchpad: Gather current shipment data (Tool-call budget: 4/5)
  ↓
Query vector store: "Find similar port congestion cases"
  ↓
LLM generates recommendation + confidence score
  ↓
Confidence > 0.75? → Auto-route to human dashboard
                  ← Auto-escalate to Supply Chain Head
  ↓
Human reviews reasoning + historical context
  ↓
Human clicks [APPROVE] → System executes (transfers, POs, etc.)
  ↓
Resolved incident stored in vector store (feeds future decisions)
```

## Data Flow: Vector Store

**Option A: S/4HANA Native** (Recommended for <100k incidents)
- Vector column in resolved_incidents table
- Built-in SAP HANA indexing
- Integrated with supply chain data

**Option B: Hybrid** (For scale >500k incidents)
- S/4HANA: Structured incident metadata
- Dedicated Vector DB (Pinecone/Weaviate): Embeddings + similarity search
- Nightly sync

## Key Benefits

| Benefit | Why It Matters |
|---------|---|
| **Speed** | Auto-decide routine cases in seconds vs. hours |
| **Safety** | Human backstop for uncertain scenarios |
| **Learning** | System improves as it resolves more incidents |
| **Compliance** | Audit trail: every decision is human-approved |
| **Cost** | Tool-call budget prevents runaway API spend |

## Repository Structure

```
prismcorp-advisor-core/
├── README.md (this file)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── adr/
│   │   └── 0001-llm-decision-system.md
│   ├── tool-catalog.md
│   ├── vector-store-design.md
│   └── safety-rails.md
├── src/
│   ├── tools/
│   │   ├── shipment_status.py
│   │   ├── alt_suppliers.py
│   │   └── sla_penalty.py
│   ├── llm_orchestrator/
│   │   ├── decision_engine.py
│   │   └── confidence_scorer.py
│   └── safety_gates/
│       ├── budget_limiter.py
│       ├── schema_validator.py
│       └── threshold_gate.py
├── tests/
│   ├── unit/
│   └── integration/
├── deployment/
│   ├── docker-compose.yml
│   ├── s4hana-schema.sql
│   └── monitoring.yaml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
└── .gitignore
```

## Implementation Roadmap

**v1 (MVP)**: Propose-only + manual approval (build trust, gather data)  
**v2**: Auto-execute low-risk decisions (confidence >0.90)  
**v3**: Multi-incident orchestration (coordinate across suppliers/ports)  

## Success Metrics

- Incident resolution time: 36 hrs → 2 hrs
- SLA penalty avoidance: $45k → $0
- Human approval rate: Track % escalations (target: <15%)
- Vector store accuracy: % recommendations match human decisions (target: >90%)

## Getting Started

1. Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for detailed design
2. Review [`docs/adr/0001-llm-decision-system.md`](docs/adr/0001-llm-decision-system.md) for decision context
3. Check [`src/`](src/) for implementation templates
4. Deploy with [`deployment/docker-compose.yml`](deployment/docker-compose.yml)

## Contributing

- Create feature branches from `main`
- Follow tool-call budget guidelines in code reviews
- Add tests for new tools/safety gates
- Update ADRs for architectural decisions

## License

MIT

---

**Owner**: Supply Chain Head | **Status**: In Development | **Last Updated**: 2026-05-31