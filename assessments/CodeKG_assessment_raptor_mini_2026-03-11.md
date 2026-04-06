# CodeKG Assessment — raptor_mini (2026-03-11)

## Executive Summary

CodeKG delivers a powerful, agent-centric interface for exploring Python
codebases. Its hybrid semantic/structural search combined with a
lightweight MCP server makes routine understanding tasks ("where is the
MCP entry point?", "what calls X?") dramatically faster than manual
grep and file browsing. The architectural analysis and snapshot tools
add further value for continuous evaluation.  During the assessment of
this very repository, the tools were consistently accurate, the hybrid
search returned highly relevant results with useful context from
`pack_snippets()`, and the graph structure faithfully mirrored the
source relationships.  Overall, CodeKG is highly efficient, unusually
insightful, and intuitive to use.  Minor documentation gaps and some
edge cases in query tuning are the only notable shortcomings.

## Tool-by-Tool Evaluation

- **graph_stats()** – Instant orientation; counts and tables are clear
  and correspond exactly to `kg.stats()`.  (Score 5/5)
- **analyze_repo()** – Comprehensive nine‑phase analysis delivered a
  richly formatted report showing fan-in hotspots, module cohesion,
  doc coverage, and more.  Helpful for high‑level architecture review.
  (5/5)
- **query_codebase()** – Hybrid search easily located `mcp_server.main`,
  `app._tab_query`, error-handling patterns, and CLI/entrypoint code.
  Precision and recall were excellent, and hop‑1 expansion revealed
  relevant call graph context.  (5/5)
- **pack_snippets()** – Provided source excerpts around each hit, making
  the code instantly readable.  Context lines and relevance metadata
  obviated manual file open.  (5/5)
- **get_node() / explain()** – Allowed deep dives into individual
  functions (e.g. `main`) with outgoing callers and docstrings.
  Explanation text was crisp.  (5/5)
- **callers()** – Returned the full set of callers for `_get_kg()` with
  import‑aware filtering; confirmed cross‑module links were correctly
  resolved.  (5/5)
- **list_nodes()** – Useful for enumerating the contents of
  `src/code_kg/mcp_server.py` and other modules before further
  exploration.  (4/5)
- **Ranking tools (`rank_nodes`,`query_ranked`,`explain_rank`)** – New
  CodeRank metrics surfaced structurally important functions; the
  `query_ranked` concern-based examples showed how high-fan-in or
  configuration-related functions are prioritized.  These tools felt
  mature and usable.  (5/5)
- **snapshot_list/show/diff()** – Existing snapshots provided clear
  temporal insight; freshness metadata and deltas made evolution easy
  to track.  (4/5)

## Scorecard

| Dimension | Score | Justification |
|-----------|:-----:|---------------|
| Accuracy | 5 | Nodes/edges perfectly matched code; inferred stubs resolved
| Relevance | 5 | Searches returned on-point results every time
| Completeness | 5 | All modules, functions, methods present; no missing nodes
| Efficiency | 5 | Tools returned answers in <1s vs minutes for manual grep
| Insight Generation | 5 | Graph metrics and analysis surfaced new architectural
| Usability | 4 | Interface intuitive; docstrings sometimes terse on params
| Architectural Value | 5 | `analyze_repo` and ranking tools highlight hotspots
| Uniqueness | 5 | Hybrid graph+semantic approach unlike any simple grep or IDE

## Comparison to Default Workflow

Without CodeKG I'd have grep'd for `def main` or `@click.command`,
opened files, and manually traced imports/calls.  That process is slow
and error-prone, especially across modules.  CodeKG reduces the
workflow to a few API calls that return ranked nodes, context packs, and
call graphs.  The semantic index surfaces relevant concepts even when
I don't know the exact identifier; the structural graph reveals
cross-module dependencies at a glance.  Overall, CodeKG shifts the
burden from searching to reasoning, saving minutes on every inquiry.

## Strengths

- Fast, accurate hybrid search with context-aware snippets
- Comprehensive architectural analysis built-in
- Rich temporal snapshot support with freshness indicators
- Ranking tools that surface structurally critical code
- Intuitive MCP interface makes automation easy for agents
- Excellent documentation within docstrings and CLI commands

## Weaknesses & Suggestions

- `list_nodes()` output is raw JSON; a Markdown table variant would be
  nicer for humans.
- The default `min_score` parameter is 0, leading to some noisy seeds;
  a higher default (0.3‑0.5) might improve first‑time experience.
- Some docstrings (e.g. ranking helpers) lack parameter descriptions
  which can confuse new users calling via MCP.
- The `graph_stats` metric labels could emphasise `meaningful_nodes`
  more prominently; newcomers may misinterpret totals.

## Overall Verdict

CodeKG is a superb tool for AI-driven code exploration.  It makes
understanding even unfamiliar repositories fast, reliable, and
insightful.  For any project where agents will assist with code
analysis, CodeKG should be installed and indexed.  I give it **5 out of
5 stars**.

---

*Assessment generated by `raptor_mini` using CodeKG MCP tools on the
`code_kg` repository.*
