> **Analysis Report Metadata**
> - **Generated:** 2026-08-11T23:27:37Z
> - **Version:** pycode-kg 0.22.0
> - **Commit:** a313fe2 (main)
> - **Platform:** macOS 27.0 | arm64 (arm) | turing | Python 3.12.13
> - **Graph:** 6221 nodes · 5858 edges (377 meaningful)
> - **Included directories:** src
> - **Excluded directories:** none
> - **Elapsed time:** 3s

# pycode_kg Analysis

**Generated:** 2026-08-11 23:27:37 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **pycode_kg** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
|----------------|-------|-------|
| [B] **Good** | **B** | 82 / 100 |

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| **Total Nodes** | 6221 |
| **Total Edges** | 5858 |
| **Modules** | 56 (of 56 total) |
| **Functions** | 145 |
| **Classes** | 30 |
| **Methods** | 146 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 2172 |
| CONTAINS | 321 |
| IMPORTS | 449 |
| ATTR_ACCESS | 2007 |
| INHERITS | 10 |

---

## Fan-In Ranking

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers |
|---|----------|--------|---------|
| 1 | `_get_kg()` | src/pycode_kg/mcp_server.py | **17** |
| 2 | `compute_coderank()` | src/pycode_kg/ranking/coderank.py | **7** |
| 3 | `_rewrap()` | src/pycode_kg/snapshots.py | **5** |
| 4 | `_add_edge()` | src/pycode_kg/visitor.py | **5** |
| 5 | `_get_node_id()` | src/pycode_kg/visitor.py | **5** |
| 6 | `_add_var_edge()` | src/pycode_kg/visitor.py | **5** |
| 7 | `extract()` | src/pycode_kg/graph.py | **4** |
| 8 | `_extract_reads()` | src/pycode_kg/visitor.py | **4** |
| 9 | `nodes()` | src/pycode_kg/graph.py | **4** |
| 10 | `FunctionMetrics()` | src/pycode_kg/pycodekg_thorough_analysis.py | **4** |
| 11 | `reset_camera()` | src/pycode_kg/viz3d.py | **4** |
| 12 | `_run_pipeline()` | src/pycode_kg/cli/cmd_build_full.py | **3** |
| 13 | `load_snapshots_timeline()` | src/pycode_kg/viz3d_timeline.py | **3** |
| 14 | `reset_actor_appearances()` | src/pycode_kg/viz3d.py | **3** |
| 15 | `_get_snapshot_mgr()` | src/pycode_kg/mcp_server.py | **3** |


**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:
- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.

| # | Function | Module | Calls | Type |
|---|----------|--------|-------|------|
| 1 | `init()` | src/pycode_kg/cli/cmd_init.py | **43** | Coordinator |

---

## Module Architecture

Top modules by dependency coupling and cohesion (showing up to 10 with activity).
Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.

| Module | Functions | Classes | Incoming | Outgoing | Cohesion |
|--------|-----------|---------|----------|----------|----------|
| `src/pycode_kg/viz3d.py` | 7 | 3 | 0 | 1 | 0.00 |
| `src/pycode_kg/pycodekg_thorough_analysis.py` | 5 | 4 | 4 | 1 | 0.67 |
| `src/pycode_kg/mcp_server.py` | 25 | 0 | 0 | 3 | 0.00 |
| `src/pycode_kg/snapshots.py` | 5 | 4 | 6 | 0 | 0.86 |
| `src/pycode_kg/visitor.py` | 1 | 1 | 1 | 1 | 0.33 |
| `src/pycode_kg/architecture.py` | 0 | 4 | 1 | 0 | 0.50 |
| `src/pycode_kg/app.py` | 14 | 0 | 0 | 2 | 0.00 |
| `src/pycode_kg/analysis/centrality.py` | 1 | 5 | 3 | 0 | 0.75 |
| `src/pycode_kg/ranking/coderank.py` | 12 | 1 | 1 | 0 | 0.50 |
| `src/pycode_kg/kg.py` | 0 | 1 | 6 | 4 | 0.55 |

