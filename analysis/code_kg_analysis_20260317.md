> **Analysis Report Metadata**
> - **Generated:** 2026-03-17T21:32:07Z
> - **Version:** pycode-kg 0.9.1
> - **Commit:** ee4b7d1 (main)
> - **Platform:** macOS 26.3 | arm64 (arm) | Turing | Python 3.12.13
> - **Graph:** 6982 nodes · 6943 edges (458 meaningful)
> - **Included directories:** src
> - **Excluded directories:** none
> - **Elapsed time:** 3s

# pycode_kg Analysis

**Generated:** 2026-03-17 21:32:07 UTC

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
| **Total Nodes** | 6982 |
| **Total Edges** | 6943 |
| **Modules** | 55 (of 55 total) |
| **Functions** | 148 |
| **Classes** | 47 |
| **Methods** | 208 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 2452 |
| CONTAINS | 403 |
| IMPORTS | 412 |
| ATTR_ACCESS | 2248 |
| INHERITS | 12 |

---

## Fan-In Ranking

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers |
|---|----------|--------|---------|
| 1 | `_get_kg()` | src/pycode_kg/mcp_server.py | **15** |
| 2 | `close()` | src/pycode_kg/module/base.py | **15** |
| 3 | `close()` | src/pycode_kg/store.py | **15** |
| 4 | `node()` | src/pycode_kg/store.py | **14** |
| 5 | `con()` | src/pycode_kg/store.py | **12** |
| 6 | `store()` | src/pycode_kg/module/base.py | **8** |
| 7 | `compute_coderank()` | src/pycode_kg/ranking/coderank.py | **7** |
| 8 | `to_json()` | src/pycode_kg/module/types.py | **6** |
| 9 | `to_markdown()` | src/pycode_kg/module/types.py | **6** |
| 10 | `extract()` | src/pycode_kg/graph.py | **5** |
| 11 | `_add_edge()` | src/pycode_kg/visitor.py | **5** |
| 12 | `_get_node_id()` | src/pycode_kg/visitor.py | **5** |
| 13 | `to_dict()` | src/pycode_kg/module/types.py | **5** |
| 14 | `load_manifest()` | src/pycode_kg/snapshots.py | **5** |
| 15 | `_add_var_edge()` | src/pycode_kg/visitor.py | **5** |


**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:
- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.

| # | Function | Module | Calls | Type |
|---|----------|--------|-------|------|
| 1 | `__init__()` | src/pycode_kg/viz3d.py | **95** | Orchestrator |

---

## Module Architecture

Top modules by dependency coupling and cohesion (showing up to 10 with activity).
Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.

| Module | Functions | Classes | Incoming | Outgoing | Cohesion |
|--------|-----------|---------|----------|----------|----------|
| `src/pycode_kg/viz3d.py` | 9 | 3 | 0 | 0 | 0.00 |
| `src/pycode_kg/pycodekg_thorough_analysis.py` | 5 | 4 | 3 | 1 | 0.20 |
| `src/pycode_kg/store.py` | 3 | 2 | 9 | 2 | 0.17 |
| `src/pycode_kg/module/types.py` | 11 | 4 | 4 | 0 | 0.00 |
| `src/pycode_kg/module/base.py` | 3 | 1 | 3 | 4 | 0.50 |
| `src/pycode_kg/snapshots.py` | 0 | 5 | 5 | 0 | 0.00 |
| `src/pycode_kg/mcp_server.py` | 23 | 0 | 0 | 3 | 0.75 |
| `src/pycode_kg/index.py` | 5 | 4 | 5 | 0 | 0.00 |
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
| `PyCodeKG()` | src/pycode_kg/kg.py | 8 | class |
| `GraphStore()` | src/pycode_kg/store.py | 8 | class |
| `SnapshotManager()` | src/pycode_kg/snapshots.py | 7 | class |
| `compute_coderank()` | src/pycode_kg/ranking/coderank.py | 7 | function |
| `StructuralImportanceRanker()` | src/pycode_kg/analysis/centrality.py | 6 | class |
| `CodeGraph()` | src/pycode_kg/graph.py | 4 | class |
| `SentenceTransformerEmbedder()` | src/pycode_kg/index.py | 4 | class |
| `build()` | src/pycode_kg/cli/cmd_build_full.py | 4 | function |
| `norm()` | src/pycode_kg/analysis/framework_detector.py | 4 | function |
| `norm()` | src/pycode_kg/analysis/hybrid_rank.py | 4 | function |
---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 128 | 148 | [OK] 86.5% |
| `method` | 203 | 208 | [OK] 97.6% |
| `class` | 45 | 47 | [OK] 95.7% |
| `module` | 50 | 55 | [OK] 90.9% |
| **total** | **426** | **458** | **[OK] 93.0%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.140417 | 27 | `src/pycode_kg/store.py` |
| 2 | 0.091642 | 25 | `src/pycode_kg/snapshots.py` |
| 3 | 0.090244 | 25 | `src/pycode_kg/module/base.py` |
| 4 | 0.082483 | 40 | `src/pycode_kg/viz3d.py` |
| 5 | 0.049369 | 26 | `src/pycode_kg/module/types.py` |
| 6 | 0.045072 | 37 | `src/pycode_kg/pycodekg_thorough_analysis.py` |
| 7 | 0.044687 | 23 | `src/pycode_kg/index.py` |
| 8 | 0.037285 | 14 | `src/pycode_kg/analysis/centrality.py` |
| 9 | 0.033657 | 8 | `src/pycode_kg/pycodekg.py` |
| 10 | 0.033255 | 20 | `src/pycode_kg/visitor.py` |
| 11 | 0.032355 | 17 | `src/pycode_kg/layout3d.py` |
| 12 | 0.031957 | 24 | `src/pycode_kg/mcp_server.py` |
| 13 | 0.030518 | 9 | `src/pycode_kg/graph.py` |
| 14 | 0.029859 | 16 | `src/pycode_kg/module/extractor.py` |
| 15 | 0.026103 | 18 | `src/pycode_kg/architecture.py` |



