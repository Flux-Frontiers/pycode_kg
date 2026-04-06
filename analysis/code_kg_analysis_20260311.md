> **Analysis Report Metadata**  
> - **Generated:** 2026-03-11T22:52:55Z  
> - **Version:** code-kg 0.7.1  
> - **Commit:** d8ee9eb (feature/bridge_centrality)  
> - **Platform:** Darwin arm64 | Python 3.12.10  
> - **Graph:** 6540 nodes · 6352 edges (414 meaningful)  
> - **Included directories:** src  

# code_kg Analysis

**Generated:** 2026-03-11 22:52:55 UTC

---

## 📊 Executive Summary

This report provides a comprehensive architectural analysis of the **code_kg** repository using CodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
|----------------|-------|-------|
| 🟢 **Excellent** | **A** | 92 / 100 |

---

## 📈 Baseline Metrics

| Metric | Value |
|--------|-------|
| **Total Nodes** | 6540 |
| **Total Edges** | 6352 |
| **Modules** | 50 (of 50 total) |
| **Functions** | 141 |
| **Classes** | 42 |
| **Methods** | 181 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 2324 |
| CONTAINS | 364 |
| IMPORTS | 338 |
| ATTR_ACCESS | 2118 |
| INHERITS | 8 |

---

## 🔥 Fan-In Ranking

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers |
|---|----------|--------|---------|
| 1 | `_get_kg()` | src/code_kg/mcp_server.py | **15** |
| 2 | `close()` | src/code_kg/kg.py | **15** |
| 3 | `close()` | src/code_kg/store.py | **15** |
| 4 | `node()` | src/code_kg/store.py | **13** |
| 5 | `con()` | src/code_kg/store.py | **12** |
| 6 | `store()` | src/code_kg/kg.py | **8** |
| 7 | `to_json()` | src/code_kg/kg.py | **6** |
| 8 | `extract()` | src/code_kg/graph.py | **5** |
| 9 | `_add_edge()` | src/code_kg/visitor.py | **5** |
| 10 | `_get_node_id()` | src/code_kg/visitor.py | **5** |
| 11 | `to_dict()` | src/code_kg/kg.py | **5** |
| 12 | `load_manifest()` | src/code_kg/snapshots.py | **5** |
| 13 | `_add_var_edge()` | src/code_kg/visitor.py | **5** |
| 14 | `load_snapshot()` | src/code_kg/snapshots.py | **5** |
| 15 | `compute_coderank()` | src/code_kg/ranking/coderank.py | **5** |


**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:
- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## 🔗 High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.

| # | Function | Module | Calls | Type |
|---|----------|--------|-------|------|
| 1 | `__init__()` | src/code_kg/viz3d.py | **95** | Orchestrator |

---

## 📦 Module Architecture

Top modules by dependency coupling and cohesion (showing up to 10 with activity).
Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.

| Module | Functions | Classes | Incoming | Outgoing | Cohesion |
|--------|-----------|---------|----------|----------|----------|
| `src/code_kg/kg.py` | 12 | 5 | 5 | 3 | 0.33 |
| `src/code_kg/viz3d.py` | 9 | 3 | 0 | 0 | 0.00 |
| `src/code_kg/codekg_thorough_analysis.py` | 5 | 4 | 3 | 1 | 0.20 |
| `src/code_kg/store.py` | 3 | 2 | 8 | 2 | 0.18 |
| `src/code_kg/mcp_server.py` | 23 | 0 | 0 | 3 | 0.75 |
| `src/code_kg/snapshots.py` | 0 | 5 | 5 | 0 | 0.00 |
| `src/code_kg/index.py` | 5 | 4 | 5 | 0 | 0.00 |
| `src/code_kg/visitor.py` | 1 | 1 | 1 | 1 | 0.33 |
| `src/code_kg/architecture.py` | 0 | 4 | 1 | 1 | 0.33 |
| `src/code_kg/layout3d.py` | 3 | 5 | 0 | 0 | 0.00 |

---

## 🔗 Key Call Chains

Deepest call chains in the codebase.

**Chain 1** (depth: 3)

```
__exit__ → close → close
```

---

## 🔓 Public API Surface

Identified public APIs (module-level functions with high usage).

| Function | Module | Fan-In | Type |
|----------|--------|--------|------|
| `CodeKG()` | src/code_kg/kg.py | 8 | class |
| `GraphStore()` | src/code_kg/store.py | 8 | class |
| `SnapshotManager()` | src/code_kg/snapshots.py | 7 | class |
| `StructuralImportanceRanker()` | src/code_kg/analysis/centrality.py | 5 | class |
| `compute_coderank()` | src/code_kg/ranking/coderank.py | 5 | function |
| `build()` | src/code_kg/cli/cmd_build_full.py | 4 | function |
| `SentenceTransformerEmbedder()` | src/code_kg/index.py | 4 | class |
| `pack()` | src/code_kg/cli/cmd_query.py | 3 | function |
| `norm()` | src/code_kg/analysis/framework_detector.py | 3 | function |
| `SnapshotDelta()` | src/code_kg/snapshots.py | 3 | class |
---

