> **Analysis Report Metadata**
> - **Generated:** 2026-04-19T18:28:01Z
> - **Version:** pycode-kg 0.14.0
> - **Commit:** bd9d858 (main)
> - **Platform:** macOS 26.4.1 | arm64 (arm) | Turing | Python 3.12.13
> - **Graph:** 7178 nodes · 7139 edges (473 meaningful)
> - **Included directories:** src
> - **Excluded directories:** none
> - **Elapsed time:** 5s

# pycode_kg Analysis

**Generated:** 2026-04-19 18:28:01 UTC

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
| **Total Nodes** | 7178 |
| **Total Edges** | 7139 |
| **Modules** | 56 (of 56 total) |
| **Functions** | 156 |
| **Classes** | 46 |
| **Methods** | 215 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 2516 |
| CONTAINS | 417 |
| IMPORTS | 426 |
| ATTR_ACCESS | 2335 |
| INHERITS | 14 |

---

## Fan-In Ranking

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers |
|---|----------|--------|---------|
| 1 | `close()` | src/pycode_kg/module/base.py | **16** |
| 2 | `close()` | src/pycode_kg/store.py | **16** |
| 3 | `_get_kg()` | src/pycode_kg/mcp_server.py | **15** |
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
| `src/pycode_kg/module/types.py` | 11 | 4 | 4 | 0 | 0.00 |
| `src/pycode_kg/module/base.py` | 3 | 1 | 3 | 4 | 0.50 |
| `src/pycode_kg/snapshots.py` | 4 | 4 | 5 | 0 | 0.00 |
| `src/pycode_kg/mcp_server.py` | 23 | 0 | 0 | 3 | 0.75 |
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
| `CodeGraph()` | src/pycode_kg/graph.py | 4 | class |
| `SentenceTransformerEmbedder()` | src/pycode_kg/index.py | 4 | class |
| `norm()` | src/pycode_kg/analysis/framework_detector.py | 4 | function |
---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 139 | 156 | [OK] 89.1% |
| `method` | 204 | 215 | [OK] 94.9% |
| `class` | 44 | 46 | [OK] 95.7% |
| `module` | 51 | 56 | [OK] 91.1% |
| **total** | **438** | **473** | **[OK] 92.6%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.139276 | 27 | `src/pycode_kg/store.py` |
| 2 | 0.090735 | 48 | `src/pycode_kg/viz3d.py` |
| 3 | 0.087131 | 25 | `src/pycode_kg/module/base.py` |
| 4 | 0.078995 | 25 | `src/pycode_kg/snapshots.py` |
| 5 | 0.047802 | 26 | `src/pycode_kg/module/types.py` |
| 6 | 0.045844 | 23 | `src/pycode_kg/index.py` |
| 7 | 0.044011 | 37 | `src/pycode_kg/pycodekg_thorough_analysis.py` |
| 8 | 0.036661 | 14 | `src/pycode_kg/analysis/centrality.py` |
| 9 | 0.033370 | 8 | `src/pycode_kg/pycodekg.py` |
| 10 | 0.032505 | 20 | `src/pycode_kg/visitor.py` |
| 11 | 0.031612 | 17 | `src/pycode_kg/layout3d.py` |
| 12 | 0.031192 | 9 | `src/pycode_kg/graph.py` |
| 13 | 0.031142 | 24 | `src/pycode_kg/mcp_server.py` |
| 14 | 0.029736 | 16 | `src/pycode_kg/module/extractor.py` |
| 15 | 0.025433 | 18 | `src/pycode_kg/architecture.py` |



---

## Code Quality Issues

- [WARN] 1 functions with high fan-out -- potential orchestrators or god objects

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No obvious dead code detected
- Good docstring coverage: 92.6% of functions/methods/classes/modules documented

---

## Recommendations

### Immediate Actions
1. **Refactor high fan-out orchestrators** — `init` calls 43 functions; consider splitting into smaller, focused coordinators

### Medium-term Refactoring
1. **Harden high fan-in functions** — `close`, `close`, `_get_kg` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
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
| 1 | 2026-04-13 02:48:59 | main | 0.12.0 | 7178 | 7139 | 92.6% | +0 | +1 | +0.0% |
| 2 | 2026-04-13 02:41:47 | main | 0.12.0 | 7178 | 7138 | 92.6% | -2 | -3 | +0.0% |
| 3 | 2026-04-13 02:34:25 | main | 0.12.0 | 7180 | 7141 | 92.6% | +111 | +131 | +0.1% |
| 4 | 2026-04-07 17:43:34 | main | 0.12.0 | 7069 | 7010 | 92.5% | +23 | +23 | +0.0% |
| 5 | 2026-04-07 13:25:43 | main | 0.11.0 | 7046 | 6987 | 92.5% | -12 | -12 | -0.2% |
| 6 | 2026-04-06 13:21:44 | main | 0.11.0 | 7058 | 6999 | 92.7% | +0 | +0 | +0.0% |
| 7 | 2026-03-22 16:55:23 | main | 0.9.3 | 7058 | 6999 | 92.7% | +24 | +13 | +0.0% |
| 8 | 2026-03-20 02:42:41 | main | 0.9.3 | 7034 | 6986 | 92.7% | -12 | -8 | +0.7% |
| 9 | 2026-03-20 00:46:03 | main | 0.9.3 | 7046 | 6994 | 92.0% | +79 | +94 | +0.1% |
| 10 | 2026-03-19 22:40:46 | main | 0.9.3 | 6967 | 6900 | 91.9% | -24 | -52 | -1.1% |


