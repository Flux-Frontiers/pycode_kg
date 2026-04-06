# rerank_mode Comparison: legacy vs semantic vs hybrid

**Date:** 2026-03-09
**Index:** all-MiniLM-L6-v2, 5301 nodes / 5222 edges
**Scope:** `query_codebase` with `paths="src/pycode_kg"` across three representative queries

---

## How Each Mode Works

### `legacy` (pre-reranking behavior)

Sort key: `(best_hop, vector_distance, kind_priority, node_id)`

Hop distance is the primary sort dimension. Every node at hop=0 (direct seed) ranks above every node at hop=1 (graph expansion), regardless of how semantically relevant the hop=1 node is. Within a hop band, lower vector distance wins. The semantic score is effectively only a tiebreaker within the same hop.

**Problem:** A highly relevant node reached via 1-hop expansion is buried below a weakly-related but directly-seeded node.

---

### `semantic` (score-first, hop second)

Sort key: `(-semantic_score, best_hop, kind_priority, node_id)`

Pure vector similarity score wins. Nodes sharing the same `via_seed` (expanded neighbors) inherit the seed's score, so close neighbors of a strong seed can rise above weaker direct seeds. Hop is only a tiebreaker for equal-scoring nodes.

**Problem:** Nodes whose names or docstrings contain exact query terms but have weak embeddings are missed. `_snapshot_freshness` (zero semantic score, but literally named for "freshness") is pushed to position 10 on a "snapshot freshness comparison" query.

---

### `hybrid` (default)

Sort key: `(-(0.7 × semantic + 0.3 × lexical), best_hop, kind_priority, node_id)`

Blends vector similarity with lexical overlap: query tokens matched against node `name + qualname + module_path + docstring`. A node with zero semantic score but strong name/docstring match can still rank highly. Weights default to 70% semantic / 30% lexical.

**Problem:** Cannot rescue a bad seed set. If the right node was not in the top-k vector results, no reranking promotes it. Lexical scoring also does not understand synonyms.

---

## Test Results

### Query 1: `"snapshot freshness comparison"` (hop=1, k=8, max_nodes=10)

| Rank | legacy | semantic | hybrid |
|------|--------|----------|--------|
| 1 | `SnapshotManager.diff_snapshots` (sem=0.127, hop=0) | `SnapshotManager.diff_snapshots` (sem=0.127) | `SnapshotManager` class (hyb=0.234, lex=0.667) |
| 2 | `snapshot_diff` MCP (sem=0.125, hop=0) | `SnapshotManager._compute_delta` (sem=0.127, hop=1) | `mcp_server` module (hyb=0.231, lex=0.667) |
| 3 | `SnapshotManager.save_snapshot` (sem=0.048, hop=0) | `SnapshotManager.load_snapshot` (sem=0.127, hop=1) | `SnapshotManager.get_baseline` (hyb=0.231, lex=0.667) |
| 4 | `snapshot_list` MCP (sem=0.044, hop=0) | `snapshot_diff` MCP (sem=0.125, hop=0) | `_snapshot_freshness` **(hyb=0.200, lex=0.667)** |
| 5 | `SnapshotManager.get_baseline` (sem=0.044, hop=0) | `SnapshotManager.save_snapshot` (sem=0.048, hop=0) | `SnapshotManager.diff_snapshots` (hyb=0.189) |
| 7 | `_snapshot_freshness` (sem=0.0, hop=0) | — | — |
| 9 | `SnapshotManager._compute_delta` (hop=1) | — | — |

