> **Analysis Report Metadata**  
> - **Generated:** 2026-03-14T21:56:50Z  
> - **Version:** code-kg 0.8.1  
> - **Commit:** f4fc790 (develop)  
> - **Platform:** Darwin arm64 | Python 3.12.13  
> - **Graph:** 6782 nodes · 6565 edges (424 meaningful)  
> - **Included directories:** src  
> - **Excluded directories:** none  
> - **Elapsed time:** 6s  

# code_kg Analysis

**Generated:** 2026-03-14 21:56:50 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **code_kg** repository using CodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
|----------------|-------|-------|
| [A] **Excellent** | **A** | 92 / 100 |

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| **Total Nodes** | 6782 |
| **Total Edges** | 6565 |
| **Modules** | 51 (of 51 total) |
| **Functions** | 146 |
| **Classes** | 42 |
| **Methods** | 185 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 2420 |
| CONTAINS | 373 |
| IMPORTS | 345 |
| ATTR_ACCESS | 2188 |
| INHERITS | 8 |

---

## Fan-In Ranking

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers |
|---|----------|--------|---------|
| 1 | `_get_kg()` | src/code_kg/mcp_server.py | **15** |
| 2 | `close()` | src/code_kg/kg.py | **15** |
| 3 | `close()` | src/code_kg/store.py | **15** |
| 4 | `node()` | src/code_kg/store.py | **13** |
| 5 | `con()` | src/code_kg/store.py | **12** |
| 6 | `store()` | src/code_kg/kg.py | **8** |
| 7 | `compute_coderank()` | src/code_kg/ranking/coderank.py | **7** |
| 8 | `to_json()` | src/code_kg/kg.py | **6** |
| 9 | `extract()` | src/code_kg/graph.py | **5** |
| 10 | `_add_edge()` | src/code_kg/visitor.py | **5** |
| 11 | `_get_node_id()` | src/code_kg/visitor.py | **5** |
| 12 | `to_dict()` | src/code_kg/kg.py | **5** |
| 13 | `load_manifest()` | src/code_kg/snapshots.py | **5** |
| 14 | `_add_var_edge()` | src/code_kg/visitor.py | **5** |
| 15 | `load_snapshot()` | src/code_kg/snapshots.py | **5** |


**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:
- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.

| # | Function | Module | Calls | Type |
|---|----------|--------|-------|------|
| 1 | `__init__()` | src/code_kg/viz3d.py | **95** | Orchestrator |

---

## Module Architecture

Top modules by dependency coupling and cohesion (showing up to 10 with activity).
Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.

