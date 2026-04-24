> **Analysis Report Metadata**
> - **Generated:** 2026-04-24T13:40:24Z
> - **Version:** pycode-kg 0.15.0
> - **Commit:** a5dedca (main)
> - **Platform:** macOS 26.4.1 | arm64 (arm) | Turing | Python 3.12.13
> - **Graph:** 7282 nodes · 7229 edges (477 meaningful)
> - **Included directories:** src
> - **Excluded directories:** none
> - **Elapsed time:** 4s

# pycode_kg Analysis

**Generated:** 2026-04-24 13:40:24 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **pycode_kg** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
|----------------|-------|-------|
| [A] **Excellent** | **A** | 92 / 100 |

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| **Total Nodes** | 7282 |
| **Total Edges** | 7229 |
| **Modules** | 56 (of 56 total) |
| **Functions** | 160 |
| **Classes** | 46 |
| **Methods** | 215 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 2557 |
| CONTAINS | 421 |
| IMPORTS | 426 |
| ATTR_ACCESS | 2358 |
| INHERITS | 14 |

---

## Fan-In Ranking

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers |
|---|----------|--------|---------|
| 1 | `_get_kg()` | src/pycode_kg/mcp_server.py | **17** |
| 2 | `close()` | src/pycode_kg/module/base.py | **16** |
| 3 | `close()` | src/pycode_kg/store.py | **16** |
| 4 | `node()` | src/pycode_kg/store.py | **14** |
| 5 | `con()` | src/pycode_kg/store.py | **12** |
| 6 | `store()` | src/pycode_kg/module/base.py | **8** |
| 7 | `compute_coderank()` | src/pycode_kg/ranking/coderank.py | **7** |
| 8 | `to_json()` | src/pycode_kg/module/types.py | **6** |
| 9 | `to_markdown()` | src/pycode_kg/module/types.py | **6** |
| 10 | `extract()` | src/pycode_kg/graph.py | **5** |
| 11 | `_add_edge()` | src/pycode_kg/visitor.py | **5** |
| 12 | `_get_node_id()` | src/pycode_kg/visitor.py | **5** |
| 13 | `_add_var_edge()` | src/pycode_kg/visitor.py | **5** |
| 14 | `clear()` | src/pycode_kg/store.py | **5** |
| 15 | `to_dict()` | src/pycode_kg/module/types.py | **4** |


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
| `src/pycode_kg/viz3d.py` | 7 | 3 | 0 | 0 | 0.00 |
| `src/pycode_kg/pycodekg_thorough_analysis.py` | 5 | 4 | 3 | 1 | 0.20 |
| `src/pycode_kg/store.py` | 3 | 2 | 9 | 2 | 0.17 |
| `src/pycode_kg/mcp_server.py` | 25 | 0 | 0 | 3 | 0.75 |
| `src/pycode_kg/module/types.py` | 11 | 4 | 4 | 0 | 0.00 |
| `src/pycode_kg/module/base.py` | 3 | 1 | 3 | 4 | 0.50 |
| `src/pycode_kg/snapshots.py` | 4 | 4 | 5 | 0 | 0.00 |
| `src/pycode_kg/index.py` | 5 | 4 | 6 | 0 | 0.00 |
| `src/pycode_kg/visitor.py` | 1 | 1 | 1 | 1 | 0.33 |
| `src/pycode_kg/architecture.py` | 0 | 4 | 1 | 1 | 0.33 |

---

## Key Call Chains

Deepest call chains in the codebase.

**Chain 1** (depth: 3)

```
__exit__ → close → close
```

---

## Public API Surface

Identified public APIs (module-level functions with high usage).

