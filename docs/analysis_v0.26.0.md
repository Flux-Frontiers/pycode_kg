> **Analysis Report Metadata**
> - **Generated:** 2026-09-06T21:10:11Z
> - **Version:** pycode-kg 0.26.0
> - **Commit:** c244726 (main)
> - **Index freshness:** [WARN] 6 uncommitted change(s) — the index may not reflect current file contents; line numbers and edge counts can drift. Re-run `pycodekg build` before trusting them.
> - **Platform:** macOS 27.0 | arm64 (arm) | turing | Python 3.12.13
> - **Graph:** 6931 nodes · 6418 edges (406 meaningful)
> - **Included directories:** src
> - **Excluded directories:** none
> - **Elapsed time:** 3s

# pycode_kg Analysis

**Generated:** 2026-09-06 21:10:11 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **pycode_kg** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
| :--- | :--- | :--- |
| [A] **Excellent** | **A** | 100.0 / 100 |

Score components:

| Component | Points | Max | Basis |
| :--- | ---: | ---: | :--- |
| Docstring coverage | 40.0 | 40 | 95.1% documented (full marks at 90%) |
| Dead code | 25.0 | 25 | 0 candidates / 350 definitions scanned (0.0%; zero points at 5%) |
| High fan-out | 20.0 | 20 | 0 orchestrator(s); −4 pts each |
| Circular dependencies | 15.0 | 15 | 0 cycle(s); −5 pts each |

---

## Baseline Metrics

| Metric | Value |
| :--- | :--- |
| **Total Nodes** | 6931 |
| **Total Edges** | 6418 |
| **Modules** | 56 (of 56 total) |
| **Functions** | 174 |
| **Classes** | 31 |
| **Methods** | 145 |

### Edge Distribution

| Relationship Type | Count |
| :--- | ---: |
| CALLS | 2430 |
| CONTAINS | 350 |
| IMPORTS | 493 |
| ATTR_ACCESS | 2212 |
| INHERITS | 10 |

_Excludes 923 `RESOLVES_TO` edges: internal symbol-stub resolutions, not relationships between two pieces of code. This table therefore does not sum to Total Edges._

---

## Fan-In Ranking

Most-called functions and methods — potential bottlenecks or core functionality.  Classes are omitted: instantiation counts are not architectural fan-in.

| # | Kind | Function | Module | Callers |
| ---: | :--- | :--- | ---: | :--- |
| 1 | function | `_get_kg()` | src/pycode_kg/mcp_server.py | **17** |
| 2 | function | `compute_coderank()` | src/pycode_kg/ranking/coderank.py | **7** |
| 3 | method | `to_markdown()` | src/pycode_kg/pycodekg_thorough_analysis.py | **6** |
| 4 | method | `_add_edge()` | src/pycode_kg/visitor.py | **5** |
| 5 | method | `_get_node_id()` | src/pycode_kg/visitor.py | **5** |
| 6 | method | `_add_var_edge()` | src/pycode_kg/visitor.py | **5** |
| 7 | method | `extract()` | src/pycode_kg/graph.py | **4** |
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
| `src/pycode_kg/pycodekg_thorough_analysis.py` | 16 | 4 | 4 | 3 | 0.50 |  |
| `src/pycode_kg/mcp_server.py` | 25 | 0 | 0 | 3 | 0.00 | externally driven |
| `src/pycode_kg/visitor.py` | 1 | 1 | 1 | 1 | 0.33 |  |
| `src/pycode_kg/architecture.py` | 0 | 4 | 1 | 0 | 0.50 |  |
| `src/pycode_kg/app.py` | 14 | 0 | 0 | 2 | 0.00 | externally driven |
| `src/pycode_kg/analysis/centrality.py` | 1 | 5 | 3 | 0 | 0.75 |  |
| `src/pycode_kg/ranking/coderank.py` | 12 | 1 | 1 | 0 | 0.50 |  |
| `src/pycode_kg/snapshots.py` | 4 | 3 | 6 | 0 | 0.86 |  |
| `src/pycode_kg/pycodekg.py` | 8 | 2 | 3 | 2 | 0.50 |  |

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
| `PyCodeKG` | src/pycode_kg/kg.py | 9 | class |
| `SnapshotManager` | src/pycode_kg/snapshots.py | 9 | class |
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
| `function` | 161 | 174 | [OK] 92.5% |
| `method` | 140 | 145 | [OK] 96.6% |
| `class` | 29 | 31 | [OK] 93.5% |
| `module` | 56 | 56 | [OK] 100.0% |
| **total** | **386** | **406** | **[OK] 95.1%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
| ---: | ---: | ---: | :--- |
| 1 | 0.111575 | 57 | `src/pycode_kg/viz3d.py` |
| 2 | 0.090311 | 53 | `src/pycode_kg/pycodekg_thorough_analysis.py` |
| 3 | 0.067931 | 11 | `src/pycode_kg/pycodekg.py` |
| 4 | 0.059946 | 13 | `src/pycode_kg/snapshots.py` |
| 5 | 0.059030 | 26 | `src/pycode_kg/mcp_server.py` |
| 6 | 0.051449 | 14 | `src/pycode_kg/analysis/centrality.py` |
| 7 | 0.041148 | 20 | `src/pycode_kg/visitor.py` |
| 8 | 0.039548 | 9 | `src/pycode_kg/graph.py` |
| 9 | 0.037350 | 18 | `src/pycode_kg/architecture.py` |
| 10 | 0.031877 | 4 | `src/pycode_kg/graph_html.py` |
| 11 | 0.030747 | 3 | `src/pycode_kg/ranking/cli_rank.py` |
| 12 | 0.030235 | 14 | `src/pycode_kg/ranking/coderank.py` |
| 13 | 0.023296 | 9 | `src/pycode_kg/kg.py` |
| 14 | 0.022237 | 15 | `src/pycode_kg/app.py` |
| 15 | 0.021863 | 7 | `src/pycode_kg/module/extractor.py` |