---

## Appendix: Orphaned Code

Functions with zero callers (potential dead code):

No orphaned functions detected.
---

## CodeRank -- Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000599 | method | `GraphStore.con` | src/pycode_kg/store.py |
| 2 | 0.000542 | method | `KGModule.store` | src/pycode_kg/module/base.py |
| 3 | 0.000501 | method | `CodeGraph.extract` | src/pycode_kg/graph.py |
| 4 | 0.000446 | function | `_get_kg` | src/pycode_kg/mcp_server.py |
| 5 | 0.000358 | function | `_load_dir_list` | src/pycode_kg/config.py |
| 6 | 0.000351 | function | `metrics_to_dict` | src/pycode_kg/snapshots.py |
| 7 | 0.000313 | method | `PyCodeKGVisitor._get_node_id` | src/pycode_kg/visitor.py |
| 8 | 0.000313 | method | `PyCodeKGVisitor._add_edge` | src/pycode_kg/visitor.py |
| 9 | 0.000307 | function | `expr_to_name` | src/pycode_kg/pycodekg.py |
| 10 | 0.000304 | method | `SnippetPack.to_dict` | src/pycode_kg/module/types.py |
| 11 | 0.000289 | function | `delta_to_dict` | src/pycode_kg/snapshots.py |
| 12 | 0.000283 | function | `_run_pipeline` | src/pycode_kg/cli/cmd_build_full.py |
| 13 | 0.000276 | function | `_format_table` | src/pycode_kg/cli/cmd_centrality.py |
| 14 | 0.000274 | class | `SnapshotDelta` | src/pycode_kg/snapshots.py |
| 15 | 0.000257 | function | `delta_from_dict` | src/pycode_kg/snapshots.py |
| 16 | 0.000254 | method | `PyCodeKGVisitor._add_var_edge` | src/pycode_kg/visitor.py |
| 17 | 0.000251 | function | `_load_store` | src/pycode_kg/app.py |
| 18 | 0.000250 | class | `SnapshotMetrics` | src/pycode_kg/snapshots.py |
| 19 | 0.000245 | method | `GraphStore.close` | src/pycode_kg/store.py |
| 20 | 0.000245 | method | `SentenceTransformerEmbedder.embed_texts` | src/pycode_kg/index.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.753 | function | `_init_state` | src/pycode_kg/app.py |
| 2 | 0.7526 | function | `_load_kg` | src/pycode_kg/app.py |
| 3 | 0.7433 | method | `PyCodeKGExtractor.__init__` | src/pycode_kg/module/extractor.py |
| 4 | 0.7431 | function | `main` | src/pycode_kg/mcp_server.py |
| 5 | 0.7361 | method | `KGExtractor.__init__` | src/pycode_kg/module/extractor.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.8297 | method | `KGModule.store` | src/pycode_kg/module/base.py |
| 2 | 0.7664 | function | `_load_store` | src/pycode_kg/app.py |
| 3 | 0.7296 | method | `SemanticIndex.build` | src/pycode_kg/index.py |
| 4 | 0.7162 | function | `_get_store` | src/pycode_kg/app.py |
| 5 | 0.7142 | method | `ArchitectureAnalyzer.__init__` | src/pycode_kg/architecture.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `SemanticIndex.search` | src/pycode_kg/index.py |
| 2 | 0.7324 | method | `KGModule.query` | src/pycode_kg/module/base.py |
| 3 | 0.7228 | function | `query_codebase` | src/pycode_kg/mcp_server.py |
| 4 | 0.7082 | function | `query_ranked` | src/pycode_kg/mcp_server.py |
| 5 | 0.7054 | function | `query` | src/pycode_kg/cli/cmd_query.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `LayerCakeLayout.compute` | src/pycode_kg/layout3d.py |
| 2 | 0.747 | method | `AlliumLayout.compute` | src/pycode_kg/layout3d.py |
| 3 | 0.7461 | method | `PyCodeKGVisitor._add_edge` | src/pycode_kg/visitor.py |
| 4 | 0.7461 | method | `Layout3D.compute` | src/pycode_kg/layout3d.py |
| 5 | 0.7206 | method | `GraphStore.edges_from` | src/pycode_kg/store.py |



---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 5.0s*
