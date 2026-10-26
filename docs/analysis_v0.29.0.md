> **Analysis Report Metadata**
> - **Generated:** 2026-10-26T04:00:04Z
> - **Version:** pycode-kg 0.29.0
> - **Commit:** b76953b (feat/mcp-server-base)
> - **Index freshness:** [WARN] 6 uncommitted change(s) — the index may not reflect current file contents; line numbers and edge counts can drift. Re-run `pycodekg build` before trusting them.
> - **Platform:** macOS 27.2 | arm64 (arm) | turing | Python 3.12.13
> - **Graph:** 6887 nodes · 6341 edges (404 meaningful)
> - **Included directories:** src
> - **Excluded directories:** none
> - **Elapsed time:** 3s

# pycode_kg Analysis

**Generated:** 2026-10-26 04:00:04 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **pycode_kg** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
| :--- | :--- | :--- |
| [A] **Excellent** | **A** | 100.0 / 100 |

Score components:

| Component | Points | Max | Basis |
| :--- | ---: | ---: | :--- |
| Docstring coverage | 40.0 | 40 | 94.6% documented (full marks at 90%) |
| Dead code | 25.0 | 25 | 0 candidates / 348 definitions scanned (0.0%; zero points at 5%) |
| High fan-out | 20.0 | 20 | 0 orchestrator(s); −4 pts each |
| Circular dependencies | 15.0 | 15 | 0 cycle(s); −5 pts each |

---

## Baseline Metrics

| Metric | Value |
| :--- | :--- |
| **Total Nodes** | 6887 |
| **Total Edges** | 6341 |
| **Modules** | 56 (of 56 total) |
| **Functions** | 174 |
| **Classes** | 31 |
| **Methods** | 143 |

### Edge Distribution

| Relationship Type | Count |
| :--- | ---: |
| CALLS | 2373 |
| CONTAINS | 348 |
| IMPORTS | 500 |
| ATTR_ACCESS | 2199 |
| INHERITS | 10 |

_Excludes 911 `RESOLVES_TO` edges: internal symbol-stub resolutions, not relationships between two pieces of code. This table therefore does not sum to Total Edges._

---

## Fan-In Ranking

Most-called functions and methods — potential bottlenecks or core functionality.  Classes are omitted: instantiation counts are not architectural fan-in.

| # | Kind | Function | Module | Callers |
| ---: | :--- | :--- | ---: | :--- |
| 1 | function | `compute_coderank()` | src/pycode_kg/ranking/coderank.py | **7** |
| 2 | method | `to_markdown()` | src/pycode_kg/pycodekg_thorough_analysis.py | **6** |
| 3 | method | `_add_edge()` | src/pycode_kg/visitor.py | **5** |
| 4 | method | `_get_node_id()` | src/pycode_kg/visitor.py | **5** |
| 5 | method | `_add_var_edge()` | src/pycode_kg/visitor.py | **5** |
| 6 | method | `extract()` | src/pycode_kg/graph.py | **4** |
| 7 | function | `_snapshots()` | src/pycode_kg/mcp_server.py | **4** |
| 8 | method | `_h2()` | src/pycode_kg/viz3d.py | **4** |
| 9 | method | `_extract_reads()` | src/pycode_kg/visitor.py | **4** |
| 10 | method | `_get_package_root()` | src/pycode_kg/pycodekg_thorough_analysis.py | **4** |
| 11 | function | `_run_pipeline()` | src/pycode_kg/cli/cmd_build_full.py | **3** |
| 12 | function | `load_snapshots_timeline()` | src/pycode_kg/viz3d_timeline.py | **3** |
| 13 | method | `nodes()` | src/pycode_kg/graph.py | **3** |
| 14 | method | `reset_actor_appearances()` | src/pycode_kg/viz3d.py | **3** |

**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:

- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.  Only repo-internal callees are counted — stdlib and third-party calls are not orchestration.

No extreme high fan-out functions detected. Well-balanced architecture.

---

## Module Architecture

Top modules by dependency coupling and cohesion (showing 10 of 56 with activity).
Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.  Modules with no in-repo callers are externally driven (MCP router, CLI, GUI event loop) — their 0.00 cohesion is expected, not a coupling problem.