---

## Key Call Chains

Deepest call chains in the codebase.

**Chain 1** (depth: 5)

```
from_dict → _rewrap → update → _run_pipeline → _banner
```

**Chain 2** (depth: 3)

```
_add_var_edge → _get_node_id → node_id
```

---

## Public API Surface

Identified public APIs (module-level functions with high usage).

| Function | Module | Fan-In | Type |
|----------|--------|--------|------|
| `SnapshotManager()` | src/pycode_kg/snapshots.py | 9 | class |
| `PyCodeKG()` | src/pycode_kg/kg.py | 9 | class |
| `StructuralImportanceRanker()` | src/pycode_kg/analysis/centrality.py | 7 | class |
| `compute_coderank()` | src/pycode_kg/ranking/coderank.py | 7 | function |
| `build_graph_html()` | src/pycode_kg/graph_html.py | 5 | function |
| `norm()` | src/pycode_kg/analysis/framework_detector.py | 4 | function |
| `norm()` | src/pycode_kg/analysis/hybrid_rank.py | 4 | function |
| `aggregate_module_scores()` | src/pycode_kg/analysis/centrality.py | 4 | function |
| `FunctionMetrics()` | src/pycode_kg/pycodekg_thorough_analysis.py | 4 | class |
| `build()` | src/pycode_kg/cli/cmd_build_full.py | 3 | function |
---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 132 | 145 | [OK] 91.0% |
| `method` | 138 | 146 | [OK] 94.5% |
| `class` | 28 | 30 | [OK] 93.3% |
| `module` | 51 | 56 | [OK] 91.1% |
| **total** | **349** | **377** | **[OK] 92.6%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.122389 | 52 | `src/pycode_kg/viz3d.py` |
| 2 | 0.098383 | 25 | `src/pycode_kg/snapshots.py` |
| 3 | 0.061969 | 37 | `src/pycode_kg/pycodekg_thorough_analysis.py` |
| 4 | 0.060086 | 26 | `src/pycode_kg/mcp_server.py` |
| 5 | 0.053266 | 14 | `src/pycode_kg/analysis/centrality.py` |
| 6 | 0.049843 | 9 | `src/pycode_kg/graph.py` |
| 7 | 0.044623 | 8 | `src/pycode_kg/pycodekg.py` |
| 8 | 0.044376 | 8 | `src/pycode_kg/cli/cmd_build_full.py` |
| 9 | 0.042298 | 20 | `src/pycode_kg/visitor.py` |
| 10 | 0.036910 | 18 | `src/pycode_kg/architecture.py` |
| 11 | 0.031554 | 4 | `src/pycode_kg/graph_html.py` |
| 12 | 0.030433 | 3 | `src/pycode_kg/ranking/cli_rank.py` |
| 13 | 0.028963 | 14 | `src/pycode_kg/ranking/coderank.py` |
| 14 | 0.026396 | 7 | `src/pycode_kg/module/extractor.py` |
| 15 | 0.025500 | 10 | `src/pycode_kg/kg.py` |



---

## Code Quality Issues

- [WARN] 1 orphaned functions found (`Snippet`) -- consider archiving or documenting
- [WARN] 1 functions with high fan-out -- potential orchestrators or god objects
- [WARN] `viz3d.py` has 51 functions/methods/classes -- consider splitting into focused submodules
- [WARN] `pycodekg_thorough_analysis.py` has 36 functions/methods/classes -- consider splitting into focused submodules

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- Good docstring coverage: 92.6% of functions/methods/classes/modules documented

---

## Recommendations

### Immediate Actions
1. **Remove or archive orphaned functions** — `Snippet` have zero callers and add maintenance burden
2. **Refactor high fan-out orchestrators** — `init` calls 43 functions; consider splitting into smaller, focused coordinators

