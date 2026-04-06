> **Analysis Report Metadata**
> - **Generated:** 2026-03-17T17:10:45Z
> - **Version:** code-kg 0.9.1
> - **Commit:** 05889b8 (main)
> - **Platform:** macOS 26.3 | arm64 (arm) | Turing | Python 3.12.13
> - **Graph:** 147081 nodes · 344290 edges (12782 meaningful)
> - **Included directories:** all
> - **Excluded directories:** none
> - **Elapsed time:** 58s

# matplotlib Analysis

**Generated:** 2026-03-17 17:10:45 UTC

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **matplotlib** repository using CodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
|----------------|-------|-------|
| [F] **Critical** | **F** | 35 / 100 |

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| **Total Nodes** | 147081 |
| **Total Edges** | 344290 |
| **Modules** | 913 (of 913 total) |
| **Functions** | 4559 |
| **Classes** | 1122 |
| **Methods** | 6188 |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | 48878 |
| CONTAINS | 11869 |
| IMPORTS | 5562 |
| ATTR_ACCESS | 56807 |
| INHERITS | 753 |

---

## Fan-In Ranking

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers |
|---|----------|--------|---------|
| 1 | `plot()` | lib/matplotlib/axes/_axes.py | **530** |
| 2 | `figure()` | lib/matplotlib/pyplot.py | **527** |
| 3 | `gca()` | lib/matplotlib/pyplot.py | **177** |
| 4 | `update()` | lib/matplotlib/widgets.py | **150** |
| 5 | `set_visible()` | lib/matplotlib/widgets.py | **134** |
| 6 | `_copy_docstring_and_deprecators()` | lib/matplotlib/pyplot.py | **101** |
| 7 | `axes()` | lib/matplotlib/figure.py | **82** |
| 8 | `axes()` | lib/matplotlib/figure.py | **82** |
| 9 | `get_points()` | lib/matplotlib/transforms.py | **73** |
| 10 | `to_rgba()` | lib/matplotlib/colors.py | **67** |
| 11 | `norm()` | lib/matplotlib/colorizer.py | **62** |
| 12 | `norm()` | lib/matplotlib/colorizer.py | **62** |
| 13 | `get_matrix()` | lib/matplotlib/transforms.py | **48** |
| 14 | `tick_values()` | lib/matplotlib/ticker.py | **46** |
| 15 | `Bbox()` | lib/matplotlib/transforms.py | **44** |


**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:
- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.

No extreme high fan-out functions detected. Well-balanced architecture.

---

## Module Architecture

Top modules by dependency coupling and cohesion (showing up to 10 with activity).
Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.

| Module | Functions | Classes | Incoming | Outgoing | Cohesion |
|--------|-----------|---------|----------|----------|----------|
| `lib/matplotlib/tests/test_axes.py` | 633 | 10 | 0 | 31 | 0.97 |
| `lib/matplotlib/patches.py` | 7 | 56 | 114 | 13 | 0.10 |
| `lib/matplotlib/transforms.py` | 12 | 24 | 124 | 3 | 0.02 |
| `lib/matplotlib/widgets.py` | 3 | 24 | 33 | 23 | 0.40 |
| `lib/matplotlib/backend_bases.py` | 19 | 22 | 44 | 23 | 0.34 |
| `lib/matplotlib/colors.py` | 25 | 23 | 84 | 5 | 0.06 |
| `lib/matplotlib/axes/_base.py` | 5 | 7 | 77 | 30 | 0.28 |
| `lib/matplotlib/ticker.py` | 9 | 31 | 57 | 3 | 0.05 |
| `lib/matplotlib/pyplot.py` | 176 | 1 | 658 | 28 | 0.04 |
| `lib/matplotlib/axis.py` | 3 | 8 | 10 | 19 | 0.63 |

---

## Key Call Chains

Deepest call chains in the codebase.

**Chain 1** (depth: 6)

```
loglog → plot → normalize_kwargs → get → _copy_docstring_and_deprecators → _add_pyplot_note
```

**Chain 2** (depth: 8)

