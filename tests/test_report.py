"""Tests for the report renderer split (pycode_kg.report).

The analyzer computes state; ``render_markdown`` formats it.  These tests pin
the seam: the renderer works from analyzer attributes alone, handles a
freshly-constructed (empty) analyzer without raising, and the delegating
``to_markdown`` method produces the identical document.
"""

from types import SimpleNamespace

import pytest

from pycode_kg.pycodekg_thorough_analysis import PyCodeKGAnalyzer
from pycode_kg.report import render_markdown


@pytest.fixture
def analyzer(tmp_path) -> PyCodeKGAnalyzer:
    """Analyzer stub with empty state — every section takes its else-branch."""
    return PyCodeKGAnalyzer(kg=SimpleNamespace(repo_root=str(tmp_path)))


def test_empty_analyzer_renders_all_sections(analyzer) -> None:
    """An analyzer with no data still renders the full report skeleton."""
    md = render_markdown(analyzer)
    for heading in (
        "## Executive Summary",
        "## Baseline Metrics",
        "## Fan-In Ranking",
        "## Module Architecture",
        "## Docstring Coverage",
        "## Orphaned Code",
        "## Snapshot History",
    ):
        assert heading in md


def test_grade_breakdown_table_is_rendered(analyzer) -> None:
    """The score-components table appears with all four rows."""
    md = render_markdown(analyzer)
    for component in ("Docstring coverage", "Dead code", "High fan-out", "Circular dependencies"):
        assert component in md


def test_metadata_and_footer_are_optional(analyzer) -> None:
    """metadata prepends verbatim; elapsed_seconds adds the timing footer."""
    md = render_markdown(analyzer, metadata="> provenance", elapsed_seconds=1.5)
    assert md.startswith("> provenance")
    assert "1.5s" in md
    bare = render_markdown(analyzer)
    assert "provenance" not in bare


def test_to_markdown_delegates_to_render_markdown(analyzer) -> None:
    """The analyzer method and the renderer produce the identical document."""
    assert analyzer.to_markdown() == render_markdown(analyzer)
