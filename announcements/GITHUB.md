# 🎉 PyCodeKG v0.19.0 — Public Release

We're thrilled to announce **PyCodeKG** is now publicly available.

PyCodeKG is a **deterministic knowledge graph for Python codebases** that brings structural precision and semantic intelligence together. It powers source-grounded code search, precise agent reasoning, and interactive codebase exploration.

---

## What is PyCodeKG?

PyCodeKG constructs an auditable knowledge graph from Python source code using **static analysis**:

1. **Parse** your codebase with three AST passes (structure, call graph, data-flow)
2. **Store** the graph in SQLite (nodes + edges with provenance)
3. **Index** semantically with LanceDB for fast NL search
4. **Query** using a hybrid model: embeddings seed retrieval, graph traversal ranks and bounds results
5. **Extract** source-grounded snippets with exact line numbers
6. **Integrate** via MCP server (Claude Code, GitHub Copilot, Cursor, Continue) or CLI/web UI

### Key Principles

- **Structure is authoritative.** The AST-derived graph is source of truth.
- **Semantics accelerate, never decide.** Embeddings are entry points, not arbiters.
- **Everything is traceable.** Every node and edge maps to a file and line number.
- **Determinism over heuristics.** Identical input yields identical output, always.
- **Composable artifacts.** SQLite for structure, LanceDB for vectors, Markdown/JSON for consumption.

---

## Core Features

✅ **AST-based knowledge graph** — Three-pass static analysis (structure, calls, data-flow)
✅ **Deterministic output** — No randomness, no heuristics
✅ **Symbol resolution** — Cross-module call sites resolved via import aliases
✅ **Hybrid query engine** — Semantic seeding + structural graph expansion
✅ **Source-grounded snippets** — Definition and call-site code with line numbers
✅ **Precise fan-in lookup** — Find all callers of a function across modules
✅ **MCP server** — Five tools for AI agent integration
✅ **Streamlit visualizer** — interactive web app for browsing the graph
🚧 **3D PyVista graph** (`viz3d`) — actively in development; functional but still rough around the edges
✅ **One-line installer** — Automated setup for Claude Code, GitHub Copilot, Cline, Continue
✅ **Elastic License 2.0** — Free to use, modify, distribute; no hosted service reselling

---

## Quick Start

```bash
pip install 'pycode-kg[viz,viz3d]'   # base + Streamlit + 3D viewer

cd /path/to/your/repo
pycodekg init --repo .               # download model, build graph, install hooks, snapshot
pycodekg analyze .                   # the architectural report
```

MCP-only (no visualizers):

```bash
pip install pycode-kg
pycodekg init --repo .
pycodekg mcp --repo .
```

Poetry:

```bash
poetry add 'pycode-kg[viz,viz3d]'
```

---

## The Fast Win: `pycodekg analyze`

This single command is the actual reason PyCodeKG exists. The author got tired of LLMs grepping through `src/` every time they asked for a codebase analysis — so a proper 15-phase structural pipeline was built instead. It runs in seconds and hands the LLM something it can actually reason about. It's been run against **numpy** and **matplotlib**; the reports live in `analysis/` if you want to see what real-world output looks like.

```bash
pycodekg init --repo .    # first time: downloads embedder, builds graph, installs hooks
pycodekg analyze .        # the full report
# optional: save JSON for CI/trend tracking
pycodekg analyze --json ~/.claude/pycodekg_analysis_latest.json
```

> **Note:** First run downloads the embedder model — be patient. Subsequent runs are fast.

### The 15-Phase Pipeline

| # | Phase | What it surfaces |
|---|-------|-----------------|
| 1 | Baseline metrics | Node/edge counts, graph shape |
| 2 | CodeRank (global PageRank) | Structurally most important symbols |
| 3 | Fan-in analysis | Heavily depended-on functions (breaking-change risk) |
| 4 | Fan-out analysis | Orchestrators and complexity hotspots |
| 5 | Dependency analysis | Orphaned / dead code candidates |
| 6 | Pattern detection | Anti-patterns and structural red flags |
| 7 | Module coupling | Tightly coupled pairs, import graph density |
| 8 | Critical paths | Longest call chains, bottlenecks |
| 9 | Public API identification | Exposed vs. internal surface |
| 10 | Docstring coverage | By module, class, function, method |
| 11 | Inheritance hierarchy | Depth, multiple inheritance, diamond patterns |
| 12 | Insight synthesis | Issues + strengths callouts |
| 13 | Snapshot history | Metric trends across releases |
| 14 | Structural centrality (SIR) | Bridge nodes, graph removal impact |
| 15 | Concern-based ranking | Nodes grouped by architectural concern |