```
sca → figure → _get_backend_mod → switch_backend → install_repl_displayhook → get → _copy_docstring_and_deprecators → _add_pyplot_note
```

**Chain 3** (depth: 4)

```
box → gca → _copy_docstring_and_deprecators → _add_pyplot_note
```

**Chain 4** (depth: 6)

```
clear → update → _load_blit_background → get → _copy_docstring_and_deprecators → _add_pyplot_note
```

**Chain 5** (depth: 6)

```
_clear_without_update → set_visible → set_visible → pchanged → process → func
```

---

## Public API Surface

Identified public APIs (module-level functions with high usage).

| Function | Module | Fan-In | Type |
|----------|--------|--------|------|
| `figure()` | lib/matplotlib/pyplot.py | 527 | function |
| `Path()` | lib/matplotlib/path.py | 236 | class |
| `gca()` | lib/matplotlib/pyplot.py | 177 | function |
| `context()` | lib/matplotlib/style/__init__.py | 107 | function |
| `rc_context()` | lib/matplotlib/__init__.py | 87 | function |
| `rc_context()` | lib/matplotlib/pyplot.py | 87 | function |
| `axes()` | lib/matplotlib/pyplot.py | 67 | function |
| `to_rgba()` | lib/matplotlib/colors.py | 67 | function |
| `Bbox()` | lib/matplotlib/transforms.py | 44 | class |
| `Triangulation()` | lib/matplotlib/tri/_triangulation.py | 34 | class |
---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
| `function` | 1023 | 4559 | [LOW] 22.4% |
| `method` | 2835 | 6188 | [LOW] 45.8% |
| `class` | 623 | 1122 | [WARN] 55.5% |
| `module` | 724 | 913 | [WARN] 79.3% |
| **total** | **5205** | **12782** | **[LOW] 40.7%** |

> **Recommendation:** 7577 nodes lack docstrings. Prioritize documenting high-fan-in functions and public API surface first — these have the highest impact on query accuracy.

---

## Structural Importance Ranking (SIR)

Weighted PageRank aggregated by module — reveals architectural spine. Cross-module edges boosted 1.5×; private symbols penalized 0.85×. Node-level detail: `codekg centrality --top 25`

| Rank | Score | Members | Module |
|------|-------|---------|--------|
| 1 | 0.060105 | 247 | `lib/matplotlib/transforms.py` |
| 2 | 0.042248 | 178 | `lib/matplotlib/pyplot.py` |
| 3 | 0.031948 | 203 | `lib/matplotlib/colors.py` |
| 4 | 0.029399 | 133 | `lib/matplotlib/cbook.py` |
| 5 | 0.025334 | 317 | `lib/matplotlib/patches.py` |
| 6 | 0.025071 | 218 | `lib/matplotlib/backend_bases.py` |
| 7 | 0.023238 | 191 | `lib/matplotlib/ticker.py` |
| 8 | 0.022554 | 144 | `lib/matplotlib/backends/backend_pdf.py` |
| 9 | 0.021673 | 131 | `lib/matplotlib/figure.py` |
| 10 | 0.021286 | 673 | `lib/matplotlib/tests/test_axes.py` |
| 11 | 0.020207 | 233 | `lib/matplotlib/widgets.py` |
| 12 | 0.018975 | 202 | `lib/matplotlib/axes/_base.py` |
| 13 | 0.018096 | 43 | `lib/matplotlib/path.py` |
| 14 | 0.016867 | 107 | `lib/matplotlib/artist.py` |
| 15 | 0.016384 | 175 | `lib/matplotlib/_mathtext.py` |



---

## Code Quality Issues

