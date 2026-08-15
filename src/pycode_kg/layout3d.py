#!/usr/bin/env python3
"""
PyCodeKG's 3-D layout bindings over the shared layout engine.

The engine itself lives in :mod:`kg_utils.viz3d`, shared with every other KG
module — GutenbergKG was already importing it from here, paying a full
``pycode-kg`` dependency for five symbols that have nothing to do with parsing
Python.  What stays here is the part that is genuinely specific to a *code*
graph: which node kinds occupy which Z level, which comes from
:mod:`pycode_kg.theme`.

Everything is re-exported so existing callers do not need to know where the
implementation moved.

The Fibonacci utilities (``fibonacci_sphere``, ``fibonacci_annulus``) are
adapted from *repo_vis* ``pkg_visualizer/utility.py``
(Eric G. Suchanek, PhD — https://github.com/Suchanek/repo_vis).

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

from __future__ import annotations

from kg_utils.viz3d import (
    AlliumLayout,
    Layout3D,
    LayoutEdge,
    LayoutNode,
    fibonacci_annulus,
    fibonacci_sphere,
    golden_spiral_2d,
)
from kg_utils.viz3d import FunnelLayout as _SharedFunnelLayout

from pycode_kg import theme

__all__ = [
    "AlliumLayout",
    "FunnelLayout",
    "Layout3D",
    "LayoutEdge",
    "LayoutNode",
    "fibonacci_annulus",
    "fibonacci_sphere",
    "golden_spiral_2d",
]


class FunnelLayout(_SharedFunnelLayout):
    """Funnel layout stratified by *code* node kind.

    The shared engine takes the kind→Z-level mapping as an argument, because
    only the domain knows its own hierarchy — modules at the bottom, then
    classes, then functions and methods, with symbol stubs on top is a fact
    about Python code, not about knowledge graphs.  This subclass supplies
    that mapping from :mod:`pycode_kg.theme`, so the layout engine, the 3-D
    viewer and the 2-D explorer keep sharing one definition.

    Unknown kinds land on the symbol level, matching
    :func:`pycode_kg.theme.resolve_kind`, which collapses anything the palette
    does not recognise to ``symbol``.

    :param layer_gap: Vertical distance between adjacent layers.
    :param node_spacing: Spacing multiplier — larger spreads layers out more.
    :param kwargs: Forwarded to :class:`kg_utils.viz3d.FunnelLayout`; the
        theme-derived defaults are only applied to keys left unset.
    """

    def __init__(
        self,
        layer_gap: float = 12.0,
        node_spacing: float = 2.0,
        **kwargs,
    ) -> None:
        """Initialise layout parameters, defaulting the maps from the theme.

        :param layer_gap: Vertical separation between layers.
        :param node_spacing: Controls minimum gap between node surfaces.
        :param kwargs: Overrides forwarded to the shared layout.
        """
        kwargs.setdefault("zlevels", theme.KIND_ZLEVEL)
        kwargs.setdefault("level_sizes", theme.LEVEL_NODE_SIZE)
        kwargs.setdefault("default_level", theme.KIND_ZLEVEL[theme.UNKNOWN_KIND])
        super().__init__(layer_gap=layer_gap, node_spacing=node_spacing, **kwargs)
