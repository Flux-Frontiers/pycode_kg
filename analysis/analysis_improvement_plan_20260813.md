# Improvement Plan — from the 2026-08-13 Thorough-Analysis Run

**Source report:** `analysis/pycode_kg_analysis_20260813.md` (commit 85f65a2, grade C / 67)
**Prior run:** 2026-08-12 (commit 7d505d1, grade B / 82)
**Status:** plan only — no changes made.

---

## Reading the grade drop correctly

The B → C swing is **not code decay**. Score arithmetic for the 0813 run:

| Component | Points | Why |
| :--- | ---: | :--- |
| Docstring coverage (92.4% ≥ 80%) | 40 / 40 | unchanged |
| Orphaned functions (31 found) | **0 / 25** | was 15/25 on 0812 (≤2 found) |
| High fan-out (1: `cmd_init.init`) | 12 / 20 | unchanged |
| Circular deps (0) | 15 / 15 | unchanged |
| **Total** | **67** | |

The entire 15-point drop is the orphan bucket, and the orphan count exploded
because `_analyze_dependencies` now scans **every** node instead of a semantic
sample (the right change — the old sample systematically missed dead code).
The exhaustive scan exposed that `_is_special_entry_point` is too weak for it:
**~26 of the 31 reported orphans are false positives.** Verified classes:

| Class of false positive | Members (of the 31) | Evidence |
| :--- | :--- | :--- |
| `ast.NodeVisitor` dispatch | `visit_Module`, `visit_ClassDef`, `visit_FunctionDef`, `visit_AsyncFunctionDef`, `visit_Assign`, `visit_Call`, `visit_Attribute` | `PyCodeKGVisitor(ast.NodeVisitor)` — dispatched via `getattr` in `ast.NodeVisitor.visit` |
| KGModule SDK protocol overrides | `make_extractor` ×2, `_post_build_hook` ×2, `analyze` ×2, `edge_kinds`, `node_kinds`, `meaningful_node_kinds`, `graph`, `KGModule` | invoked by `kg_utils.pipeline` (external package — callers invisible to the graph) |
| Base classes used only via INHERITS | `KGModule` | orphan check counts CALLS + ATTR_ACCESS but not INHERITS |
| `__main__`-guarded entry points | `main` (app.py), `main` (cli_rank.py) | both modules end in `if __name__ == "__main__": main()` — module-scope calls produce no CALLS edge |
| Test-only / public-API helpers | `with_alpha`, `rel_color`, `color_for`, `shape_for`, `_kind_priority`, `_resolve_kind`, … | graph indexes `include = ["src"]` only, so anything called solely from `tests/` (or by downstream fleet repos) has zero visible callers — e.g. `with_alpha` has 5 dedicated tests |

Remaining **genuine** dead-code candidates (~5): `rerank_hybrid`
(`analysis/hybrid_rank.py` — likely superseded by `ranking/coderank.rank_query_hybrid`),
`_analyze_coderank_section` (superseded by `_compute_coderank`), `_compute_delta`,
`Snippet`, `_line_range`. Each needs individual triage in Phase 4 — **after**
Phase 1, so the triage list is trustworthy.

> ⚠️ Do **not** act on the report's "Immediate Action: remove or archive orphaned
> functions" as written — deleting `visit_*` would break the visitor entirely.

---

## Phase 1 — Fix orphan-detection false positives

**Priority: highest · Complexity: medium · Blocks: Phase 4**

The exhaustive scan is correct; the exclusion logic must catch up. All changes
in `_is_special_entry_point` / `_analyze_dependencies`:

1. **NodeVisitor dispatch** — exclude `visit_*` methods on classes whose
   INHERITS chain reaches `ast.NodeVisitor`. The graph already stores INHERITS
   edges; fall back to a name-pattern check (`visit_[A-Z]`) if the base is
   external and unresolvable.
2. **Count INHERITS as usage** — a class with incoming INHERITS edges is not
   orphaned (fixes `KGModule`).
3. **Protocol overrides of external bases** — if a method's class inherits
   from a base outside the graph and the method overrides a base attribute
   (`hasattr` on the imported base, or a maintained interface list for
   `kg_utils.KGModule` / `KGExtractor`), exclude it. Covers `make_extractor`,
   `analyze`, `edge_kinds`, `node_kinds`, `meaningful_node_kinds`,
   `_post_build_hook`, `graph`, `kind`.
4. **`__main__` entry points** — exclude module-level `main()` when the module
   has an `if __name__ == "__main__"` guard (cheap source check), and exclude
   any function named as a `[project.scripts]` target in pyproject.
5. **Property methods, generally** — replace the hardcoded
   `property_names = {"key"}` with a decorator check; the visitor sees
   `@property` at parse time and could stamp it on the node.
6. **Test-only usage** — the graph indexes `src` only, so test-covered helpers
   look dead. Cheapest fix that avoids polluting the graph: at report time,
   grep `tests/` for the orphan's name and split the table into
   **"dead (no callers anywhere)"** vs **"prod-orphaned but test-covered
   (possible public API)"**. Only the first bucket should count against the
   grade; the second is a judgment list, since fleet repos consume this
   package's API invisibly.

