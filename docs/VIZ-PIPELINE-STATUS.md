# Interactive KG Visualization — Repo State & Next Steps

Companion to [`INTERACTIVE-KG-VIZ-PLAN.md`](./INTERACTIVE-KG-VIZ-PLAN.md).
That document is the analysis and the options; this one is where things stand and
what happens next.

Working branch across the fleet: **`claude/knowledge-graph-viz-pipeline-qvt5ui`**

---

## 1. What has actually happened so far

Two things, and it is worth being clear that only one of them is progress on the
visualization work:

1. **A survey and a proposal.** All six repos' viz layers were mapped, the
   techniques from the source article were reconstructed from `d3graph` /
   `d3blocks` documentation and source, and the result is written up as an
   analysis with three options and a phasing proposal.
2. **Incidental defect cleanup.** The survey turned up seven unrelated defects.
   Six are fixed and pushed; one needs a decision (§4).
3. **Phase 0 is implemented in pycode_kg** (§6.1) — persisted centrality now
   reaches both renderers, and the three divergent kind→colour maps are gone.
   Phases 1 onward are still unstarted, and no stand-alone HTML exporter
   exists yet.

---

## 2. Repo state

All six repos are on the working branch with clean working trees.

| Repo | Ahead of `main` | Contents | Risk |
|---|---|---|---|
| **pycode_kg** | 5 commits | Plan + status docs; the dependency and doc fixes (`networkx>=3.0`, streamlit floor `>=1.56.0`, `cake`→`funnel`); and **Phase 0** — `theme.py`, `analysis/scores.py`, centrality wired into both renderers, 61 new tests | medium — Phase 0 changes what both viewers look like |
| **metabo_kg** | 1 commit | `tempfile` fix in `_build_pyvis`; streamlit floor `>=1.56.0`; remove dead `_golden_spiral_2d` alias | low — only touches untested viz code; both layouts smoke-tested after |
| **doc_kg** | 1 commit | Drop unused `plotly` from `viz` and `all` extras | very low — confirmed zero references repo-wide |
| **KG_utils** | — | untouched | — |
| **gutenberg_kg** | — | untouched | — |
| **KGRAG** | — | untouched | — |

`poetry.lock` was regenerated in all three changed repos, since CI runs
`poetry install` and fails against a stale lock. Streamlit resolves to 1.59.0.

### Verification performed

- `ruff format --check .` and `ruff check .` clean across the repo.
- `ty check src/` clean (the CI type-check job).
- **353 tests pass**, including 61 new ones for `theme` and `analysis.scores`.
  The 6 failures in the local run are missing optional dependencies (`scipy`,
  `sqlite-vec`) and reproduce identically on stashed, pre-change code — they are
  environmental, not regressions.
- `metabo_kg.layout3d` imported and both layouts confirmed to compute positions
  after the alias removal.
- Lockfiles confirmed to reflect the intended changes.

### Verification *not* performed

- **Nothing was rendered.** Neither `streamlit` nor `pyvista`/`PyQt5` is
  installable in this environment, so `app.py` and `viz3d.py` were checked by
  lint, type-check and compile only — no visual confirmation that centrality
  sizing looks right. The pure logic behind it (`theme`, `analysis.scores`) is
  covered by tests; the wiring is not.
- **No graph was built**, so the metric selectors were never exercised against a
  real `centrality_scores` table.
- The `st.iframe` version fix is reasoned from the release notes, not observed.

---

## 3. Correction on the record

The first survey pass reported that `st.iframe` "does not exist" and that the 2D
graph render was broken in two repos. **That was wrong.** `st.iframe` is a real
top-level Streamlit API added in **1.56.0** (2026-03-31), and its first parameter
accepts a raw HTML string, so the existing calls are correct usage.

The genuine defect was the declared floor — `streamlit>=1.35.0` permitted
resolutions where the attribute does not exist. That is what was fixed.

Two independent surveys reached the same confident wrong conclusion, because the
API postdates their training data. Any future claim of the form "this API does
not exist" should be checked against release notes before acting on it.

---

## 4. The one open defect

**`seed_ids` in `pycode_kg/app.py` (lines 249, 306, 318, 331).**

Seed highlighting — a gold border on nodes that came from the vector search — is
fully implemented and no caller passes the parameter. It cannot be wired up as
things stand: `QueryResult.seeds` (`kg_utils/specs.py:120`) is an `int` count, not
a collection of node IDs, so the information does not survive the query path.

Three ways out, in order of preference:

1. **Add seed IDs to `QueryResult`** in KG_utils and populate them in
   `KGModule.query`. Makes the feature live and is likely useful beyond the
   viewer, but it is a change to the shared SDK contract that every consumer
   inherits.
2. **Leave it.** Harmless, documented, and awaiting the data. Costs nothing.
3. **Delete it.** Removes ~4 lines of working feature code and loses the intent.

This needs a decision rather than a unilateral edit, which is why it is still
open.

