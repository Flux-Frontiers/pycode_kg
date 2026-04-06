"""CodeRank and hybrid ranking utilities for PyCodeKG.

This module implements:
- weighted global PageRank ("CodeRank")
- query-induced personalized PageRank
- hybrid score combination with semantic relevance and graph proximity
- explainable per-node score components

The implementation is designed to be repo-agnostic and easy to adapt to the
existing PyCodeKG SQLite schema.

Assumptions
-----------
- Nodes live in a ``nodes`` table with at least:
    id, kind, name, qualname, module_path
- Edges live in an ``edges`` table with at least:
    source_id, target_id, relation

Notes
-----
- Edge weights in this module represent *strength*.
- If you later compute shortest-path or betweenness centrality, convert these
  strengths to distances, e.g. distance = 1 / (weight + eps).
"""

from __future__ import annotations

import math
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

import networkx as nx

DEFAULT_EDGE_WEIGHTS: dict[str, float] = {
    "CALLS": 1.00,
    "IMPORTS": 0.90,
    "INHERITS": 0.75,
    "RESOLVES_TO": 0.30,
    "CONTAINS": 0.15,
    "ATTR_ACCESS": 0.10,
    "READS": 0.05,
    "WRITES": 0.05,
}

DEFAULT_KIND_PRIORS: dict[str, float] = {
    "function": 1.00,
    "method": 1.00,
    "class": 0.92,
    "module": 0.80,
    "symbol": 0.50,
    "attribute": 0.50,
}

DEFAULT_GLOBAL_RELS: tuple[str, ...] = (
    "CALLS",
    "IMPORTS",
    "INHERITS",
    "RESOLVES_TO",
)

DEFAULT_HYBRID_WEIGHTS: dict[str, float] = {
    "semantic": 0.60,
    "centrality": 0.25,
    "proximity": 0.15,
}


@dataclass(frozen=True)
class RankResult:
    """Final hybrid ranking result for one node."""

    node_id: str
    final_score: float
    semantic_score: float
    centrality_score: float
    proximity_score: float
    adjusted_score: float
    kind: str | None
    qualname: str | None
    module_path: str | None
    why: tuple[str, ...]


def _normalize_scores(scores: Mapping[str, float]) -> dict[str, float]:
    """Min-max normalize a score mapping into [0, 1].

    If all scores are equal, return 1.0 for positive entries and 0 otherwise.
    """
    if not scores:
        return {}

    values = list(scores.values())
    min_v = min(values)
    max_v = max(values)
    if math.isclose(min_v, max_v):
        return {k: (1.0 if v > 0 else 0.0) for k, v in scores.items()}

    scale = max_v - min_v
    return {k: (v - min_v) / scale for k, v in scores.items()}


def _safe_norm_sum(scores: Mapping[str, float]) -> dict[str, float]:
    """Normalize nonnegative scores to sum to 1.0."""
    total = sum(max(v, 0.0) for v in scores.values())
    if total <= 0:
        return {k: 0.0 for k in scores}
    return {k: max(v, 0.0) / total for k, v in scores.items()}


