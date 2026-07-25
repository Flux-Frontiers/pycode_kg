"""
Build self-contained interactive graph HTML from knowledge-graph nodes and edges.

Extracted from ``app.py`` so that producing a graph does not require Streamlit.
The 2-D explorer imports from here, and so does ``pycodekg viz-export``, which
writes the same HTML to a file without starting a server — previously the only
way to see a 2-D graph was to run the Streamlit app and look at it.

Nothing in this module touches Streamlit, so it is importable anywhere pyvis is
installed.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path

from pyvis.network import Network

from pycode_kg import theme
from pycode_kg.analysis.scores import ScoreSet

__all__ = [
    "CENTRALITY_MIN_OPACITY",
    "CENTRALITY_SIZE_RANGE",
    "SEED_FRACTION",
    "build_graph_html",
    "build_node_tooltip",
    "select_nodes",
]

#: Node diameter range in pixels when a centrality metric drives sizing.
CENTRALITY_SIZE_RANGE: tuple[int, int] = (8, 42)

#: Opacity floor for the least central node.  Never 0 — an invisible node is
#: indistinguishable from a missing one.
CENTRALITY_MIN_OPACITY: float = 0.35

#: Share of the node budget spent on seeds; the rest goes to their neighbours.
SEED_FRACTION: int = 4


def build_node_tooltip(n: dict, color: str, *, scores: ScoreSet | None = None) -> str:
    """
    Build a rich HTML tooltip for a pyvis node.

    Shows: kind badge · qualname · module path · line range · full docstring,
    plus the node's centrality rank when a metric is active.

    :param n: Node attribute dictionary containing keys such as ``kind``,
        ``qualname``, ``module_path``, ``lineno``, ``end_lineno``, and
        ``docstring``.
    :param color: Hex colour string used for the kind badge and left border.
    :param scores: Active centrality scores, used to add a rank line.
    :return: An HTML string suitable for use as a pyvis node ``title``.
    """
    kind = n.get("kind", "symbol")
    qualname = n.get("qualname") or n.get("name", "")
    module = n.get("module_path") or ""
    lineno = n.get("lineno")
    end_lineno = n.get("end_lineno")
    docstring = (n.get("docstring") or "").strip()

    # Line range string
    if lineno and end_lineno and end_lineno != lineno:
        line_str = f"lines {lineno}–{end_lineno}"
    elif lineno:
        line_str = f"line {lineno}"
    else:
        line_str = ""

    # Docstring — show up to 8 lines, wrap long lines
    doc_html = ""
    if docstring:
        doc_lines = docstring.splitlines()
        shown = doc_lines[:8]
        escaped = [
            line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for line in shown
        ]
        doc_html = (
            "<hr style='border:0;border-top:1px solid #444;margin:6px 0;'>"
            "<div style='font-family:monospace;font-size:11px;color:#ccc;"
            "white-space:pre-wrap;max-width:380px;'>"
            + "<br>".join(escaped)
            + ("…" if len(doc_lines) > 8 else "")
            + "</div>"
        )

    rank_html = ""
    if scores is not None:
        rank = scores.rank(n.get("id", ""))
        if rank is not None:
            rank_html = (
                f"<br><span style='color:#F1C40F;font-size:11px;'>"
                f"⬤ {scores.metric}: rank {rank} of {len(scores)} "
                f"({scores.score(n['id']):.5g})</span>"
            )

    tooltip = (
        f"<div style='font-family:sans-serif;font-size:12px;"
        f"background:#1e1e2e;color:#e0e0e0;padding:10px 14px;"
        f"border-radius:8px;border-left:4px solid {color};"
        f"max-width:400px;'>"
        f"<span style='background:{color};color:#fff;border-radius:4px;"
        f"padding:1px 7px;font-size:11px;font-weight:bold;'>{kind}</span>"
        f"&nbsp;&nbsp;<b style='font-size:13px;'>{qualname}</b>"
        + (
            f"<br><span style='color:#888;font-size:11px;'>"
            f"📄 {module}" + (f" &nbsp;·&nbsp; {line_str}" if line_str else "") + "</span>"
            if module
            else ""
        )
        + rank_html
        + doc_html
        + "</div>"
    )
    return tooltip


def build_graph_html(
    nodes: list[dict],
    edges: list[dict],
    *,
    height: str = "620px",
    seed_ids: set[str] | None = None,
    physics: bool = True,
    scores: ScoreSet | None = None,
) -> str:
    """
    Build a pyvis Network from node/edge dicts and return the HTML string.

    Seed nodes (from semantic search) are rendered with a gold border.
    Hovering shows a rich tooltip; clicking a node opens a floating detail
    panel inside the graph iframe with the full docstring and metadata.

    When *scores* is supplied, node diameter encodes the metric's magnitude and
    node opacity encodes its rank percentile.  Without it, diameter falls back
    to a per-kind constant and every node is fully opaque — the behaviour
    before centrality was wired in.

    :param nodes: List of node attribute dicts, each containing at minimum
        an ``id`` key plus optional ``kind``, ``name``, ``qualname``,
        ``module_path``, ``lineno``, ``end_lineno``, and ``docstring``.
    :param edges: List of edge dicts with ``src``, ``dst``, and ``rel`` keys.
    :param height: CSS height string for the iframe (e.g. ``"620px"``).
    :param seed_ids: Set of node IDs that originated from the semantic seed
        query; these are highlighted with a gold border.
    :param physics: Whether to enable the Barnes-Hut physics simulation.
    :param scores: Centrality scores driving node size and opacity, or ``None``
        for uniform per-kind sizing.
    :return: A self-contained HTML string that renders the interactive graph.
    """
    net = Network(
        height=height,
        width="100%",
        bgcolor="#0e1117",
        font_color="#e0e0e0",
        directed=True,
        notebook=False,
        # pyvis defaults to cdn_resources="local", which emits *relative* asset
        # paths (lib/bindings/utils.js, ../node_modules/vis/dist/vis.js) plus a
        # cdnjs fallback.  Streamlit embeds this HTML in a srcdoc iframe, which
        # has no base URL, so the relative paths cannot resolve and the graph
        # renders only if cdnjs is reachable at view time — it fails silently
        # with "vis is not defined" offline or behind a restrictive network.
        # "in_line" inlines vis-network so the HTML is genuinely self-contained.
        cdn_resources="in_line",
    )
    net.set_options(
        json.dumps(
            {
                "physics": {
                    "enabled": physics,
                    "barnesHut": {
                        "gravitationalConstant": -8000,
                        "centralGravity": 0.3,
                        "springLength": 120,
                        "springConstant": 0.04,
                        "damping": 0.09,
                    },
                    "stabilization": {"iterations": 150},
                },
                "edges": {
                    "smooth": {"type": "dynamic"},
                    "arrows": {"to": {"enabled": True, "scaleFactor": 0.6}},
                    "font": {"size": 10, "color": "#aaaaaa"},
                },
                "interaction": {
                    "hover": True,
                    "tooltipDelay": 80,
                    "navigationButtons": True,
                    "keyboard": True,
                },
            }
        )
    )

    seed_ids = seed_ids or set()

    # Build a JS-safe node data map for the click panel
    node_data_js: dict[str, dict] = {}

    lo_size, hi_size = CENTRALITY_SIZE_RANGE

    for n in nodes:
        node_id = n["id"]
        kind = theme.resolve_kind(n.get("kind", "symbol"), n.get("name", ""))
        color = theme.color_for(kind)
        shape = theme.shape_for(kind)
        label = n.get("name", node_id)
        if len(label) > 28:
            label = label[:25] + "…"
        border_color = "#FFD700" if node_id in seed_ids else color
        tooltip = build_node_tooltip(n, color, scores=scores)

        if scores is None:
            size: float = theme.KIND_PIXEL_SIZE.get(kind, 12)
            background = color
        else:
            # Both size and opacity derive from rank percentile.  Centrality
            # scores are top-heavy enough that magnitude-preserving scalers
            # bunch almost every node at one end of the range; see
            # ScoreSet.scaled for the measurements behind that default.
            size = scores.scaled(node_id, lo_size, hi_size, default=lo_size)
            alpha = CENTRALITY_MIN_OPACITY + (1.0 - CENTRALITY_MIN_OPACITY) * (
                scores.percentile(node_id)
            )
            background = theme.with_alpha(color, alpha)

        net.add_node(
            node_id,
            label=label,
            title=tooltip,
            color={
                "background": background,
                "border": border_color,
                "highlight": {"background": color, "border": "#FFFFFF"},
            },
            shape=shape,
            size=size,
            borderWidth=3 if node_id in seed_ids else 1,
            font={"size": 11},
        )
        node_data_js[n["id"]] = {
            "id": n["id"],
            "kind": kind,
            "color": color,
            "qualname": n.get("qualname") or n.get("name", ""),
            "module": n.get("module_path") or "",
            "lineno": n.get("lineno"),
            "end_lineno": n.get("end_lineno"),
            "docstring": (n.get("docstring") or "").strip(),
        }

    for e in edges:
        rel = e.get("rel", "")
        ecolor = theme.rel_color(rel)
        net.add_edge(
            e["src"],
            e["dst"],
            label=rel,
            color=ecolor,
            width=1.5,
            title=rel,
        )

    # Write to a temp file and read back as HTML string
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        tmp_path = f.name
    net.save_graph(tmp_path)
    html = Path(tmp_path).read_text(encoding="utf-8")
    os.unlink(tmp_path)

    # Inject: floating click-detail panel + node data map
    node_data_json = json.dumps(node_data_js, ensure_ascii=False)

    panel_css = """
