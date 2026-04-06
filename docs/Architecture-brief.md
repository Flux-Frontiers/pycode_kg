# PyCodeKG Architecture (Condensed)

**PyCodeKG v0.5** — Deterministic knowledge graph for Python codebases via static analysis, SQLite persistence, and semantic search acceleration.

<p align="center">
  <img src="../assets/pycode_kg_arch_square-web.jpg" alt="PyCodeKG Architecture" width="480"/>
</p>

---

## Core Design

1. **Structure is authoritative** — AST-derived graph is ground truth
2. **Semantics accelerate, never decide** — Vector embeddings seed/rank, never invent
3. **Everything traceable** — Nodes/edges map to concrete file:lineno
4. **Deterministic** — Identical input → identical output
5. **Composable** — SQLite (structure), LanceDB (vectors), Markdown/JSON (export)
6. **Honest** — Only what is visible in the AST; no inference, no LLMs

---

## Layered Architecture

```
PyCodeKG (orchestrator — kg.py)
  ├─ CodeGraph     (pure AST extraction, no I/O — graph.py)
  ├─ GraphStore    (SQLite: nodes/edges, BFS traversal — store.py)
  ├─ SemanticIndex (LanceDB: embeddings, disposable — index.py)
  └─ Primitives    (locked v0 contract — pycodekg.py)
       ├─ PyCodeKGVisitor  (Pass 3 data-flow — visitor.py)
       └─ load_exclude_dirs()  (pyproject.toml config — config.py)
```

---

## Layer 1: Primitives (`pycodekg.py`)

- **Node**: frozen dataclass — id, kind, name, qualname, module_path, lineno, end_lineno, docstring
- **Edge**: frozen dataclass — src, rel, dst, evidence
- **`extract_repo(repo_root, exclude=None)`**: three-pass AST extraction → `(nodes, edges)`
- **`iter_python_files(repo_root, exclude=None)`**: yields `.py` files, skipping SKIP_DIRS + exclude

**Node kinds:** `module`, `class`, `function`, `method`, `symbol`

**Edge relations:**

| Relation | Pass | Description |
|---|---|---|
| `CONTAINS` | 1 | Structural parent → child |
| `IMPORTS` | 1 | Module import dependency |
| `INHERITS` | 1 | Class inheritance |
| `CALLS` | 2 | Function/method call |
| `READS` | 3 | Variable read (data-flow) |
| `WRITES` | 3 | Variable write (data-flow) |
| `ATTR_ACCESS` | 3 | Attribute access (data-flow) |
| `DEPENDS_ON` | 3 | Future control-flow placeholder |
| `RESOLVES_TO` | post | `sym:` stub → first-party definition |

### Pass 3: PyCodeKGVisitor (`visitor.py`)

`ast.NodeVisitor` subclass for data-flow extraction. Processes each `.py` file and emits READS, WRITES, ATTR_ACCESS edges with `{lineno, file}` evidence.

### Config: `config.py`

`load_exclude_dirs(repo_root)` reads `[tool.pycodekg].exclude` from `pyproject.toml`. Returns `set[str]` of directory names to skip. Returns empty set on any error.

---

## Layer 2: CodeGraph (`graph.py`)

Pure AST extraction with lazy evaluation. No persistence, no embeddings.

```python
graph = CodeGraph("/path/to/repo", exclude={"old", "vendor"})
graph.extract()          # cached; force=True to re-run
nodes, edges = graph.result()
graph.stats()            # node/edge counts by kind
```

---

## Layer 3: GraphStore (`store.py`)

SQLite-backed authoritative store. No embeddings, no AST.

**Key methods:**

| Method | Description |
|---|---|
| `write(nodes, edges, wipe=False)` | Persist graph (upsert) |
| `node(id)` | Fetch single node by ID |
| `query_nodes(kinds=, module=)` | Filtered node list |
| `edges_within(node_ids)` | Edges with both endpoints in set |
| `expand(seed_ids, hop=N, rels=…)` | BFS → `Dict[id, ProvMeta]` |
| `resolve_symbols()` | Post-build: `sym:` → `RESOLVES_TO` edges |
| `callers_of(node_id)` | Two-phase reverse lookup (direct + via sym: stubs) |
| `stats()` | Node/edge counts by kind/relation |

**ProvMeta** (from expand): `best_hop`, `via_seed`

---

## Layer 4: SemanticIndex (`index.py`)

LanceDB-backed vector index. Derived, disposable, rebuildable.

```python
idx = SemanticIndex("./lancedb", embedder=SentenceTransformerEmbedder())
idx.build(store, wipe=True)
hits = idx.search("database setup", k=8)  # → List[SeedHit]
```

**Embedder**: abstract interface (`embed_texts`, `embed_query`)
**SentenceTransformerEmbedder**: default (model: `BAAI/bge-small-en-v1.5`)
**SeedHit**: id, kind, name, qualname, module_path, distance, rank

