#!/usr/bin/env python3
"""
mcp_server.py — PyCodeKG MCP Server

Exposes the PyCodeKG hybrid query and snippet-pack pipeline as
Model Context Protocol (MCP) tools, allowing any MCP-compatible
agent (Claude Desktop, Cursor, Continue, etc.) to query a codebase
knowledge graph directly.

Operational notes:
- Entry points and configuration: the CLI ``main()`` resolves repo, SQLite,
    and LanceDB paths with sensible defaults under ``.pycodekg/``.
- Logging approach: startup diagnostics and warnings are written to stderr so
    host MCP clients can capture runtime state.
- Error handling strategy: startup reports misconfiguration warnings clearly
    (for example missing SQLite graph) before attempting tool execution.

Tools
-----
query_codebase(q, k, hop, rels, include_symbols, max_nodes, min_score, max_per_module, paths, rerank_mode, rerank_semantic_weight, rerank_lexical_weight, include_edge_provenance)
    Hybrid semantic + structural query.  Returns ranked nodes and edges
    as a JSON string.  Default rerank_mode='hybrid' (70% semantic +
    30% lexical overlap); pass rerank_mode='legacy' to restore hop-first
    ordering.

pack_snippets(q, k, hop, rels, include_symbols, context, max_lines, max_nodes, min_score, max_per_module, rerank_mode, rerank_semantic_weight, rerank_lexical_weight, missing_lineno_policy, include_edge_provenance)
    Hybrid query + source-grounded snippet extraction.  Returns a
    Markdown context pack suitable for direct LLM ingestion.  Default
    rerank_mode='hybrid'.  Emits Warnings section when snippets are
    capped or omitted due to missing line metadata.

get_node(node_id, include_edges)
    Fetch a single node by its stable ID.  Returns Markdown with kind,
    location, and docstring.  Pass include_edges=True to also render
    outgoing edges by relation type and incoming CALLS callers, avoiding
    a separate callers() round-trip.  Use query_codebase() to discover
    node IDs.

graph_stats()
    Return node and edge counts by kind/relation as a Markdown summary
    with tables.  Call this first to understand graph scale before
    issuing query_codebase() or pack_snippets().

callers(node_id, rel)
    Find all callers of a node, resolving through ``sym:`` import stubs
    with import-aware filtering for ambiguous same-name targets.
    Returns JSON.  Use get_node(include_edges=True) for a combined
    node + callers view without a separate round-trip.

analyze_repo()
    Run the full nine-phase architectural analysis pipeline and return
    results as Markdown (complexity, coupling, docstring coverage, etc.).

explain(node_id, limit=10)
    Return a Markdown natural-language explanation of a single code node,
    including metadata, docstring, callers, callees, and role assessment.
    limit controls how many callers/callees are listed (0 = all).

snapshot_list(limit, branch)
    List saved temporal snapshots in reverse chronological order.
    Returns JSON array of snapshot metadata with key metrics and
    freshness indicator vs. current DB node count.

snapshot_show(key)
    Show full details of a specific snapshot by key (tree hash), or the
    most recent snapshot when key="latest".  Returns JSON with
    freshness indicator vs. current DB node count.

snapshot_diff(key_a, key_b)
    Compare two snapshots side-by-side and return computed deltas for
    nodes, edges, docstring coverage, and critical issues.  Returns JSON
    including freshness metadata and lists of introduced/resolved issues.

list_nodes(module_path, kind)
    List nodes filtered by module path prefix and/or kind.  Returns a
    JSON array of matching node dicts.  Useful for enumerating classes
    or functions in a specific module.

centrality(top, kinds, group_by)
    Compute Structural Importance Ranking (SIR): a deterministic weighted
    PageRank over the resolved call graph that scores every node by
    structural centrality.  Returns a Markdown ranking table.  Use
    group_by='module' for per-module rollup.

rank_nodes(top, rels, persist_metric, exclude_tests)
    Compute global weighted CodeRank (PageRank) over the repository graph.
    Returns JSON array of top-ranked nodes with score, top_pct (e.g. "top 0.5%"),
    kind, qualname, and module_path.  Optionally persists scores to node_metrics.

query_ranked(q, k, mode, top, rels, radius, exclude_tests)
    Rank query results using CodeRank-enhanced hybrid or personalized
    PageRank.  mode='hybrid' (default) or 'ppr'.  Returns JSON with
    per-node score components (semantic, centrality, proximity) and
    explainability ``why`` strings.

explain_rank(node_id, q)
    Explain the CodeRank score components for a specific node.  Returns
    Markdown with global rank position, inbound/outbound edge counts, and
    optional query-conditioned semantic + proximity scores.

Usage
-----
Install the package, then run::

    pycodekg mcp --repo /path/to/repo

``--db`` and ``--lancedb`` are optional; they default to
``.pycodekg/graph.sqlite`` and ``.pycodekg/lancedb`` relative to ``--repo``.

Per-project config for Claude Code and Kilo Code (``.mcp.json``)::

    {
      "mcpServers": {
        "pycodekg": {
          "command": "/path/to/.venv/bin/pycodekg",
          "args": ["mcp", "--repo", "/path/to/repo"]
        }
      }
    }

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from pycode_kg import PyCodeKG
from pycode_kg.pycodekg import DEFAULT_MODEL
from pycode_kg.pycodekg_thorough_analysis import PyCodeKGAnalyzer
from pycode_kg.snapshots import SnapshotManager
from pycode_kg.store import DEFAULT_RELS

# ---------------------------------------------------------------------------
# Global state — initialised in main() before the server starts
# ---------------------------------------------------------------------------

_kg: PyCodeKG | None = None
_snapshot_mgr: SnapshotManager | None = None


def _get_kg() -> PyCodeKG:
    """
    Return the global PyCodeKG instance, raising if it has not been initialised.

    :return: The active PyCodeKG instance.
    :raises RuntimeError: If ``main()`` has not been called to initialise the graph.
    """
    if _kg is None:
        raise RuntimeError(
            "PyCodeKG not initialised.  Run the server via 'pycodekg-mcp --repo /path/to/repo'"
        )
    return _kg


def _get_snapshot_mgr() -> SnapshotManager:
    """
    Return the global SnapshotManager instance, raising if not initialised.

    :return: The active SnapshotManager instance.
    :raises RuntimeError: If ``main()`` has not been called to initialise the server.
    """
    if _snapshot_mgr is None:
        raise RuntimeError(
            "SnapshotManager not initialised.  Run the server via 'pycodekg-mcp --repo /path/to/repo'"
        )
    return _snapshot_mgr


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


def _snapshot_freshness(snapshot_total_nodes: int) -> dict:
    """Compare a snapshot's node count against the currently loaded graph DB.

    :param snapshot_total_nodes: ``metrics.total_nodes`` from a snapshot object.
    :return: Freshness metadata payload.
    """
    current = _get_kg().stats()
    current_nodes = int(current.get("total_nodes", 0))
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
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "pycodekg",
    instructions=(
        "PyCodeKG is a hybrid semantic + structural knowledge graph for a Python codebase. "
        "It indexes every module, class, function, and method as a node, with typed edges "
        "(CALLS, IMPORTS, CONTAINS, INHERITS) connecting them. Use these tools to navigate "
        "and understand the codebase precisely and efficiently.\n\n"
        "## Tools\n\n"
        "**graph_stats()** — Start here when you first engage with a repo. Returns a Markdown "
        "summary with total node and edge counts broken down by kind (module, class, function, "
        "method) and relation, plus meaningful_nodes (real code entities, excluding sym: stubs). "
        "Use it to understand the size and shape of the codebase before issuing "
        "query_codebase() or pack_snippets() queries.\n\n"
        "**query_codebase(q, k, hop, rels, include_symbols, max_nodes, min_score, max_per_module, paths, rerank_mode, rerank_semantic_weight, rerank_lexical_weight, include_edge_provenance)** — Hybrid "
        "semantic + structural search. Seeds on vector similarity then expands through the "
        "graph. Use hop=0 for pure semantic lookup (highest precision), hop=1 (default) for "
        "call chains and module relationships, hop=2 for broad dependency tracing. Use the "
        "paths parameter to restrict results to a specific subtree (e.g. 'src/pycode_kg'). "
        "rerank_mode controls result ordering: 'hybrid' (default) blends vector similarity "
        "(70%) with lexical name/docstring overlap (30%) — best overall quality; 'semantic' "
        "ranks by vector score only; 'legacy' uses hop-first ordering (pre-reranking behavior, "
        "use only for stable comparisons). Set include_edge_provenance=True to annotate "
        "inferred edges with confidence and resolution metadata. "
        "For precision queries where you know the concept well, use min_score=0.5 to filter "
        "out incidental docstring mentions. "
        "Returns ranked nodes and edges as JSON.\n\n"
        "**pack_snippets(q, k, hop, rels, include_symbols, context, max_lines, max_nodes, min_score, max_per_module, rerank_mode, rerank_semantic_weight, rerank_lexical_weight, missing_lineno_policy, include_edge_provenance)** — "
        "Same hybrid search as query_codebase, but returns actual source code. Produces a "
        "Markdown context pack with ranked, deduplicated snippets and line numbers. Prefer "
        "this over query_codebase whenever you need to read or reason about implementation "
        "details, trace logic, or answer 'how does X work?' questions. Default rerank_mode "
        "is 'hybrid' (same as query_codebase). Includes a Warnings section when snippets "
        "are capped or omitted due to missing line metadata.\n\n"
        "**get_node(node_id, include_edges)** — Precise lookup of a single node by its stable ID "
        "(format: '<kind>:<module_path>:<qualname>', e.g. "
        "'cls:src/pycode_kg/store.py:GraphStore'). Returns Markdown with kind, location, ID, "
        "and full docstring. Pass include_edges=True to also render the node's immediate "
        "neighborhood: outgoing edges grouped by relation type (CALLS, CONTAINS, IMPORTS, "
        "INHERITS) and resolved incoming CALLS callers, eliminating a separate callers() "
        "round-trip. Use query_codebase() to discover node IDs, then get_node() to inspect "
        "them, then pack_snippets() to read the source.\n\n"
        "**list_nodes(module_path, kind)** — List nodes filtered by module path prefix "
        "and/or kind (e.g. 'function', 'class'). Returns a JSON array of matching nodes. "
        "Use this to enumerate the contents of a specific module before inspecting "
        "individual nodes with get_node().\n\n"
        "**centrality(top, kinds, group_by)** — Compute Structural Importance Ranking (SIR): "
        "a deterministic weighted PageRank over the sym-stub-resolved call graph. Edge weights "
        "favour CALLS > INHERITS > IMPORTS > CONTAINS; cross-module edges receive a boost and "
        "private symbols are penalized. Returns a Markdown ranking table. Use top to cap "
        "results (default 20), kinds to filter by node type (e.g. 'class,function'), and "
        "group_by='module' for a per-module rollup. Ideal for identifying hotspots before "
        "refactoring, prioritizing test coverage, or understanding which modules are most "
        "depended upon.\n\n"
        "**explain(node_id, limit=10)** — Natural-language orientation for a single node. Returns a "
        "Markdown report with: kind and qualified name, module path and line range, full "
        "docstring, list of callers (what calls this node), list of callees (what this node "
        "calls), and a role assessment (high-value / utility / orphaned) based on call count. "
        "Pass limit=0 to list all callers and callees without truncation. "
        "Use this as the first step when a user asks about a specific function or class, "
        "before reaching for pack_snippets.\n\n"
        "**callers(node_id, rel, paths)** — Reverse edge lookup: find every node that calls "
        "(or imports, or inherits from) a given node. Resolves through sym: import stubs so "
        "cross-module callers are included. Use paths to restrict to production code only "
        "(e.g. paths='src/'). Returns JSON with node_id, rel, caller_count, and a callers "
        "list of node dicts — suitable for programmatic processing or chaining into other "
        "tools. Useful for impact analysis — 'what breaks if I change X?'. "
        "Alternatively, use get_node(include_edges=True) to get callers alongside the full "
        "node details in a single call.\n\n"
        "**analyze_repo()** — Full nine-phase architectural analysis: complexity hotspots, "
        "high fan-out functions, module coupling, circular dependencies, key call chains, "
        "public API surface, docstring coverage, code quality issues, and orphaned code. "
        "Returns structured Markdown. Use when the user wants a health check or architectural "
        "overview of the entire codebase.\n\n"
        "**snapshot_list(limit, branch)** — List saved temporal snapshots in reverse "
        "chronological order. Each entry has a ``key`` (tree hash), branch, timestamp, "
        "version, and key metrics (nodes, edges, coverage, critical issues) plus deltas vs. "
        "the previous snapshot. Optional ``branch`` filters to a specific branch. Each "
        "entry includes a freshness indicator comparing snapshot node count to the current DB. "
        "Use to answer 'how has the codebase grown?' or 'when did coverage improve?'\n\n"
        "**snapshot_show(key)** — Show full details of a specific snapshot by its ``key`` "
        "(tree hash from snapshot_list), or the most recent snapshot when key='latest' "
        "(default). Returns full metrics, complexity hotspots, deltas vs. both the "
        "previous and baseline snapshots, plus freshness vs. current DB.\n\n"
        "**snapshot_diff(key_a, key_b)** — Compare two snapshots side-by-side. Returns "
        "metrics for both snapshots and a computed delta (b − a) for nodes, edges, coverage, "
        "and critical issues, along with lists of introduced and resolved issues. Also reports "
        "freshness for both snapshots. Use snapshot_list() first to get the ``key`` values.\n\n"
        "## Recommended Workflows\n\n"
        "- **Explore unfamiliar code**: graph_stats → query_codebase → list_nodes (to enumerate a module) → explain → pack_snippets\n"
        "- **Understand a specific function**: get_node(include_edges=True) → pack_snippets\n"
        "- **Impact analysis before a change**: explain → callers (with paths='src/')\n"
        "- **Architecture review**: analyze_repo\n"
        "- **Answer 'how does X work?'**: pack_snippets with a descriptive query\n"
        "- **Track codebase evolution**: snapshot_list → snapshot_diff(key_a=..., key_b=...)\n"
        "- **Identify most important code**: centrality(top=20) → explain → pack_snippets\n\n"
        "## CodeRank Tools\n\n"
        "**rank_nodes(top, rels, persist_metric, exclude_tests)** — Compute global weighted "
        "CodeRank (PageRank) over the repository graph. Returns a JSON array of the top-N "
        "most structurally important nodes with score, top_pct (e.g. 'top 0.5%'), kind, "
        "qualname, and module_path. "
        "Pass persist_metric='coderank_global' to save scores into the node_metrics table "
        "for later use at query time. Relation weights: CALLS=1.0, IMPORTS=0.9, INHERITS=0.75. "
        "Test paths are excluded by default.\n\n"
        "**query_ranked(q, k, mode, top, rels, radius, exclude_tests)** — Rank query results "
        "using CodeRank-enhanced hybrid or personalized PageRank. Combines semantic seed scores "
        "from the vector index with structural centrality and graph proximity. "
        "mode='hybrid' (default): 0.60×semantic + 0.25×centrality + 0.15×proximity. "
        "mode='ppr': 0.70×personalized PageRank + 0.30×semantic. "
        "Returns JSON with per-node score components and explainability 'why' strings. "
        "Use this instead of query_codebase when you want structure-aware ranking.\n\n"
        "**explain_rank(node_id, q)** — Explain the CodeRank score components for a specific "
        "node. Returns Markdown with global rank position, inbound/outbound edge counts "
        "(callers, importers, inheritors), and optional query-conditioned semantic + proximity "
        "scores when q is provided. Use after rank_nodes or query_ranked to understand why "
        "a node ranked where it did.\n\n"
        "## CodeRank Workflows\n\n"
        "- **Find most important nodes globally**: rank_nodes(top=25) → explain_rank\n"
        "- **Persist global rank for later use**: rank_nodes(persist_metric='coderank_global')\n"
        "- **Structure-aware query**: query_ranked(q='database connection', mode='hybrid')\n"
        "- **PPR query**: query_ranked(q='...', mode='ppr') → explain_rank(node_id, q='...')"
    ),
)


@mcp.tool()
def query_codebase(
    q: str,
    k: int = 8,
    hop: int = 1,
    rels: str = "CONTAINS,CALLS,IMPORTS,INHERITS",
    include_symbols: bool = False,
    max_nodes: int = 25,
    min_score: float = 0.0,
    max_per_module: int = 0,
    paths: str = "",
    rerank_mode: str = "hybrid",
    rerank_semantic_weight: float = 0.7,
    rerank_lexical_weight: float = 0.3,
    include_edge_provenance: bool = False,
) -> str:
    """
    Hybrid semantic + structural query over the codebase knowledge graph.

    Performs vector-similarity seeding followed by graph expansion to return
    a ranked set of relevant nodes (modules, classes, functions, methods) and
    the edges between them.

    **hop heuristic:**

    - ``hop=0`` — pure semantic search; highest precision, no graph expansion.
      Best for concept lookup ("find the retry logic").
    - ``hop=1`` — semantic seeds + 1-hop expansion (default); reveals call
      chains and module relationships. Best for architecture questions.
    - ``hop=2`` — deep dependency tracing; may return many loosely related
      nodes. Use only when you need broad coverage.

    **rerank_mode** controls result ordering after graph expansion:

    - ``hybrid`` (default) — blends vector similarity (70%) with lexical
      overlap on name/qualname/module/docstring (30%). Best overall quality:
      surfaces the right node even when the embedding alone is weak.
    - ``semantic`` — ranks purely by vector similarity score. Use when
      exact name matching is not important.
    - ``legacy`` — hop distance first, then vector distance. Preserves
      pre-reranking behavior; use only if you need stable ordering for
      comparisons against older results.

    :param q: Natural-language query, e.g. "database connection setup".
    :param k: Number of semantic seed nodes (default 8).
    :param hop: Graph expansion hops from each seed (default 1).
    :param rels: Comma-separated edge types to follow
                 (CONTAINS, CALLS, IMPORTS, INHERITS).
    :param include_symbols: Include low-level symbol nodes (default False).
    :param max_nodes: Maximum nodes to return (default 25).
    :param min_score: Minimum semantic score for seed inclusion in ``[0, 1]``.
    :param max_per_module: Maximum nodes per module (0 disables this cap).
    :param paths: Comma-separated module path prefixes to include, e.g.
                  ``"src/pycode_kg"`` to exclude tests and scripts.
                  Empty string (default) returns all paths.
    :param rerank_mode: Ranking strategy: ``hybrid`` (default), ``semantic``,
        or ``legacy``.
    :param rerank_semantic_weight: Semantic component weight for ``hybrid``
        mode (default 0.7).
    :param rerank_lexical_weight: Lexical component weight for ``hybrid``
        mode (default 0.3).
    :param include_edge_provenance: When ``True``, inferred edges include
        confidence/provenance fields when available.
    :return: JSON string with keys: query, seeds, expanded_nodes,
             returned_nodes, hop, rels, nodes, edges.
    """
    rel_tuple = tuple(r.strip() for r in rels.split(",") if r.strip())
    result = _get_kg().query(
        q,
        k=k,
        hop=hop,
        rels=rel_tuple or DEFAULT_RELS,
        include_symbols=include_symbols,
        max_nodes=max_nodes,
        min_score=min_score,
        max_per_module=max_per_module if max_per_module > 0 else None,
        rerank_mode=rerank_mode,
        rerank_semantic_weight=rerank_semantic_weight,
        rerank_lexical_weight=rerank_lexical_weight,
    )
    data = json.loads(result.to_json())
    if include_edge_provenance:
        data["edges"] = _enrich_edges_with_provenance(data.get("edges", []))
    if not paths:
        return json.dumps(data, indent=2, ensure_ascii=False)

    path_prefixes = [p.strip() for p in paths.split(",") if p.strip()]
    included_ids = {
        n["id"]
        for n in data["nodes"]
        if any((n.get("module_path") or "").startswith(pfx) for pfx in path_prefixes)
    }
    data["nodes"] = [n for n in data["nodes"] if n["id"] in included_ids]
    data["edges"] = [
        e for e in data["edges"] if e["src"] in included_ids and e["dst"] in included_ids
    ]
    data["returned_nodes"] = len(data["nodes"])
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
def pack_snippets(
    q: str,
    k: int = 8,
    hop: int = 1,
    rels: str = "CONTAINS,CALLS,IMPORTS,INHERITS",
    include_symbols: bool = False,
    context: int = 5,
    max_lines: int = 60,
    max_nodes: int = 15,
    min_score: float = 0.0,
    max_per_module: int = 0,
    rerank_mode: str = "hybrid",
    rerank_semantic_weight: float = 0.7,
    rerank_lexical_weight: float = 0.3,
    missing_lineno_policy: str = "cap_or_skip",
    include_edge_provenance: bool = False,
) -> str:
    """
    Hybrid query + source-grounded snippet extraction.

    Returns a Markdown context pack containing ranked, deduplicated code
    snippets with line numbers — ready for direct LLM ingestion.

    **rerank_mode** controls result ordering after graph expansion:

    - ``hybrid`` (default) — blends vector similarity (70%) with lexical
      overlap on name/qualname/module/docstring (30%). Best overall quality:
      surfaces the right node even when the embedding alone is weak.
    - ``semantic`` — ranks purely by vector similarity score. Use when
      exact name matching is not important.
    - ``legacy`` — hop distance first, then vector distance. Preserves
      pre-reranking behavior; use only if you need stable ordering for
      comparisons against older results.

    :param q: Natural-language query, e.g. "configuration loading".
    :param k: Number of semantic seed nodes (default 8).
    :param hop: Graph expansion hops (default 1).
    :param rels: Comma-separated edge types to follow.
    :param include_symbols: Include symbol nodes (default False).
    :param context: Extra context lines around each definition (default 5).
    :param max_lines: Maximum lines per snippet block (default 60).
    :param max_nodes: Maximum nodes to include in the pack (default 15).
    :param min_score: Minimum semantic score for seed inclusion in ``[0, 1]``.
    :param max_per_module: Maximum nodes per module (0 disables this cap).
    :param rerank_mode: Ranking strategy: ``hybrid`` (default), ``semantic``,
        or ``legacy``.
    :param rerank_semantic_weight: Semantic component weight for ``hybrid``
        mode (default 0.7).
    :param rerank_lexical_weight: Lexical component weight for ``hybrid``
        mode (default 0.3).
    :param missing_lineno_policy: Behavior when a non-module node has missing
        line metadata: ``cap_or_skip`` (default) falls back to a capped parent
        span or omits the snippet; ``legacy`` uses the old uncapped behavior.
    :param include_edge_provenance: When ``True``, enrich edges in markdown
        output with inferred confidence/provenance fields.
    :return: Markdown string with source-grounded code snippets.
    """
    rel_tuple = tuple(r.strip() for r in rels.split(",") if r.strip())
    pack = _get_kg().pack(
        q,
        k=k,
        hop=hop,
        rels=rel_tuple or DEFAULT_RELS,
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
        pack.edges = _enrich_edges_with_provenance(pack.edges)
    return pack.to_markdown()


@mcp.tool()
def callers(node_id: str, rel: str = "CALLS", paths: str = "") -> str:
    """
    Return all nodes that call a given node, resolving through ``sym:`` stubs.

    Unlike ``query_codebase`` (which seeds on semantics and expands outward),
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
    caller_list = _get_kg().callers(node_id, rel=rel)
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


