# SAP BTP APJ RIG — Case Study Pack

> Complete interview-ready package for the PrismCorp Data & AI Transformation case study.

## Contents

| File | When to use it |
|---|---|
| [`README.md`](./README.md) | **Master document.** Architecture, decision framework, Phase 0 deep-dive, POC, Q&A prep. Read this end-to-end. ~25 min. |
| [`slides.pptx`](./slides.pptx) | **The PowerPoint deck.** 24 slides, 16:9, SAP-blue branded. Open in PowerPoint / Keynote / Google Slides. *Edit freely.* |
| [`slides.md`](./slides.md) | **Editable slide source** (Marp markdown). Tweak text, regenerate the PPTX from this. |
| [`build_pptx.py`](./build_pptx.py) | **Builder script.** Regenerates `slides.pptx` from data. Run via the local `.venv`. |
| [`one-pager.md`](./one-pager.md) | **Leave-behind.** Print/PDF for the panel. Captures everything on a single page. |
| [`talk-track.md`](./talk-track.md) | **Live script.** Time-boxed talking points, anchor lines, anti-patterns. Use during the interview itself. |
| [`diagrams/`](./diagrams/) | **Mermaid sources** for every architecture, sequence, and Gantt diagram in the README. Edit / export to PNG/SVG. |

## Regenerating the PowerPoint

The Python builder uses `python-pptx`. A local venv lives at the repo root.

```bash
# from the repo root (design-patterns/)
.venv/bin/python sap-btp-case-study/build_pptx.py
# → writes sap-btp-case-study/slides.pptx
```

If the venv doesn't exist:

```bash
python3 -m venv .venv
.venv/bin/pip install python-pptx
```

## Slide deck contents — 24 slides

1. Title  ·  2. Agenda  ·  3. The Business Problem  ·  4. The Paradox  ·  5. Leadership's Two Asks
6. Decision Framework (section)  ·  7. The Rubric  ·  8. Mapping Pains → Verdict
9. Target Architecture (section)  ·  10. 4-Layer Architecture  ·  11. Agent Topology  ·  12. Agent Design Choices
13. Phased Rollout  ·  14. Phase 0 (section)  ·  15. Goal & Scope  ·  16. Phase 0 Architecture
17. Data Products  ·  18. 6-Week Plan  ·  19. Acceptance Gates  ·  20. Phase 1 POC Scope & Scenario
21. Demo Flow  ·  22. Example Agent Output  ·  23. Metrics · Risks · Governance  ·  24. Closing Line

## Pre-interview workflow

1. **Day −2:** Read `README.md` cover-to-cover. Internalise the rubric in §3 and the closer lines in §13.
2. **Day −1:** Walk through `talk-track.md`. Time yourself — target 25 min for the walk.
3. **Day −1:** Render diagrams from `diagrams/` if you want PNG exports for slides.
4. **Day 0:** Carry the printed `one-pager.md` as a leave-behind.

## The four anchor points (memorise)

If pushed off-script, return to one of these:

1. **The hybrid framing** — workflow for plumbing, agentic for decisions.
2. **Phase 0 acceptance criteria** — five numeric gates.
3. **"Agents propose; system-of-record disposes."** — the safety principle.
4. **Per-entity opt-in** — the EA-board defuser.

## Source case study

Original brief: SAP BTP RIG — Case Study (PrismCorp), APJ Regional Implementation Group.