## 📝 Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 123 | 141 | 🟢 87.2% |
| `method` | 176 | 181 | 🟢 97.2% |
| `class` | 40 | 42 | 🟢 95.2% |
| `module` | 45 | 50 | 🟢 90.0% |
| **total** | **384** | **414** | **🟢 92.8%** |

---

## 🏆 Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `codekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.150591 | 27 | `src/code_kg/store.py` |
| 2 | 0.140968 | 45 | `src/code_kg/kg.py` |
| 3 | 0.099705 | 24 | `src/code_kg/snapshots.py` |
| 4 | 0.090184 | 40 | `src/code_kg/viz3d.py` |
| 5 | 0.051315 | 23 | `src/code_kg/index.py` |
| 6 | 0.044460 | 33 | `src/code_kg/codekg_thorough_analysis.py` |
| 7 | 0.038323 | 14 | `src/code_kg/analysis/centrality.py` |
| 8 | 0.035963 | 20 | `src/code_kg/visitor.py` |
| 9 | 0.034754 | 24 | `src/code_kg/mcp_server.py` |
| 10 | 0.034442 | 17 | `src/code_kg/layout3d.py` |
| 11 | 0.033991 | 8 | `src/code_kg/codekg.py` |
| 12 | 0.032544 | 9 | `src/code_kg/graph.py` |
| 13 | 0.028203 | 18 | `src/code_kg/architecture.py` |
| 14 | 0.027225 | 3 | `src/code_kg/ranking/cli_rank.py` |
| 15 | 0.023361 | 14 | `src/code_kg/ranking/coderank.py` |



---

## ⚠️  Code Quality Issues

- ⚠️  1 functions with high fan-out — potential orchestrators or god objects

---

## ✅ Architectural Strengths

- ✓ Well-structured with 15 core functions identified
- ✓ No obvious dead code detected
- ✓ Good docstring coverage: 92.8% of functions/methods/classes/modules documented

---

## 💡 Recommendations

### Immediate Actions
1. **Refactor high fan-out orchestrators** — `__init__` calls 95 functions; consider splitting into smaller, focused coordinators

### Medium-term Refactoring
1. **Harden high fan-in functions** — `_get_kg`, `close`, `close` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `CodeKG`, `GraphStore`, `SnapshotManager`
2. **Enforce layer boundaries** — add linting or CI checks to prevent unexpected cross-module dependencies as the codebase grows
3. **Monitor hot paths** — instrument the high fan-in functions identified here to catch performance regressions early

---

## 🧬 Inheritance Hierarchy

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

## 📸 Snapshot History

Recent snapshots in reverse chronological order. Δ columns show change vs. the immediately preceding snapshot.

| # | Timestamp | Branch | Version | Nodes | Edges | Coverage | Δ Nodes | Δ Edges | Δ Coverage |
|---|-----------|--------|---------|-------|-------|----------|---------|---------|------------|
| 1 | 2026-03-11 17:27:41 | develop | 0.8.0 | 5841 | 5684 | 94.4% | +338 | +312 | -2.8% |
| 2 | 2026-03-11 12:23:38 | develop | 0.8.0 | 5503 | 5372 | 97.2% | +6 | +3 | +0.0% |
| 3 | 2026-03-11 11:51:03 | develop | 0.8.0 | 5497 | 5369 | 97.2% | +48 | +30 | +0.0% |
| 4 | 2026-03-11 04:08:05 | develop | 0.8.0 | 5449 | 5339 | 97.2% | +11 | +14 | +0.0% |
| 5 | 2026-03-11 03:24:57 | develop | 0.8.0 | 5438 | 5325 | 97.2% | +25 | +19 | +0.1% |
| 6 | 2026-03-11 02:10:22 | develop | 0.8.0 | 5413 | 5306 | 97.1% | +0 | +0 | +0.0% |
| 7 | 2026-03-11 01:14:39 | develop | 0.8.0 | 5413 | 5306 | 97.1% | +112 | +84 | +0.3% |
| 8 | 2026-03-10 22:58:35 | develop | 0.7.1 | 5301 | 5222 | 96.8% | +0 | +0 | +0.0% |
| 9 | 2026-03-10 21:58:48 | develop | 0.7.1 | 5301 | 5222 | 96.8% | +0 | +0 | +0.0% |
| 10 | 2026-03-10 21:35:57 | develop | 0.7.1 | 5301 | 5222 | 96.8% | +0 | +0 | +0.0% |