@mcp.tool()
def get_node(node_id: str, include_edges: bool = False) -> str:
    """
    Fetch a single node by its stable ID and render it as Markdown.

    Node IDs follow the pattern ``<kind>:<module_path>:<qualname>``,
    e.g. ``cls:src/pycode_kg/store.py:GraphStore`` or
    ``fn:src/pycode_kg/store.py:GraphStore.expand``.  Use
    ``query_codebase()`` to discover node IDs when the exact ID is
    unknown.

    When *include_edges* is ``True`` the Markdown report also contains
    the node's immediate neighborhood — outgoing edges grouped by
    relation type (CALLS, CONTAINS, IMPORTS, INHERITS) and all resolved
    incoming CALLS callers — eliminating a separate ``callers()``
    round-trip for routine inspection.  Follow up with ``pack_snippets()``
    to retrieve the actual source implementation.

    Example workflow::

        # 1. Discover the node ID
        query_codebase("graph database storage")

        # 2. Inspect the node and its neighborhood
        get_node("cls:src/pycode_kg/store.py:GraphStore", include_edges=True)

        # 3. Read the source
        pack_snippets("GraphStore implementation")

    :param node_id: Stable node identifier in ``<kind>:<module_path>:<qualname>``
                    format, e.g. ``fn:src/pycode_kg/store.py:GraphStore.expand``.
    :param include_edges: If ``True``, append outgoing edges by relation type
                          and incoming CALLS callers to the report
                          (default ``False``).
    :return: Markdown-formatted node summary with optional neighborhood, or an
             error section if the node does not exist.
    """
    kg = _get_kg()
    node = kg.node(node_id)
    if node is None:
        return f"## Node Not Found\n\nNode ID `{node_id}` does not exist in the knowledge graph."

    kind = node.get("kind", "unknown")
    name = node.get("qualname") or node.get("name", "unknown")
    out: list[str] = [f"## `{name}` ({kind})\n"]

    module = node.get("module_path", "")
    lineno = node.get("lineno")
    end_lineno = node.get("end_lineno")
    if module:
        out.append(f"- **Module:** `{module}`")
    if lineno is not None:
        loc = f"line {lineno}"
        if end_lineno:
            loc += f"–{end_lineno}"
        out.append(f"- **Location:** {loc}")
    out.append(f"- **ID:** `{node_id}`")
    out.append("")

    docstring = node.get("docstring", "").strip()
    if docstring:
        out.append("### Documentation\n")
        out.append(docstring)
        out.append("")

    if not include_edges:
        return "\n".join(out)

    # Build neighborhood: outgoing edges per relation type
    store = getattr(kg, "_store", None)
    if store is not None:
        for rel in ("CALLS", "CONTAINS", "IMPORTS", "INHERITS"):
            edges = store.edges_from(node_id, rel=rel)
            visible = [e for e in edges if not e["dst"].startswith("sym:")] if edges else []
            if visible:
                out.append(f"### Outgoing {rel}\n")
                for e in visible:
                    out.append(f"- `{e['dst']}`")
                out.append("")

    # Incoming CALLS callers (resolved through sym: stubs)
    try:
        caller_nodes = kg.callers(node_id, rel="CALLS")
        if caller_nodes:
            out.append("### Incoming Calls\n")
            for c in caller_nodes:
                cname = c.get("qualname") or c.get("name", "")
                cmod = c.get("module_path", "")
                cline = c.get("lineno")
                cid = c.get("id", "")
                loc_str = f" (line {cline})" if cline else ""
                out.append(f"- `{cid}` — `{cname}` in `{cmod}`{loc_str}")
            out.append("")
    except (AttributeError, ValueError, RuntimeError):
        pass

    return "\n".join(out)


