> **Analysis Report Metadata**
> - **Generated:** 2026-03-20T00:57:20Z
> - **Version:** pycode-kg 0.9.2
> - **Commit:** 91dc6f3 (main)
> - **Platform:** macOS 26.3.1 | arm64 (arm) | Turing | Python 3.12.13
> - **Graph:** 7046 nodes · 6994 edges (464 meaningful)
> - **Included directories:** src
> - **Excluded directories:** none
> - **Elapsed time:** 3s

# pycode_kg Analysis

**Generated:** 2026-03-20 00:57:20 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **pycode_kg** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
|----------------|-------|-------|
| [A] **Excellent** | **A** | 100 / 100 |

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| **Total Nodes** | 7046 |
| **Total Edges** | 6994 |
| **Modules** | 55 (of 55 total) |
| **Functions** | 150 |
| **Classes** | 46 |
| **Methods** | 213 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 2470 |
| CONTAINS | 409 |
| IMPORTS | 412 |
| ATTR_ACCESS | 2282 |
| INHERITS | 14 |

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
| 13 | `metrics_to_dict()` | src/pycode_kg/snapshots.py | **5** |
| 14 | `_add_var_edge()` | src/pycode_kg/visitor.py | **5** |
| 15 | `metrics()` | src/pycode_kg/snapshots.py | **5** |


**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:
- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.

No extreme high fan-out functions detected. Well-balanced architecture.

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
| `src/pycode_kg/mcp_server.py` | 23 | 0 | 0 | 3 | 0.75 |
| `src/pycode_kg/index.py` | 5 | 4 | 5 | 0 | 0.00 |
| `src/pycode_kg/snapshots.py` | 4 | 4 | 5 | 0 | 0.00 |
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
| `metrics_to_dict()` | src/pycode_kg/snapshots.py | 5 | function |
| `build()` | src/pycode_kg/cli/cmd_build_full.py | 4 | function |
| `norm()` | src/pycode_kg/analysis/framework_detector.py | 4 | function |
| `norm()` | src/pycode_kg/analysis/hybrid_rank.py | 4 | function |
| `SentenceTransformerEmbedder()` | src/pycode_kg/index.py | 4 | class |
---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 130 | 150 | [OK] 86.7% |
| `method` | 203 | 213 | [OK] 95.3% |
| `class` | 44 | 46 | [OK] 95.7% |
| `module` | 50 | 55 | [OK] 90.9% |
| **total** | **427** | **464** | **[OK] 92.0%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.140455 | 27 | `src/pycode_kg/store.py` |
| 2 | 0.093592 | 48 | `src/pycode_kg/viz3d.py` |
| 3 | 0.090273 | 25 | `src/pycode_kg/module/base.py` |
| 4 | 0.073805 | 23 | `src/pycode_kg/snapshots.py` |
| 5 | 0.048829 | 26 | `src/pycode_kg/module/types.py` |
| 6 | 0.045497 | 23 | `src/pycode_kg/index.py` |
| 7 | 0.045203 | 37 | `src/pycode_kg/pycodekg_thorough_analysis.py` |
| 8 | 0.037776 | 14 | `src/pycode_kg/analysis/centrality.py` |
| 9 | 0.033704 | 8 | `src/pycode_kg/pycodekg.py` |
| 10 | 0.033389 | 20 | `src/pycode_kg/visitor.py` |
| 11 | 0.032607 | 17 | `src/pycode_kg/layout3d.py` |
| 12 | 0.032119 | 24 | `src/pycode_kg/mcp_server.py` |
| 13 | 0.030741 | 9 | `src/pycode_kg/graph.py` |
| 14 | 0.030211 | 16 | `src/pycode_kg/module/extractor.py` |
| 15 | 0.026238 | 18 | `src/pycode_kg/architecture.py` |



---

## Code Quality Issues

- No major issues detected

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No obvious dead code detected
- No god objects or god functions detected
- Good docstring coverage: 92.0% of functions/methods/classes/modules documented

---

## Recommendations

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

**14** INHERITS edges across **15** classes. Max depth: **1**.