<style>
#pycodekg-panel {
  display: none;
  position: fixed;
  top: 12px;
  right: 12px;
  width: 340px;
  max-height: 88vh;
  overflow-y: auto;
  background: #1e1e2e;
  border-radius: 10px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.6);
  z-index: 9999;
  font-family: sans-serif;
  font-size: 13px;
  color: #e0e0e0;
}
#pycodekg-panel-inner { padding: 14px 16px 16px 16px; }
#pycodekg-panel-close {
  position: absolute;
  top: 8px; right: 10px;
  cursor: pointer;
  font-size: 18px;
  color: #888;
  line-height: 1;
  background: none;
  border: none;
}
#pycodekg-panel-close:hover { color: #fff; }
#pycodekg-panel-docstring {
  background: #12121f;
  border: 1px solid #2a2a3e;
  border-radius: 6px;
  padding: 8px 10px;
  font-family: monospace;
  font-size: 12px;
  color: #c9d1d9;
  white-space: pre-wrap;
  word-break: break-word;
  margin-top: 8px;
  max-height: 300px;
  overflow-y: auto;
}
</style>
"""

    panel_html = """
<div id="pycodekg-panel">
  <button id="pycodekg-panel-close" onclick="document.getElementById('pycodekg-panel').style.display='none'">✕</button>
  <div id="pycodekg-panel-inner">
    <div id="pycodekg-panel-badge"></div>
    <div id="pycodekg-panel-qualname" style="font-size:15px;font-weight:bold;margin:6px 0 2px 0;"></div>
    <div id="pycodekg-panel-meta" style="color:#888;font-size:11px;font-family:monospace;"></div>
    <div id="pycodekg-panel-id" style="color:#444;font-size:10px;font-family:monospace;margin-top:2px;"></div>
    <div id="pycodekg-panel-docstring"></div>
  </div>
