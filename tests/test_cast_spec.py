"""
test_cast_spec.py

Guards the quilt specification the viewer's "Cast to LG" button renders.

Casting deliberately renders smaller than ``pycodekg quilt`` does, because the
wait is Bridge decoding the PNG rather than the local render.  Scaling a quilt
is not a free operation though: the tile grid has to keep landing on integer
pixel boundaries, or every view is sampled a fraction off and the display fuses
a subtly wrong image.
"""

from __future__ import annotations

import pytest

quiltwright = pytest.importorskip("quiltwright")

from pycode_kg.viz3d import CAST_SCALE, QUILT_SPEC  # noqa: E402


def _cast_spec():
    """Build the cast spec exactly as ``cast_to_looking_glass`` does.

    This calls the same ``QuiltSpec.scaled`` the viewer calls, rather than
    re-deriving the arithmetic.  It used to open-code the ``// columns *
    columns`` rounding, which meant this file tested *its own* copy of the
    formula: the viewer could have changed and every assertion below would
    still have passed.

    :return: ``(preset, scaled spec)``.
    """
    preset = quiltwright.QUILT_PRESETS[QUILT_SPEC]
    return preset, preset.scaled(CAST_SCALE)


def test_cast_preset_exists() -> None:
    """The preset the button names is a real one."""
    assert QUILT_SPEC in quiltwright.QUILT_PRESETS


def test_scaled_quilt_still_tiles_exactly() -> None:
    """Tiles divide the scaled quilt with no remainder.

    This is the reason ``QuiltSpec.scaled`` rounds down to the tile grid;
    plain multiplication by 0.5 is not guaranteed to stay grid-aligned for
    every preset, and a fractional tile misaligns every view.
    """
    _preset, spec = _cast_spec()

    assert spec.tile_width * spec.columns == spec.quilt_width
    assert spec.tile_height * spec.rows == spec.quilt_height


def test_cast_preserves_the_view_geometry() -> None:
    """Scaling changes pixels only — never the optics.

    View count, aspect and cone are what the display uses to fuse the quilt;
    a cast that changed any of them would not match the panel.
    """
    preset, spec = _cast_spec()

    assert spec.n_views == preset.n_views
    assert spec.aspect == preset.aspect
    assert spec.view_cone == preset.view_cone
    assert spec.columns == preset.columns
    assert spec.rows == preset.rows


def test_cast_is_meaningfully_cheaper() -> None:
    """The point of casting small is decode time, which scales with area."""
    preset, spec = _cast_spec()

    full = preset.quilt_width * preset.quilt_height
    cast = spec.quilt_width * spec.quilt_height
    assert cast < full / 3, "casting should cut decode area substantially"
