#!/usr/bin/env python3
"""
app.py — PyCodeKG Streamlit Visualizer

Interactive knowledge-graph explorer with:
  • Sidebar: configure repo/db paths and query parameters
  • Graph tab: pyvis interactive graph of the full KG or query results
  • Query tab: hybrid semantic+structural query with ranked node results
  • Snippets tab: source-grounded snippet pack viewer

Run with:
    poetry run pycodekg-viz
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import streamlit as st
from pyvis.network import Network

from pycode_kg.store import DEFAULT_RELS, GraphStore

# ---------------------------------------------------------------------------
# Constants — colours and shapes per node kind
# ---------------------------------------------------------------------------

_KIND_COLOR: dict[str, str] = {
    "module": "#4A90D9",  # blue
    "class": "#E67E22",  # orange
    "function": "#27AE60",  # green
    "method": "#8E44AD",  # purple
    "symbol": "#95A5A6",  # grey
}

_KIND_SHAPE: dict[str, str] = {
    "module": "box",
    "class": "diamond",
    "function": "ellipse",
    "method": "dot",
    "symbol": "triangle",
}

_REL_COLOR: dict[str, str] = {
    "CONTAINS": "#BDC3C7",
    "CALLS": "#E74C3C",
    "IMPORTS": "#3498DB",
    "INHERITS": "#F39C12",
}

# Honour the PYCODEKG_DB env var so the Docker image (which mounts
# persistent data at /data) works out of the box without the user
# having to change the sidebar path manually.
import os as _os  # noqa: E402

_DEFAULT_DB = _os.environ.get("PYCODEKG_DB", ".pycodekg/graph.sqlite")
_DEFAULT_LANCEDB = _os.environ.get("PYCODEKG_LANCEDB", ".pycodekg/lancedb")

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="PyCodeKG Explorer",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Minimal CSS tweaks
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] { font-size: 1rem; padding: 6px 18px; }
    .node-card {
        background: #1e1e2e;
        border-left: 4px solid #4A90D9;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-family: monospace;
        font-size: 0.85rem;
    }
    .edge-row { font-family: monospace; font-size: 0.82rem; color: #aaa; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------


def _init_state() -> None:
    """
    Initialize Streamlit session state with default values.

    Sets keys for database path, store, query/pack results, graph data,
    PyCodeKG instance, and selected node if they are not already present.
    """
    defaults = {
        "db_path": _DEFAULT_DB,
        "store": None,
        "store_loaded_path": None,
        "query_result": None,
        "pack_result": None,
        "graph_nodes": None,
        "graph_edges": None,
        "kg": None,
        "kg_loaded_path": None,
        "selected_node_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Store helpers
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner="Opening SQLite store…")
def _load_store(db_path: str) -> GraphStore | None:
    """
    Load and cache a GraphStore from the given SQLite database path.

    Returns ``None`` if the file does not exist.

    :param db_path: Filesystem path to the SQLite database file.
    :return: A connected ``GraphStore`` instance, or ``None`` if the file is absent.
    """
    p = Path(db_path)
    if not p.exists():
        return None
    return GraphStore(db_path)


def _get_store() -> GraphStore | None:
    """
    Retrieve the current GraphStore, loading it if the database path has changed.

    Compares the cached loaded path against ``st.session_state.db_path`` and
    calls ``_load_store`` only when the path differs.

    :return: The active ``GraphStore`` instance, or ``None`` if no database is available.
    """
    db = st.session_state.db_path
    if st.session_state.store_loaded_path != db:
        st.session_state.store = _load_store(db)
        st.session_state.store_loaded_path = db
    return st.session_state.store


# ---------------------------------------------------------------------------
# PyCodeKG helper (lazy, cached per (db_path, repo_root, model))
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner="Loading PyCodeKG (embedder may take a moment)…")
def _load_kg(repo_root: str, db_path: str, lancedb_dir: str, model: str):
    """
    Load and cache a ``PyCodeKG`` instance for the given configuration.

    Keyed on all four parameters so that changing any one triggers a fresh load.
    This is the main entry point for query/snippet execution in the UI and the
    configuration boundary between Streamlit controls and runtime PyCodeKG state.

    :param repo_root: Root directory of the Python repository to analyse.
    :param db_path: Path to the SQLite graph database.
    :param lancedb_dir: Directory for the LanceDB vector index.
    :param model: Name of the sentence-transformer embedding model to use.
    :return: An initialised ``PyCodeKG`` instance.
    """
    from pycode_kg import PyCodeKG  # pylint: disable=import-outside-toplevel

    return PyCodeKG(
        repo_root=repo_root,
        db_path=db_path,
        lancedb_dir=lancedb_dir,
        model=model,
    )


# ---------------------------------------------------------------------------
# pyvis graph builder
# ---------------------------------------------------------------------------


def _build_node_tooltip(n: dict, color: str) -> str:
    """
    Build a rich HTML tooltip for a pyvis node.

    Shows: kind badge · qualname · module path · line range · full docstring.
    Rendered inside the pyvis hover popup (supports basic HTML).

    :param n: Node attribute dictionary containing keys such as ``kind``,
        ``qualname``, ``module_path``, ``lineno``, ``end_lineno``, and
        ``docstring``.
    :param color: Hex colour string used for the kind badge and left border.
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
        + doc_html
        + "</div>"
    )
    return tooltip


