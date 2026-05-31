# Talk Track — Live Interview Walkthrough

> A linear, time-boxed script. Stays on rails even under pressure.
> Total time: **~25 min walk + 15 min Q&A**.

---

## 0:00 — Opening (60 sec)

> *"Before I jump into architecture, let me frame the problem the way I read it, because the framing drives every choice that follows."*

State the problem in 3 lines:

- PrismCorp has the symptoms of an AI problem (SLA breaches, manual coordination).
- But the actual constraint is **decision latency** caused by **data fragmentation across 5 ERPs**.
- And — critically — **the platforms to fix this are already owned and contracted**: SAP BTP, BDC, Integration Suite. They're just not active.

> *"So the question is not 'should we buy something'. It's 'what should we activate, in what order, and where does AI genuinely earn its place'."*

---

## 1:00 — The Agentic AI vs Workflow Decision (3 min)

**Open with the rubric**, not the answer. (Refer to README §3.)

> *"I use five dimensions when deciding between workflow and agent — decision space, input variability, reasoning depth, tool selection, and explainability."*

Walk down the table. Then map PrismCorp's three pain points:

1. *No real-time data* → **integration**, not AI.
2. *Manual coordination* → **hybrid**.
3. *Surfacing ranked alternatives* → **agentic**.

**Land:**

> *"Hybrid. Deterministic plumbing for the data layer; agentic AI for the decision layer. Using agents for plumbing is over-engineering. Using workflows for diagnosis is under-delivering."*

⚠️ **Watch for interruption here** — interviewers love to push back. Likely:
- *"Why not all workflow?"* → variability of root causes, no fixed playbook.
- *"Why not all agentic?"* → cost, audit, governance, EA buy-in.

---

## 4:00 — Target Architecture (5 min)

**Whiteboard the 4-layer diagram.** Draw it in this order:

