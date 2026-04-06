# CodeKG Agent Assessment
## Model: claude-sonnet-4-6 | Date: 2026-03-11

**Assessor:** Claude Sonnet 4.6 (claude-sonnet-4-6)
**Repository indexed:** code_kg itself (self-referential)
**Graph version:** 0.8.0 | 353 meaningful nodes | 5,369 edges

---

## 1. Executive Summary

CodeKG is a genuinely useful tool that changes how an AI agent navigates a Python codebase. Rather than reading files sequentially or running grep searches in the dark, an agent equipped with CodeKG can orient itself in seconds using `graph_stats()`, pinpoint relevant code through hybrid semantic+structural search, and trace call relationships without ever opening a file. The workflow compression is real and substantial.

The tool suite is internally consistent and well-documented. Across all four phases of this assessment—orientation, semantic search, structural navigation, and temporal analysis—every tool returned useful output without errors. The standout tools are `get_node(include_edges=True)`, `explain()`, and `pack_snippets()`, which together replace what would otherwise require five or more file-read and grep operations. The hybrid reranker (70% semantic / 30% lexical) is a meaningful improvement over pure vector search, especially when docstrings are rich.

The primary weakness is semantic search precision for abstract queries (e.g., "error handling strategy"): the lexical component can surface nodes whose *docstrings mention* a concept without the node *implementing* it. Relevance scores cluster in a narrow 0.35–0.73 band, making it hard to distinguish strong matches from noise. The `analyze_repo()` fan-in table also has a signal-to-noise issue: constructors and dataclass instantiations appear as "most called" functions, which is technically correct but architecturally misleading. These are solvable problems and do not undermine the core value.

---

## 2. Tool-by-Tool Evaluation

### `graph_stats()`
**Rating: 5/5**

Returns a clean markdown summary of node and edge counts, broken down by kind and relation. The critical design choice of separating `meaningful_nodes` (353) from `total_nodes` (5,497) is immediately clarifying—without it, the 5,144 `sym:` stub nodes would dominate the picture and mislead orientation. Output arrived in under 1 second. This is the correct first call, and the tool is exactly scoped for that role.

One minor note: the output doesn't show which embedding model is active. Knowing the model matters when assessing expected semantic quality (BAAI/bge-small-en-v1.5 vs. MiniLM vs. CodeBERT will produce different score distributions).

---

### `analyze_repo()`
**Rating: 3.5/5**

The nine-phase analysis covers all the right territory: fan-in/fan-out, module coupling, docstring coverage, inheritance hierarchy, and orphaned code. The 97.2% docstring coverage figure is meaningful—it directly predicts semantic search quality. The module architecture table correctly notes "showing 10 of 38 total" which prevents silent truncation confusion (a previous known issue, now fixed).

**Issues found:**

1. **Fan-in ranking is misleading.** The top "most-called" functions are `FunctionMetrics()`, `ModuleMetrics()`, and `ModuleLayer()`—all dataclass constructors with 1–4 callers. These are not bottlenecks or core functionality; they're just frequently instantiated value objects. The table title says "Most-called functions are potential bottlenecks or core functionality"—but these are neither. A filter excluding constructors/dataclasses, or a separate column for "kind", would greatly improve signal.

2. **`viz3d.__init__` fan-out flag is a false positive.** The critical issue "🔴 `__init__` has high fan-out (95 calls)" refers to the Qt main window constructor building all its UI elements. This is a natural, intentional pattern for GUI initialization, not an architectural smell. The report doesn't distinguish between GUI construction (expected to be large) and business logic orchestrators (where high fan-out *is* a concern).

3. **"No deep call chains detected"** — with `viz3d.__init__` having 95 outgoing calls, this seems underdetected. The call chain analysis may not be traversing into that file, or the threshold is too high.

**Strengths:** Inheritance hierarchy table is excellent—depth, parents, children at a glance. Orphan detection is accurate (no false positives observed). Snapshot history embedded in the analysis is a smart design choice.