| Module | Functions | Classes | Incoming | Outgoing | Cohesion | Note |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `src/pycode_kg/viz3d.py` | 9 | 3 | 0 | 1 | 0.00 | externally driven |
| `src/pycode_kg/pycodekg_thorough_analysis.py` | 17 | 4 | 4 | 3 | 0.50 |  |
| `src/pycode_kg/mcp_server.py` | 23 | 0 | 0 | 3 | 0.00 | externally driven |
| `src/pycode_kg/visitor.py` | 1 | 1 | 1 | 1 | 0.33 |  |
| `src/pycode_kg/architecture.py` | 0 | 4 | 1 | 0 | 0.50 |  |
| `src/pycode_kg/app.py` | 14 | 0 | 0 | 2 | 0.00 | externally driven |
| `src/pycode_kg/analysis/centrality.py` | 1 | 5 | 3 | 0 | 0.75 |  |
| `src/pycode_kg/ranking/coderank.py` | 12 | 1 | 1 | 0 | 0.50 |  |
| `src/pycode_kg/pycodekg.py` | 8 | 2 | 3 | 2 | 0.50 |  |
| `src/pycode_kg/snapshots.py` | 4 | 3 | 6 | 0 | 0.86 |  |

---

## Key Call Chains

Deepest call chains in the codebase.

**Chain 1** (depth: 4)

```
pycodekg_thorough_analysis.py:_write_report → pycodekg_thorough_analysis.py:to_markdown → report.py:render_markdown → report.py:_bar
```

**Chain 2** (depth: 3)

```
visitor.py:_add_var_edge → visitor.py:_get_node_id → utils.py:node_id
```

---

## Public API Surface

Definitions re-exported from an `__init__.py` or otherwise reachable as public entry points, ranked by fan-in.  Top 10 of 31 shown.

| Name | Module | Fan-In | Kind |
| :--- | :--- | ---: | :--- |
| `SnapshotManager` | src/pycode_kg/snapshots.py | 9 | class |
| `PyCodeKG` | src/pycode_kg/kg.py | 8 | class |
| `StructuralImportanceRanker` | src/pycode_kg/analysis/centrality.py | 7 | class |
| `compute_coderank()` | src/pycode_kg/ranking/coderank.py | 7 | function |
| `build_graph_html()` | src/pycode_kg/graph_html.py | 5 | function |
| `aggregate_module_scores()` | src/pycode_kg/analysis/centrality.py | 4 | function |
| `FunctionMetrics` | src/pycode_kg/pycodekg_thorough_analysis.py | 4 | class |
| `PyCodeKGExtractor` | src/pycode_kg/module/extractor.py | 3 | class |
| `load_snapshots_timeline()` | src/pycode_kg/viz3d_timeline.py | 3 | function |
| `CentralityRecord` | src/pycode_kg/analysis/centrality.py | 2 | class |

---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where keyword search is as effective as vector embeddings. The semantic model earns its value only when a docstring is present.

| Kind | Documented | Total | Coverage |
| :--- | ---: | ---: | :--- |
| `function` | 159 | 174 | [OK] 91.4% |
| `method` | 138 | 143 | [OK] 96.5% |
| `class` | 29 | 31 | [OK] 93.5% |
| `module` | 56 | 56 | [OK] 100.0% |
| **total** | **382** | **404** | **[OK] 94.6%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
| ---: | ---: | ---: | :--- |
| 1 | 0.110630 | 57 | `src/pycode_kg/viz3d.py` |
| 2 | 0.091679 | 54 | `src/pycode_kg/pycodekg_thorough_analysis.py` |
| 3 | 0.089792 | 24 | `src/pycode_kg/mcp_server.py` |
| 4 | 0.065771 | 11 | `src/pycode_kg/pycodekg.py` |
| 5 | 0.051977 | 14 | `src/pycode_kg/analysis/centrality.py` |
| 6 | 0.047914 | 11 | `src/pycode_kg/snapshots.py` |
| 7 | 0.040699 | 20 | `src/pycode_kg/visitor.py` |
| 8 | 0.037230 | 18 | `src/pycode_kg/architecture.py` |
| 9 | 0.034900 | 9 | `src/pycode_kg/graph.py` |
| 10 | 0.031292 | 4 | `src/pycode_kg/graph_html.py` |
| 11 | 0.030662 | 14 | `src/pycode_kg/ranking/coderank.py` |
| 12 | 0.022635 | 3 | `src/pycode_kg/ranking/cli_rank.py` |
| 13 | 0.022452 | 15 | `src/pycode_kg/app.py` |
| 14 | 0.021677 | 9 | `src/pycode_kg/kg.py` |
| 15 | 0.021423 | 7 | `src/pycode_kg/module/extractor.py` |