| Function | Module | Fan-In | Type |
|----------|--------|--------|------|
| `SnapshotManager()` | src/pycode_kg/snapshots.py | 9 | class |
| `GraphStore()` | src/pycode_kg/store.py | 9 | class |
| `PyCodeKG()` | src/pycode_kg/kg.py | 9 | class |
| `query()` | src/pycode_kg/cli/cmd_query.py | 8 | function |
| `compute_coderank()` | src/pycode_kg/ranking/coderank.py | 7 | function |
| `StructuralImportanceRanker()` | src/pycode_kg/analysis/centrality.py | 6 | class |
| `build()` | src/pycode_kg/cli/cmd_build_full.py | 4 | function |
| `SentenceTransformerEmbedder()` | src/pycode_kg/index.py | 4 | class |
| `CodeGraph()` | src/pycode_kg/graph.py | 4 | class |
| `norm()` | src/pycode_kg/analysis/framework_detector.py | 4 | function |
---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 142 | 160 | [OK] 88.8% |
| `method` | 204 | 215 | [OK] 94.9% |
| `class` | 44 | 46 | [OK] 95.7% |
| `module` | 51 | 56 | [OK] 91.1% |
| **total** | **441** | **477** | **[OK] 92.5%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.138829 | 27 | `src/pycode_kg/store.py` |
| 2 | 0.090219 | 48 | `src/pycode_kg/viz3d.py` |
| 3 | 0.086799 | 25 | `src/pycode_kg/module/base.py` |
| 4 | 0.078526 | 25 | `src/pycode_kg/snapshots.py` |
| 5 | 0.047488 | 26 | `src/pycode_kg/module/types.py` |
| 6 | 0.045576 | 23 | `src/pycode_kg/index.py` |
| 7 | 0.043744 | 37 | `src/pycode_kg/pycodekg_thorough_analysis.py` |
| 8 | 0.036450 | 14 | `src/pycode_kg/analysis/centrality.py` |
| 9 | 0.034582 | 26 | `src/pycode_kg/mcp_server.py` |
| 10 | 0.033238 | 8 | `src/pycode_kg/pycodekg.py` |
| 11 | 0.032332 | 20 | `src/pycode_kg/visitor.py` |
| 12 | 0.031431 | 17 | `src/pycode_kg/layout3d.py` |
| 13 | 0.031146 | 9 | `src/pycode_kg/graph.py` |
| 14 | 0.029564 | 16 | `src/pycode_kg/module/extractor.py` |
| 15 | 0.025288 | 18 | `src/pycode_kg/architecture.py` |



---

## Code Quality Issues

- [WARN] 1 functions with high fan-out -- potential orchestrators or god objects
- [WARN] `viz3d.py` has 47 functions/methods/classes -- consider splitting into focused submodules
- [WARN] `pycodekg_thorough_analysis.py` has 36 functions/methods/classes -- consider splitting into focused submodules

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No obvious dead code detected
- Good docstring coverage: 92.5% of functions/methods/classes/modules documented

---

## Recommendations

### Immediate Actions
1. **Refactor high fan-out orchestrators** — `init` calls 43 functions; consider splitting into smaller, focused coordinators

### Medium-term Refactoring
1. **Harden high fan-in functions** — `_get_kg`, `close`, `close` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `SnapshotManager`, `GraphStore`, `PyCodeKG`
2. **Enforce layer boundaries** — add linting or CI checks to prevent unexpected cross-module dependencies as the codebase grows
3. **Monitor hot paths** — instrument the high fan-in functions identified here to catch performance regressions early

---

## Inheritance Hierarchy

**14** INHERITS edges across **15** classes. Max depth: **1**.

| Class | Module | Depth | Parents | Children |
|-------|--------|-------|---------|----------|
| `SentenceTransformerEmbedder` | src/pycode_kg/index.py | 1 | 1 | 0 |
| `PyCodeKG` | src/pycode_kg/kg.py | 1 | 1 | 0 |
| `AlliumLayout` | src/pycode_kg/layout3d.py | 1 | 1 | 0 |
| `LayerCakeLayout` | src/pycode_kg/layout3d.py | 1 | 1 | 0 |
| `PyCodeKGExtractor` | src/pycode_kg/module/extractor.py | 1 | 1 | 0 |
| `Embedder` | src/pycode_kg/index.py | 0 | 0 | 1 |
| `Layout3D` | src/pycode_kg/layout3d.py | 0 | 1 | 2 |
| `KGModule` | src/pycode_kg/module/base.py | 0 | 1 | 1 |
| `KGExtractor` | src/pycode_kg/module/extractor.py | 0 | 1 | 1 |
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
| 1 | 2026-04-24 01:10:44 | main | 0.14.1 | 7282 | 7229 | 92.5% | +0 | +0 | +0.0% |
| 2 | 2026-04-24 01:09:56 | main | 0.14.1 | 7282 | 7229 | 92.5% | +0 | +0 | +0.0% |
| 3 | 2026-04-24 01:08:48 | main | 0.14.1 | 7282 | 7229 | 92.5% | +20 | +12 | +0.0% |
| 4 | 2026-04-21 13:23:37 | main | 0.14.1 | 7262 | 7217 | 92.5% | +75 | +73 | -0.1% |
| 5 | 2026-04-20 23:17:26 | main | 0.14.1 | 7187 | 7144 | 92.6% | +0 | +0 | +0.0% |
| 6 | 2026-04-20 17:27:44 | main | 0.14.0 | 7187 | 7144 | 92.6% | +9 | +5 | +0.0% |
| 7 | 2026-04-13 02:48:59 | main | 0.12.0 | 7178 | 7139 | 92.6% | +0 | +1 | +0.0% |
| 8 | 2026-04-13 02:41:47 | main | 0.12.0 | 7178 | 7138 | 92.6% | -2 | -3 | +0.0% |
| 9 | 2026-04-13 02:34:25 | main | 0.12.0 | 7180 | 7141 | 92.6% | +111 | +131 | +0.1% |
| 10 | 2026-04-07 17:43:34 | main | 0.12.0 | 7069 | 7010 | 92.5% | +23 | +23 | +0.0% |