**Retrieval quality note:** `BAAI/bge-small-en-v1.5` (384 dims) is the current default because it is small, fast, and performs well on short retrieval queries in this codebase. The model bridges NL queries to code *only when a docstring is present*; without one, the embedded text reduces to structured identifiers (`KIND/NAME/QUALNAME/MODULE`) where BM25 is equally effective. Hop expansion from seed nodes recovers many undocumented nodes, but accuracy depends on seed quality. **The real retrieval lever is docstring coverage, not model size.**

---

## Orchestrator: PyCodeKG (`kg.py`)

Owns all four layers with lazy initialization. Supports context manager.

```python
kg = PyCodeKG(repo_root, db_path, lancedb_dir, model, table)
kg.build(wipe=True)           # full pipeline
kg.build_graph(wipe=True)     # AST → SQLite only
kg.build_index(wipe=True)     # SQLite → LanceDB only
kg.query(q, k=8, hop=1)       # → QueryResult
kg.pack(q, k=8, hop=1)        # → SnippetPack (with source snippets)
kg.callers(node_id)           # → List[dict]  (two-phase fan-in)
kg.stats()                    # → BuildStats
kg.node(node_id)              # fetch node dict
```

**Result types:**
- **BuildStats**: repo_root, db_path, total_nodes, total_edges, node_counts, edge_counts, indexed_rows?, index_dim?
- **QueryResult**: query, seeds, expanded_nodes, returned_nodes, hop, rels, nodes[], edges[]
- **SnippetPack**: extends QueryResult; each node dict may include a `snippet` with path/start/end/text

---

## Build Pipeline

### Phase 1: Static Analysis (AST → SQLite)
1. Walk `.py` files (skip .venv, __pycache__, .git, configured exclude dirs)
2. **Pass 1**: modules, classes, functions, methods, imports, inheritance
3. **Pass 2**: call graph (honest; unresolved → `sym:` stubs)
4. **Pass 3**: data-flow edges via `PyCodeKGVisitor` (READS, WRITES, ATTR_ACCESS)
5. Generate stable node IDs: `mod:`, `cls:`, `fn:`, `m:`, `sym:`
6. Emit edges with evidence (lineno, expr, file)
7. Persist to SQLite (upsert, idempotent)
8. `resolve_symbols()`: name-match `sym:` stubs → `RESOLVES_TO` edges

### Phase 2: Semantic Indexing (SQLite → LanceDB)
1. Read module/class/function/method nodes
2. Build canonical index text (name + qualname + module + docstring)
3. Embed in batches via SentenceTransformerEmbedder
4. Upsert to LanceDB (delete-then-add per batch)

---

## Hybrid Query Model

**Phase 1 — Semantic Seeding:** `query → embed → vector search → top-K SeedHit list`

**Phase 2 — Structural Expansion:** `seed_ids → BFS over CONTAINS/CALLS/IMPORTS/INHERITS → Dict[id, ProvMeta]`

**Ranking** (deterministic composite key): `(best_hop, seed_distance, kind_priority, node_id)`
Kind priority: function=0, method=1, class=2, module=3, symbol=4

**Deduplication** (pack only): skip overlapping spans (2-line gap) in same file; cap at max_nodes

**Snippet extraction**: resolve path → read lines (cached) → AST span ± context → line-numbered block

---

## Interfaces

### Streamlit Web App (`pycodekg viz`)

Three tabs: **Graph Browser** (pyvis interactive, filter by kind/module), **Hybrid Query** (NL → ranked results), **Snippet Pack** (source-grounded snippets with MD/JSON download). Sidebar: Build Graph, Build Index, Build All.

### 3D Visualizer (`pycodekg viz3d`)

PyVista/PyQt5 scene with `KGVisualizer` (data model), `MainWindow` (Qt window), `DocstringPopup` (markdown popup). Layouts: `allium`, `cake`. Right-click to pick/highlight/inspect nodes. Requires `viz3d` extras (`extras = ["viz3d"]` for consumers; `--with viz3d` for local dev).

### Thorough Analyzer (`pycodekg analyze`)

`PyCodeKGAnalyzer` runs 7 analysis phases: complexity hotspots, entry points, dead code, docstring coverage, cohesion, coupling, critical paths. Emits Markdown report + JSON snapshot.

Classes: `PyCodeKGAnalyzer`, `FunctionMetrics`, `ModuleMetrics`, `CallChain`

### MCP Server (`pycodekg-mcp`)

Thin wrapper around `PyCodeKG`. Stateful (one instance per process), read-only.

| Tool | Returns |
|---|---|
| `query_codebase(q, k, hop, rels, include_symbols, max_nodes, min_score, max_per_module)` | JSON |
| `pack_snippets(q, k, hop, rels, context, max_lines, max_nodes, min_score, max_per_module)` | Markdown |
| `callers(node_id, rel)` | JSON |
| `get_node(node_id)` | JSON |
| `graph_stats()` | JSON |

Start: `pycodekg-mcp --repo /path [--db ...] [--lancedb ...] [--transport stdio|sse]`

