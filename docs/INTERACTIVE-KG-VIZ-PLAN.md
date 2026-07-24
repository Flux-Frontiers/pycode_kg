# Interactive Knowledge-Graph Visualization — Analysis & Plan

Status: **proposal / options** — no implementation started.
Scope: fleet-wide (KG_utils, pycode_kg, doc_kg, metabo_kg, gutenberg_kg, KGRAG).

---

## 1. Where this came from

The prompt was a Medium article, *"How to Turn Any Network Into an Interactive
Knowledge Graph to Discover Hidden Insights"* (Data Science Collective). The
article itself is member-only, but it is written by Erdogan Taskesen and the
techniques it demonstrates are exactly the published feature set of his two
libraries, `d3graph` and `d3blocks`/Elasticgraph. Those are the primary sources
used below.

The article's pitch is an *Obsidian-like* graph: a stand-alone HTML file, no
server, that you can hand to somebody, and that lets them **find structure they
did not know was there** by manipulating the graph rather than by reading a
static picture.

### The five mechanics that actually do the work

| # | Mechanic | What it buys you | Source |
|---|---|---|---|
| 1 | **Edge-weight threshold slider** | The signature move. Drag the threshold up and the hairball *progressively shatters* into disconnected components. Structure invisible at threshold 0 becomes obvious at threshold 0.6. This is the "hidden insight" engine. | `d3graph` — `slider=[None, None]`, `show_slider` |
| 2 | **Louvain community detection → colour + convex hulls** | Clusters are *computed from topology*, not hand-assigned by `kind`. Nodes are coloured by modularity partition and wrapped in a hull. | Elasticgraph (`hull_offset=15`) |
| 3 | **Collapse / expand super-nodes** | Each community collapses to one node; single-click expands it. This is what makes a 50k-node graph navigable at all. | Elasticgraph (`single_click_expand`) |
| 4 | **Centrality-driven encoding** | Node *size* = importance, node *colour* = community, tooltip = metadata. The picture encodes analytics, not just taxonomy. | `d3graph` node properties |
| 5 | **Level-of-detail + sticky physics** | Labels hide below a zoom threshold (`label_zoom_threshold=0.4`); dragged nodes pin in place (`sticky=True`, right-click releases) so you can hand-curate a layout. | Elasticgraph |

Everything is emitted as **one self-contained HTML file** — D3 v7 inlined, data
embedded as JSON, opens from `file://`.

A sixth idea worth stealing from the same author's `hnet`: **statistical edge
significance**. Test each association against a null model (hypergeometric /
permutation) and keep only edges that survive. Applied to a code graph this
answers "is this coupling more than you'd expect by chance?" — which is a
genuinely different question from "does this edge exist?"

---

## 2. Honest assessment of our current pipeline

Surveys of all six repos. The short version: **we have better analytics than the
article and a worse viewer.**

### 2.1 What we have

Roughly **5,000 LOC of visualization**, none of it shared:

| Repo | Module | LOC | Stack |
|---|---|---|---|
| pycode_kg | `app.py` | 1335 | Streamlit + pyvis |
| pycode_kg | `viz3d.py` | 1407 | PyVista + PyQt5 |
| pycode_kg | `layout3d.py` | 486 | numpy (Allium, Funnel) |
| pycode_kg | `viz3d_timeline.py` | 364 | Plotly |
| gutenberg_kg | `viz3d.py` | 1529 | PyVista + PyQt5 (ForestLayout) |
| metabo_kg | `viz3d.py` / `layout3d.py` | 1007 / 460 | PyVista (near-fork of pycode_kg) |
| metabo_kg | `app.py` | 1180 | Streamlit + pyvis |
| doc_kg | `app.py` | 412 | Streamlit + pyvis (no 3D at all) |
| KGRAG | `viz.py`, `viz_qt.py` | 224 + | Viewport abstraction (spec only) |

`KG_utils` — the shared SDK every repo depends on — contains **zero**
visualization code and **zero** graph analytics.

`metabo_kg/layout3d.py` is a fork-and-rename of `pycode_kg/layout3d.py`: only
~222 of ~460 lines differ, and the entire Fibonacci core is byte-identical apart
from docstrings. The divergence is almost purely domain vocabulary
(module→pathway, class→reaction, function→enzyme) and a different `_KIND_ZLEVEL`
map. `FunnelLayout` and `LayerCakeLayout` are the same algorithm under two names.

Analytics that *do* exist (all in pycode_kg):

