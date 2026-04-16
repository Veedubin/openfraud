# OpenFraud

> A production-ready, multi-agent fraud detection framework combining forensic mathematics, machine learning, and graph analysis.

[![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/downloads/)
[![Tests](https://github.com/Veedubin/openfraud/actions/workflows/ci.yml/badge.svg)](https://github.com/Veedubin/openfraud/actions)
[![PyPI](https://img.shields.io/pypi/v/openfraud)](https://pypi.org/project/openfraud/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

---

## What is OpenFraud?

**OpenFraud** is an extensible fraud detection framework built for real-world investigations. Whether you're analyzing healthcare claims, financial transactions, e-commerce orders, or document leaks, OpenFraud gives you a unified toolkit to find anomalies that matter.

It combines three powerful detection layers:

- **Forensic Mathematics** — Hard rules that cannot be violated (Benford's Law, velocity checks, frozen ledger detection, peer deviation)
- **Machine Learning** — LightGBM models with calibration and cross-validation for pattern discovery
- **Graph Analysis** — Memgraph-powered network analytics (PageRank, communities, self-loops, spiderwebs, cliques)

### The Boomerang Protocol

OpenFraud is built around a core principle: **forensic hard flags cannot be overridden by ML predictions.**

If a machine learning model assigns low risk but the forensic accountant detects an impossible velocity violation, the entity is **flagged as high risk anyway**. The ML output is "boomeranged" back for reweighting. This ensures mathematical truth always wins over pattern probability.

---

## Powered By

OpenFraud leverages two key open-source projects for AI-assisted orchestration:

- **[`boomerang-opencode`](https://github.com/Veedubin/boomerang-opencode)** — The Boomerang Protocol engine. Provides multi-agent task decomposition, consensus, and the hard-flag validation layer that makes OpenFraud reliable.
- **[`super-memory`](https://github.com/Veedubin/super-memory)** — Long-term semantic memory for investigations. Every dataset, finding, and pattern can be recalled across sessions.

> **Note:** To use the full multi-agent OpenCode integration, install `boomerang-opencode` separately and register both plugins in your `.opencode/opencode.json`. See [Configuration](#configuration) below.

---

## Installation

```bash
# Using pip
pip install openfraud

# Using uv (recommended)
uv pip install openfraud

# With all optional dependencies (dev + viz)
pip install "openfraud[all]"
```

---

## Quick Start

### 1. Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- **Memgraph** (graph database) on port 7687
- **Memgraph Lab** (visualization UI) on port 3000
- **SearXNG** (privacy search) on port 8080
- **Redis** (cache) internally

### 2. Run Forensic Analysis

```python
import numpy as np
from openfraud.core import calculate_benford_ssd, calculate_z_score

# Generate or load transaction amounts
amounts = np.random.lognormal(3.0, 1.5, 5000)

# Benford's Law — detect manipulated data
ssd = calculate_benford_ssd(amounts)
print(f"Benford SSD: {ssd:.4f}")
if ssd > 0.1:
    print("Possible data manipulation detected!")

# Peer deviation
z = calculate_z_score(value=150.0, population_mean=50.0, population_std=20.0)
print(f"Z-score: {z:.2f}")
```

### 3. Train a Fraud Model

```python
import pandas as pd
from openfraud.models import train_fraud_model

df = pd.read_parquet("transactions.parquet")

model, metrics = train_fraud_model(
    df=df,
    feature_cols=["amount", "velocity_24h", "peer_z_score"],
    target_col="is_fraud",
    entity_id_col="user_id",
)

print(f"AUPRC: {metrics['auprc']:.4f}")
```

### 4. Run Graph Analysis

```python
from openfraud.graph import calculate_pagerank, find_self_loops
from memgraph_toolbox.api.memgraph import Memgraph

db = Memgraph(url="bolt://localhost:7687")

# Find influential nodes
pagerank = calculate_pagerank(db)
print(pagerank.head())

# Find suspicious self-loops
self_loops = find_self_loops(db)
print(f"Self-loops found: {len(self_loops)}")
```

### 5. Launch the TUI

```bash
openfraud
```

An interactive terminal UI for exploring graph data, risk-ranked entities, and fraud patterns.

---

## OpenCode Plugin Tools

OpenFraud ships with a native OpenCode plugin exposing 6 investigation tools:

| Tool | Description |
|------|-------------|
| `openfraud_forensics` | Run forensic analysis (Benford, Z-score, velocity, frozen ledger) |
| `openfraud_ml_train` | Train and evaluate LightGBM fraud models |
| `openfraud_graph_analysis` | Execute Memgraph graph queries |
| `openfraud_status` | Show framework component status |
| `openfraud_tui` | Launch the interactive TUI app |
| `openfraud_investigate` | Run full multi-agent investigation workflow |

### Agent Persona

The `openfraud` agent persona (`.opencode/agents/openfraud.md`) is a plugin-enabled orchestrator that:
- Queries `super-memory` for investigation context
- Uses `sequential-thinking` for structured reasoning
- Delegates coding tasks via the Boomerang Protocol
- Invokes all 6 OpenFraud tools directly

### Example Usage

```
> openfraud
Run a full forensic analysis on sample_data/transactions.parquet
with amount_column='claim_amount' and entity_column='provider_id'
```

---

## Configuration

To register the OpenFraud plugin in OpenCode, add it to your `.opencode/opencode.json`:

```json
{
  "mcp": {
    "sequential-thinking": { "enabled": true },
    "super-memory": { "enabled": true },
    "duckdb": { "enabled": true }
  },
  "plugin": [
    "file:///absolute/path/to/boomerang-opencode/dist",
    "file:///absolute/path/to/openfraud/.opencode/plugins/openfraud/dist"
  ]
}
```

> **Important:** `boomerang-opencode` must be installed separately. It is the orchestration engine that enables the Boomerang Protocol.

See `.opencode/opencode.json` in this repository for a complete example configuration.

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

### Key Design Principles

1. **Fail fast** — Clear errors, validated inputs, no silent failures
2. **Absolute imports** — Clean module boundaries
3. **Strict typing** — `mypy` enforced across the codebase
4. **Parquet-first** — Optimized for large datasets with chunked reading
5. **No secrets** — Credentials are never committed

---

## Documentation

- [`docs/TUI_SUMMARY.md`](docs/TUI_SUMMARY.md) — TUI widgets and features
- [`docs/TUI_INTEGRATION.md`](docs/TUI_INTEGRATION.md) — Integrating OpenFraud TUI into other apps
- [`docs/UNIVERSAL_INVESTIGATION_WORKBENCH.md`](docs/UNIVERSAL_INVESTIGATION_WORKBENCH.md) — Vision for domain-agnostic investigations
- [`templates/CUSTOMIZATION_PROMPT.md`](templates/CUSTOMIZATION_PROMPT.md) — Template for adapting OpenFraud to your domain

---

## Project Structure

```
openfraud/
├── openfraud/              # Main Python package
│   ├── core/              # Forensic mathematics
│   ├── models/            # LightGBM ML pipeline
│   ├── graph/             # Memgraph network analysis
│   ├── utils/             # Data utilities
│   ├── cli/               # CLI wrappers
│   └── tui/               # Textual TUI
├── tests/                 # Test suite
├── templates/             # Sample data + customization prompt
├── docs/                  # Documentation
├── .opencode/             # OpenCode plugin + agent persona
│   ├── plugins/openfraud/
│   ├── agents/openfraud.md
│   └── opencode.json
├── docker-compose.yml     # Infrastructure services
├── pyproject.toml         # Package configuration
└── README.md             # This file
```

---

## Development

```bash
# Clone
git clone https://github.com/Veedubin/openfraud.git
cd openfraud

# Install in dev mode
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check .

# Type check
mypy openfraud/
```

---

## Contributing

We welcome contributions! Areas where help is especially appreciated:

- Additional forensic algorithms
- New graph analysis patterns
- Domain-specific examples (finance, healthcare, e-commerce, threat hunting)
- Documentation improvements
- Bug fixes and tests

Please open an issue or pull request on [GitHub](https://github.com/Veedubin/openfraud/issues).

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Originally developed for large-scale fraud detection investigations
- Built with [LightGBM](https://lightgbm.readthedocs.io/), [Memgraph](https://memgraph.com/), [Textual](https://textual.textualize.io/), and [OpenCode](https://opencode.ai/)
- Orchestrated by [`boomerang-opencode`](https://github.com/Veedubin/boomerang-opencode)
- Powered by [`super-memory`](https://github.com/Veedubin/super-memory) for long-term investigation context