### Medium-term Refactoring
1. **Harden high fan-in functions** — `_get_kg`, `compute_coderank`, `_rewrap` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `SnapshotManager`, `PyCodeKG`, `StructuralImportanceRanker`
2. **Enforce layer boundaries** — add linting or CI checks to prevent unexpected cross-module dependencies as the codebase grows
3. **Monitor hot paths** — instrument the high fan-in functions identified here to catch performance regressions early

---

## Inheritance Hierarchy

**10** INHERITS edges across **10** classes. Max depth: **1**.

| Class | Module | Depth | Parents | Children |
|-------|--------|-------|---------|----------|
| `PyCodeKG` | src/pycode_kg/kg.py | 1 | 1 | 0 |
| `FunnelLayout` | src/pycode_kg/layout3d.py | 0 | 1 | 0 |
| `KGModule` | src/pycode_kg/module/base.py | 0 | 1 | 1 |
| `PyCodeKGExtractor` | src/pycode_kg/module/extractor.py | 0 | 1 | 0 |
| `Snapshot` | src/pycode_kg/snapshots.py | 0 | 1 | 0 |
| `SnapshotManager` | src/pycode_kg/snapshots.py | 0 | 1 | 0 |
| `PyCodeKGVisitor` | src/pycode_kg/visitor.py | 0 | 1 | 0 |
| `DocstringPopup` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |
| `KGVisualizer` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |
| `MainWindow` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |


---

## Snapshot History

Recent snapshots in reverse chronological order. Δ columns show change vs. the immediately preceding snapshot.

| # | Timestamp | Branch | Version | Nodes | Edges | Coverage | Δ Nodes | Δ Edges | Δ Coverage |
|---|-----------|--------|---------|-------|-------|----------|---------|---------|------------|
| 1 | 2026-08-11 23:07:27 | feat/viz3d-shared | 0.21.4 | 6221 | 5858 | 92.6% | -182 | -167 | -0.2% |
| 2 | 2026-08-03 21:57:37 | fix/runpod-pin-kgmodule-utils | 0.21.3 | 6403 | 6025 | 92.8% | +0 | +0 | +0.0% |
| 3 | 2026-08-03 15:45:45 | main | 0.21.3 | 6403 | 6025 | 92.8% | +0 | +0 | +0.0% |
| 4 | 2026-08-03 15:37:21 | main | 0.21.3 | 6403 | 6025 | 92.8% | +0 | +0 | +0.0% |
| 5 | 2026-08-03 15:30:54 | chore/kgmodule-utils-semantic-extra | 0.21.3 | 6403 | 6025 | 92.8% | +0 | +0 | +0.0% |
| 6 | 2026-08-02 20:35:11 | main | 0.21.3 | 6403 | 6025 | 92.8% | +0 | +0 | +0.0% |
| 7 | 2026-07-29 19:33:11 | main | 0.21.1 | 6403 | 6025 | 92.8% | +0 | +0 | +0.0% |
| 8 | 2026-07-29 19:29:39 | main | 0.21.1 | 6403 | 6025 | 92.8% | +0 | +0 | +0.0% |
| 9 | 2026-07-29 19:23:41 | main | 0.21.1 | 6403 | 6025 | 92.8% | +0 | +0 | +0.0% |
| 10 | 2026-07-29 19:21:48 | main | 0.21.1 | 6403 | 6025 | 92.8% | +0 | +0 | +0.0% |


---

## Appendix: Orphaned Code

Functions with zero callers (potential dead code):

| Function | Module | Lines |
|----------|--------|-------|
| `Snippet()` | src/pycode_kg/module/types.py | 9 |
---