- [LOW] Low docstring coverage (40.7%) — semantic query quality will be poor; embedding undocumented nodes yields only structured identifiers, not NL-searchable text. Prioritize docstrings on high-fan-in functions first.
- [WARN] 9 orphaned functions found (`wrapper`, `empty_with_docstring`, `_meth`, `_deprecated_parameter_class`, `wrapper`, `test_load_old_api`, `_deprecated_property`, `_old_init`, `deprecate`) -- consider archiving or documenting
- [WARN] Diamond inheritance detected: `GeoAxes`, `HammerAxes`, `SkewXAxes`, `SkewXAxis`, `MyApp`, `App`, `App`, `MyApp`, `App`, `XAxis`, `YAxis`, `FigureCanvasGTK3Agg`, `FigureCanvasGTK3Cairo`, `FigureCanvasGTK4Agg`, `FigureCanvasGTK4Cairo`, `FigureCanvasMac`, `FigureManagerNbAgg`, `FigureCanvasQTAgg`, `FigureCanvasQTCairo`, `FigureCanvasTkAgg`, `FigureCanvasTkCairo`, `FigureManagerWebAgg`, `FigureCanvasWxAgg`, `FigureCanvasWxCairo`, `AitoffAxes`, `GeoAxes`, `HammerAxes`, `LambertAxes`, `MollweideAxes`, `PolarAxes`, `RadialAxis`, `ThetaAxis`, `SubclassAxes`, `SkewXAxes`, `SkewXAxis`, `AutoLocator`, `LogitLocator`, `Axes`, `Axes`, `AxesZero`, `FixedAxisArtistHelper`, `FloatingAxisArtistHelper`, `GridHelperCurveLinear`, `MaxNLocator`, `Axes3D`, `Axis`, `XAxis`, `YAxis`, `ZAxis` -- verify MRO is intentional (C3 linearisation)
- [WARN] Deep inheritance hierarchy (max depth 6) -- consider flattening via composition

---

## Architectural Strengths

- Well-structured with 15 core functions identified
- No god objects or god functions detected

---

## Recommendations

### Immediate Actions
1. **Improve docstring coverage** — 7577 nodes lack docstrings; prioritize high-fan-in functions and public APIs first for maximum semantic retrieval gain
2. **Remove or archive orphaned functions** — `wrapper`, `empty_with_docstring`, `_meth`, `_deprecated_parameter_class`, `wrapper` (and 4 more) have zero callers and add maintenance burden

### Medium-term Refactoring
1. **Harden high fan-in functions** — `plot`, `figure`, `gca` are widely depended upon; review for thread safety, clear contracts, and stable interfaces
2. **Reduce module coupling** — consider splitting tightly coupled modules or introducing interface boundaries
3. **Add tests for key call chains** — the identified call chains represent well-traveled execution paths that benefit most from regression coverage

### Long-term Architecture
1. **Version and stabilize the public API** — document breaking-change policies for `figure`, `Path`, `gca`
2. **Enforce layer boundaries** — add linting or CI checks to prevent unexpected cross-module dependencies as the codebase grows
3. **Monitor hot paths** — instrument the high fan-in functions identified here to catch performance regressions early

---

## Inheritance Hierarchy

**753** INHERITS edges across **773** classes. Max depth: **6**.

| Class | Module | Depth | Parents | Children |
|-------|--------|-------|---------|----------|
| `HammerAxes` | galleries/examples/misc/custom_projection.py | 6 | 1 | 0 |
| `AsteriskPolygonCollection` | lib/matplotlib/collections.py | 6 | 1 | 0 |
| `FillBetweenPolyCollection` | lib/matplotlib/collections.py | 6 | 1 | 0 |
| `PolyQuadMesh` | lib/matplotlib/collections.py | 6 | 2 | 0 |
| `StarPolygonCollection` | lib/matplotlib/collections.py | 6 | 1 | 0 |
| `AitoffAxes` | lib/matplotlib/projections/geo.py | 6 | 1 | 0 |
| `HammerAxes` | lib/matplotlib/projections/geo.py | 6 | 1 | 0 |
| `LambertAxes` | lib/matplotlib/projections/geo.py | 6 | 1 | 0 |
| `MollweideAxes` | lib/matplotlib/projections/geo.py | 6 | 1 | 0 |
| `Barbs` | lib/matplotlib/quiver.py | 6 | 1 | 0 |
| `Quiver` | lib/matplotlib/quiver.py | 6 | 1 | 0 |
| `Path3DCollection` | lib/mpl_toolkits/mplot3d/art3d.py | 6 | 1 | 0 |
| `Poly3DCollection` | lib/mpl_toolkits/mplot3d/art3d.py | 6 | 1 | 0 |
| `GeoAxes` | galleries/examples/misc/custom_projection.py | 5 | 1 | 5 |
| `RibbonBoxImage` | galleries/examples/misc/demo_ribbon_box.py | 5 | 1 | 0 |
| `SkewXAxes` | galleries/examples/specialty_plots/skewt.py | 5 | 1 | 0 |
| `SkewXAxis` | galleries/examples/specialty_plots/skewt.py | 5 | 1 | 0 |
| `CircleCollection` | lib/matplotlib/collections.py | 5 | 1 | 0 |
| `EventCollection` | lib/matplotlib/collections.py | 5 | 1 | 0 |
| `PathCollection` | lib/matplotlib/collections.py | 5 | 1 | 1 |

