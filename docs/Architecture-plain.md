CodeKG Architecture - A Deterministic Knowledge Graph for Python Codebases

Version: 0.5.0
Author: Eric G. Suchanek, PhD

OVERVIEW

CodeKG constructs a deterministic, explainable knowledge graph from a Python codebase using static analysis. The graph captures structural relationships (definitions, calls, imports, inheritance) and data-flow relationships (reads, writes, attribute access) directly from the Python AST, stores them in SQLite, and augments retrieval with vector embeddings via LanceDB. Structure is treated as ground truth; semantic search is an acceleration layer. Every node and edge maps to a concrete file and line number.

The system ships with: a Python library with a layered class API, a Click-based CLI (codekg) with subcommands, a Streamlit web application (codekg viz) for 2D interactive exploration, a 3D PyVista visualizer (codekg viz3d) for immersive graph navigation, a thorough analysis tool (codekg analyze) for architectural insights, an MCP server (codekg-mcp) for AI agent integration, and a /setup-mcp Claude skill for automated MCP configuration.

DESIGN PRINCIPLES

Structure is authoritative. Semantics accelerate, never decide. Everything is traceable. Determinism over heuristics. Composable artifacts (SQLite + LanceDB + Markdown/JSON). Honest extraction - only what is explicitly visible in the AST; no inference, no guessing.

LAYERED ARCHITECTURE

The system is organized into focused layers, each independently testable and composable. CodeKG (orchestrator) owns CodeGraph (pure AST extraction), GraphStore (SQLite canonical store), and SemanticIndex (LanceDB vector index). The primitives layer in codekg.py is the locked v0 contract. The visitor.py module provides Pass 3 data-flow extraction via CodeKGVisitor. The config.py module provides directory exclusion configuration via load_exclude_dirs().

LAYER 1 - PRIMITIVES (codekg.py)

Node is a frozen dataclass with fields: id, kind, name, qualname, module_path, lineno, end_lineno, docstring. Edge is a frozen dataclass with fields: src, rel, dst, evidence. extract_repo(repo_root, exclude=None) performs three-pass AST extraction and returns (nodes, edges). iter_python_files(repo_root, exclude=None) yields .py files skipping SKIP_DIRS and any exclude directories.

Node kinds: module, class, function, method, symbol.

Edge relations by extraction pass:
Pass 1 (structure): CONTAINS (parent to child), IMPORTS (module dependency), INHERITS (class inheritance).
Pass 2 (call graph): CALLS (function/method calls; unresolved calls become sym: stub nodes).
Pass 3 (data-flow via CodeKGVisitor): READS (variable read), WRITES (variable write), ATTR_ACCESS (attribute access), DEPENDS_ON (placeholder for future control-flow).
Post-build: RESOLVES_TO (sym: stub to first-party fn:/cls:/m:/mod: definition, added by GraphStore.resolve_symbols()).

LAYER 1a - DATA-FLOW VISITOR (visitor.py)

CodeKGVisitor is an ast.NodeVisitor subclass implementing Pass 3 of the extraction pipeline. For each source file it emits data-flow edges. visit_FunctionDef and visit_AsyncFunctionDef emit CONTAINS edges. visit_Assign emits READS edges for right-hand-side variables and WRITES edges for targets. visit_Attribute emits ATTR_ACCESS edges when the object is a simple Name node. visit_Call emits READS edges for arguments. Every edge carries evidence (lineno, file) for traceability.

LAYER 1b - CONFIGURATION (config.py)

load_exclude_dirs(repo_root) reads the [tool.codekg].exclude list from pyproject.toml at the repository root. Returns a set of directory name strings to skip (e.g., old, vendor, generated). Returns an empty set if the section or key is absent, the file is missing, the TOML is invalid, or the value is not a list. CLI flags (--exclude-dir) are merged with the config-file set at build time.

LAYER 2 - CodeGraph (graph.py)

