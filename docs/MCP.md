# PyCodeKG MCP Reference

**Tool reference and query strategy for the PyCodeKG MCP server**

*Author: Eric G. Suchanek, PhD*

---

## Overview

PyCodeKG ships a built-in MCP server (`pycodekg mcp`) that exposes the full hybrid query and snippet-pack pipeline as structured tools consumable by any MCP-compatible AI agent — Claude Code, Claude Desktop, Cursor, Continue, GitHub Copilot, or Kilo Code.

Once configured, the agent gains nineteen tools, grouped by purpose:

**Discovery & exploration**

| Tool | Purpose |
|---|---|
| `graph_stats()` | Codebase size and shape — good first call |
| `query_codebase(q)` | Semantic + structural graph exploration |
| `pack_snippets(q)` | Source-grounded code snippets for implementation detail |
| `get_node(node_id, include_edges)` | Single node metadata; optionally returns immediate neighborhood |
| `list_nodes(module_path, kind)` | List nodes filtered by module path prefix and/or kind |
| `find_node(name, kind)` | Search nodes by (partial) name when you don't know the stable ID |
| `find_definition_at(file, line)` | Reverse-lookup the node spanning a `file:line` location |

**Relationships & analysis**

| Tool | Purpose |
|---|---|
| `callers(node_id, rel)` | Precise fan-in lookup — resolves through `sym:` stubs |
| `explain(node_id)` | Natural-language explanation: role, docstring, callers, callees |
| `analyze_repo()` | Full architectural analysis: complexity, coupling, coverage, orphans |

**Centrality & ranking**

| Tool | Purpose |
|---|---|
| `centrality(top, kinds, group_by)` | SIR-weighted PageRank — most structurally important nodes/modules |
| `bridge_centrality(top, include_imports)` | Module connectivity — orchestrator/hub identification |
| `framework_nodes(top)` | Hub modules combining high SIR + high connectivity |
| `rank_nodes(top, rels, persist_metric, exclude_tests)` | Global CodeRank PageRank with optional persistence |
| `query_ranked(q, mode, k, top, rels, radius, exclude_tests)` | Query + hybrid/PPR ranking with explainability |
| `explain_rank(node_id, q)` | Explain a node's CodeRank score components |

**Temporal snapshots**

| Tool | Purpose |
|---|---|
| `snapshot_list(limit, branch)` | List saved codebase snapshots in reverse chronological order |
| `snapshot_show(key)` | Full metrics for a specific snapshot (or `"latest"`) |
| `snapshot_diff(key_a, key_b)` | Compare two snapshots side-by-side with computed deltas |

> **Setup is covered separately.** For installing `pycode-kg`, building the graph, and configuring Claude Code / Claude Desktop / Kilo Code / GitHub Copilot / Cline, see **[INSTALLATION.md](INSTALLATION.md)**. This document picks up *after* the server is running.

---

## Smoke Test

Verify the pipeline end-to-end before wiring the server into an agent:

```bash
# Sample query against the built graph
pycodekg query "module structure"
```

Or call PyCodeKG directly from Python:

```bash
poetry run python -c "
from pycode_kg import PyCodeKG
import json
kg = PyCodeKG(repo_root='.', db_path='.pycodekg/graph.sqlite', vectors_path='.pycodekg/vectors.sqlite')
print(json.dumps(kg.stats(), indent=2))
"
```

Expected output shape:

```json
{
  "total_nodes": 412,
  "total_edges": 1087,
  "node_counts": { "module": 18, "class": 34, "function": 201, "method": 143 },
  "edge_counts": { "CONTAINS": 378, "CALLS": 512, "IMPORTS": 147, "INHERITS": 50 },
  "db_path": ".pycodekg/graph.sqlite"
}
```

If this succeeds, the MCP server will work correctly.

---

## Tool Reference

### `graph_stats()`

Return node and edge counts broken down by kind and relation.

**When to use:** First call in any session — understand the codebase size and shape before querying.

**Parameters:** None.

**Returns:**

```json
{
  "total_nodes": 412,
  "total_edges": 1087,
  "node_counts": {
    "module": 18, "class": 34, "function": 201, "method": 143, "symbol": 16
  },
  "edge_counts": {
    "CONTAINS": 378, "CALLS": 512, "IMPORTS": 147, "INHERITS": 50
  },
  "db_path": ".pycodekg/graph.sqlite"
}
```

---

### `query_codebase(q, k, hop, rels, include_symbols, max_nodes, min_score, max_per_module)`

Hybrid semantic + structural query. Returns ranked nodes and edges as JSON.