</div>
"""

    panel_js = f"""
<script>
(function() {{
  var NODE_DATA = {node_data_json};

  function showPanel(nodeId) {{
    var n = NODE_DATA[nodeId];
    if (!n) return;

    var panel = document.getElementById('pycodekg-panel');
    var badge = document.getElementById('pycodekg-panel-badge');
    var qname = document.getElementById('pycodekg-panel-qualname');
    var meta  = document.getElementById('pycodekg-panel-meta');
    var nid   = document.getElementById('pycodekg-panel-id');
    var doc   = document.getElementById('pycodekg-panel-docstring');

    badge.innerHTML = '<span style="background:' + n.color + ';color:#fff;border-radius:4px;' +
      'padding:2px 8px;font-size:11px;font-weight:bold;font-family:monospace;">' +
      n.kind + '</span>';

    qname.textContent = n.qualname;
    qname.style.color = '#f0f0f0';

    var lineStr = '';
    if (n.lineno && n.end_lineno && n.end_lineno !== n.lineno) {{
      lineStr = ' · lines ' + n.lineno + '–' + n.end_lineno;
    }} else if (n.lineno) {{
      lineStr = ' · line ' + n.lineno;
    }}
    meta.textContent = (n.module || '—') + lineStr;

    nid.textContent = 'id: ' + n.id;

    if (n.docstring) {{
      doc.style.display = 'block';
      doc.textContent = n.docstring;
    }} else {{
      doc.style.display = 'block';
      doc.textContent = '(no docstring)';
      doc.style.color = '#555';
    }}

    panel.style.borderLeft = '5px solid ' + n.color;
    panel.style.display = 'block';
  }}

  function fixHtmlTitles() {{
    // vis-network renders string titles as plain text; swap in DOM elements
    // so that the rich HTML tooltips display correctly.
    var ids = network.body.data.nodes.getIds();
    ids.forEach(function(id) {{
      var node = network.body.data.nodes.get(id);
      if (node && typeof node.title === 'string' && node.title.trim().charAt(0) === '<') {{
        var div = document.createElement('div');
        div.innerHTML = node.title;
        network.body.data.nodes.update({{id: id, title: div}});
      }}
    }});
  }}

  function waitForNetwork() {{
    if (typeof network === 'undefined') {{
      setTimeout(waitForNetwork, 200);
      return;
    }}
    fixHtmlTitles();
    network.on('click', function(params) {{
      if (params.nodes && params.nodes.length > 0) {{
        showPanel(String(params.nodes[0]));
      }} else {{
        // click on empty space — hide panel
        document.getElementById('pycodekg-panel').style.display = 'none';
      }}
    }});
  }}
  waitForNetwork();
}})();
</script>
"""

    html = html.replace("</head>", panel_css + "\n</head>")
    html = html.replace("</body>", panel_html + panel_js + "\n</body>")
    return html


def _describe(scores: ScoreSet, kept: list[str], suffix: str) -> str:
    """Summarise a selection for the caption above the graph.

    Reporting how many kept nodes carry no score matters once neighbours are
    pulled in by expansion: those are frequently unscored, and a reader should
    not assume every node on screen was ranked.

    :param scores: The active metric.
    :param kept: Node IDs that were kept.
    :param suffix: Extra text describing the strategy.
    :return: Human-readable description.
    """
    unscored = sum(1 for i in kept if scores.rank(i) is None)
    tail = f" ({unscored} unscored)" if unscored else ""
    return f"most central by {scores.metric}{suffix}{tail}"


def select_nodes(
    nodes: list[dict],
    limit: int,
    scores: ScoreSet | None,
    mode: str,
    expand: Callable[[set[str], int], set[str]] | None = None,
) -> tuple[list[dict], str]:
    """Reduce *nodes* to at most *limit*, choosing which ones to keep.

    The graph can only draw a few hundred nodes, so which ones survive the cap
    decides what the user actually sees.  Two strategies, and the difference is
    stark on a real graph:

    * ``"path"`` truncates the store's natural order (``ORDER BY module_path,
      lineno``).  Because that order is contiguous by module, the result is well
      connected — but it is an alphabetical slice, and on pycode_kg's own graph
      it is mostly ``test_*`` and ``a*`` modules with none of the important code.
    * ``"central"`` seeds on the most central nodes and then pulls in their
      graph neighbours until the budget is spent.

    Seeding *and expanding* rather than simply taking the top N by centrality is
    the important detail.  The most central nodes are scattered across modules,
    so keeping only them strands most of them: measured on pycode_kg at a cap of
    150, top-N-by-centrality left 47 nodes with no edges at all and halved the
    edge count, producing a field of dots rather than a graph.  Expanding from a
    smaller seed set keeps the picture connected.

    :param nodes: Candidate nodes, already filtered.
    :param limit: Maximum number to keep.
    :param scores: Active centrality scores, or ``None``.
    :param mode: ``"central"`` or ``"path"``.
    :param expand: Callable taking ``(seed_ids, hop)`` and returning the node IDs
        reachable within that many hops.  Without it, ``"central"`` degrades to
        top-N by centrality.
    :return: The kept nodes and a short description of how they were chosen.
    """
    if len(nodes) <= limit:
        return nodes, "all matching nodes"
    if mode != "central" or scores is None:
        return nodes[:limit], "first by module path"

    by_id = {n["id"]: n for n in nodes}
    ranked = sorted(
        by_id,
        key=lambda i: (scores.rank(i) is None, scores.rank(i) or 0, i),
    )

    if expand is None:
        top = ranked[:limit]
        return [by_id[i] for i in top], _describe(scores, top, "")

    # Seed on a fraction of the budget so there is room for the neighbourhood.
    seed_count = max(1, limit // SEED_FRACTION)
    seeds = set(ranked[:seed_count])
    reachable = expand(seeds, 1) & by_id.keys()

    kept: list[str] = list(ranked[:seed_count])
    seen = set(kept)
    for node_id in sorted(
        reachable, key=lambda i: (scores.rank(i) is None, scores.rank(i) or 0, i)
    ):
        if len(kept) >= limit:
            break
        if node_id not in seen:
            kept.append(node_id)
            seen.add(node_id)
    # Any leftover budget goes to the next most central nodes.
    for node_id in ranked:
        if len(kept) >= limit:
            break
        if node_id not in seen:
            kept.append(node_id)
            seen.add(node_id)

    return [by_id[i] for i in kept], _describe(scores, kept, ", plus neighbours")