Pure AST extraction with a clean object interface. No I/O, no persistence. Accepts an optional exclude parameter (set of directory names) forwarded to extract_repo(). Lazy extraction: .nodes and .edges properties trigger extract() automatically on first access. extract(force=True) re-runs from scratch. result() returns the (nodes, edges) tuple. stats() returns counts by kind/relation.

LAYER 3 - GraphStore (store.py)

SQLite-backed authoritative store. No embeddings, no AST. Methods: write(nodes, edges, wipe=False) for upsert persistence, clear() to delete all data, node(id) to fetch a single node dict, query_nodes(kinds=, module=) for filtered lists, edges_within(node_ids) for edges with both endpoints in a set, expand(seed_ids, hop=1, rels=...) for BFS traversal returning Dict[id, ProvMeta], resolve_symbols() for post-build sym: stub resolution, callers_of(node_id, rel=CALLS) for two-phase reverse lookup (direct plus via sym: stubs), stats() for node/edge counts. ProvMeta contains best_hop (minimum hop from any seed) and via_seed (seed that yielded shortest path). Supports context manager.

LAYER 4 - SemanticIndex (index.py)

LanceDB-backed vector index. Derived from SQLite; disposable and rebuildable. Embedder is an abstract interface with embed_texts(texts) and embed_query(query) methods. SentenceTransformerEmbedder is the default implementation using sentence-transformers (model: BAAI/bge-small-en-v1.5). SeedHit is a dataclass with fields: id, kind, name, qualname, module_path, distance, rank. Index text format (stable): KIND, NAME, QUALNAME, MODULE, LINE, DOCSTRING.

ORCHESTRATOR - CodeKG (kg.py)

Top-level entry point owning all four layers with lazy initialization. The embedder and LanceDB connection are only created on first use. Methods: build(wipe=True) for the full pipeline, build_graph(wipe=True) for AST to SQLite, build_index(wipe=True) for SQLite to LanceDB, query(q, k=8, hop=1, min_score=0.0, max_per_module=None) returning QueryResult, pack(q, k=8, hop=1, min_score=0.0, max_per_module=None) returning SnippetPack with source snippets, callers(node_id, rel=CALLS) for two-phase fan-in lookup with import-aware stub disambiguation, stats() for store stats, node(id) to fetch a node dict. Supports context manager.

RESULT TYPES

BuildStats: repo_root, db_path, total_nodes, total_edges, node_counts dict, edge_counts dict, indexed_rows (None if not built), index_dim (None if not built). Methods: to_dict(), __str__().

QueryResult: query, seeds, expanded_nodes, returned_nodes, hop, rels, nodes list sorted by rank, edges list within the returned node set. Methods: to_dict(), to_json(), print_summary().

SnippetPack: extends QueryResult with source snippets. Each node dict may contain a snippet key with path, start, end, and text fields. Methods: to_dict(), to_json(), to_markdown(), save(path, fmt=md).

BUILD PIPELINE

Phase 1 - Static Analysis (AST to SQLite): Walk .py files skipping .venv, __pycache__, .git, and any configured exclude directories. Pass 1 extracts modules, classes, functions, methods, imports, and inheritance. Pass 2 extracts the call graph; unresolved calls become sym: stub nodes. Pass 3 emits data-flow edges via CodeKGVisitor (READS, WRITES, ATTR_ACCESS). Generate stable node IDs (mod:, cls:, fn:, m:, sym:) with evidence (lineno, expr, file). Persist to SQLite via upsert (idempotent). GraphStore.resolve_symbols() prefers exact qualified-name matches (including `src/` alias variants), then falls back to names and writes RESOLVES_TO edges with confidence metadata, enabling fan-in queries across module boundaries. Operation is idempotent.

Phase 2 - Semantic Indexing (SQLite to LanceDB): Read module, class, function, and method nodes from SQLite. Build canonical index text (name + qualname + module + docstring). Embed in batches via SentenceTransformerEmbedder. Upsert to LanceDB (delete-then-add per batch). The vector index is derived and disposable - rebuild from SQLite at any time.

HYBRID QUERY MODEL