---

### `query_codebase()`
**Rating: 3.5/5**

Tested with three query types:

**Precise query — "graph database storage SQLite persistence" (score range 0.49–0.69)**
Results were highly accurate: `GraphStore` class, `store.py` module, and `_load_store` all correctly surfaced. The hop=1 expansion appropriately pulled in `CodeKG.store` (the lazy property that opens the store) and `build_graph` (which writes to it). Edge provenance was included in JSON and correctly reflected CALLS relationships with source line numbers.

**Broad query — "error handling exception strategy" (score range 0.38–0.61)**
Top result was `CodeKG.query` with score 0.61 — a **false positive**. The method's docstring happens to mention "error handling" in an example list of concepts, but the method itself is the hybrid query engine, not error-handling code. The codebase's actual error handling (simple `try/except` in CLI commands) was not surfaced at all. This illustrates a real weakness: the lexical boosting on docstring text can be gamed by incidental mentions.

**Exploratory query — "CLI entry points configuration startup" (score range 0.47–0.73)**
Excellent results. `mcp_server.py` module ranked first (0.73) because its docstring explicitly lists "Entry points and configuration" as a section header. `main()` ranked second (0.67), `cli/__init__.py` third (0.61). The lexical boost correctly amplified exact phrase matches. This is the use case where hybrid reranking shines: the semantic vector alone would have ranked these lower.

**Observation:** The `paths` parameter for restricting results to a subtree is a very useful precision tool that shouldn't be overlooked. In larger codebases, scoping to `src/` vs. `tests/` will dramatically improve signal.

---

### `pack_snippets()`
**Rating: 5/5**

This is the flagship tool. It returns actual source code with surrounding context and line numbers, ranked by the same hybrid scoring as `query_codebase()`. A single `pack_snippets()` call replaced what would otherwise require: (1) running `query_codebase()`, (2) looking up each node ID, (3) reading the relevant file, (4) finding the right line range, (5) reading neighboring context.

The output format—a Markdown "context pack" with `node id`, `module path`, `line`, relevance breakdown, and fenced code—is immediately usable. Deduplication across overlapping node spans prevents the same code from appearing twice. The `missing_lineno_policy=cap_or_skip` default is appropriate and the Warnings section correctly flags when snippets are omitted.

The `max_lines=60` default is well-chosen for LLM token budgets. Setting `context=5` gives just enough surrounding code to understand the function's invocation pattern.

---

### `get_node(node_id, include_edges=True)`
**Rating: 5/5**

Tested on `cls:src/code_kg/store.py:GraphStore`. With `include_edges=True`, a single call returned:
- Full docstring with usage examples
- 19 CONTAINS edges (all methods of GraphStore by name)
- 8 incoming CALLS callers with source file and line number

This completely replaces a typical "find the class, read the file, grep for usages" workflow. The caller list is cross-module and resolved through `sym:` stubs — `_load_store` in `app.py`, `build_sqlite` in CLI, `save_snapshot` in `cmd_snapshot.py` were all correctly included. Without this tool, tracing those cross-module callers would require multiple grep operations.

The stable ID format (`cls:src/code_kg/store.py:GraphStore`) is predictable once learned. `query_codebase()` → `get_node()` is a natural two-step workflow.

---

### `explain(node_id)`
**Rating: 4.5/5**

Tested on `m:src/code_kg/kg.py:CodeKG.query` and `fn:src/code_kg/mcp_server.py:main`.

For `CodeKG.query`: returned 6 callers (analysis pipeline, app UI, CLI, MCP server), 8 callees (scoring helpers + index search), full docstring, and a role assessment. The output is immediately orientating. One quibble: the role assessment calls it a "🟢 Utility function: Called 6 time(s)" — with 6 callers across multiple subsystems and 8 callees including the entire scoring machinery, this is more accurately the *core query engine*, not a utility. The threshold for "high-value" vs. "utility" deserves tuning.

