"""
test_scene3d.py

Guards the organic code-tree layout — the contract that a repository's shape
survives the trip into wood.

The layout itself is pure geometry (NumPy only), so most of this file needs no
renderer.  Only the two scene-composition tests require the ``viz3d`` extra,
and they skip cleanly without it.
"""

from __future__ import annotations

import numpy as np
import pytest

from pycode_kg.layout3d import LayoutNode
from pycode_kg.scene3d import CodeTreeLayout, crown_kinds


def _module(path: str) -> LayoutNode:
    """Build a module node for *path*.

    :param path: Module path.
    :return: A ``LayoutNode`` of kind ``module``.
    """
    return LayoutNode(id=f"mod:{path}", kind="module", name=path, module_path=path)


def _defs(path: str, n: int, kind: str = "function") -> list[LayoutNode]:
    """Build *n* definition nodes inside *path*.

    :param path: Owning module path.
    :param n: How many definitions.
    :param kind: Node kind.
    :return: List of ``LayoutNode``.
    """
    return [
        LayoutNode(id=f"{kind}:{path}:f{i}", kind=kind, name=f"f{i}", module_path=path)
        for i in range(n)
    ]


def _repo(sizes: dict[str, int]) -> list[LayoutNode]:
    """Build a synthetic repo: one module per key, holding that many functions.

    :param sizes: Mapping of module path to definition count.
    :return: Flat node list.
    """
    nodes: list[LayoutNode] = []
    for path, n in sizes.items():
        nodes.append(_module(path))
        nodes.extend(_defs(path, n))
    return nodes


def test_every_definition_reaches_the_crown() -> None:
    """Each class/function/method gets a position; none is silently dropped."""
    nodes = _repo({"a.py": 4, "b.py": 7})
    positions = CodeTreeLayout().compute(nodes, [])

    crown = crown_kinds()
    defs = [n for n in nodes if n.kind in crown]
    assert len(defs) == 11
    assert all(n.id in positions for n in defs)


def test_the_tree_stands_on_the_origin() -> None:
    """The trunk axis is at x=y=0 and everything grows upward from z=0.

    The renderer plants the root at the origin, so a layout that drifted off
    axis would grow a tree leaning away from its own trunk.
    """
    layout = CodeTreeLayout()
    positions = layout.compute(_repo({"a.py": 5, "b.py": 5, "c.py": 5}), [])

    pts = np.array(list(positions.values()))
    assert pts[:, 2].min() >= -1e-9, "nothing may hang below the ground plane"
    # Limb stations start on the axis itself.
    for axis, _tip in layout.branch_lines:
        assert abs(axis[0]) < 1e-9
        assert abs(axis[1]) < 1e-9


def test_limb_length_reports_module_size() -> None:
    """A module with more definitions reaches further from the trunk.

    This is the load-bearing claim of the whole visualisation: limb geometry
    is data, not decoration.  Without it every limb ends at the same radius
    and the crown is a hollow shell.
    """
    layout = CodeTreeLayout()
    layout.compute(_repo({"small.py": 2, "big.py": 40}), [])

    reaches = {}
    for (axis, tip), path in zip(layout.branch_lines, sorted({"small.py", "big.py"}), strict=True):
        reaches[path] = float(np.linalg.norm(tip - axis))

    assert reaches["big.py"] > reaches["small.py"] * 1.5


def test_trunk_grows_with_the_repository_but_is_capped() -> None:
    """Trunk height rises with definition count and stops at the cap."""
    layout = CodeTreeLayout()

    layout.compute(_repo({"a.py": 4}), [])
    small = layout.trunk_height
    layout.compute(_repo({f"m{i}.py": 20 for i in range(40)}), [])
    large = layout.trunk_height

    assert small < large
    assert large <= layout.max_trunk_height


def test_trunk_guides_sit_below_the_lowest_limb() -> None:
    """Growth guides climb the axis and stop before the branching starts.

    A guide that reached into the crown would grow a bare pole through the
    middle of the canopy.
    """
    layout = CodeTreeLayout()
    layout.compute(_repo({"a.py": 6, "b.py": 6}), [])
    guides = layout.trunk_guides()

    assert guides.shape[1] == 3
    assert np.allclose(guides[:, :2], 0.0), "guides must stay on the trunk axis"
    lowest_limb_z = min(tip[2] for _axis, tip in layout.branch_lines)
    assert guides[:, 2].max() < lowest_limb_z


def test_layout_is_reproducible() -> None:
    """The same repository lays out identically twice — no RNG, no set order."""
    nodes = _repo({"a.py": 5, "b.py": 9, "c.py": 3})
    first = CodeTreeLayout().compute(nodes, [])
    second = CodeTreeLayout().compute(nodes, [])

    assert first.keys() == second.keys()
    for key in first:
        assert np.allclose(first[key], second[key])


def test_symbol_stubs_are_not_foliage() -> None:
    """``sym:`` stubs are placed but never counted as leaves.

    Six thousand import stubs would swamp three hundred real definitions and
    the canopy would stop meaning anything.
    """
    nodes = _repo({"a.py": 3})
    stubs = [
        LayoutNode(id=f"sym:x{i}", kind="symbol", name=f"x{i}", module_path="a.py")
        for i in range(20)
    ]
    layout = CodeTreeLayout()
    positions = layout.compute([*nodes, *stubs], [])

    assert all(s.id in positions for s in stubs), "stubs still need somewhere to go"
    assert "symbol" not in crown_kinds()


class TestSceneComposition:
    """Scene tests that need a real renderer."""

    @staticmethod
    def _plotter():
        """Build an off-screen plotter, skipping if PyVista is absent.

        :return: An off-screen ``pv.Plotter``.
        """
        pv = pytest.importorskip("pyvista")
        return pv.Plotter(off_screen=True)

    def test_wood_and_foliage_are_two_actors(self) -> None:
        """However large the repo, the tree costs two actors — not one per node."""
        from pycode_kg.scene3d import build_code_tree_scene

        plotter = self._plotter()
        try:
            scene = build_code_tree_scene(
                _repo({f"m{i}.py": 8 for i in range(12)}), [], plotter, key="t"
            )
            assert set(plotter.actors) == {"wood", "foliage"}
            assert scene.n_leaves == 96
            assert scene.n_modules == 12
        finally:
            plotter.close()

    def test_an_empty_crown_is_refused_clearly(self) -> None:
        """A repo with no definitions raises rather than growing a bare stick."""
        from pycode_kg.scene3d import build_code_tree_scene

        plotter = self._plotter()
        try:
            with pytest.raises(ValueError, match="empty crown"):
                build_code_tree_scene([_module("a.py")], [], plotter, key="t")
        finally:
            plotter.close()

    def test_trunk_is_thicker_than_its_twigs(self) -> None:
        """Pipe-model radii: the trunk carries every tip, so it is the thickest.

        This is what makes limb thickness readable as "how much code".
        """
        from pycode_kg.scene3d import build_code_tree_scene

        plotter = self._plotter()
        try:
            scene = build_code_tree_scene(
                _repo({f"m{i}.py": 6 for i in range(8)}), [], plotter, key="t", tip_radius=0.1
            )
            radii = scene.skeleton.radii
            assert radii is not None
            assert radii[0] > 0.1, "trunk must exceed the tip radius"
            assert radii[0] == pytest.approx(radii.max())
        finally:
            plotter.close()
