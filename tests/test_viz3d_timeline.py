"""
test_viz3d_timeline.py

Tests for viz3d_timeline: field name contract and format-string rendering.

Both bugs that were fixed were runtime-only:
  1. load_snapshots_timeline used stale field names ("commit", "nodes", "edges", "coverage")
     instead of the kg_utils names ("key", "total_nodes", "total_edges", "docstring_coverage").
  2. display_timeline_summary used invalid f-string format specs ({val:+d:<46}) that
     raised ValueError at render time.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from unittest.mock import patch

import pytest

from pycode_kg.viz3d_timeline import (
    create_timeline_figure,
    display_timeline_summary,
    load_snapshots_timeline,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_SNAP = {
    "key": "abcdef1234567890",  # pragma: allowlist secret
    "version": "0.17.0",
    "timestamp": "2026-04-01T10:00:00+00:00",
    "branch": "main",
    "metrics": {
        "total_nodes": 100,
        "total_edges": 150,
        "docstring_coverage": 0.85,
        "critical_issues": 2,
        "complexity_median": 3.5,
        "node_counts": {},
        "edge_counts": {},
        "meaningful_nodes": 80,
    },
    "hotspots": [],
}

_SECOND_SNAP = {
    "key": "fedcba0987654321",  # pragma: allowlist secret
    "version": "0.17.1",
    "timestamp": "2026-04-10T10:00:00+00:00",
    "branch": "main",
    "metrics": {
        "total_nodes": 120,
        "total_edges": 180,
        "docstring_coverage": 0.90,
        "critical_issues": 1,
        "complexity_median": 3.2,
        "node_counts": {},
        "edge_counts": {},
        "meaningful_nodes": 95,
    },
    "hotspots": [],
}


def _patch_snapshots(snaps: list[dict]) -> contextlib.AbstractContextManager:
    return patch(
        "pycode_kg.viz3d_timeline.SnapshotManager.list_snapshots",
        return_value=snaps,
    )


# ---------------------------------------------------------------------------
# load_snapshots_timeline — field name contract
# ---------------------------------------------------------------------------


def test_load_snapshots_timeline_empty(tmp_path: Path) -> None:
    """Returns {} when no snapshots exist."""
    with _patch_snapshots([]):
        result = load_snapshots_timeline(tmp_path)
    assert result == {}


def test_load_snapshots_timeline_uses_key_field(tmp_path: Path) -> None:
    """Commit short-hash is taken from snap['key'], not snap['commit']."""
    with _patch_snapshots([_BASE_SNAP]):
        tl = load_snapshots_timeline(tmp_path)
    assert tl["commits"] == ["abcdef1"]


def test_load_snapshots_timeline_uses_total_nodes(tmp_path: Path) -> None:
    """Nodes read from metrics['total_nodes'], not metrics['nodes']."""
    with _patch_snapshots([_BASE_SNAP]):
        tl = load_snapshots_timeline(tmp_path)
    assert tl["nodes"] == [100]


def test_load_snapshots_timeline_uses_total_edges(tmp_path: Path) -> None:
    """Edges read from metrics['total_edges'], not metrics['edges']."""
    with _patch_snapshots([_BASE_SNAP]):
        tl = load_snapshots_timeline(tmp_path)
    assert tl["edges"] == [150]


def test_load_snapshots_timeline_coverage_as_percentage(tmp_path: Path) -> None:
    """Coverage is multiplied by 100 (stored as fraction, displayed as %)."""
    with _patch_snapshots([_BASE_SNAP]):
        tl = load_snapshots_timeline(tmp_path)
    assert tl["coverage"] == [pytest.approx(85.0)]


def test_load_snapshots_timeline_uses_docstring_coverage(tmp_path: Path) -> None:
    """Coverage reads metrics['docstring_coverage'], not metrics['coverage']."""
    snap = dict(_BASE_SNAP)
    snap["metrics"] = dict(_BASE_SNAP["metrics"])
    # Ensure "coverage" key is absent — only "docstring_coverage" present
    assert "coverage" not in snap["metrics"]
    with _patch_snapshots([snap]):
        tl = load_snapshots_timeline(tmp_path)
    assert tl["coverage"] == [pytest.approx(85.0)]


def test_load_snapshots_timeline_critical_issues(tmp_path: Path) -> None:
    """critical_issues is extracted correctly."""
    with _patch_snapshots([_BASE_SNAP]):
        tl = load_snapshots_timeline(tmp_path)
    assert tl["critical_issues"] == [2]


def test_load_snapshots_timeline_multiple_snapshots(tmp_path: Path) -> None:
    """Multiple snapshots produce parallel lists of equal length."""
    with _patch_snapshots([_BASE_SNAP, _SECOND_SNAP]):
        tl = load_snapshots_timeline(tmp_path)
    assert len(tl["commits"]) == 2
    assert len(tl["nodes"]) == 2
    assert tl["nodes"] == [100, 120]
    assert tl["edges"] == [150, 180]
    assert tl["coverage"] == [pytest.approx(85.0), pytest.approx(90.0)]
    assert tl["critical_issues"] == [2, 1]


def test_load_snapshots_timeline_complexity_median_fallback(tmp_path: Path) -> None:
    """Missing complexity_median defaults to 0, not KeyError."""
    snap = dict(_BASE_SNAP)
    snap["metrics"] = {k: v for k, v in _BASE_SNAP["metrics"].items() if k != "complexity_median"}
    with _patch_snapshots([snap]):
        tl = load_snapshots_timeline(tmp_path)
    assert tl["complexity_median"] == [0]


# ---------------------------------------------------------------------------
# display_timeline_summary — format-string rendering
# ---------------------------------------------------------------------------


def test_display_timeline_summary_no_snapshots(tmp_path: Path) -> None:
    """Returns a plain message when no snapshots exist."""
    with _patch_snapshots([]):
        result = display_timeline_summary(tmp_path)
    assert "No snapshots" in result


def test_display_timeline_summary_renders_without_error(tmp_path: Path) -> None:
    """Does not raise ValueError (invalid format spec regression)."""
    with _patch_snapshots([_BASE_SNAP, _SECOND_SNAP]):
        result = display_timeline_summary(tmp_path)
    assert isinstance(result, str)
    assert len(result) > 0


def test_display_timeline_summary_contains_node_counts(tmp_path: Path) -> None:
    """Summary includes first and latest node counts."""
    with _patch_snapshots([_BASE_SNAP, _SECOND_SNAP]):
        result = display_timeline_summary(tmp_path)
    assert "100" in result
    assert "120" in result


def test_display_timeline_summary_contains_coverage(tmp_path: Path) -> None:
    """Summary includes coverage percentages with one decimal place."""
    with _patch_snapshots([_BASE_SNAP, _SECOND_SNAP]):
        result = display_timeline_summary(tmp_path)
    assert "85.0%" in result
    assert "90.0%" in result


def test_display_timeline_summary_coverage_delta_format(tmp_path: Path) -> None:
    """Coverage delta is formatted as ±X.Y% (regression: was invalid spec)."""
    with _patch_snapshots([_BASE_SNAP, _SECOND_SNAP]):
        result = display_timeline_summary(tmp_path)
    assert "+5.0%" in result


def test_display_timeline_summary_node_delta_sign(tmp_path: Path) -> None:
    """Node delta is shown with an explicit sign (regression: was invalid spec)."""
    with _patch_snapshots([_BASE_SNAP, _SECOND_SNAP]):
        result = display_timeline_summary(tmp_path)
    assert "+20" in result


def test_display_timeline_summary_improving_trend(tmp_path: Path) -> None:
    """Shows 'Improving' when critical issues decreased."""
    with _patch_snapshots([_BASE_SNAP, _SECOND_SNAP]):
        result = display_timeline_summary(tmp_path)
    assert "Improving" in result


def test_display_timeline_summary_regressing_trend(tmp_path: Path) -> None:
    """Shows 'Regressing' when critical issues increased."""
    worse = dict(_SECOND_SNAP)
    worse["metrics"] = dict(_SECOND_SNAP["metrics"], critical_issues=5)
    with _patch_snapshots([_BASE_SNAP, worse]):
        result = display_timeline_summary(tmp_path)
    assert "Regressing" in result


def test_display_timeline_summary_single_snapshot(tmp_path: Path) -> None:
    """Works with a single snapshot (zero deltas, no IndexError)."""
    with _patch_snapshots([_BASE_SNAP]):
        result = display_timeline_summary(tmp_path)
    assert isinstance(result, str)
    assert "+0" in result  # zero node delta


# ---------------------------------------------------------------------------
# create_timeline_figure — smoke tests (no renderer needed)
# ---------------------------------------------------------------------------


def test_create_timeline_figure_no_snapshots_returns_figure(tmp_path: Path) -> None:
    """Returns a Figure with an annotation when no snapshots exist."""
    import plotly.graph_objects as go

    with _patch_snapshots([]):
        fig = create_timeline_figure(tmp_path)
    assert isinstance(fig, go.Figure)


def test_create_timeline_figure_with_snapshots(tmp_path: Path) -> None:
    """Returns a populated Figure without raising."""
    import plotly.graph_objects as go

    with _patch_snapshots([_BASE_SNAP, _SECOND_SNAP]):
        fig = create_timeline_figure(tmp_path)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 4  # nodes, edges, coverage, critical_issues traces
