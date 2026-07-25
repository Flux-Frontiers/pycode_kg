"""
test_scores.py

Tests for :mod:`pycode_kg.analysis.scores` — reading persisted centrality
metrics back out of SQLite for visual encoding.

The behaviour that matters most here is graceful degradation.  Neither
``centrality_scores`` nor ``node_metrics`` belongs to the base graph schema;
each is created lazily by its writer, so a perfectly healthy database may have
neither.  Every entry point must treat that as "no data" rather than raising,
because the visualisers call these on every render.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from pycode_kg.analysis.scores import (
    METRIC_TABLES,
    MetricRef,
    ScoreSet,
    available_metrics,
    load_scores,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_centrality(db: Path, rows: list[tuple[str, str, float, int]]) -> None:
    """Create ``centrality_scores`` and insert *rows*.

    :param db: Database path.
    :param rows: Tuples of ``(node_id, metric, score, rank)``.
    """
    con = sqlite3.connect(db)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS centrality_scores (
            node_id TEXT NOT NULL, metric TEXT NOT NULL, score REAL NOT NULL,
            rank INTEGER, computed_at TEXT NOT NULL, params_json TEXT NOT NULL,
            PRIMARY KEY (node_id, metric)
        )
        """
    )
    con.executemany(
        "INSERT INTO centrality_scores VALUES (?, ?, ?, ?, '2026-01-01', '{}')",
        rows,
    )
    con.commit()
    con.close()