- `analysis/centrality.py` — SIR weighted PageRank, hand-rolled power iteration,
  per-relation weights (CALLS 1.0 / INHERITS 0.8 / IMPORTS 0.45 / CONTAINS 0.15),
  persisted to a `centrality_scores` table.
- `ranking/coderank.py` — networkx PageRank, personalized PPR, query-subgraph
  induction, persisted to `node_metrics`.
- `analysis/bridge.py` — module connectivity centrality.
- `doc_kg/manifold.py` — embedding manifold projection.

### 2.2 The four findings that shape the plan

**Finding 1 — our analytics are computed, persisted, and then ignored.**
`centrality_scores` and `node_metrics` are written by the analysis pipeline and
read by *nothing* in either visualizer. Node size and colour in both the 2D and
3D viewers are driven **only** by `kind` (plus a `name.startswith("_")` check).
We already pay for PageRank and then throw the answer away. This is the single
cheapest, highest-value fix on the list.

**Finding 2 — the edge schema cannot support a threshold slider yet.**
`EdgeSpec.weight: float = 1.0` exists in `kg_utils/specs.py:51`, documented as
*"Edge weight for PageRank / centrality"* — but `GraphStore._upsert_edges`
(`kg_utils/store.py:206`) never writes it, and the `edges` table has no `weight`
column at all:

```sql
CREATE TABLE IF NOT EXISTS edges (
  src TEXT NOT NULL, rel TEXT NOT NULL, dst TEXT NOT NULL,
  evidence TEXT, PRIMARY KEY (src, rel, dst)
);
```

The weight is silently dropped on write. (`NodeSpec.metadata` is dropped the same
way.) The domain stores repeat the pattern: `metabo_kg/store.py:39-60` and
`doc_kg/store.py:44-67` both define `edges(src, rel, dst, evidence)` with no
weight column.

**And we are already computing a real per-edge weight and throwing it away.**
DocKG generates `SIMILAR_TO` edges from cosine similarity with a threshold and a
top-k cap (`doc_kg/kg.py:770-773` — `similar_k`, `similarity_edge_threshold`,
`similar_max_degree`), then discards the score at persist time. That cosine is
the single best natural input to a threshold slider anywhere in the fleet: a
semantic-similarity graph where dragging the threshold up peels apart topic
clusters is *precisely* the article's demo, and we are two lines from having the
data for it.

Mechanic #1 is blocked on this. There is a fallback — derive weight from relation
type, which `coderank.py` already does at analysis time and `doc_kg/kg.py:431`
does for BFS expansion scoring (`SIMILAR_TO: 0.8`, …). That gets a *working*
slider without a migration, and a *good* one after it.

**Finding 3 — we have no community detection anywhere in the fleet.**
No Louvain, no Leiden, no label propagation, no modularity. A repo-wide grep for
`centrality|louvain|community|modularity|networkx|umap|pagerank|betweenness`
across `metabo_kg/src` returns zero hits; doc_kg is the same. Our clusters are
taxonomic (`kind`, `module_path`, `HAS_TOPIC` edges), never topological.
Mechanics #2 and #3 both depend on this. It has to be written or imported.

Two partial exceptions worth knowing about. DocKG has `manifold.py` (282 LOC —
PCA elbow, participation ratio, TwoNN intrinsic dimension) which is diagnostic
rather than a 2D projection, but the PCA machinery is most of the way to an
*embedding-space layout* — a "semantic" alternative to force-directed that the
article does not have and we could. And DocKG already runs KMeans in three places
(`topics.py:607`, `discover_topics.py:159`, `sampler.py:204`) for topic
discovery, so clustering infrastructure exists, just not graph-topological
clustering.

**Finding 4 — KGRAG already specifies the thing we want and never built it.**
`KGRAG/src/kg_rag/viz.py:94` defines `DisplayMode.ONTOLOGICAL` with a detailed
spec — nodes sized by degree, coloured by kind, edges by relation, force-directed
layout, hover-to-inspect, click-to-resolve `kgrag://` — and
`adapters/base.py:198` `display()` dispatches straight to `_display_stub()`. The
architecture is designed, the renderer was never written.

**Finding 5 — we already ship one stand-alone HTML export, and it proves the
appetite.** `metabo_kg/viz3d.py:1000-1002` calls PyVista's `Plotter.export_html`
(VTK.js-backed), driven by `--export-html` on `metabokg viz3d`, and it runs
headless with no Qt window. So a self-contained, no-Python-required artifact is
not a foreign idea here — it exists, for 3D, in exactly one repo. What it *isn't*
is analytical: it exports a baked scene, so there is no threshold slider, no
community colouring, and no way to interrogate the graph. It is a snapshot, not
an instrument. That gap is the whole argument for this work.