query() and pack() execute in two phases. Phase 1 - Semantic Seeding: query string to embed to vector search to top-K SeedHit list (id, distance, rank). Phase 2 - Structural Expansion: seed IDs to GraphStore.expand(hop=N) to BFS over CONTAINS, CALLS, IMPORTS, and INHERITS edges, recording best_hop and via_seed for each reachable node.

RANKING AND DEDUPLICATION

Nodes are ranked deterministically by composite key: (best_hop, seed_distance, kind_priority, node_id). Kind priority: function=0, method=1, class=2, module=3, symbol=4. Deduplication in pack() only: compute source span per node, skip overlapping spans (2-line gap) in the same file, cap at max_nodes (default 50).

SNIPPET EXTRACTION

For each retained node: resolve module_path to absolute path (path-traversal safe via _safe_join), read file lines (cached per file), compute span using AST lineno/end_lineno plus/minus context lines (capped at max_lines), emit line-numbered text block. Module nodes show the top-of-file window.

INTERFACES

Streamlit Web App (codekg viz): Three tabs: Graph Browser (pyvis interactive graph, filter by kind or module, click for detail panels), Hybrid Query (NL query to semantic seeds to graph expansion to ranked results with graph/table/edge/JSON views), Snippet Pack (source-grounded snippets with Markdown and JSON download). Sidebar: Build Graph, Build Index, Build All controls. Reads CODEKG_DB and CODEKG_LANCEDB environment variables.

3D Visualizer (codekg viz3d): Optional PyVista/PyQt5 visualizer. Requires the viz3d dependency group (pyvista, pyvistaqt, PyQt5, param, markdown, trame-vtk). KGVisualizer is the param-reactive data model. MainWindow is the full Qt window with left control panel and right PyVista QtInteractor. DocstringPopup renders docstrings as HTML/Markdown. create_kg_visualization() renders the 3D scene with per-kind meshes and Bezier arc edges. Layouts: allium (hierarchical cluster, default), cake (layered by node kind). Right-click a node to highlight, focus camera, and show its docstring popup.

Thorough Analysis Tool (codekg analyze): CodeKGAnalyzer runs 7 analysis phases using the live knowledge graph: complexity hotspots (fan-in/fan-out), entry points (no callers), dead code candidates (unreachable), docstring coverage, module cohesion (internal coupling), module coupling (IMPORTS-based dependencies), and critical paths (deepest call chains). FunctionMetrics captures per-function fan-in, fan-out, line count, docstring, and risk level. ModuleMetrics captures per-module function/class counts, incoming/outgoing deps, and cohesion score. CallChain represents a critical path with chain, depth, and total callers. Outputs a Markdown report and a JSON snapshot.

MCP Server (codekg-mcp): Thin wrapper around CodeKG. Stateful (one CodeKG instance per server process). Read-only. Start: codekg-mcp --repo /path/to/repo [--db ...] [--lancedb ...] [--transport stdio|sse]. Tools: query_codebase(q, k, hop, rels, include_symbols, max_nodes, min_score, max_per_module) returning JSON, pack_snippets(q, k, hop, rels, context, max_lines, max_nodes, min_score, max_per_module) returning Markdown, callers(node_id, rel) returning JSON (with import-aware stub filtering), get_node(node_id) returning JSON, graph_stats() returning JSON, plus snapshot_list/snapshot_show/snapshot_diff for temporal metrics keyed by tree hash. MCP server is included in the standard install: pip install 'code-kg @ git+https://github.com/Flux-Frontiers/code_kg.git'.

/setup-mcp Claude Skill: Automates full MCP setup. Steps: resolve repo path, verify CodeKG installation, build SQLite graph, build LanceDB index, smoke-test pipeline, configure .mcp.json, .vscode/mcp.json, and claude_desktop_config.json.

DIRECTORY EXCLUSION

Exclude directories via pyproject.toml under [tool.codekg] exclude key (list of directory names), or via CLI --exclude-dir flag (repeatable). Both sources are merged at build time and apply to iter_python_files(), extract_repo(), CodeGraph, and CodeKG.

CLI ENTRY POINTS

