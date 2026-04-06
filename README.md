
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: Elastic-2.0](https://img.shields.io/badge/License-Elastic%202.0-blue.svg)](https://www.elastic.co/licensing/elastic-license)
[![Version](https://img.shields.io/badge/version-0.11.0-blue.svg)](https://github.com/Flux-Frontiers/code_kg/releases)
[![CI](https://github.com/Flux-Frontiers/code_kg/actions/workflows/ci.yml/badge.svg)](https://github.com/Flux-Frontiers/code_kg/actions/workflows/ci.yml)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)

<p align="center">
  <img src="assets/logo-md-256x256.png" alt="CodeKG logo" width="256"/>
</p>

**CodeKG** — A Deterministic Knowledge Graph for Python Codebases
with Semantic Indexing and Source-Grounded Snippet Packing

*Author: Eric G. Suchanek, PhD*

*Flux-Frontiers, Liberty TWP, OH*

[Technical Paper (PDF)](article/code_kg.pdf)

---

## Overview

CodeKG constructs a **deterministic, explainable knowledge graph** from a Python codebase using static analysis. The graph captures structural relationships — definitions, calls, imports, and inheritance — directly from the Python AST, stores them in SQLite, and augments retrieval with vector embeddings via LanceDB.

Structure is treated as **ground truth**; semantic search is strictly an acceleration layer. The result is a searchable, auditable representation of a codebase that supports precise navigation, contextual snippet extraction, and downstream reasoning without hallucination — making it an ideal retrieval engine for LLMs and a practical foundation for **Knowledge-Graph RAG (KRAG)**, in contrast to embedding-only approaches such as Amplify and probabilistic graph methods such as Microsoft GraphRAG.

---

## Features

- **Static analysis pipeline** — Three-pass AST extraction: structure, call graph, data-flow
- **Deterministic knowledge graph** — SQLite-backed canonical store (nodes + edges with provenance)
- **Symbol resolution** — Post-build `RESOLVES_TO` edges bridge cross-module call sites via import aliases
- **Hybrid query model** — Semantic seeding (LanceDB embeddings) + structural expansion (graph traversal)
- **Source-grounded snippet packing** — Extract definition and call-site snippets with line numbers
- **Precise fan-in lookup** — Two-phase reverse traversal resolving cross-module caller chains
- **Composable outputs** — Markdown, JSON, and interactive visualization
- **MCP server** — Ten tools for AI agent integration (`graph_stats`, `query_codebase`, `pack_snippets`, `get_node`, `callers`, `explain`, `analyze_repo`, `snapshot_list`, `snapshot_show`, `snapshot_diff`)
- **Streamlit web app** — Interactive graph browser, hybrid query UI, snippet pack explorer
- **Zero-config MCP setup** — Single-line installer configures Claude Code, Kilo Code, GitHub Copilot, and Cline

## Contribution Checklist

When changing MCP tools in `src/code_kg/mcp_server.py` (signature, params, defaults, or behavior), update all three in the same commit:

- Module docstring `Tools` list at the top of `src/code_kg/mcp_server.py`
- `mcp = FastMCP(..., instructions=(...))` tool descriptions in `src/code_kg/mcp_server.py`
- The runtime tool implementation and `:param:` docstrings

---

## Quick Start

The fastest way to integrate CodeKG into any Python repository — run the one-line installer from within the repo you want to index:

```bash
curl -fsSL https://raw.githubusercontent.com/Flux-Frontiers/code_kg/main/scripts/install-skill.sh | bash
```

The installer sets up the full **AI integration layer** end-to-end:

1. Installs `SKILL.md` reference files for Claude Code, Kilo Code, and other agents
2. Installs Claude Code slash commands (`/codekg`, `/setup-mcp`) to `~/.claude/commands/`
3. Installs the `/codekg` slash command into the target repo's `.claude/commands/` for Cline
4. Installs the `code-kg` package if not already present — prefers the latest GitHub release wheel, falls back to GitHub source
5. Builds the SQLite knowledge graph (`.codekg/graph.sqlite`) and LanceDB semantic index
6. Writes MCP configuration for each provider:
   - `.mcp.json` — Claude Code and Kilo Code (per-repo)
   - `.vscode/mcp.json` — GitHub Copilot (per-repo)
   - `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` — Cline (global, keyed as `codekg-<repo-name>`)

By default all providers are configured. Pass `--providers` to target specific ones, or `--dry-run` to preview without making changes:

```bash
# All providers (default)
curl -fsSL .../install-skill.sh | bash -s -- --providers all

# Claude Code and GitHub Copilot only
curl -fsSL .../install-skill.sh | bash -s -- --providers claude,copilot

# Preview without making changes
curl -fsSL .../install-skill.sh | bash -s -- --dry-run
```

After the script completes, the `codekg` CLI commands are immediately available in your terminal. To activate the MCP servers in your AI coding agents, restart each one:

| Agent | How to restart |
|-------|---------------|
| **Claude Code** | `Cmd+Shift+P` → `Developer: Reload Window` |
| **Cline** | `Cmd+Shift+P` → `Developer: Reload Window` |
| **Kilo Code** | `Cmd+Shift+P` → `Developer: Reload Window` |
| **GitHub Copilot** | `Cmd+Shift+P` → `Developer: Reload Window` |
| **Claude Desktop** | Quit and relaunch the app |

---

## Usage Examples

### Build and query the knowledge graph

```bash
# Index a repository (SQLite + LanceDB in one step)
codekg build --repo /path/to/your/repo

# Natural-language query — returns ranked nodes
codekg query "authentication flow"

# Source-grounded snippet pack — paste straight into an LLM prompt
codekg pack "database connection setup" --format md --out context.md

# Find all callers of a function by node ID
codekg query "GraphStore.callers_of"   # find the node ID first
# then:
# codekg callers fn:store:GraphStore.callers_of

# Get a natural-language explanation of a code node by ID
codekg explain "fn:src/code_kg/store.py:GraphStore.expand"
```

### Analyze a codebase

```bash
# Run the full architectural analysis (Phase 1–9, including docstring coverage)
codekg analyze /path/to/your/repo

# Quiet mode for CI — no Rich table, exits 1 on issues
codekg analyze /path/to/your/repo --quiet
```

### Pre-download the embedding model (offline / CI)

```bash
# Cache BAAI/bge-small-en-v1.5 into .codekg/models/ before first use
codekg-download-model --repo .
```

### Use via MCP in Claude Code / Cline

Once the MCP server is running, your AI agent gets ten tools:

```
graph_stats()                         # node/edge counts by kind
query_codebase("authentication flow", min_score=0.2, max_per_module=3) # hybrid semantic + structural search with precision/diversity controls
pack_snippets("database layer", min_score=0.2, max_per_module=2)        # source-grounded snippets as Markdown
get_node("fn:store:GraphStore.write") # fetch a single node by ID
callers("fn:store:GraphStore.write")  # precise fan-in lookup
explain("fn:store:GraphStore.write")  # natural-language explanation of a node
analyze_repo()                        # full architectural analysis as Markdown
snapshot_list()                       # list saved snapshot keys and deltas
snapshot_show("latest")              # inspect the latest snapshot
snapshot_diff("<key_a>", "<key_b>")  # compare two snapshots by key
```

### Python API

```python
from code_kg import CodeKG

kg = CodeKG(repo_root="/path/to/repo")
stats = kg.build(wipe=True)

result = kg.query("database connection setup", k=8, hop=1)
for node in result.nodes:
    print(node["id"], node["name"])

pack = kg.pack("authentication flow")
pack.save("context.md")
```

---

## Installation

**Requirements:** Python ≥ 3.12, < 3.14

### Standalone (pip)

```bash
# Core install (SQLite + LanceDB + MCP server)
pip install 'code-kg @ git+https://github.com/Flux-Frontiers/code_kg.git'

# With Streamlit web visualizer (adds Streamlit, pyvis, plotly)
pip install 'code-kg[viz] @ git+https://github.com/Flux-Frontiers/code_kg.git'

# With 3D visualizer extras (adds PyVista, PyQt5, etc. — heavy dependencies)
pip install 'code-kg[viz3d] @ git+https://github.com/Flux-Frontiers/code_kg.git'

# With both visualizers
pip install 'code-kg[viz,viz3d] @ git+https://github.com/Flux-Frontiers/code_kg.git'
```

### Existing Poetry project

Add `code-kg` as a dependency from GitHub:

```bash
# Core (MCP server + graph engine, no visualizer)
poetry add 'code-kg @ git+https://github.com/Flux-Frontiers/code_kg.git'

# With Streamlit web visualizer (adds Streamlit, pyvis, plotly)
poetry add 'code-kg[viz] @ git+https://github.com/Flux-Frontiers/code_kg.git'

# With optional viz3d extras (for 3D visualizer — does NOT auto-install in CI)
poetry add 'code-kg[viz3d] @ git+https://github.com/Flux-Frontiers/code_kg.git'
```

Or declare it directly in your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
# Core (no visualizer)
code-kg = {git = "https://github.com/Flux-Frontiers/code_kg.git"}

# With Streamlit visualizer
code-kg = {git = "https://github.com/Flux-Frontiers/code_kg.git", extras = ["viz"]}

# With 3D visualizer
code-kg = {git = "https://github.com/Flux-Frontiers/code_kg.git", extras = ["viz3d"]}
```

> **Note for CodeKG developers:** When working on CodeKG itself, use `poetry install --with dev` to install the full dev environment (includes doc-kg, ftree-kg, agent-kg). Add `-E viz` or `-E viz3d` for the visualizer extras. The `extras` mechanism above is for *consumers* of the package; the `--with` / `-E` flags are for local development only.

All CLI entry points are available immediately — no changes to your own `pyproject.toml` required:

```bash
# --db and --lancedb default to .codekg/ — flags are optional
codekg build-sqlite  --repo .
codekg build-lancedb --repo .
codekg mcp           --repo .
```

Each subcommand also ships as a dedicated `codekg-<name>` script installed directly into the venv — no `poetry run` needed, useful for shell scripts, `Makefile` targets, and CI pipelines:

```bash
codekg-build-sqlite  --repo .
codekg-build-lancedb --repo .
codekg-build         --repo .   # SQLite + LanceDB in one step
codekg-query         "database connection setup"
codekg-pack          "authentication flow"
codekg-analyze       .
codekg-architecture  .
codekg-viz
codekg-viz3d
codekg-viz-timeline
codekg-mcp           --repo .
codekg-download-model --repo .
codekg-install-hooks --repo .
```

### For Downstream Projects

If your project depends on CodeKG (e.g., `meta_kg`), **do not** redefine the CLI entrypoints in your own `pyproject.toml`. CodeKG's tools are already installed globally and ready to use.

**✅ Correct approach: Use CodeKG's commands directly**

```bash
poetry run codekg build-sqlite --repo /path/to/repo
poetry run codekg build-lancedb --repo /path/to/repo
poetry run codekg query "search term"
```

**✅ Also correct: Forward to CodeKG's modules via CLI**

If you must create aliases in your own `pyproject.toml`, point directly to CodeKG's CLI module functions:

```toml
[tool.poetry.scripts]
my-build-sqlite  = "code_kg.cli.cmd_build:build_sqlite"  # ✅ Correct
my-build-lancedb = "code_kg.cli.cmd_build:build_lancedb"  # ✅ Correct
my-mcp           = "code_kg.mcp_server:main"              # ✅ Correct
```

**❌ Incorrect: Avoid legacy module names**

```toml
[tool.poetry.scripts]
my-build-sqlite = "code_kg.build_codekg_sqlite:main"  # ❌ Wrong (legacy)
```

The legacy module names (`build_codekg_sqlite`, `build_codekg_lancedb`) exist only for backward compatibility as re-export stubs. Always import from `code_kg.cli.cmd_build` instead.

---

## CLI Usage

Once installed, all commands are available via the unified `codekg` CLI:

```bash
codekg --help
```

Every subcommand also has a dedicated `codekg-<name>` script entry point. Both forms are fully equivalent:

```bash
codekg build-sqlite --repo .
# same as
codekg-build-sqlite --repo .
```

| Script alias | Equivalent subcommand |
|---|---|
| `codekg-build-sqlite` | `codekg build-sqlite` |
| `codekg-build-lancedb` | `codekg build-lancedb` |
| `codekg-build` | `codekg build` |
| `codekg-query` | `codekg query` |
| `codekg-pack` | `codekg pack` |
| `codekg-analyze` | `codekg analyze` |
| `codekg-architecture` | `codekg architecture` |
| `codekg-viz` | `codekg viz` |
| `codekg-viz3d` | `codekg viz3d` |
| `codekg-viz-timeline` | `codekg viz-timeline` |
| `codekg-mcp` | `codekg mcp` |
| `codekg-download-model` | `codekg download-model` |
| `codekg-install-hooks` | `codekg install-hooks` |

### Quick Start: Build Both Databases (Recommended)

**The easiest way** — build both the SQLite graph and LanceDB semantic index in one step:

```bash
codekg build --repo /path/to/repo [--wipe]
```

This combines steps 1 and 2 below and is the recommended workflow for most users.

---

### Including Only Specific Directories

By default, CodeKG indexes all Python files in your repository. You can restrict indexing to specific top-level directories using:

**Option 1: Configuration in `pyproject.toml`** (persistent, recommended)

Add to your project's `pyproject.toml`:

```toml
[tool.codekg]
include = ["src", "lib"]
```

**Option 2: CLI flags** (per-command override)

```bash
# Include only one directory
codekg build --repo . --include-dir src

# Include multiple directories (use flag multiple times)
codekg build --repo . --include-dir src --include-dir lib

# Also works with build-sqlite and analyze
codekg build-sqlite --repo . --include-dir src
codekg analyze . --include-dir src
```

When no `include` is configured, all directories are indexed (excluding the built-in skip list: `.git`, `.venv`, `__pycache__`, `.codekg`, etc.).

**Use cases:**
- `src/` — index only production source, skipping tests and scripts
- `src/ lib/` — multi-package repos where only certain packages matter
- Omit `tests/` to avoid skewed metrics: pytest entry points appear as orphaned code, test helpers inflate fan-in, and undocumented test functions drag down docstring coverage

---

### Advanced: Build Step-by-Step (Full Control)

For granular control or to rebuild only a specific component, use the individual commands below.

### 1. Build the SQLite knowledge graph

```bash
codekg build-sqlite --repo /path/to/repo --db .codekg/graph.sqlite [--wipe]
```

### 2. Build the LanceDB semantic index

```bash
codekg build-lancedb --sqlite .codekg/graph.sqlite [--model BAAI/bge-small-en-v1.5] [--wipe]
```

### 3. Run a hybrid query

```bash
codekg query \
  --sqlite .codekg/graph.sqlite \
  --q "database connection setup" \
  --k 8 \
  --hop 1
```

### 4. Generate a snippet pack

```bash
codekg pack \
  --repo-root /path/to/repo \
  --sqlite .codekg/graph.sqlite \
  --q "configuration loading" \
  --k 8 \
  --hop 1 \
  --format md \
  --out context_pack.md
```

**Key options for `pack`:**

| Option             | Default                          | Description                              |
|--------------------|----------------------------------|------------------------------------------|
| `--k`              | `8`                              | Top-K semantic hits                      |
| `--hop`            | `1`                              | Graph expansion hops                     |
| `--rels`           | `CONTAINS,CALLS,IMPORTS,INHERITS`| Edge types to expand                     |
| `--context`        | `5`                              | Extra context lines around each span     |
| `--max-lines`      | `160`                            | Max lines per snippet block              |
| `--max-nodes`      | `50`                             | Max nodes returned in pack               |
| `--format`         | `md`                             | Output format: `md` or `json`            |
| `--include-symbols`| off                              | Include symbol nodes in output           |

### 5. Launch the Streamlit visualizer

```bash
codekg viz [--db .codekg/graph.sqlite] [--port 8500]
```

### 6. Start the MCP server

```bash
codekg mcp --repo /path/to/repo
```

### 7. Run a thorough codebase analysis

```bash
codekg analyze /path/to/repo
```

---

## Streamlit Web Application

CodeKG ships an interactive knowledge-graph explorer built with Streamlit and pyvis:

> **Requires the `viz` extra:** `pip install 'code-kg[viz]'` or `poetry install -E viz`

```bash
codekg viz
```

The app provides three tabs:

| Tab | Description |
|---|---|
| **🗺️ Graph Browser** | Interactive pyvis graph; filter by node kind or module path; click nodes for rich detail panels |
| **🔍 Hybrid Query** | Natural-language query → ranked nodes with graph, table, edge, and JSON views; download results |
| **📦 Snippet Pack** | Query → source-grounded code snippets; download as Markdown or JSON |

The sidebar provides one-click **Build Graph**, **Build Index**, and **Build All** buttons.

---

## 3D Knowledge Graph Visualizer

CodeKG ships an interactive 3D graph explorer built with **PyVista** and **PyQt5** (actively being developed):

> ⚠️ **Active Development:** The Allium layout is stable and recommended. The LayerCake layout is undergoing refinement for better hierarchical clarity and is subject to change.

```bash
codekg viz3d [--db .codekg/graph.sqlite] [--layout allium|cake]
```

Explore the knowledge graph in stunning 3D with two layout strategies:

| Layout | Description |
|---|---|
| **Allium** (default) | Radial/onion structure; nodes clustered by semantic proximity; edges flow outward from core modules |
| **LayerCake** | Hierarchical levels; structural layers (definitions, calls, imports, inheritance) displayed vertically for easy traversal |

**Features:**
- Rotate, zoom, and pan the graph in real-time
- Click nodes to inspect details (docstring, line numbers, edge evidence)
- Filter edge types interactively (`--rels CALLS IMPORTS INHERITS CONTAINS`)
- Toggle `CONTAINS` edges for cleaner/denser views (`--show-contains`)
- Export to HTML (`--export-html graph.html`) for sharing
- Export to PNG (`--export-png screenshot.png`) for documentation

**Example usage:**

```bash
# Interactive 3D graph with Allium layout (default)
codekg viz3d

# Layer-cake view showing only calls and inheritance
codekg viz3d --layout cake --rels CALLS INHERITS

# Export to HTML (no window)
codekg viz3d --export-html my_graph.html
```

---

## MCP Server

CodeKG ships a built-in **Model Context Protocol (MCP) server** that exposes the full query pipeline as structured tools for AI agents — Claude Code, Kilo Code, GitHub Copilot, Claude Desktop, Cursor, Continue, or any custom agent.

### Prerequisites

Build the knowledge graph first (the MCP server is read-only):

```bash
codekg build-sqlite  --repo /path/to/repo
codekg build-lancedb --repo /path/to/repo
```

### Available Tools

| Tool | Description |
|---|---|
| `query_codebase(q, ...)` | Hybrid semantic + structural query; returns ranked nodes and edges as JSON |
| `pack_snippets(q, ...)` | Hybrid query + source-grounded snippet extraction; returns Markdown |
| `get_node(node_id, include_edges)` | Fetch a single node by its stable ID; `include_edges=True` also returns outgoing edges and incoming callers |
| `graph_stats()` | Node and edge counts by kind/relation |
| `callers(node_id)` | Precise fan-in lookup resolving cross-module `sym:` stubs via `RESOLVES_TO` edges |
| `explain(node_id)` | Natural-language explanation of a node: metadata, docstring, callers, and callees |
| `analyze_repo()` | Run the full nine-phase architectural analysis (complexity, coupling, docstring coverage, etc.); returns Markdown |
| `snapshot_list(limit, branch)` | List saved codebase metric snapshots newest-first with deltas vs. previous; optionally filter by branch |
| `snapshot_show(key)` | Full metrics for a specific snapshot key (tree hash), or `"latest"` for the most recent snapshot |
| `snapshot_diff(key_a, key_b)` | Compare two snapshots side-by-side; returns delta for nodes, edges, coverage, and critical issues |

### Automated setup

The Quick Start installer (`curl ... | bash`) writes all MCP config files automatically for every supported provider. Alternatively, from inside Claude Code run:

```
/setup-mcp [/path/to/repo]
```

This skill verifies installation, builds the graph and index, smoke-tests the pipeline, and writes/updates the config files.

See [`docs/MCP.md`](docs/MCP.md) for the full MCP reference including tool schemas, query strategy guide, and troubleshooting.

### Cline (manual)

Cline does not support per-repo MCP config. The installer writes a uniquely-keyed entry to Cline's **global** settings file:

**macOS:** `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

Add an entry keyed as `codekg-<repo-name>`:

```json
{
  "mcpServers": {
    "codekg-my-repo": {
      "command": "/absolute/path/to/venv/bin/codekg-mcp",
      "args": ["--repo", "/absolute/path/to/repo"]
    }
  }
}
```

> ⚠️ Do **not** add a `codekg` entry without a repo-specific suffix — global settings are shared across all VS Code windows.

### Claude Desktop (manual)

Add a `codekg` entry to `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "codekg": {
      "command": "/absolute/path/to/venv/bin/codekg-mcp",
      "args": ["--repo", "/absolute/path/to/repo"]
    }
  }
}
```

Use **absolute paths** — Claude Desktop does not inherit your shell's working directory.

### Claude Code / Kilo Code — `.mcp.json`

Both Claude Code and Kilo Code read per-repo config from `.mcp.json`:

```json
{
  "mcpServers": {
    "codekg": {
      "command": "codekg",
      "args": ["mcp", "--repo", "/absolute/path/to/repo"]
    }
  }
}
```

> ⚠️ Use per-repo `.mcp.json` only — do NOT add `codekg` to any global settings file.

### GitHub Copilot — `.vscode/mcp.json`

GitHub Copilot uses `.vscode/mcp.json` with a different schema:

```json
{
  "servers": {
    "codekg": {
      "type": "stdio",
      "command": "/absolute/path/to/.venv/bin/codekg-mcp",
      "args": [
        "--repo",
        "/absolute/path/to/repo",
        "--db",
        "/absolute/path/to/repo/.codekg/graph.sqlite",
        "--lancedb",
        "/absolute/path/to/repo/.codekg/lancedb"
      ]
    }
  }
}
```

---

## Output Artifacts

| Artifact             | Description                                      |
|----------------------|--------------------------------------------------|
| `.codekg/graph.sqlite` | Canonical knowledge graph (nodes + edges)      |
| `.codekg/lancedb/`    | Derived semantic vector index                  |
| Markdown        | Human-readable context packs with line numbers |
| JSON            | Structured payload for agent/LLM ingestion     |

---

## Project Structure

```
code_kg/
├── CHANGELOG.md
├── CLAUDE.md
├── LICENSE
├── README.md
├── release-notes.md
├── pyproject.toml
├── docs/
│   ├── Architecture.md
│   ├── Architecture-brief.md
│   ├── Architecture-plain.md
│   ├── CHEATSHEET.md
│   ├── code_kg.pdf
│   ├── code_kg_arch_9x16.png
│   ├── code_kg_arch_banana.png
│   ├── code_kg_arch_square.png
│   ├── code_kg_workflow.md
│   ├── deployment.md
│   ├── MCP.md
│   └── logo.png
├── lib/
│   ├── bindings/
│   │   └── utils.js
│   ├── tom-select/
│   │   ├── tom-select.complete.min.js
│   │   └── tom-select.css
│   └── vis-9.1.2/
│       ├── vis-network.css
│       └── vis-network.min.js
├── scripts/
│   └── install-skill.sh
├── src/
│   └── code_kg/
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py                      # Streamlit web interface
│       ├── kg.py                       # Core CodeKG orchestrator
│       ├── graph.py                    # AST extraction (3-pass)
│       ├── store.py                    # SQLite persistence + graph traversal
│       ├── index.py                    # LanceDB semantic indexing
│       ├── visitor.py                  # AST visitor for data-flow analysis
│       ├── config.py                   # Configuration loading
│       ├── mcp_server.py               # Model Context Protocol server
│       ├── viz3d.py                    # 3D graph visualizer (PyVista/PyQt5)
│       ├── cli/                        # Click-based CLI entry points
│       │   ├── __init__.py
│       │   ├── main.py                 # Root Click group
│       │   ├── cmd_build.py            # build-sqlite, build-lancedb
│       │   ├── cmd_build_full.py       # build (full pipeline)
│       │   ├── cmd_query.py            # query, pack
│       │   ├── cmd_viz.py              # viz, viz3d
│       │   ├── cmd_analyze.py          # analyze
│       │   ├── cmd_mcp.py              # mcp
│       │   └── options.py              # Shared CLI options
│       ├── build_codekg_lancedb.py    # Legacy re-export (deprecated)
│       └── build_codekg_sqlite.py     # Legacy re-export (deprecated)
├── tests/
│   ├── test_graph.py
│   ├── test_kg.py
│   ├── test_primitives.py
│   └── test_store.py
└── __pycache__/
```

---

## Development

To work on CodeKG itself, clone the repository and install in editable mode with dev dependencies:

```bash
git clone https://github.com/Flux-Frontiers/code_kg.git
cd code_kg
poetry install --with dev          # core + dev (includes doc-kg, ftree-kg, agent-kg)
poetry install --with dev -E viz   # + Streamlit visualizer
poetry install --with dev -E viz3d # + 3D visualizer (PyVista/PyQt5)
poetry install --all-extras --with dev  # everything
```

Run the test suite:

```bash
poetry run pytest
```

---

## Architecture

<p align="center">
  <img src="assets/codeKG_arch_square-web.jpg" alt="CodeKG architecture workflow" width="600"/>
</p>

### Design Principles

1. **Structure is authoritative** — The AST-derived graph is the source of truth.
2. **Semantics accelerate, never decide** — Vector embeddings seed and rank retrieval but never invent structure.
3. **Everything is traceable** — Nodes and edges map to concrete files and line numbers.
4. **Determinism over heuristics** — Identical input yields identical output.
5. **Composable artifacts** — SQLite for structure, LanceDB for vectors, Markdown/JSON for consumption.

### Core Data Model

#### Nodes

| Kind       | Description                                                    |
|------------|----------------------------------------------------------------|
| `module`   | Python source file                                             |
| `class`    | Class definition                                               |
| `function` | Top-level function                                             |
| `method`   | Class method                                                   |
| `symbol`   | Variables, parameters, and attributes (data-flow pass)        |

Each node stores: `id`, `kind`, `name`, `qualname`, `module_path`, `lineno`, `end_lineno`, and optional `docstring`. Nodes live in **SQLite**, which is canonical.

#### Edges

| Relation       | Meaning                                                       |
|----------------|---------------------------------------------------------------|
| `CONTAINS`     | Module → class/function; class → method                      |
| `CALLS`        | Function/method → function/method                            |
| `IMPORTS`      | Module → module/symbol                                        |
| `INHERITS`     | Class → base class                                            |
| `RESOLVES_TO`  | `sym:` stub → first-party definition (enables cross-module fan-in) |
| `ATTR_ACCESS`  | Variable/symbol → accessed attribute (`obj.attr`)             |
| `READS`        | Variable read at assignment RHS or call site                  |
| `WRITES`       | Variable written at assignment target                         |

Edges carry **evidence** (source line number and expression text), enabling call-site extraction and precise auditability.

### Build Pipeline

#### Phase 1 — Static Analysis (AST → SQLite)

The repository is parsed using Python's `ast` module in **three sequential passes** over each file:

1. **Pass 1 — Structural extraction** — modules, classes, functions, methods; emit `CONTAINS`/`IMPORTS`/`INHERITS` edges
2. **Pass 2 — Call graph** — call expressions resolved to targets; emit `CALLS` edges with source-line evidence
3. **Pass 3 — Data-flow** — `CodeKGVisitor` walks each AST to emit `READS`, `WRITES`, `ATTR_ACCESS` edges at variable and attribute level; new `symbol` nodes merged non-destructively

**Output:** SQLite database (`.codekg/graph.sqlite`) with `nodes` and `edges` tables.

4. **Post-build — Symbol resolution** — `resolve_symbols()` first attempts exact qualified-name resolution (including common `src/` alias variants), then falls back to name matching, and writes `RESOLVES_TO` edges with evidence metadata (`resolution_mode`, `confidence`, optional ambiguity count); idempotent and automatic.

> This phase uses **no embeddings and no LLMs**.

#### Phase 2 — Semantic Indexing (SQLite → LanceDB)

Subset of nodes (`module`, `class`, `function`, `method`) selected for vector indexing. Embedding text constructed from names and docstrings, embedded using `BAAI/bge-small-en-v1.5` (384-dim, overridable via `CODEKG_MODEL`), stored in **LanceDB**.

The vector index is **derived and disposable**; SQLite remains authoritative.

### Hybrid Query Model

Queries execute in **two explicit phases**:

1. **Semantic seeding** — Natural-language query embedded and used to retrieve small set of semantically similar nodes from vector index (entry points)
2. **Structural expansion** — From semantic seeds, relational graph expanded using selected edge types (`CONTAINS`, `CALLS`, `IMPORTS`, `INHERITS`); bounded by hop count; records provenance (minimum hop distance and originating seed)

### Ranking, Deduplication & Snippet Extraction

Retrieved nodes ranked deterministically by: (1) hop distance from seed, (2) seed embedding distance, (3) node kind priority (`function`/`method` > `class` > `module` > `symbol`).

Nodes deduplicated by file and source span; overlapping spans merged; per-file cap prevents large modules from dominating results. For retained nodes, CodeKG extracts **source-grounded definition and call-site snippets** using recorded `module_path`, `lineno`, and `end_lineno`, with bounded context windows.

### Caller Lookup (Fan-In)

CodeKG provides precise fan-in lookup via the `callers()` API and `callers` MCP tool. The two-phase lookup combines:

1. **Direct reverse** — nodes with `CALLS → target` edges
2. **Stub reverse** — nodes with `CALLS → sym:Foo` where `sym:Foo RESOLVES_TO target`

This bridges the gap for imported functions where the AST visitor emits `CALLS → sym:Foo` stubs for unresolved call targets (imported names, attribute accesses).

When stub callers are ambiguous, `callers()` applies import-aware filtering in the caller module so same-name definitions are not over-linked.

### Data Flow Diagram

```
Repository
  ↓
AST parsing — Pass 1: structure, Pass 2: calls, Pass 3: data-flow  (graph.py + visitor.py)
  ↓
SQLite graph — nodes + edges  (store.py / codekg build-sqlite)
  ↓
Symbol resolution — RESOLVES_TO edges (sym: stubs → fn:/cls: defs)  (store.py)
  ↓
Vector indexing — LanceDB  (index.py / codekg build-lancedb)
  ↓
Hybrid query — semantic + graph  (kg.py / codekg query)
  ↓
Ranking + deduplication
  ↓
Snippet pack — Markdown / JSON  (kg.py / codekg pack)
  ↓
  ├──▶  Streamlit web app  (app.py / codekg viz)
  └──▶  MCP server tools   (mcp_server.py / codekg mcp)
```

---

## References

### Tools & Technologies

- **[PaperBanana](https://paperbanana.dev/)** — Technical diagram generation from structured data. The architecture diagram at the top of the Architecture section was created by feeding CodeKG's own analysis output (generated via `codekg analyze`) to PaperBanana, demonstrating how well-structured, deterministic code analysis feeds downstream visualization tools and validating CodeKG's core design philosophy: clean, traceable data structures enable rich, accurate, and beautiful downstream consumption.

### Related Work

- **[Microsoft GraphRAG](https://microsoft.com/research/)** — Probabilistic knowledge graph approaches for LLM retrieval (comparison: GraphRAG uses statistical inference; CodeKG prioritizes determinism and auditability).
- **[Amplify](https://amplify.dev/)** — Embedding-only code search (comparison: CodeKG augments semantic retrieval with structural graph traversal).
- **[LanceDB](https://lancedb.com/)** — Vector database used for semantic indexing in CodeKG.
- **[Streamlit](https://streamlit.io/)** — Web application framework for the interactive CodeKG visualizer.

---

## License

[Elastic License 2.0](https://www.elastic.co/licensing/elastic-license) — see [LICENSE](LICENSE).

Free to use, modify, and distribute. You may not offer the software as a hosted or managed service to third parties. Commercial use internally is permitted.
