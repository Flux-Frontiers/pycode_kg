# PyCodeKG Architecture: Layered Methodology & Hybrid Query Flow

Use this document to regenerate the architecture diagram. It describes every
component, layer, data flow, and output surface in the current codebase.

---

## Title

**PyCodeKG Architecture: Layered Methodology & Hybrid Query Flow**

---

## Input

**Python Codebase** (`.py` files)
→ Static Analysis (3-pass AST)

---

## Core Layers (inside the main orchestration boundary)

### Layer 0 — Primitives (`pycodekg.py` + `visitor.py`)

Frozen dataclasses. No side effects, no I/O.

| Symbol | Role |
|--------|------|
| `Node` | `id`, `kind`, `name`, `qualname`, `loc`, `docstring` |
| `Edge` | `src`, `rel`, `dst`, `evidence` |
| `extract_repo()` | 3-pass AST extraction entry point |
| `PyCodeKGVisitor` (`visitor.py`) | Pass 3: data-flow edges (ATTR_ACCESS, READS, WRITES) |

**Edge relation types produced:**
`CONTAINS`, `IMPORTS`, `INHERITS`, `CALLS`, `ATTR_ACCESS`, `RESOLVES_TO`

---

### Layer 1 — AST Extraction (`graph.py`)

Pure, deterministic extraction. No persistence, no embeddings.

| Symbol | Role |
|--------|------|
| `CodeGraph` | Wraps `extract_repo()` with a clean object interface |
| `CodeGraph.extract()` | Returns `(nodes, edges)` via lazy evaluation |

Passes extracted nodes/edges to Layer 2.

---

### Layer 2 — GraphStore (`store.py` → SQLite)

**Authoritative, canonical store.** No embeddings, no vector data.

| Symbol | Role |
|--------|------|
| `GraphStore` | SQLite-backed persistence for nodes + edges tables |
| `.write(nodes, edges, wipe)` | Persist extracted graph (full wipe or incremental upsert) |
| `.node(id)` | Fetch a single node by stable ID |
| `.expand(seeds, hop, rels)` | BFS graph traversal from seed node IDs |
| `.resolve_symbols()` | Post-build: adds `RESOLVES_TO` edges from `sym:` stubs → first-party definitions |
| `.query_nodes(kinds)` | Bulk node retrieval by kind |
| `.stats()` | Node/edge counts |

**Artifact:** `.pycodekg/graph.sqlite`

---

### Layer 3 — SemanticIndex (`index.py` → sqlite-vec)

**Derived, disposable vector index.** Rebuilt from SQLite at any time.

| Symbol | Role |
|--------|------|
| `SemanticIndex` | sqlite-vec-backed semantic index |
| `SentenceTransformerEmbedder` | Embedding backend (`BAAI/bge-small-en-v1.5`) |
| `.build(store, wipe)` | Read nodes from GraphStore → embed → upsert into the vector store |
| `.search(q, k)` | ANN vector search, returns top-K hits with distance scores |
| `_build_index_text(node)` | Canonical text format for embedding (KIND, NAME, QUALNAME, MODULE, DOCSTRING, KEYWORDS) |

Reads nodes from Layer 2 (GraphStore).

**Artifact:** `.pycodekg/vectors.sqlite`

---

### Layer 4 — KGModule Orchestrator (`module/base.py`, `kg.py`)

Wires all layers together. `KGModule` is abstract; `PyCodeKG` is the concrete subclass.

| Symbol | Role |
|--------|------|
| `KGModule` (abstract) | Base class: build/query/pack infrastructure. Domain authors implement `make_extractor()` + `kind()` |
| `PyCodeKG` | Concrete subclass for Python repos. Wires `CodeGraph` → `GraphStore` → `SemanticIndex` |
| `.build(wipe)` | Full pipeline: AST extraction → GraphStore → SemanticIndex |
| `.query(q, k, hop, rels, rerank_mode)` | Hybrid query: semantic seeding (sqlite-vec) + BFS expansion (SQLite) + reranking |
| `.pack(q, ...)` | Source-grounded snippet extraction with context lines |

**Rerank modes:**
- `hybrid` (default): 70% semantic score + 30% lexical name/docstring overlap
- `semantic`: vector score only
- `legacy`: hop-distance first, then vector distance

**Left-side annotation:** `resolve_symbols()` / `RESOLVES_TO` edges (post-build step, GraphStore → GraphStore)

---

### Layer 5 — Ranking & Analysis (`architecture.py`, centrality, snapshots)

| Symbol | Role |
|--------|------|
| `ArchitectureAnalyzer` | Nine-phase analysis: complexity, coupling, docstring coverage, circular deps, orphaned functions, health signals |
| Centrality tools | SIR PageRank (`centrality`), betweenness (`bridge_centrality`), CodeRank (`rank_nodes`) |
| `SnapshotManager` (`snapshots.py`) | Temporal metric snapshots: nodes, edges, coverage, critical issues, complexity median; `capture()`, `diff_snapshots()` |