---

## Code Quality Issues

- [INFO] 4 definitions are unused in production code but exercised by tests -- likely public API for downstream packages; not counted against the quality grade
- [WARN] `viz3d.py` has 56 functions/methods/classes -- consider splitting into focused submodules
- [WARN] `pycodekg_thorough_analysis.py` has 53 functions/methods/classes -- consider splitting into focused submodules

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No obvious dead code detected
- No god objects or god functions detected
- Good docstring coverage: 94.6% of functions/methods/classes/modules documented

---

## Recommendations

### Medium-term Refactoring
1. **Harden high fan-in functions** — `compute_coderank`, `to_markdown`, `_add_edge` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
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
| :--- | :--- | ---: | ---: | ---: |
| `PyCodeKG` | src/pycode_kg/kg.py | 1 | 1 | 0 |
| `FunnelLayout` | src/pycode_kg/layout3d.py | 0 | 1 | 0 |
| `KGModule` | src/pycode_kg/module/base.py | 0 | 1 | 1 |
| `PyCodeKGExtractor` | src/pycode_kg/module/extractor.py | 0 | 1 | 0 |
| `CodeTreeLayout` | src/pycode_kg/scene3d.py | 0 | 1 | 0 |
| `SnapshotManager` | src/pycode_kg/snapshots.py | 0 | 1 | 0 |
| `PyCodeKGVisitor` | src/pycode_kg/visitor.py | 0 | 1 | 0 |
| `DocstringPopup` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |
| `KGVisualizer` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |
| `MainWindow` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |

---

## Snapshot History

Recent snapshots in reverse chronological order. Δ columns show change vs. the immediately preceding snapshot.  1 unchanged snapshot(s) elided.

| # | Timestamp | Branch | Version | Nodes | Edges | Coverage | Δ Nodes | Δ Edges | Δ Coverage |
| ---: | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2026-10-15 12:53:46 | main | 0.28.2 | 6943 | 6428 | 95.1% (387/407) | +19 | +16 | +0.0% |
| 2 | 2026-09-24 01:19:57 | main | 0.28.1 | 6924 | 6412 | 95.1% (386/406) | +14 | +12 | +0.0% |
| 3 | 2026-09-21 00:09:46 | main | 0.28.0 | 6910 | 6400 | 95.1% (386/406) | +6 | +5 | +0.0% |
| 5 | 2026-09-09 00:45:51 | main | 0.27.0 | 6904 | 6395 | 95.1% (385/405) | -27 | -23 | +0.0% |
| 6 | 2026-09-06 21:11:19 | main | 0.26.0 | 6931 | 6418 | 95.1% (386/406) | -69 | -97 | +0.6% |
| 7 | 2026-08-25 15:45:25 | main | 0.24.1 | 7000 | 6515 | 94.5% (395/418) | +819 | +687 | +2.1% |
| 8 | 2026-08-13 22:43:29 | main | 0.22.0 | 6181 | 5828 | 92.4% | -222 | -197 | -0.4% |
| 9 | 2026-07-29 02:44:18 | main | 0.21.0 | 6403 | 6025 | 92.8% | +120 | +150 | +0.2% |
| 10 | 2026-06-09 12:15:17 | main | 0.19.3 | 6283 | 5875 | 92.6% | — | — | — |

---

## Orphaned Code

No dead-code candidates detected.

4 further definitions are unused in production code but exercised by tests — likely public API consumed by downstream packages.  Not counted against the quality grade; review for intentional export.

| Name | Kind | Module | Lines |
| :--- | :--- | :--- | ---: |
| `with_alpha()` | function | src/pycode_kg/theme.py | 20 |
| `rel_color()` | function | src/pycode_kg/theme.py | 8 |
| `color_for()` | function | src/pycode_kg/theme.py | 6 |
| `shape_for()` | function | src/pycode_kg/theme.py | 6 |

3 further methods override a base class outside the indexed graph — the caller may live in that dependency, so these cannot be judged dead or alive.  Not counted against the quality grade.

| Name | Kind | Module | Lines |
| :--- | :--- | :--- | ---: |
| `visualize()` | method | src/pycode_kg/viz3d.py | 20 |
| `_domain_metrics()` | method | src/pycode_kg/snapshots.py | 14 |
| `_compute_delta_from_metrics()` | method | src/pycode_kg/snapshots.py | 13 |

---

