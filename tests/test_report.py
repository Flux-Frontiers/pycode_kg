"""Tests for the report renderer split (pycode_kg.report).

The analyzer computes state; ``render_markdown`` formats it.  These tests pin
the seam: the renderer works from analyzer attributes alone, handles a
freshly-constructed (empty) analyzer without raising, and the delegating
``to_markdown`` method produces the identical document.
"""

from types import SimpleNamespace

import pytest

from pycode_kg.pycodekg_thorough_analysis import CallChain, FunctionMetrics, PyCodeKGAnalyzer
from pycode_kg.report import _snapshot_row, render_markdown


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


def test_edge_distribution_notes_excluded_resolves_to(analyzer) -> None:
    """The table omits RESOLVES_TO, so it says so rather than silently not summing."""
    analyzer.stats = {
        "total_edges": 6443,
        "edge_counts": {
            "CALLS": 2430,
            "ATTR_ACCESS": 2199,
            "IMPORTS": 488,
            "CONTAINS": 357,
            "INHERITS": 11,
            "RESOLVES_TO": 958,
        },
    }
    md = render_markdown(analyzer)
    assert "Excludes 958 `RESOLVES_TO` edges" in md
    # The row itself stays out of the table.
    assert "| RESOLVES_TO |" not in md


def test_edge_distribution_omits_note_when_nothing_excluded(analyzer) -> None:
    """A graph with no RESOLVES_TO edges gets no dangling caveat."""
    analyzer.stats = {
        "total_edges": 2787,
        "edge_counts": {"CALLS": 2430, "IMPORTS": 346, "INHERITS": 11},
    }
    md = render_markdown(analyzer)
    assert "RESOLVES_TO" not in md


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


def test_single_shallow_call_chain_renders_empty_state(analyzer) -> None:
    """One depth-3 chain carries no signal — the empty-state line renders instead."""
    analyzer.critical_paths = [CallChain(chain=["a", "b", "c"], depth=3, total_callers=1)]
    md = render_markdown(analyzer)
    assert "No deep call chains detected." in md
    assert "Deepest call chains in the codebase." not in md


def test_deep_call_chain_renders_section(analyzer) -> None:
    """A single chain that clears the depth bar is shown."""
    analyzer.critical_paths = [CallChain(chain=["a", "b", "c", "d"], depth=4, total_callers=1)]
    md = render_markdown(analyzer)
    assert "Deepest call chains in the codebase." in md


def test_several_shallow_chains_render_section(analyzer) -> None:
    """Enough shallow chains together are signal even if none alone is deep."""
    analyzer.critical_paths = [
        CallChain(chain=["a", "b", "c"], depth=3, total_callers=1) for _ in range(3)
    ]
    md = render_markdown(analyzer)
    assert "Deepest call chains in the codebase." in md


def test_unverifiable_overrides_render_as_separate_section(analyzer) -> None:
    """External-base overrides are shown, not silently dropped or called dead."""
    analyzer.unverifiable_overrides = [
        FunctionMetrics(
            node_id="m:src/p/w.py:W.render",
            name="render",
            module="src/p/w.py",
            kind="method",
            fan_in=0,
            fan_out=0,
            lines=5,
        )
    ]
    md = render_markdown(analyzer)
    assert "render" in md
    assert "cannot be judged dead or alive" in md


def test_snapshot_row_shows_documented_over_total() -> None:
    """The coverage cell shows counts alongside the percentage when available."""
    snap = {
        "timestamp": "2026-08-23T12:00:00+00:00",
        "branch": "main",
        "version": "0.23.1",
        "metrics": {
            "total_nodes": 100,
            "total_edges": 150,
            "docstring_coverage": 0.85,
            "coverage_documented": 68,
            "coverage_total": 80,
        },
    }
    row = _snapshot_row(1, snap)
    assert row[6] == "85.0% (68/80)"


def test_snapshot_row_falls_back_without_counts() -> None:
    """A snapshot saved before coverage counts existed still renders a bare percentage."""
    snap = {
        "timestamp": "2026-08-23T12:00:00+00:00",
        "branch": "main",
        "version": "0.23.0",
        "metrics": {"total_nodes": 100, "total_edges": 150, "docstring_coverage": 0.85},
    }
    row = _snapshot_row(1, snap)
    assert row[6] == "85.0%"