1. Sources (bottom)
2. Integration Suite (layer 2)
3. BDC (layer 1, but draw second — it's the consumer)
4. Agents (layer 3)
5. UI (layer 4, last)

While drawing, narrate three principles:

1. **Separation of planes** — data ≠ integration ≠ reasoning ≠ experience.
2. **Multi-agent, not monolithic** — narrow tool catalogs per agent.
3. **Agents propose; system-of-record disposes** — execution goes back through governed APIs.

> *"That last line is the single most important sentence in this design. It's what makes 5 EA boards comfortable."*

---

## 9:00 — Agent Topology (4 min)

Sketch the orchestrator + 5 sub-agents.

Call out the tools-not-SQL choice:

> *"The LLM never writes SQL. It picks tools from a typed catalog. `get_shipment_status`, `find_alt_suppliers`, `calc_sla_penalty`. That bounds what the model can do."*

Call out the memory model:

> *"Short-term scratchpad per incident. Long-term vector store of resolved incidents in BDC. That gives us learning without fine-tuning."*

Call out the guardrails:

- Tool-call budget
- Schema-validated outputs
- Confidence threshold → human fallback
- Propose-only in v1

---

## 13:00 — Phased Plan (1 min)

Show the 4-phase Gantt. Don't dwell.

> *"Phase 0 is the foundation. Phase 1 is the demo I'd take to the EA boards. Phase 2 scales horizontally. Phase 3 is selective autonomy."*

Pivot to Phase 0 — *this is where most interviewers will live*.

---

## 14:00 — Phase 0 Deep-Dive (6 min) ⭐ centerpiece

**Open with the framing line:**

> *"Phase 0 has no LLM in scope. If we can't trust the data, agents will hallucinate plausibly."*

Then the four moves:

### Move 1: Scope (1 min)
> *"One entity — APAC, worst SLA. One process — delivery order fulfilment. Read-only. Two non-SAP systems. One dashboard as the acceptance demo."*

### Move 2: Architecture (2 min)
Whiteboard the Phase 0 diagram. Three ingestion patterns — CDC, event, polled. *Explicitly say why three:*

> *"You can't pretend a real landscape is uniform. S/4 wants CDC; logistics wants events; WMS wants polling. The integration layer has to handle all three from day one."*

### Move 3: Deliverables (2 min)
The data products table is the moment to *show your work*. Each product has schema + owner + SLA + lineage.

> *"That last word — lineage — is what unblocks the EA boards. They need to see source-to-consumer for every byte."*

### Move 4: Acceptance criteria (1 min)
> *"Five numeric gates. ≤5 min latency p95, ≥99.9% replication completeness, ≥99% DQ, ≥99.5% uptime, ≤3s dashboard. Miss any, no go for Phase 1."*

> *"That's not bureaucracy — that's the contract that earns Phase 1."*

---

## 20:00 — Phase 1 POC Demo (3 min)

**Tell the story, don't just show the diagram.**

> *"Picture this. Tuesday morning. A high-priority shipment of 5,000 units to a Tier-1 customer is stuck at Singapore. ETA slipped 6 days. SLA breach in 48 hours."*
>
> *"The Supply Chain Head opens Joule. Types: 'What are my options for ORDER-7842?' Ninety seconds later: three options, ranked, with a paragraph of rationale each. She approves Option A. Integration Suite reroutes. Logged. Done."*

Then walk the sequence diagram quickly.

Then call out the three POC discipline rules:

1. Single entity, single decision class.
2. Mocked data for the other 4 entities — but real data for APAC.
3. Propose-only — no autonomy.

> *"This is a 6–8 week POC. Not a platform launch."*

---

## 23:00 — Risks + Governance (1 min)

Two sentences each. Don't recite — pick the top 3 of each:

**Risks**
- Hallucinated alternatives → tool catalog.
- Semantic drift across ERPs → data contract by Week 3.
- Over-automation → human-in-loop is a feature.

**Governance**
- No new vendor.
- Read-only by design.
- Per-entity opt-in (the killer point).

---

## 24:00 — Closer (60 sec)

Pick one of three closers based on the panel:

- **For a technical panel** → *"Agents propose; system-of-record disposes. That single rule keeps this architecture safe enough for 5 EA boards and useful enough for the Supply Chain Head."*

- **For a business panel** → *"PrismCorp doesn't have a data problem or an AI problem. It has a decision-latency problem. The data layer is integration; the decision layer is agentic AI. Use both — in that order."*

- **For an SAP-savvy panel** → *"Phase 0 activates assets PrismCorp has already paid for. The platform is bought; the project is to make it real."*

---

## 25:00 — Q&A (15 min)

**Anchor points** — if pushed, return to one of these:

1. **The hybrid framing** (workflow + agentic, in deliberate places).
2. **Phase 0 acceptance criteria** (the 5 numeric gates).
3. **"Agents propose; SoR disposes"** (the safety principle).
4. **Per-entity opt-in** (the EA-board defuser).

**If asked to whiteboard a sub-system** — pick one of these you can draw cleanly:
- The Phase 0 Integration Suite topology.
- The agent tool-catalog for the Alt-Generator agent.
- The sequence diagram for ORDER-7842.
- The data product contract template (schema + SLA + owner + lineage).

---

## Anti-patterns to avoid in delivery

| Don't | Do |
|---|---|
| Start with the agent | Start with the problem framing |
| Pitch BDC and Datasphere as the same thing | Call out: BDC is the semantic layer, Datasphere is storage |
| Promise autonomy in v1 | Sell propose-only |
| Skip the EA-board angle | Lead with per-entity opt-in |
| Read the README aloud | Walk the whiteboard; the README is the leave-behind |

---

## One-glance pre-interview checklist

- [ ] I can whiteboard the 4-layer architecture in < 2 min
- [ ] I can name the 5 sub-agents and their tools
- [ ] I can recite the Phase 0 acceptance criteria
- [ ] I can name the 3 ingestion patterns (CDC / event / polled)
- [ ] I can defend "agentic vs workflow" with the rubric
- [ ] I have all 3 closer lines memorized
- [ ] I have answers ready for the 8 Q&A questions in README §12

---

*Use the README as your leave-behind. Use this talk-track as your live script.*
