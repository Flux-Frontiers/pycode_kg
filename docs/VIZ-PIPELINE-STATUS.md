# Interactive KG Visualization — Repo State & Next Steps

Companion to [`INTERACTIVE-KG-VIZ-PLAN.md`](./INTERACTIVE-KG-VIZ-PLAN.md).
That document is the analysis and the options; this one is where things stand and
what happens next.

Working branch across the fleet: **`claude/knowledge-graph-viz-pipeline-qvt5ui`**

---

## 1. What has actually happened so far

Four things. Only one of them is progress on the visualization work itself:

1. **A survey and a proposal.** All six repos' viz layers were mapped, the
   techniques from the source article were reconstructed from `d3graph` /
   `d3blocks` documentation and source, and the result is written up as an
   analysis with three options and a phasing proposal (see the plan document).
2. **Phase 0, in pycode_kg** (§6) — persisted centrality now reaches both
   renderers and the three divergent kind→colour maps are gone. Phases 1 onward
   are unstarted; there is still no stand-alone HTML exporter.
3. **Incidental defect cleanup** across three repos — seven defects found during
   the survey (§2.5 of the plan), plus three more found by rendering (§7) and one
   found by chasing test failures (§5.4).
4. **Two corrections to my own earlier claims** — the `st.iframe` diagnosis (§3)
   and the scaling diagnosis (§7.2). Both were confidently stated and wrong.

---

## 2. Repo state

All six repos are on the working branch with clean working trees.

| Repo | Ahead of `main` | Contents | Risk |
|---|---|---|---|
| **pycode_kg** | 11 commits | Plan + status docs; dependency and doc fixes (`networkx>=3.0`, streamlit floor `>=1.56.0`, `cake`→`funnel`, stale 3-D colour table); **Phase 0** (`theme.py`, `analysis/scores.py`, centrality in both renderers); pyvis `cdn_resources` fix; 3-D sizing regression fix | medium — Phase 0 changes what both viewers look like |
| **metabo_kg** | 3 commits | `tempfile` fix in `_build_pyvis`; streamlit floor `>=1.56.0`; dead `_golden_spiral_2d` alias removed; pyvis `cdn_resources` fix; **migrated off `kg-snapshot`** onto the shared `kg_utils.snapshots` | low |
| **doc_kg** | 3 commits | Unused `plotly` dropped; pyvis `cdn_resources` fix; **`scikit-learn` declared** as an `analysis` extra after five modules were found importing it undeclared (§5.4) | low |
| **KG_utils** | — | untouched | — |
| **gutenberg_kg** | — | untouched | — |
| **KGRAG** | — | untouched | — |

`poetry.lock` regenerated wherever `pyproject.toml` changed, since CI runs
`poetry install` and fails against a stale lock.

### Test state

All three changed repos are **fully green** locally, with every declared
dependency installed:

| Repo | Passing | Skipped | Failing |
|---|---|---|---|
| pycode_kg | 373 | 16 | 0 |
| doc_kg | 387 | 4 | 0 |
| metabo_kg | 188 | 0 | 0 |

Earlier revisions of this document reported failures in these suites. Every one
of them traced either to a declared dependency missing from the ad-hoc
virtualenvs used here (`scipy`, `sqlite-vec`, `sentence-transformers`,
`kg-snapshot`, `pymupdf4llm`) or to the one genuine declaration bug in §5.4. None
were regressions.

### Verification performed

- `ruff format --check .` and `ruff check .` clean in all three repos.
- `ty check src/` clean in pycode_kg (the CI type-check job).
- Both renderers exercised for real, headless, against a graph built from
  pycode_kg itself — 10,312 nodes / 10,654 edges with 883 SIR centrality scores
  computed and persisted:
  - **2-D** — Streamlit served headless, driven and screenshotted through the
    pre-installed Chromium via Playwright. The Centrality selector populates
    (`sir pagerank — 883 nodes`) and node size and opacity vary by metric.
  - **3-D** — `pyvista` off-screen under `xvfb-run` with
    `QT_QPA_PLATFORM=offscreen`, calling the real `create_kg_visualization`.
- **`st.iframe` confirmed empirically** on Streamlit 1.60.0 — it exists, and its
  docstring states it auto-detects URLs, file paths and HTML strings. The §3
  correction is observed, not inferred.