### CLI Entry Points

| Command | Alias | Description |
|---|---|---|
| `pycodekg build-sqlite` | `pycodekg-build-sqlite` | AST → SQLite |
| `pycodekg build-lancedb` | `pycodekg-build-lancedb` | SQLite → LanceDB |
| `pycodekg build` | `pycodekg-build` | Full pipeline (always wipes) |
| `pycodekg update` | `pycodekg-update` | Incremental upsert (no wipe) |
| `pycodekg query` | `pycodekg-query` | Hybrid query |
| `pycodekg pack` | `pycodekg-pack` | Snippet pack |
| `pycodekg viz` | `pycodekg-viz` | Streamlit 2D visualizer |
| `pycodekg viz3d` | `pycodekg-viz3d` | PyVista 3D visualizer |
| `pycodekg analyze` | `pycodekg-analyze` | Architectural analysis |
| `pycodekg mcp` | `pycodekg-mcp` | MCP server |

### Directory Exclusion

Via `pyproject.toml`:
```toml
[tool.pycodekg]
exclude = ["old", "vendor", "generated"]
```
Or CLI: `pycodekg build --repo . --exclude-dir old --exclude-dir vendor`
Both sources are merged at build time.

---

## Source Layout

```
src/pycode_kg/
  ├── pycodekg.py                    # Locked v0 primitives
  ├── visitor.py                   # PyCodeKGVisitor (Pass 3 data-flow)
  ├── config.py                    # load_exclude_dirs()
  ├── graph.py                     # CodeGraph
  ├── store.py                     # GraphStore
  ├── index.py                     # SemanticIndex
  ├── kg.py                        # PyCodeKG orchestrator + result types
  ├── layout3d.py                  # 3D layout algorithms
  ├── viz3d.py                     # 3D PyVista/PyQt5 visualizer
  ├── pycodekg_thorough_analysis.py  # PyCodeKGAnalyzer
  ├── app.py                       # Streamlit web app
  ├── mcp_server.py                # MCP server
  ├── utils.py                     # Shared utilities
  └── cli/
      ├── main.py                  # Click entry point
      ├── cmd_build.py             # build-sqlite, build-lancedb
      ├── cmd_build_full.py        # build (full)
      ├── cmd_query.py             # query, pack
      ├── cmd_viz.py               # viz, viz3d
      ├── cmd_analyze.py           # analyze
      ├── cmd_mcp.py               # mcp
      └── options.py               # Shared Click options

tests/
  ├── test_primitives.py    # Node, Edge, extract_repo
  ├── test_graph.py         # CodeGraph
  ├── test_store.py         # GraphStore
  ├── test_kg.py            # PyCodeKG, result types
  ├── test_visitor.py       # PyCodeKGVisitor
  ├── test_exclusions.py    # Directory exclusion
  └── test_index.py         # SemanticIndex
```

---

## Data Flow

```
.py files
  ↓ iter_python_files(exclude=…)
filtered files
  ↓ extract_repo() — 3 AST passes
(nodes, edges)            Pass 1: CONTAINS/IMPORTS/INHERITS
                          Pass 2: CALLS (sym: stubs)
                          Pass 3: READS/WRITES/ATTR_ACCESS
  ↓ GraphStore.write()
.pycodekg/graph.sqlite      authoritative, canonical
  ↓ resolve_symbols()
RESOLVES_TO edges         sym: → fn:/cls:/m: defs
  ↓ SemanticIndex.build()
.pycodekg/lancedb           derived, disposable
  ↓ PyCodeKG.query() / .pack()
semantic seeds + structural BFS
  ↓ rank + dedupe
QueryResult / SnippetPack
  ↓
  ├→ Streamlit (pycodekg viz)
  ├→ 3D visualizer (pycodekg viz3d)
  ├→ Analyzer (pycodekg analyze)
  └→ MCP server (pycodekg-mcp)
```

---

## Dependencies

### Core
- `lancedb ≥ 0.29.0` — vector database
- `sentence-transformers ≥ 2.7.0` — embedder
- `numpy ≥ 1.24.0` — vector ops
- `streamlit ≥ 1.35.0` — web app
- `pyvis ≥ 0.3.2` — 2D graph viz
- `pandas ≥ 2.0.0` — tables
- `rich ≥ 14.0.0` — terminal output
- `click ≥ 8.1.0` — CLI
- `ast`, `sqlite3` (stdlib)

### Optional: viz3d
- Consumers: `pip install 'pycode-kg[viz3d] @ git+https://github.com/Flux-Frontiers/pycode_kg.git'`
- Local dev: `poetry install --with viz3d`
- `pyvista ≥ 0.44.0`, `pyvistaqt ≥ 0.11.0`, `PyQt5 ≥ 5.15.0`, `param ≥ 2.0.0`, `markdown ≥ 3.6`, `trame-vtk ≥ 2.0.0`

**Python ≥ 3.12, < 3.13**
