# Diagram Sources

Mermaid source files for every architectural diagram in the main `README.md`. Use these if you want to:

- Edit a diagram (then paste back into the README, or render to PNG/SVG)
- Export to PNG/SVG/PDF for slide decks
- Run diagram-as-code review independent of the prose

## File index

| File | Diagram | Used in README §  |
|---|---|---|
| `01-target-architecture.mmd` | Target 4-layer architecture | §4 Target Architecture |
| `02-agent-topology.mmd` | Orchestrator + sub-agents + HITL | §5 Agent Topology |
| `03-phase0-architecture.mmd` | Phase 0 BDC + IS topology | §7.3 Phase 0 Architecture |
| `04-incident-sequence.mmd` | End-to-end POC sequence (ORDER-7842) | §8.3 Demo flow |
| `05-phased-rollout.mmd` | 4-phase Gantt | §6 Phased Rollout |

## Render to PNG locally

```bash
# install once
npm install -g @mermaid-js/mermaid-cli

# render all
for f in *.mmd; do
  mmdc -i "$f" -o "${f%.mmd}.png" -b transparent -t default
done
```

## Render online

Paste any `.mmd` content into [mermaid.live](https://mermaid.live) to preview, edit, and export.