---

## Code Quality Issues

- [WARN] 1 orphaned functions found (`_analyze_dependencies`) -- consider archiving or documenting
- [WARN] 1 functions with high fan-out -- potential orchestrators or god objects

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- Good docstring coverage: 93.0% of functions/methods/classes/modules documented

---

## Recommendations

### Immediate Actions
1. **Remove or archive orphaned functions** — `_analyze_dependencies` have zero callers and add maintenance burden
2. **Refactor high fan-out orchestrators** — `__init__` calls 95 functions; consider splitting into smaller, focused coordinators

### Medium-term Refactoring
1. **Harden high fan-in functions** — `_get_kg`, `close`, `close` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `PyCodeKG`, `GraphStore`, `SnapshotManager`
2. **Enforce layer boundaries** — add linting or CI checks to prevent unexpected cross-module dependencies as the codebase grows
3. **Monitor hot paths** — instrument the high fan-in functions identified here to catch performance regressions early

---

## Inheritance Hierarchy

**12** INHERITS edges across **13** classes. Max depth: **1**.

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
| `PyCodeKGVisitor` | src/pycode_kg/visitor.py | 0 | 1 | 0 |
| `DocstringPopup` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |
| `KGVisualizer` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |
| `MainWindow` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |


---

## Snapshot History

Recent snapshots in reverse chronological order. Δ columns show change vs. the immediately preceding snapshot.

| # | Timestamp | Branch | Version | Nodes | Edges | Coverage | Δ Nodes | Δ Edges | Δ Coverage |
|---|-----------|--------|---------|-------|-------|----------|---------|---------|------------|
| 1 | 2026-03-16 22:01:14 | main | 0.9.0 | 6941 | 6922 | 93.0% | +0 | +0 | +0.0% |
| 2 | 2026-03-15 03:59:18 | feature/kg-factory | 0.9.0 | 6941 | 6922 | 93.0% | +160 | +359 | +0.3% |
| 3 | 2026-03-14 23:58:50 | main | 0.81b | 6781 | 6563 | 92.7% | -1 | -2 | +0.0% |
| 4 | 2026-03-14 21:46:51 | develop | 0.8.1 | 6782 | 6565 | 92.7% | +0 | +0 | +0.0% |
| 5 | 2026-03-14 21:15:43 | refactor/cleanup-output | 0.8.1 | 6782 | 6565 | 92.7% | +0 | +0 | +0.0% |
| 6 | 2026-03-14 18:14:58 | main | 0.8.1 | 6782 | 6565 | 92.7% | +0 | +0 | +0.0% |
| 7 | 2026-03-14 18:04:40 | main | 0.8.1 | 6782 | 6565 | 92.7% | +0 | +0 | +0.0% |
| 8 | 2026-03-14 17:54:01 | main | 0.8.1 | 6782 | 6565 | 92.7% | +41 | +30 | +0.0% |
| 9 | 2026-03-13 17:45:53 | main | 0.8.1 | 6741 | 6535 | 92.7% | +0 | +0 | +0.0% |
| 10 | 2026-03-13 04:14:50 | main | 0.8.0 | 6741 | 6535 | 92.7% | +0 | +0 | +0.0% |


