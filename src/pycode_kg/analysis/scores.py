"""
Read persisted node-level metrics so renderers can encode them visually.

PyCodeKG computes structural importance in two places and writes both to
SQLite: :mod:`pycode_kg.analysis.centrality` fills ``centrality_scores`` and
:mod:`pycode_kg.ranking.coderank` fills ``node_metrics``.  Until now nothing
read either table back — node size and colour in both visualisers were driven
purely by node kind, so the ranking work never reached the screen.

This module closes that gap.  Both tables are already long-format and keyed by
``(node_id, metric)``, which is exactly the shape needed to offer a metric
selector, so no schema change is required.

Neither table is part of the base graph schema — each is created lazily by its
writer — so every function here treats a missing table, a missing database, or
an unknown metric as "no data" rather than an error.  Renderers degrade to
uniform sizing.

Typical use::

    metrics = available_metrics("graph.sqlite")
    scores = load_scores("graph.sqlite", metrics[0].metric)
    if scores:
        radius = scores.scaled(node_id, 0.4, 2.0, default=0.7)
        alpha = 0.35 + 0.65 * scores.percentile(node_id)
"""

from __future__ import annotations

import math
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

__all__ = [
    "METRIC_TABLES",
    "MetricRef",
    "ScoreSet",
    "Scaler",
    "available_metrics",
    "load_scores",
]

#: Tables scanned for metrics, in preference order.  ``centrality_scores`` is
#: first because its writer also records the parameters used.
METRIC_TABLES: Final[tuple[str, ...]] = ("centrality_scores", "node_metrics")

#: How a raw score is mapped onto a visual range.
Scaler = Literal["log", "linear", "rank"]

#: Guards ``log(0)`` when a metric's minimum equals one of its values.
_LOG_EPSILON: Final[float] = 1e-9


@dataclass(frozen=True)
class MetricRef:
    """A metric that exists in the database and can be loaded.

    :param metric: Metric name as stored, e.g. ``"sir_pagerank"``.
    :param table: Table the metric was found in.
    :param count: Number of nodes carrying a score for this metric.
    """

    metric: str
    table: str
    count: int

    @property
    def label(self) -> str:
        """Human-readable label for a selector widget.

        :return: The metric name with underscores replaced by spaces.
        """
        return self.metric.replace("_", " ")


@dataclass(frozen=True)
class ScoreSet:
    """Scores for one metric, with rank and percentile derived on load.

    Ranks are computed from the loaded scores rather than read from the
    ``rank`` column of ``centrality_scores``.  The stored rank reflects whatever
    set the writer ranked, which may have been filtered or truncated; deriving
    it here guarantees dense, consistent ranks over exactly the rows loaded, and
    means ``node_metrics`` (which has no rank column) behaves identically.

    :param metric: Metric name.
    :param table: Table the scores came from.
    :param scores: Mapping of node ID to raw score.
    :param ranks: Mapping of node ID to 1-based rank, 1 being most central.
    """

    metric: str
    table: str
    scores: Mapping[str, float]
    ranks: Mapping[str, int]

    def __len__(self) -> int:
        """Number of scored nodes.

        :return: Count of nodes carrying a score.
        """
        return len(self.scores)

    def __contains__(self, node_id: str) -> bool:
        """Whether *node_id* carries a score.

        :param node_id: Node ID to test.
        :return: ``True`` if scored.
        """
        return node_id in self.scores

    def score(self, node_id: str, default: float = 0.0) -> float:
        """Raw score for *node_id*.

        :param node_id: Node ID to look up.
        :param default: Returned when the node is unscored.
        :return: The stored score, or *default*.
        """
        return self.scores.get(node_id, default)

    def rank(self, node_id: str) -> int | None:
        """1-based rank for *node_id*, 1 being most central.

        :param node_id: Node ID to look up.
        :return: The rank, or ``None`` when the node is unscored.
        """
        return self.ranks.get(node_id)

    def percentile(self, node_id: str, default: float = 0.0) -> float:
        """Rank percentile in ``[0, 1]``, where ``1.0`` is the most central node.

        Percentile is preferred over the raw score for opacity because
        PageRank-style scores are heavily skewed — a linear map on raw values
        leaves almost every node at the bottom of the range.

        :param node_id: Node ID to look up.
        :param default: Returned when the node is unscored.
        :return: Percentile in ``[0, 1]``, or *default*.
        """
        rank = self.ranks.get(node_id)
        if rank is None:
            return default
        n = len(self.ranks)
        if n <= 1:
            return 1.0
        return (n - rank) / (n - 1)

    def scaled(
        self,
        node_id: str,
        lo: float,
        hi: float,
        *,
        scaler: Scaler = "rank",
        default: float | None = None,
    ) -> float:
        """Map *node_id*'s score onto the range ``[lo, hi]``.

        ``"rank"`` is the default because it is the only option that uses the
        full output range on real data.  Centrality scores are extremely
        top-heavy — on pycode_kg's own graph the median SIR score is 1.2x the
        minimum while the maximum is 58x it — and both alternatives handle that
        badly.  ``"linear"`` collapses three quarters of the nodes onto the
        floor; ``"log"`` overcorrects, because the single smallest value
        stretches the bottom of the range far enough to push the bulk to ~0.73
        of it.  Measured interquartile spread over an 8-42 px range was 1 px for
        ``"linear"``, 4 px for ``"log"`` and 8 px for ``"rank"``.

        The trade is that ``"rank"`` discards magnitude, implying visual
        difference between scores that are nearly identical.  That is acceptable
        for a node-link diagram, where size is a navigational affordance rather
        than a measurement — callers wanting faithful magnitude should pass
        ``"linear"`` and read exact values from the score itself.

        :param node_id: Node ID to look up.
        :param lo: Lower bound of the output range.
        :param hi: Upper bound of the output range.
        :param scaler: One of ``"rank"`` (default), ``"log"`` or ``"linear"``.
        :param default: Returned when the node is unscored.  When ``None``, the
            midpoint of ``[lo, hi]`` is used.
        :return: A value within ``[lo, hi]``.
        """
        if node_id not in self.scores:
            return (lo + hi) / 2.0 if default is None else default
        return lo + self._fraction(node_id, scaler) * (hi - lo)

    def _fraction(self, node_id: str, scaler: Scaler) -> float:
        """Position of *node_id* within the metric's spread, in ``[0, 1]``.

        :param node_id: Node ID to look up.
        :param scaler: Scaling strategy.
        :return: Fraction in ``[0, 1]``.
        """
        if scaler == "rank":
            return self.percentile(node_id)

        values = self.scores.values()
        lo_val, hi_val = min(values), max(values)
        if math.isclose(lo_val, hi_val):
            # A degenerate metric carries no information; sit at the midpoint
            # rather than pinning every node to one end of the range.
            return 0.5

        value = self.scores[node_id]
        if scaler == "log":
            shift = _LOG_EPSILON - lo_val
            span = math.log(hi_val + shift) - math.log(lo_val + shift)
            if span <= 0.0:
                return 0.5
            return (math.log(value + shift) - math.log(lo_val + shift)) / span
        return (value - lo_val) / (hi_val - lo_val)


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    """Whether *table* exists in the connected database.

    :param con: Open SQLite connection.
    :param table: Table name.
    :return: ``True`` when the table is present.
    """
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _connect(db_path: str | Path) -> sqlite3.Connection | None:
    """Open *db_path* read-only, or return ``None`` when it does not exist.

    A plain :func:`sqlite3.connect` would *create* a missing database, which
    would silently produce an empty graph rather than a clear "not built yet".

    :param db_path: Path to the graph database.
    :return: An open connection, or ``None``.
    """
    path = Path(db_path)
    if not path.is_file():
        return None
    try:
        return sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None