---

## 5. Next steps

Phase 0 is done (§6). Nothing below it has started, and the first
decision gates everything after it.

### 5.1 Decisions needed before implementation

| # | Decision | Why it blocks |
|---|---|---|
| 1 | **Option B (depend on `d3graph`) or Option C (own the D3 template)?** | Determines the shape of the whole exporter. B is far faster to a demo; C is the only route to collapse/expand, which our graph sizes arguably make mandatory. |
| 2 | **pycode_kg or doc_kg as the pilot?** | pycode_kg has centrality already persisted and is the cheapest plumbing. doc_kg has cosine-weighted edges, which is the only graph in the fleet where the threshold slider is *natively* meaningful. Plumbing vs. idea. |
| 3 | **Is a stand-alone HTML artifact the goal**, or a better Streamlit experience? | The article's entire premise is the former; almost all our existing investment is in the latter. |
| 4 | **`seed_ids` / `QueryResult`** (§4) | Small, but it is an SDK contract change. |

### 5.2 Phase 0 — **delivered**, see §6

### 5.3 Phase 1 — enabling work, needed by both B and C

- Add `weight REAL NOT NULL DEFAULT 1.0` to the `edges` table and persist
  `EdgeSpec.weight`, which is currently declared and silently dropped.
- Stop discarding the `SIMILAR_TO` cosine in `doc_kg/kg.py:770-773` — the best
  natural slider input in the fleet.
- Add a `REL_WEIGHTS` fallback so weight is derivable without a rebuild.
- New `kg_utils/analysis/community.py` (Louvain); promote centrality out of
  pycode_kg into `kg_utils/analysis/`.
- Needs a store migration test and a backward-compatibility test against an
  existing `graph.sqlite`.

Phases 2–5 are in the plan and depend on the decisions above.

### 5.4 Hygiene worth doing whenever

- Confirm the three pushed branches go green in CI — the test suites were not run
  locally (§2).
- Collapse the `layout3d.py` fork: pycode_kg (486 LOC) and metabo_kg (460 LOC)
  differ by ~222 lines, almost entirely domain vocabulary.
- `metabo_kg` and `KGRAG` still declare `kgmodule-utils>=0.4.4` while the rest of
  the fleet is on `>=0.6.2`.

---

## 6. Phase 0 — delivered

Persisted centrality now reaches both renderers. Nothing else in the plan has
started.

### 6.1 What was added

| Module | Role |
|---|---|
| `src/pycode_kg/theme.py` | The shared visual vocabulary — kind→colour/shape/size, relation colours, Z levels, `resolve_kind`, `with_alpha`. Replaces three divergent copies. |
| `src/pycode_kg/analysis/scores.py` | Reads `centrality_scores` / `node_metrics` back out of SQLite. `available_metrics`, `load_scores`, and a `ScoreSet` exposing raw score, dense rank, percentile and range scaling. |

Wired into `app.py` (2-D), `viz3d.py` (3-D) and `layout3d.py` (constants only).

### 6.2 What changed on screen

- **2-D explorer** — a **Centrality** sidebar section. Node diameter encodes the
  metric (log-scaled, 8–42 px) and opacity encodes rank percentile, floored at
  0.35 so nothing becomes invisible. Tooltips gained a rank line.
- **3-D viewer** — a **Size Nodes By** dropdown. Node radius encodes the metric
  (log-scaled, 0.35–2.4 world units).
- **Both** — one palette. The 3-D viewer's class/function/method colours changed
  to match the 2-D explorer, which is what its own comment always claimed. 2-D
  now distinguishes `private_function` in yellow, as 3-D already did.

### 6.3 Decisions worth knowing about

- **Log scaling is the default.** PageRank-family scores are power-law
  distributed; under a linear map nearly every node sits at the minimum size.
  `"linear"` and `"rank"` scalers exist for callers that want them.
- **Ranks are derived on load, not read from the `rank` column.** The stored rank
  reflects whatever set the writer ranked, which may have been truncated.
  Deriving guarantees dense ranks over exactly the rows loaded, and makes
  `node_metrics` (which has no rank column) behave identically. This removes the
  "add a rank column to `node_metrics`" task the plan listed in §3.6.
- **Absence is normal, not an error.** Neither metric table is part of the base
  schema, so a graph built but never analysed simply gets uniform sizing and a
  hint to run `pycodekg analyze`.
- **`layout3d.py` now imports `pycode_kg.theme`**, so it is no longer
  dependency-free. In practice it is only ever loaded through `viz3d.py`, which
  already imports the package — but the standalone-import property the survey
  praised is genuinely gone. Consistency was judged the better trade; the theme
  tests assert the maps stay aligned.

### 6.4 Not done

- `seed_ids` remains unwired (§4) — untouched by this work.
- No stand-alone HTML export, no edge weights, no community detection. Those are
  Phases 1–3 and depend on the decisions in §5.1.