For `main()`: simple and accurate — 1 caller, 1 callee, clean role summary. Works correctly for simple functions.

**Strength:** Unlike `get_node()`, `explain()` renders callers and callees in prose rather than raw JSON, making it more readable for quick orientation. The two tools are complementary — `get_node(include_edges=True)` for structured inspection, `explain()` for narrative orientation.

---

### `callers(node_id)`
**Rating: 5/5**

Tested on `m:src/code_kg/store.py:GraphStore.expand` with `paths="src/"`.

Returned exactly 2 callers: `CodeKG.query` (line 644) and `CodeKG.pack` (line 800). Both are correct. The `call_site_lineno` field makes this immediately actionable — I know exactly which line of `kg.py` to look at. The `sym:` resolution through import stubs is the key differentiator from a naive grep — cross-module callers that reference `expand` through an aliased import would still be found.

The `paths` scoping is important for large codebases; restricting to `src/` excluded test files from the count automatically.

---

### `snapshot_list()` / `snapshot_show()` / `snapshot_diff()`
**Rating: 4/5**

**`snapshot_list()`:** 10 snapshots available, all on `develop` branch. Each entry has key, timestamp, version, metrics, deltas vs. previous, and a freshness indicator vs. current DB. The freshness field (`fresh` / `near_fresh` / `behind`) is practical — it immediately tells an agent whether the snapshot is still representative. Pre-commit hook integration means snapshots accumulate automatically with every commit, requiring no agent action.

**`snapshot_show("latest")`:** Returns full metrics plus a hotspots list and issue list. The delta fields vs. both `vs_previous` and `vs_baseline` allow reasoning about both recent changes and long-term trajectory.

**`snapshot_diff(oldest, newest)` — across ~33 hours of active development:**
- +337 total nodes (+9 functions, +2 methods, +326 `sym:` stubs)
- +269 edges (+131 CALLS, +82 ATTR_ACCESS)
- Coverage: 95.3% → 97.2% (+1.9 percentage points)
- Critical issues: 0 → 2 (viz3d `__init__` fan-out introduced)
- 0 new classes (structural design was stable)

This tells a coherent story: active function/method development, improving documentation, no new architectural coupling introduced. The `issues_delta.introduced` / `resolved` arrays are the right abstraction — a CI system could alert on this list.

**Minor issues:** The `snapshot_diff` output correctly shows `node_counts_delta` broken out by kind. However, if both snapshots are "behind" current DB, there's no warning that the diff is between two stale states. A freshness warning on the diff output itself would help.

---

### `list_nodes(module_path, kind)`
**Rating: 4/5**

Not explicitly in the protocol but used implicitly when exploring. Returns a flat JSON array of nodes matching a module prefix and/or kind filter. Useful for enumerating "all functions in `src/code_kg/store.py`" before deciding which to inspect with `get_node()`. Less useful than `get_node(include_edges=True)` for a single known class, but fills a gap when you need to survey a whole module.

---

## 3. Scorecard