### 2.3 Scale reality check

| Corpus | Nodes | Edges |
|---|---|---|
| doc_kg (own corpus) | 3–5k | 4k–22k (dense when `SIMILAR_TO` discovery ran) |
| pycode_kg (own repo) | ~7k | — |
| metabo_kg `hsa` | 22,290 | 11,298 |
| gutenberg_kg | up to 850k | up to 5M |

A naive D3 force simulation dies somewhere around 5–8k nodes. So collapse/expand
(mechanic #3) is not a nice-to-have for us — above metabo_kg's scale it is the
only way the graph renders at all. Any exporter needs a server-side subgraph
extraction step with a hard, *documented* node budget.

Today we dodge this by truncating: `doc_kg/app.py:245` caps the Graph tab at 400
nodes, so the UI never shows more than ~8% of its own graph, and pycode_kg's
browser caps at 500. Silent truncation is why nobody has noticed there's no
community structure to see — you can't see it in an 8% sample.

### 2.4 Licensing constraint (important)

Every repo in the fleet is **Elastic-2.0**.

- `d3graph` is **BSD-3-Clause** → safe to depend on.
- `d3blocks` (which is where Elasticgraph, i.e. mechanics #2 and #3, lives) is
  **GPL-3.0-or-later** → **cannot** be a dependency. The collapse/expand and hull
  behaviour has to be reimplemented, not imported.

### 2.5 Incidental defects the survey turned up

Not part of this proposal, but they were found while mapping the viz layer and
should be triaged separately. Listed in rough severity order.

1. **`st.iframe` does not exist.** Called at `pycode_kg/app.py:945, 1050, 1211`
   and `metabo_kg/app.py:470, 675`. Streamlit exposes `st.components.v1.html` /
   `st.components.v1.iframe`; there is no top-level `st.iframe`, and no shim or
   alias is defined in either module. DocKG uses the correct form at
   `doc_kg/app.py:319, 363`. On the face of it the 2D graph render is broken in
   two repos, and no test covers it. **Verify against the pinned Streamlit
   version before acting** — but this is the first thing to check.
2. **`networkx` is imported but never declared.** `pycode_kg/ranking/coderank.py:34`
   imports it; it appears in no repo's `pyproject.toml` and currently resolves
   only as a transitive dependency of `torch`. A latent break.
3. **Temp-file handling in `metabo_kg/app.py:349-353`** writes
   `f"temp_{id(net)}.html"` into the *current working directory*. `id()` is a
   reused memory address, not a UUID, so concurrent Streamlit sessions can
   collide, and any crash before cleanup litters the user's repo. DocKG's
   `tempfile.NamedTemporaryFile` discipline (`doc_kg/app.py:201-205`) is the
   pattern to copy.
4. **Dead `seed_ids` parameter** in `pycode_kg/app.py:318, 331` — seed
   highlighting is implemented and no caller ever passes it.
5. **`plotly` declared but unimported** in doc_kg's `viz` and `all` extras.
6. **Stale docs** — `pycode_kg/docs/Architecture-brief.md:187` and
   `Architecture-plain.md:86` still name the `cake` layout, renamed to `funnel`.
7. **Stale alias** — `metabo_kg/layout3d.py:150` keeps `_golden_spiral_2d` for
   "unit tests" that do not exist; `metabo_kg/tests/` has no layout test at all.

---

## 3. Options

Three coherent options, plus a recommendation. They are not mutually exclusive —
Option A is a sensible Phase 0 for Option C.

### Option A — Retrofit the viewers we already have

Wire the existing `centrality_scores` / `node_metrics` tables into `app.py` and
`viz3d.py`. Node radius ∝ PageRank, opacity ∝ rank percentile, add a "top-N by
centrality" filter. Add a shared `theme.py` to KG_utils to kill the three
divergent kind→colour maps.

- **Adds:** mechanic #4 only.
- **New dependencies:** none.
- **Complexity:** low. Touches ~200 LOC across two files.
- **Risk:** very low.
- **Gets you:** the highest value-per-line change available. The graph starts
  *meaning* something immediately.
- **Doesn't get you:** the threshold slider, communities, a shareable artifact.

### Option B — Depend on `d3graph` (BSD-3)

Write a `to_d3graph()` exporter: `GraphStore` → adjacency/edge-list DataFrame →
`d3graph` → standalone HTML. Threshold slider, Louvain colouring, and the
stand-alone file come essentially free.

- **Adds:** mechanics #1, #2, #4 (partial).
- **New dependencies:** 11 direct (`pandas`, `numpy`, `networkx`, `jinja2`,
  `python-louvain`, `colourmap`, `ismember`, `datazets`, `distfit`, …). Heavy for
  a package whose core is deliberately zero-dependency.
- **Complexity:** low-medium. Mostly a data-shaping adapter.
- **Risk:** medium. We own none of the template. Cannot add collapse/expand,
  `kgrag://` deep links, or our own tooltips without forking. `datazets` and
  `distfit` are dead weight we'd be shipping.
- **Gets you:** the fastest possible path to a working demo of the article's
  core trick.
- **Doesn't get you:** mechanic #3 (that's the GPL half), and no path to it.

### Option C — Own the template: `kg_utils.viz.web`

A new optional `viz-web` extra in KG_utils: a Jinja2 (or `string.Template`, to
preserve the zero-dep core) HTML emitter plus a hand-written D3 v7 bundle we
control. Server-side Python does subgraph extraction, Louvain partitioning,
centrality lookup, and weight resolution; the browser does force layout,
threshold filtering, hull drawing, and collapse/expand.

- **Adds:** all five mechanics, plus the ones the article doesn't have —
  `kgrag://` deep links, snapshot diff overlay, semantic (embedding-manifold)
  layout as an alternative to force-directed.
- **New dependencies:** `networkx` (declare it properly — we already use it),
  optional `python-louvain`; or implement Louvain in ~120 LOC of pure Python and
  keep the extra at zero runtime deps.
- **Complexity:** medium-high. ~600 LOC JS + ~400 LOC Python + tests.
- **Risk:** medium. It's real frontend work and we'd own the maintenance.
- **Gets you:** one exporter that serves every KG in the fleet, no GPL exposure,
  full control, and the first genuinely *shareable* artifact the project has ever
  produced — `pycodekg export-html && open graph.html`, no Streamlit, no Qt, no
  Python on the recipient's machine.

### Enabling work (required by B and C, independent of which)

| Task | Where | Complexity | Blocks |
|---|---|---|---|
| Add `weight REAL NOT NULL DEFAULT 1.0` to `edges`; persist `EdgeSpec.weight` | `kg_utils/store.py:41`, `:206` | low | mechanic #1 |
| Stop discarding the `SIMILAR_TO` cosine score | `doc_kg/kg.py:770-773` | low | mechanic #1 (best data) |
| Add `REL_WEIGHTS` fallback so weight is derivable without a rebuild | `kg_utils/store.py` | low | mechanic #1 |
| New `kg_utils/analysis/community.py` — Louvain over the store | KG_utils | medium | mechanics #2, #3 |
| Promote centrality out of pycode_kg into `kg_utils/analysis/` | KG_utils | medium | fleet-wide reuse |
| Collapse the `layout3d.py` fork into one shared copy | KG_utils | medium | fleet-wide reuse |
| Declare `networkx` in every `pyproject.toml` that imports it | all | trivial | correctness |

Note that persisting `NodeSpec.metadata` (currently also dropped) is the natural
companion to the edge-weight migration — same file, same test, and it unblocks
domain-specific tooltip content.

---

## 4. Recommended starting repo: **pycode_kg** (pilot) → **KG_utils** (home)

Not one repo — a two-step. Build it where feedback is fastest, then promote it
where it belongs.

**Why pycode_kg as the pilot:**

1. It is the *only* repo with centrality already computed and persisted. Every
   other repo would need the analytics built first; here the data is sitting in a
   table waiting to be read.
2. It is the only true `KGModule` subclass, so whatever we build against its
   store is automatically correct for the SDK contract.
3. `layout3d.py` has **zero coupling** — imports only numpy and stdlib, and is a
   pure `(nodes, edges) -> positions` function. The survey called it the cheapest
   extension point in the codebase.
4. We dogfood it. Every commit to pycode_kg is immediately visible in the graph
   of pycode_kg itself.
5. Its graph (~7k nodes) is large enough to be a real test of collapse/expand and
   small enough to iterate on.

**Why KG_utils as the destination:** the survey found `layout3d.py` already
near-forked between pycode_kg (486 LOC) and metabo_kg (460 LOC), and three
divergent kind→colour maps within pycode_kg alone. Building viz #6 in a sixth
repo repeats the mistake. The zero-dep-core-plus-extras pattern
(`semantic`, `sqlite-vec`, `synthesis`) is already established and a `viz-web`
extra slots straight into it.

**The serious alternative: doc_kg.** This is a closer call than it first looks,
and it turns on what you think the demo should be.

pycode_kg's edges are *structural and typed* — `CALLS`, `CONTAINS`, `IMPORTS`.
Their weights are conventions we assign per relation type, so a threshold slider
over them is really a relation filter with extra steps. DocKG's `SIMILAR_TO`
edges are *continuously weighted by cosine similarity*, which is the graph shape
the article is actually about: raise the threshold and semantic topic clusters
physically separate. That is the demo that sells the idea. DocKG's graph is also
the right size (3–5k nodes) to render in D3 without needing collapse/expand
first, which removes the hardest phase from the critical path — and its `app.py`
is the cleanest viz module in the fleet at 412 LOC.

Against it: DocKG has no centrality, no 3D, no layout engine, and no export path,
so more has to be built from nothing. pycode_kg has PageRank sitting in a table
already.

The honest framing: **pick pycode_kg to prove the plumbing, pick doc_kg to prove
the idea.** If the goal is a working exporter with the least new code, start with
pycode_kg. If the goal is to show somebody why this matters, start with doc_kg —
persist that cosine and the slider does the rest.

**Third: KGRAG.** Tempting because the multi-KG federated view is the most
compelling thing we could eventually build, and because `DisplayMode.ONTOLOGICAL`
is already specified down to the colour codes. But the `display(viewport)`
contract is Streamlit/Qt-shaped, and the article's whole value proposition is a
stand-alone file with *no* host. Do KGRAG once the exporter exists and the
adapter is a five-line delegation.

---

## 5. Suggested phasing

Priorities and dependencies only — no time estimates, per project policy.

**Phase 0 — cheap wins (Option A).** Priority: high. Complexity: low. No
dependencies. Wire persisted centrality into `app.py` and `viz3d.py`; extract a
shared `theme.py`; declare `networkx`. Ships value on its own even if nothing
else follows.

**Phase 1 — enabling schema + analytics.** Priority: high. Complexity: medium.
Depends on: nothing. Edge `weight` column + persistence + `REL_WEIGHTS` fallback;
`kg_utils/analysis/community.py`; promote centrality to KG_utils. Needs a store
migration test and a backward-compat test against an existing `graph.sqlite`.

**Phase 2 — the exporter (Option C).** Priority: high. Complexity: medium-high.
Depends on: Phase 1. `kg_utils/viz/web.py` + D3 template + `pycodekg export-html`
CLI command. Mechanics #1, #2, #4, #5. Hard node budget with documented
truncation.

**Phase 3 — collapse/expand.** Priority: medium. Complexity: high. Depends on:
Phase 2. Mechanic #3. This is what unlocks metabo_kg and gutenberg_kg's large
corpora.

**Phase 4 — fleet rollout + KGRAG.** Priority: medium. Depends on: Phase 2.
Implement `display()` for the ONTOLOGICAL mode by delegating to the exporter;
add `export-html` to doc_kg, metabo_kg, gutenberg_kg.

**Phase 5 — statistical edge significance.** Priority: low. Complexity: high.
Depends on: Phase 1. The `hnet` idea — permutation-test each edge against a null
model, expose "significant edges only" as a filter. Genuinely novel for a code
graph; explicitly speculative.

---

## 6. Open questions for review

1. **Option B or C?** B is much faster to a demo; C is the only one that reaches
   collapse/expand, which our graph sizes arguably make mandatory.
2. **pycode_kg or doc_kg as the pilot?** See §4 — plumbing vs. idea. This is the
   one decision that changes the shape of Phase 2.
3. **Is a stand-alone HTML artifact actually wanted**, or is the goal a better
   Streamlit experience? The article's entire premise is the former; our existing
   investment is almost entirely in the latter (metabo_kg's `export_html` being
   the lone exception, and it's a baked scene rather than an instrument).
4. **Louvain: vendor or depend?** `python-louvain` is BSD; a pure-Python
   implementation is ~120 LOC and keeps the KG_utils core dependency-free.
5. **Migration policy for `edges.weight`** — `ALTER TABLE ADD COLUMN` on open, or
   require a rebuild? The former is friendlier; the latter is cleaner.
6. **Is the `st.iframe` call in §2.5 actually broken?** If so it is more urgent
   than anything else in this document, and unrelated to it.
