"""Tests for Structural Importance Ranking."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from code_kg.analysis.centrality import StructuralImportanceRanker, aggregate_module_scores

SCHEMA = """
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    qualname TEXT,
    module_path TEXT,
    lineno INTEGER,
    end_lineno INTEGER,
    docstring TEXT
);
CREATE TABLE edges (
    src TEXT NOT NULL,
    rel TEXT NOT NULL,
    dst TEXT NOT NULL,
    evidence TEXT,
    PRIMARY KEY (src, rel, dst)
);
"""


def _make_db(path: Path) -> Path:
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.executemany(
        "INSERT INTO nodes (id, kind, name, qualname, module_path, lineno, end_lineno, docstring) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("fn:a:f1", "function", "f1", "f1", "a.py", 1, 2, None),
            ("fn:b:f2", "function", "f2", "f2", "b.py", 1, 2, None),
            ("fn:c:core", "function", "core", "core", "core.py", 1, 2, None),
            ("sym:core", "symbol", "core", "core", "b.py", 1, 1, None),
            ("mod:core", "module", "core", "core", "core.py", 1, 100, None),
        ],
    )
    con.executemany(
        "INSERT INTO edges (src, rel, dst, evidence) VALUES (?, ?, ?, ?)",
        [
            ("fn:a:f1", "CALLS", "fn:c:core", None),
            ("fn:b:f2", "CALLS", "sym:core", None),
            ("sym:core", "RESOLVES_TO", "fn:c:core", None),
            ("mod:core", "CONTAINS", "fn:c:core", None),
        ],
    )
    con.commit()
    con.close()
    return path


def test_sir_resolves_symbol_edges(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "graph.sqlite")
    ranker = StructuralImportanceRanker(db)
    records = ranker.compute()
    top = records[0]
    assert top.node_id == "fn:c:core"
    assert top.inbound_count >= 2


def test_module_aggregation(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "graph.sqlite")
    ranker = StructuralImportanceRanker(db)
    records = ranker.compute()
    modules = aggregate_module_scores(records)
    assert modules[0]["module_path"] == "core.py"
