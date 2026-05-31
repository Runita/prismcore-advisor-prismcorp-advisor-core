# ADR-0001: LLM-Driven Supply Chain Decision System

**Status**: Proposed  
**Date**: 2026-05-31  
**Deciders**: Supply Chain Head, Engineering Lead, Enterprise Architect  
**Affects**: Incident resolution SLA (36 hr window), cost optimization ($45k penalty risk)

## Context

### Problem
PrismCorp experiences supply chain bottlenecks (e.g., port congestion) that require fast, data-driven decisions within tight SLA windows. Current manual review process:
- Takes 8-12 hours for Supply Chain Head to review incident + options
- Results in missed resolution opportunities
- Exposes company to penalties ($45k+)
- Cannot scale to multiple concurrent incidents

### Constraints
- **Time**: 36-hour SLA window is hard deadline
- **Compliance**: All decisions must be auditable + human-approved (v1)
- **Safety**: Cannot execute automated trades without human oversight
- **Cost**: Tool calls + vector DB storage must be predictable + bounded

## Decision

Implement a **tool-bounded LLM orchestration system** with:

1. **Tool-call budget** (≤5 calls per incident)
   - Prevents infinite loops
   - Forces efficiency
   - Bounds cost

2. **Dual memory system**
   - Short-term: Incident scratchpad
   - Long-term: Vector store of resolved incidents (S/4HANA or hybrid)
   - Enables learning without fine-tuning

3. **Safety gates** (serial validation)
   - Schema validation (structured output only)
   - Confidence threshold (>0.75 for auto-route, <0.75 for escalation)
   - Propose-only in v1 (human approval before execution)

4. **S/4HANA native vector storage**
   - Vectors stored alongside incident metadata
   - Built-in HANA indexing for similarity search
   - Integrated with supply chain data

## Alternatives Considered

### Alternative 1: Pure ML Pipeline (No LLM)
- Train classifier on historical incidents → recommend decision
- **Pros**: Deterministic, fast, well-understood
- **Cons**: Brittle to new scenarios, requires labeled training data, no reasoning transparency
- **Decision**: Rejected—LLM reasoning helps with edge cases

### Alternative 2: Full Automation (No Human Gate)
- LLM makes decisions → system executes immediately
- **Pros**: Fastest, no human latency
- **Cons**: High compliance risk, SLA penalty if LLM fails, regulatory friction
- **Decision**: Rejected—propose-only model required for v1 trust-building

### Alternative 3: Manual Review Only (No LLM)
- Humans review all options → decide
- **Pros**: No AI risk, full human control
- **Cons**: Doesn't solve the 36-hour SLA window, doesn't scale, doesn't optimize costs
- **Decision**: Rejected—doesn't address business problem

### Alternative 4: Dedicated Vector DB (Pinecone/Weaviate)
- Separate vector DB service for embeddings
- **Pros**: Specialized indexing, sub-100ms search, scales to millions
- **Cons**: Additional service, sync complexity, licensing cost
- **Decision**: Deferred to v2—S/4HANA sufficient for initial <100k incidents

## Consequences

### Positive
- ✅ **Speed**: Incidents resolved in 2-5 hours (vs 8-12 hours manual)
- ✅ **Learning**: System improves as it resolves more incidents (vector store compound effect)
- ✅ **Safety**: Human backstop for edge cases (confidence threshold)
- ✅ **Compliance**: 100% audit trail (every decision human-approved in v1)
- ✅ **Cost optimization**: $13k savings vs alternate supplier orders (from dashboard mockup)
- ✅ **Bounded cost**: Tool-call budget prevents runaway API spend

### Negative
- ⚠️ **Initial complexity**: 3 layers of safety gates add engineering lift
- ⚠️ **S/4HANA dependency**: Requires HANA 2.0+ with vector extensions
- ⚠️ **Vector quality**: Garbage in → garbage out (incident summaries must be well-structured)
- ⚠️ **Human training**: Supply Chain Head must understand LLM confidence scores

### Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM hallucinates tool calls | Medium | High | Budget limiter + schema validation |
| Confidence threshold miscalibrated | Medium | Medium | A/B test thresholds, collect approval feedback |
| Vector embeddings don't capture nuance | Low | Medium | Use domain-specific embeddings (supply chain), fine-tune over time |
| S/4HANA vector indexing slow | Low | Medium | Scale to dedicated vector DB (v2) if needed |
| Human ignores LLM reasoning | Low | Low | Monitor approval rate, adjust confidence threshold |

## Implementation Plan

### Phase 1: Foundation (Weeks 1-2)
- [ ] Define tool catalog (`get_shipment_status`, `find_alt_suppliers`, etc.)
- [ ] Build budget limiter + schema validator
- [ ] Set up S/4HANA vector schema
- [ ] Implement confidence scorer (logistic regression on historical data)

### Phase 2: Integration (Weeks 3-4)
- [ ] LLM orchestrator (OpenAI / Claude, tool-calling API)
- [ ] Human approval dashboard (React UI)
- [ ] Audit logging (every decision + human approval timestamped)
- [ ] Vector store indexing (load historical incidents)

### Phase 3: Testing (Weeks 5-6)
- [ ] Unit tests (budget limiter, schema validation, confidence scorer)
- [ ] Integration tests (LLM + tools + gates + S/4HANA)
- [ ] UAT with Supply Chain Head (real incidents, feedback loop)
- [ ] Performance testing (latency, vector search speed)

### Phase 4: Deploy (Week 7+)
- [ ] v1 (propose-only, human approval required)
- [ ] Monitor: tool budget usage, confidence scores, human approval rate
- [ ] v2 (auto-execute low-confidence decisions if approval rate >95%)

## Success Criteria

| Metric | Target | Owner |
|--------|--------|-------|
| Decision time (end-to-end) | <5 min (vs 36 hr SLA window) | Eng Lead |
| SLA penalty avoidance | $45k → $0 | Supply Chain Head |
| Human approval rate | >90% (system is trustworthy) | Supply Chain Head |
| Vector search accuracy | % similar cases returned are truly similar (>85%) | Data Engineer |
| System uptime | 99.9% | DevOps |
| Tool-call budget efficiency | <4 calls per incident (avg) | Eng Lead |

## Open Questions

1. **Confidence threshold**: Start at 0.75—should we adjust based on cost impact?
2. **Vector similarity**: Use sentence-transformers (open) or OpenAI embeddings (proprietary)?
3. **Human feedback loop**: How do we collect + learn from human approval/rejection?
4. **v2 auto-execution**: What confidence threshold + approval rate triggers v2?

## Related

- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md)—Detailed design
- [`docs/tool-catalog.md`](../tool-catalog.md)—Tool specifications
- [`docs/vector-store-design.md`](../vector-store-design.md)—S/4HANA schema + queries

---

**Decision Date**: 2026-05-31  
**Last Updated**: 2026-05-31  
**Approved By**: [Pending stakeholder sign-off]