Primary interface: codekg (the main Click CLI). Each subcommand is also available as a standalone script alias.

codekg build-sqlite (alias: codekg-build-sqlite): AST extraction to SQLite.
codekg build-lancedb (alias: codekg-build-lancedb): SQLite to LanceDB embeddings.
codekg build (alias: codekg-build): Full pipeline (SQLite + LanceDB), always wipes existing data.
codekg update (alias: codekg-update): Incremental upsert pipeline (SQLite + LanceDB), no wipe.
codekg query (alias: codekg-query): Hybrid query, text output.
codekg pack (alias: codekg-pack): Hybrid query + snippet pack.
codekg viz (alias: codekg-viz): Launch Streamlit 2D visualizer.
codekg viz3d (alias: codekg-viz3d): Launch 3D PyVista visualizer.
codekg analyze (alias: codekg-analyze): Thorough architectural analysis.
codekg mcp (alias: codekg-mcp): Start MCP server.

All subcommands live in src/code_kg/cli/. Shared options (repo path, db path, exclude dirs) live in cli/options.py.

SOURCE LAYOUT

src/code_kg/: codekg.py (locked v0 primitives), visitor.py (CodeKGVisitor, Pass 3 data-flow), config.py (load_exclude_dirs), graph.py (CodeGraph), store.py (GraphStore), index.py (SemanticIndex), kg.py (CodeKG orchestrator and result types), layout3d.py (3D layout algorithms), viz3d.py (3D PyVista/PyQt5 visualizer), codekg_thorough_analysis.py (CodeKGAnalyzer), app.py (Streamlit web app), mcp_server.py (MCP server), utils.py (shared utilities), cli/ (Click CLI subpackage: main.py, cmd_build.py, cmd_build_full.py, cmd_query.py, cmd_viz.py, cmd_analyze.py, cmd_mcp.py, options.py).

tests/: test_primitives.py (Node, Edge, extract_repo), test_graph.py (CodeGraph), test_store.py (GraphStore), test_kg.py (CodeKG and result types), test_visitor.py (CodeKGVisitor), test_exclusions.py (directory exclusion), test_index.py (SemanticIndex).

docs/: Architecture.md (full reference with images), Architecture-brief.md (condensed), Architecture-plain.md (this file), MCP.md (MCP server reference).

assets/: code_kg_arch_square-web.jpg, code_kg_arch_square.png, code_kg_arch_9x16.png, logo files (xs/sm/md/lg/xl).

DATA FLOW

.py files filtered by iter_python_files(exclude=...) to extract_repo() running three AST passes yielding (nodes, edges) with CONTAINS/IMPORTS/INHERITS from Pass 1, CALLS and sym: stubs from Pass 2, and READS/WRITES/ATTR_ACCESS from Pass 3 to GraphStore.write() persisting to .codekg/graph.sqlite (authoritative) to GraphStore.resolve_symbols() writing RESOLVES_TO edges (sym: to fn:/cls:/m:) to SemanticIndex.build() writing to .codekg/lancedb (derived, disposable) to CodeKG.query()/.pack() combining semantic seeds from LanceDB with structural BFS from SQLite to rank and dedupe to QueryResult/SnippetPack to Markdown/JSON output to Streamlit (codekg viz), 3D visualizer (codekg viz3d), thorough analyzer (codekg analyze), or MCP server (codekg-mcp).

DEPENDENCIES

Core (required): lancedb 0.29.0+, sentence-transformers 2.7.0+, numpy 1.24.0+, streamlit 1.35.0+, pyvis 0.3.2+, pandas 2.0.0+, rich 14.0.0+, click 8.1.0+, Python stdlib ast and sqlite3.

MCP server is included in the standard install (no extra needed). The mcp package (1.0.0+) is a core dependency.

Optional - 3D visualizer (poetry install --with viz3d): pyvista 0.44.0+, pyvistaqt 0.11.0+, PyQt5 5.15.0+, param 2.0.0+, markdown 3.6+, trame-vtk 2.0.0+.

Python 3.10 to 3.12 (exclusive of 3.13).
