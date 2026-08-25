> **Analysis Report Metadata**
> - **Generated:** 2026-08-25T15:26:33Z
> - **Version:** pycode-kg 0.24.1
> - **Commit:** f3bb0cf (main)
> - **Index freshness:** [OK] working tree clean
> - **Platform:** macOS 27.0 | arm64 (arm) | turing | Python 3.12.13
> - **Graph:** 7000 nodes · 6515 edges (418 meaningful)
> - **Included directories:** src
> - **Excluded directories:** none
> - **Elapsed time:** 2s

# pycode_kg Analysis

**Generated:** 2026-08-25 15:26:33 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **pycode_kg** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
| :--- | :--- | :--- |
| [A] **Excellent** | **A** | 100.0 / 100 |

Score components:

| Component | Points | Max | Basis |
| :--- | ---: | ---: | :--- |
| Docstring coverage | 40.0 | 40 | 94.5% documented (full marks at 90%) |
| Dead code | 25.0 | 25 | 0 candidates / 362 definitions scanned (0.0%; zero points at 5%) |
| High fan-out | 20.0 | 20 | 0 orchestrator(s); −4 pts each |
| Circular dependencies | 15.0 | 15 | 0 cycle(s); −5 pts each |

---

## Baseline Metrics

| Metric | Value |
| :--- | :--- |
| **Total Nodes** | 7000 |
| **Total Edges** | 6515 |
| **Modules** | 56 (of 56 total) |
| **Functions** | 175 |
| **Classes** | 32 |
| **Methods** | 155 |

### Edge Distribution

| Relationship Type | Count |
| :--- | ---: |
| CALLS | 2458 |
| CONTAINS | 362 |
| IMPORTS | 490 |
| ATTR_ACCESS | 2233 |
| INHERITS | 11 |

_Excludes 961 `RESOLVES_TO` edges: internal symbol-stub resolutions, not relationships between two pieces of code. This table therefore does not sum to Total Edges._

---

## Fan-In Ranking

Most-called functions and methods — potential bottlenecks or core functionality.  Classes are omitted: instantiation counts are not architectural fan-in.

| # | Kind | Function | Module | Callers |
| ---: | :--- | :--- | ---: | :--- |
| 1 | function | `_get_kg()` | src/pycode_kg/mcp_server.py | **17** |
| 2 | function | `compute_coderank()` | src/pycode_kg/ranking/coderank.py | **7** |
| 3 | method | `to_markdown()` | src/pycode_kg/pycodekg_thorough_analysis.py | **6** |
| 4 | function | `_rewrap()` | src/pycode_kg/snapshots.py | **5** |
| 5 | method | `_add_edge()` | src/pycode_kg/visitor.py | **5** |
| 6 | method | `_get_node_id()` | src/pycode_kg/visitor.py | **5** |
| 7 | method | `_add_var_edge()` | src/pycode_kg/visitor.py | **5** |
| 8 | method | `extract()` | src/pycode_kg/graph.py | **4** |
| 9 | method | `_h2()` | src/pycode_kg/viz3d.py | **4** |
| 10 | method | `_extract_reads()` | src/pycode_kg/visitor.py | **4** |
| 11 | method | `_get_package_root()` | src/pycode_kg/pycodekg_thorough_analysis.py | **4** |
| 12 | function | `_run_pipeline()` | src/pycode_kg/cli/cmd_build_full.py | **3** |
| 13 | function | `load_snapshots_timeline()` | src/pycode_kg/viz3d_timeline.py | **3** |
| 14 | method | `nodes()` | src/pycode_kg/graph.py | **3** |

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
| `src/pycode_kg/snapshots.py` | 5 | 4 | 6 | 0 | 0.86 |  |
| `src/pycode_kg/visitor.py` | 1 | 1 | 1 | 1 | 0.33 |  |
| `src/pycode_kg/architecture.py` | 0 | 4 | 1 | 0 | 0.50 |  |
| `src/pycode_kg/app.py` | 14 | 0 | 0 | 2 | 0.00 | externally driven |
| `src/pycode_kg/analysis/centrality.py` | 1 | 5 | 3 | 0 | 0.75 |  |
| `src/pycode_kg/ranking/coderank.py` | 12 | 1 | 1 | 0 | 0.50 |  |
| `src/pycode_kg/pycodekg.py` | 8 | 2 | 3 | 2 | 0.50 |  |

---

## Key Call Chains

Deepest call chains in the codebase.

**Chain 1** (depth: 4)

```
pycodekg_thorough_analysis.py:_write_report → pycodekg_thorough_analysis.py:to_markdown → report.py:render_markdown → report.py:_bar
```

---

## Public API Surface

Definitions re-exported from an `__init__.py` or otherwise reachable as public entry points, ranked by fan-in.  Top 10 of 32 shown.

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
| `function` | 162 | 175 | [OK] 92.6% |
| `method` | 147 | 155 | [OK] 94.8% |
| `class` | 30 | 32 | [OK] 93.8% |
| `module` | 56 | 56 | [OK] 100.0% |
| **total** | **395** | **418** | **[OK] 94.5%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
| ---: | ---: | ---: | :--- |
| 1 | 0.106987 | 57 | `src/pycode_kg/viz3d.py` |
| 2 | 0.093902 | 25 | `src/pycode_kg/snapshots.py` |
| 3 | 0.088400 | 53 | `src/pycode_kg/pycodekg_thorough_analysis.py` |
| 4 | 0.066057 | 11 | `src/pycode_kg/pycodekg.py` |
| 5 | 0.057205 | 26 | `src/pycode_kg/mcp_server.py` |
| 6 | 0.049820 | 14 | `src/pycode_kg/analysis/centrality.py` |
| 7 | 0.039923 | 20 | `src/pycode_kg/visitor.py` |
| 8 | 0.038539 | 9 | `src/pycode_kg/graph.py` |
| 9 | 0.036212 | 18 | `src/pycode_kg/architecture.py` |
| 10 | 0.030974 | 4 | `src/pycode_kg/graph_html.py` |
| 11 | 0.029879 | 3 | `src/pycode_kg/ranking/cli_rank.py` |
| 12 | 0.029392 | 14 | `src/pycode_kg/ranking/coderank.py` |
| 13 | 0.022852 | 9 | `src/pycode_kg/kg.py` |
| 14 | 0.021609 | 15 | `src/pycode_kg/app.py` |
| 15 | 0.021076 | 7 | `src/pycode_kg/module/extractor.py` |

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
- Good docstring coverage: 94.5% of functions/methods/classes/modules documented

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

