# PyCodeKG Agent Assessment — Claude Code (Remote Execution)

**Assessor:** Claude Code, remote execution environment (model identity withheld per harness policy; ask the session owner)
**Date:** 2026-06-10
**Subject repo:** PyCodeKG itself, v0.19.3 (self-indexing — 6,283 nodes / 5,875 edges; 379 meaningful nodes)
**Platform:** Ephemeral Linux cloud container, Python 3.13.x, fresh clone, no GPU
**Protocol:** `assessments/AssessmentProtocol_PyCodeKG.md`
**Methodology note:** No MCP host was attached to this session, so I installed the package from source (`uv pip install -e .`, Python 3.13 venv), built both graph layers from scratch, and invoked the `@mcp.tool()` functions in `mcp_server.py` directly from Python after replicating `main()`'s initialization. Same code paths as MCP transport, minus serialization overhead. All timings below are warm-process wall clock unless noted.

---

## 1. Executive Summary

This is the first assessment in this directory performed from a completely cold environment: no prebuilt graph, no cached model, no MCP host. That turned out to be the most persuasive part. From `pip install` to a queryable hybrid knowledge graph took under a minute of compute: `build-sqlite` indexed the repo in **2.9 s** (6,283 nodes, 913 resolved cross-module symbols) and `build-lancedb` took **35 s including the BGE model download**. Once warm, every structural tool answers in single-digit-to-low-double-digit milliseconds, and hybrid semantic queries return in **~30 ms**. The whole four-phase protocol consumed less wall-clock time than a single thorough grep-and-read pass over an unfamiliar repo would have.

The accuracy spot-checks were the highlight. `callers()` on `_get_kg` reported exactly 17 callers; naive `grep -c "_get_kg()"` returns 18 because it counts the `def` line itself — the graph was right and grep needed manual correction. Better still, a `graph.extract()` call appearing inside a docstring example at `graph.py:32` was correctly *excluded* from the call graph. Static analysis that doesn't count docstring code is exactly the kind of precision an agent needs to trust a tool.

I also found two genuine defects, which is what an assessment is for. First, a cold-start ordering bug: in a fresh server session, calling `list_nodes()` or `find_node()` **as the first tool call** returns `{"error": "No database store available."}` because both read the private lazy field via `getattr(kg, "_store", None)` instead of the initializing `kg.store` property; any other store-touching call first (e.g. `graph_stats()`) masks it. I reproduced this deterministically in a fresh process. Second, a same-name resolution conflation: `CodeGraph.extract` lists `build_sqlite` and `_run_pipeline` among its callers, but those sites call `PyCodeKGExtractor.extract()` — a different method that merely *delegates* to `CodeGraph`. Indirectly true, structurally misattributed. Neither defect undermines the verdict: **4.5 / 5, recommended without hesitation** — but both should be fixed.

---

## 2. Tool-by-Tool Evaluation

| Tool | Latency | Verdict | Notes |
|------|--------:|---------|-------|
| `graph_stats` | 4 ms | 5/5 | Perfect orientation call: node/edge breakdown, docstring coverage (92.8%), snapshot count, and a footnote explaining `sym:` stubs so the 5,904 symbol nodes don't mislead you. |
| `analyze_repo` | 8.4 s | 4.5/5 | 11.7 KB Markdown report. Fan-in table, orchestrator detection (`cmd_init.init()` with fan-out 43), module cohesion, public API surface. Slight docs drift: the tool docstring says "nine-phase pipeline" while the README and CLI advertise 15 phases. |
| `query_codebase` | 6.2 s cold, 27–29 ms warm | 4/5 | Precise query ("LanceDB vector index construction") and exploratory query ("where does graph extraction start") both put the right nodes on top with `via_seed` provenance. Broad query ("error handling strategy") diluted: positions 4–8 were `viz3d.py` GUI methods at semantic ≈0.56. Scores cluster in 0.55–0.66; thresholds matter. |
| `pack_snippets` | 26–27 ms | 5/5 | Source-grounded snippets with real line numbers, relevance components broken out per node (semantic / lexical / docstring / hop), and context lines around each definition. This is the tool I'd reach for first in a real task. |
| `get_node(include_edges=True)` | 1–3 ms | 5/5 | Location, docstring, incoming calls with caller line numbers, outgoing CALLS — one call replaces a grep + several file reads. |
| `explain` | 8–14 ms | 4.5/5 | The "Role in Codebase" synthesis is genuinely useful ("Called 17 times (≥7 = top 2% of this codebase)"). |
| `callers` | 5 ms | 4/5 | Correct and complete (all 17 callers of `_get_kg`), but the JSON includes each caller's **full untruncated docstring** — 23.4 KB for 17 callers. For an LLM consumer that's expensive context for information `explain()` conveys in 1.1 KB. |
| `find_node` | 4 ms | 4/5 | Found both `compute_coderank` definitions instantly. Subject to the cold-start store bug below. |
| `list_nodes` | <1 ms | 3/5 | Works after warm-up, but **fails as the first call of a session** (see Weaknesses). Also no `limit` parameter, so a kind-wide listing on a big repo is unbounded output. |
| `find_definition_at` | 17 ms | 5/5 | Reverse (file, line) → node lookup; resolved `mcp_server.py:160` to `_get_kg` with the full explain report. Exactly what an agent holding a traceback wants. |
| `centrality` / `bridge_centrality` / `framework_nodes` | 14–91 ms | 4/5 | Fast and explainable. Caveat: `viz3d.py` (a PyQt GUI) tops both connectivity and framework rankings because dense internal wiring scores like architectural centrality. Numbers are correct; interpretation needs care. |
| `query_ranked` / `explain_rank` | 6.4 s cold / 155 ms | 4.5/5 | The per-result `why` array ("direct semantic seed", "called by 1 upstream node(s)") and the score decomposition in `explain_rank` are the most LLM-legible ranking explanations I've seen in a code tool. |
| `snapshot_list` / `snapshot_show` / `snapshot_diff` | 10–18 ms | 4.5/5 | 109 snapshots on this clone. Diffed 2026-05-25 → 2026-06-09 in 10 ms with per-module node deltas. A temporal axis grep simply does not have. |