**When to use:** Exploring the graph — finding what classes, functions, and modules are relevant to a topic, understanding call relationships, tracing imports.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | `str` | — | Natural-language query |
| `k` | `int` | `8` | Semantic seed count (top-K from vector search) |
| `hop` | `int` | `1` | Graph expansion hops from each seed |
| `rels` | `str` | `"CONTAINS,CALLS,IMPORTS,INHERITS"` | Comma-separated edge types to follow |
| `include_symbols` | `bool` | `false` | Include low-level `sym:` nodes |
| `max_nodes` | `int` | `25` | Maximum nodes to return |
| `min_score` | `float` | `0.0` | Minimum seed score (`score = 1 - distance`, clamped to `[0,1]`) |
| `max_per_module` | `int` | `0` | Maximum returned nodes per module (`0` disables the cap) |

**Returns:** JSON with keys: `query`, `seeds`, `expanded_nodes`, `returned_nodes`, `hop`, `rels`, `nodes`, `edges`.

---

### `pack_snippets(q, k, hop, rels, include_symbols, context, max_lines, max_nodes, min_score, max_per_module)`

Hybrid query + source-grounded snippet extraction. Returns a Markdown context pack.

**When to use:** Any time you need to read actual source code — understanding an implementation, debugging, writing tests, reviewing logic. **Prefer this over `query_codebase` when implementation details matter.**

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | `str` | — | Natural-language query |
| `k` | `int` | `8` | Semantic seed count |
| `hop` | `int` | `1` | Graph expansion hops |
| `rels` | `str` | `"CONTAINS,CALLS,IMPORTS,INHERITS"` | Edge types to follow |
| `include_symbols` | `bool` | `false` | Include symbol nodes |
| `context` | `int` | `5` | Extra context lines around each definition |
| `max_lines` | `int` | `160` | Maximum lines per snippet block |
| `max_nodes` | `int` | `50` | Maximum nodes in the pack |
| `min_score` | `float` | `0.0` | Minimum seed score (`score = 1 - distance`, clamped to `[0,1]`) |
| `max_per_module` | `int` | `0` | Maximum returned nodes per module (`0` disables the cap) |

**Returns:** Markdown string with ranked, deduplicated code snippets and line numbers.

---

### `get_node(node_id, include_edges)`

Fetch a single node by its stable ID, optionally including its immediate neighborhood.

**When to use:** You have a node ID from a previous query result and want its full metadata. Pass `include_edges=True` to get outgoing edges and incoming callers in one call, avoiding a separate `callers()` round-trip.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `node_id` | `str` | — | Stable node ID, e.g. `fn:src/auth/jwt.py:JWTValidator.validate` |
| `include_edges` | `bool` | `false` | If `true`, attach `outgoing_edges` (by relation type) and `incoming_calls` |

**Node ID format:** `<kind>:<module_path>:<qualname>`

| Prefix | Kind |
|---|---|
| `mod:` | module |
| `cls:` | class |
| `fn:` | function / method |
| `sym:` | unresolved external symbol |

**Returns:** JSON object with all node fields, or `{"error": "Node not found: '...'"}`.\
When `include_edges=True`: also includes `outgoing_edges` (dict keyed by relation type) and `incoming_calls` (list of caller node dicts).

---

### `list_nodes(module_path, kind)`

List nodes filtered by module path prefix and/or kind.

**When to use:** Enumerating the contents (classes, functions) of a specific module before inspecting individual nodes with `get_node`.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `module_path` | `str` | `""` | Module path prefix filter |
| `kind` | `str` | `""` | Node kind filter (e.g., `class`, `function`) |

**Returns:** JSON array of matching node dicts.

---

### `find_node(name, kind)`

Search graph nodes by name (or qualname) without knowing the full stable ID.

**When to use:** You saw a function or class name in a traceback, log line, or user question and don't yet have its node ID. Once you have the ID, pass it to `get_node`, `explain`, or `callers`.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | — | Function, method, or class name. Case-insensitive match against `name` and `qualname` |
| `kind` | `str` | `""` | Optional kind filter: `module` / `class` / `function` / `method`. Empty matches all |

**Returns:** JSON array of matching node dicts (`id`, `name`, `qualname`, `kind`, `module_path`, `lineno`, truncated `docstring`). Empty array when no match.

---

### `find_definition_at(file, line)`

Reverse-resolve a `(file, line)` pair to the innermost node spanning that location.