def build_code_graph(
    sqlite_path: str,
    *,
    include_relations: Iterable[str] | None = None,
    include_kinds: Iterable[str] | None = None,
    edge_weights: Mapping[str, float] | None = None,
    kind_priors: Mapping[str, float] | None = None,
    exclude_test_paths: bool = True,
) -> nx.DiGraph:
    """Build a weighted directed graph from the PyCodeKG SQLite store.

    :param sqlite_path: Path to the PyCodeKG SQLite database.
    :param include_relations: Optional subset of relations to include.
    :param include_kinds: Optional subset of node kinds to include.
    :param edge_weights: Edge strength per relation type.
    :param kind_priors: Multiplicative weight prior based on target node kind.
    :param exclude_test_paths: Exclude nodes whose module_path appears to be test code.
    :returns: A NetworkX DiGraph with edge attribute ``weight``.
    """
    relations = set(include_relations) if include_relations else None
    kinds = set(include_kinds) if include_kinds else None
    rel_weights = dict(DEFAULT_EDGE_WEIGHTS)
    if edge_weights:
        rel_weights.update(edge_weights)
    priors = dict(DEFAULT_KIND_PRIORS)
    if kind_priors:
        priors.update(kind_priors)

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    graph = nx.DiGraph()

    cur.execute(
        """
        SELECT id, kind, name, qualname, module_path
        FROM nodes
        """
    )
    for row in cur.fetchall():
        kind = row["kind"]
        module_path = row["module_path"]

        if kinds and kind not in kinds:
            continue
        if exclude_test_paths and module_path:
            lowered = module_path.lower()
            if (
                "/tests/" in lowered
                or lowered.startswith("tests/")
                or lowered.endswith("_test.py")
                or lowered.endswith("test_.py")
            ):
                continue

        graph.add_node(
            row["id"],
            kind=kind,
            name=row["name"],
            qualname=row["qualname"],
            module_path=module_path,
        )

    cur.execute(
        """
        SELECT src, dst, rel
        FROM edges
        """
    )
    for row in cur.fetchall():
        src = row["src"]
        dst = row["dst"]
        relation = row["rel"]

        if src not in graph or dst not in graph:
            continue
        if relations and relation not in relations:
            continue

        base_weight = rel_weights.get(relation, 0.0)
        if base_weight <= 0:
            continue

        target_kind = graph.nodes[dst].get("kind")
        weight = base_weight * priors.get(target_kind, 1.0)
        if weight <= 0:
            continue

        if graph.has_edge(src, dst):
            graph[src][dst]["weight"] += weight
            graph[src][dst]["relations"].add(relation)
        else:
            graph.add_edge(src, dst, weight=weight, relations={relation})

    conn.close()
    return graph


def compute_coderank(
    graph: nx.DiGraph,
    *,
    alpha: float = 0.85,
    max_iter: int = 200,
    tol: float = 1.0e-8,
) -> dict[str, float]:
    """Compute global weighted PageRank on the graph."""
    if graph.number_of_nodes() == 0:
        return {}
    return nx.pagerank(
        graph,
        alpha=alpha,
        weight="weight",
        max_iter=max_iter,
        tol=tol,
    )


def compute_personalized_coderank(
    graph: nx.DiGraph,
    seed_scores: Mapping[str, float],
    *,
    alpha: float = 0.85,
    max_iter: int = 200,
    tol: float = 1.0e-8,
) -> dict[str, float]:
    """Compute weighted personalized PageRank from seed nodes."""
    if graph.number_of_nodes() == 0:
        return {}

    personalization = {node_id: 0.0 for node_id in graph.nodes}
    for node_id, score in seed_scores.items():
        if node_id in personalization and score > 0:
            personalization[node_id] = float(score)

    personalization = _safe_norm_sum(personalization)
    if sum(personalization.values()) <= 0:
        return compute_coderank(graph, alpha=alpha, max_iter=max_iter, tol=tol)

    return nx.pagerank(
        graph,
        alpha=alpha,
        weight="weight",
        personalization=personalization,
        dangling=personalization,
        max_iter=max_iter,
        tol=tol,
    )


def induce_query_subgraph(
    graph: nx.DiGraph,
    seeds: Sequence[str],
    *,
    radius: int = 2,
    include_reverse: bool = True,
) -> nx.DiGraph:
    """Induce a local query subgraph around seed nodes.

    This collects nodes reachable within ``radius`` hops from the seed set.
    When ``include_reverse`` is true, both successors and predecessors are
    traversed so caller/importer context is included.
    """
    if not seeds:
        return graph.copy()

    frontier = {node for node in seeds if node in graph}
    visited = set(frontier)

    for _ in range(max(radius, 0)):
        next_frontier: set[str] = set()
        for node in frontier:
            next_frontier.update(graph.successors(node))
            if include_reverse:
                next_frontier.update(graph.predecessors(node))
        next_frontier.difference_update(visited)
        visited.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break

    return graph.subgraph(visited).copy()


