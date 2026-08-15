# PyCodeKG 3D Visualizer

`viz3d` renders your Python codebase as an interactive 3-D knowledge graph — every
module, class, function, and method becomes a solid object in space, and every
relationship between them becomes a coloured edge.  You can orbit, zoom, and pick
any node to read its docstring.

---

## What the graph represents

The knowledge graph is built from your repo's AST and stores four structural
relationships:

| Edge type | Meaning |
|-----------|---------|
| **CONTAINS** | A module contains a class or function; a class contains its methods |
| **CALLS** | One function or method calls another |
| **IMPORTS** | A module imports another module or symbol |
| **INHERITS** | A class inherits from another class |

Every node is one of:

| Node kind | Shape | Colour |
|-----------|-------|--------|
| Module | Cube | Blue `#4A90D9` |
| Class | Icosahedron (Octahedron at low LOD) | Orange `#E67E22` |
| Function | Cylinder | Green `#27AE60` |
| Private function (`_…`) | Cylinder | Yellow `#F1C40F` |
| Method | Icosahedron (Sphere at low LOD) | Purple `#8E44AD` |
| Symbol stub | Small sphere | Grey `#95A5A6` |

Colours come from `pycode_kg.theme`, shared with the 2-D explorer so the two
views agree. Shape and colour together identify the node's *kind*; node **size**
is reserved for centrality (see below).

Node geometry is automatically simplified for large repos (Level-of-Detail tiers at
800 and 1 500 visible nodes) so rendering stays interactive at scale.

---

## Layout styles

### Allium

Each module is drawn as a **Giant Allium flower**:

- The **module node** (cube) sits in a flat Fibonacci-annulus ring in the XY plane
  at Z = 0.  Modules are spaced outward from the centre so the ring grows with
  the number of modules.
- The **stem apex** rises vertically above each module cube.
- **Classes and top-level functions** are scattered on a Fibonacci sphere
  ("the flower head") centred at the stem apex.  The head radius grows with
  the square root of the child count.
- **Methods** orbit their parent class on a smaller Fibonacci sphere just
  above the head.

The result is a botanical landscape — you can visually identify large modules
(tall, bushy alliums), densely connected classes (compact heads), and lightly
populated modules (sparse heads) at a glance.

> Best for: exploring intra-module structure, spotting size imbalances,
> comparing module complexity.

### Funnel

Nodes are **stratified by kind** across horizontal Z layers:

| Layer | Node kind | Z height |
|-------|-----------|----------|
| 0 | Modules | 0 |
| 1 | Classes | `layer_gap` (default 20) |
| 2 | Functions & Methods | `2 × layer_gap` |
| 3 | Symbol stubs | `3 × layer_gap` |

Within each layer, XY positions are placed on a golden-angle disc spiral.
The disc radius is derived algorithmically — `r = spacing × node_size × √n` —
so the layout scales correctly for repos of any size without hand-tuning.

Cross-cutting edges (CALLS, IMPORTS, INHERITS) arc between layers, making
structural coupling immediately visible from any angle.  The overall silhouette
typically narrows at the top (fewer modules, many functions), giving the layout
its name.

> Best for: understanding cross-layer coupling, import architecture,
> call graph shape at a glance.

### Organic

Allium and Funnel *place* nodes on a lattice. Organic **grows** a tree toward
them, by space colonization: the wood starts at the origin and branches its way
out to reach every definition, the way a real tree grows toward light.

| Graph | Geometry |
|-------|----------|
| Repository | The trunk, standing at the origin |
| Module | A limb, on a golden-angle spiral up the trunk |
| Class, function, method | A leaf — a crown attractor the wood must reach |

Because the attractors are the actual definitions, the canopy's shape *is* the
shape of the codebase. Two properties follow from the growth rather than being
drawn on top of it:

- **Limb thickness** obeys the pipe model (`r_parent = (Σ r_child^2.2)^(1/2.2)`),
  so a limb's girth is exactly how much code hangs off it. The trunk's radius
  is a pure function of the repository's total definition count.