---

## Appendix: Orphaned Code

Functions with zero callers (potential dead code):

| Function | Module | Lines |
|----------|--------|-------|
| `_analyze_dependencies()` | src/pycode_kg/pycodekg_thorough_analysis.py | 61 |
---

## CodeRank -- Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000616 | method | `GraphStore.con` | src/pycode_kg/store.py |
| 2 | 0.000558 | method | `KGModule.store` | src/pycode_kg/module/base.py |
| 3 | 0.000516 | method | `CodeGraph.extract` | src/pycode_kg/graph.py |
| 4 | 0.000459 | function | `_get_kg` | src/pycode_kg/mcp_server.py |
| 5 | 0.000368 | function | `_load_dir_list` | src/pycode_kg/config.py |
| 6 | 0.000335 | class | `SnapshotDelta` | src/pycode_kg/snapshots.py |
| 7 | 0.000322 | method | `PyCodeKGVisitor._get_node_id` | src/pycode_kg/visitor.py |
| 8 | 0.000322 | method | `PyCodeKGVisitor._add_edge` | src/pycode_kg/visitor.py |
| 9 | 0.000316 | function | `expr_to_name` | src/pycode_kg/pycodekg.py |
| 10 | 0.000313 | method | `SnippetPack.to_dict` | src/pycode_kg/module/types.py |
| 11 | 0.000302 | class | `SnapshotManifest` | src/pycode_kg/snapshots.py |
| 12 | 0.000284 | function | `_format_table` | src/pycode_kg/cli/cmd_centrality.py |
| 13 | 0.000283 | method | `SnapshotManager.load_manifest` | src/pycode_kg/snapshots.py |
| 14 | 0.000262 | method | `PyCodeKGVisitor._add_var_edge` | src/pycode_kg/visitor.py |
| 15 | 0.000259 | function | `_load_store` | src/pycode_kg/app.py |
| 16 | 0.000252 | method | `GraphStore.close` | src/pycode_kg/store.py |
| 17 | 0.000252 | method | `SentenceTransformerEmbedder.embed_texts` | src/pycode_kg/index.py |
| 18 | 0.000252 | method | `PyCodeKGExtractor.node_kinds` | src/pycode_kg/module/extractor.py |
| 19 | 0.000252 | method | `KGModule.close` | src/pycode_kg/module/base.py |
| 20 | 0.000250 | function | `load_snapshots_timeline` | src/pycode_kg/viz3d_timeline.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7533 | function | `_init_state` | src/pycode_kg/app.py |
| 2 | 0.748 | function | `_load_kg` | src/pycode_kg/app.py |
| 3 | 0.7414 | function | `main` | src/pycode_kg/mcp_server.py |
| 4 | 0.7405 | method | `PyCodeKGExtractor.__init__` | src/pycode_kg/module/extractor.py |
| 5 | 0.7305 | method | `KGExtractor.__init__` | src/pycode_kg/module/extractor.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.8239 | method | `KGModule.store` | src/pycode_kg/module/base.py |
| 2 | 0.7586 | function | `_load_store` | src/pycode_kg/app.py |
| 3 | 0.7197 | method | `SemanticIndex.build` | src/pycode_kg/index.py |
| 4 | 0.7104 | function | `_get_store` | src/pycode_kg/app.py |
| 5 | 0.7077 | method | `GraphStore.__init__` | src/pycode_kg/store.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `SemanticIndex.search` | src/pycode_kg/index.py |
| 2 | 0.7323 | method | `KGModule.query` | src/pycode_kg/module/base.py |
| 3 | 0.7203 | function | `query_codebase` | src/pycode_kg/mcp_server.py |
| 4 | 0.7094 | function | `query` | src/pycode_kg/cli/cmd_query.py |
| 5 | 0.7079 | function | `query_ranked` | src/pycode_kg/mcp_server.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `LayerCakeLayout.compute` | src/pycode_kg/layout3d.py |
| 2 | 0.7486 | method | `AlliumLayout.compute` | src/pycode_kg/layout3d.py |
| 3 | 0.7427 | method | `Layout3D.compute` | src/pycode_kg/layout3d.py |
| 4 | 0.7209 | method | `GraphStore.edges_from` | src/pycode_kg/store.py |
| 5 | 0.7092 | method | `GraphStore.callers_of` | src/pycode_kg/store.py |



---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 3.7s*
