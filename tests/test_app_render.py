"""
test_app_render.py

Tests for the 2-D pyvis builder in :mod:`pycode_kg.app`.

These require the ``viz`` extra and are skipped without it.

The regression these guard is subtle and was only caught by actually rendering
the page in a browser: pyvis defaults to ``cdn_resources="local"``, which emits
*relative* asset paths.  Streamlit embeds the result in a ``srcdoc`` iframe,
which has no base URL, so those paths cannot resolve — the graph then renders
only if the cdnjs fallback is reachable, and fails silently with
``vis is not defined`` when it is not.
"""

from __future__ import annotations

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("pyvis")

import streamlit as st  # noqa: E402

# Importing app.py executes st.set_page_config at module scope, which is only
# legal inside a `streamlit run` process.
st.set_page_config = lambda **kwargs: None  # type: ignore[assignment]

from pycode_kg.analysis.scores import ScoreSet  # noqa: E402
from pycode_kg.app import _build_pyvis  # noqa: E402

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
    html = _build_pyvis(NODES, EDGES)
    assert "cdnjs.cloudflare.com/ajax/libs/vis-network" not in html


def test_no_relative_script_that_the_graph_depends_on() -> None:
    """The utils shim must be inlined, not referenced relatively.

    pyvis's template also leaves a ``../node_modules/vis/dist/vis.js`` tag
    behind even when inlining.  That one is harmless — the inlined bundle has
    already defined ``vis`` by the time it 404s — so it is deliberately not
    asserted against here.
    """
    html = _build_pyvis(NODES, EDGES)
    assert 'src="lib/bindings/utils.js"' not in html


def test_vis_source_is_present() -> None:
    """The inlined bundle really carries the vis-network implementation."""
    html = _build_pyvis(NODES, EDGES)
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

    by_id = _node_payload(_build_pyvis(NODES, EDGES, scores=None))
    assert by_id["mod:a.py"]["size"] == theme.KIND_PIXEL_SIZE["module"]
    assert by_id["fn:a.py:hot"]["size"] == theme.KIND_PIXEL_SIZE["function"]
    for node in by_id.values():
        assert not node["color"]["background"].startswith("rgba(")


def test_centrality_fades_nodes_by_rank() -> None:
    """With a metric, backgrounds become rgba and the top node is most opaque."""
    by_id = _node_payload(_build_pyvis(NODES, EDGES, scores=SCORES))
    backgrounds = {k: v["color"]["background"] for k, v in by_id.items()}
    assert backgrounds["fn:a.py:hot"].startswith("rgba(")

    alpha = lambda s: float(s.rsplit(",", 1)[1].rstrip(") "))  # noqa: E731
    assert alpha(backgrounds["fn:a.py:hot"]) > alpha(backgrounds["fn:a.py:cold"])


def test_opacity_never_reaches_zero() -> None:
    """The least central node must stay visible."""
    by_id = _node_payload(_build_pyvis(NODES, EDGES, scores=SCORES))
    bg = by_id["fn:a.py:cold"]["color"]["background"]
    assert float(bg.rsplit(",", 1)[1].rstrip(") ")) > 0.0


def test_more_central_node_renders_larger() -> None:
    """The top-ranked node must be drawn bigger than the bottom-ranked one."""
    by_id = _node_payload(_build_pyvis(NODES, EDGES, scores=SCORES))
    assert by_id["fn:a.py:hot"]["size"] > by_id["fn:a.py:cold"]["size"]


def test_unscored_node_still_renders(caplog: pytest.LogCaptureFixture) -> None:
    """A node absent from the metric must not be dropped from the graph."""
    html = _build_pyvis(NODES, EDGES, scores=SCORES)
    assert "fn:a.py:_priv" in html


def test_private_function_uses_its_own_colour() -> None:
    """``resolve_kind`` reaches the 2-D renderer, not just the 3-D one."""
    from pycode_kg import theme

    html = _build_pyvis(NODES, EDGES)
    r, g, b = (
        int(theme.KIND_COLOR["private_function"].lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
    )
    assert theme.KIND_COLOR["private_function"] in html or f"rgba({r}, {g}, {b}" in html
