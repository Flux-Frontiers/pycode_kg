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
   analysis with three options and a phasing proposal. **No visualization code
   has been written.**
2. **Incidental defect cleanup.** The survey turned up seven unrelated defects.
   Six are fixed and pushed; one needs a decision (§4).

---

## 2. Repo state

All six repos are on the working branch with clean working trees.

| Repo | Ahead of `main` | Contents | Risk |
|---|---|---|---|
| **pycode_kg** | 3 commits | The plan document (§1 of this file), plus: declare `networkx>=3.0`; raise streamlit floor to `>=1.56.0`; correct the stale `cake`→`funnel` layout name in two architecture docs | low — one real dependency addition, rest is docs/metadata |
| **metabo_kg** | 1 commit | `tempfile` fix in `_build_pyvis`; streamlit floor `>=1.56.0`; remove dead `_golden_spiral_2d` alias | low — only touches untested viz code; both layouts smoke-tested after |
| **doc_kg** | 1 commit | Drop unused `plotly` from `viz` and `all` extras | very low — confirmed zero references repo-wide |
| **KG_utils** | — | untouched | — |
| **gutenberg_kg** | — | untouched | — |
| **KGRAG** | — | untouched | — |

`poetry.lock` was regenerated in all three changed repos, since CI runs
`poetry install` and fails against a stale lock. Streamlit resolves to 1.59.0.

### Verification performed

- `ruff check` and `ruff format --check` pass on every changed Python file.
- `python -m py_compile` passes on the changed modules.
- `metabo_kg.layout3d` imported and both `AlliumLayout` and `LayerCakeLayout`
  confirmed to compute positions after the alias removal.
- Lockfiles confirmed to reflect the intended changes (`networkx` present in
  pycode_kg, `plotly` absent from doc_kg, streamlit ≥1.56 in both).

### Verification *not* performed

- **Full test suites were not run.** The changed code (`app.py`, `layout3d.py`)
  has no test coverage in either repo, and installing those dependency trees
  (scipy, cobra, torch) is expensive. This should be confirmed in CI before merge.
- **Nothing was rendered.** No Streamlit app was launched; the `st.iframe`
  version fix is reasoned from the release notes and API docs, not observed.

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

Nothing below is started. The first decision gates everything after it.

### 5.1 Decisions needed before implementation

| # | Decision | Why it blocks |
|---|---|---|
| 1 | **Option B (depend on `d3graph`) or Option C (own the D3 template)?** | Determines the shape of the whole exporter. B is far faster to a demo; C is the only route to collapse/expand, which our graph sizes arguably make mandatory. |
| 2 | **pycode_kg or doc_kg as the pilot?** | pycode_kg has centrality already persisted and is the cheapest plumbing. doc_kg has cosine-weighted edges, which is the only graph in the fleet where the threshold slider is *natively* meaningful. Plumbing vs. idea. |
| 3 | **Is a stand-alone HTML artifact the goal**, or a better Streamlit experience? | The article's entire premise is the former; almost all our existing investment is in the latter. |
| 4 | **`seed_ids` / `QueryResult`** (§4) | Small, but it is an SDK contract change. |

### 5.2 Phase 0 — ready to start regardless of the above

The one piece of work that is useful under *every* option, because it depends on
data we already compute and persist:

- Read `centrality_scores` / `node_metrics` and bind score → node size, rank
  percentile → opacity, in `app.py` and `viz3d.py`. Degrade to uniform when the
  tables are absent (they are created lazily by their writers, so absence is
  normal).
- Add a metric selector driven by the existing `metric` column — both tables are
  already long-format, which is exactly the shape a switcher needs.
- Extract a shared `theme.py`; the kind→colour map currently diverges three ways
  within pycode_kg alone.

This is pure wiring against existing data. No new dependencies, no schema change,
no rebuild. See §3.5–3.6 of the plan.

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