- **Limb length** is scaled by the module's definition count, so the biggest
  module reaches furthest and the crown fills instead of forming a hollow shell.

Leaves are tinted by kind — orange classes, green functions, yellow private
functions, purple methods — so a mostly-purple cluster is a class-heavy module
and a mostly-green one is a module of free functions.

```bash
pycodekg viz3d --layout organic
```

> Best for: seeing the whole repository's shape and weight distribution at once,
> and for holographic output (see below).
>
> **Picking is disabled** in this mode. The canopy is a single glyphed mesh with
> no per-node actor to pick, and the wood is grown rather than positioned — a
> leaf is a definition, but the branch it hangs from belongs to no single node.

---

## Holographic output — `pycodekg quilt`

The organic tree can be rendered as a **quilt**: the tiled multi-view image a
Looking Glass lenticular display fuses into real depth.

```bash
pycodekg quilt                          # 16" Gen3 Landscape, the default
pycodekg quilt --spec portrait          # a different device preset
pycodekg quilt --zoom 1.5               # fill more of the frame — more depth
pycodekg quilt --orbit 120 --fps 24     # a turntable quilt video instead
pycodekg quilt --cast                   # send it straight to the display
```

Output lands in `renders/quilts/` with the `_qs<cols>x<rows>a<aspect>` suffix
Looking Glass Bridge and Studio parse, plus a flat centre-view PNG in
`renders/previews/` — a quilt opened in an ordinary image viewer is a tiled
contact sheet, which is useless for judging whether the tree looks right. The
whole `renders/` directory is git-ignored; everything in it regenerates.

Every render prints a **disparity budget** first:

```
  focal plane      137.3 units
  view cone        35.0 deg over 48 views
  adjacent-view disparity:
    nearest foliage       126.7   2.55 px
    focal plane (display surface)    137.3   0.00 px
    farthest foliage      147.8   2.18 px
```

That is the per-view pixel shift at each depth, and it is what decides whether
the display *fuses* the views or ghosts them. Roughly 4–5 px is the practical
ceiling; past ~8 px expect visible doubling. Content exactly at the focal plane
has zero disparity, which is why the camera is framed with the focal point at
mid-canopy — the crown straddles the display surface, half in front of the
glass and half behind.

The budget is reported for the camera the render will actually use, not the
one you framed: `render_quilt` narrows the FOV and dollies back before it
sweeps, so the focal distance above is larger than the framing distance. That
is `quiltwright.depth_report`, which takes the same `--fov` and `--zoom` this
command passes on.