| Dimension | Score | Justification |
|-----------|-------|---------------|
| **Accuracy** | 5/5 | Nodes, edges, callers, and line numbers are all verified correct against the actual codebase. No false edges observed. `sym:` resolution correctly disambiguated cross-module callers. |
| **Relevance** | 3.5/5 | Precise and exploratory queries return excellent results. Broad/abstract queries (e.g., "error handling") can surface nodes that mention a concept without implementing it. Score range is narrow, making confidence discrimination difficult. |
| **Completeness** | 4.5/5 | 97.2% docstring coverage → 353 meaningful nodes indexed with rich metadata. All 38 modules present. `sym:` stubs ensure cross-module edges are preserved. Minor gap: abstract concepts not expressed in docstrings are not findable semantically. |
| **Efficiency** | 5/5 | `graph_stats()` in ~1s. `pack_snippets()` in ~2–3s for a complex query. Replaced what would be 5+ sequential file reads. `get_node(include_edges=True)` eliminates the grep-for-usages step entirely. |
| **Insight Generation** | 4.5/5 | `snapshot_diff` revealed that 0 new classes were added across 33 hours of active development — structural stability during feature growth, not evident from commit messages alone. `explain()` showed `CodeKG.query` is called by the analysis pipeline internally, not just externally — a dependency I wouldn't have found by reading `kg.py` alone. |
| **Usability** | 4.5/5 | Stable ID format is learnable. Markdown output is clean and directly renderable. `include_edges=True` is a well-designed opt-in. Primary friction: no way to autocomplete or discover node IDs without running `query_codebase()` first; could benefit from a `list_nodes(kind='class')` as a browsing entry point. |
| **Architectural Value** | 3.5/5 | `analyze_repo()` correctly identifies `store.py` and `kg.py` as the high-coupling core. Module cohesion table is useful. Fan-in ranking is noisy (dataclass constructors dominate). The viz3d fan-out false positive reduces trust in the critical issues list. |
| **Uniqueness** | 5/5 | No other codebase analysis approach I've encountered combines semantic vector search, structural graph traversal, source-grounded snippets, and temporal snapshots in a single MCP-accessible interface. The `sym:` import stub resolution for cross-module caller lookup is particularly novel. |

**Overall Average: 4.4/5**

---

## 4. Comparison to Default Workflow

Without CodeKG, my default approach for understanding a new Python codebase is:

1. `ls`/`glob` to find files
2. Read `__init__.py` files to understand package structure
3. `grep` for class/function names to find usages
4. Read relevant files in full
5. Manually trace imports across modules

With CodeKG, that workflow compresses to:

1. `graph_stats()` — understand scale and shape (replaces steps 1–2)
2. `query_codebase()` or `pack_snippets()` — find relevant code by concept (replaces step 3)
3. `get_node(include_edges=True)` — understand a node's neighborhood (replaces steps 4–5)

The compression is most dramatic for **cross-module caller tracing** and **concept-first search**. Grep cannot find "all callers of `GraphStore.expand` across the entire codebase including through import aliases" — `callers()` does this in one call. Grep cannot find "code related to SQLite persistence" without knowing the class name first — `query_codebase()` does this without priors.

The one area where CodeKG doesn't replace file reading: when I need to understand *implementation details* (the actual SQL in `GraphStore.write`, for example), `pack_snippets()` with `context=5` handles this but longer methods may still require a direct `Read` call if they exceed `max_lines`.

---

## 5. Strengths

1. **`get_node(include_edges=True)` is a workflow killer** — one call surfaces the class structure, all methods, and all cross-module callers with line numbers. Nothing else comes close.

2. **Source-grounded snippets with line numbers** — `pack_snippets()` returns actual code, not summaries. Combined with relevance scores and the hybrid reranker, this is immediately actionable for LLM reasoning.

3. **`sym:` resolution makes callers() cross-module accurate** — import alias disambiguation means fan-in analysis works across the full codebase, not just within a single file.

4. **Temporal snapshots + freshness indicator** — the `snapshot_diff` approach enables genuine codebase evolution reasoning. The freshness field tells an agent immediately whether a snapshot is still representative.

5. **97.2% docstring coverage** — the codebase is its own best advertisement; rich docstrings are what make semantic search work well. The analyze_repo() coverage report provides a direct quality signal for expected search performance.

6. **Self-describing and well-scoped tools** — each tool has a clear single purpose. The parameter taxonomy (`k`, `hop`, `rels`, `min_score`, `max_per_module`) is consistent across `query_codebase()` and `pack_snippets()`, reducing the learning curve.

7. **`paths` scoping** — the ability to restrict queries to a subtree (e.g., `src/` only) prevents test code from contaminating production architecture analysis.

---

## 6. Weaknesses & Suggestions

### W1: Abstract queries return docstring-contaminated results
**Observed:** "error handling exception strategy" returned `CodeKG.query` as top result because the method's docstring mentions "error handling" as an example concept, not as something the method implements.