def compute_seed_proximity(
    graph: nx.DiGraph,
    seeds: Sequence[str],
) -> dict[str, float]:
    """Compute simple inverse-distance proximity to the nearest seed."""
    if graph.number_of_nodes() == 0:
        return {}
    valid_seeds = [seed for seed in seeds if seed in graph]
    if not valid_seeds:
        return {node_id: 0.0 for node_id in graph.nodes}

    undirected = graph.to_undirected()
    best_distance: dict[str, int] = {}
    for seed in valid_seeds:
        lengths = nx.single_source_shortest_path_length(undirected, seed)
        for node_id, dist in lengths.items():
            current = best_distance.get(node_id)
            if current is None or dist < current:
                best_distance[node_id] = dist

    return {
        node_id: 1.0 / (1.0 + best_distance[node_id]) if node_id in best_distance else 0.0
        for node_id in graph.nodes
    }


def combine_hybrid_scores(
    graph: nx.DiGraph,
    semantic_scores: Mapping[str, float],
    centrality_scores: Mapping[str, float],
    proximity_scores: Mapping[str, float],
    *,
    weights: Mapping[str, float] | None = None,
    kind_priors: Mapping[str, float] | None = None,
    top_k: int | None = None,
) -> list[RankResult]:
    """Combine semantic, centrality, and proximity scores into a final ranking."""
    score_weights = dict(DEFAULT_HYBRID_WEIGHTS)
    if weights:
        score_weights.update(weights)

    semantic_norm = _normalize_scores(
        {node: semantic_scores.get(node, 0.0) for node in graph.nodes}
    )
    centrality_norm = _normalize_scores(
        {node: centrality_scores.get(node, 0.0) for node in graph.nodes}
    )
    proximity_norm = _normalize_scores(
        {node: proximity_scores.get(node, 0.0) for node in graph.nodes}
    )

    priors = dict(DEFAULT_KIND_PRIORS)
    if kind_priors:
        priors.update(kind_priors)

    results: list[RankResult] = []
    for node_id, attrs in graph.nodes(data=True):
        semantic = semantic_norm.get(node_id, 0.0)
        centrality = centrality_norm.get(node_id, 0.0)
        proximity = proximity_norm.get(node_id, 0.0)
        final = (
            score_weights["semantic"] * semantic
            + score_weights["centrality"] * centrality
            + score_weights["proximity"] * proximity
        )
        kind = attrs.get("kind")
        adjusted = final * priors.get(kind, 1.0)

        reasons = _build_why(
            graph=graph,
            node_id=node_id,
            semantic=semantic,
            centrality=centrality,
            proximity=proximity,
        )

        results.append(
            RankResult(
                node_id=node_id,
                final_score=final,
                semantic_score=semantic,
                centrality_score=centrality,
                proximity_score=proximity,
                adjusted_score=adjusted,
                kind=kind,
                qualname=attrs.get("qualname"),
                module_path=attrs.get("module_path"),
                why=reasons,
            )
        )

    results.sort(key=lambda item: item.adjusted_score, reverse=True)
    if top_k is not None:
        return results[:top_k]
    return results


def rank_query_hybrid(
    graph: nx.DiGraph,
    semantic_scores: Mapping[str, float],
    *,
    global_coderank: Mapping[str, float] | None = None,
    radius: int = 2,
    top_k: int = 25,
    weights: Mapping[str, float] | None = None,
) -> list[RankResult]:
    """Hybrid rank for a query using semantic scores + global centrality + proximity."""
    seeds = [node_id for node_id, score in semantic_scores.items() if score > 0]
    local_graph = induce_query_subgraph(graph, seeds, radius=radius, include_reverse=True)
    centrality = global_coderank or compute_coderank(local_graph)
    proximity = compute_seed_proximity(local_graph, seeds)
    local_semantic = {node_id: semantic_scores.get(node_id, 0.0) for node_id in local_graph.nodes}
    local_centrality = {node_id: centrality.get(node_id, 0.0) for node_id in local_graph.nodes}
    return combine_hybrid_scores(
        local_graph,
        local_semantic,
        local_centrality,
        proximity,
        weights=weights,
        top_k=top_k,
    )


