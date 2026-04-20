# Release Notes — PyCodeKG v0.14.1

> Released: 2026-04-20

## Overview

PyCodeKG is a hybrid semantic + structural knowledge graph for Python codebases. It indexes every module, class, function, and method as a node — with typed edges (CALLS, IMPORTS, CONTAINS, INHERITS) connecting them — and exposes the graph through a Model Context Protocol (MCP) server so AI agents can navigate and reason about code precisely and efficiently.

This is the first general release.

## What's Included

### Knowledge Graph Pipeline

PyCodeKG compiles a Python repository into a queryable knowledge graph through five semantically ordered enrichment phases:

1. **Structural extraction** — AST-based indexing of modules, classes, functions, and methods into SQLite
2. **Call graph** — CALLS and ATTR_ACCESS edges derived from function invocations
3. **Data flow** — IMPORTS edges and cross-module dependency tracing
4. **Symbol resolution** — Disambiguation of same-name symbols across modules
5. **Semantic indexing** — Vector embeddings via `BAAI/bge-small-en-v1.5` stored in LanceDB

### MCP Server (27 Tools)

A full FastMCP server exposes the graph to any MCP-compatible client (Claude, Cursor, Continue):

- `graph_stats` — node/edge counts by kind and relation
- `query_codebase` — hybrid semantic + structural search with hop expansion
- `pack_snippets` — source-grounded code snippets for LLM context windows
- `get_node` / `list_nodes` — precise node lookup and enumeration
- `callers` — find all callers of any function
- `explain` / `explain_rank` — natural-language explanations with structural context
- `centrality` / `bridge_centrality` / `framework_nodes` / `rank_nodes` / `query_ranked` — structural importance rankings via SIR PageRank
- `analyze_repo` — full architectural analysis (complexity, coupling, coverage, orphans)
- `snapshot_list` / `snapshot_show` / `snapshot_diff` — temporal metrics across versions

### CLI

```bash
pycodekg init          # one-command setup: model download, build, hooks, snapshot
pycodekg build         # full rebuild (SQLite + LanceDB)
pycodekg update        # incremental upsert (no wipe)
pycodekg query "..."   # hybrid query from the terminal
pycodekg pack "..."    # snippet pack for LLM analysis
pycodekg analyze .     # thorough architectural report
pycodekg mcp           # start the MCP server
pycodekg viz           # Streamlit interactive visualizer
pycodekg viz3d         # 3D PyVista/PyQt5 visualizer
```

### Quality & Architecture

- Grade A (92/100) on internal self-analysis (`pycodekg analyze`)
- 7,178 indexed nodes, 92.6% docstring coverage
- Orphan detection accounts for bound-method callback patterns (ATTR_ACCESS edges)
- `pycodekg build` always wipes for clean rebuilds; `pycodekg update` for incremental upserts

## Installation

```bash
# Core install (SQLite + LanceDB + MCP server)
pip install 'pycode-kg @ git+https://github.com/Flux-Frontiers/pycode_kg.git'

# With Streamlit web visualizer
pip install 'pycode-kg[viz] @ git+https://github.com/Flux-Frontiers/pycode_kg.git'

# With 3D visualizer extras (PyVista, PyQt5 — heavy dependencies)
pip install 'pycode-kg[viz3d] @ git+https://github.com/Flux-Frontiers/pycode_kg.git'

# Both visualizers
pip install 'pycode-kg[viz,viz3d] @ git+https://github.com/Flux-Frontiers/pycode_kg.git'
```

Requires Python ≥ 3.12, < 3.14. See [INSTALLATION.md](docs/INSTALLATION.md) for Poetry install, development setup, MCP configuration, and full CLI reference.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
