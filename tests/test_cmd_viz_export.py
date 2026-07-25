"""
test_cmd_viz_export.py

Tests for the ``pycodekg viz-export`` command.

Its reason to exist is that seeing a 2-D graph previously required running the
Streamlit app: the builder lived inside ``app.py``, which calls
``st.set_page_config`` at import time. These tests therefore care most that the
command produces a usable file from a plain database, with no server and no
Streamlit installed.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

pytest.importorskip("pyvis")

from click.testing import CliRunner  # noqa: E402

from pycode_kg.cli.cmd_viz import cli  # noqa: E402


@pytest.fixture
def graph_db(tmp_path: Path) -> Path:
    """A small graph with centrality scores, as the analysis pipeline leaves it.

    :param tmp_path: pytest temporary directory.
    :return: Path to the database.
    """
    path = tmp_path / "graph.sqlite"
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE nodes (
          id TEXT PRIMARY KEY, kind TEXT NOT NULL, name TEXT NOT NULL,
          qualname TEXT, module_path TEXT, lineno INTEGER, end_lineno INTEGER,
          docstring TEXT
        );
        CREATE TABLE edges (
          src TEXT NOT NULL, rel TEXT NOT NULL, dst TEXT NOT NULL, evidence TEXT,
          PRIMARY KEY (src, rel, dst)
        );
        CREATE TABLE centrality_scores (
          node_id TEXT NOT NULL, metric TEXT NOT NULL, score REAL NOT NULL,
          rank INTEGER, computed_at TEXT NOT NULL, params_json TEXT NOT NULL,
          PRIMARY KEY (node_id, metric)
        );
        """
    )
    con.executemany(
        "INSERT INTO nodes VALUES (?, ?, ?, ?, ?, 1, 2, '')",
        [
            ("mod:a.py", "module", "a", "a", "a.py"),
            ("fn:a.py:hot", "function", "hot", "hot", "a.py"),
            ("fn:a.py:cold", "function", "cold", "cold", "a.py"),
        ],
    )
    con.executemany(
        "INSERT INTO edges VALUES (?, ?, ?, NULL)",
        [("mod:a.py", "CONTAINS", "fn:a.py:hot"), ("fn:a.py:hot", "CALLS", "fn:a.py:cold")],
    )
    con.executemany(
        "INSERT INTO centrality_scores VALUES (?, 'sir_pagerank', ?, ?, '2026-01-01', '{}')",
        [("fn:a.py:hot", 0.9, 1), ("mod:a.py", 0.4, 2), ("fn:a.py:cold", 0.1, 3)],
    )
    con.commit()
    con.close()
    return path


def test_writes_a_self_contained_file(graph_db: Path, tmp_path: Path) -> None:
    """The whole point: one command, a file, no server."""
    out = tmp_path / "graph.html"
    result = CliRunner().invoke(cli, ["viz-export", "--db", str(graph_db), "-o", str(out)])

    assert result.exit_code == 0, result.output
    html = out.read_text(encoding="utf-8")
    assert "cdnjs.cloudflare.com/ajax/libs/vis-network" not in html
    assert len(html) > 500_000, "vis-network should be inlined"


def test_reports_what_it_drew(graph_db: Path, tmp_path: Path) -> None:
    """The caller should not have to open the file to learn what is in it."""
    out = tmp_path / "graph.html"
    result = CliRunner().invoke(cli, ["viz-export", "--db", str(graph_db), "-o", str(out)])

    assert "3 of 3 nodes" in result.output
    assert "sized by sir_pagerank" in result.output


def test_metric_none_gives_uniform_sizing(graph_db: Path, tmp_path: Path) -> None:
    """Centrality encoding is opt-out."""
    out = tmp_path / "graph.html"
    result = CliRunner().invoke(
        cli, ["viz-export", "--db", str(graph_db), "-o", str(out), "--metric", "none"]
    )

    assert result.exit_code == 0, result.output
    assert "uniform sizing" in result.output


def test_unknown_metric_is_a_clear_error(graph_db: Path, tmp_path: Path) -> None:
    """A typo must not silently produce an unweighted graph."""
    out = tmp_path / "graph.html"
    result = CliRunner().invoke(
        cli, ["viz-export", "--db", str(graph_db), "-o", str(out), "--metric", "nonsense"]
    )

    assert result.exit_code != 0
    assert "not found" in result.output
    assert not out.exists()


def test_missing_database_points_at_the_fix(tmp_path: Path) -> None:
    """The error should say what to run, not just what failed."""
    result = CliRunner().invoke(
        cli,
        ["viz-export", "--db", str(tmp_path / "nope.sqlite"), "-o", str(tmp_path / "g.html")],
    )

    assert result.exit_code != 0
    assert "build-sqlite" in result.output


def test_kind_filter_with_no_matches_is_an_error(graph_db: Path, tmp_path: Path) -> None:
    """An empty graph is a mistake worth reporting, not an empty file."""
    out = tmp_path / "graph.html"
    result = CliRunner().invoke(
        cli, ["viz-export", "--db", str(graph_db), "-o", str(out), "--kinds", "nonexistent"]
    )

    assert result.exit_code != 0
    assert "No nodes match" in result.output


def test_works_without_streamlit(graph_db: Path, tmp_path: Path, monkeypatch) -> None:
    """Exporting must not require the Streamlit stack.

    This is the property the extraction bought: previously the only way to build
    a 2-D graph was to import ``app.py``, which imports Streamlit at module
    scope and calls ``st.set_page_config`` on import.
    """
    import sys

    monkeypatch.setitem(sys.modules, "streamlit", None)
    out = tmp_path / "graph.html"
    result = CliRunner().invoke(cli, ["viz-export", "--db", str(graph_db), "-o", str(out)])

    assert result.exit_code == 0, result.output
    assert out.is_file()
