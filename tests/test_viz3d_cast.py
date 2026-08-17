"""Tests for the cast seam in the 3-D viewer.

Only the seam, not the window: constructing ``MainWindow`` builds a
``QtInteractor``, which without a GL context aborts the interpreter rather than
raising — and a fatal abort is not an exception, so it takes every queued test
with it. Importing the module is safe, so the seam is testable and the Qt
plumbing is not.

The seam moved down a layer. The four-step build/render/write/cast is
``kg_utils.viz3d.qt.cast_scene_to_looking_glass`` as of kgmodule-utils 0.15.0,
and the tile-grid scaling is ``QuiltSpec.scaled`` as of quiltwright 0.6.0.
Both arrived here by way of ``gutenberg_kg``, which had the same code: not
similar code, the same code, copied and then nudged until only the widget names
differed. What is left to pin is that this repo really does use them — a
re-introduced local copy would drift exactly the way the first one did.
"""

from __future__ import annotations

import inspect

import pytest

pytest.importorskip("pyvistaqt", reason="viz3d extra not installed — needs `viz3d`")
pytest.importorskip("quiltwright", reason="quiltwright not installed — needs `viz3d`")

from pycode_kg import viz3d  # noqa: E402

# No module-level `integration` mark: CI runs `pytest -m "not integration"`, and
# a migration guard that CI skips is not a guard. Only the classes that build a
# real ``pv.Plotter`` are marked, since those need a GL context.


class TestTheMachineryIsNotOursAnyMore:
    """Guards against a local copy of the cast pipeline creeping back in."""

    @pytest.fixture
    def cast_source(self) -> str:
        return inspect.getsource(viz3d.MainWindow.cast_to_looking_glass)

    def test_it_calls_the_sdk_helper(self, cast_source):
        assert "cast_scene_to_looking_glass" in cast_source

    @pytest.mark.parametrize("gone", ["render_quilt(", "save_quilt(", "cast_quilt("])
    def test_it_no_longer_drives_quiltwright_directly(self, cast_source, gone):
        """Those three calls in sequence *are* the pipeline that moved."""
        assert gone not in cast_source

    def test_it_no_longer_open_codes_the_tile_rounding(self, cast_source):
        """`// columns * columns` is QuiltSpec.scaled's job now."""
        assert "// preset.columns" not in cast_source
        assert ".scaled(" in cast_source

    def test_it_no_longer_builds_its_own_offscreen_plotter(self, cast_source):
        assert "pv.Plotter(off_screen=True)" not in cast_source

    def test_the_sdk_helper_is_importable(self):
        from kg_utils.viz3d import qt

        assert qt.cast_scene_to_looking_glass.__module__ == "kg_utils.viz3d.qt"


@pytest.mark.integration
class TestTheContractTheViewerReliesOn:
    """`cast_to_looking_glass` branches on this shape.

    Marked integration: ``cast_scene_to_looking_glass`` builds an off-screen
    ``pv.Plotter`` before it reaches the builder, so these need a working GL
    context even though the builder always raises.
    """

    def test_the_helper_returns_a_path_and_an_error_slot(self):
        """`(None, msg)` means the render failed; `(path, msg)` means only Bridge did."""
        from kg_utils.viz3d.qt import cast_scene_to_looking_glass

        def explode(_plotter):
            raise RuntimeError("scene build failed")

        spec = _tiny_spec()
        path, error = cast_scene_to_looking_glass(explode, None, "unused", spec)
        assert path is None
        assert error is not None and "scene build failed" in error

    def test_a_failed_build_is_returned_not_raised(self):
        """A dark panel — or a broken scene — must not kill the viewer."""
        from kg_utils.viz3d.qt import cast_scene_to_looking_glass

        def explode(_plotter):
            raise RuntimeError("boom")

        cast_scene_to_looking_glass(explode, None, "unused", _tiny_spec())

    def test_progress_is_reported_with_a_step_total(self):
        """The viewer's `step(n, total, message)` signature depends on this."""
        from kg_utils.viz3d.qt import cast_scene_to_looking_glass

        seen: list[tuple[int, int, str]] = []

        def explode(_plotter):
            raise RuntimeError("stop")

        cast_scene_to_looking_glass(
            explode, None, "unused", _tiny_spec(), progress=lambda *a: seen.append(a)
        )
        assert seen and seen[0][0] == 1 and seen[0][1] == 4


class TestTheScaledSpecIsWhatGetsCast:
    """The viewer and the spec test must agree on one calculation."""

    def test_the_viewer_scales_the_preset_it_names(self):
        from quiltwright import QUILT_PRESETS

        preset = QUILT_PRESETS[viz3d.QUILT_SPEC]
        scaled = preset.scaled(viz3d.CAST_SCALE)
        assert scaled.n_views == preset.n_views
        assert scaled.quilt_width % scaled.columns == 0
        assert scaled.quilt_height % scaled.rows == 0
        assert scaled.quilt_width < preset.quilt_width


def _tiny_spec():
    """:return: A minimal 2x2 quilt spec."""
    from quiltwright import QuiltSpec

    return QuiltSpec(columns=2, rows=2, quilt_width=128, quilt_height=128, aspect=1.0)
