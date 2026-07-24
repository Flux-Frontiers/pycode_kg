"""
Shared visual vocabulary for every PyCodeKG renderer.

Before this module the kind→colour mapping was defined three times — in
``app.py`` (2-D pyvis), ``viz3d.py`` (3-D PyVista) and ``layout3d.py`` (node
radii) — and the three copies had drifted apart, even though ``viz3d.py``
carried a comment claiming it was "aligned with app.py".  This module is the
single source of truth; renderers import from here rather than defining their
own constants.

The palette is the one from the 2-D explorer, which is the alignment target the
3-D viewer's comment always claimed.  ``private_function`` is carried over from
the 3-D viewer, which is the only renderer that distinguishes it.
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Node kinds
# ---------------------------------------------------------------------------

#: Fallback used for any kind not present in the maps below.
UNKNOWN_KIND: Final[str] = "symbol"

#: Kinds that actually exist in the graph store.  ``private_function`` is a
#: *render* kind synthesised by :func:`resolve_kind`, so it must never be used
#: to filter or query the store.
STORE_KINDS: Final[tuple[str, ...]] = (
    "module",
    "class",
    "function",
    "method",
    "symbol",
)

KIND_COLOR: Final[dict[str, str]] = {
    "module": "#4A90D9",  # blue
    "class": "#E67E22",  # orange
    "function": "#27AE60",  # green
    "private_function": "#F1C40F",  # yellow — 3-D only
    "method": "#8E44AD",  # purple
    "symbol": "#95A5A6",  # grey
}

#: vis.js node shapes (2-D renderer only).
KIND_SHAPE: Final[dict[str, str]] = {
    "module": "box",
    "class": "diamond",
    "function": "ellipse",
    "private_function": "ellipse",
    "method": "dot",
    "symbol": "triangle",
}

#: Base node radius in world units (3-D renderer and layout engine).
KIND_SIZE: Final[dict[str, float]] = {
    "module": 1.2,
    "class": 0.9,
    "function": 0.7,
    "private_function": 0.7,
    "method": 0.5,
    "symbol": 0.4,
}

#: Base node diameter in pixels (2-D renderer).
KIND_PIXEL_SIZE: Final[dict[str, int]] = {
    "module": 18,
    "class": 18,
    "function": 12,
    "private_function": 12,
    "method": 12,
    "symbol": 12,
}


def color_for(kind: str) -> str:
    """Return the palette colour for *kind*, falling back to the symbol grey.

    :param kind: Node kind, e.g. ``"function"``.
    :return: Hex colour string.
    """
    return KIND_COLOR.get(kind, KIND_COLOR[UNKNOWN_KIND])


def shape_for(kind: str) -> str:
    """Return the vis.js shape for *kind*.

    :param kind: Node kind.
    :return: vis.js shape name.
    """
    return KIND_SHAPE.get(kind, KIND_SHAPE[UNKNOWN_KIND])


def resolve_kind(kind: str, name: str) -> str:
    """Map a raw node kind onto a *render* kind.

    Functions whose name begins with an underscore render as
    ``private_function`` so they can be de-emphasised; anything the palette does
    not know about collapses to ``symbol``.

    :param kind: Raw node kind from the graph store.
    :param name: Node name, used to detect private functions.
    :return: A kind guaranteed to be present in the palette maps.
    """
    if kind == "function" and name.startswith("_"):
        return "private_function"
    if kind not in KIND_SIZE:
        return UNKNOWN_KIND
    return kind


def with_alpha(hex_color: str, alpha: float) -> str:
    """Convert ``#RRGGBB`` to an ``rgba()`` string at the given opacity.

    vis.js accepts CSS colour strings for node backgrounds, so opacity is
    expressed by converting the palette hex rather than by compositing against
    the canvas background.

    :param hex_color: Colour in ``#RRGGBB`` form.
    :param alpha: Opacity in ``[0, 1]``; values outside the range are clamped.
    :return: An ``rgba(r, g, b, a)`` string, or *hex_color* unchanged when it is
        not a 6-digit hex colour.
    """
    raw = hex_color.lstrip("#")
    if len(raw) != 6:
        return hex_color
    try:
        r, g, b = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return hex_color
    a = min(1.0, max(0.0, alpha))
    return f"rgba({r}, {g}, {b}, {a:.3f})"


# ---------------------------------------------------------------------------
# Edge relations
# ---------------------------------------------------------------------------

REL_COLOR: Final[dict[str, str]] = {
    "CONTAINS": "#BDC3C7",
    "CALLS": "#E74C3C",
    "IMPORTS": "#3498DB",
    "INHERITS": "#F39C12",
}

#: 3-D override.  ``CONTAINS`` forms the structural skeleton and is by far the
#: most numerous relation, so in a dense 3-D scene the 2-D light grey drowns out
#: everything else.  Only that one entry differs.
REL_COLOR_3D: Final[dict[str, str]] = {**REL_COLOR, "CONTAINS": "#555555"}

#: Neutral colour for relations absent from the maps above.
REL_FALLBACK: Final[str] = "#888888"


def rel_color(rel: str, *, three_d: bool = False) -> str:
    """Return the colour for an edge relation.

    :param rel: Relation name, e.g. ``"CALLS"``.
    :param three_d: Use the 3-D palette (dimmer ``CONTAINS``).
    :return: Hex colour string.
    """
    table = REL_COLOR_3D if three_d else REL_COLOR
    return table.get(rel, REL_FALLBACK)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

#: Z level per node kind, used by the funnel layout.
KIND_ZLEVEL: Final[dict[str, int]] = {
    "module": 0,
    "class": 1,
    "function": 2,
    "private_function": 2,
    "method": 2,
    "symbol": 3,
}

#: Representative node radius per Z level, derived from :data:`KIND_SIZE`.
LEVEL_NODE_SIZE: Final[dict[int, float]] = {
    0: KIND_SIZE["module"],
    1: KIND_SIZE["class"],
    2: KIND_SIZE["function"],
    3: KIND_SIZE["symbol"],
}