def _write_node_metrics(db: Path, rows: list[tuple[str, str, float]]) -> None:
    """Create ``node_metrics`` and insert *rows*.

    :param db: Database path.
    :param rows: Tuples of ``(node_id, metric, score)``.
    """
    con = sqlite3.connect(db)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS node_metrics (
            node_id TEXT NOT NULL, metric TEXT NOT NULL, score REAL NOT NULL,
            computed_at TEXT NOT NULL, PRIMARY KEY (node_id, metric)
        )
        """
    )
    con.executemany("INSERT INTO node_metrics VALUES (?, ?, ?, '2026-01-01')", rows)
    con.commit()
    con.close()


@pytest.fixture
def db(tmp_path: Path) -> Path:
    """A graph database carrying SIR scores in ``centrality_scores``.

    :param tmp_path: pytest temporary directory.
    :return: Path to the database.
    """
    path = tmp_path / "graph.sqlite"
    _write_centrality(
        path,
        [
            ("fn:a.py:alpha", "sir_pagerank", 0.40, 1),
            ("fn:a.py:beta", "sir_pagerank", 0.20, 2),
            ("fn:a.py:gamma", "sir_pagerank", 0.10, 3),
            ("fn:a.py:delta", "sir_pagerank", 0.05, 4),
        ],
    )
    return path


# ---------------------------------------------------------------------------
# Degradation — the visualisers depend on these never raising
# ---------------------------------------------------------------------------


def test_missing_database_yields_no_metrics(tmp_path: Path) -> None:
    """A nonexistent path returns empty rather than raising."""
    missing = tmp_path / "nope.sqlite"
    assert available_metrics(missing) == []
    assert load_scores(missing, "sir_pagerank") is None


def test_missing_database_is_not_created(tmp_path: Path) -> None:
    """Reading must not bring an empty database into existence.

    ``sqlite3.connect`` creates missing files, which would turn "not built yet"
    into a silently empty graph.
    """
    missing = tmp_path / "nope.sqlite"
    available_metrics(missing)
    load_scores(missing, "sir_pagerank")
    assert not missing.exists()


def test_database_without_metric_tables(tmp_path: Path) -> None:
    """A graph built but never analysed has neither table."""
    path = tmp_path / "graph.sqlite"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE nodes (id TEXT PRIMARY KEY)")
    con.commit()
    con.close()

    assert available_metrics(path) == []
    assert load_scores(path, "sir_pagerank") is None


def test_unknown_metric_returns_none(db: Path) -> None:
    """Asking for a metric that was never computed yields ``None``."""
    assert load_scores(db, "betweenness") is None


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def test_available_metrics_finds_centrality_scores(db: Path) -> None:
    """Metrics in ``centrality_scores`` are discovered with their coverage."""
    metrics = available_metrics(db)
    assert metrics == [MetricRef(metric="sir_pagerank", table="centrality_scores", count=4)]


def test_available_metrics_spans_both_tables(db: Path) -> None:
    """Both tables are scanned, ``centrality_scores`` ordered first."""
    _write_node_metrics(db, [("fn:a.py:alpha", "coderank", 0.9)])
    metrics = available_metrics(db)

    assert [m.table for m in metrics] == ["centrality_scores", "node_metrics"]
    assert [m.metric for m in metrics] == ["sir_pagerank", "coderank"]


def test_metric_ref_label_is_readable(db: Path) -> None:
    """Underscored metric names become selector-friendly labels."""
    assert available_metrics(db)[0].label == "sir pagerank"


def test_table_preference_order_is_declared() -> None:
    """``centrality_scores`` outranks ``node_metrics``."""
    assert METRIC_TABLES == ("centrality_scores", "node_metrics")


# ---------------------------------------------------------------------------
# Loading and ranking
# ---------------------------------------------------------------------------


def test_load_scores_reads_all_rows(db: Path) -> None:
    """Every scored node is loaded with its raw score."""
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None
    assert len(scores) == 4
    assert scores.score("fn:a.py:alpha") == pytest.approx(0.40)
    assert "fn:a.py:alpha" in scores


def test_ranks_are_derived_densely(db: Path) -> None:
    """Ranks run 1..n over the loaded rows, 1 being most central."""
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None
    assert scores.rank("fn:a.py:alpha") == 1
    assert scores.rank("fn:a.py:delta") == 4


def test_ranks_ignore_the_stored_rank_column(tmp_path: Path) -> None:
    """Stored ranks may reflect a filtered set, so they are recomputed.

    Here the writer persisted ranks 7 and 9 from some larger ranking; loading
    two rows must renumber them densely as 1 and 2.
    """
    path = tmp_path / "graph.sqlite"
    _write_centrality(
        path,
        [("fn:a.py:x", "sir_pagerank", 0.9, 7), ("fn:a.py:y", "sir_pagerank", 0.1, 9)],
    )
    scores = load_scores(path, "sir_pagerank")
    assert scores is not None
    assert scores.rank("fn:a.py:x") == 1
    assert scores.rank("fn:a.py:y") == 2


def test_ranking_ties_break_deterministically(tmp_path: Path) -> None:
    """Equal scores rank by node ID so renders are reproducible."""
    path = tmp_path / "graph.sqlite"
    _write_centrality(
        path,
        [("fn:b", "m", 0.5, 1), ("fn:a", "m", 0.5, 2), ("fn:c", "m", 0.5, 3)],
    )
    scores = load_scores(path, "m")
    assert scores is not None
    assert [scores.rank(n) for n in ("fn:a", "fn:b", "fn:c")] == [1, 2, 3]


def test_explicit_table_restricts_lookup(db: Path) -> None:
    """A metric absent from the named table is not found elsewhere."""
    _write_node_metrics(db, [("fn:a.py:alpha", "coderank", 0.9)])
    assert load_scores(db, "coderank", table="centrality_scores") is None
    assert load_scores(db, "coderank", table="node_metrics") is not None


# ---------------------------------------------------------------------------
# Percentile
# ---------------------------------------------------------------------------


def test_percentile_spans_the_full_range(db: Path) -> None:
    """The top node is 1.0 and the bottom node is 0.0."""
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None
    assert scores.percentile("fn:a.py:alpha") == pytest.approx(1.0)
    assert scores.percentile("fn:a.py:delta") == pytest.approx(0.0)
    assert scores.percentile("fn:a.py:beta") == pytest.approx(2 / 3)


def test_percentile_of_unscored_node_uses_default(db: Path) -> None:
    """Unscored nodes fall back rather than raising."""
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None
    assert scores.percentile("fn:a.py:missing") == 0.0
    assert scores.percentile("fn:a.py:missing", default=0.5) == 0.5
    assert scores.rank("fn:a.py:missing") is None


def test_percentile_of_single_node_is_top(tmp_path: Path) -> None:
    """A one-node metric must not divide by zero."""
    path = tmp_path / "graph.sqlite"
    _write_centrality(path, [("fn:only", "m", 0.5, 1)])
    scores = load_scores(path, "m")
    assert scores is not None
    assert scores.percentile("fn:only") == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Scaling
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scaler", ["log", "linear", "rank"])
def test_scaled_stays_within_bounds(db: Path, scaler: str) -> None:
    """Every scaler maps into the requested range, endpoints included."""
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None
    values = [
        scores.scaled(n, 0.4, 2.0, scaler=scaler)  # type: ignore[arg-type]
        for n in scores.scores
    ]
    assert all(0.4 <= v <= 2.0 for v in values)
    assert max(values) == pytest.approx(2.0)
    assert min(values) == pytest.approx(0.4)


@pytest.mark.parametrize("scaler", ["log", "linear", "rank"])
def test_scaled_preserves_ordering(db: Path, scaler: str) -> None:
    """A more central node is never drawn smaller than a less central one."""
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None
    ordered = sorted(scores.scores, key=lambda n: scores.rank(n) or 0)
    sizes = [
        scores.scaled(n, 0.4, 2.0, scaler=scaler)  # type: ignore[arg-type]
        for n in ordered
    ]
    assert sizes == sorted(sizes, reverse=True)


def test_rank_is_the_default_scaler(db: Path) -> None:
    """The default must be ``rank`` — the renderers rely on it.

    Centrality scores are extremely top-heavy, and rank is the only scaler that
    spreads them across the output range rather than bunching them at one end.
    """
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None
    for node in scores.scores:
        assert scores.scaled(node, 8, 42) == scores.scaled(node, 8, 42, scaler="rank")


def test_rank_discriminates_better_than_log_or_linear(db: Path) -> None:
    """Rank spreads a top-heavy metric more evenly than the alternatives.

    This is the measured justification for the default: on a skewed
    distribution, linear pins most nodes to the floor and log pushes most of
    them to the ceiling, while rank uses the whole range.
    """
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None

    def spread(scaler: str) -> float:
        sizes = sorted(
            scores.scaled(n, 8, 42, scaler=scaler)  # type: ignore[arg-type]
            for n in scores.scores
        )
        mid = len(sizes) // 2
        return sizes[-1] - sizes[mid]  # distance from median to top

    assert spread("rank") > spread("log")


def test_log_scaler_lifts_the_skewed_tail(db: Path) -> None:
    """Log scaling separates small values that linear scaling flattens.

    This is the whole reason ``"log"`` is the default: PageRank-family scores
    span orders of magnitude, and a linear map leaves the tail indistinguishable.
    """
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None
    node = "fn:a.py:gamma"
    assert scores.scaled(node, 0.0, 1.0, scaler="log") > scores.scaled(
        node, 0.0, 1.0, scaler="linear"
    )


def test_scaled_unscored_node_defaults_to_midpoint(db: Path) -> None:
    """Unscored nodes sit mid-range unless told otherwise."""
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None
    assert scores.scaled("fn:a.py:missing", 0.0, 2.0) == pytest.approx(1.0)
    assert scores.scaled("fn:a.py:missing", 0.0, 2.0, default=0.7) == pytest.approx(0.7)


def test_degenerate_metric_sits_mid_range(tmp_path: Path) -> None:
    """When every score is identical, nothing should be pinned to an extreme."""
    path = tmp_path / "graph.sqlite"
    _write_centrality(path, [("fn:a", "m", 0.3, 1), ("fn:b", "m", 0.3, 2), ("fn:c", "m", 0.3, 3)])
    scores = load_scores(path, "m")
    assert scores is not None
    for node in ("fn:a", "fn:b", "fn:c"):
        assert scores.scaled(node, 0.0, 2.0, scaler="log") == pytest.approx(1.0)
        assert scores.scaled(node, 0.0, 2.0, scaler="linear") == pytest.approx(1.0)


def test_zero_and_negative_scores_are_handled(tmp_path: Path) -> None:
    """Log scaling must survive metrics that are not strictly positive."""
    path = tmp_path / "graph.sqlite"
    _write_centrality(path, [("fn:a", "m", -1.0, 1), ("fn:b", "m", 0.0, 2), ("fn:c", "m", 4.0, 3)])
    scores = load_scores(path, "m")
    assert scores is not None
    values = [scores.scaled(n, 1.0, 5.0, scaler="log") for n in ("fn:a", "fn:b", "fn:c")]
    assert all(1.0 <= v <= 5.0 for v in values)
    assert values == sorted(values)


def test_scoreset_is_constructible_directly() -> None:
    """The dataclass is usable without a database, for callers that already have scores."""
    scores = ScoreSet(metric="m", table="centrality_scores", scores={"a": 1.0}, ranks={"a": 1})
    assert len(scores) == 1
    assert scores.percentile("a") == pytest.approx(1.0)
