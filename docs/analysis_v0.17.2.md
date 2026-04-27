> **Analysis Report Metadata**  
> - **Generated:** 2026-04-27T22:58:43Z  
> - **Version:** pycode-kg 0.17.2  
> - **Commit:** e9a9e27 (main)  
> - **Platform:** macOS 26.4.1 | arm64 (arm) | Turing | Python 3.12.13  
> - **Graph:** 7240 nodes · 7196 edges (479 meaningful)  
> - **Included directories:** src  
> - **Excluded directories:** none  
> - **Elapsed time:** 4s  

# pycode_kg Analysis

**Generated:** 2026-04-27 22:58:43 UTC

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
| **Total Nodes** | 7240 |
| **Total Edges** | 7196 |
| **Modules** | 56 (of 56 total) |
| **Functions** | 163 |
| **Classes** | 46 |
| **Methods** | 214 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 2550 |
| CONTAINS | 423 |
| IMPORTS | 430 |
| ATTR_ACCESS | 2332 |
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
| 11 | `_rewrap()` | src/pycode_kg/snapshots.py | **5** |
| 12 | `_add_edge()` | src/pycode_kg/visitor.py | **5** |
| 13 | `_get_node_id()` | src/pycode_kg/visitor.py | **5** |
| 14 | `_add_var_edge()` | src/pycode_kg/visitor.py | **5** |
| 15 | `clear()` | src/pycode_kg/store.py | **5** |


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
| `src/pycode_kg/pycodekg_thorough_analysis.py` | 5 | 4 | 4 | 1 | 0.17 |
| `src/pycode_kg/store.py` | 3 | 2 | 10 | 2 | 0.15 |
| `src/pycode_kg/mcp_server.py` | 25 | 0 | 0 | 3 | 0.75 |
| `src/pycode_kg/module/types.py` | 11 | 4 | 4 | 0 | 0.00 |
| `src/pycode_kg/index.py` | 7 | 4 | 6 | 0 | 0.00 |
| `src/pycode_kg/module/base.py` | 3 | 1 | 3 | 4 | 0.50 |
| `src/pycode_kg/snapshots.py` | 5 | 4 | 6 | 0 | 0.00 |
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
| `PyCodeKG()` | src/pycode_kg/kg.py | 9 | class |
| `GraphStore()` | src/pycode_kg/store.py | 9 | class |
| `compute_coderank()` | src/pycode_kg/ranking/coderank.py | 7 | function |
| `StructuralImportanceRanker()` | src/pycode_kg/analysis/centrality.py | 6 | class |
| `build()` | src/pycode_kg/cli/cmd_build_full.py | 4 | function |
| `norm()` | src/pycode_kg/analysis/framework_detector.py | 4 | function |
| `norm()` | src/pycode_kg/analysis/hybrid_rank.py | 4 | function |
| `CodeGraph()` | src/pycode_kg/graph.py | 4 | class |
| `SentenceTransformerEmbedder()` | src/pycode_kg/index.py | 4 | class |
---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 144 | 163 | [OK] 88.3% |
| `method` | 202 | 214 | [OK] 94.4% |
| `class` | 44 | 46 | [OK] 95.7% |
| `module` | 51 | 56 | [OK] 91.1% |
| **total** | **441** | **479** | **[OK] 92.1%** |

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `pycodekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.139507 | 27 | `src/pycode_kg/store.py` |
| 2 | 0.087838 | 48 | `src/pycode_kg/viz3d.py` |
| 3 | 0.087307 | 25 | `src/pycode_kg/module/base.py` |
| 4 | 0.070752 | 25 | `src/pycode_kg/snapshots.py` |
| 5 | 0.053296 | 25 | `src/pycode_kg/index.py` |
| 6 | 0.045167 | 26 | `src/pycode_kg/module/types.py` |
| 7 | 0.043079 | 37 | `src/pycode_kg/pycodekg_thorough_analysis.py` |
| 8 | 0.035422 | 14 | `src/pycode_kg/analysis/centrality.py` |
| 9 | 0.033734 | 26 | `src/pycode_kg/mcp_server.py` |
| 10 | 0.033409 | 8 | `src/pycode_kg/pycodekg.py` |
| 11 | 0.032240 | 9 | `src/pycode_kg/graph.py` |
| 12 | 0.031677 | 20 | `src/pycode_kg/visitor.py` |
| 13 | 0.031350 | 17 | `src/pycode_kg/layout3d.py` |
| 14 | 0.029262 | 16 | `src/pycode_kg/module/extractor.py` |
| 15 | 0.024850 | 8 | `src/pycode_kg/cli/cmd_build_full.py` |



---

## Code Quality Issues

- [WARN] 1 functions with high fan-out -- potential orchestrators or god objects
- [WARN] `viz3d.py` has 47 functions/methods/classes -- consider splitting into focused submodules
- [WARN] `pycodekg_thorough_analysis.py` has 36 functions/methods/classes -- consider splitting into focused submodules

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No obvious dead code detected
- Good docstring coverage: 92.1% of functions/methods/classes/modules documented

---

## Recommendations

### Immediate Actions
1. **Refactor high fan-out orchestrators** — `init` calls 43 functions; consider splitting into smaller, focused coordinators

### Medium-term Refactoring
1. **Harden high fan-in functions** — `_get_kg`, `close`, `close` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `SnapshotManager`, `PyCodeKG`, `GraphStore`
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
| 1 | 2026-04-27 22:57:18 | main | 0.17.1 | 7240 | 7196 | 92.1% | +0 | +0 | +0.0% |
| 2 | 2026-04-27 16:09:14 | main | 0.17.1 | 7240 | 7196 | 92.1% | +0 | +0 | +0.0% |
| 3 | 2026-04-27 15:45:37 | main | 0.17.1 | 7240 | 7196 | 92.1% | +0 | +0 | +0.0% |
| 4 | 2026-04-27 15:40:12 | main | 0.17.1 | 7240 | 7196 | 92.1% | +0 | +0 | +0.0% |
| 5 | 2026-04-27 14:15:11 | main | 0.16.1 | 7240 | 7196 | 92.1% | -37 | -39 | -0.4% |
| 6 | 2026-04-26 22:43:24 | main | 0.16.1 | 7277 | 7235 | 92.5% | +0 | +0 | +0.0% |
| 7 | 2026-04-26 17:22:03 | main | 0.16.1 | 7277 | 7235 | 92.5% | -6 | -1 | +0.0% |
| 8 | 2026-04-25 21:13:23 | main | 0.15.2 | 7283 | 7236 | 92.5% | +0 | +0 | +0.0% |
| 9 | 2026-04-25 21:10:54 | main | 0.15.2 | 7283 | 7236 | 92.5% | +0 | +0 | +0.0% |
| 10 | 2026-04-25 21:10:08 | main | 0.15.2 | 7283 | 7236 | 92.5% | +0 | +0 | +0.0% |


---

## Appendix: Orphaned Code

Functions with zero callers (potential dead code):

No orphaned functions detected.
---

## CodeRank -- Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000574 | method | `GraphStore.con` | src/pycode_kg/store.py |
| 2 | 0.000537 | method | `KGModule.store` | src/pycode_kg/module/base.py |
| 3 | 0.000497 | method | `CodeGraph.extract` | src/pycode_kg/graph.py |
| 4 | 0.000484 | function | `_get_kg` | src/pycode_kg/mcp_server.py |
| 5 | 0.000410 | function | `_rewrap` | src/pycode_kg/snapshots.py |
| 6 | 0.000355 | function | `_load_dir_list` | src/pycode_kg/config.py |
| 7 | 0.000310 | method | `PyCodeKGVisitor._get_node_id` | src/pycode_kg/visitor.py |
| 8 | 0.000310 | method | `PyCodeKGVisitor._add_edge` | src/pycode_kg/visitor.py |
| 9 | 0.000305 | function | `expr_to_name` | src/pycode_kg/pycodekg.py |
| 10 | 0.000301 | method | `SnippetPack.to_dict` | src/pycode_kg/module/types.py |
| 11 | 0.000280 | function | `_run_pipeline` | src/pycode_kg/cli/cmd_build_full.py |
| 12 | 0.000274 | function | `_format_table` | src/pycode_kg/cli/cmd_centrality.py |
| 13 | 0.000252 | method | `PyCodeKGVisitor._add_var_edge` | src/pycode_kg/visitor.py |
| 14 | 0.000249 | function | `_load_store` | src/pycode_kg/app.py |
| 15 | 0.000243 | method | `GraphStore.close` | src/pycode_kg/store.py |
| 16 | 0.000243 | method | `SentenceTransformerEmbedder.embed_texts` | src/pycode_kg/index.py |
| 17 | 0.000243 | method | `PyCodeKGExtractor.node_kinds` | src/pycode_kg/module/extractor.py |
| 18 | 0.000243 | method | `KGModule.close` | src/pycode_kg/module/base.py |
| 19 | 0.000240 | function | `load_snapshots_timeline` | src/pycode_kg/viz3d_timeline.py |
| 20 | 0.000224 | method | `PyCodeKGVisitor._extract_reads` | src/pycode_kg/visitor.py |

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
| 1 | 0.8286 | method | `KGModule.store` | src/pycode_kg/module/base.py |
| 2 | 0.7666 | function | `_load_store` | src/pycode_kg/app.py |
| 3 | 0.7297 | method | `SemanticIndex.build` | src/pycode_kg/index.py |
| 4 | 0.7164 | function | `_get_store` | src/pycode_kg/app.py |
| 5 | 0.7142 | method | `ArchitectureAnalyzer.__init__` | src/pycode_kg/architecture.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `SemanticIndex.search` | src/pycode_kg/index.py |
| 2 | 0.7331 | method | `KGModule.query` | src/pycode_kg/module/base.py |
| 3 | 0.7296 | function | `query_codebase` | src/pycode_kg/mcp_server.py |
| 4 | 0.709 | function | `query_ranked` | src/pycode_kg/mcp_server.py |
| 5 | 0.7068 | method | `SentenceTransformerEmbedder.embed_query` | src/pycode_kg/index.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `LayerCakeLayout.compute` | src/pycode_kg/layout3d.py |
| 2 | 0.747 | method | `AlliumLayout.compute` | src/pycode_kg/layout3d.py |
| 3 | 0.7461 | method | `Layout3D.compute` | src/pycode_kg/layout3d.py |
| 4 | 0.7456 | method | `PyCodeKGVisitor._add_edge` | src/pycode_kg/visitor.py |
| 5 | 0.7206 | method | `GraphStore.edges_from` | src/pycode_kg/store.py |



---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 4.2s*
