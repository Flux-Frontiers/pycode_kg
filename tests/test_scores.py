"""
test_scores.py

Guards the ``pycode_kg.analysis`` compatibility shim.

The implementation moved to :mod:`kg_utils.analysis.scores` when it was promoted
for sharing with doc_kg and gutenberg_kg, and its behavioural tests moved with
it. What is left here is the re-export: existing callers import these names from
``pycode_kg.analysis``, and that must keep working without them knowing the
module changed address.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from pycode_kg.analysis import MetricRef, ScoreSet, available_metrics, load_scores


def test_names_are_re_exported() -> None:
    """The shim exposes exactly what callers were importing before the move."""
    from pycode_kg import analysis

    for name in ("MetricRef", "ScoreSet", "available_metrics", "load_scores"):
        assert name in analysis.__all__
        assert hasattr(analysis, name)


def test_re_exports_are_the_promoted_objects() -> None:
    """The shim must forward, not shadow with a divergent copy."""
    from kg_utils.analysis import scores as promoted

    assert ScoreSet is promoted.ScoreSet
    assert MetricRef is promoted.MetricRef
    assert load_scores is promoted.load_scores
    assert available_metrics is promoted.available_metrics


def test_shim_works_end_to_end(tmp_path: Path) -> None:
    """A round trip through the shim behaves as it did before the move.

    One live check rather than a duplicate of the promoted module's suite:
    enough to catch a broken re-export, without testing code this repo no
    longer owns.
    """
    db = tmp_path / "graph.sqlite"
    con = sqlite3.connect(db)
    con.execute(
        """
        CREATE TABLE centrality_scores (
            node_id TEXT NOT NULL, metric TEXT NOT NULL, score REAL NOT NULL,
            rank INTEGER, computed_at TEXT NOT NULL, params_json TEXT NOT NULL,
            PRIMARY KEY (node_id, metric)
        )
        """
    )
    con.executemany(
        "INSERT INTO centrality_scores VALUES (?, 'sir_pagerank', ?, ?, '2026-01-01', '{}')",
        [("fn:hot", 0.9, 1), ("fn:cold", 0.1, 2)],
    )
    con.commit()
    con.close()

    assert available_metrics(db) == [
        MetricRef(metric="sir_pagerank", table="centrality_scores", count=2)
    ]
    scores = load_scores(db, "sir_pagerank")
    assert scores is not None
    assert scores.rank("fn:hot") == 1
    assert scores.percentile("fn:hot") == pytest.approx(1.0)


def test_absent_database_still_degrades_quietly(tmp_path: Path) -> None:
    """The renderers call these on every draw, so absence must not raise."""
    missing = tmp_path / "nope.sqlite"
    assert available_metrics(missing) == []
    assert load_scores(missing, "sir_pagerank") is None