@mcp.tool()
def graph_stats() -> str:
    """
    Return node and edge counts broken down by kind and relation as Markdown.

    Call this first when engaging with a new repo to understand the scale and
    shape of the knowledge graph before issuing ``query_codebase()`` or
    ``pack_snippets()`` queries.  ``meaningful_nodes`` excludes ``sym:``
    infrastructure stubs so the count reflects real code entities (modules,
    classes, functions, methods).

    :return: Markdown-formatted summary with total counts, a nodes-by-kind
             table, and an edges-by-relation table.
    """
    stats = _get_kg().stats()
    out: list[str] = ["## PyCodeKG Graph Statistics\n"]
    out.append(f"- **Database:** `{stats.get('db_path', '')}`")
    out.append(f"- **Total nodes:** {stats.get('total_nodes', 0):,}")
    out.append(
        f"- **Meaningful nodes:** {stats.get('meaningful_nodes', 0):,} *(excludes sym: stubs)*"
    )
    out.append(f"- **Total edges:** {stats.get('total_edges', 0):,}")
    out.append("")

    node_counts: dict = stats.get("node_counts", {})
    if node_counts:
        out.append("### Nodes by Kind\n")
        out.append("| Kind | Count |")
        out.append("|------|------:|")
        for kind, count in sorted(node_counts.items(), key=lambda x: -x[1]):
            out.append(f"| {kind} | {count:,} |")
        out.append("")

    edge_counts: dict = stats.get("edge_counts", {})
    if edge_counts:
        out.append("### Edges by Relation\n")
        out.append("| Relation | Count |")
        out.append("|----------|------:|")
        for rel, count in sorted(edge_counts.items(), key=lambda x: -x[1]):
            out.append(f"| {rel} | {count:,} |")
        out.append("")

    out.append(
        "> `sym:` nodes are import stub placeholders used for cross-module caller resolution — they are not local code entities."
    )
    return "\n".join(out)