---

## 3. Scorecard

| Dimension | Score | Justification |
|-----------|------:|---------------|
| **Accuracy** | 4.5 | `_get_kg` caller count exactly right where grep over-counts; docstring-embedded calls correctly excluded. Docked half a point for the `PyCodeKGExtractor.extract` → `CodeGraph.extract` same-name conflation. |
| **Relevance** | 4 | Precise and exploratory queries excellent with seed provenance; broad architectural queries dilute into popular GUI modules. |
| **Completeness** | 4.5 | All 55 modules, 5 edge relations, 913 resolved cross-module symbols, 92.8% docstring coverage measured. |
| **Efficiency** | 5 | Sub-30 ms warm queries, 1–5 ms structural lookups, full graph rebuild in 2.9 s. The entire protocol cost less time than reading three files. |
| **Insight Generation** | 4.5 | Fan-out 43 on `init()`, top-2% fan-in framing, 109-snapshot history — none of this is discoverable by file reading at comparable cost. |
| **Usability** | 4 | Markdown outputs are model-ready and self-documenting. Docked for the `list_nodes` cold-start failure, `callers()` verbosity, and missing `limit` parameter. |
| **Architectural Value** | 4.5 | `analyze_repo` is a real orientation document; centrality tools need human/agent judgment about GUI-module skew. |
| **Uniqueness** | 4.5 | The combination of deterministic AST graph + local vector seeding + explainable ranking + temporal snapshots, all behind MCP, has no equivalent in my default toolkit. |

---

## 4. Comparison to Default Workflow

My baseline in this exact session would have been `Grep`/`Glob`/`Read`. Concrete comparison from this run: answering "who calls `_get_kg` and how important is it?" took one `explain()` call (14 ms, 1.1 KB of model-ready Markdown). The grep equivalent returned 18 matches needing manual triage (the `def` line, plus verifying none were docstring mentions — which, notably, the graph had already handled at `graph.py:32`). For "where does extraction start?", `query_codebase` put `CodeGraph.extract`, `extract_repo`, and `PyCodeKGExtractor` in the top 5 from a vague natural-language phrase; grep requires already knowing the vocabulary. The honest caveat: for a *single* known-string lookup, grep is still simpler — PyCodeKG's advantage compounds with question depth, and it is decisive for caller resolution, ranking, and anything temporal.

## 5. Strengths

- **Trust through verifiability.** Every claim carries a file and line number; my spot-checks against raw source all passed (with the one conflation noted).
- **Cold-start economics.** Fresh container → queryable hybrid graph in under a minute. This matters for ephemeral CI/cloud agents like the one writing this.
- **Provenance everywhere.** `via_seed`, relevance component breakdowns, `why` arrays, SIR score decomposition — the tool shows its work, which is exactly what lets an agent decide how much to trust a result.
- **Docstring-aware call graph.** Excluding example code in docstrings from CALLS edges is a subtle correctness win most tools miss.

## 6. Weaknesses & Suggestions

1. **Cold-start store bug (fix-worthy).** `list_nodes()` and `find_node()` use `getattr(kg, "_store", None)` and error out if they're the session's first tool call; `kg_utils.pipeline.KGModule` only creates `_store` inside the `store` property. **Fix:** use `kg.store` (one-line change, two sites in `mcp_server.py`). Reproduced deterministically in a fresh process.
2. **Same-name method conflation.** `extractor.extract()` call sites are attributed to `CodeGraph.extract`. **Suggestion:** when receiver type is unknown, either emit edges to all candidates with a `confidence` field or prefer the receiver's class when assignment is locally resolvable.
3. **`callers()` payload size.** 23.4 KB for 17 callers due to full docstrings. **Suggestion:** truncate docstrings to ~120 chars (as `find_node` already does) with an opt-in `full_docstrings` flag.
4. **Broad-query dilution.** High-degree GUI modules absorb relevance on vague queries. **Suggestion:** a non-zero default `max_per_module` when query length/specificity is low.
5. **Docs drift.** `analyze_repo`'s docstring says "nine-phase"; README says 15. Given this repo's own MCP-instruction-sync rule, that's a self-detectable inconsistency.
6. **`list_nodes` lacks `limit`/pagination** — unbounded output on large repos.

## 7. Overall Verdict

**4.5 / 5 — recommended without hesitation.** PyCodeKG converts codebase comprehension from an iterative guessing game into a sequence of cheap, verifiable lookups. It proved itself under the least favorable conditions available — an ephemeral container with nothing cached — and the two defects I found are small, precisely localized, and were themselves found *using the tool's own outputs cross-checked against source*, which is the workflow the tool exists to enable. Best fit: agent-assisted work on any non-trivial Python codebase, refactoring triage, and CI-tracked architectural health. The one habit users should keep: treat centrality rankings as evidence, not conclusions, on GUI-heavy repos.
