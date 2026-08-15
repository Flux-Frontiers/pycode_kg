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

License: Elastic 2.0
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from kg_utils.analysis.scores import ScoreSet, available_metrics, load_scores

from pycode_kg import theme
from pycode_kg.graph_html import build_graph_html, select_nodes
from pycode_kg.store import DEFAULT_RELS, GraphStore

# ---------------------------------------------------------------------------
# Constants — colours and shapes per node kind
# ---------------------------------------------------------------------------

# Colours, shapes and sizes live in pycode_kg.theme so that the 2-D explorer,
# the 3-D viewer and the layout engine cannot drift apart again.
_KIND_COLOR = theme.KIND_COLOR
_KIND_SHAPE = theme.KIND_SHAPE
_REL_COLOR = theme.REL_COLOR

# Honour the PYCODEKG_DB env var so the Docker image (which mounts
# persistent data at /data) works out of the box without the user
# having to change the sidebar path manually.
import os as _os  # noqa: E402

_DEFAULT_DB = _os.environ.get("PYCODEKG_DB", ".pycodekg/graph.sqlite")
_DEFAULT_VECTORS = _os.environ.get("PYCODEKG_VECTORS", ".pycodekg/vectors.sqlite")

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
def _load_kg(repo_root: str, db_path: str, vectors_path: str, model: str):
    """
    Load and cache a ``PyCodeKG`` instance for the given configuration.

    Keyed on all four parameters so that changing any one triggers a fresh load.
    This is the main entry point for query/snippet execution in the UI and the
    configuration boundary between Streamlit controls and runtime PyCodeKG state.

    :param repo_root: Root directory of the Python repository to analyse.
    :param db_path: Path to the SQLite graph database.
    :param vectors_path: Path to the sqlite-vec vector store.
    :param model: Name of the sentence-transformer embedding model to use.
    :return: An initialised ``PyCodeKG`` instance.
    """
    from pycode_kg import PyCodeKG  # noqa: PLC0415

    return PyCodeKG(
        repo_root=repo_root,
        db_path=db_path,
        vectors_path=vectors_path,
        model=model,
    )


# ---------------------------------------------------------------------------
# pyvis graph builder
# ---------------------------------------------------------------------------


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
                import pandas as pd  # noqa: PLC0415

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


