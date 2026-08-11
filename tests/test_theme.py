"""
test_theme.py

Tests for :mod:`pycode_kg.theme`, the shared visual vocabulary.

The point of this module is to stop the renderers drifting apart again, so most
of these tests assert *consistency invariants* rather than specific values —
every kind must be present in every map, the renderers must resolve kinds the
same way, and render-only kinds must never leak into store queries.
"""

from __future__ import annotations

import pytest

from pycode_kg import theme

# ---------------------------------------------------------------------------
# Completeness — a kind missing from one map is exactly how the drift started
# ---------------------------------------------------------------------------


def test_every_kind_appears_in_every_map() -> None:
    """Colour, shape, size and pixel-size maps cover identical kinds."""
    kinds = set(theme.KIND_COLOR)
    assert set(theme.KIND_SHAPE) == kinds
    assert set(theme.KIND_SIZE) == kinds
    assert set(theme.KIND_PIXEL_SIZE) == kinds
    assert set(theme.KIND_ZLEVEL) == kinds


def test_unknown_kind_is_itself_mapped() -> None:
    """The fallback kind must exist in the maps it is a fallback for."""
    assert theme.UNKNOWN_KIND in theme.KIND_COLOR
    assert theme.UNKNOWN_KIND in theme.KIND_SHAPE
    assert theme.UNKNOWN_KIND in theme.KIND_SIZE


def test_colours_are_six_digit_hex() -> None:
    """Every colour is ``#RRGGBB`` — the 2-D renderer parses these for opacity."""
    for palette in (theme.KIND_COLOR, theme.REL_COLOR, theme.REL_COLOR_3D):
        for value in palette.values():
            assert value.startswith("#")
            assert len(value) == 7
            int(value[1:], 16)


def test_colours_are_distinguishable() -> None:
    """No two node kinds share a colour."""
    colours = list(theme.KIND_COLOR.values())
    assert len(colours) == len(set(colours))


# ---------------------------------------------------------------------------
# Store kinds vs render kinds
# ---------------------------------------------------------------------------


def test_store_kinds_exclude_render_only_kinds() -> None:
    """``private_function`` is synthesised at render time, not stored.

    Using it to filter the graph store would silently match nothing.
    """
    assert "private_function" not in theme.STORE_KINDS
    assert "private_function" in theme.KIND_COLOR


def test_store_kinds_are_all_renderable() -> None:
    """Every kind the store can return has a visual definition."""
    for kind in theme.STORE_KINDS:
        assert kind in theme.KIND_COLOR
        assert kind in theme.KIND_SIZE


# ---------------------------------------------------------------------------
# resolve_kind — both renderers must agree
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "name", "expected"),
    [
        ("function", "_helper", "private_function"),
        ("function", "__dunder__", "private_function"),
        ("function", "public", "function"),
        ("method", "_private_method", "method"),
        ("class", "_Private", "class"),
        ("module", "mod", "module"),
        ("symbol", "sym", "symbol"),
        ("nonsense", "x", "symbol"),
        ("", "", "symbol"),
    ],
)
def test_resolve_kind(kind: str, name: str, expected: str) -> None:
    """Only underscore-prefixed *functions* become ``private_function``.

    Methods are deliberately left alone — a leading underscore on a method is
    convention rather than a strong signal, and colouring every ``_method``
    differently would swamp the palette.
    """
    assert theme.resolve_kind(kind, name) == expected


def test_resolve_kind_always_yields_a_renderable_kind() -> None:
    """Whatever comes out of the store, the result is safe to look up."""
    for kind in (*theme.STORE_KINDS, "unheard-of", ""):
        resolved = theme.resolve_kind(kind, "name")
        assert resolved in theme.KIND_SIZE
        assert resolved in theme.KIND_COLOR


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def test_color_and_shape_fall_back_rather_than_raise() -> None:
    """Unknown kinds degrade to the symbol styling."""
    assert theme.color_for("nope") == theme.KIND_COLOR[theme.UNKNOWN_KIND]
    assert theme.shape_for("nope") == theme.KIND_SHAPE[theme.UNKNOWN_KIND]
    assert theme.color_for("module") == theme.KIND_COLOR["module"]


def test_rel_color_palettes_differ_only_in_contains() -> None:
    """The 3-D override exists solely to dim the dominant relation."""
    differing = {rel for rel in theme.REL_COLOR if theme.REL_COLOR[rel] != theme.REL_COLOR_3D[rel]}
    assert differing == {"CONTAINS"}


def test_rel_color_selects_the_right_palette() -> None:
    """``three_d`` switches palettes, and unknown relations fall back."""
    assert theme.rel_color("CONTAINS") == theme.REL_COLOR["CONTAINS"]
    assert theme.rel_color("CONTAINS", three_d=True) == theme.REL_COLOR_3D["CONTAINS"]
    assert theme.rel_color("CALLS") == theme.rel_color("CALLS", three_d=True)
    assert theme.rel_color("MADE_UP") == theme.REL_FALLBACK