---

## Code Quality Issues

- [INFO] 4 definitions are unused in production code but exercised by tests -- likely public API for downstream packages; not counted against the quality grade
- [WARN] `viz3d.py` has 56 functions/methods/classes -- consider splitting into focused submodules
- [WARN] `pycodekg_thorough_analysis.py` has 52 functions/methods/classes -- consider splitting into focused submodules

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No obvious dead code detected
- No god objects or god functions detected
- Good docstring coverage: 95.1% of functions/methods/classes/modules documented

---

## Recommendations

### Medium-term Refactoring
1. **Harden high fan-in functions** — `_get_kg`, `compute_coderank`, `to_markdown` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `PyCodeKG`, `SnapshotManager`, `StructuralImportanceRanker`
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

Recent snapshots in reverse chronological order. Δ columns show change vs. the immediately preceding snapshot.  6 unchanged snapshot(s) elided.

| # | Timestamp | Branch | Version | Nodes | Edges | Coverage | Δ Nodes | Δ Edges | Δ Coverage |
| ---: | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2026-08-25 15:45:25 | main | 0.24.1 | 7000 | 6515 | 94.5% (395/418) | +207 | +175 | +0.2% |
| 6 | 2026-08-18 12:55:57 | main | 0.23.1 | 6793 | 6340 | 94.3% | -19 | -21 | +0.0% |
| 8 | 2026-08-17 01:03:31 | refactor/promoted-leaf-helpers | 0.23.1 | 6812 | 6361 | 94.3% | -20 | -15 | -0.1% |
| 10 | 2026-08-15 14:09:43 | main | 0.23.0 | 6832 | 6376 | 94.4% | +401 | +364 | +1.5% |

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

2 further methods override a base class outside the indexed graph — the caller may live in that dependency, so these cannot be judged dead or alive.  Not counted against the quality grade.

| Name | Kind | Module | Lines |
| :--- | :--- | :--- | ---: |
| `visualize()` | method | src/pycode_kg/viz3d.py | 20 |
| `_compute_delta_from_metrics()` | method | src/pycode_kg/snapshots.py | 13 |

---

