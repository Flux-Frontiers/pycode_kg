# Release Notes — v0.19.0

> Released: 2026-05-02

### Added

- **`src/pycode_kg/explain.py` — shared `render_explain()` presenter** — single source of truth for the Markdown explanation rendered by the `pycodekg explain` CLI and the MCP `explain` tool. Both surfaces previously rendered independently and had drifted: the MCP version used relative thresholds (top-5%/2%) while the CLI used hard-coded `50`/`10`, and only the MCP version had the kind-aware role labels and orchestrator branch. Centralizing prevents future drift; the footer call-to-action is parameterized so MCP shows `pack_snippets()` and CLI shows `pycodekg pack`.
- **`list_nodes(include_symbols=False)` parameter** — `mcp__pycodekg__list_nodes` now excludes `sym:` import-stub nodes by default; pass `include_symbols=True` to restore the previous noisy output. Module docstring and `FastMCP` instructions block updated to match.
- **`tests/test_explain.py`** — six tests covering the presenter: not-found header, class-aware role labels (regression guard for the "Utility function" misclassification), zero-caller orphan branch, protocol-method dunder branch, parameterized footer hint, and standard-section smoke test.
- **`tests/test_module_coupling.py`** — three regression tests for `PyCodeKGAnalyzer._analyze_module_coupling` cohesion calculation: a leaf entry-point module must score ~0, a widely-imported module must score high, and the formula must match the documented `incoming / (incoming + outgoing + 1)`.

### Changed

- **`framework_nodes()` — module-only ranking with corrected key-space join** — the tool advertises "Framework-like Modules" but previously mixed two key spaces in its scoring: `sir_pagerank` rows are keyed by typed node IDs (`mod:...`, `m:...:method`, `fn:...:func`) while `module_connectivity` rows are keyed by bare paths (`src/...`). The accidental union let methods like `GraphStore.con` and functions like `parse_args` appear alongside genuine modules. Now aggregates node-level SIR up to module level via the existing `aggregate_module_scores()`, joins on bare paths, and emits `(mod:<path>, score, <path>)` tuples — guaranteed module-only output. Top-of-list is now `store.py`, `viz3d.py`, `module/base.py`, `snapshots.py`, `visitor.py`, `mcp_server.py`.
- **Concern-based hybrid ranking — decoupled display label from embedding query** — concern entries in `_analyze_concerns` are now `(label, query)` tuples. The "graph traversal node edge" concern previously surfaced 3-D layout `compute()` methods (`FunnelLayout.compute`, `AlliumLayout.compute`, `Layout3D.compute`) because their docstrings happen to say "nodes" / "edges" / "graph"; the embedding query was a pure noun phrase with no verb anchor. The query is now `"graph expansion traverse callers neighbors edges from seeds"` — verb anchors that 3-D layout code does not contain — while the section heading in the report stays the original short label. New top results: `GraphStore.expand`, `PyCodeKGVisitor._add_edge`, `GraphStore.callers_of`, `induce_query_subgraph`, `query_codebase` — actual graph-traversal/expansion code.

### Fixed

- **`explain()` — kind-aware role labels** — a class with N callers was previously labeled a "Utility function" regardless of node kind. The role assessment now branches on `node.get("kind")` to pick a noun (`class` / `module` / `function`) and verb (`Constructed` / `Imported` / `Called`). `GraphStore` (9 callers) now correctly reads as **"Important class: Constructed 9 times (≥9 = top 2% of this codebase)"** instead of "Utility function: Called 9 time(s)…". Both the CLI and MCP surfaces inherit the fix via the new shared presenter.
- **`explain()` — off-by-one in threshold comparisons** — the "High-value" and "Important" branches used `>` instead of `>=`, so a node sitting exactly at the top-5% / top-2% boundary fell through to the "Utility" branch. Now uses `>=`. Surfaced by GPT-5.4's PyCodeKG assessment (2026-05-02).
- **Module cohesion formula was inverted** — `PyCodeKGAnalyzer._analyze_module_coupling` documented `cohesion = incoming / (incoming + outgoing + 1)` ("higher = more internally focused") but the code used `outgoing` in the numerator, which inverted the meaning. A leaf entry-point like `mcp_server.py` (`incoming=0, outgoing=3`) read as `0.75` cohesion when it should read `0.00`. After the fix, the top-cohesion modules in this repo are `cli/main.py` (0.94), `index.py` and `snapshots.py` (0.86), and `store.py` (0.77) — the modules that everything depends on but that do not sprawl outward, which is what cohesion is supposed to measure.
- **Stale `query`/`pack` CLI flags in docs and tasks** — `pycodekg query` and `pycodekg pack` take the query string as a positional `QUERY` argument, not `--q`, and they accept `--k` for top-k, not `--top` (which is a `centrality`-only flag). Five files referenced the old forms: `.claude/commands/setup-pycodekg-mcp.md`, `.claude/skills/pycodekg/references/installation.md`, `.vscode/tasks.json`, `article/pycode_kg_medium.md`, and `docs/pycode_kg_workflow.md`. All updated to match the actual signatures in `cli/cmd_query.py`.

### Removed

- **Duplicated `_explain_node()` from `cli/cmd_explain.py` and the inlined explain-rendering block from `mcp_server.py`** — ~322 lines of duplicated Markdown-rendering and role-classification logic, replaced by single-line delegations into `pycode_kg.explain.render_explain()`.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