**Verify:** rerun the analysis; expected orphan count 31 → ≤5, every survivor
manually confirmed as a real candidate. Add regression tests pinning each
exclusion class (a NodeVisitor fixture, an external-base override fixture, a
`__main__` module fixture).

## Phase 2 — Make the grade stable and explainable

**Priority: high · Complexity: low**

1. **Smooth the cliffs.** Every bucket is a step function (orphans 0/15/25;
   docstrings 0/20/40), so one boundary crossing moves the grade a full letter.
   Interpolate linearly, and normalize orphans as a *percentage of meaningful
   definitions* (31/383 ≈ 8%) instead of an absolute count so the score doesn't
   punish repo growth.
2. **Print the subscore breakdown** in the Executive Summary (the four
   components as a table). A B→C swing should be self-explaining from the
   report alone — this run's wasn't.
3. **Record the grade in snapshots** so the Snapshot History table can show a
   grade trend column alongside Δ nodes/edges/coverage.

**Verify:** re-grade both the 0812 and 0813 graphs with the new curve; the two
runs should land within a few points of each other once Phase 1 lands.

## Phase 3 — Report-quality fixes

**Priority: medium · Complexity: low each**

1. **Dedupe and qualify the WARN line** — the orphan insight lists bare names
   with duplicates (`main`, `main`, `analyze`, `analyze`…); module-qualify and
   collapse.
2. **Label truncation** — "Orphaned Code" shows 15 rows under a count of 31
   with no "top 15 of 31" note; same audit for every top-N table (fan-in shows
   14, CodeRank 20).
3. **Call-chain resolution bug (CONFIRMED, mitigated in Phase 3)** — the chain
   `from_dict → _rewrap → update → _run_pipeline → _banner` came from the
   graph build resolving `snap.__dict__.update(...)` to the `update()` Click
   command in `cmd_build_full.py`. Verified in the DB: **every** dotted attr
   call ending in `update` (`visited.update`, `rel_weights.update`,
   `priors.update`, …) carries a RESOLVES_TO edge onto that Click command —
   last-segment name matching with no receiver-type awareness. The chain
   walker now skips dotted sym: stubs ending in builtin container/str method
   names, and chain steps are module-qualified in the report.

   **Backlog (builder-side, needs reindex):** the RESOLVES_TO pass itself
   should not resolve attr calls whose receiver is clearly not a module
   (builtin-method names, `self.x.y` chains) onto bare same-named repo
   functions. This pollutes CALLS-derived analytics beyond chains: fan-in and
   CodeRank both count these edges. Fix belongs in the visitor/store
   resolution pass, with a rebuilt index to verify.
4. **Cohesion table context** — `mcp_server.py`, `app.py`, `viz3d.py` score
   0.00 cohesion because their callers are external frameworks (MCP router,
   Streamlit, Qt). Mark entry-point modules as such instead of letting them
   read as the worst-coupled modules in the repo.
5. **Collapse no-change snapshot rows** — 8 of 10 history rows are `+0 +0
   +0.0%`; show changed rows plus a "n unchanged snapshots elided" line.

## Phase 4 — Genuine code improvements the report surfaced

**Priority: medium · Complexity: varies · Depends on: Phase 1**

1. **Dead-code triage** (small, after Phase 1 confirms the list):
   `rerank_hybrid`, `cli_rank.main` (vs the `cmd_centrality` path),
   `_analyze_coderank_section`, `_compute_delta`, `Snippet`, `_line_range` —
   verify each against fleet usage, then delete or wire in. One commit per
   decision, changelog notes for anything public.
2. **Split `cmd_init.init()`** (fan-out 43 — the one real orchestrator
   finding): extract phase helpers (scaffold, MCP config writes, hook install,
   build) so each is testable; behavior-preserving, verified by existing init
   tests plus new per-phase ones.
3. **Finish the `thorough_analysis` split** (2,574 lines, 40 defs — already in
   flight): `render.py` now owns `md_table`; continue by moving the remaining
   rendering (`to_markdown`, `_sym`, `_bar`, `_snapshot_row`, section
   emitters) into the render layer so `pycodekg_thorough_analysis.py` keeps
   only analysis phases. Target: analyzer computes dataclasses, renderer
   formats them — testable independently.
4. **Split `viz3d.py`** (51 defs): `KGVisualizer` (data/scene model),
   `MainWindow` (Qt shell), `DocstringPopup` + pickers (interaction) into a
   `viz3d/` package, following the precedent of moving `layout3d` into the
   SDK. Lowest priority — GUI code, low churn, and the lazy-import discipline
   must survive the split.

---

## Suggested sequencing

```
Phase 1 (orphan exclusions)  ──►  Phase 4.1 (dead-code triage)
Phase 2 (grade curve)        ──►  re-baseline grade, then compare runs meaningfully
Phase 3 (report polish)      ──►  independent, any time
Phase 4.2–4.4 (refactors)    ──►  independent, as capacity allows
```

The next analysis run after Phases 1–2 is the real baseline; today's C/67 and
yesterday's B/82 are both artifacts of the detector transition and shouldn't
drive refactoring decisions on their own.