## CodeRank — Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds fan-in discovery and the concern queries below.  Top 20 of 25 shown.

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.000524 | method | `CodeGraph.extract()` | src/pycode_kg/graph.py |
| 2 | 0.000480 | function | `expr_to_name()` | src/pycode_kg/pycodekg.py |
| 3 | 0.000374 | function | `_load_dir_list()` | src/pycode_kg/config.py |
| 4 | 0.000327 | method | `PyCodeKGVisitor._get_node_id()` | src/pycode_kg/visitor.py |
| 5 | 0.000327 | method | `PyCodeKGVisitor._add_edge()` | src/pycode_kg/visitor.py |
| 6 | 0.000311 | function | `_own_scope_nodes()` | src/pycode_kg/pycodekg.py |
| 7 | 0.000296 | function | `_run_pipeline()` | src/pycode_kg/cli/cmd_build_full.py |
| 8 | 0.000289 | function | `_format_table()` | src/pycode_kg/cli/cmd_centrality.py |
| 9 | 0.000266 | method | `PyCodeKGVisitor._add_var_edge()` | src/pycode_kg/visitor.py |
| 10 | 0.000262 | function | `_load_store()` | src/pycode_kg/app.py |
| 11 | 0.000256 | method | `SnapshotManager._collect_module_node_counts()` | src/pycode_kg/snapshots.py |
| 12 | 0.000254 | function | `load_snapshots_timeline()` | src/pycode_kg/viz3d_timeline.py |
| 13 | 0.000250 | function | `_annotation_class_name()` | src/pycode_kg/pycodekg.py |
| 14 | 0.000241 | function | `_snapshots()` | src/pycode_kg/mcp_server.py |
| 15 | 0.000239 | method | `MainWindow._h2()` | src/pycode_kg/viz3d.py |
| 16 | 0.000237 | method | `PyCodeKGVisitor._extract_reads()` | src/pycode_kg/visitor.py |
| 17 | 0.000231 | function | `_remove_highlight_actors()` | src/pycode_kg/viz3d.py |
| 18 | 0.000228 | method | `KGVisualizer._load_scores()` | src/pycode_kg/viz3d.py |
| 19 | 0.000227 | method | `CodeGraph.nodes()` | src/pycode_kg/graph.py |
| 20 | 0.000227 | method | `CodeGraph.edges()` | src/pycode_kg/graph.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7528 | function | `_load_kg()` | src/pycode_kg/app.py |
| 2 | 0.7521 | function | `_init_state()` | src/pycode_kg/app.py |
| 3 | 0.7461 | method | `PyCodeKGExtractor.__init__()` | src/pycode_kg/module/extractor.py |
| 4 | 0.7396 | method | `MainWindow.__init__()` | src/pycode_kg/viz3d.py |
| 5 | 0.739 | method | `StructuralImportanceRanker.__init__()` | src/pycode_kg/analysis/centrality.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7742 | function | `_load_store()` | src/pycode_kg/app.py |
| 2 | 0.7328 | function | `_get_store()` | src/pycode_kg/app.py |
| 3 | 0.7306 | method | `ArchitectureAnalyzer.__init__()` | src/pycode_kg/architecture.py |
| 4 | 0.7256 | function | `_load_kg()` | src/pycode_kg/app.py |
| 5 | 0.7249 | function | `persist_metric_scores()` | src/pycode_kg/ranking/coderank.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.75 | function | `query()` | src/pycode_kg/mcp_server.py |
| 2 | 0.746 | function | `query()` | src/pycode_kg/cli/cmd_query.py |
| 3 | 0.7351 | function | `query_ranked()` | src/pycode_kg/mcp_server.py |
| 4 | 0.7245 | function | `rank_query_hybrid()` | src/pycode_kg/ranking/coderank.py |
| 5 | 0.7183 | function | `pack()` | src/pycode_kg/mcp_server.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7826 | method | `PyCodeKGVisitor._add_edge()` | src/pycode_kg/visitor.py |
| 2 | 0.7586 | method | `CodeGraph.edges()` | src/pycode_kg/graph.py |
| 3 | 0.7563 | function | `induce_query_subgraph()` | src/pycode_kg/ranking/coderank.py |
| 4 | 0.7504 | function | `compute_seed_proximity()` | src/pycode_kg/ranking/coderank.py |
| 5 | 0.7499 | method | `StructuralImportanceRanker._load_effective_edges()` | src/pycode_kg/analysis/centrality.py |

---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 3.3s*