Every finding maps to a file and line number. No hallucinated signatures. Drop the Markdown into your favorite LLM and say *"here's my codebase — what should I fix first?"*

---

## Usage Examples

### Query the Graph

```bash
pycodekg query "database connection setup"
# with options:
pycodekg query "database connection setup" --k 8 --hop 1
```

### Generate Code Context for LLMs

```bash
pycodekg pack "configuration loading" --out context_pack.md
```

### Explore Interactively

```bash
# Streamlit web app
pycodekg viz

# 3D graph visualizer (actively in development — functional but rough around the edges)
pycodekg viz3d --layout allium
```

### Analyze Codebase Architecture

```bash
pycodekg analyze .
```

### Start MCP Server

```bash
pycodekg mcp --repo .
```

Connect your IDE and use these tools:
- `query_codebase(q, ...)` — Hybrid search
- `pack_snippets(q, ...)` — Source-grounded context
- `get_node(node_id)` — Fetch by stable ID
- `callers(node_id)` — Find all callers (cross-module)
- `graph_stats()` — Node/edge counts

---

## Architecture

<img src="docs/pycode_kg_arch_square.png" alt="PyCodeKG Architecture" width="600"/>

**Build pipeline:**

```
Repository
  ↓
AST Parsing (3 passes: structure, calls, data-flow)
  ↓
SQLite Knowledge Graph (nodes + edges)
  ↓
Symbol Resolution (RESOLVES_TO edges for cross-module calls)
  ↓
LanceDB Semantic Index (embeddings)
  ↓
Hybrid Query (semantic seeding + structural expansion)
  ↓
Ranking + Deduplication + Snippet Extraction
  ↓
JSON / Markdown / Interactive UI / MCP
```

**Node kinds:** `module`, `class`, `function`, `method`, `symbol`

**Edge relations:** `CONTAINS`, `CALLS`, `IMPORTS`, `INHERITS`, `RESOLVES_TO`, `ATTR_ACCESS`, `READS`, `WRITES`

---

## Use Cases

**AI Agents:**
- Precise code context for LLM reasoning (Claude Code, GitHub Copilot, Cursor, Continue)
- Source-grounded retrieval with line numbers and full traceability

**Developers:**
- Interactive codebase exploration without grep
- Understand code flow and dependencies visually
- Search by intent, not syntax

**Teams:**
- Onboarding: Give engineers precise code context
- Code review: Understand impact of changes
- Documentation: Auto-generate from graph structure

**Enterprises:**
- Canonical store of code structure for compliance auditing
- Foundation for custom analysis and tooling
- Deterministic, auditable reasoning for sensitive codebases

---

## Comparisons

| Feature | PyCodeKG | GraphRAG | Amplify |
|---------|--------|----------|---------|
| **Foundation** | Deterministic AST | Probabilistic inference | Embeddings only |
| **Structure** | Graph with provenance | Implicit, learned | None |
| **Auditability** | Full (every answer traceable) | Limited (statistical) | Limited (vector distance) |
| **Line numbers** | Yes, always | No | No |
| **Cross-module calls** | Yes (symbol resolution) | Yes | Limited |
| **Performance** | O(k + h) graph traversal | LLM-based | Vector search |

---

## Documentation

- **[README](README.md)** — Overview, quick start, feature summary
- **[docs/Architecture.md](docs/Architecture.md)** — Deep dive into design, data model, pipeline
- **[docs/MCP.md](docs/MCP.md)** — MCP tool reference, integration guide, troubleshooting
- **[docs/CHEATSHEET.md](docs/CHEATSHEET.md)** — CLI quick reference
- **[CHANGELOG.md](CHANGELOG.md)** — Version history

---

## Repository

- **GitHub:** [github.com/Flux-Frontiers/pycode_kg](https://github.com/Flux-Frontiers/pycode_kg)
- **License:** [Elastic License 2.0](LICENSE) — Free to use, modify, distribute; no hosted service reselling
- **Author:** Eric G. Suchanek, PhD (Flux-Frontiers, Liberty TWP, OH)

---

## Contributing

Contributions welcome! Open issues for bugs, feature requests, or questions. See `DEVELOPING` section in README.

---

## Thanks

PyCodeKG builds on excellent open-source projects:
- **Python AST** — Standard library static analysis
- **SQLite** — Reliable, portable structured storage
- **LanceDB** — Fast vector indexing
- **Streamlit** — Interactive web UI
- **PyVista** — 3D graph visualization
- **MCP** — Model Context Protocol for agent integration
