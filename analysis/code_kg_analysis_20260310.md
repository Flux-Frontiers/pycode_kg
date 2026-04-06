> **Analysis Report Metadata**
> - **Generated:** 2026-03-10T21:54:54Z
> - **Version:** pycode-kg 0.7.1
> - **Commit:** 4295d2b (develop)
> - **Platform:** Darwin arm64 | Python 3.12.10
> - **Graph:** 5301 nodes · 5222 edges (348 meaningful)
> - **Included directories:** src

# pycode_kg Analysis

**Generated:** 2026-03-10 21:54:54 UTC

---

## 📊 Executive Summary

This report provides a comprehensive architectural analysis of the **pycode_kg** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, critical call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
|----------------|-------|-------|
| 🟢 **Excellent** | **A** | 100 / 100 |

---

## 📈 Baseline Metrics

| Metric | Value |
|--------|-------|
| **Total Nodes** | 5301 |
| **Total Edges** | 5222 |
| **Modules** | 38 (of 38 total) |
| **Functions** | 102 |
| **Classes** | 36 |
| **Methods** | 172 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 1887 |
| CONTAINS | 310 |
| IMPORTS | 284 |
| ATTR_ACCESS | 1768 |
| INHERITS | 8 |

---

## 🔥 Complexity Hotspots (High Fan-In)

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers | Risk Level |
|---|----------|--------|---------|-----------|
| 1 | `FunctionMetrics()` | src/pycode_kg/pycodekg_thorough_analysis.py | **4** | 🟡 MEDIUM |
| 2 | `_qualname()` | src/pycode_kg/visitor.py | **3** | 🟡 MEDIUM |
| 3 | `node_id()` | src/pycode_kg/utils.py | **3** | 🟡 MEDIUM |
| 4 | `_seed_params()` | src/pycode_kg/visitor.py | **2** | 🟢 LOW |
| 5 | `expr_to_name()` | src/pycode_kg/pycodekg.py | **2** | 🟢 LOW |
| 6 | `_enclosing_def()` | src/pycode_kg/pycodekg.py | **1** | 🟢 LOW |
| 7 | `ModuleMetrics()` | src/pycode_kg/pycodekg_thorough_analysis.py | **1** | 🟢 LOW |
| 8 | `_compute_depth()` | src/pycode_kg/pycodekg_thorough_analysis.py | **1** | 🟢 LOW |
| 9 | `CallChain()` | src/pycode_kg/pycodekg_thorough_analysis.py | **1** | 🟢 LOW |
| 10 | `_compile_results()` | src/pycode_kg/pycodekg_thorough_analysis.py | **1** | 🟢 LOW |
| 11 | `ModuleLayer()` | src/pycode_kg/architecture.py | **1** | 🟢 LOW |
| 12 | `_summary()` | src/pycode_kg/cli/cmd_build_full.py | **1** | 🟢 LOW |
| 13 | `Node()` | src/pycode_kg/pycodekg.py | **1** | 🟢 LOW |
| 14 | `_resolve_dst()` | src/pycode_kg/pycodekg_thorough_analysis.py | **1** | 🟢 LOW |
| 15 | `_owner_id()` | src/pycode_kg/pycodekg.py | **1** | 🟢 LOW |


**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:
- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## 🔗 High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.

✓ No extreme high fan-out functions detected. Well-balanced architecture.

---

## 📦 Module Architecture

Top modules by dependency coupling and cohesion (showing up to 10 with activity).

| Module | Functions | Classes | Incoming | Outgoing | Cohesion |
|--------|-----------|---------|----------|----------|----------|
| `src/pycode_kg/kg.py` | 10 | 5 | 5 | 3 | 0.33 |
| `src/pycode_kg/viz3d.py` | 9 | 3 | 0 | 0 | 0.00 |
| `src/pycode_kg/pycodekg_thorough_analysis.py` | 5 | 4 | 3 | 0 | 0.00 |
| `src/pycode_kg/store.py` | 2 | 2 | 8 | 2 | 0.18 |
| `src/pycode_kg/snapshots.py` | 0 | 5 | 4 | 0 | 0.00 |
| `src/pycode_kg/index.py` | 5 | 4 | 5 | 0 | 0.00 |
| `src/pycode_kg/visitor.py` | 1 | 1 | 1 | 1 | 0.33 |
| `src/pycode_kg/architecture.py` | 0 | 4 | 1 | 1 | 0.33 |
| `src/pycode_kg/layout3d.py` | 3 | 5 | 0 | 0 | 0.00 |
| `src/pycode_kg/mcp_server.py` | 16 | 0 | 0 | 3 | 0.75 |

---

## 🔗 Critical Call Chains

Deepest call chains in the codebase. These represent critical execution paths.

**Chain 1** (depth: 2)

```
_analyze_fan_in → FunctionMetrics
```

**Chain 2** (depth: 2)

```
visit_ClassDef → _qualname
```

**Chain 3** (depth: 2)

```
_is_compatible_stub_caller → node_id
```

**Chain 4** (depth: 2)

```
visit_FunctionDef → _seed_params
```

**Chain 5** (depth: 2)

```
expr_to_name → expr_to_name
```

---

