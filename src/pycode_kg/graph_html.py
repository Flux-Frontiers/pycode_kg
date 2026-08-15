"""
PyCodeKG's visual vocabulary for the shared graph renderer.

The rendering itself lives in :mod:`kg_utils.viz`, shared with every other KG
module.  What stays here is the part that is genuinely specific to a *code*
graph: which node kinds exist, how they are coloured, and which fields are worth
showing on hover.

``build_graph_html`` and ``select_nodes`` are re-exported so existing callers do
not need to know where the implementation moved.

License: Elastic 2.0
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from kg_utils.viz import (
    CENTRALITY_MIN_OPACITY,
    CENTRALITY_SIZE_RANGE,
    GraphTheme,
    KindStyle,
    TooltipRow,
    TooltipSpec,
    select_nodes,
)
from kg_utils.viz import build_graph_html as _build_graph_html

from pycode_kg import theme

__all__ = [
    "CENTRALITY_MIN_OPACITY",
    "CENTRALITY_SIZE_RANGE",
    "CODE_THEME",
    "CODE_TOOLTIP",
    "build_graph_html",
    "select_nodes",
]


def _resolve_kind(node: Mapping[str, Any]) -> str:
    """Map a stored node onto a render kind.

    Underscore-prefixed functions render as ``private_function`` so they can be
    de-emphasised.  That kind exists only for display — the store never holds it,
    which is why the mapping lives in the theme rather than in the schema.

    :param node: Node attribute mapping.
    :return: A render kind.
    """
    return theme.resolve_kind(str(node.get("kind", "")), str(node.get("name", "")))


def _line_range(node: Mapping[str, Any]) -> str:
    """Format a node's source line range for the tooltip.

    :param node: Node attribute mapping.
    :return: ``"lines 12–40"``, ``"line 12"``, or an empty string.
    """
    start, end = node.get("lineno"), node.get("end_lineno")
    if start and end and end != start:
        return f"lines {start}–{end}"
    return f"line {start}" if start else ""


#: How a Python code graph is drawn.  Colours come from :mod:`pycode_kg.theme`,
#: which the 3-D viewer and the layout engine share.
CODE_THEME: Final[GraphTheme] = GraphTheme(
    kinds={
        kind: KindStyle(
            color=theme.KIND_COLOR[kind],
            shape=theme.KIND_SHAPE[kind],
            size=theme.KIND_PIXEL_SIZE[kind],
            radius=theme.KIND_SIZE[kind],
        )
        for kind in theme.KIND_COLOR
    },
    fallback=KindStyle(
        color=theme.KIND_COLOR[theme.UNKNOWN_KIND],
        shape=theme.KIND_SHAPE[theme.UNKNOWN_KIND],
        size=theme.KIND_PIXEL_SIZE[theme.UNKNOWN_KIND],
        radius=theme.KIND_SIZE[theme.UNKNOWN_KIND],
    ),
    relations=theme.REL_COLOR,
    relation_fallback=theme.REL_FALLBACK,
    resolve_kind=_resolve_kind,
)

#: Which code fields are worth showing on hover.
CODE_TOOLTIP: Final[TooltipSpec] = TooltipSpec(
    title="qualname",
    rows=(
        TooltipRow("module_path", prefix="📄 "),
        TooltipRow(_line_range),
    ),
    body="docstring",
)


def build_graph_html(
    nodes: list[dict],
    edges: list[dict],
    *,
    height: str = "620px",
    seed_ids: set[str] | None = None,
    physics: bool = True,
    scores: Any | None = None,
) -> str:
    """Render a code graph as a self-contained interactive HTML page.

    A thin wrapper binding PyCodeKG's theme and tooltip to the shared renderer.

    :param nodes: Node attribute dicts, each with at least an ``id``.
    :param edges: Edge dicts with ``src``, ``dst`` and ``rel`` keys.
    :param height: CSS height for the canvas.
    :param seed_ids: Node IDs from a semantic seed query, drawn with a gold
        border.
    :param physics: Whether to run the Barnes-Hut simulation.
    :param scores: Centrality scores driving size and opacity, or ``None``.
    :return: A self-contained HTML document.
    """
    return _build_graph_html(
        nodes,
        edges,
        theme=CODE_THEME,
        tooltip=CODE_TOOLTIP,
        scores=scores,
        height=height,
        physics=physics,
        highlight_ids=seed_ids,
    )