def available_metrics(db_path: str | Path) -> list[MetricRef]:
    """List every metric present in the database.

    Metrics are returned in table preference order (``centrality_scores`` before
    ``node_metrics``), then by descending coverage.  A metric name appearing in
    both tables yields two entries, distinguished by :attr:`MetricRef.table`.

    :param db_path: Path to the graph database.
    :return: Available metrics; empty when the database or both tables are
        absent.
    """
    con = _connect(db_path)
    if con is None:
        return []

    found: list[MetricRef] = []
    try:
        for table in METRIC_TABLES:
            if not _table_exists(con, table):
                continue
            rows = con.execute(
                f"SELECT metric, COUNT(*) FROM {table} GROUP BY metric"  # noqa: S608
            ).fetchall()
            found.extend(
                MetricRef(metric=metric, table=table, count=count)
                for metric, count in rows
                if count
            )
    except sqlite3.Error:
        return []
    finally:
        con.close()

    order = {table: i for i, table in enumerate(METRIC_TABLES)}
    found.sort(key=lambda ref: (order.get(ref.table, 99), -ref.count, ref.metric))
    return found


def load_scores(
    db_path: str | Path,
    metric: str,
    *,
    table: str | None = None,
) -> ScoreSet | None:
    """Load all scores for *metric*.

    :param db_path: Path to the graph database.
    :param metric: Metric name to load.
    :param table: Restrict the lookup to one table.  When ``None``, the tables
        in :data:`METRIC_TABLES` are tried in order and the first with rows for
        *metric* wins.
    :return: A :class:`ScoreSet`, or ``None`` when the metric is not present.
    """
    con = _connect(db_path)
    if con is None:
        return None

    tables = (table,) if table else METRIC_TABLES
    try:
        for name in tables:
            if name is None or not _table_exists(con, name):
                continue
            rows = con.execute(
                f"SELECT node_id, score FROM {name} WHERE metric = ?",  # noqa: S608
                (metric,),
            ).fetchall()
            if not rows:
                continue
            scores = {node_id: float(score) for node_id, score in rows}
            ranks = {
                node_id: i
                for i, (node_id, _) in enumerate(
                    sorted(scores.items(), key=lambda kv: (-kv[1], kv[0])), start=1
                )
            }
            return ScoreSet(metric=metric, table=name, scores=scores, ranks=ranks)
    except sqlite3.Error:
        return None
    finally:
        con.close()

    return None