| Module | Functions | Classes | Incoming | Outgoing | Cohesion |
|--------|-----------|---------|----------|----------|----------|
| `src/code_kg/kg.py` | 12 | 5 | 5 | 3 | 0.33 |
| `src/code_kg/viz3d.py` | 9 | 3 | 0 | 0 | 0.00 |
| `src/code_kg/codekg_thorough_analysis.py` | 5 | 4 | 3 | 1 | 0.20 |
| `src/code_kg/store.py` | 3 | 2 | 8 | 2 | 0.18 |
| `src/code_kg/snapshots.py` | 0 | 5 | 5 | 0 | 0.00 |
| `src/code_kg/mcp_server.py` | 23 | 0 | 0 | 3 | 0.75 |
| `src/code_kg/index.py` | 5 | 4 | 5 | 0 | 0.00 |
| `src/code_kg/visitor.py` | 1 | 1 | 1 | 1 | 0.33 |
| `src/code_kg/architecture.py` | 0 | 4 | 1 | 1 | 0.33 |
| `src/code_kg/layout3d.py` | 3 | 5 | 0 | 0 | 0.00 |

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
| `GraphStore()` | src/code_kg/store.py | 8 | class |
| `CodeKG()` | src/code_kg/kg.py | 8 | class |
| `SnapshotManager()` | src/code_kg/snapshots.py | 7 | class |
| `compute_coderank()` | src/code_kg/ranking/coderank.py | 7 | function |
| `StructuralImportanceRanker()` | src/code_kg/analysis/centrality.py | 6 | class |
| `SentenceTransformerEmbedder()` | src/code_kg/index.py | 4 | class |
| `build()` | src/code_kg/cli/cmd_build_full.py | 4 | function |
| `norm()` | src/code_kg/analysis/framework_detector.py | 4 | function |
| `norm()` | src/code_kg/analysis/hybrid_rank.py | 4 | function |
| `CodeGraph()` | src/code_kg/graph.py | 3 | class |
---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 127 | 146 | [OK] 87.0% |
| `method` | 180 | 185 | [OK] 97.3% |
| `class` | 40 | 42 | [OK] 95.2% |
| `module` | 46 | 51 | [OK] 90.2% |
| **total** | **393** | **424** | **[OK] 92.7%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `codekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.148983 | 27 | `src/code_kg/store.py` |
| 2 | 0.139522 | 45 | `src/code_kg/kg.py` |
| 3 | 0.097182 | 25 | `src/code_kg/snapshots.py` |
| 4 | 0.087913 | 40 | `src/code_kg/viz3d.py` |
| 5 | 0.049885 | 23 | `src/code_kg/index.py` |
| 6 | 0.045848 | 36 | `src/code_kg/codekg_thorough_analysis.py` |
| 7 | 0.038141 | 14 | `src/code_kg/analysis/centrality.py` |
| 8 | 0.035107 | 20 | `src/code_kg/visitor.py` |
| 9 | 0.034130 | 17 | `src/code_kg/layout3d.py` |
| 10 | 0.033914 | 24 | `src/code_kg/mcp_server.py` |
| 11 | 0.033093 | 8 | `src/code_kg/codekg.py` |
| 12 | 0.031544 | 9 | `src/code_kg/graph.py` |
| 13 | 0.027549 | 18 | `src/code_kg/architecture.py` |
| 14 | 0.026593 | 3 | `src/code_kg/ranking/cli_rank.py` |
| 15 | 0.024667 | 14 | `src/code_kg/ranking/coderank.py` |



---

## Code Quality Issues

- [WARN] 1 functions with high fan-out -- potential orchestrators or god objects

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No obvious dead code detected
- Good docstring coverage: 92.7% of functions/methods/classes/modules documented

---

## Recommendations

### Immediate Actions
1. **Refactor high fan-out orchestrators** — `__init__` calls 95 functions; consider splitting into smaller, focused coordinators

### Medium-term Refactoring
1. **Harden high fan-in functions** — `_get_kg`, `close`, `close` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `GraphStore`, `CodeKG`, `SnapshotManager`
2. **Enforce layer boundaries** — add linting or CI checks to prevent unexpected cross-module dependencies as the codebase grows
3. **Monitor hot paths** — instrument the high fan-in functions identified here to catch performance regressions early

---

## Inheritance Hierarchy

**8** INHERITS edges across **9** classes. Max depth: **1**.

| Class | Module | Depth | Parents | Children |
|-------|--------|-------|---------|----------|
| `SentenceTransformerEmbedder` | src/code_kg/index.py | 1 | 1 | 0 |
| `AlliumLayout` | src/code_kg/layout3d.py | 1 | 1 | 0 |
| `LayerCakeLayout` | src/code_kg/layout3d.py | 1 | 1 | 0 |
| `Embedder` | src/code_kg/index.py | 0 | 0 | 1 |
| `Layout3D` | src/code_kg/layout3d.py | 0 | 1 | 2 |
| `CodeKGVisitor` | src/code_kg/visitor.py | 0 | 1 | 0 |
| `DocstringPopup` | src/code_kg/viz3d.py | 0 | 1 | 0 |
| `KGVisualizer` | src/code_kg/viz3d.py | 0 | 1 | 0 |
| `MainWindow` | src/code_kg/viz3d.py | 0 | 1 | 0 |


---

## Snapshot History

Recent snapshots in reverse chronological order. Δ columns show change vs. the immediately preceding snapshot.

| # | Timestamp | Branch | Version | Nodes | Edges | Coverage | Δ Nodes | Δ Edges | Δ Coverage |
|---|-----------|--------|---------|-------|-------|----------|---------|---------|------------|
| 1 | 2026-03-14 21:46:51 | develop | 0.8.1 | 6782 | 6565 | 92.7% | +0 | +0 | +0.0% |
| 2 | 2026-03-14 21:15:43 | refactor/cleanup-output | 0.8.1 | 6782 | 6565 | 92.7% | +0 | +0 | +0.0% |
| 3 | 2026-03-14 18:14:58 | main | 0.8.1 | 6782 | 6565 | 92.7% | +0 | +0 | +0.0% |
| 4 | 2026-03-14 18:04:40 | main | 0.8.1 | 6782 | 6565 | 92.7% | +0 | +0 | +0.0% |
| 5 | 2026-03-14 17:54:01 | main | 0.8.1 | 6782 | 6565 | 92.7% | +41 | +30 | +0.0% |
| 6 | 2026-03-13 17:45:53 | main | 0.8.1 | 6741 | 6535 | 92.7% | +0 | +0 | +0.0% |
| 7 | 2026-03-13 04:14:50 | main | 0.8.0 | 6741 | 6535 | 92.7% | +0 | +0 | +0.0% |
| 8 | 2026-03-13 02:01:20 | main | 0.8.0 | 6741 | 6535 | 92.7% | +0 | +0 | +0.0% |
| 9 | 2026-03-13 01:47:59 | main | 0.8.0 | 6741 | 6535 | 92.7% | +70 | +56 | -0.1% |
| 10 | 2026-03-12 18:39:17 | main | 0.8.0 | 6671 | 6479 | 92.8% | +0 | +0 | +0.0% |


---

## Appendix: Orphaned Code

Functions with zero callers (potential dead code):

No orphaned functions detected.
---

## CodeRank -- Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000635 | method | `GraphStore.con` | src/code_kg/store.py |
| 2 | 0.000578 | method | `CodeKG.store` | src/code_kg/kg.py |
| 3 | 0.000532 | method | `CodeGraph.extract` | src/code_kg/graph.py |
| 4 | 0.000473 | function | `_get_kg` | src/code_kg/mcp_server.py |
| 5 | 0.000380 | function | `_load_dir_list` | src/code_kg/config.py |
| 6 | 0.000345 | class | `SnapshotDelta` | src/code_kg/snapshots.py |
| 7 | 0.000332 | method | `CodeKGVisitor._get_node_id` | src/code_kg/visitor.py |
| 8 | 0.000332 | method | `CodeKGVisitor._add_edge` | src/code_kg/visitor.py |
| 9 | 0.000326 | function | `expr_to_name` | src/code_kg/codekg.py |
| 10 | 0.000322 | method | `SnippetPack.to_dict` | src/code_kg/kg.py |
| 11 | 0.000311 | class | `SnapshotManifest` | src/code_kg/snapshots.py |
| 12 | 0.000293 | function | `_format_table` | src/code_kg/cli/cmd_centrality.py |
| 13 | 0.000291 | method | `SnapshotManager.load_manifest` | src/code_kg/snapshots.py |
| 14 | 0.000270 | method | `CodeKGVisitor._add_var_edge` | src/code_kg/visitor.py |
| 15 | 0.000266 | function | `_load_store` | src/code_kg/app.py |
| 16 | 0.000260 | method | `GraphStore.close` | src/code_kg/store.py |
| 17 | 0.000260 | method | `SentenceTransformerEmbedder.embed_texts` | src/code_kg/index.py |
| 18 | 0.000260 | method | `CodeKG.close` | src/code_kg/kg.py |
| 19 | 0.000257 | function | `load_snapshots_timeline` | src/code_kg/viz3d_timeline.py |
| 20 | 0.000249 | method | `CodeKG.embedder` | src/code_kg/kg.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7535 | function | `_init_state` | src/code_kg/app.py |
| 2 | 0.7482 | function | `_load_kg` | src/code_kg/app.py |
| 3 | 0.7396 | function | `main` | src/code_kg/mcp_server.py |
| 4 | 0.7301 | method | `MainWindow.__init__` | src/code_kg/viz3d.py |
| 5 | 0.7257 | function | `load_include_dirs` | src/code_kg/config.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.8344 | method | `CodeKG.store` | src/code_kg/kg.py |
| 2 | 0.7601 | function | `_load_store` | src/code_kg/app.py |
| 3 | 0.7191 | method | `SemanticIndex.build` | src/code_kg/index.py |
| 4 | 0.7103 | function | `_get_store` | src/code_kg/app.py |
| 5 | 0.7075 | method | `GraphStore.__init__` | src/code_kg/store.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `CodeKG.query` | src/code_kg/kg.py |
| 2 | 0.7444 | method | `SemanticIndex.search` | src/code_kg/index.py |
| 3 | 0.7147 | function | `query_codebase` | src/code_kg/mcp_server.py |
| 4 | 0.7039 | function | `query` | src/code_kg/cli/cmd_query.py |
| 5 | 0.7024 | function | `query_ranked` | src/code_kg/mcp_server.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `LayerCakeLayout.compute` | src/code_kg/layout3d.py |
| 2 | 0.7486 | method | `AlliumLayout.compute` | src/code_kg/layout3d.py |
| 3 | 0.7427 | method | `Layout3D.compute` | src/code_kg/layout3d.py |
| 4 | 0.7209 | method | `GraphStore.edges_from` | src/code_kg/store.py |
| 5 | 0.7092 | method | `GraphStore.callers_of` | src/code_kg/store.py |



---

*Report generated by CodeKG Thorough Analysis Tool — analysis completed in 6.9s*