### Multiple Inheritance (49 classes)

- `RcParams` (lib/matplotlib/__init__.py) inherits from `MutableMapping`, `dict`
- `CapStyle` (lib/matplotlib/_enums.py) inherits from `Enum`, `str`
- `JoinStyle` (lib/matplotlib/_enums.py) inherits from `Enum`, `str`
- `FFMpegFileWriter` (lib/matplotlib/animation.py) inherits from `FFMpegBase`, `FileMovieWriter`
- `FFMpegWriter` (lib/matplotlib/animation.py) inherits from `FFMpegBase`, `MovieWriter`
- `ImageMagickFileWriter` (lib/matplotlib/animation.py) inherits from `FileMovieWriter`, `ImageMagickBase`
- `ImageMagickWriter` (lib/matplotlib/animation.py) inherits from `ImageMagickBase`, `MovieWriter`
- `_Mode` (lib/matplotlib/backend_bases.py) inherits from `Enum`, `str`
- `NavigationToolbar2Tk` (lib/matplotlib/backends/_backend_tk.py) inherits from `Frame`, `NavigationToolbar2`
- `ToolbarTk` (lib/matplotlib/backends/_backend_tk.py) inherits from `Frame`, `ToolContainerBase`
- `FigureCanvasGTK3` (lib/matplotlib/backends/backend_gtk3.py) inherits from `DrawingArea`, `_FigureCanvasGTK`
- `NavigationToolbar2GTK3` (lib/matplotlib/backends/backend_gtk3.py) inherits from `Toolbar`, `_NavigationToolbar2GTK`
- `ToolbarGTK3` (lib/matplotlib/backends/backend_gtk3.py) inherits from `Box`, `ToolContainerBase`
- `FigureCanvasGTK3Agg` (lib/matplotlib/backends/backend_gtk3agg.py) inherits from `FigureCanvasAgg`, `FigureCanvasGTK3`
- `FigureCanvasGTK3Cairo` (lib/matplotlib/backends/backend_gtk3cairo.py) inherits from `FigureCanvasCairo`, `FigureCanvasGTK3`
- `FigureCanvasGTK4` (lib/matplotlib/backends/backend_gtk4.py) inherits from `DrawingArea`, `_FigureCanvasGTK`
- `NavigationToolbar2GTK4` (lib/matplotlib/backends/backend_gtk4.py) inherits from `Box`, `_NavigationToolbar2GTK`
- `ToolbarGTK4` (lib/matplotlib/backends/backend_gtk4.py) inherits from `Box`, `ToolContainerBase`
- `FigureCanvasGTK4Agg` (lib/matplotlib/backends/backend_gtk4agg.py) inherits from `FigureCanvasAgg`, `FigureCanvasGTK4`
- `FigureCanvasGTK4Cairo` (lib/matplotlib/backends/backend_gtk4cairo.py) inherits from `FigureCanvasCairo`, `FigureCanvasGTK4`
- `FigureCanvasMac` (lib/matplotlib/backends/backend_macosx.py) inherits from `FigureCanvasAgg`, `FigureCanvasBase`, `_macosx.FigureCanvas`
- `FigureManagerMac` (lib/matplotlib/backends/backend_macosx.py) inherits from `FigureManagerBase`, `_macosx.FigureManager`
- `NavigationToolbar2Mac` (lib/matplotlib/backends/backend_macosx.py) inherits from `NavigationToolbar2`
- `TimerMac` (lib/matplotlib/backends/backend_macosx.py) inherits from `TimerBase`, `_macosx.Timer`
- `FigureCanvasQT` (lib/matplotlib/backends/backend_qt.py) inherits from `FigureCanvasBase`, `QtWidgets.QWidget`
- `NavigationToolbar2QT` (lib/matplotlib/backends/backend_qt.py) inherits from `NavigationToolbar2`, `QtWidgets.QToolBar`
- `ToolbarQt` (lib/matplotlib/backends/backend_qt.py) inherits from `QtWidgets.QToolBar`, `ToolContainerBase`
- `FigureCanvasQTAgg` (lib/matplotlib/backends/backend_qtagg.py) inherits from `FigureCanvasAgg`, `FigureCanvasQT`
- `FigureCanvasQTCairo` (lib/matplotlib/backends/backend_qtcairo.py) inherits from `FigureCanvasCairo`, `FigureCanvasQT`
- `FigureCanvasTkAgg` (lib/matplotlib/backends/backend_tkagg.py) inherits from `FigureCanvasAgg`, `FigureCanvasTk`
- `FigureCanvasTkCairo` (lib/matplotlib/backends/backend_tkcairo.py) inherits from `FigureCanvasCairo`, `FigureCanvasTk`
- `NavigationToolbar2Wx` (lib/matplotlib/backends/backend_wx.py) inherits from `NavigationToolbar2`, `wx.ToolBar`
- `ToolbarWx` (lib/matplotlib/backends/backend_wx.py) inherits from `ToolContainerBase`, `wx.ToolBar`
- `_FigureCanvasWxBase` (lib/matplotlib/backends/backend_wx.py) inherits from `FigureCanvasBase`, `wx.Panel`
- `FigureCanvasWxAgg` (lib/matplotlib/backends/backend_wxagg.py) inherits from `FigureCanvasAgg`, `_FigureCanvasWxBase`
- `FigureCanvasWxCairo` (lib/matplotlib/backends/backend_wxcairo.py) inherits from `FigureCanvasCairo`, `_FigureCanvasWxBase`
- `PolyQuadMesh` (lib/matplotlib/collections.py) inherits from `PolyCollection`, `_MeshData`
- `QuadMesh` (lib/matplotlib/collections.py) inherits from `Collection`, `_MeshData`
- `ColorizingArtist` (lib/matplotlib/colorizer.py) inherits from `Artist`, `_ScalarMappable`
- `ContourSet` (lib/matplotlib/contour.py) inherits from `Collection`, `ContourLabeler`
- `AnnotationBbox` (lib/matplotlib/offsetbox.py) inherits from `Artist`, `_AnnotationBase`
- `figmplnode` (lib/matplotlib/sphinxext/figmpl_directive.py) inherits from `nodes.Element`, `nodes.General`
- `latex_math` (lib/matplotlib/sphinxext/mathmpl.py) inherits from `nodes.Element`, `nodes.General`
- `_QueryReference` (lib/matplotlib/sphinxext/roles.py) inherits from `nodes.Inline`, `nodes.TextElement`
- `Annotation` (lib/matplotlib/text.py) inherits from `Text`, `Text`, `_AnnotationBase`
- `BlendedAffine2D` (lib/matplotlib/transforms.py) inherits from `Affine2DBase`, `_BlendedMixin`
- `BlendedGenericTransform` (lib/matplotlib/transforms.py) inherits from `Transform`, `_BlendedMixin`
- `AxisLabel` (lib/mpl_toolkits/axisartist/axis_artist.py) inherits from `AttributeCopier`, `LabelBase`
- `Ticks` (lib/mpl_toolkits/axisartist/axis_artist.py) inherits from `AttributeCopier`, `Line2D`

