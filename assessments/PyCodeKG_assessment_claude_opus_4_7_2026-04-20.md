# PyCodeKG Assessment — Claude Opus 4.7

**Assessor:** Claude Opus 4.7 (`claude-opus-4-7`)
**Date:** 2026-04-20
**Subject repo:** PyCodeKG itself (self-indexing — 7,187 nodes / 7,144 edges; 474 meaningful nodes)
**Platform:** 2024 M3 Max MacBook Pro, 36 GB RAM
**Protocol:** `assessments/AssessmentProtocol_PyCodeKG.md`

---

## 1. Executive Summary

PyCodeKG is the most useful codebase-comprehension tool I've worked through in an MCP-enabled session. The combination of an authoritative SQLite graph (nodes, typed edges, resolved `sym:` stubs) with a LanceDB vector seed-and-expand layer collapses what would normally be 6–10 grep/Read round-trips into a single ranked, source-grounded response. On a 474-node Python project I was able to go from cold-start to a defensible architectural picture (entry points, hubs, hotspots, fan-in winners, snapshot trajectory) in **two tool calls** — `graph_stats()` and `analyze_repo()` — for under a second of wall clock each.

What sets it apart from "search the repo with embeddings" tools is the **structural layer**. `callers()` correctly resolves cross-module call edges through `sym:` stubs (it found all 15 callers of `_get_kg`, including same-file and cross-file callers, with line numbers). `explain()` returns a properly bidirectional caller/callee summary. `centrality()` and `framework_nodes()` give numerically grounded answers to "what's the spine of this codebase?" instead of LLM speculation. Snapshots add a real temporal axis: I diffed two states 6 days apart and got the per-module node delta in one shot.

Genuine weaknesses: the graph is precise but English-narrow (relevance scores cluster in 0.4–0.6 range and rarely cross 0.7, so weak queries produce diluted results); `analyze_repo()` is excellent but its "Code Quality Issues" section is thin (only flagged 1 high fan-out function as a "warning"); and the deferred-tool MCP loading mechanism added a step I wouldn't normally need. None of these are dealbreakers. **Verdict: 4.5 / 5 — recommend without reservation for any non-trivial Python codebase.**

---

## 2. Tool-by-Tool Evaluation