**When to use:** You're reading a file in an IDE and want to understand the symbol at a specific line without manually constructing a node ID. Returns the same Markdown report as `explain()`.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `file` | `str` | Module path as stored in the graph, e.g. `src/pycode_kg/store.py`. Leading `./` is stripped |
| `line` | `int` | 1-indexed line number within the file |

**Returns:** Markdown explanation from `explain()` for the innermost function / method / class whose `lineno ≤ line ≤ end_lineno`, falling back to the module node when no narrower match exists. Informative error if no node spans the location.

---

### `callers(node_id, rel)`

Find all callers of a specific node by inverting a relation — fan-in analysis.

**When to use:** Finding all callers of a specific function/method/class. More precise than `query_codebase` for this use case because it resolves cross-module callers through `sym:` import stubs.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `node_id` | `str` | — | Stable node ID, e.g. `fn:src/auth/jwt.py:JWTValidator.validate` |
| `rel` | `str` | `"CALLS"` | Relation type to invert |

**Returns:** JSON with `node_id`, `rel`, `caller_count`, `callers` (list of node dicts).

**Example return shape:**

```json
{
  "node_id": "fn:src/pycode_kg/store.py:GraphStore.expand",
  "rel": "CALLS",
  "caller_count": 7,
  "callers": [
    { "id": "m:src/pycode_kg/kg.py:PyCodeKG.query", "kind": "method", ... }
  ]
}
```

> **Note:** `sym:` nodes are resolved automatically — callers from other modules that import the target function are included even when they reference it via an alias.

---

### `explain(node_id)`

Return a natural-language Markdown explanation of a single code node.

**When to use:** You want to understand what a specific function, method, or class does — its role, who calls it, what it calls — without reading the raw source. Use as the first step when a user asks about a specific node before reaching for `pack_snippets`.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `node_id` | `str` | Stable node ID, e.g. `fn:src/pycode_kg/store.py:GraphStore.expand` |

**Returns:** Markdown report with: kind and qualified name, module path and line range, full docstring, list of callers (top 10), list of callees, and a role assessment (high-value / utility / orphaned) based on call count.

---

### `analyze_repo()`

Run a full nine-phase architectural analysis of the entire codebase.

**When to use:** When you want a comprehensive health check or architectural overview — complexity hotspots, high fan-out functions, module coupling, circular dependencies, critical call paths, public API surface, docstring coverage, code quality issues, and orphaned code.

**Parameters:** None.

**Returns:** Structured Markdown with sections for: baseline metrics, complexity hotspots, high fan-out functions, module architecture, critical paths, public API surface, docstring coverage, issues and strengths.

---

### `centrality(top, kinds, group_by)`

Run Structural Importance Ranking (SIR) — a deterministic weighted PageRank over the `sym`-resolved call graph.

**When to use:** Identify the most structurally critical nodes or modules — high-leverage refactor targets, candidates for tighter test coverage, the de-facto "core" of the codebase. Edge weights favor `CALLS` > `INHERITS` > `IMPORTS` > `CONTAINS`, with cross-module amplification and a private-symbol penalty.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `top` | `int` | `20` | Maximum ranked entries to return |
| `kinds` | `str` | `""` | Comma-separated kinds: `module,class,function,method`. Empty = all. Ignored when `group_by="module"` |
| `group_by` | `str` | `"node"` | `"node"` for individual rankings; `"module"` aggregates per module (class nodes ×1.2) |

**Returns:** Markdown ranking table with score, inbound edge count, and cross-module inbound count.

---

### `bridge_centrality(top, include_imports)`

Compute module connectivity — how many unique modules each module interacts with. Replaces betweenness centrality (meaningless when inter-module edges are zero).

**When to use:** Find orchestrator and hub modules in well-modularized codebases. Connectivity score = (unique callers + unique callees) / 30 + frequency / 50. Persists scores to the `centrality_scores` table for `framework_nodes()`.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `top` | `int` | `20` | Number of top connectivity modules to return |
| `include_imports` | `bool` | `true` | Include `IMPORTS` edges in the connectivity calculation |

**Returns:** Markdown ranking table of modules by connectivity score.

---

### `framework_nodes(top)`

Identify framework-like (hub) modules using `0.6 × normalized SIR + 0.4 × normalized connectivity`. Auto-runs `centrality()` and `bridge_centrality()` on first call if not already persisted.

**When to use:** Find modules that are *both* structurally central *and* highly connected — architecturally critical hubs (orchestrators, framework cores) rather than just popular utilities.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `top` | `int` | `20` | Number of top framework-like modules to return |

**Returns:** Markdown ranking table of framework nodes with composite score.

---

### `rank_nodes(top, rels, persist_metric, exclude_tests)`