@mcp.tool()
def list_nodes(module_path: str = "", kind: str = "") -> str:
    """
    List nodes filtered by module path prefix and/or kind.

    :param module_path: Module path prefix filter (e.g. "src/pycode_kg/store.py").
    :param kind: Node kind filter: module | class | function | method.
    :return: JSON array of matching node dicts.
    """
    kg = _get_kg()
    store = getattr(kg, "_store", None)
    if not store:
        return json.dumps({"error": "No database store available."}, indent=2)

    query = "SELECT id, name, qualname, kind, module_path, lineno, docstring FROM nodes WHERE 1=1"
    params = []

    if module_path:
        query += " AND module_path LIKE ?"
        params.append(f"{module_path}%")

    if kind:
        query += " AND kind = ?"
        params.append(kind)

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
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def centrality(
    top: int = 20,
    kinds: str = "",
    group_by: str = "node",
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
        from pycode_kg.analysis.centrality import (  # pylint: disable=import-outside-toplevel
            StructuralImportanceRanker,
            aggregate_module_scores,
        )

        db_path = _get_kg().db_path
        ranker = StructuralImportanceRanker(db_path)
        all_records = ranker.compute()
    except Exception as e:  # pylint: disable=broad-except
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


@mcp.tool()
def bridge_centrality(
    top: int = 20,
    include_imports: bool = True,
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
        from pycode_kg.analysis.bridge import (  # pylint: disable=import-outside-toplevel
            compute_bridge_centrality,
        )

        db_path = str(_get_kg().db_path)
        modules = compute_bridge_centrality(
            kind="module",
            include_imports=include_imports,
            top=top,
            db_path=db_path,
        )
    except Exception as e:  # pylint: disable=broad-except
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


@mcp.tool()
def framework_nodes(top: int = 20) -> str:
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
        from pycode_kg.analysis.bridge import (  # pylint: disable=import-outside-toplevel
            compute_bridge_centrality,
        )
        from pycode_kg.analysis.centrality import (  # pylint: disable=import-outside-toplevel
            StructuralImportanceRanker,
        )
        from pycode_kg.analysis.framework_detector import (  # pylint: disable=import-outside-toplevel
            detect_framework_nodes,
        )

        kg = _get_kg()
        db_path = str(kg.db_path)

        # Compute and persist SIR scores (structural importance)
        try:
            ranker = StructuralImportanceRanker(db_path)
            records = ranker.compute()
            ranker.write_scores(records, metric="sir_pagerank")
        except Exception as e:  # pylint: disable=broad-except
            return f"## Framework Nodes Error\n\nFailed to compute SIR scores: `{e}`"

        # Compute and persist module connectivity scores (interaction complexity)
        try:
            compute_bridge_centrality(kind="module", include_imports=True, top=25, db_path=db_path)
        except Exception as e:  # pylint: disable=broad-except
            return f"## Framework Nodes Error\n\nFailed to compute module connectivity: `{e}`"

        # Detect framework nodes by combining both metrics
        nodes = detect_framework_nodes(limit=top, db_path=db_path)
    except Exception as e:  # pylint: disable=broad-except
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


@mcp.tool()
def analyze_repo() -> str:
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
    ``pack_snippets()`` tool's Markdown output format.

    :return: Markdown-formatted string containing timestamp, baseline metrics,
             complexity hotspots, high fan-out functions, module architecture,
             key call chains, public APIs, docstring coverage, code quality
             issues, architectural strengths, and orphaned code.
    """
    from io import StringIO  # pylint: disable=import-outside-toplevel

    from rich.console import Console  # pylint: disable=import-outside-toplevel

    silent = Console(file=StringIO(), highlight=False)
    analyzer = PyCodeKGAnalyzer(_get_kg(), console=silent, snapshot_mgr=_snapshot_mgr)
    analyzer.run_analysis()
    return analyzer.to_markdown()


@mcp.tool()
def explain(node_id: str, limit: int = 10) -> str:
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
    without needing to read the full source code. Use ``pack_snippets()``
    to then retrieve the actual implementation.

    :param node_id: Stable node identifier, e.g.
                    ``fn:src/pycode_kg/store.py:GraphStore.expand``.
    :param limit: Maximum callers and callees to list (default 10). Pass 0
                  to list all.
    :return: Markdown-formatted explanation ready for LLM consumption.
    """
    kg = _get_kg()
    node = kg.node(node_id)

    if node is None:
        return f"# Node Not Found\n\nNode ID `{node_id}` does not exist in the knowledge graph."

    out: list[str] = []

    # Header with kind and name
    kind = node.get("kind", "unknown")
    name = node.get("qualname") or node.get("name", "unknown")
    out.append(f"# {kind.capitalize()}: `{name}`\n")

    # Metadata
    out.append("## Metadata\n")
    if node.get("module_path"):
        out.append(f"- **Module**: `{node['module_path']}`")
    if node.get("lineno") is not None:
        out.append(
            f"- **Location**: line {node['lineno']}"
            + (f"–{node['end_lineno']}" if node.get("end_lineno") else "")
        )
    out.append(f"- **ID**: `{node_id}`")
    out.append("")

    # Docstring
    docstring = node.get("docstring", "").strip()
    if docstring:
        out.append("## Documentation\n")
        out.append(docstring)
        out.append("")

    # Get callers
    try:
        caller_list = kg.callers(node_id, rel="CALLS")
        if caller_list:
            out.append("## Called By (Callers)\n")
            out.append(f"This {kind} is called by **{len(caller_list)}** other function(s):\n")
            shown_callers = caller_list[:limit] if limit > 0 else caller_list
            for caller in shown_callers:
                caller_name = caller.get("qualname") or caller.get("name", "unknown")
                caller_module = caller.get("module_path", "")
                out.append(f"- `{caller_name}` ({caller_module})")
            if limit > 0 and len(caller_list) > limit:
                out.append(f"- ... and {len(caller_list) - limit} more")
            out.append("")
    except (AttributeError, ValueError, RuntimeError):
        pass

    # Get callees (what this function calls)
    try:
        if hasattr(kg, "_store") and kg._store is not None:
            store = kg._store
            edges = store.edges_from(node_id, rel="CALLS", limit=50)
            if edges:
                callees = set()
                for edge in edges:
                    dst = edge.get("dst")
                    if dst is not None:
                        dst_node = kg.node(dst)
                        if (
                            dst_node
                            and dst_node.get("kind") != "symbol"
                            and dst_node.get("module_path")  # exclude builtins/stdlib
                        ):
                            dst_name = dst_node.get("qualname") or dst_node.get("name", "unknown")
                            callees.add(f"- `{dst_name}`")
                if callees:
                    out.append("## Calls (Callees)\n")
                    out.append(f"This {kind} calls **{len(callees)}** other function(s):\n")
                    sorted_callees = sorted(callees)
                    shown_callees = sorted_callees[:limit] if limit > 0 else sorted_callees
                    for callee in shown_callees:
                        out.append(callee)
                    if limit > 0 and len(callees) > limit:
                        out.append(f"- ... and {len(callees) - limit} more")
                    out.append("")
    except (AttributeError, ValueError, RuntimeError):
        pass

    # Role assessment — use relative thresholds so that a node called by >5% of
    # meaningful nodes is always flagged high-value, regardless of codebase size.
    out.append("## Role in Codebase\n")
    try:
        caller_count = len(kg.callers(node_id, rel="CALLS"))
        # Compute callee count for orchestrator detection — a node that calls many
        # things is a coordination hub even if it has few callers.
        callee_count = 0
        try:
            if hasattr(kg, "_store") and kg._store is not None:
                _callee_edges = kg._store.edges_from(node_id, rel="CALLS", limit=100)
                callee_count = sum(
                    1
                    for _e in (_callee_edges or [])
                    if not (_e.get("dst") or "").startswith("sym:")
                    and kg.node(_e.get("dst") or "")
                    and (kg.node(_e.get("dst") or "") or {}).get("module_path")
                )
        except (AttributeError, ValueError, RuntimeError):
            pass
        try:
            meaningful_nodes = kg.stats().get("meaningful_nodes", 100)
        except (AttributeError, ValueError, RuntimeError):
            meaningful_nodes = 100
        _thresh_high_value = max(15, int(meaningful_nodes * 0.05))  # top 5%
        _thresh_important = max(5, int(meaningful_nodes * 0.02))  # top 2%
        _thresh_orchestrator = 8  # calling 8+ distinct functions signals a coordination hub
        if caller_count > _thresh_high_value:
            out.append(
                f"**High-value function**: Called {caller_count} times "
                f"(>{_thresh_high_value} = top 5% of this codebase). "
                "This is likely a core API or bottleneck. Changes here may have wide impact."
            )
        elif caller_count > _thresh_important:
            out.append(
                f"**Important function**: Called {caller_count} times "
                f"(>{_thresh_important} = top 2% of this codebase). "
                "Part of the essential infrastructure."
            )
        elif callee_count >= _thresh_orchestrator and caller_count > 0:
            out.append(
                f"**Core orchestrator**: Called {caller_count} time(s), calls {callee_count} others. "
                "Low caller count likely reflects a top-level entry point — "
                "the high fan-out indicates a coordination hub, not a utility."
            )
        elif caller_count > 0:
            out.append(
                f"**Utility function**: Called {caller_count} time(s). "
                "Specific to particular use cases."
            )
        else:
            module = node.get("module_path", "")
            name = node.get("name", "")
            if name.startswith("__") and name.endswith("__"):
                out.append(
                    "**Protocol method**: Zero internal callers by design. "
                    "Invoked by Python's runtime machinery (e.g., `__init__`, `__str__`, `__exit__`)."
                )
            elif "mcp_server" in module or name.startswith("_get_"):
                out.append(
                    "**MCP Tool / Framework entry point**: Zero internal callers by design. "
                    "Invoked by the MCP protocol dispatcher, not by code."
                )
            elif "/cli/" in module or module.endswith("cli.py"):
                out.append(
                    "**CLI entry point**: Zero internal callers by design. "
                    "Invoked by Click's CLI router when the user runs the command."
                )
            else:
                out.append(
                    "**Orphaned**: Never called internally. "
                    "May be dead code, a public API, or a framework entry point."
                )
    except (AttributeError, ValueError, RuntimeError):
        out.append("Unable to determine call graph role.")

    out.append("")
    out.append("---\n")
    out.append("*Use `pack_snippets()` to retrieve the full source code.*")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# CodeRank MCP tools
# ---------------------------------------------------------------------------


@mcp.tool()
def rank_nodes(
    top: int = 25,
    rels: str = "CALLS,IMPORTS,INHERITS",
    persist_metric: str = "",
    exclude_tests: bool = True,
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
    from pycode_kg.ranking.coderank import (  # pylint: disable=import-outside-toplevel
        build_code_graph,
        compute_coderank,
        persist_metric_scores,
    )

    db_path = str(_get_kg().db_path)
    rel_list = [r.strip() for r in rels.split(",") if r.strip()]

    try:
        graph = build_code_graph(
            db_path,
            include_relations=rel_list,
            exclude_test_paths=exclude_tests,
        )
        scores = compute_coderank(graph)
    except Exception as exc:  # pylint: disable=broad-except
        return json.dumps({"error": str(exc)}, indent=2)

    if persist_metric:
        try:
            persist_metric_scores(db_path, persist_metric, scores)
        except Exception:  # pylint: disable=broad-except
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


@mcp.tool()
def query_ranked(
    q: str,
    k: int = 8,
    mode: str = "hybrid",
    top: int = 25,
    rels: str = "CALLS,IMPORTS,INHERITS",
    radius: int = 2,
    exclude_tests: bool = True,
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
    from pycode_kg.ranking.coderank import (  # pylint: disable=import-outside-toplevel
        build_code_graph,
        compute_coderank,
        rank_query_hybrid,
        rank_query_ppr,
    )

    kg = _get_kg()
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
    except Exception as exc:  # pylint: disable=broad-except
        return json.dumps({"error": f"Seed retrieval failed: {exc}"}, indent=2)

    if not semantic_scores:
        return json.dumps({"error": "No semantic seeds found for query."}, indent=2)

    try:
        graph = build_code_graph(
            db_path,
            include_relations=rel_list,
            exclude_test_paths=exclude_tests,
        )
    except Exception as exc:  # pylint: disable=broad-except
        return json.dumps({"error": f"Graph build failed: {exc}"}, indent=2)

    global_cr = compute_coderank(graph)
    try:
        if mode == "ppr":
            results = rank_query_ppr(graph, semantic_scores, radius=radius, top_k=top)
        else:
            results = rank_query_hybrid(
                graph, semantic_scores, global_coderank=global_cr, radius=radius, top_k=top
            )
    except Exception as exc:  # pylint: disable=broad-except
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


@mcp.tool()
def explain_rank(node_id: str, q: str = "") -> str:
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
    from pycode_kg.ranking.coderank import (  # pylint: disable=import-outside-toplevel
        DEFAULT_GLOBAL_RELS,
        build_code_graph,
        compute_coderank,
        compute_seed_proximity,
    )

    kg = _get_kg()
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
    except Exception as exc:  # pylint: disable=broad-except
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
        except Exception as exc:  # pylint: disable=broad-except
            out.append(f"- Query scoring failed: `{exc}`")
        out.append("")

    out.append("---\n")
    out.append(
        "*Use `rank_nodes()` for global top-N ranking, or `query_ranked()` for query-conditioned ranking.*"
    )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Temporal snapshot tools
# ---------------------------------------------------------------------------


@mcp.tool()
def snapshot_list(limit: int = 10, branch: str = "") -> str:
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
    mgr = _get_snapshot_mgr()
    snapshots = mgr.list_snapshots(
        limit=limit if limit > 0 else None,
        branch=branch if branch else None,
    )
    for snap in snapshots:
        snap_metrics = snap.get("metrics", {})
        snap["freshness"] = _snapshot_freshness(snap_metrics.get("total_nodes", 0))
    return json.dumps(snapshots, indent=2, ensure_ascii=False)


@mcp.tool()
def snapshot_show(key: str = "latest") -> str:
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
    mgr = _get_snapshot_mgr()

    if key == "latest":
        entries = mgr.list_snapshots(limit=1)
        if not entries:
            return json.dumps({"error": "No snapshots found."})
        key = entries[0]["key"]

    snapshot = mgr.load_snapshot(key)
    if snapshot is None:
        return json.dumps({"error": f"Snapshot not found for key: {key!r}"})
    out = snapshot.to_dict()
    out["freshness"] = _snapshot_freshness(snapshot.metrics.total_nodes)
    return json.dumps(out, indent=2, ensure_ascii=False)


@mcp.tool()
def snapshot_diff(key_a: str, key_b: str) -> str:
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
    mgr = _get_snapshot_mgr()
    result = mgr.diff_snapshots(key_a, key_b)
    if "error" not in result:
        result["freshness"] = {
            "a": _snapshot_freshness(result.get("a", {}).get("metrics", {}).get("total_nodes", 0)),
            "b": _snapshot_freshness(result.get("b", {}).get("metrics", {}).get("total_nodes", 0)),
        }
    return json.dumps(result, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args(argv: list | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments for the PyCodeKG MCP server entry point.

    Centralizes runtime configuration for repository path, graph/index paths,
    embedder model selection, and transport wiring (stdio vs sse).

    :param argv: Argument list to parse; defaults to ``sys.argv[1:]`` when ``None``.
    :return: Parsed argument namespace.
    """
    p = argparse.ArgumentParser(
        prog="pycodekg-mcp",
        description="PyCodeKG MCP server — exposes codebase query tools to AI agents.",
    )
    p.add_argument(
        "--repo",
        default=".",
        help="Repository root directory (default: current directory)",
    )
    p.add_argument(
        "--db",
        default=".pycodekg/graph.sqlite",
        help="Path to the SQLite knowledge graph (default: .pycodekg/graph.sqlite)",
    )
    p.add_argument(
        "--lancedb",
        default=".pycodekg/lancedb",
        help="Path to the LanceDB vector index directory (default: .pycodekg/lancedb)",
    )
    p.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Sentence-transformer model name (default: {DEFAULT_MODEL})",
    )
    p.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport: stdio (default, for Claude Desktop) or sse (HTTP)",
    )
    return p.parse_args(argv)


def main(argv: list | None = None) -> None:
    """
    CLI entry point for the PyCodeKG MCP server.

    Initialises the PyCodeKG instance, the SnapshotManager, and starts the
    MCP server using the requested transport (stdio for Claude Desktop,
    sse for HTTP clients).

    This startup path is the operational "entry point and configuration"
    surface for MCP usage, including model selection and database/index
    location handling. It also provides warning output for common
    misconfiguration states (missing SQLite graph before startup).

    Logging approach: writes startup diagnostics and warnings to stderr so
    MCP hosts can capture them without mixing with tool payloads.
    Error handling strategy: emits actionable warnings for missing inputs
    and continues initialization when safe to do so.

    :param argv: Argument list forwarded to ``_parse_args``; defaults to
                 ``sys.argv[1:]`` when ``None``.
    """
    global _kg, _snapshot_mgr

    args = _parse_args(argv)

    repo = Path(args.repo).resolve()
    db = Path(args.db) if Path(args.db).is_absolute() else repo / args.db
    lancedb_dir = Path(args.lancedb) if Path(args.lancedb).is_absolute() else repo / args.lancedb

    if not db.exists():
        print(
            f"WARNING: SQLite database not found at '{db}'.\n"
            "Run 'pycodekg-build-sqlite' and 'pycodekg-build-lancedb' first.",
            file=sys.stderr,
        )

    print(
        f"PyCodeKG MCP server starting\n"
        f"  repo     : {repo}\n"
        f"  db       : {db}\n"
        f"  lancedb  : {lancedb_dir}\n"
        f"  model    : {args.model}\n"
        f"  transport: {args.transport}",
        file=sys.stderr,
    )

    _kg = PyCodeKG(
        repo_root=repo,
        db_path=db,
        lancedb_dir=lancedb_dir,
        model=args.model,
    )

    _snapshot_mgr = SnapshotManager(repo / ".pycodekg" / "snapshots", db_path=db)

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