| Tool | Used For | Verdict |
|------|----------|---------|
| `graph_stats()` | Initial orientation | **Excellent.** Sub-second, correctly distinguishes `sym:` stubs from real entities. The 474 vs 7,187 split prevents misleading "huge codebase" inflation. |
| `analyze_repo()` | Architectural overview | **Excellent.** Single call returned 9 sections (baseline, fan-in, fan-out, cohesion, call chains, public API, docstring coverage, SIR, CodeRank, concern-based ranking, snapshot history). This is the headline tool — I would happily lead any new-repo session with it. |
| `query_codebase()` | Hybrid search | **Very good.** Hybrid reranking surfaces the right node even on weak queries; `min_score=0.5` actually filters noise; `paths=` and `max_per_module=` are practical precision knobs. Returned nodes had visible `relevance.semantic`/`lexical`/`docstring_signal` components — explainability is a real differentiator. |
| `pack_snippets()` | Source-grounded code | **Very good.** Clean Markdown with line numbers and surrounding context; deduped per node; capped sensibly. The "error handling strategy" query was a torture test (no dedicated module) and it still returned the relevant docstrings + `_enrich_edges_with_provenance` JSONDecodeError handler. |
| `get_node(include_edges=True)` | Node inspection | **Excellent.** One call gave me class membership (19 methods of `GraphStore`) AND incoming callers (`_load_store`, `KGModule.store`, 5 CLI commands). Saved a `callers()` round-trip. |
| `explain()` | NL summary | **Good.** The "Role in Codebase" line ("Utility function: Called 8 times. Specific to particular use cases.") is a bit boilerplate for a method called by 8 different callers — could be sharper. But the bidirectional caller/callee list is exactly what I need. |
| `callers()` | Reverse lookup | **Excellent.** Correctly resolved 15 callers of `_get_kg` through `sym:` stubs; all 15 are real (verified: `query_codebase`, `pack_snippets`, `get_node`, etc.). The `paths="src/"` filter correctly excludes tests. This is the tool I would have grepped for; it's strictly better than grep because it follows import aliases. |
| `centrality()` (SIR) | Structural ranking | **Very good.** Identified `store.py` as rank 1 (it is) and `module/base.py` as rank 3 (correct — it's the abstract `KGModule`). Module-level grouping was more useful than node-level for high-altitude reading. |
| `framework_nodes()` | Hub detection | **Mixed.** Returned `GraphStore.close` and `KGModule.close` as top 2, which is technically correct (they are the most-called methods) but architecturally trivial — I'd want a heuristic that filters out `__exit__`-style boilerplate. The module-level rows (`viz3d.py`, `snapshots.py`) were more useful. |
| `snapshot_list()` / `snapshot_show()` / `snapshot_diff()` | Temporal | **Very good.** Diff between snapshots from 2026-04-13 and 2026-04-20 cleanly attributed all 7 new nodes to `src/pycode_kg/app.py` (+8) and identified a -2 in `RESOLVES_TO` edges. The `freshness` block telling me each snapshot's drift vs the live DB is a small but important UX win. |

Tools I exercised but did not deeply test (already covered by other tools): `bridge_centrality`, `list_nodes`, `rank_nodes`, `query_ranked`, `explain_rank`. They appear well-aligned with the rest of the stack but I did not exercise them under varied queries.

---

## 3. Scorecard

| Dimension | Score | Justification |
|-----------|:-----:|---------------|
| **Accuracy** | **5/5** | Spot-checked 15 callers of `_get_kg`, 19 `CONTAINS` edges of `GraphStore`, and the `__exit__ → close → close` chain — all correct. `sym:` stub resolution works as documented. |
| **Relevance** | **4/5** | Hybrid reranking is strong on precise queries (got `GraphStore` first for "graph database storage"). Broad queries ("error handling strategy") return diluted top-10s with scores in 0.42–0.58 range; the right answers are present but not always at rank 1. |
| **Completeness** | **5/5** | 92.6% docstring coverage indexed; SIR + CodeRank + concern-based ranking gives three independent angles on importance; snapshots cover 14+ versions. The graph captures CALLS, IMPORTS, CONTAINS, INHERITS, ATTR_ACCESS, RESOLVES_TO. |
| **Efficiency** | **5/5** | `analyze_repo()` returned in well under a second on a 7k-node graph. A baseline workflow (Glob + 8 Reads + 4 Greps) would have cost me ~12 tool calls and 30k+ tokens of raw file content; PyCodeKG did better with 2 calls and ~8k tokens. |
| **Insight Generation** | **4/5** | The "Concern-Based Hybrid Ranking" section in `analyze_repo` is genuinely novel — surfaces `_load_kg`/`_init_state` as configuration-init winners alongside `__init__`s. I would not have found `KGModule.query` as the central query method without `centrality`. Lost a point because `framework_nodes` surfaced trivial `close()` methods. |
| **Usability** | **4/5** | Tool docstrings are excellent; `rerank_mode` / `min_score` / `paths` knobs are well-thought-out. Lost a point for the deferred-tool loading mechanism (extra step) and for occasionally verbose JSON output (could use a `format=markdown` toggle on `query_codebase`). |
| **Architectural Value** | **5/5** | `analyze_repo` is a category-defining tool. Nine sections, all useful, all sourced from the live graph. The snapshot history table embedded in the analysis output is a particularly strong touch. |
| **Uniqueness** | **5/5** | I have not encountered another tool that combines: typed-edge AST graph + vector search + cross-module sym-stub resolution + temporal snapshots + concern-based ranking + MCP exposure. Each piece exists individually; the integration is the value. |

**Weighted average: 4.6 / 5.**

---

## 4. Comparison to Default Workflow

| Question | Default (Grep + Read) | PyCodeKG | Winner |
|----------|----------------------|----------|--------|
| "What's this codebase?" | Glob + Read top README + Read 5–10 files (~10 calls, ~25k tokens) | `graph_stats()` + `analyze_repo()` (2 calls, ~8k tokens) | **PyCodeKG, by ~5×** |
| "Find the SQLite store" | Grep "sqlite" → grep "GraphStore" → Read store.py | `query_codebase("graph database storage")` → first result is `GraphStore` | **PyCodeKG** |
| "Who calls `_get_kg`?" | Grep "_get_kg(" — but you'd miss aliased imports | `callers("fn:.../mcp_server.py:_get_kg")` — finds 15, including stub-resolved | **PyCodeKG, decisively** |
| "What's the architectural spine?" | Read every module + guess | `centrality(group_by="module")` returns ranked list with scores | **PyCodeKG** |
| "What changed since v0.12?" | git log + git diff | `snapshot_diff(key_a, key_b)` returns per-module node delta | **PyCodeKG for graph-shape changes; git for code-line changes** |
| Pinpoint a specific bug at line 247 | Read file:247 | `pack_snippets()` (ok but verbose for 1 line) | **Default** |

PyCodeKG **changes my approach** in three concrete ways:
1. I now lead with `graph_stats()` + `analyze_repo()` instead of Glob + README.
2. I use `callers()` instead of grepping for function names.
3. I use `pack_snippets()` to seed analysis context before I touch any file directly.

I still fall back to `Read` for line-level edits and `Grep` for non-Python text (config files, markdown). Those are not PyCodeKG's job.

---

## 5. Strengths

1. **`analyze_repo()` is a hero tool.** One call, nine architectural perspectives, includes embedded snapshot history. This alone justifies installing PyCodeKG.
2. **Sym-stub resolution is the differentiator.** `callers()` works correctly across import aliases; this is the thing grep fundamentally cannot do.
3. **Explainable relevance scoring.** Each result carries `semantic`, `lexical`, `docstring_signal`, `hop`, `via_seed` components. I can see *why* a node ranked.
4. **Temporal snapshots.** The `freshness` indicator on every snapshot (telling you how stale it is vs the live DB) is the kind of thoughtful detail that reveals a tool author who actually uses their own product.
5. **Tunable precision.** `min_score`, `paths`, `max_per_module`, `rerank_mode` are practical, well-documented controls — not a black box.
6. **Self-indexing as documentation.** The fact that PyCodeKG indexes itself and its module docstrings explicitly describe the tool surface (e.g., the `mcp_server.py` module docstring lists every tool) means semantic search converges quickly on the right answer.

---

## 6. Weaknesses & Suggestions

1. **`framework_nodes()` surfaces trivial methods.** `GraphStore.close` and `KGModule.close` outranked the actual hub modules. **Suggestion:** filter out `__init__`, `__exit__`, `close`, and other boilerplate from the ranking, or weight by node body size / cyclomatic complexity.
2. **`analyze_repo()` "Code Quality Issues" is too thin.** The current implementation flagged 1 issue (high fan-out on `init()`) but missed obvious targets like the 1336-line `app.py` and the 958-node `pycodekg_thorough_analysis.py`. **Suggestion:** add module-size / per-module node-count thresholds to the issues section.
3. **Relevance scores plateau low.** Top semantic scores rarely cross 0.71 even on perfect-match queries. This makes `min_score` thresholding tricky to tune across queries. **Suggestion:** apply per-query score normalization so top hits land near 1.0.
4. **JSON-vs-Markdown inconsistency.** `query_codebase` returns JSON, `pack_snippets` returns Markdown, `centrality` returns Markdown. Predictable from docs, but a `format=` parameter would let agents standardize.
5. **`explain()` "Role in Codebase" line is generic.** Almost always says "Utility function: Called N times. Specific to particular use cases." **Suggestion:** synthesize role from the actual caller modules (e.g., "MCP-tool helper: called by 14 of 15 MCP tool entry points").
6. **No `find_definition_at(file, line)` tool.** When I'm reading a file in the IDE and want to understand a symbol, I have to translate to `<kind>:<module>:<qualname>` myself. A reverse-resolve from `(file, lineno)` would close that loop.

---

## 7. Overall Verdict

**Recommend: yes, strongly. Final rating: 4.5 / 5.**

**Best use cases:**
- **Cold start on an unfamiliar Python codebase.** `analyze_repo()` + `centrality()` + targeted `pack_snippets()` will get you to a working mental model faster than any other tool I've used.
- **Refactoring planning.** `callers()` + `framework_nodes()` + `bridge_centrality()` give you the blast-radius information you need before touching a hub.
- **Code review at the architectural level.** Snapshot diffs let you see what shape *the graph* took on, not just what lines changed.
- **Agent-driven exploration.** This is purpose-built for LLMs — the explainable scores and Markdown-formatted output read like they were designed for prompt context.

**Less suited for:**
- Single-file or single-line edits (just `Read` + `Edit`).
- Non-Python codebases (out of scope, though `KGModule` looks designed for extension).
- Codebases where the docstrings are sparse or misleading — the embedding seeds rely on them.

PyCodeKG is the kind of tool where, after using it, going back to grep-only feels like working without an index. That is the highest praise I can give a developer tool.

---

*Assessment generated 2026-04-20 by Claude Opus 4.7 working through `assessments/AssessmentProtocol_PyCodeKG.md`. Every claim above was generated from live MCP tool output during this session.*
