#!/usr/bin/env python3
"""Structural centrality analysis for CodeKG.

Implements Structural Importance Ranking (SIR): a deterministic weighted
PageRank over the sym-stub-resolved CodeKG graph.  Edge weights are tuned
per relation type (CALLS > INHERITS > IMPORTS > CONTAINS) and amplified for
cross-module links, giving a stable, interpretable importance score for every
module, class, function, and method in the indexed codebase.

Public API:
    - :class:`StructuralImportanceRanker` — compute and persist SIR scores.
    - :func:`aggregate_module_scores` — roll node scores up to module level.

Author: Eric G. Suchanek, PhD
Last Revision: 2026-03-11 12:45:30
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_ALLOWED_KINDS = {"module", "class", "function", "method"}
_STRUCTURAL_RELS = ("CALLS", "INHERITS", "IMPORTS", "CONTAINS")


@dataclass(slots=True)
class CentralityConfig:
    """Configuration for Structural Importance Ranking.

    :param damping: PageRank damping factor.
    :param max_iter: Maximum PageRank iterations.
    :param tol: Convergence tolerance.
    :param rel_weights: Per-relation weights.
    :param cross_module_boost: Weight multiplier for cross-module edges.
    :param private_penalty: Multiplier for private symbols.
    """

    damping: float = 0.85
    max_iter: int = 100
    tol: float = 1e-10
    rel_weights: dict[str, float] = field(
        default_factory=lambda: {
            "CALLS": 1.0,
            "INHERITS": 0.8,
            "IMPORTS": 0.45,
            "CONTAINS": 0.15,
        }
    )
    cross_module_boost: float = 1.5
    private_penalty: float = 0.85


@dataclass(slots=True)
class CentralityRecord:
    """Centrality result for a single node.

    :param node_id: Stable node identifier.
    :param kind: CodeKG node kind.
    :param name: Node name.
    :param module_path: Module path from the store.
    :param score: Final importance score.
    :param rank: Rank among all returned nodes.
    :param inbound_count: Number of inbound effective edges.
    :param cross_module_inbound: Number of inbound cross-module edges.
    :param rel_breakdown: Inbound counts by relation type.
    :param top_contributors: Top inbound contributor summaries.
    """

    node_id: str
    kind: str
    name: str
    module_path: str | None
    score: float
    rank: int
    inbound_count: int
    cross_module_inbound: int
    rel_breakdown: dict[str, int]
    top_contributors: list[dict[str, Any]]


@dataclass(slots=True)
class _NodeInfo:
    node_id: str
    kind: str
    name: str
    module_path: str | None


@dataclass(slots=True)
class _EffectiveEdge:
    src: str
    dst: str
    rel: str
    weight: float
    same_module: bool


class StructuralImportanceRanker:
    """Compute Structural Importance Ranking (SIR) for a CodeKG SQLite database.

    Loads all real nodes (excluding sym-stub intermediates) and structural
    edges, resolves cross-module symbol stubs, then runs a weighted PageRank
    where each relation type contributes a distinct edge weight and
    cross-module edges receive an additional boost.  Private symbols are
    penalized post-convergence.  Scores are normalized to sum to 1.0.
    """

    def __init__(self, db_path: str | Path, config: CentralityConfig | None = None) -> None:
        self.db_path = Path(db_path)
        self.config = config or CentralityConfig()

    def compute(
        self,
        *,
        kinds: set[str] | None = None,
        top: int | None = None,
    ) -> list[CentralityRecord]:
        """Compute SIR scores for all nodes in the graph.

        :param kinds: Restrict results to a subset of node kinds
            (``'module'``, ``'class'``, ``'function'``, ``'method'``).
            When ``None``, all kinds are returned.
        :param top: Cap the number of returned records after filtering.
        :return: Records sorted descending by normalized importance score,
            each annotated with rank, inbound-edge counts, and top
            contributing callers.
        """
        node_map = self._load_nodes()
        effective_edges = self._load_effective_edges(node_map)
        scores = self._pagerank(node_map, effective_edges)
        records = self._assemble_records(node_map, effective_edges, scores)

        if kinds:
            records = [r for r in records if r.kind in kinds]
        if top is not None:
            records = records[:top]
        return records

    def write_scores(
        self,
        records: list[CentralityRecord],
        *,
        metric: str = "sir_pagerank",
    ) -> int:
        """Persist SIR scores into the ``centrality_scores`` table.

        Upserts on ``(node_id, metric)`` so repeated runs overwrite stale
        scores without accumulating duplicate rows.

        :param records: Ranked records from :meth:`compute`.
        :param metric: Label for the metric column (default ``'sir_pagerank'``).
        :return: Number of rows written.
        """
        rows = []
        computed_at = datetime.now(UTC).isoformat()
        params = json.dumps(
            {
                "damping": self.config.damping,
                "max_iter": self.config.max_iter,
                "tol": self.config.tol,
                "rel_weights": self.config.rel_weights,
                "cross_module_boost": self.config.cross_module_boost,
                "private_penalty": self.config.private_penalty,
            },
            sort_keys=True,
        )
        for rec in records:
            rows.append((rec.node_id, metric, rec.score, rec.rank, computed_at, params))

        with sqlite3.connect(self.db_path) as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS centrality_scores (
                    node_id TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    score REAL NOT NULL,
                    rank INTEGER,
                    computed_at TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    PRIMARY KEY (node_id, metric)
                )
                """
            )
            con.executemany(
                """
                INSERT INTO centrality_scores
                    (node_id, metric, score, rank, computed_at, params_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(node_id, metric) DO UPDATE SET
                    score = excluded.score,
                    rank = excluded.rank,
                    computed_at = excluded.computed_at,
                    params_json = excluded.params_json
                """,
                rows,
            )
            con.commit()
        return len(rows)

    def _load_nodes(self) -> dict[str, _NodeInfo]:
        with sqlite3.connect(self.db_path) as con:
            rows = con.execute(
                """
                SELECT id, kind, name, module_path
                FROM nodes
                WHERE kind IN ('module', 'class', 'function', 'method')
                """
            ).fetchall()
        return {
            row[0]: _NodeInfo(node_id=row[0], kind=row[1], name=row[2], module_path=row[3])
            for row in rows
        }

    def _load_effective_edges(
        self,
        node_map: dict[str, _NodeInfo],
    ) -> list[_EffectiveEdge]:
        with sqlite3.connect(self.db_path) as con:
            structural = con.execute(
                """
                SELECT src, rel, dst
                FROM edges
                WHERE rel IN ('CALLS', 'INHERITS', 'IMPORTS', 'CONTAINS')
                """
            ).fetchall()
            resolves = con.execute(
                """
                SELECT src, dst
                FROM edges
                WHERE rel = 'RESOLVES_TO'
                """
            ).fetchall()

        resolve_map: dict[str, list[str]] = defaultdict(list)
        for sym_id, dst in resolves:
            if dst in node_map:
                resolve_map[sym_id].append(dst)

        dedup: set[tuple[str, str, str]] = set()
        effective: list[_EffectiveEdge] = []

        for src, rel, dst in structural:
            if src not in node_map:
                continue
            targets: list[str]
            if dst in node_map:
                targets = [dst]
            else:
                targets = resolve_map.get(dst, [])
            for target in targets:
                if target not in node_map:
                    continue
                key = (src, rel, target)
                if key in dedup:
                    continue
                dedup.add(key)
                weight = float(self.config.rel_weights[rel])
                same_module = node_map[src].module_path == node_map[target].module_path
                if not same_module:
                    weight *= self.config.cross_module_boost
                effective.append(
                    _EffectiveEdge(
                        src=src,
                        dst=target,
                        rel=rel,
                        weight=weight,
                        same_module=same_module,
                    )
                )
        return effective

    def _pagerank(
        self,
        node_map: dict[str, _NodeInfo],
        effective_edges: list[_EffectiveEdge],
    ) -> dict[str, float]:
        nodes = list(node_map)
        n = len(nodes)
        if n == 0:
            return {}

        out_weight: dict[str, float] = defaultdict(float)
        incoming: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for edge in effective_edges:
            out_weight[edge.src] += edge.weight
            incoming[edge.dst].append((edge.src, edge.weight))

        pr = {node_id: 1.0 / n for node_id in nodes}
        damping = self.config.damping

        for _ in range(self.config.max_iter):
            base = (1.0 - damping) / n
            dangling_mass = sum(pr[node_id] for node_id in nodes if out_weight[node_id] == 0.0)
            dangling_share = damping * dangling_mass / n
            new_pr: dict[str, float] = {}
            delta = 0.0

            for node_id in nodes:
                score = base + dangling_share
                for src, weight in incoming.get(node_id, []):
                    denom = out_weight[src]
                    if denom > 0.0:
                        score += damping * pr[src] * (weight / denom)
                new_pr[node_id] = score
                delta += abs(score - pr[node_id])

            pr = new_pr
            if delta < self.config.tol:
                break

        for node_id, info in node_map.items():
            if info.name.startswith("_"):
                pr[node_id] *= self.config.private_penalty

        total = sum(pr.values())
        if total > 0.0:
            pr = {node_id: score / total for node_id, score in pr.items()}
        return pr

    def _assemble_records(
        self,
        node_map: dict[str, _NodeInfo],
        effective_edges: list[_EffectiveEdge],
        scores: dict[str, float],
    ) -> list[CentralityRecord]:
        inbound_counts: dict[str, int] = defaultdict(int)
        cross_counts: dict[str, int] = defaultdict(int)
        rel_breakdown: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        out_weight: dict[str, float] = defaultdict(float)
        incoming_edges: dict[str, list[_EffectiveEdge]] = defaultdict(list)

        for edge in effective_edges:
            out_weight[edge.src] += edge.weight
            inbound_counts[edge.dst] += 1
            rel_breakdown[edge.dst][edge.rel] += 1
            if not edge.same_module:
                cross_counts[edge.dst] += 1
            incoming_edges[edge.dst].append(edge)

        ranked_ids = sorted(scores, key=lambda node_id: scores[node_id], reverse=True)
        records: list[CentralityRecord] = []
        for rank, node_id in enumerate(ranked_ids, start=1):
            info = node_map[node_id]
            contributors: list[dict[str, Any]] = []
            for edge in incoming_edges.get(node_id, []):
                denom = out_weight[edge.src]
                contrib = 0.0 if denom == 0.0 else scores[edge.src] * (edge.weight / denom)
                src_info = node_map.get(edge.src)
                contributors.append(
                    {
                        "src": edge.src,
                        "src_name": src_info.name if src_info else edge.src,
                        "rel": edge.rel,
                        "same_module": edge.same_module,
                        "contribution": contrib,
                    }
                )
            contributors.sort(key=lambda item: item["contribution"], reverse=True)
            records.append(
                CentralityRecord(
                    node_id=node_id,
                    kind=info.kind,
                    name=info.name,
                    module_path=info.module_path,
                    score=scores[node_id],
                    rank=rank,
                    inbound_count=inbound_counts[node_id],
                    cross_module_inbound=cross_counts[node_id],
                    rel_breakdown=dict(sorted(rel_breakdown[node_id].items())),
                    top_contributors=contributors[:5],
                )
            )
        return records


def aggregate_module_scores(records: list[CentralityRecord]) -> list[dict[str, Any]]:
    """Roll up node-level SIR scores into per-module totals.

    Each node's score is weighted by kind (class × 1.2, all others × 1.0)
    before accumulation, so modules that export important classes rank
    higher than those containing only utility functions of similar raw score.

    :param records: Node-level centrality records from
        :meth:`StructuralImportanceRanker.compute`.
    :return: List of ``{module_path, score, rank, member_count}`` dicts,
        sorted descending by aggregated score.
    """
    kind_weight = {"function": 1.0, "method": 1.0, "class": 1.2, "module": 1.0}
    totals: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)

    for rec in records:
        module_key = rec.module_path or "<unknown>"
        totals[module_key] += rec.score * kind_weight.get(rec.kind, 1.0)
        counts[module_key] += 1

    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    return [
        {
            "module_path": module_path,
            "score": score,
            "rank": rank,
            "member_count": counts[module_path],
        }
        for rank, (module_path, score) in enumerate(ranked, start=1)
    ]
