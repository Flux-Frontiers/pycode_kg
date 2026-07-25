"""
test_graph_html.py

Tests for :mod:`pycode_kg.graph_html`, the Streamlit-free graph builder.

These need only the ``viz`` extra's pyvis; they used to live in
``test_app_render.py`` and had to monkey-patch ``st.set_page_config`` just to
import the builder out of ``app.py``. Extracting the builder removed that.

The self-containment tests guard a regression only a browser could catch: pyvis
defaults to ``cdn_resources="local"``, which emits *relative* asset paths.
Embedded in a ``srcdoc`` iframe — which has no base URL — those cannot resolve,
so the graph rendered only when the cdnjs fallback was reachable and otherwise
failed silently with ``vis is not defined``.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pyvis")

from pycode_kg.analysis.scores import ScoreSet  # noqa: E402
from pycode_kg.graph_html import build_graph_html, select_nodes  # noqa: E402

NODES = [
    {"id": "mod:a.py", "kind": "module", "name": "a", "module_path": "a.py"},
    {"id": "fn:a.py:hot", "kind": "function", "name": "hot", "module_path": "a.py"},
    {"id": "fn:a.py:cold", "kind": "function", "name": "cold", "module_path": "a.py"},
    {"id": "fn:a.py:_priv", "kind": "function", "name": "_priv", "module_path": "a.py"},
]
EDGES = [
    {"src": "mod:a.py", "rel": "CONTAINS", "dst": "fn:a.py:hot"},
    {"src": "fn:a.py:hot", "rel": "CALLS", "dst": "fn:a.py:cold"},
]
SCORES = ScoreSet(
    metric="sir_pagerank",
    table="centrality_scores",
    scores={"fn:a.py:hot": 0.9, "fn:a.py:cold": 0.01, "mod:a.py": 0.3},
    ranks={"fn:a.py:hot": 1, "mod:a.py": 2, "fn:a.py:cold": 3},
)


# ---------------------------------------------------------------------------
# Self-containment
# ---------------------------------------------------------------------------


def test_vis_library_is_inlined_not_cdn_linked() -> None:
    """The graph must not depend on reaching cdnjs to render."""
    html = build_graph_html(NODES, EDGES)
    assert "cdnjs.cloudflare.com/ajax/libs/vis-network" not in html


def test_no_relative_script_that_the_graph_depends_on() -> None:
    """The utils shim must be inlined, not referenced relatively.

    pyvis's template also leaves a ``../node_modules/vis/dist/vis.js`` tag
    behind even when inlining.  That one is harmless — the inlined bundle has
    already defined ``vis`` by the time it 404s — so it is deliberately not
    asserted against here.
    """
    html = build_graph_html(NODES, EDGES)
    assert 'src="lib/bindings/utils.js"' not in html


def test_vis_source_is_present() -> None:
    """The inlined bundle really carries the vis-network implementation."""
    html = build_graph_html(NODES, EDGES)
    assert "vis-network" in html
    assert len(html) > 500_000, "inlined bundle should dominate the payload"


# ---------------------------------------------------------------------------
# Centrality encoding
# ---------------------------------------------------------------------------


def _node_payload(html: str) -> dict[str, dict]:
    """Parse the vis.DataSet node array out of the generated page.

    Asserting on the payload rather than on raw substrings keeps these tests
    honest — pyvis's own template contains ``rgba(...)`` literals for its
    neighbourhood-highlight feature, so a naive substring check passes even
    when no node is faded.

    :param html: Generated page source.
    :return: Node dicts keyed by node ID.
    """
    import json
    import re

    payload = re.search(r"nodes\s*=\s*new vis\.DataSet\((\[.*?\])\);", html, re.S)
    assert payload, "could not locate the vis.DataSet node payload"
    return {n["id"]: n for n in json.loads(payload.group(1))}


def test_uniform_sizing_without_scores() -> None:
    """Without a metric, nodes keep per-kind sizes and stay fully opaque."""
    from pycode_kg import theme

    by_id = _node_payload(build_graph_html(NODES, EDGES, scores=None))
    assert by_id["mod:a.py"]["size"] == theme.KIND_PIXEL_SIZE["module"]
    assert by_id["fn:a.py:hot"]["size"] == theme.KIND_PIXEL_SIZE["function"]
    for node in by_id.values():
        assert not node["color"]["background"].startswith("rgba(")


def test_centrality_fades_nodes_by_rank() -> None:
    """With a metric, backgrounds become rgba and the top node is most opaque."""
    by_id = _node_payload(build_graph_html(NODES, EDGES, scores=SCORES))
    backgrounds = {k: v["color"]["background"] for k, v in by_id.items()}
    assert backgrounds["fn:a.py:hot"].startswith("rgba(")

    alpha = lambda s: float(s.rsplit(",", 1)[1].rstrip(") "))  # noqa: E731
    assert alpha(backgrounds["fn:a.py:hot"]) > alpha(backgrounds["fn:a.py:cold"])


def test_opacity_never_reaches_zero() -> None:
    """The least central node must stay visible."""
    by_id = _node_payload(build_graph_html(NODES, EDGES, scores=SCORES))
    bg = by_id["fn:a.py:cold"]["color"]["background"]
    assert float(bg.rsplit(",", 1)[1].rstrip(") ")) > 0.0


def test_more_central_node_renders_larger() -> None:
    """The top-ranked node must be drawn bigger than the bottom-ranked one."""
    by_id = _node_payload(build_graph_html(NODES, EDGES, scores=SCORES))
    assert by_id["fn:a.py:hot"]["size"] > by_id["fn:a.py:cold"]["size"]


def test_unscored_node_still_renders(caplog: pytest.LogCaptureFixture) -> None:
    """A node absent from the metric must not be dropped from the graph."""
    html = build_graph_html(NODES, EDGES, scores=SCORES)
    assert "fn:a.py:_priv" in html


def test_private_function_uses_its_own_colour() -> None:
    """``resolve_kind`` reaches the 2-D renderer, not just the 3-D one."""
    from pycode_kg import theme

    html = build_graph_html(NODES, EDGES)
    r, g, b = (
        int(theme.KIND_COLOR["private_function"].lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
    )
    assert theme.KIND_COLOR["private_function"] in html or f"rgba({r}, {g}, {b}" in html


# ---------------------------------------------------------------------------
# Node selection under the display cap
# ---------------------------------------------------------------------------


def _many(n: int) -> list[dict]:
    """Build *n* nodes in module-path order.

    :param n: How many nodes to build.
    :return: Node dicts, ``fn:z00`` first.
    """
    return [{"id": f"fn:z{i:02d}", "kind": "function", "name": f"f{i}"} for i in range(n)]


def test_no_selection_needed_under_the_limit() -> None:
    """Everything is kept when the graph already fits."""
    nodes = _many(5)
    kept, how = select_nodes(nodes, 10, None, "central")
    assert kept == nodes
    assert how == "all matching nodes"


def test_falls_back_to_path_order_without_scores() -> None:
    """With no metric loaded there is nothing to rank by."""
    kept, how = select_nodes(_many(10), 3, None, "central")
    assert [n["id"] for n in kept] == ["fn:z00", "fn:z01", "fn:z02"]
    assert how == "first by module path"


def _fake_expand(edges: dict[str, set[str]]):
    """Build an ``expand`` callable from an adjacency map.

    :param edges: Undirected adjacency, node ID to neighbour IDs.
    :return: A callable matching ``_select_nodes``' expand parameter.
    """

    def expand(seeds: set[str], hop: int) -> set[str]:
        reached = set(seeds)
        frontier = set(seeds)
        for _ in range(hop):
            nxt: set[str] = set()
            for node in frontier:
                nxt |= edges.get(node, set())
            frontier = nxt - reached
            reached |= nxt
        return reached

    return expand


def test_central_mode_seeds_then_expands_to_neighbours() -> None:
    """Seeding and expanding keeps the picture connected.

    Taking the top N by centrality alone strands most of them, because the most
    central nodes sit in different modules. Here z09 is the only seed the budget
    allows, so its neighbours should fill the rest rather than z08 and z07.
    """
    nodes = _many(10)
    scores = ScoreSet(
        metric="m",
        table="centrality_scores",
        scores={f"fn:z{i:02d}": float(i) for i in range(10)},
        ranks={f"fn:z{i:02d}": 10 - i for i in range(10)},
    )
    adjacency = {"fn:z09": {"fn:z00", "fn:z01"}}
    kept, how = select_nodes(nodes, 4, scores, "central", expand=_fake_expand(adjacency))
    ids = [n["id"] for n in kept]

    assert ids[0] == "fn:z09"
    assert {"fn:z00", "fn:z01"} <= set(ids)
    assert "plus neighbours" in how


def test_leftover_budget_falls_back_to_centrality() -> None:
    """When neighbours do not fill the budget, the next most central nodes do."""
    nodes = _many(10)
    scores = ScoreSet(
        metric="m",
        table="centrality_scores",
        scores={f"fn:z{i:02d}": float(i) for i in range(10)},
        ranks={f"fn:z{i:02d}": 10 - i for i in range(10)},
    )
    kept, _ = select_nodes(nodes, 4, scores, "central", expand=_fake_expand({}))
    assert [n["id"] for n in kept] == ["fn:z09", "fn:z08", "fn:z07", "fn:z06"]


def test_central_mode_without_expand_falls_back_to_top_n() -> None:
    """The cap must not silently discard the structurally important nodes.

    This is the behaviour that matters: the store returns nodes ordered by
    module path, so truncating it keeps an alphabetical slice rather than the
    code everything depends on.
    """
    nodes = _many(10)
    scores = ScoreSet(
        metric="sir_pagerank",
        table="centrality_scores",
        scores={f"fn:z{i:02d}": float(i) for i in range(10)},
        ranks={f"fn:z{i:02d}": 10 - i for i in range(10)},
    )
    kept, how = select_nodes(nodes, 3, scores, "central")
    assert [n["id"] for n in kept] == ["fn:z09", "fn:z08", "fn:z07"]
    assert "sir_pagerank" in how
    assert "plus neighbours" not in how


def test_path_mode_is_still_available(_=None) -> None:
    """The old behaviour remains selectable."""
    scores = ScoreSet(
        metric="m",
        table="centrality_scores",
        scores={"fn:z09": 1.0},
        ranks={"fn:z09": 1},
    )
    kept, _how = select_nodes(_many(10), 2, scores, "path")
    assert [n["id"] for n in kept] == ["fn:z00", "fn:z01"]


def test_unscored_nodes_sort_last_and_are_reported() -> None:
    """Nodes with no score must not crowd out ranked ones, and are counted."""
    nodes = _many(5)
    scores = ScoreSet(
        metric="m",
        table="centrality_scores",
        scores={"fn:z04": 1.0},
        ranks={"fn:z04": 1},
    )
    kept, how = select_nodes(nodes, 3, scores, "central")
    assert kept[0]["id"] == "fn:z04"
    assert "2 unscored" in how


def test_selection_is_deterministic() -> None:
    """Equal ranks break by node ID so reloads are reproducible."""
    nodes = _many(6)
    scores = ScoreSet(
        metric="m",
        table="centrality_scores",
        scores=dict.fromkeys((f"fn:z{i:02d}" for i in range(6)), 1.0),
        ranks=dict.fromkeys((f"fn:z{i:02d}" for i in range(6)), 1),
    )
    first, _ = select_nodes(list(nodes), 3, scores, "central")
    second, _ = select_nodes(list(reversed(nodes)), 3, scores, "central")
    assert [n["id"] for n in first] == [n["id"] for n in second]