Compute global weighted CodeRank (PageRank) over the repository graph.

**When to use:** Independent CodeRank scoring with persistence — useful for periodic baseline measurements, dashboards, or feeding ranking metrics into other tools. Default relation weights: `CALLS=1.0, IMPORTS=0.9, INHERITS=0.75`.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `top` | `int` | `25` | Number of top-ranked nodes to return |
| `rels` | `str` | `"CALLS,IMPORTS,INHERITS"` | Comma-separated relations to include in the graph |
| `persist_metric` | `str` | `""` | If non-empty, persist scores to `node_metrics` under this metric name (e.g. `"coderank_global"`) |
| `exclude_tests` | `bool` | `true` | Exclude test-path nodes from the graph |

**Returns:** JSON array of ranked node dicts: `node_id`, `score`, `top_pct` (e.g. `"top 0.5%"`), `kind`, `qualname`, `module_path`, `rank`.

---

### `query_ranked(q, mode, k, top, rels, radius, exclude_tests)`

Rank query results using CodeRank-enhanced hybrid or personalized PageRank — a more explainable alternative to `query_codebase` when you care *why* a result ranked highly.

**When to use:** Search where ranking transparency matters. Two modes:

- `hybrid` (default): `0.60 × semantic + 0.25 × centrality + 0.15 × proximity`
- `ppr`: `0.70 × personalized PageRank + 0.30 × semantic`

Each result includes a `why` string explaining the score components. `sym:` stub nodes are always excluded.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | `str` | — | Natural-language query |
| `mode` | `str` | `"hybrid"` | `"hybrid"` or `"ppr"` |
| `k` | `int` | `8` | Semantic seed count |
| `top` | `int` | `25` | Maximum ranked results to return |
| `rels` | `str` | `"CALLS,IMPORTS,INHERITS"` | Relations to include in the local graph |
| `radius` | `int` | `2` | Graph expansion radius around seeds |
| `exclude_tests` | `bool` | `true` | Exclude test-path nodes |

**Returns:** JSON array of ranked result dicts with score components and `why` explanation strings.

---

### `explain_rank(node_id, q)`

Explain the CodeRank score components for a specific node.

**When to use:** A node turned up in a ranked result and you want to understand *why* — how many nodes call/import/inherit from it, its global CodeRank, and (with `q`) its semantic relevance and proximity to the query seed set.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `node_id` | `str` | — | Stable node identifier, e.g. `fn:src/pycode_kg/store.py:GraphStore.expand` |
| `q` | `str` | `""` | Optional query. When provided, semantic score and proximity to the seed set are included |

**Returns:** Markdown report of the node's rank components.

---

### `snapshot_list(limit, branch)`

List saved temporal snapshots of codebase metrics in reverse chronological order.

**When to use:** Tracking how the codebase has grown over time — node/edge counts, docstring coverage changes, critical issue trends. Returns the `key` values needed for `snapshot_show` and `snapshot_diff`.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | `int` | `10` | Maximum snapshots to return; pass `0` for all |
| `branch` | `str` | `""` | Filter to snapshots from a specific branch; omit or pass `""` for all |

**Returns:** JSON array of snapshot metadata (key, branch, timestamp, version, key metrics, deltas vs. previous).

---

### `snapshot_show(key)`

Show full details of a specific codebase metrics snapshot.

**When to use:** Inspecting the state of the codebase at a specific snapshot — full node/edge counts, docstring coverage, complexity hotspots, and deltas vs. both the previous and baseline snapshots.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `key` | `str` | `"latest"` | Snapshot key — tree hash or `"latest"` for the most recent |

**Returns:** JSON object with full `SnapshotMetrics`, top complexity hotspots, and deltas vs. previous and baseline.

> **Legacy note:** if an older snapshot file does not contain persisted deltas, PyCodeKG backfills `vs_previous` and `vs_baseline` from manifest chronology at load time.

---

### `snapshot_diff(key_a, key_b)`

Compare two codebase metric snapshots side-by-side.

**When to use:** Quantifying the impact of a refactor, release, or sprint — how many nodes were added, did coverage improve, did critical issues increase?

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `key_a` | `str` | First (older) snapshot key (tree hash) |
| `key_b` | `str` | Second (newer) snapshot key (tree hash) |

**Returns:** JSON with keys `a` (metrics for `key_a`), `b` (metrics for `key_b`), and `delta` (b − a) for nodes, edges, coverage, and critical issues.

**Typical workflow:**