- Both sibling repos' pyvis output confirmed self-contained (~698 KB, no cdnjs
  reference, no relative asset path, nothing written to the working directory).
- `metabo_kg.layout3d` imported and both layouts confirmed to compute positions
  after the alias removal.

### Verification *not* performed

- No review of the 3-D viewer's *interactive* behaviour — picking, camera,
  docstring popups. Only still frames were captured.
- Nothing tested on a graph larger than pycode_kg's own (10,312 nodes). The
  fleet spans up to ~850k nodes.
- No CI run yet on any of the three branches.

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

### 5.4 Dependency hygiene — a recurring pattern

Three instances of the same failure mode have now surfaced on this branch:
a package is imported but declared nowhere, resolving only as a transitive
dependency of something else. Each works until the intermediary drops it.

| Repo | Package | Imported by | Resolved via | Status |
|---|---|---|---|---|
| pycode_kg | `networkx` | `ranking/coderank.py` | `torch` | fixed — declared |
| doc_kg | `scikit-learn` | 5 modules incl. `dockg.py` | `sentence-transformers` | fixed — `analysis` extra |
| gutenberg_kg | `matplotlib`, `numpy` | `viz3d.py` | `pyvista` | **attempted, reverted** — see below |

The gutenberg_kg import carried an inline comment (`# pyvista dependency, always
present`), so the reliance was acknowledged rather than accidental. The sweep also
found `numpy` imported at *module* scope in the same file and equally undeclared,
which is the more serious of the two — matplotlib is at least imported lazily.

**Declaring them was attempted and backed out.** Adding two lines to the `viz3d`
extra invalidates `poetry.lock`, and gutenberg_kg cannot re-lock in reasonable
time: two attempts ran to 15 and 50+ minutes of solid CPU without finishing.
This is a known characteristic of this repo, documented in its own CI —
`.github/workflows/docs.yml` notes that `runpod` "is deliberately in no extra —
its dep tree stalls poetry lock — so it installs via plain pip". Since CI runs
`poetry install` in three jobs, a stale lock breaks all of them, so the change
could not be landed without the regenerated lock.

Nothing is broken meanwhile: both packages resolve via pyvista exactly as they
did before. The edit is two lines in the `viz3d` extra plus a stale comment fix
at `viz3d.py:674`, and is worth redoing whenever someone can let a full
`poetry lock --regenerate` run to completion.

**The fleet-wide check has since been run** — every top-level import under each
repo's `src/`, compared against the distributions its `pyproject.toml` names:

| Repo | Undeclared third-party imports |
|---|---|
| **pycode_kg** | none |
| **KG_utils** | none |
| **metabo_kg** | `vtkmodules` (a hard dependency of `pyvista`, imported inside `viz3d.py`) |
| **doc_kg** | `joblib`, `torch`, `tqdm` — all transitively guaranteed by declared deps |
| **gutenberg_kg** | `numpy` (module scope) and `matplotlib` — **now declared**; plus ~12 optional-feature imports (`diffusers`, `mflux`, `spacy`, `openai`, sibling KGs) that are lazily imported behind guards |
| **KGRAG** | `httpx`, `huggingface_hub`, `llama_cpp`, `tomli`, plus sibling-KG adapters |

Two things the sweep clarified. `tomli` in `KGRAG/config.py` looks undeclared but
is a correctly guarded fallback for Python < 3.11 that can never fire, since the
project floor is 3.12 — harmless dead code, not a missing dependency. And the
bulk of gutenberg_kg's and KGRAG's hits are optional-feature imports behind
`try`/`except ImportError`, which is the intended pattern rather than a defect.

What remains genuinely worth attention is the KGRAG group — `httpx`,
`huggingface_hub` and `llama_cpp` are used by `app.py`, `model_coordinator.py`
and `_embedders.py`. Not fixed here; needs a look at whether each is guarded.

### 5.5 Hygiene worth doing whenever

- Confirm the three pushed branches go green in CI. The suites pass locally
  (§2), but CI installs via `poetry install --extras dev` rather than the ad-hoc
  virtualenvs used here, so the dependency sets differ.
- Collapse the `layout3d.py` fork: pycode_kg (486 LOC) and metabo_kg (460 LOC)
  differ by ~222 lines, almost entirely domain vocabulary.