## CodeRank — Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds fan-in discovery and the concern queries below.  Top 20 of 25 shown.

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.000577 | function | `_get_kg()` | src/pycode_kg/mcp_server.py |
| 2 | 0.000521 | method | `CodeGraph.extract()` | src/pycode_kg/graph.py |
| 3 | 0.000477 | function | `expr_to_name()` | src/pycode_kg/pycodekg.py |
| 4 | 0.000372 | function | `_load_dir_list()` | src/pycode_kg/config.py |
| 5 | 0.000325 | method | `PyCodeKGVisitor._get_node_id()` | src/pycode_kg/visitor.py |
| 6 | 0.000325 | method | `PyCodeKGVisitor._add_edge()` | src/pycode_kg/visitor.py |
| 7 | 0.000309 | function | `_own_scope_nodes()` | src/pycode_kg/pycodekg.py |
| 8 | 0.000294 | function | `_run_pipeline()` | src/pycode_kg/cli/cmd_build_full.py |
| 9 | 0.000287 | function | `_format_table()` | src/pycode_kg/cli/cmd_centrality.py |
| 10 | 0.000264 | method | `PyCodeKGVisitor._add_var_edge()` | src/pycode_kg/visitor.py |
| 11 | 0.000260 | function | `_load_store()` | src/pycode_kg/app.py |
| 12 | 0.000252 | function | `load_snapshots_timeline()` | src/pycode_kg/viz3d_timeline.py |
| 13 | 0.000248 | function | `_annotation_class_name()` | src/pycode_kg/pycodekg.py |
| 14 | 0.000237 | method | `MainWindow._h2()` | src/pycode_kg/viz3d.py |
| 15 | 0.000235 | method | `PyCodeKGVisitor._extract_reads()` | src/pycode_kg/visitor.py |
| 16 | 0.000229 | function | `_remove_highlight_actors()` | src/pycode_kg/viz3d.py |
| 17 | 0.000227 | method | `KGVisualizer._load_scores()` | src/pycode_kg/viz3d.py |
| 18 | 0.000225 | method | `CodeGraph.nodes()` | src/pycode_kg/graph.py |
| 19 | 0.000225 | method | `CodeGraph.edges()` | src/pycode_kg/graph.py |
| 20 | 0.000225 | function | `create_kg_visualization()` | src/pycode_kg/viz3d.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7529 | function | `_load_kg()` | src/pycode_kg/app.py |
| 2 | 0.7523 | function | `_init_state()` | src/pycode_kg/app.py |
| 3 | 0.7461 | method | `PyCodeKGExtractor.__init__()` | src/pycode_kg/module/extractor.py |
| 4 | 0.7457 | function | `main()` | src/pycode_kg/mcp_server.py |
| 5 | 0.7396 | method | `MainWindow.__init__()` | src/pycode_kg/viz3d.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7755 | function | `_load_store()` | src/pycode_kg/app.py |
| 2 | 0.7329 | function | `_get_store()` | src/pycode_kg/app.py |
| 3 | 0.7306 | method | `ArchitectureAnalyzer.__init__()` | src/pycode_kg/architecture.py |
| 4 | 0.7258 | function | `_load_kg()` | src/pycode_kg/app.py |
| 5 | 0.7249 | function | `persist_metric_scores()` | src/pycode_kg/ranking/coderank.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.75 | function | `query_codebase()` | src/pycode_kg/mcp_server.py |
| 2 | 0.7489 | function | `query()` | src/pycode_kg/cli/cmd_query.py |
| 3 | 0.7382 | function | `query_ranked()` | src/pycode_kg/mcp_server.py |
| 4 | 0.7297 | function | `pack_snippets()` | src/pycode_kg/mcp_server.py |
| 5 | 0.7273 | function | `rank_query_hybrid()` | src/pycode_kg/ranking/coderank.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.7908 | method | `PyCodeKGVisitor._add_edge()` | src/pycode_kg/visitor.py |
| 2 | 0.7607 | method | `CodeGraph.edges()` | src/pycode_kg/graph.py |
| 3 | 0.755 | function | `induce_query_subgraph()` | src/pycode_kg/ranking/coderank.py |
| 4 | 0.75 | function | `query_codebase()` | src/pycode_kg/mcp_server.py |
| 5 | 0.7491 | function | `compute_seed_proximity()` | src/pycode_kg/ranking/coderank.py |

---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 3.1s*