## 🔓 Public API Surface

Identified public APIs (module-level functions with high usage).

| Function | Module | Fan-In | Type |
|----------|--------|--------|------|
| `PyCodeKG()` | src/pycode_kg/kg.py | 8 | class |
| `GraphStore()` | src/pycode_kg/store.py | 8 | class |
| `SnapshotManager()` | src/pycode_kg/snapshots.py | 6 | class |
| `build()` | src/pycode_kg/cli/cmd_build_full.py | 4 | function |
| `SentenceTransformerEmbedder()` | src/pycode_kg/index.py | 4 | class |
| `FunctionMetrics()` | src/pycode_kg/pycodekg_thorough_analysis.py | 4 | class |
| `pack()` | src/pycode_kg/cli/cmd_query.py | 3 | function |
| `CodeGraph()` | src/pycode_kg/graph.py | 3 | class |
| `SemanticIndex()` | src/pycode_kg/index.py | 3 | class |
| `SnapshotDelta()` | src/pycode_kg/snapshots.py | 3 | class |
---

## 📝 Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 96 | 102 | 🟢 94.1% |
| `method` | 172 | 172 | 🟢 100.0% |
| `class` | 36 | 36 | 🟢 100.0% |
| `module` | 33 | 38 | 🟢 86.8% |
| **total** | **337** | **348** | **🟢 96.8%** |



---

## ⚠️  Code Quality Issues

- No major issues detected

---

## ✅ Architectural Strengths

- ✓ Well-structured with 15 core functions identified
- ✓ No obvious dead code detected
- ✓ No god objects or god functions detected
- ✓ Good docstring coverage: 96.8% of functions/methods/classes/modules documented

---

## 💡 Recommendations

### Medium-term Refactoring
1. **Harden high fan-in functions** — `FunctionMetrics`, `_qualname`, `node_id` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for critical call chains** — the identified call chains represent high-risk execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `PyCodeKG`, `GraphStore`, `SnapshotManager`
2. **Enforce layer boundaries** — add linting or CI checks to prevent unexpected cross-module dependencies as the codebase grows
3. **Monitor hot paths** — instrument the high fan-in functions identified here to catch performance regressions early

---

## 🧬 Inheritance Hierarchy

**8** INHERITS edges across **9** classes. Max depth: **1**.

| Class | Module | Depth | Parents | Children |
|-------|--------|-------|---------|----------|
| `SentenceTransformerEmbedder` | src/pycode_kg/index.py | 1 | 1 | 0 |
| `AlliumLayout` | src/pycode_kg/layout3d.py | 1 | 1 | 0 |
| `LayerCakeLayout` | src/pycode_kg/layout3d.py | 1 | 1 | 0 |
| `Embedder` | src/pycode_kg/index.py | 0 | 0 | 1 |
| `Layout3D` | src/pycode_kg/layout3d.py | 0 | 1 | 2 |
| `PyCodeKGVisitor` | src/pycode_kg/visitor.py | 0 | 1 | 0 |
| `DocstringPopup` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |
| `KGVisualizer` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |
| `MainWindow` | src/pycode_kg/viz3d.py | 0 | 1 | 0 |


---

## 📸 Snapshot History

Recent snapshots in reverse chronological order. Δ columns show change vs. the immediately preceding snapshot.

| # | Timestamp | Branch | Version | Nodes | Edges | Coverage | Δ Nodes | Δ Edges | Δ Coverage |
|---|-----------|--------|---------|-------|-------|----------|---------|---------|------------|
| 1 | 2026-03-10 21:35:57 | develop | 0.7.1 | 5301 | 5222 | 96.8% | +0 | +0 | +0.0% |
| 2 | 2026-03-10 11:28:03 | develop | 0.7.1 | 5301 | 5222 | 96.8% | +141 | +122 | +1.5% |
| 3 | 2026-03-10 02:16:55 | develop | 0.7.1 | 5160 | 5100 | 95.3% | +85 | +74 | -0.3% |
| 4 | 2026-03-10 01:29:05 | develop | 0.7.1 | 5075 | 5026 | 95.6% | +139 | +99 | -0.8% |
| 5 | 2026-03-10 01:15:27 | develop | 0.7.1 | 4936 | 4927 | 96.4% | +0 | +0 | +0.0% |
| 6 | 2026-03-10 01:10:01 | develop | 0.7.1 | 4936 | 4927 | 96.4% | +0 | +0 | +0.0% |
| 7 | 2026-03-09 18:55:34 | develop | 0.7.1 | 4936 | 4927 | 96.4% | +0 | +0 | +0.0% |
| 8 | 2026-03-09 17:36:09 | develop | 0.7.1 | 4936 | 4927 | 96.4% | -36 | -5 | -0.4% |
| 9 | 2026-03-09 13:42:57 | develop | 0.7.0 | 4972 | 4932 | 96.8% | +0 | +0 | +0.0% |
| 10 | 2026-03-09 13:18:31 | develop | 0.7.0 | 4972 | 4932 | 96.8% | +0 | +0 | +0.0% |


---

## 📋 Appendix: Orphaned Code

Functions with zero callers (potential dead code):

✓ No orphaned functions detected.


---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in 4.9s*