| Class | Module | Depth | Parents | Children |
|-------|--------|-------|---------|----------|
| `SentenceTransformerEmbedder` | src/pycode_kg/index.py | 1 | 1 | 0 |
| `PyCodeKG` | src/pycode_kg/kg.py | 1 | 1 | 0 |
| `AlliumLayout` | src/pycode_kg/layout3d.py | 1 | 1 | 0 |
| `LayerCakeLayout` | src/pycode_kg/layout3d.py | 1 | 1 | 0 |
| `PyCodeKGExtractor` | src/pycode_kg/module/extractor.py | 1 | 1 | 0 |
| `Snapshot` | src/pycode_kg/snapshots.py | 1 | 1 | 1 |
| `Embedder` | src/pycode_kg/index.py | 0 | 0 | 1 |
| `Layout3D` | src/pycode_kg/layout3d.py | 0 | 1 | 2 |
| `KGModule` | src/pycode_kg/module/base.py | 0 | 1 | 1 |
| `KGExtractor` | src/pycode_kg/module/extractor.py | 0 | 1 | 1 |
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
| 1 | 2026-03-20 00:46:31 | main | 0.9.3 | 7046 | 6994 | 92.0% | +0 | +0 | +0.0% |
| 2 | 2026-03-20 00:46:03 | main | 0.9.3 | 7046 | 6994 | 92.0% | +79 | +94 | +0.1% |
| 3 | 2026-03-19 23:42:17 | main | 0.9.3 | 6967 | 6900 | 91.9% | +0 | +0 | +0.0% |
| 4 | 2026-03-19 22:40:46 | main | 0.9.3 | 6967 | 6900 | 91.9% | -24 | -52 | -1.1% |
| 5 | 2026-03-19 04:24:06 | main | 0.9.2 | 6991 | 6952 | 93.0% | +0 | +0 | +0.0% |
| 6 | 2026-03-19 03:45:10 | main | 0.9.2 | 6991 | 6952 | 93.0% | +0 | +0 | +0.0% |
| 7 | 2026-03-19 03:03:16 | fix/snapshots | 0.9.2 | 6991 | 6952 | 93.0% | +16 | +15 | +0.0% |
| 8 | 2026-03-19 02:28:28 | fix/snapshots | 0.9.2 | 6975 | 6937 | 93.0% | +0 | +0 | +0.0% |
| 9 | 2026-03-19 01:26:59 | fix/snapshots | 0.9.2 | 6975 | 6937 | 93.0% | -13 | -14 | +0.0% |
| 10 | 2026-03-19 01:15:26 | fix/snapshots | 0.9.1 | 6988 | 6951 | 93.0% | +47 | +29 | +0.0% |


---

## Appendix: Orphaned Code

Functions with zero callers (potential dead code):

No orphaned functions detected.
---

## CodeRank -- Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000610 | method | `GraphStore.con` | src/pycode_kg/store.py |
| 2 | 0.000553 | method | `KGModule.store` | src/pycode_kg/module/base.py |
| 3 | 0.000511 | method | `CodeGraph.extract` | src/pycode_kg/graph.py |
| 4 | 0.000454 | function | `_get_kg` | src/pycode_kg/mcp_server.py |
| 5 | 0.000365 | function | `_load_dir_list` | src/pycode_kg/config.py |
| 6 | 0.000319 | method | `PyCodeKGVisitor._get_node_id` | src/pycode_kg/visitor.py |
| 7 | 0.000319 | method | `PyCodeKGVisitor._add_edge` | src/pycode_kg/visitor.py |
| 8 | 0.000313 | function | `expr_to_name` | src/pycode_kg/pycodekg.py |
| 9 | 0.000310 | method | `SnippetPack.to_dict` | src/pycode_kg/module/types.py |
| 10 | 0.000282 | function | `_format_table` | src/pycode_kg/cli/cmd_centrality.py |
| 11 | 0.000276 | function | `metrics_to_dict` | src/pycode_kg/snapshots.py |
| 12 | 0.000263 | function | `delta_to_dict` | src/pycode_kg/snapshots.py |
| 13 | 0.000260 | class | `SnapshotDelta` | src/pycode_kg/snapshots.py |
| 14 | 0.000259 | method | `PyCodeKGVisitor._add_var_edge` | src/pycode_kg/visitor.py |
| 15 | 0.000256 | function | `_load_store` | src/pycode_kg/app.py |
| 16 | 0.000250 | method | `GraphStore.close` | src/pycode_kg/store.py |
| 17 | 0.000250 | method | `SentenceTransformerEmbedder.embed_texts` | src/pycode_kg/index.py |
| 18 | 0.000250 | method | `PyCodeKGExtractor.node_kinds` | src/pycode_kg/module/extractor.py |
| 19 | 0.000250 | method | `KGModule.close` | src/pycode_kg/module/base.py |
| 20 | 0.000247 | function | `load_snapshots_timeline` | src/pycode_kg/viz3d_timeline.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7534 | function | `_init_state` | src/pycode_kg/app.py |
| 2 | 0.7481 | function | `_load_kg` | src/pycode_kg/app.py |
| 3 | 0.7414 | function | `main` | src/pycode_kg/mcp_server.py |
| 4 | 0.7405 | method | `PyCodeKGExtractor.__init__` | src/pycode_kg/module/extractor.py |
| 5 | 0.7305 | method | `KGExtractor.__init__` | src/pycode_kg/module/extractor.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.8273 | method | `KGModule.store` | src/pycode_kg/module/base.py |
| 2 | 0.7596 | function | `_load_store` | src/pycode_kg/app.py |
| 3 | 0.7197 | method | `SemanticIndex.build` | src/pycode_kg/index.py |
| 4 | 0.7105 | function | `_get_store` | src/pycode_kg/app.py |
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

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 3.0s*
