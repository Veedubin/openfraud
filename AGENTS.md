# OpenFraud - Agent Persona

**Role**: Multi-agent fraud detection framework combining forensic math, ML, and graph analysis  
**Scope**: `/home/jcharles/Projects/python/openfraud-release`  
**Stack**: Python 3.10+, `uv`, `pytest`, `ruff`, `mypy`, Docker Compose, Memgraph, LightGBM

---

## Overview

OpenFraud is a production-ready fraud detection framework. It uses a **multi-agent architecture** with a **Boomerang Protocol**: forensic hard flags cannot be overridden by ML predictions. The framework includes a native OpenCode plugin (`.opencode/plugins/openfraud/`) that exposes 6 tools for AI-assisted investigations, plus a dedicated `openfraud` agent persona.

---

## Commands

| Command | Purpose |
|---------|---------|
| `uv sync` | Install dependencies |
| `docker-compose up -d` | Start Memgraph, SearXNG, Redis |
| `pytest tests/ -v` | Run tests |
| `ruff check .` | Lint |
| `mypy openfraud/` | Type check |
| `python -m openfraud.cli.status` | Check framework status |
| `python -m openfraud.cli.forensics --data-path PATH --amount-column COL --analysis-type all` | Run forensic CLI |
| `python -m openfraud.cli.ml --data-path PATH --target-col COL` | Train fraud model |
| `python -m openfraud.cli.graph` | Run graph analysis |
| `python -m openfraud.tui.app` | Launch TUI |

---

## Entrypoints

| Path | Description |
|------|-------------|
| `openfraud/core/forensics.py` | Benford's Law, Z-scores, velocity, frozen ledger |
| `openfraud/models/model_stack.py` | LightGBM training, calibration, cross-validation |
| `openfraud/graph/network_analysis.py` | Memgraph analytics (PageRank, communities, self-loops) |
| `openfraud/tui/app.py` | Textual TUI for interactive exploration |
| `openfraud/cli/forensics.py` | CLI wrapper for forensic analysis |
| `openfraud/cli/ml.py` | CLI wrapper for model training |
| `openfraud/cli/graph.py` | CLI wrapper for graph queries |
| `openfraud/cli/status.py` | CLI wrapper for status checks |
| `.opencode/plugins/openfraud/dist` | OpenCode plugin (6 tools) |
| `.opencode/agents/openfraud.md` | OpenFraud orchestrator agent persona |
| `.opencode/opencode.json` | OpenCode configuration with MCP servers and plugin registry |

---

## Style

- **Tooling**: `uv` for deps, `ruff` for lint/format, `mypy` with strict typing.
- **Imports**: Standard lib → third-party → local. Use absolute imports.
- **Types**: All functions typed; `pandas` and `numpy` inputs validated.
- **Data**: Prefer Parquet/CSV. Large datasets use chunked reading.
- **Errors**: Fail fast with clear messages. CLI wrappers output JSON.
- **No secrets**: Never commit credentials or env files.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LEAD ORCHESTRATOR                        │
│              (Task Decomposition & Consensus)               │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│   Forensic   │ │    ML    │ │    Graph     │
│  Accountant  │ │ Architect│ │  Architect   │
│  (Hard Rules)│ │(Patterns)│ │ (Network)    │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │              │
       └──────────────┼──────────────┘
                      ↓
            ┌─────────────────┐
            │  Boomerang      │
            │  Validation     │
            │ (Hard flags     │
            │  cannot be      │
            │  overridden)    │
            └────────┬────────┘
                     ↓
            ┌─────────────────┐
            │   Investigator  │
            │  (Synthesis &   │
            │    Reporting)   │
            └─────────────────┘
```

### OpenCode Plugin

Registered in `.opencode/opencode.json`:
- `openfraud_forensics` — Run forensic analysis on datasets
- `openfraud_ml_train` — Train LightGBM fraud models
- `openfraud_graph_analysis` — Run Memgraph graph queries
- `openfraud_status` — Show framework status
- `openfraud_tui` — Launch the TUI app
- `openfraud_investigate` — Full multi-agent investigation workflow

The `openfraud` agent persona (`.opencode/agents/openfraud.md`) has permission to use all OpenFraud tools and delegates coding tasks via the Boomerang Protocol.

---

## Review Notes

- **2025-04-16**: OpenCode plugin v1 created at `.opencode/plugins/openfraud/`. Python CLI wrappers added in `openfraud/cli/`. Agent persona `openfraud.md` active. Plugin registered in `opencode.json`.
- The Boomerang Protocol enforces that forensic hard flags always override ML predictions.
- Memgraph must be running for graph tools to work.
- TUI is built with [Textual](https://textual.textualize.io/).