All of the quilt geometry — the off-axis frustum per view, the tiling order,
the filename convention, the depth budget, the Bridge protocol — lives in
[quiltwright](https://github.com/suchanek/quiltwright), which arrives with the
`viz3d` extra on Python 3.12 and 3.13.

---

## Camera and navigation

| Action | Result |
|--------|--------|
| Left-drag | Orbit (terrain-constrained — Z stays up) |
| Right-drag / scroll | Zoom |
| Middle-drag | Pan |
| **Reset View** button | Returns to the default front-elevated perspective |

The default view looks along +Y with a slight upward tilt so the full vertical
extent of the graph (ground modules → top functions) is visible on launch.

The **XYZ orientation widget** in the top-right corner always shows the current
camera orientation.

---

## Picking nodes

**Right-click** any node to:

- Highlight it in pink
- Open a floating docstring popup (rendered as Markdown)
- Zoom the camera toward it

Click **Show Docstring** in the button row to re-open the popup for the last
picked node.  Close the popup or click another node to clear the highlight.

---

## User interface

*(screenshot)*

### Control panel (left)

| Section | Controls |
|---------|---------|
| **Input Parameters** | Database path (`.pycodekg/graph.sqlite`), layout selector (Allium / Funnel), save path stem, save format (HTML / PNG / JPG) |
| **Module Filter** | Single-select list — choose one module to render only that subtree; leave empty to show the whole repo |
| **Render Options** | Checkboxes: Methods, Symbols, CONTAINS edges |
| **Edge Types** | Checkboxes: CALLS, IMPORTS, INHERITS |
| **Funnel Spacing** | Slider (0.5 – 10.0) — controls the XY spread of each funnel layer; only active when Funnel layout is selected |
| **Size Nodes By** | Dropdown — `(uniform)` sizes nodes by kind; any other entry sizes them by that centrality metric |
| **Graph Statistics** | Live node/edge counts updated after each render |

#### Sizing nodes by centrality

By default node radius encodes node *kind* — every function is the same size as
every other function. Selecting a metric under **Size Nodes By** switches the
radius to encode structural importance instead, so the modules and functions
everything else depends on are visibly larger.

The dropdown is populated from the `centrality_scores` and `node_metrics` tables,
which are written by the analysis pipeline rather than by the graph build. A
graph that has been built but never analysed offers only `(uniform)`; run:

```bash
pycodekg analyze .
```

then reopen the viewer (or re-enter the database path) to pick up the metrics.

Radius is the node's per-kind size multiplied by a factor between 0.6× and
1.8×, derived from the node's **rank percentile** within the metric.

Rank rather than raw magnitude because centrality scores are extremely
top-heavy — on pycode_kg's own graph the median score is 1.2× the minimum while
the maximum is 58× it. Scaling by magnitude collapses almost every node onto one
end of the range: linearly they all sit at the minimum, logarithmically they all
sit near the maximum. Rank spreads them across the full range instead. The exact
score and rank are still available on hover in the 2-D explorer.

A *multiplier* rather than an absolute range, because 3-D node positions are
fixed by the layout and so radius has a spatial budget. An allium head is only
about `2 + sqrt(n_children) * 0.4` units across; nodes sized on an absolute
scale outgrew it, fusing each head into a solid ball that hid the stem and every
CALLS arc inside it. Scaling the per-kind size keeps every node inside the room
the layout gave it.

Node *kind* is carried by shape and colour, not size, so size is free to encode
centrality alone. A highly central method can therefore render larger than an
unimportant module — that is intended. Nodes with no score for the selected
metric render at exactly their per-kind size.

The same metrics drive the 2-D Streamlit explorer, where they control node
diameter *and* opacity; see the **Centrality** section of its sidebar.

### Viewport buttons (below the 3-D view)

| Button | Action |
|--------|--------|
| **Render Graph** | (Re-)build the full 3-D scene with current settings |
| **Show Docstring** | Re-open the docstring popup for the last picked node |
| **Save View** | Export the current viewport to the configured path and format |
| **Reset View** | Restore the default camera angle and zoom |
| **Reset Settings** | Return all controls to their defaults and re-render |

### Window title bar

The title shows the repo name, version, and live node counts:

```
PyCodeKG 3D v0.17.2 | pycode_kg | Modules: 56  Classes: 46  Methods: 214  Functions: 163  Faces: 7818
```

---

## Performance notes

- **Edge cap** — edges are rendered up to a hard limit of 8 000.  When the limit
  is hit, structural `CONTAINS` edges are preserved first; `CALLS` edges are the
  first to be dropped.
- **Arc edges** — for graphs with ≤ 2 000 edges, edges are drawn as quadratic
  Bézier arcs for visual clarity.  Above that threshold straight lines are used
  for performance.
- **LOD tiers** — node geometry is automatically simplified above 800 and 1 500
  visible nodes.

---

## Launching

```bash
# Default (Allium layout, current repo)
pycodekg viz3d

# Funnel layout, custom DB
pycodekg viz3d --layout funnel --db /path/to/.pycodekg/graph.sqlite

# Grow the repository as a tree
pycodekg viz3d --layout organic

# Larger window
pycodekg viz3d --width 1920 --height 1080
```

The database must exist before launching — run `pycodekg build` first if needed.