**Key observations:**
- **legacy:** `_compute_delta` is buried at rank 9 because it's a hop=1 node — despite being reached via the strongest seed. `_snapshot_freshness` appears at rank 7 with zero semantic score, kept only because it was a direct seed.
- **semantic:** Promotes `_compute_delta` to rank 2 (inherits parent seed's 0.127 score). But `_snapshot_freshness` falls to rank 10 — semantic score is zero because MiniLM doesn't associate "freshness" with "compare node count against DB."
- **hybrid:** `_snapshot_freshness` rises to rank 4 with `lexical=0.667` — it contains "snapshot" and "freshness" in its name, and "comparison" in its docstring. This is the functionally correct result for this query. The `SnapshotManager` class also rises to #1 via lexical overlap on "snapshot"+"comparison" (docstring: "storage, retrieval, and **comparison**").

**Winner: hybrid** — surfaces `_snapshot_freshness` as a top result, which is exactly the function implementing freshness logic. Legacy and semantic both miss this.

---

### Query 2: `"missing_lineno_policy cap_or_skip fallback"` (hop=0, k=6)

All three modes returned identical node sets and identical ordering. All scores were `semantic=0.0, lexical=0.0`. Results included `_compute_span`, `_read_lines`, `LayoutNode.line_count`, `LayoutNode`, `_set_node_source_meta`, `PyCodeKG.__exit__` — none of which are the actual implementation site of `missing_lineno_policy`.

**Root cause:** `missing_lineno_policy` and `cap_or_skip` are parameter values stored only inside `PyCodeKG.pack_snippets` — not as standalone node names or docstrings. MiniLM cannot find them by embedding similarity, and the lexical scorer cannot find them because those strings do not appear in any node's `name`, `qualname`, or `module_path`.

**Finding:** All three modes fail equally on queries for internal parameter names that aren't surfaced in node metadata. The correct fix is either:
1. Use `hop=1` so `pack_snippets` (which does appear as a seed) expands to include its call graph
2. Query by concept: `"snippet extraction line metadata handling"` — which would seed on `pack_snippets` semantically

**Winner: tie (all fail)** — this is a seeding problem, not a reranking problem.

---

### Query 3: `"how does the graph get built from source code"` (hop=1, k=8, max_nodes=8)

| Rank | legacy | semantic | hybrid |
|------|--------|----------|--------|
| 1 | `graph` module (sem=0.242) | `graph` module (sem=0.242) | `CodeGraph` class (hyb=0.257) |
| 2 | `CodeGraph` class (sem=0.225) | `CodeGraph` class (sem=0.225) | `PyCodeKG` class (hyb=0.244) |
| 3 | `CodeGraph.__repr__` (sem=0.215) | `CodeGraph.edges` (sem=0.225, hop=1) | `graph` module (hyb=0.202) |
| 4 | `PyCodeKG.graph` (sem=0.206) | `CodeGraph.__repr__` (sem=0.215) | `CodeGraph.__init__` (hyb=0.201, lex=0.333) |
| 5 | `CodeGraph.nodes` (sem=0.191) | `PyCodeKG.graph` (sem=0.206) | `CodeGraph.edges` (hyb=0.191) |
| 6 | `CodeGraph.__init__` (sem=0.144) | `PyCodeKG.build_graph` (sem=0.206, hop=1) | `CodeGraph.__repr__` (hyb=0.184) |
| 7 | `ArchitectureAnalyzer._build_architecture_graph` | `PyCodeKG` class (sem=0.206, hop=1) | `PyCodeKG.graph` (hyb=0.177) |
| 8 | `CodeGraph.result` | `CodeGraph.nodes` (sem=0.191) | `PyCodeKG.build_graph` (hyb=0.177) |

**Key observations:**
- **legacy and semantic both rank `CodeGraph.__repr__` at position 3-4.** This is the developer repr string method — near-useless for "how does the graph get built." It ranks high only because it's a direct semantic seed.
- **hybrid demotes `CodeGraph.__repr__` to rank 6.** Its lexical overlap with the query ("graph" only, no "build"/"source"/"code") is weak. Hybrid redistributes budget to `PyCodeKG` class (+lexical from "code"+"kg"), `CodeGraph.__init__` (contains "graph"+"source" in docstring), and `build_graph` (literal "build"+"graph" in name).
- **`PyCodeKG` class** rises from rank 7 (semantic/legacy) to rank 2 (hybrid). Its docstring contains "builds", "source", "graph", "code" — strong lexical match.
- **`CodeGraph.__init__`** rises from rank 6 to rank 4 in hybrid — it's the constructor that sets up the graph extraction, directly answering "how does it get built."

**Winner: hybrid** — provides a noticeably more useful ranked list. Promotes `CodeGraph.__init__`, `PyCodeKG`, and `build_graph` while demoting the noise node `__repr__`.

---

## Summary Scorecard

| Query type | legacy | semantic | hybrid |
|------------|--------|----------|--------|
| Keyword in function name ("freshness") | miss at rank 7 | miss at rank 10 | **hit at rank 4** |
| Internal parameter name | all fail equally | all fail equally | all fail equally |
| Conceptual ("how does X work") | noise at rank 3 | noise at rank 3-4 | **noise demoted, better at top** |

---

## When to Use Each Mode

| Use case | Recommended mode |
|----------|-----------------|
| Default — best general quality | `hybrid` |
| Pure concept query, exact names irrelevant | `semantic` |
| Reproducing a previous result exactly | `legacy` |
| Debugging why a node ranked as it did | any mode + inspect `relevance` field |
| Benchmarking reranking against older baselines | `legacy` (stable ordering) |

---

## Known Limitation: Seeding Beats Reranking

The most important finding from Query 2: **reranking only reorders nodes that are already in the expanded set.** If the correct node wasn't among the top-k semantic seeds and isn't reachable via graph expansion from those seeds, no rerank mode can surface it.

Mitigations:
- Increase `k` (more seeds = wider candidate pool)
- Increase `hop` (deeper graph expansion)
- Rephrase query to use concepts that embed near the target node
- Use `get_node` or `callers` for precise lookups when the node ID is known

---

## Score Ranges Observed

Across all three queries, absolute semantic scores were low (max ~0.24). This is expected with MiniLM on a code-focused corpus — the embedding space is spread thin across a large vocabulary of identifiers. The lexical component provides meaningful signal precisely in the range where semantic fails (0.0–0.13), which is why hybrid consistently outperforms in practice.
