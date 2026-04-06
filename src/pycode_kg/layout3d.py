#!/usr/bin/env python3
"""
layout3d.py — Pluggable 3-D layout engine for the PyCodeKG knowledge graph.

Provides an abstract :class:`Layout3D` base class and two concrete
implementations:

- :class:`AlliumLayout`: Each module is rendered as a Giant Allium plant
  (a vertical stem with a Fibonacci-sphere "head" of classes and functions).
  Modules are arranged in a Fibonacci annulus in the XY plane.

- :class:`LayerCakeLayout`: Node kind determines the Z level (modules at
  the bottom, classes above, functions/methods at the top).  XY positions
  are spread via a golden-angle spiral within each layer.

The Fibonacci utilities (``fibonacci_sphere``, ``fibonacci_annulus``) are
adapted from *repo_vis* ``pkg_visualizer/utility.py``
(Eric G. Suchanek, PhD — https://github.com/Suchanek/repo_vis).

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

# ---------------------------------------------------------------------------
# Fibonacci spatial utilities  (adapted from repo_vis/pkg_visualizer/utility.py)
# ---------------------------------------------------------------------------


def fibonacci_sphere(
    samples: int,
    radius: float = 1.0,
    center: np.ndarray | None = None,
) -> list[np.ndarray]:
    """
    Distribute *samples* points uniformly on a sphere using the Fibonacci spiral.

    Adapted from ``utility.fibonacci_sphere`` in *repo_vis*.

    :param samples: Number of points to generate.
    :param radius: Sphere radius.
    :param center: Centre of the sphere (default: origin).
    :return: List of 3-D coordinate arrays.
    """
    if center is None:
        center = np.zeros(3)
    if samples <= 0:
        return []
    if samples == 1:
        return [center + radius * np.array([0.0, 0.0, 1.0])]

    phi = np.pi * (3.0 - np.sqrt(5.0))  # golden angle in radians
    points: list[np.ndarray] = []
    for i in range(samples):
        y = 1.0 - (i / float(samples - 1)) * 2.0
        r_at_y = np.sqrt(max(0.0, 1.0 - y * y))
        theta = phi * i
        x = np.cos(theta) * r_at_y
        z = np.sin(theta) * r_at_y
        points.append(center + radius * np.array([x, y, z]))
    return points


def fibonacci_annulus(
    samples: int,
    inner_radius: float = 1.0,
    outer_radius: float = 2.0,
    center: np.ndarray | None = None,
    z_thickness: float = 0.2,
) -> list[np.ndarray]:
    """
    Distribute *samples* points in a flat annular ring in the XY plane.

    A small Z jitter (``z_thickness``) adds visual depth when non-zero.
    Adapted from ``utility.fibonacci_annulus`` in *repo_vis*.

    :param samples: Number of points to generate.
    :param inner_radius: Inner radius of the annulus.
    :param outer_radius: Outer radius of the annulus.
    :param center: Centre of the annulus (default: origin).
    :param z_thickness: Half-range of Z jitter applied to each point.
    :return: List of 3-D coordinate arrays.
    """
    if center is None:
        center = np.zeros(3)
    if samples <= 0:
        return []
    if samples == 1:
        mid = (inner_radius + outer_radius) / 2.0
        return [center + np.array([mid, 0.0, 0.0])]

    phi = np.pi * (3.0 - np.sqrt(5.0))
    r_range = outer_radius - inner_radius
    r_step = r_range / max(samples - 1, 1)
    rng = np.random.default_rng(42)  # deterministic jitter seed

    points: list[np.ndarray] = []
    for i in range(samples):
        r = inner_radius + i * r_step
        theta = phi * i
        x = np.cos(theta) * r
        y = np.sin(theta) * r
        z = (rng.random() * 2.0 - 1.0) * z_thickness
        points.append(center + np.array([x, y, z]))
    return points


def _golden_spiral_2d(
    samples: int,
    radius: float = 1.0,
    center: np.ndarray | None = None,
    z: float = 0.0,
) -> list[np.ndarray]:
    """
    Place *samples* points in the XY plane using a golden-angle disc spiral.

    :param samples: Number of points.
    :param radius: Outer radius of the disc.
    :param center: XY centre (Z component ignored; overridden by *z*).
    :param z: Fixed Z coordinate for all output points.
    :return: List of 3-D coordinate arrays.
    """
    if center is None:
        center = np.zeros(3)
    if samples <= 0:
        return []

    phi = np.pi * (3.0 - np.sqrt(5.0))
    points: list[np.ndarray] = []
    for i in range(samples):
        r = radius * np.sqrt(i / max(samples - 1, 1))
        theta = phi * i
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        points.append(center + np.array([x, y, z]))
    return points


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------


@dataclass
class LayoutNode:
    """
    Thin wrapper around a node dict from :class:`~pycode_kg.store.GraphStore`.

    :param id: Stable node identifier (e.g. ``mod:src/foo.py``).
    :param kind: Node kind — ``module``, ``class``, ``function``, ``method``,
        or ``symbol``.
    :param name: Short name of the node.
    :param module_path: Source module path (may be ``None`` for symbol stubs).
    :param docstring: Raw docstring text (may be ``None``).
    :param lineno: First source line number (may be ``None``).
    :param end_lineno: Last source line number (may be ``None``).
    """

    id: str
    kind: str
    name: str
    module_path: str | None = None
    docstring: str | None = None
    lineno: int | None = None
    end_lineno: int | None = None

    @classmethod
    def from_dict(cls, d: dict) -> LayoutNode:
        """Construct from a GraphStore node dict.

        :param d: Dict with keys ``id``, ``kind``, ``name``, etc.
        :return: New :class:`LayoutNode`.
        """
        return cls(
            id=d["id"],
            kind=d["kind"],
            name=d["name"],
            module_path=d.get("module_path"),
            docstring=d.get("docstring"),
            lineno=d.get("lineno"),
            end_lineno=d.get("end_lineno"),
        )

    @property
    def line_count(self) -> int:
        """Approximate source size in lines (0 if unknown).

        :return: ``end_lineno - lineno`` or 0.
        """
        if self.lineno and self.end_lineno:
            return max(0, self.end_lineno - self.lineno)
        return 0


@dataclass
class LayoutEdge:
    """
    Thin wrapper around an edge dict from :class:`~pycode_kg.store.GraphStore`.

    :param src: Source node ID.
    :param rel: Relation type — ``CONTAINS``, ``CALLS``, ``IMPORTS``,
        ``INHERITS``.
    :param dst: Destination node ID.
    """

    src: str
    rel: str
    dst: str

    @classmethod
    def from_dict(cls, d: dict) -> LayoutEdge:
        """Construct from a GraphStore edge dict.

        :param d: Dict with keys ``src``, ``rel``, ``dst``.
        :return: New :class:`LayoutEdge`.
        """
        return cls(src=d["src"], rel=d["rel"], dst=d["dst"])


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class Layout3D(ABC):
    """
    Abstract base class for 3-D graph layout strategies.

    Subclasses implement :meth:`compute` to assign a 3-D position to every
    node, returning a ``{node_id: np.ndarray([x, y, z])}`` mapping that the
    :class:`~pycode_kg.viz3d.KGViz3D` renderer consumes.
    """

    @abstractmethod
    def compute(
        self,
        nodes: list[LayoutNode],
        edges: list[LayoutEdge],
    ) -> dict[str, np.ndarray]:
        """
        Compute 3-D positions for all *nodes*.

        :param nodes: All nodes in the graph.
        :param edges: All edges in the graph (used to derive hierarchy).
        :return: Mapping from node ID to ``[x, y, z]`` position.
        """
        ...


# ---------------------------------------------------------------------------
# AlliumLayout
# ---------------------------------------------------------------------------


class AlliumLayout(Layout3D):
    """
    Allium-plant layout: each module is visualised as a Giant Allium flower.

    Spatial structure:

    - **Stem base** — module node sits at XY position in a Fibonacci annulus
      at ``Z = 0``.
    - **Head** — classes and top-level functions are distributed on a
      Fibonacci sphere centred at the stem apex (``Z = stem_height``).
      Head radius scales with ``sqrt(n_children)``.
    - **Florets** — methods orbit their parent class on a smaller Fibonacci
      sphere, slightly above the head.
    - **Orphans** — nodes with no CONTAINS parent cluster on a small sphere
      at the origin.

    Multiple module-alliums are arranged in a Fibonacci annulus in the XY
    plane so they are evenly spaced regardless of count.

    Inspired by :class:`GiantAllium` in *repo_vis/pkg_visualizer/plants3d.py*.

    :param stem_height: Height of each allium stem (Z offset of the head).
    :param base_head_radius: Minimum radius for the Fibonacci sphere head.
    :param method_orbit_radius: Base radius for method sub-spheres.
    :param annulus_inner_radius: Inner radius of the module placement ring.
    :param annulus_outer_radius: Minimum outer radius (auto-scaled for large graphs).
    """

    def __init__(
        self,
        stem_height: float = 8.0,
        base_head_radius: float = 2.0,
        method_orbit_radius: float = 0.8,
        annulus_inner_radius: float = 8.0,
        annulus_outer_radius: float = 20.0,
    ) -> None:
        """Initialise layout parameters.

        :param stem_height: Vertical height of each allium stem.
        :param base_head_radius: Minimum allium head sphere radius.
        :param method_orbit_radius: Base orbit radius for methods.
        :param annulus_inner_radius: Inner radius for module ring placement.
        :param annulus_outer_radius: Minimum outer radius for module ring.
        """
        self.stem_height = stem_height
        self.base_head_radius = base_head_radius
        self.method_orbit_radius = method_orbit_radius
        self.annulus_inner_radius = annulus_inner_radius
        self.annulus_outer_radius = annulus_outer_radius

    def compute(
        self,
        nodes: list[LayoutNode],
        edges: list[LayoutEdge],
    ) -> dict[str, np.ndarray]:
        """
        Compute allium-plant 3-D positions for all nodes.

        :param nodes: All nodes in the graph.
        :param edges: All edges (``CONTAINS`` used to derive hierarchy).
        :return: Mapping from node ID to ``[x, y, z]`` position.
        """
        # Build CONTAINS hierarchy: child_id -> parent_id, parent_id -> [child_ids]
        parent: dict[str, str] = {}
        children: dict[str, list[str]] = {}
        for e in edges:
            if e.rel == "CONTAINS":
                parent[e.dst] = e.src
                children.setdefault(e.src, []).append(e.dst)

        node_by_id: dict[str, LayoutNode] = {n.id: n for n in nodes}
        positions: dict[str, np.ndarray] = {}

        # Module nodes form the allium stems
        modules = [n for n in nodes if n.kind == "module"]
        if not modules:
            # Fallback: treat nodes without a CONTAINS parent as pseudo-modules
            modules = [n for n in nodes if n.id not in parent]

        n_mods = len(modules)
        inner = self.annulus_inner_radius
        # Scale outer radius so stems don't crowd each other
        outer = max(self.annulus_outer_radius, inner + n_mods * 2.5)

        mod_positions = fibonacci_annulus(
            n_mods,
            inner_radius=inner,
            outer_radius=outer,
            center=np.zeros(3),
            z_thickness=0.0,  # flat ring — alliums stand vertically
        )

        for mod_node, mod_pos in zip(modules, mod_positions):
            positions[mod_node.id] = np.array(mod_pos)
            stem_apex = np.array([mod_pos[0], mod_pos[1], self.stem_height])

            # Direct children (classes, top-level functions)
            direct_ids = children.get(mod_node.id, [])
            direct = [node_by_id[cid] for cid in direct_ids if cid in node_by_id]
            n_direct = len(direct)
            if not direct:
                continue

            # Head radius scales with child count
            head_r = self.base_head_radius + np.sqrt(n_direct) * 0.4
            head_positions = fibonacci_sphere(n_direct, radius=head_r, center=stem_apex)

            for child, child_pos in zip(direct, head_positions):
                positions[child.id] = np.array(child_pos)

                # Grandchildren (methods) orbit their parent class
                grand_ids = children.get(child.id, [])
                grand = [node_by_id[gid] for gid in grand_ids if gid in node_by_id]
                n_grand = len(grand)
                if not grand:
                    continue

                method_r = self.method_orbit_radius + np.sqrt(n_grand) * 0.15
                method_positions = fibonacci_sphere(
                    n_grand, radius=method_r, center=np.array(child_pos)
                )
                for gc, gc_pos in zip(grand, method_positions):
                    positions[gc.id] = np.array(gc_pos)

        # Orphan nodes: anything not yet placed (symbols, unrooted nodes)
        orphans = [n for n in nodes if n.id not in positions]
        if orphans:
            orphan_positions = fibonacci_sphere(len(orphans), radius=3.0, center=np.zeros(3))
            for n, pos in zip(orphans, orphan_positions):
                positions[n.id] = np.array(pos)

        return positions


# ---------------------------------------------------------------------------
# LayerCakeLayout
# ---------------------------------------------------------------------------

# Z level per node kind
_KIND_ZLEVEL: dict[str, int] = {
    "module": 0,
    "class": 1,
    "function": 2,
    "method": 2,
    "symbol": 3,
}


class LayerCakeLayout(Layout3D):
    """
    Stratified layout: node *kind* determines the Z layer; XY positions use a
    golden-angle disc spiral within each layer.

    Layers (bottom to top):

    - **Z = 0** — modules
    - **Z = layer_gap** — classes
    - **Z = 2 × layer_gap** — functions and methods
    - **Z = 3 × layer_gap** — symbol stubs

    Cross-cutting edges (``CALLS``, ``IMPORTS``, ``INHERITS``) arc between
    layers, making structural coupling immediately visible from any angle.

    :param layer_gap: Vertical distance between adjacent layers.
    :param disc_radius: Base outer radius of the golden-angle disc per layer.
    """

    def __init__(
        self,
        layer_gap: float = 12.0,
        disc_radius: float = 28.0,
    ) -> None:
        """Initialise layout parameters.

        :param layer_gap: Vertical separation between layers.
        :param disc_radius: Base XY spread radius per layer disc.
        """
        self.layer_gap = layer_gap
        self.disc_radius = disc_radius

    def compute(
        self,
        nodes: list[LayoutNode],
        edges: list[LayoutEdge],
    ) -> dict[str, np.ndarray]:
        """
        Compute layer-cake 3-D positions for all nodes.

        :param nodes: All nodes in the graph.
        :param edges: Unused by this layout (present for API compatibility).
        :return: Mapping from node ID to ``[x, y, z]`` position.
        """
        # Group nodes by Z layer
        layers: dict[int, list[LayoutNode]] = {}
        for n in nodes:
            level = _KIND_ZLEVEL.get(n.kind, 3)
            layers.setdefault(level, []).append(n)

        positions: dict[str, np.ndarray] = {}
        n_total = max(len(nodes), 1)

        for level, layer_nodes in layers.items():
            z = level * self.layer_gap
            # Scale disc radius proportionally to the layer's node count
            r = self.disc_radius * np.sqrt(len(layer_nodes) / n_total)
            r = max(r, 4.0)  # minimum spread
            pts = _golden_spiral_2d(len(layer_nodes), radius=r, z=z)
            for n, pt in zip(layer_nodes, pts):
                positions[n.id] = pt

        return positions