## CodeRank -- Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000644 | function | `_get_kg` | src/pycode_kg/mcp_server.py |
| 2 | 0.000580 | method | `CodeGraph.extract` | src/pycode_kg/graph.py |
| 3 | 0.000479 | function | `_rewrap` | src/pycode_kg/snapshots.py |
| 4 | 0.000414 | function | `_load_dir_list` | src/pycode_kg/config.py |
| 5 | 0.000362 | method | `PyCodeKGVisitor._get_node_id` | src/pycode_kg/visitor.py |
| 6 | 0.000362 | method | `PyCodeKGVisitor._add_edge` | src/pycode_kg/visitor.py |
| 7 | 0.000355 | function | `expr_to_name` | src/pycode_kg/pycodekg.py |
| 8 | 0.000327 | function | `_run_pipeline` | src/pycode_kg/cli/cmd_build_full.py |
| 9 | 0.000319 | function | `_format_table` | src/pycode_kg/cli/cmd_centrality.py |
| 10 | 0.000294 | method | `PyCodeKGVisitor._add_var_edge` | src/pycode_kg/visitor.py |
| 11 | 0.000290 | function | `_load_store` | src/pycode_kg/app.py |
| 12 | 0.000280 | function | `load_snapshots_timeline` | src/pycode_kg/viz3d_timeline.py |
| 13 | 0.000262 | method | `PyCodeKGVisitor._extract_reads` | src/pycode_kg/visitor.py |
| 14 | 0.000257 | function | `delta_to_dict` | src/pycode_kg/snapshots.py |
| 15 | 0.000257 | function | `delta_from_dict` | src/pycode_kg/snapshots.py |
| 16 | 0.000255 | function | `_remove_highlight_actors` | src/pycode_kg/viz3d.py |
| 17 | 0.000252 | method | `KGVisualizer._load_scores` | src/pycode_kg/viz3d.py |
| 18 | 0.000252 | function | `metrics_to_dict` | src/pycode_kg/snapshots.py |
| 19 | 0.000251 | method | `CodeGraph.nodes` | src/pycode_kg/graph.py |
| 20 | 0.000251 | method | `CodeGraph.edges` | src/pycode_kg/graph.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7533 | function | `_load_kg` | src/pycode_kg/app.py |
| 2 | 0.7532 | function | `_init_state` | src/pycode_kg/app.py |
| 3 | 0.7461 | method | `PyCodeKGExtractor.__init__` | src/pycode_kg/module/extractor.py |
| 4 | 0.7459 | function | `main` | src/pycode_kg/mcp_server.py |
| 5 | 0.7396 | method | `MainWindow.__init__` | src/pycode_kg/viz3d.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.779 | function | `_load_store` | src/pycode_kg/app.py |
| 2 | 0.7326 | function | `_get_store` | src/pycode_kg/app.py |
| 3 | 0.731 | method | `SnapshotManager.save_snapshot` | src/pycode_kg/snapshots.py |
| 4 | 0.731 | method | `ArchitectureAnalyzer.__init__` | src/pycode_kg/architecture.py |
| 5 | 0.7264 | function | `_load_kg` | src/pycode_kg/app.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | function | `query_codebase` | src/pycode_kg/mcp_server.py |
| 2 | 0.7489 | function | `query` | src/pycode_kg/cli/cmd_query.py |
| 3 | 0.7382 | function | `query_ranked` | src/pycode_kg/mcp_server.py |
| 4 | 0.7294 | function | `pack_snippets` | src/pycode_kg/mcp_server.py |
| 5 | 0.7269 | function | `rank_query_hybrid` | src/pycode_kg/ranking/coderank.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7869 | method | `PyCodeKGVisitor._add_edge` | src/pycode_kg/visitor.py |
| 2 | 0.7592 | method | `CodeGraph.edges` | src/pycode_kg/graph.py |
| 3 | 0.7548 | function | `induce_query_subgraph` | src/pycode_kg/ranking/coderank.py |
| 4 | 0.75 | function | `query_codebase` | src/pycode_kg/mcp_server.py |
| 5 | 0.7487 | function | `compute_seed_proximity` | src/pycode_kg/ranking/coderank.py |



---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 3.5s*