- Check whether KGRAG's `httpx`, `huggingface_hub` and `llama_cpp` imports are
  guarded; they are undeclared and used outside adapter code.
- `doc_kg`'s `ManifoldAnalyzer.analyze()` wraps every sub-analysis in a broad
  `except Exception` and leaves failed fields at their zero defaults, so a caller
  cannot distinguish "intrinsic dimension is 0" from "the analysis failed". The
  missing-scikit-learn path that exposed this is fixed, but the silent-zeros
  behaviour itself remains — resolving it needs `ManifoldReport` to record which
  passes failed.

---

## 6. Phase 0 — delivered

Persisted centrality now reaches both renderers. Nothing else in the plan has
started.

### 6.1 What was added

| Module | Role |
|---|---|
| `src/pycode_kg/theme.py` | The shared visual vocabulary — kind→colour/shape/size, relation colours, Z levels, `resolve_kind`, `with_alpha`. Replaces three divergent copies. |
| `src/pycode_kg/analysis/scores.py` | Reads `centrality_scores` / `node_metrics` back out of SQLite. `available_metrics`, `load_scores`, and a `ScoreSet` exposing raw score, dense rank, percentile and range scaling. |

Wired into `app.py` (2-D), `viz3d.py` (3-D) and `layout3d.py` (constants only),
with 61 tests for `theme` and `analysis.scores`. Later work on this branch added
`tests/test_app_render.py` (9) and `tests/test_viz3d_sizing.py` (5), guarding the
fixes in §7.

### 6.2 What changed on screen

- **2-D explorer** — a **Centrality** sidebar section. Node diameter encodes the
  metric (log-scaled, 8–42 px) and opacity encodes rank percentile, floored at
  0.35 so nothing becomes invisible. Tooltips gained a rank line.
- **3-D viewer** — a **Size Nodes By** dropdown. Node radius is the per-kind
  radius multiplied by a log-scaled 0.6×–1.8× factor. (This began as an absolute
  0.35–2.4 range, which broke the layout; see §7.3.)
- **Both** — one palette. The 3-D viewer's class/function/method colours changed
  to match the 2-D explorer, which is what its own comment always claimed. 2-D
  now distinguishes `private_function` in yellow, as 3-D already did.

### 6.3 Decisions worth knowing about

- **Log scaling is the default — and measurement since suggests it should not
  be.** The reasoning was that PageRank-family scores are power-law distributed,
  so a linear map leaves nearly every node at the minimum size. That much is
  true, but log overcorrects: it puts the bulk at ~0.73 of the range instead, and
  is beaten by `rank` on discriminability and by `linear` on faithfulness. See
  §7.2 for the numbers and the recommendation. `"linear"` and `"rank"` already
  exist as options; only the default is in question.
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

---

## 7. What rendering revealed

### 7.1 The 2-D graph never rendered offline — fixed

pyvis defaults to `cdn_resources="local"`, which emits *relative* asset paths
(`lib/bindings/utils.js`, `../node_modules/vis/dist/vis.js`) alongside a cdnjs
fallback. Streamlit embeds the result in a `srcdoc` iframe, which has **no base
URL**, so the relative paths cannot resolve. The graph therefore rendered only
if `cdnjs.cloudflare.com` was reachable at view time, and failed silently with
`vis is not defined` when it was not — a blank panel, no error surfaced to the
user.

It had a second symptom: `cdn_resources="local"` also writes a `lib/` directory
(vis-network, tom-select, the bindings shim) into the **current working
directory** as a side effect of every render — the same class of problem as the
temp-file pollution fixed in metabo_kg.

Fixed by passing `cdn_resources="in_line"`, which inlines vis-network so the
page is genuinely self-contained (4 KB → ~700 KB, which is the point) and writes
nothing to disk. Guarded by `tests/test_app_render.py`.

This is a pre-existing bug, not a Phase 0 regression. It affected
`metabo_kg/app.py` and `doc_kg/app.py` identically — both constructed
`Network(...)` without `cdn_resources` — and **both are now fixed**, each with
the same five-test guard, including one asserting that rendering leaves the
working directory untouched.

It also matters for Phase 2: "self-contained HTML" is the entire premise of the
exporter, and this is exactly the trap it has to avoid.

### 7.2 The `log` default was the wrong scaler — fixed

Measured over the 150 nodes the graph browser displays, out of an 8–42 px range:

| scaler | p25 | median | p75 | IQR band |
|---|---|---|---|---|
| `linear` | 8 | 8 | 9 | **1 px** |
| `log` (current default) | 31 | 33 | 35 | **4 px** |
| `rank` | 28 | 31 | 36 | **8 px** |
| `rank`, rescaled to the visible subset | 16 | 25 | 34 | **17 px** |

**An earlier version of this section blamed the scale domain — global
normalisation applied to a filtered view — and proposed rescaling to the visible
subset as the fix. The measurements above show that was wrong.** Rescaling the
domain while keeping `log` moves the IQR band from 4 px to 4 px: no change at
all. The domain was never the variable that mattered.

The actual cause is the score distribution:

```
min 4.19e-04   median 5.10e-04   max 2.45e-02      max/min = 58x
```

The median is only **1.2× the minimum** while the maximum is **58×** it. Almost
every node is genuinely, equally peripheral and a handful are genuine hubs. Under
`log`, the single smallest value stretches the bottom of the range so far that
the entire bulk maps to ~0.73 of it — which is why the picture reads as
"everything is important".

That leaves a real judgement call, because the three scalers answer different
questions:

- **`linear`** is faithful to magnitude. The bulk collapses onto the floor and
  two or three hubs tower over it — which, for this distribution, is *true*. Its
  weakness is that mid-tier nodes (rank 10–100) are indistinguishable from rank
  800, and it is hostage to a single extreme value.
- **`log`** is the worst of both: it neither preserves magnitude faithfully nor
  maximises discriminability. It should not be the default.
- **`rank`** uses the full size range and is robust to outliers, at the cost of
  implying visual differences between scores that are nearly identical.

**Resolution: `rank` is now the default**, in `ScoreSet.scaled`. In a node-link
diagram size is a navigational affordance — "look here" — rather than a
measurement instrument; the true score and rank are one hover away in the 2-D
tooltip, so magnitude is not lost. `"log"` and `"linear"` remain available as
explicit arguments.

Measured effect on the 150 displayed nodes: interquartile band 4 px → 8 px, and
the 3-D radius multiplier now spans the full 0.60×–1.79× range. Re-rendered to
confirm the picture actually improved rather than just the statistic.

**Still not applied: local rescaling.** It doubles discrimination again
(8 px → 17 px) but only in combination with `rank`, and it costs cross-view
comparability — the same node changes size when the filter changes. Worth having
as an opt-in toggle; not worth making the default.

**Still not applied: exposing the scaler as a UI control.** The recommendation
included it, and it remains a sensible addition to both renderers' existing
metric selectors, but it is UI work rather than a default change.

### 7.3 The 3-D centrality sizing was actively harmful — fixed

Rendering complete module subtrees (rather than the arbitrary first-400-node
slice used initially) made it obvious that Phase 0's 3-D sizing broke the
visualisation. `CENTRALITY_SIZE_RANGE = (0.35, 2.4)` was an *absolute* radius
range replacing the per-kind size, so a max-centrality function rendered at 2.4
units against a base of 0.7 — and with log scaling putting the median high, most
nodes drew near the top of that range. Each allium head fused into a solid ball;
the stem and every CALLS arc inside it were occluded. The uniform-sizing render
of the same four modules was airy and readable by comparison.

Two distinct mistakes:

1. **Ignoring the layout's spatial budget.** 3-D node positions are fixed, so
   radius competes with the space the layout allotted. An allium head is only
   about `2 + sqrt(n_children) * 0.4` units across. (The 2-D renderer has no
   such constraint — force-directed layout pushes oversized nodes apart — which
   is why an absolute pixel range remains correct there.)
2. **Discarding the kind hierarchy**, letting a central method outgrow the
   module box that anchors its stem.

Replaced with `CENTRALITY_SCALE_RANGE = (0.6, 1.8)`, applied as a multiplier on
the per-kind radius. Guarded by `tests/test_viz3d_sizing.py`.

Worth stating plainly: this was a regression I introduced in Phase 0, it passed
lint, types and 362 tests, and only a rendered image caught it.

### 7.4 Minor

`viz3d.py:463-464` uses `mesh.n_faces_strict`, which now emits a
`PyVistaDeprecationWarning` on pyvista 0.48 (`n_faces` is the replacement).
Pre-existing, cosmetic, not fixed here.