def _build_pyvis(
    nodes: list[dict],
    edges: list[dict],
    *,
    height: str = "620px",
    seed_ids: set[str] | None = None,
    physics: bool = True,
) -> str:
    """
    Build a pyvis Network from node/edge dicts and return the HTML string.

    Seed nodes (from semantic search) are rendered with a gold border.
    Hovering shows a rich tooltip; clicking a node opens a floating detail
    panel inside the graph iframe with the full docstring and metadata.

    :param nodes: List of node attribute dicts, each containing at minimum
        an ``id`` key plus optional ``kind``, ``name``, ``qualname``,
        ``module_path``, ``lineno``, ``end_lineno``, and ``docstring``.
    :param edges: List of edge dicts with ``src``, ``dst``, and ``rel`` keys.
    :param height: CSS height string for the iframe (e.g. ``"620px"``).
    :param seed_ids: Set of node IDs that originated from the semantic seed
        query; these are highlighted with a gold border.
    :param physics: Whether to enable the Barnes-Hut physics simulation.
    :return: A self-contained HTML string that renders the interactive graph.
    """
    net = Network(
        height=height,
        width="100%",
        bgcolor="#0e1117",
        font_color="#e0e0e0",
        directed=True,
        notebook=False,
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

    for n in nodes:
        kind = n.get("kind", "symbol")
        color = _KIND_COLOR.get(kind, "#95A5A6")
        shape = _KIND_SHAPE.get(kind, "dot")
        label = n.get("name", n["id"])
        if len(label) > 28:
            label = label[:25] + "…"
        border_color = "#FFD700" if n["id"] in seed_ids else color
        tooltip = _build_node_tooltip(n, color)
        net.add_node(
            n["id"],
            label=label,
            title=tooltip,
            color={
                "background": color,
                "border": border_color,
                "highlight": {"background": color, "border": "#FFFFFF"},
            },
            shape=shape,
            size=18 if kind in ("class", "module") else 12,
            borderWidth=3 if n["id"] in seed_ids else 1,
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
        ecolor = _REL_COLOR.get(rel, "#888888")
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


# ---------------------------------------------------------------------------
# Node detail panel
# ---------------------------------------------------------------------------


def _render_node_detail(node: dict, store: GraphStore | None = None) -> None:
    """
    Render a rich detail card for a single node.

    Shows: kind badge, qualname, module + line range, full docstring,
    and (if store is provided) the node's immediate edges.

    :param node: Node attribute dictionary containing at minimum an ``id``
        key plus optional ``kind``, ``qualname``, ``name``, ``module_path``,
        ``lineno``, ``end_lineno``, and ``docstring``.
    :param store: An optional ``GraphStore`` used to look up adjacent edges.
        When ``None``, the edges section is omitted.
    """
    kind = node.get("kind", "symbol")
    color = _KIND_COLOR.get(kind, "#95A5A6")
    qualname = node.get("qualname") or node.get("name", "")
    module = node.get("module_path") or ""
    lineno = node.get("lineno")
    end_lineno = node.get("end_lineno")
    docstring = (node.get("docstring") or "").strip()
    node_id = node.get("id", "")

    # Line range
    if lineno and end_lineno and end_lineno != lineno:
        line_str = f"lines {lineno}-{end_lineno}"
    elif lineno:
        line_str = f"line {lineno}"
    else:
        line_str = "-"

    st.markdown(
        f"""
        <div style="background:#1e1e2e;border-left:5px solid {color};
                    border-radius:8px;padding:14px 18px;margin-bottom:8px;">
          <span style="background:{color};color:#fff;border-radius:4px;
                       padding:2px 9px;font-size:12px;font-weight:bold;
                       font-family:monospace;">{kind}</span>
          &nbsp;
          <span style="font-size:17px;font-weight:bold;color:#f0f0f0;">
            {qualname}
          </span>
          <br>
          <span style="color:#888;font-size:12px;font-family:monospace;">
            📄 {module or "—"} &nbsp;·&nbsp; {line_str}
          </span>
          <br>
          <span style="color:#555;font-size:10px;font-family:monospace;">
            id: {node_id}
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if docstring:
        st.markdown("**📝 Docstring**")
        st.markdown(
            f"""
            <div style="background:#12121f;border-radius:6px;padding:10px 14px;
                        font-family:monospace;font-size:13px;color:#c9d1d9;
                        white-space:pre-wrap;border:1px solid #2a2a3e;">
{docstring.replace("<", "&lt;").replace(">", "&gt;")}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("*No docstring.*")

    # Immediate edges from the store
    if store and node_id:
        st.markdown("**🔗 Edges**")
        try:
            rows = store.con.execute(
                "SELECT src, rel, dst FROM edges WHERE src = ? OR dst = ? LIMIT 60",
                (node_id, node_id),
            ).fetchall()
            if rows:
                import pandas as pd  # pylint: disable=import-outside-toplevel  # pylint: disable=import-outside-toplevel

                edf = pd.DataFrame([{"src": r[0], "rel": r[1], "dst": r[2]} for r in rows])
                st.dataframe(edf, use_container_width=True, hide_index=True)
            else:
                st.caption("*No edges.*")
        except (AttributeError, ValueError, RuntimeError, KeyError):
            pass


def _node_detail_section(
    nodes: list[dict],
    store: GraphStore | None,
    *,
    key_prefix: str = "detail",
) -> None:
    """
    Render a searchable node-detail section below a graph.

    Users pick a node from a selectbox (or type a name) and see the full
    detail card.  This is the Streamlit-native complement to the pyvis
    hover tooltip — it persists on screen and shows the complete docstring
    plus edge table.

    :param nodes: List of node attribute dicts to populate the selectbox.
    :param store: An optional ``GraphStore`` passed through to
        ``_render_node_detail`` for edge lookups.
    :param key_prefix: String prefix for Streamlit widget keys, used to
        avoid key collisions when multiple instances are rendered on the
        same page.
    """
    if not nodes:
        return

    st.markdown("---")
    st.subheader("🔎 Node Detail")

    # Build label → node mapping (qualname preferred, fall back to name)
    label_map: dict[str, dict] = {}
    for n in nodes:
        lbl = n.get("qualname") or n.get("name") or n["id"]
        # Disambiguate duplicates
        if lbl in label_map:
            lbl = f"{lbl}  [{n['id']}]"
        label_map[lbl] = n

    options = ["— select a node —"] + sorted(label_map.keys())
    chosen = st.selectbox(
        "Select node to inspect",
        options=options,
        index=0,
        key=f"{key_prefix}_node_select",
        help="Pick any node to see its full docstring and edges.",
    )

    if chosen and chosen != "— select a node —":
        node = label_map.get(chosen)
        if node:
            _render_node_detail(node, store=store)


# ---------------------------------------------------------------------------
# Legend widget
# ---------------------------------------------------------------------------


def _render_legend() -> None:
    """
    Render the graph legend showing node-kind colours and edge-relation colours.

    Displays colour swatches for each entry in ``_KIND_COLOR`` and
    ``_REL_COLOR`` as inline Streamlit markdown columns.
    """
    st.markdown("**Node kinds**")
    cols = st.columns(len(_KIND_COLOR))
    for col, (kind, color) in zip(cols, _KIND_COLOR.items()):
        col.markdown(
            f'<span style="display:inline-block;width:12px;height:12px;'
            f'background:{color};border-radius:50%;margin-right:4px;"></span>'
            f"`{kind}`",
            unsafe_allow_html=True,
        )
    st.markdown("**Edge relations**")
    cols2 = st.columns(len(_REL_COLOR))
    for col, (rel, color) in zip(cols2, _REL_COLOR.items()):
        col.markdown(
            f'<span style="display:inline-block;width:20px;height:3px;'
            f'background:{color};margin-right:4px;vertical-align:middle;"></span>'
            f"`{rel}`",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------


def _render_sidebar() -> dict:
    """
    Render the sidebar controls and return a configuration dictionary.

    Exposes controls for the SQLite path, repo root, LanceDB directory,
    embedding model, query parameters (k, hops, relations, include_symbols),
    graph display options (max nodes, physics, height), and build buttons
    for the graph and semantic index.

    :return: A dict with keys ``db_path``, ``repo_root``, ``lancedb_dir``,
        ``model``, ``k``, ``hop``, ``rels``, ``include_symbols``,
        ``max_graph_nodes``, ``physics_on``, ``graph_height``, and ``store``.
    """
    st.sidebar.title("PyCodeKG Explorer")
    st.sidebar.markdown("---")

    st.sidebar.subheader("Database")
    db_path = st.sidebar.text_input(
        "SQLite path",
        value=st.session_state.db_path,
        help="Path to .pycodekg/graph.sqlite (relative or absolute)",
    )
    st.session_state.db_path = db_path

    store = _get_store()
    if store is None:
        st.sidebar.warning(
            f"[WARNING] `{db_path}` not found.\n\n"
            "Set **Repo root** below and click **Build Graph** to create it."
        )
    else:
        s = store.stats()
        st.sidebar.success(f"{s['total_nodes']} nodes · {s['total_edges']} edges")
        with st.sidebar.expander("Node counts"):
            for k, v in sorted(s["node_counts"].items()):
                st.write(f"`{k}`: {v}")
        with st.sidebar.expander("Edge counts"):
            for k, v in sorted(s["edge_counts"].items()):
                st.write(f"`{k}`: {v}")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Paths & model")

    repo_root = st.sidebar.text_input(
        "Repo root",
        value=str(Path.cwd()),
        help="Root directory of the Python repository to analyse",
    )
    lancedb_dir = st.sidebar.text_input(
        "LanceDB dir",
        value=_DEFAULT_LANCEDB,
        help="Directory for the LanceDB vector index",
    )
    model = st.sidebar.selectbox(
        "Embedding model",
        [
            "BAAI/bge-small-en-v1.5",
            "all-mpnet-base-v2",
            "all-MiniLM-L6-v2",
            "jinaai/jina-embeddings-v3",
            "paraphrase-MiniLM-L3-v2",
        ],
        index=0,
    )
    k = st.sidebar.slider("Top-K seeds (k)", min_value=1, max_value=30, value=8)
    hop = st.sidebar.slider("Graph hops", min_value=0, max_value=4, value=1)

    all_rels = list(DEFAULT_RELS)
    chosen_rels = st.sidebar.multiselect(
        "Edge relations",
        options=all_rels,
        default=all_rels,
    )

    include_symbols = st.sidebar.checkbox("Include symbol nodes", value=False)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🗺️ Graph display")
    max_graph_nodes = st.sidebar.slider(
        "Max nodes in graph view", min_value=20, max_value=500, value=150, step=10
    )
    physics_on = st.sidebar.checkbox("Physics simulation", value=True)
    graph_height = st.sidebar.select_slider(
        "Graph height",
        options=["400px", "500px", "620px", "750px", "900px"],
        value="620px",
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔨 Build pipeline")

    build_col1, build_col2 = st.sidebar.columns(2)
    build_graph_btn = build_col1.button(
        "🔨 Build Graph",
        help="Run AST extraction → SQLite (fast, no embeddings)",
        use_container_width=True,
    )
    build_index_btn = build_col2.button(
        "🧠 Build Index",
        help="Embed nodes → LanceDB (requires graph to exist)",
        use_container_width=True,
    )
    build_all_btn = st.sidebar.button(
        "⚡ Build All (graph + index)",
        help="Full pipeline: AST → SQLite → LanceDB",
        use_container_width=True,
        type="primary",
    )

    if build_graph_btn or build_all_btn:
        with st.sidebar:
            with st.spinner("Building graph (AST → SQLite)…"):
                try:
                    from pycode_kg import (  # pylint: disable=import-outside-toplevel
                        PyCodeKG,
                    )

                    kg = PyCodeKG(
                        repo_root=repo_root,
                        db_path=db_path,
                        lancedb_dir=lancedb_dir,
                        model=model,
                    )
                    if build_all_btn:
                        stats = kg.build(wipe=True)
                        st.success(
                            f"✅ Built: {stats.total_nodes} nodes, "
                            f"{stats.total_edges} edges, "
                            f"{stats.indexed_rows} vectors"
                        )
                    else:
                        stats = kg.build_graph(wipe=True)
                        st.success(
                            f"✅ Graph: {stats.total_nodes} nodes, {stats.total_edges} edges"
                        )
                    # Invalidate cached store so sidebar refreshes
                    st.session_state.store_loaded_path = None
                    st.session_state.graph_nodes = None
                    _load_store.clear()  # type: ignore[attr-defined]
                    st.rerun()
                except (AttributeError, ValueError, RuntimeError, OSError) as exc:
                    st.error(f"Build failed: {exc}")

    if build_index_btn and not build_all_btn:
        with st.sidebar:
            with st.spinner("Building semantic index (SQLite → LanceDB)…"):
                try:
                    from pycode_kg import (  # pylint: disable=import-outside-toplevel
                        PyCodeKG,
                    )

                    kg = PyCodeKG(
                        repo_root=repo_root,
                        db_path=db_path,
                        lancedb_dir=lancedb_dir,
                        model=model,
                    )
                    stats = kg.build_index(wipe=True)
                    st.success(f"✅ Index: {stats.indexed_rows} vectors (dim={stats.index_dim})")
                    _load_kg.clear()  # type: ignore[attr-defined]
                except (AttributeError, ValueError, RuntimeError, OSError) as exc:
                    st.error(f"Index build failed: {exc}")

    return {
        "db_path": db_path,
        "repo_root": repo_root,
        "lancedb_dir": lancedb_dir,
        "model": model,
        "k": k,
        "hop": hop,
        "rels": tuple(chosen_rels) if chosen_rels else DEFAULT_RELS,
        "include_symbols": include_symbols,
        "max_graph_nodes": max_graph_nodes,
        "physics_on": physics_on,
        "graph_height": graph_height,
        "store": store,
    }


# ---------------------------------------------------------------------------
# Tab 1 — Full graph browser
# ---------------------------------------------------------------------------


def _tab_graph(cfg: dict) -> None:
    """
    Render the Graph Browser tab.

    Loads nodes and edges from the store according to the sidebar filters,
    displays the interactive pyvis graph, a node table expander, and the
    node-detail section.

    :param cfg: Configuration dictionary returned by ``_render_sidebar``,
        providing keys such as ``store``, ``max_graph_nodes``,
        ``graph_height``, and ``physics_on``.
    """
    st.header("🗺️ Knowledge Graph Browser")
    store: GraphStore | None = cfg["store"]
    if store is None:
        st.warning("No database loaded. Set the SQLite path in the sidebar.")
        return

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        kind_filter = st.multiselect(
            "Filter node kinds",
            options=list(_KIND_COLOR.keys()),
            default=["module", "class", "function", "method"],
            key="graph_kind_filter",
        )
    with col2:
        module_filter = st.text_input(
            "Filter by module path (substring)",
            value="",
            key="graph_module_filter",
        )
    with col3:
        st.write("")
        st.write("")
        load_btn = st.button("🔄 Load / Refresh", key="graph_load_btn", type="primary")

    if load_btn or st.session_state.graph_nodes is None:
        with st.spinner("Loading nodes and edges…"):
            nodes = store.query_nodes(kinds=kind_filter if kind_filter else None)
            if module_filter.strip():
                nodes = [n for n in nodes if module_filter.strip() in (n.get("module_path") or "")]
            max_n = cfg["max_graph_nodes"]
            if len(nodes) > max_n:
                st.info(f"Showing first {max_n} of {len(nodes)} nodes (increase limit in sidebar).")
                nodes = nodes[:max_n]
            node_ids = {n["id"] for n in nodes}
            edges = store.edges_within(node_ids)
            st.session_state.graph_nodes = nodes
            st.session_state.graph_edges = edges

    nodes = st.session_state.graph_nodes or []
    edges = st.session_state.graph_edges or []

    if not nodes:
        st.info("No nodes match the current filters.")
        return

    st.caption(f"Showing **{len(nodes)}** nodes · **{len(edges)}** edges")
    _render_legend()
    st.markdown("---")

    html = _build_pyvis(
        nodes,
        edges,
        height=cfg["graph_height"],
        physics=cfg["physics_on"],
    )
    st.components.v1.html(html, height=int(cfg["graph_height"].replace("px", "")), scrolling=False)

    with st.expander("📋 Node table"):
        import pandas as pd  # pylint: disable=import-outside-toplevel

        df = pd.DataFrame(
            [
                {
                    "id": n["id"],
                    "kind": n["kind"],
                    "name": n["name"],
                    "qualname": n.get("qualname", ""),
                    "module": n.get("module_path", ""),
                    "line": n.get("lineno", ""),
                }
                for n in nodes
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Node detail panel — hover tooltip complement
    _node_detail_section(nodes, store, key_prefix="graph")


# ---------------------------------------------------------------------------
# Tab 2 — Hybrid query
# ---------------------------------------------------------------------------


def _tab_query(cfg: dict) -> None:
    """
    Render the Hybrid Query tab.

    Accepts a natural-language query, runs it through the PyCodeKG hybrid
    semantic+structural search, and displays the results as a graph,
    node table, edge table, and raw JSON (with a download button).

    Error handling strategy: query execution failures are caught and surfaced
    as inline Streamlit errors so the app remains interactive.

    :param cfg: Configuration dictionary returned by ``_render_sidebar``,
        providing keys such as ``store``, ``repo_root``, ``db_path``,
        ``lancedb_dir``, ``model``, ``k``, ``hop``, ``rels``,
        ``include_symbols``, ``graph_height``, and ``physics_on``.
    """
    st.header("🔍 Hybrid Query")
    store: GraphStore | None = cfg["store"]
    if store is None:
        st.warning("No database loaded. Set the SQLite path in the sidebar.")
        return

    query_text = st.text_input(
        "Natural-language query",
        placeholder="e.g. database connection setup",
        key="query_input",
    )

    run_btn = st.button("▶ Run Query", type="primary", key="run_query_btn")

    if run_btn and query_text.strip():
        with st.spinner("Running hybrid query…"):
            try:
                kg = _load_kg(
                    cfg["repo_root"],
                    cfg["db_path"],
                    cfg["lancedb_dir"],
                    cfg["model"],
                )
                result = kg.query(
                    query_text.strip(),
                    k=cfg["k"],
                    hop=cfg["hop"],
                    rels=cfg["rels"],
                    include_symbols=cfg["include_symbols"],
                )
                st.session_state.query_result = result
            except (AttributeError, ValueError, RuntimeError, OSError) as exc:
                st.error(f"Query failed: {exc}")
                return

    result = st.session_state.query_result
    if result is None:
        st.info("Enter a query above and click **Run Query**.")
        return

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Seeds", result.seeds)
    c2.metric("Expanded", result.expanded_nodes)
    c3.metric("Returned", result.returned_nodes)
    c4.metric("Edges", len(result.edges))

    tab_graph, tab_table, tab_edges, tab_json = st.tabs(
        ["🗺️ Graph", "📋 Nodes", "🔗 Edges", "{ } JSON"]
    )

    with tab_graph:
        if result.nodes:
            _render_legend()
            html = _build_pyvis(
                result.nodes,
                result.edges,
                height=cfg["graph_height"],
                physics=cfg["physics_on"],
            )
            st.components.v1.html(
                html,
                height=int(cfg["graph_height"].replace("px", "")),
                scrolling=False,
            )
        else:
            st.info("No nodes to display.")

    with tab_table:
        import pandas as pd  # pylint: disable=import-outside-toplevel

        df = pd.DataFrame(
            [
                {
                    "kind": n["kind"],
                    "name": n["name"],
                    "qualname": n.get("qualname", ""),
                    "module": n.get("module_path", ""),
                    "line": n.get("lineno", ""),
                    "docstring": (
                        (n.get("docstring") or "").strip().splitlines()[0][:80]
                        if n.get("docstring")
                        else ""
                    ),
                }
                for n in result.nodes
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_edges:
        if result.edges:
            import pandas as pd  # pylint: disable=import-outside-toplevel

            edf = pd.DataFrame(
                [
                    {"src": e["src"], "rel": e["rel"], "dst": e["dst"]}
                    for e in sorted(result.edges, key=lambda x: (x["rel"], x["src"]))
                ]
            )
            st.dataframe(edf, use_container_width=True, hide_index=True)
        else:
            st.info("No edges in result set.")

    with tab_json:
        st.download_button(
            "⬇ Download JSON",
            data=result.to_json(),
            file_name="query_result.json",
            mime="application/json",
        )
        st.code(result.to_json(), language="json")

    # Node detail panel — below the sub-tabs
    _node_detail_section(result.nodes, store, key_prefix="query")


# ---------------------------------------------------------------------------
# Tab 3 — Snippet pack
# ---------------------------------------------------------------------------


def _tab_snippets(cfg: dict) -> None:
    """
    Render the Snippet Pack tab.

    Accepts a query, builds a source-grounded snippet pack via PyCodeKG,
    and displays metrics, download buttons, a pack graph, per-node
    expandable code snippets, and an edges table.

    Configuration defaults come from sidebar controls (model, graph/index paths,
    and traversal parameters). Runtime failures are reported inline to preserve
    the interactive debugging loop.

    :param cfg: Configuration dictionary returned by ``_render_sidebar``,
        providing keys such as ``store``, ``repo_root``, ``db_path``,
        ``lancedb_dir``, ``model``, ``k``, ``hop``, ``rels``,
        ``include_symbols``, and ``physics_on``.
    """
    st.header("📦 Snippet Pack")
    store: GraphStore | None = cfg["store"]
    if store is None:
        st.warning("No database loaded. Set the SQLite path in the sidebar.")
        return

    col_q, col_ctx, col_ml, col_mn = st.columns([3, 1, 1, 1])
    with col_q:
        pack_query = st.text_input(
            "Query for snippet pack",
            placeholder="e.g. configuration loading",
            key="pack_query_input",
        )
    with col_ctx:
        context_lines = st.number_input("Context lines", min_value=0, max_value=20, value=5)
    with col_ml:
        max_lines = st.number_input(
            "Max lines/snippet", min_value=20, max_value=400, value=160, step=20
        )
    with col_mn:
        max_nodes = st.number_input("Max nodes", min_value=5, max_value=100, value=50, step=5)

    pack_btn = st.button("📦 Build Pack", type="primary", key="pack_btn")

    if pack_btn and pack_query.strip():
        with st.spinner("Building snippet pack…"):
            try:
                kg = _load_kg(
                    cfg["repo_root"],
                    cfg["db_path"],
                    cfg["lancedb_dir"],
                    cfg["model"],
                )
                pack = kg.pack(
                    pack_query.strip(),
                    k=cfg["k"],
                    hop=cfg["hop"],
                    rels=cfg["rels"],
                    include_symbols=cfg["include_symbols"],
                    context=int(context_lines),
                    max_lines=int(max_lines),
                    max_nodes=int(max_nodes),
                )
                st.session_state.pack_result = pack
            except (AttributeError, ValueError, RuntimeError, OSError) as exc:
                st.error(f"Pack failed: {exc}")
                return

    pack = st.session_state.pack_result
    if pack is None:
        st.info("Enter a query above and click **Build Pack**.")
        return

    # Summary
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Seeds", pack.seeds)
    c2.metric("Expanded", pack.expanded_nodes)
    c3.metric("Returned", pack.returned_nodes)
    c4.metric("Model", pack.model)

    # Download buttons
    dl1, dl2 = st.columns(2)
    dl1.download_button(
        "⬇ Download Markdown",
        data=pack.to_markdown(),
        file_name="snippet_pack.md",
        mime="text/markdown",
    )
    dl2.download_button(
        "⬇ Download JSON",
        data=pack.to_json(),
        file_name="snippet_pack.json",
        mime="application/json",
    )

    st.markdown("---")

    # Graph of pack nodes
    with st.expander("🗺️ Pack graph", expanded=False):
        _render_legend()
        html = _build_pyvis(
            pack.nodes,
            pack.edges,
            height="500px",
            physics=cfg["physics_on"],
        )
        st.components.v1.html(html, height=500, scrolling=False)

    # Node cards with snippets
    st.subheader(f"Nodes ({len(pack.nodes)})")
    for n in pack.nodes:
        kind = n.get("kind", "?")
        color = _KIND_COLOR.get(kind, "#95A5A6")
        qualname = n.get("qualname") or n.get("name", "")
        module = n.get("module_path") or ""
        lineno = n.get("lineno")
        doc = (n.get("docstring") or "").strip()
        doc0 = doc.splitlines()[0][:120] if doc else ""
        snippet = n.get("snippet")

        header = f"**`{kind}`** — `{qualname}`"
        if module:
            header += f"  ·  `{module}`"
        if lineno:
            header += f"  line {lineno}"

        with st.expander(header, expanded=bool(snippet)):
            st.markdown(
                f'<div style="border-left:4px solid {color};padding-left:10px;">'
                f'<code style="color:{color}">{kind}</code> '
                f"<b>{qualname}</b><br>"
                f'<small style="color:#888">{module}'
                + (f" · line {lineno}" if lineno else "")
                + "</small>"
                + (f"<br><i>{doc0}</i>" if doc0 else "")
                + "</div>",
                unsafe_allow_html=True,
            )
            if snippet:
                st.code(snippet["text"], language="python")
                st.caption(f"`{snippet['path']}` lines {snippet['start']}–{snippet['end']}")
            elif doc:
                st.markdown(f"*{doc[:300]}*")

    # Edges table
    if pack.edges:
        with st.expander(f"🔗 Edges ({len(pack.edges)})"):
            import pandas as pd  # pylint: disable=import-outside-toplevel

            edf = pd.DataFrame(
                [
                    {"src": e["src"], "rel": e["rel"], "dst": e["dst"]}
                    for e in sorted(pack.edges, key=lambda x: (x["rel"], x["src"]))
                ]
            )
            st.dataframe(edf, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Application entry point for the PyCodeKG Streamlit visualizer.

    Initialises session state, renders the sidebar, and dispatches to the
    three tab renderers: Graph Browser, Hybrid Query, and Snippet Pack.
    """
    _init_state()
    cfg = _render_sidebar()

    st.title("🕸️ PyCodeKG Explorer")
    st.caption(
        "Interactive knowledge-graph browser for Python codebases. "
        "Built with [PyCodeKG](https://github.com/suchanek/pycode_kg) · "
        "Powered by Streamlit + pyvis."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🗺️ Graph Browser",
            "🔍 Hybrid Query",
            "📦 Snippet Pack",
        ]
    )

    with tab1:
        _tab_graph(cfg)

    with tab2:
        _tab_query(cfg)

    with tab3:
        _tab_snippets(cfg)


if __name__ == "__main__":
    main()