```
1. snapshot_list()                         → discover available snapshot keys
2. snapshot_diff("abc1234", "def5678")     → compare two points in time
```

---

## Query Strategy Guide

### Choosing `k` and `hop`

| Goal | Recommended settings |
|---|---|
| Narrow, precise lookup | `k=4, hop=0` — seeds only, no expansion |
| Standard exploration | `k=8, hop=1` — default; good for most queries |
| Broad context sweep | `k=12, hop=2` — pulls in more of the call graph |
| Deep dependency trace | `k=8, hop=2, rels="CALLS,IMPORTS"` — follow execution paths |

Higher `hop` values expand the result set geometrically. Use `max_nodes` in `pack_snippets` to keep output manageable.

### Choosing `rels`

| Relation | Meaning | When to include |
|---|---|---|
| `CONTAINS` | Module/class contains a definition | Almost always — provides structural context |
| `CALLS` | Function A calls function B | Tracing execution flow, finding callers/callees |
| `IMPORTS` | Module A imports from module B | Dependency analysis |
| `INHERITS` | Class A inherits from class B | OOP hierarchy exploration |

### Typical agent workflow

```
1. graph_stats()
   → understand codebase size and shape

2. query_codebase("authentication flow", k=8, hop=1)
   → identify relevant classes and functions, note their IDs

3. explain("cls:src/auth/jwt.py:JWTValidator")
   → natural-language orientation before reading source

4. pack_snippets("JWT token validation", k=6, hop=1)
   → read the actual implementation

5. get_node("fn:src/auth/jwt.py:JWTValidator.validate", include_edges=True)
   → fetch node metadata + outgoing edges + incoming callers in one call

6. pack_snippets("JWT token validation error handling", k=4, hop=2, rels="CALLS")
   → follow the call graph deeper into error paths

7. snapshot_list()
   → review how the codebase has evolved over time
   snapshot_diff("abc1234", "def5678")
   → compare metrics between two commits
```

### When to reach for the ranking tools

| Situation | Tool |
|---|---|
| User asked about a name from a traceback or chat — no node ID | `find_node(name)` |
| User pointed at a file and a line number in their editor | `find_definition_at(file, line)` |
| You need to know "what's actually important in this codebase?" | `centrality()` or `framework_nodes()` |
| You need explainable search results with score components | `query_ranked(q)` instead of `query_codebase(q)` |
| A ranked result surprised you — why did this node rank so high? | `explain_rank(node_id, q)` |
| You want a persisted CodeRank baseline for dashboards / regression checks | `rank_nodes(persist_metric="coderank_global")` |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Empty results from `query_codebase` | sqlite-vec index missing or stale | `pycodekg build-index --wipe` |
| Node IDs in results don't resolve with `get_node` | Graph rebuilt since last query | Rebuild both SQLite and LanceDB; restart the MCP server |
| `RuntimeError: PyCodeKG not initialised` | Server called without `main()` | Always start via `pycodekg mcp` CLI |
| Snippets show wrong line numbers | Source files changed since build | `pycodekg build-sqlite --wipe` |
| MCP server not appearing in agent | Wrong/relative paths in MCP config, or agent not restarted | See [INSTALLATION.md § MCP Server Setup](INSTALLATION.md#mcp-server-setup) — all paths must be absolute |
| `pycodekg` command not found | Package not installed or venv not active | `poetry install`, or use absolute venv path from `poetry env info --path` |

For installation, build, and per-agent config issues see [INSTALLATION.md](INSTALLATION.md).

---

## Summary

| Concern | Answer |
|---|---|
| What does the MCP server expose? | 19 tools across discovery (`graph_stats`, `query_codebase`, `pack_snippets`, `get_node`, `list_nodes`, `find_node`, `find_definition_at`), relationships (`callers`, `explain`, `analyze_repo`), centrality & ranking (`centrality`, `bridge_centrality`, `framework_nodes`, `rank_nodes`, `query_ranked`, `explain_rank`), and snapshots (`snapshot_list`, `snapshot_show`, `snapshot_diff`) |
| What must exist before starting? | `.pycodekg/graph.sqlite` + `.pycodekg/lancedb/` directory |
| How do I build those? | `pycodekg build` (or `build-sqlite` then `build-index`) — see [INSTALLATION.md](INSTALLATION.md) |
| Is the server stateful? | Yes — one `PyCodeKG` instance per server process |
| Can it modify the graph? | No — strictly read-only |
| Which tool should I call first? | `graph_stats()` for orientation |
| How do I automate setup? | One-line installer or `/setup-mcp` — see [INSTALLATION.md](INSTALLATION.md) |
