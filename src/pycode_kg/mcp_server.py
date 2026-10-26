#!/usr/bin/env python3
"""
mcp_server.py — PyCodeKG MCP Server

Serves a Python codebase's knowledge graph to any MCP-compatible agent
(Claude Code, Claude Desktop, Cursor, Copilot) over the fleet's shared server
base, :mod:`kg_utils.mcp`.

The server answers the fleet's canonical tools -- ``stats``, ``query``,
``pack``, ``get_node``, ``neighbors`` -- under the same names as every other
KG server, plus PyCodeKG's own code-graph tools (``callers``, ``explain``,
``centrality``, the CodeRank and snapshot tools, ...). ``query`` and ``pack``
are PyCodeKG's richer versions of the canonical pair: hybrid reranking by
default, a per-module cap, a ``paths`` filter and inferred-edge provenance.

The tool list is not kept by hand anywhere. Each tool's docstring is its
description, the server's instructions are generated from them, and::

    pycodekg mcp --manifest

prints the whole list as JSON without opening the graph.

Usage
-----
Install the package, then run::

    pycodekg mcp --repo /path/to/repo

``--db`` and ``--vectors`` are optional; they default to
``.pycodekg/graph.sqlite`` and ``.pycodekg/vectors.sqlite``, and a relative
path is taken from ``--repo``. ``pycodekg-mcp`` is the same command under the
name older Claude Desktop and Copilot configs use.

Per-project config for Claude Code and Kilo Code (``.mcp.json``)::

    {
      "mcpServers": {
        "pycodekg": {
          "command": "pycodekg",
          "args": ["mcp", "--repo", "/path/to/repo"]
        }
      }
    }

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kg_utils.mcp import Context, KGServer, kg_from, make_server

from pycode_kg import PyCodeKG, __version__
from pycode_kg.pycodekg import DEFAULT_MODEL
from pycode_kg.pycodekg_thorough_analysis import PyCodeKGAnalyzer
from pycode_kg.snapshots import SnapshotManager
from pycode_kg.store import DEFAULT_RELS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _snapshots(kg: PyCodeKG) -> SnapshotManager:
    """Return the snapshot manager for the session's graph.

    :param kg: The session's graph.
    :return: A :class:`SnapshotManager` over ``<repo>/.pycodekg/snapshots``.
    """
    return SnapshotManager(kg.repo_root / ".pycodekg" / "snapshots", db_path=kg.db_path)


def _enrich_edges_with_provenance(edges: list[dict]) -> list[dict]:
    """Attach confidence/provenance fields to inferred edges when possible.

    :param edges: Edge dictionaries from graph queries.
    :return: New edge list with optional ``inferred``, ``confidence``, and
        ``provenance`` fields.
    """
    enriched: list[dict] = []
    for edge in edges:
        out = dict(edge)
        ev_raw = edge.get("evidence")
        ev = None
        if isinstance(ev_raw, str):
            try:
                ev = json.loads(ev_raw)
            except json.JSONDecodeError:
                ev = None
        elif isinstance(ev_raw, dict):
            ev = ev_raw

        inferred = bool(
            edge.get("rel") == "RESOLVES_TO"
            or str(edge.get("src", "")).startswith("sym:")
            or str(edge.get("dst", "")).startswith("sym:")
            or (isinstance(ev, dict) and "resolution_mode" in ev)
        )
        if inferred:
            out["inferred"] = True
            if isinstance(ev, dict):
                out["confidence"] = ev.get("confidence", "unknown")
                out["provenance"] = {
                    "resolution_mode": ev.get("resolution_mode"),
                    "symbol": ev.get("symbol"),
                    "candidate_count": ev.get("candidate_count"),
                }
                out["evidence"] = ev
            else:
                out["confidence"] = "unknown"
                out["provenance"] = {"resolution_mode": None}
        enriched.append(out)
    return enriched


def _snapshot_freshness(kg: PyCodeKG, snapshot_total_nodes: int) -> dict:
    """Compare a snapshot's node count against the currently loaded graph DB.

    :param kg: The session's graph.
    :param snapshot_total_nodes: ``metrics.total_nodes`` from a snapshot object.
    :return: Freshness metadata payload.
    """
    current_nodes = int(kg.stats()["nodes"]["total"])
    delta = current_nodes - int(snapshot_total_nodes)

    is_fresh = delta == 0
    status = "fresh" if delta == 0 else ("behind" if delta > 0 else "ahead")
    note = None

    if 0 < delta < 50:
        is_fresh = True
        status = "near_fresh"
        note = "Within tolerance (sym: stubs often accumulate between rebuilds)"

    out = {
        "snapshot_total_nodes": int(snapshot_total_nodes),
        "current_total_nodes": current_nodes,
        "delta_nodes": delta,
        "is_fresh": is_fresh,
        "status": status,
    }
    if note:
        out["note"] = note
    return out


# ---------------------------------------------------------------------------
# Instructions: the hand-written part. The tool list is appended by kg_utils.mcp.
# ---------------------------------------------------------------------------

PREAMBLE = (
    "PyCodeKG is a hybrid semantic + structural knowledge graph for a Python codebase. "
    "It indexes every module, class, function and method as a node, with typed edges "
    "(CALLS, IMPORTS, CONTAINS, INHERITS) between them. Node IDs look like "
    "'<kind>:<module_path>:<qualname>', e.g. 'cls:src/pycode_kg/store.py:GraphStore'.\n\n"
    "## Recommended workflows\n\n"
    "- **Explore unfamiliar code**: stats → query → list_nodes (to enumerate a module) "
    "→ explain → pack\n"
    "- **Understand a specific function**: get_node → neighbors → pack\n"
    "- **Look up by name (no ID known)**: find_node(name) → explain or callers\n"
    "- **Impact analysis before a change**: explain → callers (with paths='src/')\n"
    "- **Architecture review**: analyze_repo\n"
    "- **Answer 'how does X work?'**: pack with a descriptive query\n"
    "- **Track codebase evolution**: snapshot_list → snapshot_diff(key_a=..., key_b=...)\n"
    "- **Identify the most important code**: centrality(top=20) → explain → pack\n"
    "- **Structure-aware search**: query_ranked(q='...', mode='hybrid'), or mode='ppr' "
    "→ explain_rank(node_id, q='...')\n"
    "- **Global importance**: rank_nodes(top=25) → explain_rank; "
    "rank_nodes(persist_metric='coderank_global') to keep the scores\n\n"
    "For a precision query on a concept you know well, query(min_score=0.5) filters out "
    "incidental docstring mentions."
)


# ---------------------------------------------------------------------------
# Canonical tools: PyCodeKG's richer query and pack, under the fleet's names
# ---------------------------------------------------------------------------


def query(
    q: str,
    k: int = 8,
    hop: int = 1,
    rels: list[str] | None = None,
    include_symbols: bool = False,
    max_nodes: int = 25,
    min_score: float = 0.0,
    max_per_module: int = 3,
    paths: str = "",
    rerank_mode: str = "hybrid",
    rerank_semantic_weight: float = 0.7,
    rerank_lexical_weight: float = 0.3,
    include_edge_provenance: bool = False,
    *,
    ctx: Context,
) -> dict[str, Any]:
    """
    Hybrid semantic + structural search: ranked code nodes and the edges among them.

    Seeds on vector similarity, then expands through the graph. Use ``pack``
    instead when you want the source itself.

    **hop:** ``0`` is pure semantic search, highest precision, best for
    concept lookup ("find the retry logic"); ``1`` (default) adds call chains
    and module relationships; ``2`` traces dependencies broadly and may return
    many loosely related nodes.

    **rerank_mode:** ``hybrid`` (default) blends vector similarity (70%) with
    lexical overlap on name, qualname, module and docstring (30%), the best
    overall; ``semantic`` ranks by vector score only; ``legacy`` orders by hop
    distance first, for stable comparisons with older results.

    :param q: Natural-language query, e.g. "database connection setup".
    :param k: Semantic seed nodes (1-100, default 8).
    :param hop: Graph expansion hops from each seed (0-5, default 1).
    :param rels: Edge types to follow; omit for CONTAINS, CALLS, IMPORTS, INHERITS.
    :param include_symbols: Include ``sym:`` import-stub nodes (default False).
    :param max_nodes: Most nodes to return (default 25).
    :param min_score: Minimum semantic score for a seed, 0.0-1.0; 0.5 filters
        out incidental docstring mentions.
    :param max_per_module: Most nodes from one module (default 3; 0 disables),
        so one popular module cannot dominate a hop-1 expansion.
    :param paths: Comma-separated module path prefixes to keep, e.g.
        ``"src/pycode_kg"`` to leave out tests and scripts.
    :param rerank_mode: ``hybrid`` (default), ``semantic`` or ``legacy``.
    :param rerank_semantic_weight: Semantic weight for ``hybrid`` (default 0.7).
    :param rerank_lexical_weight: Lexical weight for ``hybrid`` (default 0.3).
    :param include_edge_provenance: Annotate inferred edges with confidence
        and resolution metadata.
    """
    result = kg_from(ctx).query(
        q,
        k=k,
        hop=hop,
        rels=tuple(rels) if rels else DEFAULT_RELS,
        include_symbols=include_symbols,
        max_nodes=max_nodes,
        min_score=min_score,
        max_per_module=max_per_module if max_per_module > 0 else None,
        rerank_mode=rerank_mode,
        rerank_semantic_weight=rerank_semantic_weight,
        rerank_lexical_weight=rerank_lexical_weight,
    )
    data: dict[str, Any] = json.loads(result.to_json())
    if include_edge_provenance:
        data["edges"] = _enrich_edges_with_provenance(data.get("edges", []))
    if paths:
        prefixes = [p.strip() for p in paths.split(",") if p.strip()]
        kept = {
            n["id"]
            for n in data["nodes"]
            if any((n.get("module_path") or "").startswith(pfx) for pfx in prefixes)
        }
        data["nodes"] = [n for n in data["nodes"] if n["id"] in kept]
        data["edges"] = [e for e in data["edges"] if e["src"] in kept and e["dst"] in kept]
        data["returned_nodes"] = len(data["nodes"])
    return data


def pack(
    q: str,
    k: int = 8,
    hop: int = 1,
    rels: list[str] | None = None,
    include_symbols: bool = False,
    context: int = 5,
    max_lines: int = 60,
    max_nodes: int = 15,
    min_score: float = 0.0,
    max_per_module: int = 3,
    rerank_mode: str = "hybrid",
    rerank_semantic_weight: float = 0.7,
    rerank_lexical_weight: float = 0.3,
    missing_lineno_policy: str = "cap_or_skip",
    include_edge_provenance: bool = False,
    *,
    ctx: Context,
) -> str:
    """
    Hybrid search rendered as a Markdown context pack of source code with line numbers.

    The answer to "how does X work?": ranked, deduplicated snippets ready to
    read, with a Warnings section when a snippet is capped or omitted for
    missing line metadata. Same search and ``rerank_mode`` as ``query``.

    :param q: Natural-language query, e.g. "configuration loading".
    :param k: Semantic seed nodes (1-100, default 8).
    :param hop: Graph expansion hops (0-5, default 1).
    :param rels: Edge types to follow; omit for CONTAINS, CALLS, IMPORTS, INHERITS.
    :param include_symbols: Include ``sym:`` import-stub nodes (default False).
    :param context: Extra lines around each definition (default 5).
    :param max_lines: Longest snippet, in lines (default 60).
    :param max_nodes: Most snippets (default 15).
    :param min_score: Minimum semantic score for a seed, 0.0-1.0.
    :param max_per_module: Most nodes from one module (default 3; 0 disables).
    :param rerank_mode: ``hybrid`` (default), ``semantic`` or ``legacy``.
    :param rerank_semantic_weight: Semantic weight for ``hybrid`` (default 0.7).
    :param rerank_lexical_weight: Lexical weight for ``hybrid`` (default 0.3).
    :param missing_lineno_policy: ``cap_or_skip`` (default) falls back to a
        capped parent span or omits the snippet; ``legacy`` keeps the old
        uncapped behaviour.
    :param include_edge_provenance: Annotate inferred edges with confidence
        and resolution metadata.
    """
    result = kg_from(ctx).pack(
        q,
        k=k,
        hop=hop,
        rels=tuple(rels) if rels else DEFAULT_RELS,
        include_symbols=include_symbols,
        context=context,
        max_lines=max_lines,
        max_nodes=max_nodes,
        min_score=min_score,
        max_per_module=max_per_module if max_per_module > 0 else None,
        rerank_mode=rerank_mode,
        rerank_semantic_weight=rerank_semantic_weight,
        rerank_lexical_weight=rerank_lexical_weight,
        missing_lineno_policy=missing_lineno_policy,
    )
    if include_edge_provenance:
        result.edges = _enrich_edges_with_provenance(result.edges)
    return result.to_markdown()


# ---------------------------------------------------------------------------
# PyCodeKG's own tools
# ---------------------------------------------------------------------------


def callers(node_id: str, rel: str = "CALLS", paths: str = "", *, ctx: Context) -> str:
    """
    Return all nodes that call a given node, resolving through ``sym:`` stubs.

    Unlike ``query`` (which seeds on semantics and expands outward),
    this tool performs a precise reverse lookup: it finds every caller of the
    specified node, including cross-module callers that reference it via an
    import alias recorded as a ``sym:`` stub.

    The ``rel`` parameter accepts any edge relation, not just ``CALLS``::

        callers(node_id, rel="INHERITS")  # find all subclasses
        callers(node_id, rel="IMPORTS")   # find all importers

    Typical workflow::

        # 1. Resolve the exact node ID
        get_node("fn:src/my_pkg/utils.py:helper")

        # 2. Find all callers (production code only)
        callers("fn:src/my_pkg/utils.py:helper", paths="src/")

    :param node_id: Target node identifier, e.g.
                    ``fn:src/pycode_kg/store.py:GraphStore.expand``.
    :param rel: Relation type to invert (default ``"CALLS"``).
    :param paths: Comma-separated module path prefixes to include, e.g.
                  ``"src/"`` to exclude test callers.
                  Empty string (default) returns all callers.
    :return: JSON with ``node_id``, ``rel``, ``caller_count``, and
             ``callers`` list of node dicts.
    """
    caller_list = kg_from(ctx).callers(node_id, rel=rel)
    if paths:
        path_prefixes = [p.strip() for p in paths.split(",") if p.strip()]
        caller_list = [
            c
            for c in caller_list
            if any((c.get("module_path") or "").startswith(pfx) for pfx in path_prefixes)
        ]
    return json.dumps(
        {
            "node_id": node_id,
            "rel": rel,
            "caller_count": len(caller_list),
            "callers": caller_list,
        },
        indent=2,
        ensure_ascii=False,
    )


def list_nodes(
    module_path: str = "",
    kind: str = "",
    include_symbols: bool = False,
    *,
    ctx: Context,
) -> str:
    """
    List nodes filtered by module path prefix and/or kind.

    :param module_path: Module path prefix filter (e.g. "src/pycode_kg/store.py").
    :param kind: Node kind filter: module | class | function | method.
    :param include_symbols: If True, include ``sym:`` import-stub nodes.  Default
                            False so only meaningful code entities are returned.
    :return: JSON array of matching node dicts.
    """
    kg = kg_from(ctx)
    store = kg.store

    query = "SELECT id, name, qualname, kind, module_path, lineno, docstring FROM nodes WHERE 1=1"
    params = []

    if module_path:
        query += " AND module_path LIKE ?"
        params.append(f"{module_path}%")

    if kind:
        query += " AND kind = ?"
        params.append(kind)

    if not include_symbols:
        query += " AND id NOT LIKE 'sym:%'"

    query += " ORDER BY module_path, lineno"

    try:
        rows = store.con.execute(query, params).fetchall()
        result = []
        for r in rows:
            doc = r[6]
            if doc and len(doc) > 100:
                doc = doc[:100] + "..."
            result.append(
                {
                    "id": r[0],
                    "name": r[1],
                    "qualname": r[2],
                    "kind": r[3],
                    "module_path": r[4],
                    "lineno": r[5],
                    "docstring": doc,
                }
            )
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        return json.dumps({"error": str(e)}, indent=2)


def find_node(name: str, kind: str = "", *, ctx: Context) -> str:
    """
    Find graph nodes by name without knowing their full stable ID.

    Performs a case-insensitive search against both the ``name`` and
    ``qualname`` columns.  Use this when you know (or partially know) a
    function, class, or method name but do not yet have its stable ID
    (``<kind>:<module_path>:<qualname>``).  Once you have the ID, pass
    it to ``get_node()``, ``explain()``, or ``callers()``.

    Example workflow::

        # 1. Look up a name you saw in a traceback
        find_node("build_server")

        # 2. Use the returned id with explain or get_node
        explain("fn:src/pycode_kg/mcp_server.py:build_server")

    :param name: Function, method, or class name to search for.
                 Matched case-insensitively against ``name`` and ``qualname``.
    :param kind: Optional kind filter: ``module`` | ``class`` | ``function``
                 | ``method``.  Empty string (default) searches all kinds.
    :return: JSON array of matching node dicts with ``id``, ``name``,
             ``qualname``, ``kind``, ``module_path``, ``lineno``, and a
             truncated ``docstring``.  Returns an empty array when no match
             is found.
    """
    kg = kg_from(ctx)
    store = kg.store

    name_lower = name.lower()
    query = (
        "SELECT id, name, qualname, kind, module_path, lineno, docstring "
        "FROM nodes WHERE (LOWER(name) = ? OR LOWER(qualname) LIKE ?)"
    )
    params: list = [name_lower, f"%{name_lower}%"]

    if kind:
        query += " AND kind = ?"
        params.append(kind)

    query += " AND id NOT LIKE 'sym:%' ORDER BY module_path, lineno"

    try:
        rows = store.con.execute(query, params).fetchall()
        result = []
        for r in rows:
            doc = r[6]
            if doc and len(doc) > 120:
                doc = doc[:120] + "..."
            result.append(
                {
                    "id": r[0],
                    "name": r[1],
                    "qualname": r[2],
                    "kind": r[3],
                    "module_path": r[4],
                    "lineno": r[5],
                    "docstring": doc,
                }
            )
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        return json.dumps({"error": str(e)}, indent=2)


def centrality(
    top: int = 20,
    kinds: str = "",
    group_by: str = "node",
    *,
    ctx: Context,
) -> str:
    """
    Compute Structural Importance Ranking (SIR) for the indexed codebase.

    Runs a deterministic weighted PageRank over the sym-stub-resolved call
    graph.  Edge weights are tuned per relation type
    (CALLS > INHERITS > IMPORTS > CONTAINS) and amplified for cross-module
    links; private symbols receive a post-convergence penalty.  Scores are
    normalized to sum to 1.0.

    Use this to:

    - Identify the most structurally critical functions and classes
    - Understand which modules are most depended upon
    - Prioritize code review, refactoring, or test coverage efforts

    :param top: Maximum number of ranked entries to return (default 20).
    :param kinds: Comma-separated node kinds to include: ``module``, ``class``,
                  ``function``, ``method``.  Empty string returns all kinds.
                  Ignored when ``group_by='module'`` (all kinds contribute to
                  module aggregation).
    :param group_by: ``node`` (default) returns individual node rankings with
                     score, inbound edge count, and cross-module inbound count;
                     ``module`` aggregates node scores per module (class nodes
                     weighted ×1.2).
    :return: Markdown-formatted ranking table.
    """
    try:
        from pycode_kg.analysis.centrality import (  # noqa: PLC0415
            StructuralImportanceRanker,
            aggregate_module_scores,
        )

        db_path = kg_from(ctx).db_path
        ranker = StructuralImportanceRanker(db_path)
        all_records = ranker.compute()
    except Exception as e:  # noqa: BLE001
        return f"## Centrality Error\n\nFailed to compute SIR scores: `{e}`"

    out: list[str] = ["## Structural Importance Ranking (SIR)\n"]

    if group_by == "module":
        payload = aggregate_module_scores(all_records)[:top]
        out.append(f"**Group by:** module  |  **Top:** {top}\n")
        out.append("| Rank | Score | Members | Module |")
        out.append("|-----:|------:|--------:|--------|")
        for row in payload:
            out.append(
                f"| {row['rank']} | {row['score']:.6f}"
                f" | {row['member_count']} | `{row['module_path']}` |"
            )
    else:
        kind_set: set[str] | None = None
        if kinds.strip():
            kind_set = {k.strip().lower() for k in kinds.split(",") if k.strip()}

        filtered = [r for r in all_records if kind_set is None or r.kind in kind_set][:top]
        label = kinds if kind_set else "all kinds"
        out.append(f"**Group by:** node  |  **Top:** {top}  |  **Filter:** {label}\n")
        out.append("| Rank | Score | Kind | Name | Module | Inbound | XMod |")
        out.append("|-----:|------:|------|------|--------|--------:|-----:|")
        for r in filtered:
            module = f"`{r.module_path}`" if r.module_path else "—"
            out.append(
                f"| {r.rank} | {r.score:.6f} | {r.kind} | `{r.name}`"
                f" | {module} | {r.inbound_count} | {r.cross_module_inbound} |"
            )

    out.append("")
    out.append(
        "> SIR scores are normalized to sum 1.0 across all nodes.  "
        "Higher score = more structurally central.  "
        "XMod = cross-module inbound edges."
    )
    return "\n".join(out)


def bridge_centrality(
    top: int = 20,
    include_imports: bool = True,
    *,
    ctx: Context,
) -> str:
    """
    Compute module connectivity: how many unique modules each module interacts with.

    For well-modularized codebases, identifies orchestrator and hub modules that
    touch many other modules. Replaces betweenness centrality (which is meaningless
    when inter-module edges are zero).

    **Connectivity score** = (unique modules called + unique modules calling this) / 30 + frequency / 50
    Higher score = more complex coupling with other modules.

    Scores are persisted to the ``centrality_scores`` table under the
    ``module_connectivity`` metric for use by ``framework_nodes()``.

    :param top: Number of top connectivity modules to return (default 20).
    :param include_imports: Whether to include IMPORTS in connectivity (default True).
    :return: Markdown-formatted ranking table of modules by connectivity.
    """
    try:
        from pycode_kg.analysis.bridge import (  # noqa: PLC0415
            compute_bridge_centrality,
        )

        db_path = str(kg_from(ctx).db_path)
        modules = compute_bridge_centrality(
            kind="module",
            include_imports=include_imports,
            top=top,
            db_path=db_path,
        )
    except Exception as e:  # noqa: BLE001
        return f"## Module Connectivity Error\n\nFailed to compute connectivity: `{e}`"

    out: list[str] = ["## Module Connectivity (Interaction Complexity)\n"]
    out.append(f"**Top:** {top}  |  **Include imports:** {include_imports}\n")
    out.append("| Rank | Connectivity | Module |")
    out.append("|-----:|-------------:|--------|")
    for rank_idx, (mod, score) in enumerate(modules, start=1):
        out.append(f"| {rank_idx} | {score:.6f} | `{mod}` |")
    out.append("")
    out.append(
        "> Connectivity = unique modules called + unique modules calling this module.  "
        "Higher score = orchestrator/hub module with complex interactions.  "
        "Scores are persisted as `module_connectivity` metric for use by `framework_nodes()`."
    )
    return "\n".join(out)


def framework_nodes(top: int = 20, *, ctx: Context) -> str:
    """
    Identify framework-like (hub) modules using SIR + module connectivity.

    A "framework node" is a module that is both:
    - Structurally important (high SIR/PageRank — central to the graph)
    - Highly connected (calls/imports many modules — orchestrator/hub role)

    Framework score = 0.6 × normalized SIR + 0.4 × normalized connectivity,
    both auto-computed on first call. High-scoring modules are critical hubs:
    architecturally central AND complex in their interactions.

    :param top: Number of top framework-like modules to return (default 20).
    :return: Markdown-formatted ranking table of framework nodes.
    """
    try:
        from pycode_kg.analysis.bridge import (  # noqa: PLC0415
            compute_bridge_centrality,
        )
        from pycode_kg.analysis.centrality import (  # noqa: PLC0415
            StructuralImportanceRanker,
        )
        from pycode_kg.analysis.framework_detector import (  # noqa: PLC0415
            detect_framework_nodes,
        )

        kg = kg_from(ctx)
        db_path = str(kg.db_path)

        # Compute and persist SIR scores (structural importance)
        try:
            ranker = StructuralImportanceRanker(db_path)
            records = ranker.compute()
            ranker.write_scores(records, metric="sir_pagerank")
        except Exception as e:  # noqa: BLE001
            return f"## Framework Nodes Error\n\nFailed to compute SIR scores: `{e}`"

        # Compute and persist module connectivity scores (interaction complexity)
        try:
            compute_bridge_centrality(kind="module", include_imports=True, top=25, db_path=db_path)
        except Exception as e:  # noqa: BLE001
            return f"## Framework Nodes Error\n\nFailed to compute module connectivity: `{e}`"

        # Detect framework nodes by combining both metrics
        nodes = detect_framework_nodes(limit=top, db_path=db_path)
    except Exception as e:  # noqa: BLE001
        return f"## Framework Nodes Error\n\nFailed to detect framework nodes: `{e}`"

    out: list[str] = ["## Framework-like Modules (Critical Hubs)\n"]
    out.append(f"**Top:** {top}  |  **Score:** 0.6 × SIR + 0.4 × connectivity (both normalized)\n")
    out.append("| Rank | Score | Module |")
    out.append("|-----:|------:|--------|")
    for rank_idx, (_, score, label) in enumerate(nodes, start=1):
        out.append(f"| {rank_idx} | {score:.6f} | `{label}` |")
    out.append("")
    out.append(
        "> Framework nodes: both architecturally central (SIR) AND heavily connected "
        "(calls/imports many modules).  High-scoring modules are critical orchestrators/hubs."
    )
    return "\n".join(out)


def find_definition_at(file: str, line: int, *, ctx: Context) -> str:
    """
    Find the code node whose definition spans a given file location.

    Reverse-resolves a ``(file, line)`` pair to a graph node ID and returns the
    same Markdown report as ``explain()``.  Useful when reading a file in an IDE
    and wanting to understand the symbol at a specific line without constructing
    a node ID manually.

    Matches the innermost (most-specific) function, method, or class whose
    ``lineno ≤ line ≤ end_lineno``.  Falls back to the module node when no
    narrower match exists.

    :param file: Module path as stored in the graph, e.g. ``src/pycode_kg/store.py``.
                 Leading ``./`` is stripped automatically.
    :param line: Line number (1-indexed) within the file.
    :return: Markdown explanation from ``explain()``, or an informative error
             message if no node spans that location.
    """
    kg = kg_from(ctx)
    store = kg.store

    norm_file = file.lstrip("./")

    # Innermost span: smallest (end_lineno - lineno) that still contains `line`.
    rows = store.con.execute(
        """
        SELECT id
        FROM nodes
        WHERE (module_path = :f OR module_path LIKE :like)
          AND kind IN ('function', 'method', 'class')
          AND lineno IS NOT NULL
          AND lineno <= :ln
          AND (end_lineno IS NULL OR end_lineno >= :ln)
        ORDER BY (COALESCE(end_lineno, lineno) - lineno) ASC
        LIMIT 1
        """,
        {"f": norm_file, "like": f"%{norm_file}", "ln": line},
    ).fetchall()

    if not rows:
        # Fall back to the module node itself
        mod_rows = store.con.execute(
            "SELECT id FROM nodes WHERE kind = 'module' AND (module_path = ? OR module_path LIKE ?)",
            (norm_file, f"%{norm_file}"),
        ).fetchall()
        if not mod_rows:
            return (
                f"## No Definition Found\n\n"
                f"No function, method, or class spans `{file}:{line}` in the graph.\n\n"
                "Check that the file path matches the module path stored in the graph "
                "(use `stats()` or `list_nodes()` to browse available modules)."
            )
        node_id = mod_rows[0][0]
    else:
        node_id = rows[0][0]

    return explain(node_id, ctx=ctx)


def analyze_repo(*, ctx: Context) -> str:
    """
    Run a full architectural analysis of the indexed repository.

    Executes the nine-phase PyCodeKG analysis pipeline — complexity hotspots,
    call chains, dependency coupling, orphaned code, public API surface,
    circular dependencies, module cohesion, integration points, and docstring
    coverage — and returns the results as a structured Markdown document.

    This is the same analysis produced by ``pycodekg analyze``; calling it from
    MCP gives agents on-demand access to structural health metrics without
    leaving the conversation.  The analysis is read-only and does not modify
    the knowledge graph.

    The output is optimized for LLM ingestion, with clear sections for metrics,
    hotspots, issues, strengths, and recommendations — similar to the
    ``pack()`` tool's Markdown output format.

    :return: Markdown-formatted string containing timestamp, baseline metrics,
             complexity hotspots, high fan-out functions, module architecture,
             key call chains, public APIs, docstring coverage, code quality
             issues, architectural strengths, and orphaned code.
    """
    from io import StringIO  # noqa: PLC0415

    from rich.console import Console  # noqa: PLC0415

    silent = Console(file=StringIO(), highlight=False)
    analyzer = PyCodeKGAnalyzer(kg_from(ctx), console=silent, snapshot_mgr=_snapshots(kg_from(ctx)))
    analyzer.run_analysis()
    return analyzer.to_markdown()


def explain(node_id: str, limit: int = 10, *, ctx: Context) -> str:
    """
    Return a natural-language explanation of a code node.

    Given a node ID (e.g., ``fn:src/pycode_kg/store.py:GraphStore.expand``),
    returns a markdown-formatted explanation that includes:

    - **What it is**: The node's kind, short description from its docstring
    - **Where it lives**: Module path and source location
    - **What calls it**: The callers (reverse call graph)
    - **What it calls**: The callees (functions/methods this node invokes)
    - **Documentation**: Full docstring if available

    This is ideal for understanding the role and context of a specific node
    without needing to read the full source code. Use ``pack()``
    to then retrieve the actual implementation.

    :param node_id: Stable node identifier, e.g.
                    ``fn:src/pycode_kg/store.py:GraphStore.expand``.
    :param limit: Maximum callers and callees to list (default 10). Pass 0
                  to list all.
    :return: Markdown-formatted explanation ready for LLM consumption.
    """
    from pycode_kg.explain import render_explain  # noqa: PLC0415

    return render_explain(
        kg_from(ctx),
        node_id,
        limit=limit,
        snippets_hint="pack()",
    )


def rank_nodes(
    top: int = 25,
    rels: str = "CALLS,IMPORTS,INHERITS",
    persist_metric: str = "",
    exclude_tests: bool = True,
    *,
    ctx: Context,
) -> str:
    """
    Compute global weighted CodeRank (PageRank) over the repository graph.

    Builds a directed weighted graph from the SQLite store and runs weighted
    PageRank to identify the most structurally important nodes.  Relation
    weights follow the CodeRank defaults: CALLS=1.0, IMPORTS=0.9,
    INHERITS=0.75.  Test paths are excluded by default.

    Optionally persists the scores into the ``node_metrics`` table under the
    given metric name so they can be loaded at query time without recomputing.

    :param top: Number of top-ranked nodes to return (default 25).
    :param rels: Comma-separated relations to include in the graph
                 (default ``"CALLS,IMPORTS,INHERITS"``).
    :param persist_metric: If non-empty, persist scores to ``node_metrics``
                           under this metric name (e.g. ``"coderank_global"``).
    :param exclude_tests: Exclude test-path nodes from the graph (default True).
    :return: JSON array of ranked node dicts with ``node_id``, ``score``,
             ``top_pct`` (e.g. ``"top 0.5%"``), ``kind``, ``qualname``,
             ``module_path``, and ``rank`` fields.
    """
    from pycode_kg.ranking.coderank import (  # noqa: PLC0415
        build_code_graph,
        compute_coderank,
        persist_metric_scores,
    )

    db_path = str(kg_from(ctx).db_path)
    rel_list = [r.strip() for r in rels.split(",") if r.strip()]

    try:
        graph = build_code_graph(
            db_path,
            include_relations=rel_list,
            exclude_test_paths=exclude_tests,
        )
        scores = compute_coderank(graph)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)}, indent=2)

    if persist_metric:
        try:
            persist_metric_scores(db_path, persist_metric, scores)
        except Exception:  # noqa: BLE001
            pass  # non-fatal — still return results

    # Filter out sym: stubs (import placeholders) — only return real code entities
    all_real_nodes = [
        (nid, s)
        for nid, s in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        if not nid.startswith("sym:")
    ]
    total_real = len(all_real_nodes)
    results = []
    for rank_idx, (node_id, score) in enumerate(all_real_nodes[:top], start=1):
        attrs = graph.nodes.get(node_id, {})
        top_pct = round(rank_idx / total_real * 100, 1) if total_real > 0 else 0.0
        results.append(
            {
                "rank": rank_idx,
                "node_id": node_id,
                "score": round(score, 8),
                "top_pct": f"top {top_pct:.1f}%",
                "kind": attrs.get("kind"),
                "qualname": attrs.get("qualname"),
                "module_path": attrs.get("module_path"),
            }
        )

    return json.dumps(results, indent=2, ensure_ascii=False)


def query_ranked(
    q: str,
    k: int = 8,
    mode: str = "hybrid",
    top: int = 25,
    rels: str = "CALLS,IMPORTS,INHERITS",
    radius: int = 2,
    exclude_tests: bool = True,
    *,
    ctx: Context,
) -> str:
    """
    Rank query results using CodeRank-enhanced hybrid or personalized PageRank.

    Combines semantic seed scores from the vector index with structural
    centrality and graph proximity to produce a final ranked list with
    explainability components.

    Two modes are available:

    - ``hybrid`` (default): 0.60 × semantic + 0.25 × centrality + 0.15 × proximity
    - ``ppr``: 0.70 × personalized PageRank + 0.30 × semantic

    :param q: Natural-language query string.
    :param k: Number of semantic seed nodes to retrieve (default 8).
    :param mode: Ranking mode — ``"hybrid"`` (default) or ``"ppr"``.
    :param top: Maximum ranked results to return (default 25).
    :param rels: Comma-separated relations to include in the local graph.
    :param radius: Graph expansion radius around seeds (default 2).
    :param exclude_tests: Exclude test-path nodes (default True).
    :return: JSON array of ranked result dicts with score components and
             ``why`` explanation strings.  ``sym:`` import stub nodes are
             always excluded from the output.
    """
    from pycode_kg.ranking.coderank import (  # noqa: PLC0415
        build_code_graph,
        compute_coderank,
        rank_query_hybrid,
        rank_query_ppr,
    )

    kg = kg_from(ctx)
    db_path = str(kg.db_path)
    rel_list = [r.strip() for r in rels.split(",") if r.strip()]

    # Get semantic seeds from the vector index
    try:
        raw = kg.query(q, k=k, hop=0, rels=tuple(rel_list))
        seed_data = json.loads(raw.to_json())
        seed_nodes = seed_data.get("nodes", [])
        semantic_scores: dict[str, float] = {
            n["id"]: float((n.get("relevance") or {}).get("score", 0.0))
            for n in seed_nodes
            if (n.get("relevance") or {}).get("score", 0.0) > 0
        }
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Seed retrieval failed: {exc}"}, indent=2)

    if not semantic_scores:
        return json.dumps({"error": "No semantic seeds found for query."}, indent=2)

    try:
        graph = build_code_graph(
            db_path,
            include_relations=rel_list,
            exclude_test_paths=exclude_tests,
        )
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Graph build failed: {exc}"}, indent=2)

    global_cr = compute_coderank(graph)
    try:
        if mode == "ppr":
            results = rank_query_ppr(graph, semantic_scores, radius=radius, top_k=top)
        else:
            results = rank_query_hybrid(
                graph, semantic_scores, global_coderank=global_cr, radius=radius, top_k=top
            )
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Ranking failed: {exc}"}, indent=2)

    output = []
    for rank_idx, r in enumerate(results, start=1):
        if r.node_id.startswith("sym:"):
            continue
        output.append(
            {
                "rank": rank_idx,
                "node_id": r.node_id,
                "adjusted_score": round(r.adjusted_score, 6),
                "final_score": round(r.final_score, 6),
                "semantic_score": round(r.semantic_score, 6),
                "centrality_score": round(r.centrality_score, 6),
                "proximity_score": round(r.proximity_score, 6),
                "kind": r.kind,
                "qualname": r.qualname,
                "module_path": r.module_path,
                "why": list(r.why),
            }
        )

    return json.dumps(
        {"query": q, "mode": mode, "returned": len(output), "results": output},
        indent=2,
        ensure_ascii=False,
    )


def explain_rank(node_id: str, q: str = "", *, ctx: Context) -> str:
    """
    Explain the CodeRank score components for a specific node.

    Returns a Markdown report showing the node's structural position in the
    graph: how many nodes call it, import it, or inherit from it; its global
    CodeRank score; and, when a query is provided, its semantic relevance and
    proximity to the query seed set.

    :param node_id: Stable node identifier, e.g.
                    ``fn:src/pycode_kg/store.py:GraphStore.expand``.
    :param q: Optional query string.  When provided, semantic score and
              proximity to the query seed set are included in the report.
    :return: Markdown-formatted explanation of the node's rank components.
    """
    from pycode_kg.ranking.coderank import (  # noqa: PLC0415
        DEFAULT_GLOBAL_RELS,
        build_code_graph,
        compute_coderank,
        compute_seed_proximity,
    )

    kg = kg_from(ctx)
    db_path = str(kg.db_path)

    node = kg.node(node_id)
    if node is None:
        return f"## Node Not Found\n\nNode ID `{node_id}` does not exist."

    kind = node.get("kind", "unknown")
    name = node.get("qualname") or node.get("name", "unknown")
    out: list[str] = [f"## CodeRank Explanation: `{name}` ({kind})\n"]
    out.append(f"- **ID:** `{node_id}`")
    if node.get("module_path"):
        out.append(f"- **Module:** `{node['module_path']}`")
    out.append("")

    # Build graph and compute global CodeRank
    try:
        graph = build_code_graph(
            db_path,
            include_relations=list(DEFAULT_GLOBAL_RELS),
            exclude_test_paths=True,
        )
        scores = compute_coderank(graph)
    except Exception as exc:  # noqa: BLE001
        return f"## Error\n\nFailed to build graph: `{exc}`"

    global_score = scores.get(node_id, 0.0)
    meaningful_scores = sorted(
        (v for k, v in scores.items() if not k.startswith("sym:")), reverse=True
    )
    rank_pos = next(
        (i + 1 for i, s in enumerate(meaningful_scores) if s <= global_score),
        len(meaningful_scores),
    )

    out.append("### Global CodeRank\n")
    out.append(f"- **Score:** `{global_score:.8f}`")
    out.append(f"- **Rank:** #{rank_pos} of {len(meaningful_scores)} meaningful nodes")
    out.append("")

    # Structural context from graph
    if node_id in graph:
        in_edges = list(graph.in_edges(node_id, data=True))
        out.append("### Structural Inbound Edges\n")
        callers_count = sum(1 for _, _, d in in_edges if "CALLS" in d.get("relations", set()))
        importers_count = sum(1 for _, _, d in in_edges if "IMPORTS" in d.get("relations", set()))
        inheritors_count = sum(1 for _, _, d in in_edges if "INHERITS" in d.get("relations", set()))
        if callers_count:
            out.append(f"- Called by **{callers_count}** upstream node(s)")
        if importers_count:
            out.append(f"- Imported by **{importers_count}** upstream node(s)")
        if inheritors_count:
            out.append(f"- Inherited by **{inheritors_count}** subclass node(s)")
        if not (callers_count or importers_count or inheritors_count):
            out.append("- No inbound structural edges found in the ranked graph")
        out.append("")

        out_edges = list(graph.out_edges(node_id, data=True))
        if out_edges:
            out.append("### Structural Outbound Edges\n")
            out.append(f"- Calls/imports/inherits **{len(out_edges)}** downstream node(s)")
            out.append("")

    # Optional query-conditioned scores
    if q:
        out.append("### Query-Conditioned Scores\n")
        try:
            raw = kg.query(q, k=8, hop=0)
            seed_data = json.loads(raw.to_json())
            seed_nodes = seed_data.get("nodes", [])
            semantic_scores: dict[str, float] = {
                n["id"]: float((n.get("relevance") or {}).get("score", 0.0)) for n in seed_nodes
            }
            this_semantic = semantic_scores.get(node_id, 0.0)
            out.append(f"- **Query:** `{q}`")
            out.append(f"- **Semantic score:** `{this_semantic:.4f}`")

            if node_id in graph:
                seeds = list(semantic_scores.keys())
                proximity = compute_seed_proximity(graph, seeds)
                prox = proximity.get(node_id, 0.0)
                out.append(f"- **Proximity to seeds:** `{prox:.4f}`")
                if prox >= 1.0:
                    out.append("  → Direct semantic seed")
                elif prox >= 0.5:
                    out.append("  → One hop from a semantic seed")
                elif prox > 0:
                    out.append("  → Within local query neighborhood")
                else:
                    out.append("  → Outside query neighborhood")
        except Exception as exc:  # noqa: BLE001
            out.append(f"- Query scoring failed: `{exc}`")
        out.append("")

    out.append("---\n")
    out.append(
        "*Use `rank_nodes()` for global top-N ranking, or `query_ranked()` for query-conditioned ranking.*"
    )
    return "\n".join(out)


def snapshot_list(limit: int = 10, branch: str = "", *, ctx: Context) -> str:
    """
    List saved temporal snapshots of codebase metrics in reverse chronological order.

    Each entry in the returned list contains a ``key`` (tree hash snapshot
    identifier), ``branch``, ``timestamp``, ``version``, and a summary of
    key metrics (node count, edge count, docstring coverage, critical issues)
    plus deltas vs. the previous snapshot.  Use the ``key`` field when calling
    ``snapshot_show()`` or ``snapshot_diff(key_a=..., key_b=...)``.

    Use this tool to answer questions like "how has the codebase grown?" or
    "when did docstring coverage improve?" or "show me only main-branch snapshots".

    :param limit: Maximum number of snapshots to return (default 10; pass 0 for all).
    :param branch: If provided, filter to snapshots from this branch only
                   (e.g. ``"main"`` or ``"develop"``).
    :return: JSON array of snapshot metadata dicts, most recent first.
    """
    mgr = _snapshots(kg_from(ctx))
    snapshots = mgr.list_snapshots(
        limit=limit if limit > 0 else None,
        branch=branch if branch else None,
    )
    for snap in snapshots:
        snap_metrics = snap.get("metrics", {})
        snap["freshness"] = _snapshot_freshness(kg_from(ctx), snap_metrics.get("total_nodes", 0))
    return json.dumps(snapshots, indent=2, ensure_ascii=False)


def snapshot_show(key: str = "latest", *, ctx: Context) -> str:
    """
    Show full details of a specific codebase metrics snapshot.

    Pass a snapshot key (tree hash) to retrieve that exact snapshot, or use
    the special value ``"latest"`` (default) to retrieve the most recent one.

    Snapshot keys are the ``key`` field returned by ``snapshot_list()``.

    The returned object contains the full ``SnapshotMetrics`` (total_nodes,
    total_edges, meaningful_nodes, docstring_coverage, node_counts,
    edge_counts, critical_issues, complexity_median), the top complexity
    hotspots, and deltas computed vs. both the previous and the baseline
    (oldest) snapshots.

    :param key: Snapshot key to load, or ``"latest"`` for the most
                recent snapshot (default ``"latest"``).  Keys are tree
                hashes returned by ``snapshot_list()``.
    :return: JSON object with full snapshot details, or an error dict if
             the requested snapshot does not exist.
    """
    mgr = _snapshots(kg_from(ctx))

    if key == "latest":
        entries = mgr.list_snapshots(limit=1)
        if not entries:
            return json.dumps({"error": "No snapshots found."})
        key = entries[0]["key"]

    snapshot = mgr.load_snapshot(key)
    if snapshot is None:
        return json.dumps({"error": f"Snapshot not found for key: {key!r}"})
    out = snapshot.to_dict()
    out["freshness"] = _snapshot_freshness(kg_from(ctx), snapshot.metrics.get("total_nodes", 0))
    return json.dumps(out, indent=2, ensure_ascii=False)


def snapshot_diff(key_a: str, key_b: str, *, ctx: Context) -> str:
    """
    Compare two codebase metric snapshots side-by-side.

    Returns the full ``SnapshotMetrics`` for both snapshots and a computed
    delta (b − a) covering: node count, edge count, docstring coverage
    change, and critical-issues change. It also includes an ``issues_delta``
    listing newly introduced and resolved issues.

    Typical workflow::

        # 1. List available snapshots — note the 'key' field in each entry
        snapshot_list()

        # 2. Diff any two using the key= field values
        snapshot_diff(key_a="abc1234ef...", key_b="def5678ab...")

    :param key_a: First (older) snapshot key — the ``key`` field from
                  ``snapshot_list()`` output (a tree-hash string).
    :param key_b: Second (newer) snapshot key — the ``key`` field from
                  ``snapshot_list()`` output (a tree-hash string).
    :return: JSON object with keys ``a`` (metrics + issues list for key_a),
             ``b`` (metrics + issues list for key_b), ``delta`` (b − a),
             and ``module_node_counts_delta`` (per-module node count changes,
             only modules that differ). Returns an error dict if either snapshot
             is missing.
    """
    mgr = _snapshots(kg_from(ctx))
    result = mgr.diff_snapshots(key_a, key_b)
    if "error" not in result:
        result["freshness"] = {
            "a": _snapshot_freshness(
                kg_from(ctx), result.get("a", {}).get("metrics", {}).get("total_nodes", 0)
            ),
            "b": _snapshot_freshness(
                kg_from(ctx), result.get("b", {}).get("metrics", {}).get("total_nodes", 0)
            ),
        }
    return json.dumps(result, indent=2, ensure_ascii=False)


#: PyCodeKG's own tools, registered after the canonical set in this order.
EXTRA_TOOLS = (
    callers,
    list_nodes,
    find_node,
    centrality,
    bridge_centrality,
    framework_nodes,
    find_definition_at,
    analyze_repo,
    explain,
    rank_nodes,
    query_ranked,
    explain_rank,
    snapshot_list,
    snapshot_show,
    snapshot_diff,
)


def build_server(
    repo: str | Path,
    db: str | Path | None = None,
    vectors: str | Path | None = None,
    model: str | None = None,
) -> KGServer:
    """Build the PyCodeKG MCP server for one repository, without opening its graph.

    :param repo: Repository root the graph was built from.
    :param db: Graph database; ``None`` for ``<repo>/.pycodekg/graph.sqlite``.
    :param vectors: Vector store; ``None`` for ``<repo>/.pycodekg/vectors.sqlite``.
    :param model: Embedding model; ``None`` for :data:`DEFAULT_MODEL`.
    :return: The server; serve it with :func:`kg_utils.mcp.run`.
    """
    root = Path(repo).resolve()

    def open_kg() -> PyCodeKG:
        return PyCodeKG(root, db, vectors, model=model or DEFAULT_MODEL)

    server = make_server(
        open_kg, name="pycodekg", kind="code", version=__version__, instructions=PREAMBLE
    )
    server.canonical("query")(query)
    server.canonical("pack")(pack)
    for tool in EXTRA_TOOLS:
        server.add_tool(tool)
    return server


def main(argv: list[str] | None = None) -> None:
    """Entry point for ``pycodekg-mcp``: the same command as ``pycodekg mcp``.

    Kept as a console script because Claude Desktop and Copilot configs name
    it; it runs the standard command, so both spellings take the same flags.

    :param argv: Arguments; ``None`` for ``sys.argv[1:]``.
    """
    from pycode_kg.cli.cmd_mcp import mcp_command  # noqa: PLC0415

    mcp_command.main(args=argv, prog_name="pycodekg-mcp")


if __name__ == "__main__":
    main()
