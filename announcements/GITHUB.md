# 🎉 PyCodeKG v0.5.2 — Public Release

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
✅ **Interactive visualizers** — Streamlit web app + 3D PyVista graph
✅ **One-line installer** — Automated setup for Claude Code, GitHub Copilot, Cline, Continue
✅ **Elastic License 2.0** — Free to use, modify, distribute; no hosted service reselling

---

## Quick Start

### Fastest Way (One-Liner)

Run this from inside your Python repository:

```bash
curl -fsSL https://raw.githubusercontent.com/Flux-Frontiers/pycode_kg/main/scripts/install-skill.sh | bash
```

The installer:
1. Installs the `pycode-kg` package
2. Builds the SQLite knowledge graph (`.pycodekg/graph.sqlite`)
3. Builds the LanceDB semantic index
4. Configures MCP for your IDE (Claude Code, GitHub Copilot, Cline, Continue)
5. Sets up CLI commands and skill files

After setup, reload VS Code (`Cmd+Shift+P` → `Developer: Reload Window`) to activate.

### Manual Installation

```bash
pip install 'pycode-kg @ git+https://github.com/Flux-Frontiers/pycode_kg.git'
# or in Poetry:
poetry add 'pycode-kg @ git+https://github.com/Flux-Frontiers/pycode_kg.git'
```

Build the graph:

```bash
# Full pipeline in one step
pycodekg build --repo /path/to/repo

# Or step by step
pycodekg-build-sqlite --repo /path/to/repo
pycodekg-build-lancedb --repo /path/to/repo
```

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

# 3D graph visualizer
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
