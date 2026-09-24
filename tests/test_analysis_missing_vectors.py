"""
test_analysis_missing_vectors.py

Regression tests for analysis over a graph with no vector index beside it.

``pycodekg build-sqlite`` writes ``graph.sqlite`` and no ``vectors.sqlite``,
by design. Two analyzer phases seed on a semantic query (fan-out and
concern-based ranking), and ``VectorStoreNotFoundError`` used to escape both,
aborting ``analyze``, ``snapshot save``, ``init`` and the MCP ``analyze_repo``
tool with no report and no snapshot. The other phases read the graph only, so
their results must survive, and the report must say which sections are
missing and why.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from pycode_kg.cli.main import cli
from pycode_kg.kg import PyCodeKG
from pycode_kg.pycodekg_thorough_analysis import PyCodeKGAnalyzer

_FILES = {
    "pkg/__init__.py": "",
    "pkg/core.py": "def core():\n    return 1\n",
    "pkg/main.py": ("from pkg.core import core\n\ndef main():\n    return core()\n"),
}


def _make_repo(root: Path) -> Path:
    for rel, src in _FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))
    return root


def _graph_only_kg(tmp_path: Path) -> PyCodeKG:
    repo = _make_repo(tmp_path / "repo")
    kg = PyCodeKG(
        repo_root=repo,
        db_path=tmp_path / "graph.sqlite",
        vectors_path=tmp_path / "vectors.sqlite",
    )
    kg.build_graph(wipe=True)
    assert not (tmp_path / "vectors.sqlite").exists()
    return kg


def test_run_analysis_survives_missing_vector_store(tmp_path):
    """The two semantic phases are recorded as failed; the rest still run."""
    kg = _graph_only_kg(tmp_path)
    try:
        analyzer = PyCodeKGAnalyzer(kg)
        results = analyzer.run_analysis()
    finally:
        kg.close()

    assert [f["phase"] for f in analyzer.phase_failures] == [4, 15]
    assert all(f["missing_index"] for f in analyzer.phase_failures)
    assert results["phase_failures"] == analyzer.phase_failures
    # Graph-only phases still produced their results.
    assert results["statistics"]["total_nodes"] > 0
    assert results["docstring_coverage"]["total"] > 0


def test_report_names_the_skipped_phases(tmp_path):
    """The report says the index is missing rather than silently omitting sections."""
    kg = _graph_only_kg(tmp_path)
    try:
        analyzer = PyCodeKGAnalyzer(kg)
        analyzer.run_analysis()
        report = analyzer.to_markdown()
    finally:
        kg.close()

    assert "## Incomplete Analysis" in report
    assert "2 of 15 phases could not run" in report
    assert "pycodekg build-index" in report


def test_complete_run_has_no_incomplete_section(tmp_path):
    """A run with no failures renders no degraded-run notice."""
    analyzer = PyCodeKGAnalyzer(kg=SimpleNamespace(repo_root=str(tmp_path)))
    assert "Incomplete Analysis" not in analyzer.to_markdown()


def test_snapshot_save_after_build_sqlite(tmp_path):
    """``build-sqlite`` then ``snapshot save`` writes a snapshot and exits 0."""
    repo = _make_repo(tmp_path / "repo")
    runner = CliRunner()

    built = runner.invoke(cli, ["build-sqlite", "--repo", str(repo)])
    assert built.exit_code == 0, built.output
    assert not (repo / ".pycodekg" / "vectors.sqlite").exists()

    saved = runner.invoke(cli, ["snapshot", "save", "0.0.1", "--repo", str(repo)])
    assert saved.exit_code == 0, saved.output
    assert (repo / ".pycodekg" / "snapshots" / "0.0.1.json").exists()