**Artifact:** `.pycodekg/snapshots/` (JSON files, keyed by git tree hash)
**Trigger:** Pre-commit git hook (`install-hooks`)

---

## Query Flow (bottom section of diagram)

```
QUERY INPUT (text)
       │
       ▼
  SemanticIndex  ──── 1. Semantic Seeding (ANN vector search) ────► Seed Hits (top-K)
       │
       │  Seed Hits (top-K)
       ▼
  GraphStore  ──── 2. BFS Structural Expansion (hop=N, rels filter) ────►
       │
       │  Expanded node set
       ▼
  Reranker (hybrid/semantic/legacy)
       │
       ▼
  OUTPUT: QueryResult / SnippetPack
    - Ranked nodes + edges (JSON)
    - Source snippets with line numbers (Markdown)
```

---

## CLI Layer (`cli/`)

Built with Click. Entry point: `pycodekg` / `src/pycode_kg/cli/main.py`.

| Command | Module | Purpose |
|---------|--------|---------|
| `build` / `update` | `cmd_build_full.py` | Full wipe+rebuild or incremental upsert |
| `build-sqlite` / `build-index` | `cmd_build.py` | Individual build steps |
| `init` | `cmd_init.py` | One-command setup: download model, build, install hooks, snapshot |
| `query` | `cmd_query.py` | Hybrid query from terminal |
| `analyze` | `cmd_analyze.py` | Thorough codebase analysis |
| `architecture` | `cmd_architecture.py` | Generate Markdown/JSON architecture description |
| `centrality` | `cmd_centrality.py` | SIR PageRank ranking |
| `explain` | `cmd_explain.py` | Natural-language node explanation |
| `snapshot` | `cmd_snapshot.py` | Save / list / show / diff temporal snapshots |
| `viz` | `cmd_viz.py` | Launch Streamlit web app |
| `mcp` | `cmd_mcp.py` | Start MCP server |
| `install-hooks` | `cmd_hooks.py` | Install pre-commit git hook |
| `download-model` | `cmd_model.py` | Pre-fetch embedding model for offline use |

---

## Output / Consumer Layer

| Consumer | File(s) | Purpose |
|----------|---------|---------|
| **MCP Server** | `mcp_server.py` | 17+ MCP tools for AI agents (Claude Desktop, Cursor, Continue). Transports: `stdio` (default) / `sse`. Entry point: `pycodekg mcp --repo .` |
| **Streamlit Web App** | `app.py` | Interactive graph explorer with hybrid and structural views. Launch: `pycodekg viz` |
| **3D Visualizer** | `viz3d.py`, `layout3d.py` | PyVista/PyQt5 3D graph; layer-cake and allium layouts. Launch: `pycodekg viz3d` |

---

## Data Artifacts Summary

| Artifact | Location | Description |
|----------|----------|-------------|
| SQLite graph | `.pycodekg/graph.sqlite` | Authoritative nodes + edges; canonical source of truth |
| Vector index | `.pycodekg/vectors.sqlite` | Derived vector index; disposable, rebuilt from SQLite |
| Snapshots | `.pycodekg/snapshots/` | JSON metric snapshots keyed by git tree hash |

---

## Module Map (source → layer)

```
src/pycode_kg/
├── pycodekg.py          # Layer 0: Primitives (Node, Edge, extract_repo)
├── visitor.py           # Layer 0: AST visitor (ATTR_ACCESS / data-flow pass)
├── graph.py             # Layer 1: CodeGraph (pure AST extraction)
├── store.py             # Layer 2: GraphStore (SQLite)
├── index.py             # Layer 3: SemanticIndex (sqlite-vec)
├── kg.py                # Layer 4: PyCodeKG (top-level orchestrator subclass)
├── module/
│   ├── base.py          # Layer 4: KGModule (abstract orchestrator)
│   └── extractor.py     # Layer 4: PyCodeKGExtractor (bridges pycodekg.py → KGModule)
├── architecture.py      # Layer 5: ArchitectureAnalyzer
├── snapshots.py         # Layer 5: SnapshotManager
├── config.py            # Config loading (include/exclude dirs, pyproject.toml)
├── utils.py             # Shared utilities
├── mcp_server.py        # Output: MCP server (17+ tools)
├── app.py               # Output: Streamlit app entry
├── viz3d.py             # Output: 3D visualizer core
├── layout3d.py          # Output: 3D layout algorithms (LayerCake, Allium, etc.)
├── pycodekg_thorough_analysis.py  # Deep analysis pipeline
└── cli/                 # CLI layer (Click commands)
    ├── main.py
    ├── cmd_build_full.py
    ├── cmd_build.py
    ├── cmd_init.py
    ├── cmd_snapshot.py
    ├── cmd_query.py
    ├── cmd_analyze.py
    ├── cmd_architecture.py
    ├── cmd_centrality.py
    ├── cmd_explain.py
    ├── cmd_viz.py
    ├── cmd_mcp.py
    ├── cmd_hooks.py
    ├── cmd_model.py
    └── ...
```