**Suggestion:** Add a `min_score` threshold recommendation in the tool description (e.g., "for precision queries, use `min_score=0.5`"). Consider a `docstring_boost_cap` parameter that limits how much docstring lexical signal can inflate a result relative to its semantic score.

### W2: analyze_repo() fan-in table conflates constructors with functions
**Observed:** `FunctionMetrics()`, `ModuleMetrics()`, `ModuleLayer()` dominate the "most-called" table with 1–4 callers, but they are dataclass instantiations.

**Suggestion:** Filter constructors from the fan-in ranking, or add a `kind` column so the caller can filter themselves. A separate section for "most-instantiated classes" vs. "most-called functions" would be cleaner.

### W3: viz3d `__init__` fan-out is a false positive
**Observed:** Qt GUI constructor with 95 calls is flagged as a critical architectural issue.

**Suggestion:** Exempt `__init__` methods from high fan-out detection, or raise the threshold significantly (95 is a GUI layout, not a god object). Alternatively, add a `kind` qualifier: "high fan-out non-constructor function" is meaningful; "high fan-out constructor" generally is not.

### W4: Relevance score range is narrow and hard to read
**Observed:** All results in "precise" query ranged 0.49–0.69; "broad" query ranged 0.38–0.61. The dynamic range is insufficient to reliably distinguish "strong match" from "marginal match."

**Suggestion:** Consider normalizing scores to the returned result set (rank-normalized rather than absolute scores), or providing a confidence tier (`HIGH` / `MEDIUM` / `LOW`) alongside the numeric score.

### W5: explain() "role assessment" thresholds need tuning
**Observed:** `CodeKG.query` with 6 callers across 3 subsystems is labeled "🟢 Utility function." It is the core query engine of the entire system.

**Suggestion:** Role assessment should consider the *diversity* of callers (cross-subsystem calls are more significant than 10 calls from within the same class) and the semantic content of the node. Alternatively, a callee-count threshold for "orchestrator" classification would catch query/pack methods that call many scoring helpers.

### W6: No way to list all available node IDs without a semantic query
**Observed:** To explore what's in `src/code_kg/snapshots.py`, I must either know a function name to search for, or use `query_codebase()` with a broad query.

**Suggestion:** `list_nodes(module_path="src/code_kg/snapshots.py")` exists and works — but it's not prominent in the recommended workflow. Make it an explicit step in the "Explore unfamiliar code" workflow in tool documentation.

---

## 7. Overall Verdict

**Rating: 4.4/5 — Highly Recommended for AI Agents Working in Python Codebases**

CodeKG is not a convenience wrapper around grep — it's a qualitatively different interface to a codebase. The combination of hybrid semantic+structural search, source-grounded snippets, precise reverse call lookup, and temporal evolution tracking enables an AI agent to understand a codebase with substantially less tool-call overhead and file-reading noise than any alternative I've encountered.

**Best use cases:**
- Orienting in an unfamiliar codebase (graph_stats → query → explain → pack)
- Impact analysis before a change (callers → get_node)
- Code review context gathering (pack_snippets for a PR's touched files)
- Architectural health monitoring in CI/CD (snapshot_diff on each PR merge)
- Onboarding agents to large, well-documented Python projects

**Where it's less effective:**
- Codebases with low docstring coverage (semantic search degrades significantly below ~70%)
- Finding code that's described in comments rather than docstrings
- Abstract architectural concepts that aren't expressed in any identifier or docstring
- Very small codebases where direct file reading is faster

The `viz3d.__init__` false positive in `analyze_repo()` and the narrow score range are the two issues most worth fixing before v1.0. Everything else is refinement. The core pipeline—vector seeding → graph expansion → hybrid reranking → source extraction—is sound and meaningfully better than the alternatives.

---

*Assessment performed 2026-03-11 against code_kg v0.8.0 (develop branch), 353 meaningful nodes, BAAI/bge-small-en-v1.5 embedding model.*
