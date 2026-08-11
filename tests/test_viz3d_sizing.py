"""
test_viz3d_sizing.py

Guards the 3-D centrality sizing contract.  Requires the ``viz3d`` extra.

Unlike the 2-D renderer, the 3-D viewer places nodes at positions fixed by the
layout, so node radius has a *spatial budget*: a node that outgrows the room the
layout gave it occludes its neighbours.  An earlier version used an absolute
radius range (0.35–2.4) that ignored this and fused each allium head into a
solid ball, hiding the stem and every CALLS arc inside it.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pyvista")
pytest.importorskip("PyQt5")

import numpy as np  # noqa: E402

from pycode_kg import theme  # noqa: E402
from pycode_kg.layout3d import AlliumLayout, LayoutEdge, LayoutNode  # noqa: E402
from pycode_kg.viz3d import CENTRALITY_SCALE_RANGE, KIND_SIZE  # noqa: E402


def _head_radius(n_children: int) -> float:
    """Measure the real allium head radius for an *n_children* module.

    Measured from the layout rather than restated as a literal.  The formula
    lives in :mod:`kg_utils.viz3d` now, so a coefficient change there must move
    this budget with it — a hardcoded copy would keep passing while quietly
    describing a head that no longer exists.

    :param n_children: Number of direct children on the module.
    :return: Distance from the stem apex to a child, in world units.
    """
    root = LayoutNode("mod", "module", "mod")
    kids = [LayoutNode(f"fn:{i}", "function", str(i)) for i in range(n_children)]
    edges = [LayoutEdge("mod", "CONTAINS", k.id) for k in kids]

    layout = AlliumLayout()
    pos = layout.compute([root, *kids], edges)
    apex = np.array([pos["mod"][0], pos["mod"][1], layout.stem_height])
    return float(np.linalg.norm(pos["fn:0"] - apex))


SMALL_HEAD_RADIUS = _head_radius(4)  # a 4-child module — the tight case


def test_scale_range_is_a_multiplier_around_unity() -> None:
    """The range must straddle 1.0 so uniform sizing is the midpoint case."""
    lo, hi = CENTRALITY_SCALE_RANGE
    assert 0 < lo < 1.0 < hi


def test_scaling_stays_within_the_layout_budget() -> None:
    """Even the most central function must fit inside a small allium head.

    Functions are the numerous kind that fill the head sphere, so they are the
    ones that cause occlusion when oversized.
    """
    _, hi = CENTRALITY_SCALE_RANGE
    largest_function = KIND_SIZE["function"] * hi
    assert largest_function < SMALL_HEAD_RADIUS / 2, (
        f"a max-centrality function has radius {largest_function}, which crowds "
        f"a head of radius {SMALL_HEAD_RADIUS}"
    )


def test_scaling_never_shrinks_a_node_to_nothing() -> None:
    """The least central node must stay pickable."""
    lo, _ = CENTRALITY_SCALE_RANGE
    assert min(KIND_SIZE.values()) * lo > 0.15


def test_kind_is_carried_by_shape_and_colour_not_size() -> None:
    """Size is free to encode centrality because kind is encoded elsewhere.

    A max-centrality method does outgrow a min-centrality module, and that is
    accepted: node *shape* (box / octahedron / cylinder / icosahedron) and
    *colour* carry the kind, so size can be spent entirely on centrality.
    Preserving a strict size ordering across kinds would require a multiplier
    range narrower than the smallest adjacent-kind ratio (1.25), which is too
    weak to read as an encoding at all.
    """
    lo, hi = CENTRALITY_SCALE_RANGE
    adjacent_ratio = KIND_SIZE["module"] / KIND_SIZE["class"]
    assert hi / lo > adjacent_ratio

    # The compensating guarantee: every kind has a distinct colour and shape.
    assert len(set(theme.KIND_COLOR.values())) == len(theme.KIND_COLOR)
    assert theme.KIND_SHAPE["module"] != theme.KIND_SHAPE["method"]


def test_uniform_sizing_is_unchanged_by_the_scale_range() -> None:
    """Without a metric, radii are exactly the per-kind constants."""
    assert KIND_SIZE == dict(theme.KIND_SIZE)
