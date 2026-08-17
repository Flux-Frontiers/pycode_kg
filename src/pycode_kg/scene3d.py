#!/usr/bin/env python3
"""
Grow a code graph as an organic tree.

The funnel and allium layouts in :mod:`pycode_kg.layout3d` place nodes on a
lattice.  This module does the other thing: it *grows* a branching skeleton
toward the code, by space colonization, so a repository reads as wood rather
than as a scatter plot.  The growth engine itself lives in
:mod:`kg_utils.viz3d.organic`, shared with every other KG module; what belongs
here is the part only a *code* graph knows — which nodes are the trunk, which
are limbs, and which are the crown the branches have to reach.

The mapping::

    repository            trunk, standing at the origin
    module                limb station on a golden-angle spiral up the trunk
    class / function /    crown attractor — a leaf the wood must grow to reach
      method

That ordering is the point.  Attractors are not decoration: every leaf is a
real definition at a real position, so the canopy's shape *is* the shape of
the codebase.  Limb thickness follows from it for free, because
:func:`~kg_utils.viz3d.organic.pipe_radii` sizes a branch from the number of
tips it carries — a fat limb is a module with a lot of code in it, and it is
fat for that reason and no other.

Foliage is tinted by node kind (:data:`pycode_kg.theme.FOLIAGE_KINDS`) rather
than by season, so a module's cluster shows its composition at a glance.

The renderer is deliberately camera-agnostic: it composes a scene into a
plotter and stops.  Framing for a flat screenshot, for a Looking Glass quilt,
or for the Qt viewer is the caller's business — see
:mod:`pycode_kg.cli.cmd_quilt`.

Author: Eric G. Suchanek, PhD
Last Revision: 2026-08-14

License: Elastic 2.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from kg_utils.viz3d import (
    Layout3D,
    LayoutEdge,
    LayoutNode,
    Skeleton,
    fibonacci_sphere,
    grow_tree,
    leaf_facing,
    leaf_glyphs,
    oriented_cluster,
    seed_from_key,
    tree_mesh,
)

from pycode_kg import theme

if TYPE_CHECKING:  # pragma: no cover - import cycle guard for type checkers only
    import pyvista as pv

__all__ = [
    "CodeTreeLayout",
    "TreeScene",
    "build_code_tree_scene",
    "crown_kinds",
]

#: Golden angle, the divergence that keeps successive limbs from shadowing
#: each other.  Same constant nature uses for phyllotaxis.
GOLDEN_ANGLE: float = np.pi * (3.0 - np.sqrt(5.0))


def crown_kinds() -> frozenset[str]:
    """Return the render kinds that become crown attractors.

    :return: Frozen set of kinds, derived from :data:`pycode_kg.theme.FOLIAGE_KINDS`.
    """
    return frozenset(theme.FOLIAGE_KINDS)


@dataclass
class CodeTreeLayout(Layout3D):
    """Crown layout for a code graph — the schematic the wood grows toward.

    Produces positions for every node plus the trunk/limb line segments, which
    :func:`build_code_tree_scene` uses as growth targets.  Nothing here draws;
    the result is pure geometry, so it is testable without PyVista.

    :param trunk_scale: Trunk height per doubling of the definition count.
    :param max_trunk_height: Cap, so a large repo does not grow off-screen.
    :param crown_ratio: Limb reach as a fraction of trunk height.  Crown width
        is tied to height rather than to the module count so the silhouette
        keeps its proportions across repositories of any size — a free limb
        length makes a 60-module repo grow as a leggy weed.
    :param branch_radius: Floor on limb length, for very short trunks.
    :param leaf_radius: Base radius of a module's leaf cluster.
    :param up_bias: Upward blend for leaf-cluster facing, see :func:`~kg_utils.viz3d.leaf_facing`.
    :param limb_start: Height of the lowest limb as a fraction of the trunk.
        The bare trunk below it is what reads as a trunk rather than a bottle
        brush, and it is also the ceiling for :meth:`trunk_guides`.
    """

    trunk_scale: float = 4.0
    max_trunk_height: float = 45.0
    crown_ratio: float = 0.45
    branch_radius: float = 5.0
    leaf_radius: float = 1.5
    up_bias: float = 0.6
    limb_start: float = 0.30

    #: Trunk/limb segments as ``(start, end)`` pairs, filled by :meth:`compute`.
    branch_lines: list[tuple[np.ndarray, np.ndarray]] = field(default_factory=list)
    #: Trunk height chosen for the most recent :meth:`compute` call.
    trunk_height: float = 0.0

    def trunk_guides(self, n_points: int = 10) -> np.ndarray:
        """Attractors up the trunk axis, so the wood grows a trunk first.

        Space colonization only knows the targets it is given.  With targets
        only in the crown, the root bridges straight to whichever one is
        nearest and the "trunk" ends up a stem wandering off at an angle.
        Seeding the axis below the lowest limb makes the leader climb before
        it branches.

        These are growth targets only — they are never rendered as foliage,
        which is why the caller passes them to
        :func:`~kg_utils.viz3d.organic.grow_tree` but not to
        :func:`~kg_utils.viz3d.organic.leaf_glyphs`.

        :param n_points: Number of guide points.
        :return: ``(n_points, 3)`` positions, or an empty array if the trunk
            has no height yet.
        """
        if self.trunk_height <= 0.0 or n_points <= 0:
            return np.empty((0, 3))
        # Stop short of the lowest limb: a guide level with the branching
        # grows a bare pole up through the base of the canopy.
        z = np.linspace(
            self.trunk_height * 0.06,
            self.trunk_height * self.limb_start * 0.85,
            n_points,
        )
        return np.column_stack([np.zeros_like(z), np.zeros_like(z), z])

    def compute(
        self,
        nodes: list[LayoutNode],
        edges: list[LayoutEdge],  # noqa: ARG002 - containment comes from module_path
    ) -> dict[str, np.ndarray]:
        """Place the trunk, the module limbs, and every definition in the crown.

        Containment is taken from each node's ``module_path`` rather than from
        ``CONTAINS`` edges: the path is present on every node, survives an
        unresolved edge, and is exactly the grouping a reader means by "which
        module is this in".

        :param nodes: Nodes to lay out.
        :param edges: Unused — containment comes from ``module_path``.
        :return: Mapping of node ID to ``[x, y, z]``.
        """
        self.branch_lines = []
        positions: dict[str, np.ndarray] = {}

        crown = crown_kinds()
        by_module: dict[str, list[LayoutNode]] = {}
        module_nodes: dict[str, LayoutNode] = {}

        for node in nodes:
            kind = theme.resolve_kind(node.kind, node.name)
            path = node.module_path or ""
            if kind == "module":
                module_nodes[path] = node
            elif kind in crown:
                by_module.setdefault(path, []).append(node)

        # Every module that holds code gets a limb, in a stable order so the
        # tree is reproducible across runs.
        limb_paths = sorted(set(by_module) | set(module_nodes))
        n_defs = sum(len(v) for v in by_module.values())

        self.trunk_height = min(
            self.trunk_scale * max(1.0, float(np.log2(1 + n_defs))),
            self.max_trunk_height,
        )
        n_limbs = max(len(limb_paths), 1)
        branch_length = max(self.branch_radius, self.trunk_height * self.crown_ratio)

        # Limb reach carries information: the biggest module pushes out the
        # full length, the smallest stays tucked against the trunk.  Without
        # this every limb ends at nearly the same radius and the crown is a
        # hollow shell — which colonization then wanders around the inside of
        # instead of filling.
        biggest = max((len(v) for v in by_module.values()), default=1)

        for i, path in enumerate(limb_paths):
            t = i / max(n_limbs - 1, 1)
            z = self.trunk_height * (self.limb_start + 0.65 * t)
            angle = i * GOLDEN_ANGLE
            # Taper: upper limbs are shorter, so the silhouette closes.
            taper = 1.0 - (z / max(self.trunk_height, 1e-9)) * 0.4
            reach = 0.35 + 0.65 * float(np.sqrt(len(by_module.get(path, [])) / biggest))
            radius = branch_length * taper * reach
            tip = np.array([radius * np.cos(angle), radius * np.sin(angle), z])
            axis = np.array([0.0, 0.0, z])
            self.branch_lines.append((axis, tip))

            module_node = module_nodes.get(path)
            if module_node is not None:
                positions[module_node.id] = tip

            members = by_module.get(path, [])
            if not members:
                continue
            cluster_r = self.leaf_radius + float(np.sqrt(len(members))) * 0.12
            facing = leaf_facing(tip - axis, self.up_bias)
            for node, pos in zip(
                members,
                oriented_cluster(len(members), tip, facing, cluster_r),
                strict=True,
            ):
                positions[node.id] = pos

        # Anything left (symbol stubs, nodes with no module) rings the base so
        # it is visible without being mistaken for foliage.
        placed = set(positions)
        orphans = [n for n in nodes if n.id not in placed]
        for node, pos in zip(
            orphans,
            fibonacci_sphere(len(orphans), radius=max(branch_length * 0.4, 1.0)),
            strict=True,
        ):
            positions[node.id] = pos

        return positions


@dataclass
class TreeScene:
    """What a composed tree scene contains, for callers that need to reason about it.

    :param skeleton: The grown skeleton, whose radii report limb load.
    :param positions: Schematic positions keyed by node ID.
    :param crown: ``(M, 3)`` crown attractor positions — the leaves.
    :param trunk_height: Trunk height used, in world units.
    :param n_leaves: Number of definitions rendered as foliage.
    :param n_modules: Number of module limbs.
    """

    skeleton: Skeleton
    positions: dict[str, np.ndarray]
    crown: np.ndarray
    trunk_height: float
    n_leaves: int
    n_modules: int


def build_code_tree_scene(
    nodes: list[LayoutNode],
    edges: list[LayoutEdge],
    plotter: pv.Plotter,
    *,
    key: str,
    layout: CodeTreeLayout | None = None,
    tropism: tuple[float, float, float] | None = None,
    tip_radius: float = 0.14,
    leaf_size: float = 0.55,
    background: tuple[str, str] = theme.TREE_BACKGROUND,
) -> TreeScene:
    """Grow the code graph into *plotter* as a single tree.

    The wood is one merged mesh and the canopy is one glyphed mesh, so the
    whole tree is two actors no matter how large the repository — the same
    batching the schematic renderer uses.

    :param nodes: Nodes to render.
    :param edges: Edges, forwarded to the layout.
    :param plotter: PyVista plotter to compose into; it is cleared first.
    :param key: Stable identifier (repo path or name).  Seeds the RNG, so the
        same repository grows the same tree every time.
    :param layout: Crown layout; a default :class:`CodeTreeLayout` if omitted.
    :param tropism: Growth bias; :data:`pycode_kg.theme.DEFAULT_TROPISM` if omitted.
    :param tip_radius: Radius of leaf-bearing twigs, in world units.
    :param leaf_size: Leaf radius before density scaling.
    :param background: ``(bottom, top)`` background colours.
    :raises ValueError: If no node maps to a crown attractor — there is
        nothing for the wood to grow toward.
    :return: The composed :class:`TreeScene`.
    """
    # Lazy: matplotlib arrives with pyvista, so importing it at module scope
    # would make this module unimportable without the viz3d extra — and the
    # layout half of it is deliberately usable with NumPy alone.
    from matplotlib.colors import ListedColormap  # noqa: PLC0415

    layout = layout if layout is not None else CodeTreeLayout()
    positions = layout.compute(nodes, edges)

    crown_set = crown_kinds()
    leaves = [n for n in nodes if theme.resolve_kind(n.kind, n.name) in crown_set]
    crown = np.array([positions[n.id] for n in leaves if n.id in positions])
    if crown.size == 0:
        raise ValueError(
            "no classes, functions or methods to grow toward — an empty crown cannot make a tree"
        )

    root = np.array([0.0, 0.0, 0.0])
    skeleton = grow_tree(
        np.vstack([layout.trunk_guides(), crown]),
        root,
        key=key,
        tip_radius=tip_radius,
        tropism=tropism if tropism is not None else theme.DEFAULT_TROPISM,
    )

    plotter.clear_actors()
    plotter.set_background(background[0], top=background[1])  # ty: ignore[invalid-argument-type]
    plotter.enable_anti_aliasing("msaa")

    plotter.add_mesh(
        tree_mesh(skeleton),
        color=theme.WOOD_COLOR,
        smooth_shading=True,
        name="wood",
    )

    # A fixed leaf size tiles a dense crown into an opaque shell that hides
    # the wood entirely.  Cube root, because the canopy is a volume.
    leaf_scale = min(
        1.0,
        (theme.LEAF_REFERENCE_COUNT / max(len(crown), 1)) ** (1.0 / 3.0),
    )
    tint = np.array(
        [theme.FOLIAGE_KINDS.index(theme.resolve_kind(n.kind, n.name)) for n in leaves],
        dtype=float,
    )
    plotter.add_mesh(
        leaf_glyphs(
            crown,
            skeleton,
            size=leaf_size * leaf_scale,
            tint=tint,
            seed=seed_from_key(f"{key}:leaves"),
        ),
        scalars="tint",
        cmap=ListedColormap(list(theme.FOLIAGE_COLOR)),
        clim=[-0.5, len(theme.FOLIAGE_COLOR) - 0.5],
        show_scalar_bar=False,
        name="foliage",
    )

    return TreeScene(
        skeleton=skeleton,
        positions=positions,
        crown=crown,
        trunk_height=layout.trunk_height,
        n_leaves=len(crown),
        n_modules=len(layout.branch_lines),
    )