**11** INHERITS edges across **11** classes. Max depth: **1**.

| Class | Module | Depth | Parents | Children |
| :--- | :--- | ---: | ---: | ---: |
| `PyCodeKG` | src/pycode_kg/kg.py | 1 | 1 | 0 |
| `FunnelLayout` | src/pycode_kg/layout3d.py | 0 | 1 | 0 |
| `KGModule` | src/pycode_kg/module/base.py | 0 | 1 | 1 |
| `PyCodeKGExtractor` | src/pycode_kg/module/extractor.py | 0 | 1 | 0 |
| `CodeTreeLayout` | src/pycode_kg/scene3d.py | 0 | 1 | 0 |
| `Snapshot` | src/pycode_kg/snapshots.py | 0 | 1 | 0 |
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
| 1 | 2026-08-18 17:57:16 | chore/relativize-snapshot-db-path | 0.23.1 | 6793 | 6340 | 94.3% | +0 | +0 | +0.0% |
| 5 | 2026-08-18 12:55:57 | main | 0.23.1 | 6793 | 6340 | 94.3% | -19 | -21 | +0.0% |
| 7 | 2026-08-17 01:03:31 | refactor/promoted-leaf-helpers | 0.23.1 | 6812 | 6361 | 94.3% | -20 | -15 | -0.1% |
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
| `_compute_delta()` | method | src/pycode_kg/snapshots.py | 8 |

---

## CodeRank — Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds fan-in discovery and the concern queries below.  Top 20 of 25 shown.

| Rank | Score | Kind | Name | Module |
| ---: | ---: | :--- | :--- | :--- |
| 1 | 0.000572 | function | `_get_kg()` | src/pycode_kg/mcp_server.py |
| 2 | 0.000515 | method | `CodeGraph.extract()` | src/pycode_kg/graph.py |
| 3 | 0.000472 | function | `expr_to_name()` | src/pycode_kg/pycodekg.py |
| 4 | 0.000425 | function | `_rewrap()` | src/pycode_kg/snapshots.py |
| 5 | 0.000367 | function | `_load_dir_list()` | src/pycode_kg/config.py |
| 6 | 0.000321 | method | `PyCodeKGVisitor._get_node_id()` | src/pycode_kg/visitor.py |
| 7 | 0.000321 | method | `PyCodeKGVisitor._add_edge()` | src/pycode_kg/visitor.py |
| 8 | 0.000305 | function | `_own_scope_nodes()` | src/pycode_kg/pycodekg.py |
| 9 | 0.000290 | function | `_run_pipeline()` | src/pycode_kg/cli/cmd_build_full.py |
| 10 | 0.000284 | function | `_format_table()` | src/pycode_kg/cli/cmd_centrality.py |
| 11 | 0.000261 | method | `PyCodeKGVisitor._add_var_edge()` | src/pycode_kg/visitor.py |
| 12 | 0.000257 | function | `_load_store()` | src/pycode_kg/app.py |
| 13 | 0.000249 | function | `load_snapshots_timeline()` | src/pycode_kg/viz3d_timeline.py |
| 14 | 0.000246 | function | `_annotation_class_name()` | src/pycode_kg/pycodekg.py |
| 15 | 0.000235 | method | `MainWindow._h2()` | src/pycode_kg/viz3d.py |
| 16 | 0.000232 | method | `PyCodeKGVisitor._extract_reads()` | src/pycode_kg/visitor.py |
| 17 | 0.000229 | function | `delta_to_dict()` | src/pycode_kg/snapshots.py |
| 18 | 0.000229 | function | `delta_from_dict()` | src/pycode_kg/snapshots.py |
| 19 | 0.000227 | function | `_remove_highlight_actors()` | src/pycode_kg/viz3d.py |
| 20 | 0.000224 | method | `KGVisualizer._load_scores()` | src/pycode_kg/viz3d.py |

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
| 1 | 0.7754 | function | `_load_store()` | src/pycode_kg/app.py |
| 2 | 0.7329 | function | `_get_store()` | src/pycode_kg/app.py |
| 3 | 0.7306 | method | `ArchitectureAnalyzer.__init__()` | src/pycode_kg/architecture.py |
| 4 | 0.7302 | method | `SnapshotManager.save_snapshot()` | src/pycode_kg/snapshots.py |
| 5 | 0.7258 | function | `_load_kg()` | src/pycode_kg/app.py |

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
| 1 | 0.7925 | method | `PyCodeKGVisitor._add_edge()` | src/pycode_kg/visitor.py |
| 2 | 0.7615 | method | `CodeGraph.edges()` | src/pycode_kg/graph.py |
| 3 | 0.7553 | function | `induce_query_subgraph()` | src/pycode_kg/ranking/coderank.py |
| 4 | 0.75 | function | `query_codebase()` | src/pycode_kg/mcp_server.py |
| 5 | 0.7494 | function | `compute_seed_proximity()` | src/pycode_kg/ranking/coderank.py |

---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 3.0s*