def test_default_relations_are_all_coloured() -> None:
    """Every relation the extractor emits has a colour."""
    from pycode_kg.store import DEFAULT_RELS

    for rel in DEFAULT_RELS:
        assert rel in theme.REL_COLOR


# ---------------------------------------------------------------------------
# with_alpha — drives centrality opacity in the 2-D renderer
# ---------------------------------------------------------------------------


def test_with_alpha_converts_hex_to_rgba() -> None:
    """A palette hex becomes a CSS ``rgba()`` string vis.js understands."""
    assert theme.with_alpha("#4A90D9", 0.5) == "rgba(74, 144, 217, 0.500)"


def test_with_alpha_handles_the_endpoints() -> None:
    """Fully transparent and fully opaque both round-trip."""
    assert theme.with_alpha("#000000", 0.0) == "rgba(0, 0, 0, 0.000)"
    assert theme.with_alpha("#FFFFFF", 1.0) == "rgba(255, 255, 255, 1.000)"


@pytest.mark.parametrize(("alpha", "expected"), [(-3.0, "0.000"), (7.5, "1.000")])
def test_with_alpha_clamps_out_of_range(alpha: float, expected: str) -> None:
    """Opacity outside ``[0, 1]`` is clamped rather than emitted invalid."""
    assert theme.with_alpha("#4A90D9", alpha).endswith(f"{expected})")


def test_with_alpha_accepts_hex_without_hash() -> None:
    """A bare six-digit hex is treated the same as a prefixed one."""
    assert theme.with_alpha("4A90D9", 1.0) == theme.with_alpha("#4A90D9", 1.0)


@pytest.mark.parametrize("value", ["", "#abc", "rgba(1,2,3,1)", "#GGGGGG", "red"])
def test_with_alpha_passes_through_non_hex(value: str) -> None:
    """Anything that is not a six-digit hex is returned untouched.

    Node colours are supposed to come from the palette, but a caller passing a
    CSS keyword should degrade to an opaque colour rather than a crash mid-render.
    """
    assert theme.with_alpha(value, 0.5) == value


def test_every_palette_colour_converts() -> None:
    """No palette entry can break the opacity path."""
    for colour in theme.KIND_COLOR.values():
        assert theme.with_alpha(colour, 0.5).startswith("rgba(")


# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------


def test_level_node_size_is_derived_from_kind_size() -> None:
    """Layout radii track the 3-D node sizes instead of restating them."""
    assert theme.LEVEL_NODE_SIZE[0] == theme.KIND_SIZE["module"]
    assert theme.LEVEL_NODE_SIZE[3] == theme.KIND_SIZE["symbol"]


def test_every_zlevel_has_a_radius() -> None:
    """No kind can land on a Z level with no defined size."""
    for level in set(theme.KIND_ZLEVEL.values()):
        assert level in theme.LEVEL_NODE_SIZE


def test_layout_module_uses_the_shared_constants() -> None:
    """``layout3d`` must not carry its own copy of the maps.

    The engine itself now lives in :mod:`kg_utils.viz3d` and takes the
    kind→Z-level mapping as a constructor argument, so this asserts the wiring
    rather than a module constant: the same guarantee, one indirection further
    out.
    """
    pytest.importorskip("numpy")
    from pycode_kg.layout3d import FunnelLayout

    layout = FunnelLayout()
    assert layout.zlevels == theme.KIND_ZLEVEL
    assert layout.level_sizes == theme.LEVEL_NODE_SIZE


def test_unknown_kinds_land_on_the_symbol_level() -> None:
    """A kind the palette doesn't know renders where ``resolve_kind`` puts it.

    The shared engine defaults unrecognised kinds to level 0, which for a code
    graph would drop them into the *module* layer. The theme already collapses
    unknown kinds to ``symbol``, so the layout must agree.
    """
    pytest.importorskip("numpy")
    from pycode_kg.layout3d import FunnelLayout

    assert FunnelLayout().default_level == theme.KIND_ZLEVEL[theme.UNKNOWN_KIND]


def test_layout3d_reexports_the_shared_engine() -> None:
    """The shim's whole job is that existing imports keep working."""
    pytest.importorskip("numpy")
    from pycode_kg import layout3d

    for name in (
        "AlliumLayout",
        "FunnelLayout",
        "Layout3D",
        "LayoutEdge",
        "LayoutNode",
        "fibonacci_annulus",
        "fibonacci_sphere",
    ):
        assert hasattr(layout3d, name), f"layout3d no longer exports {name}"