---

## Appendix: Orphaned Code

Functions with zero callers (potential dead code):

No orphaned functions detected.
---

## CodeRank -- Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000570 | method | `GraphStore.con` | src/pycode_kg/store.py |
| 2 | 0.000534 | method | `KGModule.store` | src/pycode_kg/module/base.py |
| 3 | 0.000494 | method | `CodeGraph.extract` | src/pycode_kg/graph.py |
| 4 | 0.000481 | function | `_get_kg` | src/pycode_kg/mcp_server.py |
| 5 | 0.000353 | function | `_load_dir_list` | src/pycode_kg/config.py |
| 6 | 0.000346 | function | `metrics_to_dict` | src/pycode_kg/snapshots.py |
| 7 | 0.000309 | method | `PyCodeKGVisitor._get_node_id` | src/pycode_kg/visitor.py |
| 8 | 0.000309 | method | `PyCodeKGVisitor._add_edge` | src/pycode_kg/visitor.py |
| 9 | 0.000303 | function | `expr_to_name` | src/pycode_kg/pycodekg.py |
| 10 | 0.000300 | method | `SnippetPack.to_dict` | src/pycode_kg/module/types.py |
| 11 | 0.000285 | function | `delta_to_dict` | src/pycode_kg/snapshots.py |
| 12 | 0.000279 | function | `_run_pipeline` | src/pycode_kg/cli/cmd_build_full.py |
| 13 | 0.000272 | function | `_format_table` | src/pycode_kg/cli/cmd_centrality.py |
| 14 | 0.000270 | class | `SnapshotDelta` | src/pycode_kg/snapshots.py |
| 15 | 0.000253 | function | `delta_from_dict` | src/pycode_kg/snapshots.py |
| 16 | 0.000251 | method | `PyCodeKGVisitor._add_var_edge` | src/pycode_kg/visitor.py |
| 17 | 0.000248 | function | `_load_store` | src/pycode_kg/app.py |
| 18 | 0.000246 | class | `SnapshotMetrics` | src/pycode_kg/snapshots.py |
| 19 | 0.000242 | method | `GraphStore.close` | src/pycode_kg/store.py |
| 20 | 0.000242 | method | `SentenceTransformerEmbedder.embed_texts` | src/pycode_kg/index.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7525 | function | `_load_kg` | src/pycode_kg/app.py |
| 2 | 0.7523 | function | `_init_state` | src/pycode_kg/app.py |
| 3 | 0.7439 | function | `main` | src/pycode_kg/mcp_server.py |
| 4 | 0.7436 | method | `PyCodeKGExtractor.__init__` | src/pycode_kg/module/extractor.py |
| 5 | 0.7365 | method | `KGExtractor.__init__` | src/pycode_kg/module/extractor.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.8296 | method | `KGModule.store` | src/pycode_kg/module/base.py |
| 2 | 0.7669 | function | `_load_store` | src/pycode_kg/app.py |
| 3 | 0.7293 | method | `SemanticIndex.build` | src/pycode_kg/index.py |
| 4 | 0.7164 | function | `_get_store` | src/pycode_kg/app.py |
| 5 | 0.7142 | method | `ArchitectureAnalyzer.__init__` | src/pycode_kg/architecture.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `SemanticIndex.search` | src/pycode_kg/index.py |
| 2 | 0.7332 | method | `KGModule.query` | src/pycode_kg/module/base.py |
| 3 | 0.7297 | function | `query_codebase` | src/pycode_kg/mcp_server.py |
| 4 | 0.709 | function | `query_ranked` | src/pycode_kg/mcp_server.py |
| 5 | 0.7063 | method | `SentenceTransformerEmbedder.embed_query` | src/pycode_kg/index.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `LayerCakeLayout.compute` | src/pycode_kg/layout3d.py |
| 2 | 0.747 | method | `AlliumLayout.compute` | src/pycode_kg/layout3d.py |
| 3 | 0.7461 | method | `Layout3D.compute` | src/pycode_kg/layout3d.py |
| 4 | 0.7456 | method | `PyCodeKGVisitor._add_edge` | src/pycode_kg/visitor.py |
| 5 | 0.7206 | method | `GraphStore.edges_from` | src/pycode_kg/store.py |



---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 4.9s*