def rank_query_ppr(
    graph: nx.DiGraph,
    semantic_scores: Mapping[str, float],
    *,
    radius: int = 2,
    top_k: int = 25,
    ppr_weight: float = 0.70,
    semantic_weight: float = 0.30,
) -> list[RankResult]:
    """Rank query results using personalized PageRank on a query-induced subgraph."""
    seeds = [node_id for node_id, score in semantic_scores.items() if score > 0]
    local_graph = induce_query_subgraph(graph, seeds, radius=radius, include_reverse=True)

    local_semantic = {node_id: semantic_scores.get(node_id, 0.0) for node_id in local_graph.nodes}
    ppr = compute_personalized_coderank(local_graph, local_semantic)
    ppr_norm = _normalize_scores(ppr)
    semantic_norm = _normalize_scores(local_semantic)
    proximity = compute_seed_proximity(local_graph, seeds)

    priors = DEFAULT_KIND_PRIORS
    results: list[RankResult] = []
    for node_id, attrs in local_graph.nodes(data=True):
        ppr_score = ppr_norm.get(node_id, 0.0)
        semantic_score = semantic_norm.get(node_id, 0.0)
        final = ppr_weight * ppr_score + semantic_weight * semantic_score
        adjusted = final * priors.get(attrs.get("kind"), 1.0)
        reasons = _build_why(
            graph=local_graph,
            node_id=node_id,
            semantic=semantic_score,
            centrality=ppr_score,
            proximity=proximity.get(node_id, 0.0),
            centrality_label="ppr",
        )
        results.append(
            RankResult(
                node_id=node_id,
                final_score=final,
                semantic_score=semantic_score,
                centrality_score=ppr_score,
                proximity_score=proximity.get(node_id, 0.0),
                adjusted_score=adjusted,
                kind=attrs.get("kind"),
                qualname=attrs.get("qualname"),
                module_path=attrs.get("module_path"),
                why=reasons,
            )
        )

    results.sort(key=lambda item: item.adjusted_score, reverse=True)
    return results[:top_k]


def persist_metric_scores(
    sqlite_path: str,
    metric: str,
    scores: Mapping[str, float],
) -> None:
    """Persist node-level metric scores into a ``node_metrics`` table."""
    now = datetime.now(UTC).isoformat()
    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS node_metrics (
            node_id TEXT NOT NULL,
            metric TEXT NOT NULL,
            score REAL NOT NULL,
            computed_at TEXT NOT NULL,
            PRIMARY KEY (node_id, metric)
        )
        """
    )
    cur.executemany(
        """
        INSERT INTO node_metrics (node_id, metric, score, computed_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(node_id, metric) DO UPDATE SET
            score = excluded.score,
            computed_at = excluded.computed_at
        """,
        [(node_id, metric, float(score), now) for node_id, score in scores.items()],
    )
    conn.commit()
    conn.close()


def _build_why(
    *,
    graph: nx.DiGraph,
    node_id: str,
    semantic: float,
    centrality: float,
    proximity: float,
    centrality_label: str = "centrality",
) -> tuple[str, ...]:
    """Generate an explainable summary for a node score."""
    messages: list[str] = []

    incoming = list(graph.in_edges(node_id, data=True))
    if incoming:
        callers = 0
        importers = 0
        inheritors = 0
        for _, _, data in incoming:
            relations = data.get("relations", set())
            callers += int("CALLS" in relations)
            importers += int("IMPORTS" in relations)
            inheritors += int("INHERITS" in relations)
        if callers:
            messages.append(f"called by {callers} upstream node(s)")
        if importers:
            messages.append(f"imported by {importers} upstream node(s)")
        if inheritors:
            messages.append(f"inherited by {inheritors} subclass node(s)")

    if semantic > 0.75:
        messages.append("strong semantic match to the query")
    elif semantic > 0.40:
        messages.append("moderate semantic match to the query")

    if centrality > 0.75:
        messages.append(f"high {centrality_label} within the ranked subgraph")
    elif centrality > 0.40:
        messages.append(f"moderate {centrality_label} within the ranked subgraph")

    if proximity >= 1.0:
        messages.append("direct semantic seed")
    elif proximity >= 0.5:
        messages.append("one hop from a semantic seed")
    elif proximity > 0:
        messages.append("within local query neighborhood")

    if not messages:
        messages.append("ranked by combined structural and semantic signals")

    return tuple(messages)