---

## 📋 Appendix: Orphaned Code

Functions with zero callers (potential dead code):

✓ No orphaned functions detected.
---

## 📐 CodeRank — Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000659 | method | `GraphStore.con` | src/code_kg/store.py |
| 2 | 0.000600 | method | `CodeKG.store` | src/code_kg/kg.py |
| 3 | 0.000551 | method | `CodeGraph.extract` | src/code_kg/graph.py |
| 4 | 0.000505 | function | `_get_kg` | src/code_kg/mcp_server.py |
| 5 | 0.000362 | class | `SnapshotDelta` | src/code_kg/snapshots.py |
| 6 | 0.000344 | method | `CodeKGVisitor._get_node_id` | src/code_kg/visitor.py |
| 7 | 0.000344 | method | `CodeKGVisitor._add_edge` | src/code_kg/visitor.py |
| 8 | 0.000338 | function | `expr_to_name` | src/code_kg/codekg.py |
| 9 | 0.000334 | method | `SnippetPack.to_dict` | src/code_kg/kg.py |
| 10 | 0.000323 | class | `SnapshotManifest` | src/code_kg/snapshots.py |
| 11 | 0.000304 | function | `_format_table` | src/code_kg/cli/cmd_centrality.py |
| 12 | 0.000303 | method | `SnapshotManager.load_manifest` | src/code_kg/snapshots.py |
| 13 | 0.000280 | method | `CodeKGVisitor._add_var_edge` | src/code_kg/visitor.py |
| 14 | 0.000276 | function | `_load_store` | src/code_kg/app.py |
| 15 | 0.000270 | method | `GraphStore.close` | src/code_kg/store.py |
| 16 | 0.000270 | method | `SentenceTransformerEmbedder.embed_texts` | src/code_kg/index.py |
| 17 | 0.000270 | method | `CodeKG.close` | src/code_kg/kg.py |
| 18 | 0.000267 | function | `load_snapshots_timeline` | src/code_kg/viz3d_timeline.py |
| 19 | 0.000258 | method | `SnapshotManager.load_snapshot` | src/code_kg/snapshots.py |
| 20 | 0.000258 | method | `CodeKG.embedder` | src/code_kg/kg.py |

---

## 🔎 Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Error Handling Exception Recovery

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7681 | method | `CodeKGVisitor._extract_reads` | src/code_kg/visitor.py |
| 2 | 0.75 | method | `CodeKG.__exit__` | src/code_kg/kg.py |
| 3 | 0.7496 | method | `SnapshotManifest.from_dict` | src/code_kg/snapshots.py |
| 4 | 0.7389 | method | `Snapshot.from_dict` | src/code_kg/snapshots.py |
| 5 | 0.734 | method | `SemanticIndex._get_table` | src/code_kg/index.py |

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.7536 | function | `_init_state` | src/code_kg/app.py |
| 2 | 0.7482 | function | `_load_kg` | src/code_kg/app.py |
| 3 | 0.7402 | function | `main` | src/code_kg/mcp_server.py |
| 4 | 0.7301 | method | `MainWindow.__init__` | src/code_kg/viz3d.py |
| 5 | 0.7262 | function | `load_include_dirs` | src/code_kg/config.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.8349 | method | `CodeKG.store` | src/code_kg/kg.py |
| 2 | 0.7602 | function | `_load_store` | src/code_kg/app.py |
| 3 | 0.7196 | method | `SemanticIndex.build` | src/code_kg/index.py |
| 4 | 0.7103 | function | `_get_store` | src/code_kg/app.py |
| 5 | 0.7075 | method | `GraphStore.__init__` | src/code_kg/store.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `CodeKG.query` | src/code_kg/kg.py |
| 2 | 0.7438 | method | `SemanticIndex.search` | src/code_kg/index.py |
| 3 | 0.7143 | function | `query_codebase` | src/code_kg/mcp_server.py |
| 4 | 0.7039 | function | `query` | src/code_kg/cli/cmd_query.py |
| 5 | 0.7034 | function | `query_ranked` | src/code_kg/mcp_server.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `LayerCakeLayout.compute` | src/code_kg/layout3d.py |
| 2 | 0.7486 | method | `AlliumLayout.compute` | src/code_kg/layout3d.py |
| 3 | 0.7427 | method | `Layout3D.compute` | src/code_kg/layout3d.py |
| 4 | 0.7209 | method | `GraphStore.edges_from` | src/code_kg/store.py |
| 5 | 0.7083 | method | `GraphStore.edges_within` | src/code_kg/store.py |



---

*Report generated by CodeKG Thorough Analysis Tool — analysis completed in 4.6s*