### Diamond Patterns (49 detected)

- `GeoAxes` (galleries/examples/misc/custom_projection.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`
- `HammerAxes` (galleries/examples/misc/custom_projection.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`, `Axes`, `Axes`
- `SkewXAxes` (galleries/examples/specialty_plots/skewt.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`
- `SkewXAxis` (galleries/examples/specialty_plots/skewt.py) — common ancestor(s): `Artist`, `Axis`, `XAxis`, `Axis`, `XAxis`
- `MyApp` (galleries/examples/user_interfaces/embedding_in_wx3_sgskip.py) — common ancestor(s): `App`
- `App` (galleries/examples/user_interfaces/embedding_in_wx4_sgskip.py) — common ancestor(s): `App`
- `App` (galleries/examples/user_interfaces/fourier_demo_wx_sgskip.py) — common ancestor(s): `App`
- `MyApp` (galleries/examples/user_interfaces/mathtext_wx_sgskip.py) — common ancestor(s): `App`
- `App` (galleries/examples/user_interfaces/wxcursor_demo_sgskip.py) — common ancestor(s): `App`
- `XAxis` (lib/matplotlib/axis.py) — common ancestor(s): `Artist`, `Axis`
- `YAxis` (lib/matplotlib/axis.py) — common ancestor(s): `Artist`, `Axis`
- `FigureCanvasGTK3Agg` (lib/matplotlib/backends/backend_gtk3agg.py) — common ancestor(s): `FigureCanvasBase`
- `FigureCanvasGTK3Cairo` (lib/matplotlib/backends/backend_gtk3cairo.py) — common ancestor(s): `FigureCanvasBase`
- `FigureCanvasGTK4Agg` (lib/matplotlib/backends/backend_gtk4agg.py) — common ancestor(s): `FigureCanvasBase`
- `FigureCanvasGTK4Cairo` (lib/matplotlib/backends/backend_gtk4cairo.py) — common ancestor(s): `FigureCanvasBase`
- `FigureCanvasMac` (lib/matplotlib/backends/backend_macosx.py) — common ancestor(s): `FigureCanvasBase`
- `FigureManagerNbAgg` (lib/matplotlib/backends/backend_nbagg.py) — common ancestor(s): `FigureManagerBase`, `FigureManagerWebAgg`
- `FigureCanvasQTAgg` (lib/matplotlib/backends/backend_qtagg.py) — common ancestor(s): `FigureCanvasBase`
- `FigureCanvasQTCairo` (lib/matplotlib/backends/backend_qtcairo.py) — common ancestor(s): `FigureCanvasBase`
- `FigureCanvasTkAgg` (lib/matplotlib/backends/backend_tkagg.py) — common ancestor(s): `FigureCanvasBase`
- `FigureCanvasTkCairo` (lib/matplotlib/backends/backend_tkcairo.py) — common ancestor(s): `FigureCanvasBase`
- `FigureManagerWebAgg` (lib/matplotlib/backends/backend_webagg.py) — common ancestor(s): `FigureManagerBase`, `FigureManagerWebAgg`
- `FigureCanvasWxAgg` (lib/matplotlib/backends/backend_wxagg.py) — common ancestor(s): `FigureCanvasBase`
- `FigureCanvasWxCairo` (lib/matplotlib/backends/backend_wxcairo.py) — common ancestor(s): `FigureCanvasBase`
- `AitoffAxes` (lib/matplotlib/projections/geo.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`, `Axes`, `Axes`
- `GeoAxes` (lib/matplotlib/projections/geo.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`
- `HammerAxes` (lib/matplotlib/projections/geo.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`, `Axes`, `Axes`
- `LambertAxes` (lib/matplotlib/projections/geo.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`, `Axes`, `Axes`
- `MollweideAxes` (lib/matplotlib/projections/geo.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`, `Axes`, `Axes`
- `PolarAxes` (lib/matplotlib/projections/polar.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`
- `RadialAxis` (lib/matplotlib/projections/polar.py) — common ancestor(s): `Artist`, `Axis`, `XAxis`, `Axis`, `XAxis`
- `ThetaAxis` (lib/matplotlib/projections/polar.py) — common ancestor(s): `Artist`, `Axis`, `XAxis`, `Axis`, `XAxis`
- `SubclassAxes` (lib/matplotlib/tests/test_axes.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`
- `SkewXAxes` (lib/matplotlib/tests/test_skew.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`
- `SkewXAxis` (lib/matplotlib/tests/test_skew.py) — common ancestor(s): `Artist`, `Axis`, `XAxis`, `Axis`, `XAxis`
- `AutoLocator` (lib/matplotlib/ticker.py) — common ancestor(s): `Locator`, `MaxNLocator`, `TickHelper`
- `LogitLocator` (lib/matplotlib/ticker.py) — common ancestor(s): `Locator`, `MaxNLocator`, `TickHelper`
- `Axes` (lib/mpl_toolkits/axes_grid1/mpl_axes.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`
- `Axes` (lib/mpl_toolkits/axisartist/axislines.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`
- `AxesZero` (lib/mpl_toolkits/axisartist/axislines.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`
- `FixedAxisArtistHelper` (lib/mpl_toolkits/axisartist/floating_axes.py) — common ancestor(s): `_AxisArtistHelperBase`, `_FloatingAxisArtistHelperBase`, `FloatingAxisArtistHelper`
- `FloatingAxisArtistHelper` (lib/mpl_toolkits/axisartist/floating_axes.py) — common ancestor(s): `_AxisArtistHelperBase`, `_FloatingAxisArtistHelperBase`, `FloatingAxisArtistHelper`
- `GridHelperCurveLinear` (lib/mpl_toolkits/axisartist/floating_axes.py) — common ancestor(s): `GridHelperBase`, `GridHelperCurveLinear`
- `MaxNLocator` (lib/mpl_toolkits/axisartist/grid_finder.py) — common ancestor(s): `Locator`, `MaxNLocator`, `TickHelper`
- `Axes3D` (lib/mpl_toolkits/mplot3d/axes3d.py) — common ancestor(s): `Artist`, `Axes`, `_AxesBase`
- `Axis` (lib/mpl_toolkits/mplot3d/axis3d.py) — common ancestor(s): `Artist`, `Axis`, `XAxis`, `Axis`, `XAxis`
- `XAxis` (lib/mpl_toolkits/mplot3d/axis3d.py) — common ancestor(s): `Artist`, `Axis`
- `YAxis` (lib/mpl_toolkits/mplot3d/axis3d.py) — common ancestor(s): `Artist`, `Axis`
- `ZAxis` (lib/mpl_toolkits/mplot3d/axis3d.py) — common ancestor(s): `Artist`, `Axis`


---

## Snapshot History

No snapshots found. Run `codekg snapshot save <version>` to capture one.


---

## Appendix: Orphaned Code

Functions with zero callers (potential dead code):

| Function | Module | Lines |
|----------|--------|-------|
| `deprecate()` | lib/matplotlib/_api/deprecation.py | 91 |
| `wrapper()` | lib/matplotlib/_api/deprecation.py | 32 |
| `_deprecated_property()` | lib/matplotlib/_api/deprecation.py | 20 |
| `test_load_old_api()` | lib/matplotlib/tests/test_backend_template.py | 9 |
| `wrapper()` | lib/matplotlib/_api/deprecation.py | 3 |
| `_deprecated_parameter_class()` | lib/matplotlib/_api/deprecation.py | 2 |
| `_old_init()` | lib/mpl_toolkits/mplot3d/axis3d.py | 2 |
| `empty_with_docstring()` | lib/matplotlib/_api/deprecation.py | 0 |
| `_meth()` | lib/matplotlib/tests/test_api.py | 0 |
---

## CodeRank -- Global Structural Importance

Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths excluded). Scores are normalized to sum to 1.0. This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.000460 | function | `_copy_docstring_and_deprecators` | lib/matplotlib/pyplot.py |
| 2 | 0.000287 | function | `gca` | lib/matplotlib/pyplot.py |
| 3 | 0.000233 | method | `LockableBbox.get_points` | lib/matplotlib/transforms.py |
| 4 | 0.000194 | function | `gcf` | lib/matplotlib/pyplot.py |
| 5 | 0.000170 | function | `_dispatch` | lib/matplotlib/dviread.py |
| 6 | 0.000170 | method | `TransformNode.invalidate` | lib/matplotlib/transforms.py |
| 7 | 0.000154 | function | `set_cmap` | lib/matplotlib/pyplot.py |
| 8 | 0.000153 | method | `CompositeGenericTransform._invalidate_internal` | lib/matplotlib/transforms.py |
| 9 | 0.000130 | function | `figure` | lib/matplotlib/pyplot.py |
| 10 | 0.000097 | function | `_add_pyplot_note` | lib/matplotlib/pyplot.py |
| 11 | 0.000089 | method | `MultiNorm._changed` | lib/matplotlib/colors.py |
| 12 | 0.000080 | method | `Artist.stale` | lib/matplotlib/artist.py |
| 13 | 0.000073 | class | `Bbox` | lib/matplotlib/transforms.py |
| 14 | 0.000070 | method | `ParserState.font` | lib/matplotlib/_mathtext.py |
| 15 | 0.000069 | method | `Colorbar.long_axis` | lib/matplotlib/colorbar.py |
| 16 | 0.000068 | method | `MarkerStyle.get_fillstyle` | lib/matplotlib/markers.py |
| 17 | 0.000065 | class | `TaggedValue` | galleries/examples/units/basic_units.py |
| 18 | 0.000063 | function | `select_step` | lib/mpl_toolkits/axisartist/angle_helper.py |
| 19 | 0.000062 | class | `Name` | lib/matplotlib/backends/backend_pdf.py |
| 20 | 0.000061 | method | `BivarColormapFromImage._init` | lib/matplotlib/colors.py |

---

## Concern-Based Hybrid Ranking

Top structurally-dominant nodes per architectural concern (0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).

### Configuration Loading Initialization Setup

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | function | `setup` | doc/conf.py |
| 2 | 0.7335 | method | `Sfnt.__init__` | tools/subset.py |
| 3 | 0.7299 | method | `BackendRegistry._ensure_entry_points_loaded` | lib/matplotlib/backends/registry.py |
| 4 | 0.7273 | function | `setup` | lib/matplotlib/testing/__init__.py |
| 5 | 0.7215 | function | `_setup_new_guiapp` | lib/matplotlib/cbook.py |

### Data Persistence Storage Database

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | function | `download_or_cache` | tools/cache_zenodo_svg.py |
| 2 | 0.7468 | method | `ImageMagickBase.isAvailable` | lib/matplotlib/animation.py |
| 3 | 0.6888 | class | `DataManager` | galleries/examples/user_interfaces/gtk4_spreadsheet_sgskip.py |
| 5 | 0.0378 | function | `_get_xdg_cache_dir` | tools/cache_zenodo_svg.py |

### Query Search Retrieval Semantic

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `_QueryReference.to_query_string` | lib/matplotlib/sphinxext/roles.py |
| 2 | 0.7342 | function | `_visit_query_reference_node` | lib/matplotlib/sphinxext/roles.py |
| 3 | 0.7288 | function | `compare` | galleries/examples/images_contours_and_fields/shading_example.py |
| 4 | 0.7248 | method | `_LuatexKpsewhich.search` | lib/matplotlib/dviread.py |
| 5 | 0.7199 | function | `get_paged_request` | tools/gh_api.py |

### Graph Traversal Node Edge

| Rank | Score | Kind | Name | Module |
|------|-------|------|------|--------|
| 1 | 0.75 | method | `Triangulation.edges` | lib/matplotlib/tri/_triangulation.py |
| 2 | 0.7418 | method | `_Edge_integer.ge` | lib/matplotlib/ticker.py |
| 3 | 0.7396 | method | `BoundaryNorm.__init__` | lib/matplotlib/colors.py |
| 4 | 0.7368 | method | `Path.__init__` | lib/matplotlib/path.py |
| 5 | 0.7366 | method | `RectangleSelector.edge_centers` | lib/matplotlib/widgets.py |



---

*Report generated by CodeKG Thorough Analysis Tool — analysis completed in 58.3s*