def _centrality_selector(db_path: str) -> ScoreSet | None:
    """Render the sidebar centrality control and return the chosen scores.

    Both metric tables are created lazily by the analysis pipeline, so a graph
    that has been built but never analysed carries no metrics at all.  In that
    case the control explains how to produce them rather than showing an empty
    dropdown.

    :param db_path: Path to the graph database.
    :return: The selected :class:`ScoreSet`, or ``None`` when sizing should stay
        uniform.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("⬤ Centrality")

    metrics = available_metrics(db_path)
    if not metrics:
        st.sidebar.caption(
            "No metrics found. Run `pycodekg analyze` to compute "
            "structural importance, then reload."
        )
        return None

    options = ["(uniform)"] + [f"{m.label} — {m.count} nodes" for m in metrics]
    choice = st.sidebar.selectbox(
        "Size & fade nodes by",
        options=options,
        index=1,
        help=(
            "Node diameter and opacity both encode the metric's rank "
            "percentile. Hover a node for its exact score and rank."
        ),
    )
    if choice == options[0]:
        return None

    ref = metrics[options.index(choice) - 1]
    scores = load_scores(db_path, ref.metric, table=ref.table)
    if scores is None:
        st.sidebar.warning(f"Could not load `{ref.metric}` from `{ref.table}`.")
    return scores


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

    Exposes controls for the SQLite path, repo root, sqlite-vec store path,
    embedding model, query parameters (k, hops, relations, include_symbols),
    graph display options (max nodes, physics, height), and build buttons
    for the graph and semantic index.

    :return: A dict with keys ``db_path``, ``repo_root``, ``vectors_path``,
        ``model``, ``k``, ``hop``, ``rels``, ``include_symbols``,
        ``max_graph_nodes``, ``physics_on``, ``graph_height``, ``scores``,
        ``selection``, and ``store``.
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
    vectors_path = st.sidebar.text_input(
        "Vector store path",
        value=_DEFAULT_VECTORS,
        help="Path to the sqlite-vec vector store",
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

    scores = _centrality_selector(db_path)

    selection = "central" if scores is not None else "path"
    if scores is not None:
        selection = (
            "central"
            if st.sidebar.radio(
                "When over the node limit, keep",
                options=["Most central + neighbours", "First by module path"],
                index=0,
                help=(
                    "The graph can only draw a few hundred nodes. Seeding on the "
                    "most central ones and expanding to their neighbours shows the "
                    "code everything depends on, still connected; keeping the first "
                    "by path shows a well-connected but alphabetical slice."
                ),
            )
            == "Most central + neighbours"
            else "path"
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
        help="Embed nodes → sqlite-vec (requires graph to exist)",
        use_container_width=True,
    )
    build_all_btn = st.sidebar.button(
        "⚡ Build All (graph + index)",
        help="Full pipeline: AST → SQLite → sqlite-vec",
        use_container_width=True,
        type="primary",
    )

    if build_graph_btn or build_all_btn:
        with st.sidebar:
            with st.spinner("Building graph (AST → SQLite)…"):
                try:
                    from pycode_kg import (  # noqa: PLC0415
                        PyCodeKG,
                    )

                    kg = PyCodeKG(
                        repo_root=repo_root,
                        db_path=db_path,
                        vectors_path=vectors_path,
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
            with st.spinner("Building semantic index (SQLite → sqlite-vec)…"):
                try:
                    from pycode_kg import (  # noqa: PLC0415
                        PyCodeKG,
                    )

                    kg = PyCodeKG(
                        repo_root=repo_root,
                        db_path=db_path,
                        vectors_path=vectors_path,
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
        "vectors_path": vectors_path,
        "model": model,
        "k": k,
        "hop": hop,
        "rels": tuple(chosen_rels) if chosen_rels else DEFAULT_RELS,
        "include_symbols": include_symbols,
        "max_graph_nodes": max_graph_nodes,
        "physics_on": physics_on,
        "graph_height": graph_height,
        "scores": scores,
        "selection": selection,
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
            options=list(theme.STORE_KINDS),
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
                total = len(nodes)
                nodes, how = select_nodes(
                    nodes,
                    max_n,
                    cfg["scores"],
                    cfg["selection"],
                    expand=lambda ids, hop: set(store.expand(ids, hop=hop)),
                )
                st.info(
                    f"Showing {max_n} of {total} nodes — {how}. Adjust the limit in the sidebar."
                )
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

    html = build_graph_html(
        nodes,
        edges,
        height=cfg["graph_height"],
        physics=cfg["physics_on"],
        scores=cfg["scores"],
    )
    st.iframe(html, height=int(cfg["graph_height"].replace("px", "")))

    with st.expander("📋 Node table"):
        import pandas as pd  # noqa: PLC0415

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
        ``vectors_path``, ``model``, ``k``, ``hop``, ``rels``,
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
                    cfg["vectors_path"],
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
            html = build_graph_html(
                result.nodes,
                result.edges,
                height=cfg["graph_height"],
                physics=cfg["physics_on"],
                scores=cfg["scores"],
            )
            st.iframe(html, height=int(cfg["graph_height"].replace("px", "")))
        else:
            st.info("No nodes to display.")

    with tab_table:
        import pandas as pd  # noqa: PLC0415

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
            import pandas as pd  # noqa: PLC0415

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
        ``vectors_path``, ``model``, ``k``, ``hop``, ``rels``,
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
                    cfg["vectors_path"],
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
        html = build_graph_html(
            pack.nodes,
            pack.edges,
            height="500px",
            physics=cfg["physics_on"],
            scores=cfg["scores"],
        )
        st.iframe(html, height=500)

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
            import pandas as pd  # noqa: PLC0415

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


def _inject_css() -> None:
    """Inject CSS that matches Streamlit's active theme (light or dark)."""
    is_dark = st.get_option("theme.base") == "dark"
    card_bg = "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.04)"
    card_color = "#e0e0e0" if is_dark else "#111"
    small_color = "#aaa" if is_dark else "#555"
    edge_color = "#aaa" if is_dark else "#444"
    st.markdown(
        f"""
        <style>
        .stTabs [data-baseweb="tab-list"] {{ gap: 12px; }}
        .stTabs [data-baseweb="tab"] {{ font-size: 1rem; padding: 6px 18px; }}
        .node-card {{
            background: {card_bg};
            color: {card_color};
            border-left: 4px solid #4A90D9;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 8px;
            font-family: monospace;
            font-size: 0.85rem;
        }}
        .node-card small {{ color: {small_color}; }}
        .edge-row {{ font-family: monospace; font-size: 0.82rem; color: {edge_color}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """
    Application entry point for the PyCodeKG Streamlit visualizer.

    Initialises session state, renders the sidebar, and dispatches to the
    three tab renderers: Graph Browser, Hybrid Query, and Snippet Pack.
    """
    _init_state()
    _inject_css()
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
