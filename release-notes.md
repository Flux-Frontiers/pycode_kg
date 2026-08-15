# Release Notes — v0.22.1

> Released: 2026-08-14

This release makes `pycodekg analyze` trustworthy. The thorough-analysis report previously mixed real findings with artifacts of its own sampling and resolution quirks — dead code it merely failed to see, "orchestrators" that were ordinary CLI commands, and a deep call chain that never existed. All of that is fixed, and the quality grade now moves smoothly instead of jumping a letter at a threshold.

## What changed

**Orphan detection is exhaustive and accurate.** The dead-code phase now scans every function, method, and class via SQL instead of seeding from a semantic query, then excludes real framework dispatch it used to miss: `ast.NodeVisitor` `visit_*` methods, SDK protocol overrides, `[project.scripts]` targets, `__main__`-guard calls, property decorators, and bare-name callback references. Definitions that are unused in production but exercised by tests are reported separately as likely public API rather than counted as dead code.

**The quality grade is a continuous curve.** Every scoring component was a step function, so a single boundary crossing could swing the grade a full letter between runs a day apart. Scores are now linear, a per-component breakdown prints under the Executive Summary (and in the JSON export), and one extra finding shifts points, never a letter.

**Phantom callers are gone from the graph.** Name-fallback resolution matched `sym:` stubs by bare last segment, so builtin container-method calls like `visited.update(...)` gained RESOLVES_TO edges onto any repo function sharing the name — polluting fan-in, CodeRank, and call chains. The new `pycode_kg.resolution` module prunes these lookalikes at every build site.

**Report rendering has its own module.** The ~550 lines of Markdown section emitters moved from the analyzer into `pycode_kg.report`, alongside the shared `pycode_kg.render` table primitives. `PyCodeKGAnalyzer.to_markdown()` and the MCP `analyze_repo` tool keep their APIs.

**Housekeeping.** The dead `pycode_kg.analysis.hybrid_rank` module is deleted (found by the new scan, fittingly). A direct starlette constraint prevents a double-locked version from silently corrupting the virtualenv. The optional `kg` group now requires doc-kg ≥0.21.2.

## Upgrading

No API changes — `kg.analyze()`, the CLI, and all MCP tools keep their signatures. To get the benefit of resolution pruning, rebuild your knowledge graph (`pycodekg build`); existing graphs retain any phantom RESOLVES_TO edges until rebuilt. If you imported `pycode_kg.analysis.hybrid_rank` (nothing in the fleet did), switch to `pycode_kg.ranking.coderank.rank_query_hybrid`.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
