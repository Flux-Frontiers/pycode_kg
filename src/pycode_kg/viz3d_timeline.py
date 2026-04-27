"""
viz3d_timeline.py — Temporal Metrics Visualization for PyCodeKG Snapshots

Visualizes codebase metrics evolution across commits using 3D plotting.
Shows trends in nodes, edges, coverage, and critical issues over time.

Features:
  - Interactive 3D line charts for metric trends
  - Side-by-side comparison of multiple metrics
  - Commit-based X-axis with version labels
  - Color-coded risk assessment (green→yellow→red)
  - Hover tooltips with snapshot details
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import plotly.subplots as subplots

from pycode_kg.snapshots import SnapshotManager


def load_snapshots_timeline(snapshots_dir: Path) -> dict[str, Any]:
    """
    Load all snapshots and extract timeline data.

    :param snapshots_dir: Path to .pycodekg/snapshots/
    :return: Dict with timeline data indexed by metric name.
    """
    mgr = SnapshotManager(snapshots_dir)
    snapshots = mgr.list_snapshots()  # Chronological order

    if not snapshots:
        return {}

    # Extract timeline data
    timeline: dict[str, list[Any]] = {
        "commits": [],
        "versions": [],
        "timestamps": [],
        "nodes": [],
        "edges": [],
        "coverage": [],
        "critical_issues": [],
        "complexity_median": [],
    }

    for snap in snapshots:
        timeline["commits"].append(snap["key"][:7])  # Short hash
        timeline["versions"].append(snap["version"])
        timeline["timestamps"].append(snap["timestamp"])
        timeline["nodes"].append(snap["metrics"]["total_nodes"])
        timeline["edges"].append(snap["metrics"]["total_edges"])
        timeline["coverage"].append(snap["metrics"]["docstring_coverage"] * 100)  # Percentage
        timeline["critical_issues"].append(snap["metrics"]["critical_issues"])
        timeline["complexity_median"].append(snap.get("metrics", {}).get("complexity_median", 0))

    return timeline


def create_timeline_figure(snapshots_dir: Path) -> go.Figure:
    """
    Create interactive 3D timeline visualization.

    Shows 4 metrics:
    1. Nodes (absolute count)
    2. Edges (absolute count)
    3. Coverage (percentage)
    4. Critical Issues (count)

    :param snapshots_dir: Path to .pycodekg/snapshots/
    :return: Plotly Figure ready for display.
    """
    timeline = load_snapshots_timeline(snapshots_dir)

    if not timeline["commits"]:
        return go.Figure().add_annotation(text="No snapshots found")

    # Create subplot figure with 2x2 layout
    fig = subplots.make_subplots(
        rows=2,
        cols=2,
        subplot_titles=("Total Nodes", "Total Edges", "Docstring Coverage %", "Critical Issues"),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}],
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.12,
    )

    # Hover text for all traces
    hover_text = [
        f"<b>{v}</b> ({c})<br>Timestamp: {t}"
        for v, c, t in zip(timeline["versions"], timeline["commits"], timeline["timestamps"])
    ]

    # 1. Total Nodes (green trend)
    fig.add_trace(
        go.Scatter(
            x=timeline["commits"],
            y=timeline["nodes"],
            mode="lines+markers",
            name="Nodes",
            line=dict(color="#22c55e", width=3),
            marker=dict(size=8),
            hovertemplate="<b>Nodes:</b> %{y}<br>" + "%{customdata}<extra></extra>",
            customdata=hover_text,
        ),
        row=1,
        col=1,
    )

    # 2. Total Edges (blue trend)
    fig.add_trace(
        go.Scatter(
            x=timeline["commits"],
            y=timeline["edges"],
            mode="lines+markers",
            name="Edges",
            line=dict(color="#3b82f6", width=3),
            marker=dict(size=8),
            hovertemplate="<b>Edges:</b> %{y}<br>" + "%{customdata}<extra></extra>",
            customdata=hover_text,
        ),
        row=1,
        col=2,
    )

    # 3. Coverage % (cyan trend, with target line)
    fig.add_trace(
        go.Scatter(
            x=timeline["commits"],
            y=timeline["coverage"],
            mode="lines+markers",
            name="Coverage %",
            line=dict(color="#06b6d4", width=3),
            marker=dict(size=8),
            hovertemplate="<b>Coverage:</b> %{y:.1f}%<br>" + "%{customdata}<extra></extra>",
            customdata=hover_text,
        ),
        row=2,
        col=1,
    )

    # Add 90% target line for coverage
    fig.add_hline(
        y=90,
        line_dash="dash",
        line_color="orange",
        annotation_text="90% Target",
        row=2,
        col=1,
    )

    # 4. Critical Issues (red risk indicator, lower is better)
    fig.add_trace(
        go.Scatter(
            x=timeline["commits"],
            y=timeline["critical_issues"],
            mode="lines+markers",
            name="Critical Issues",
            line=dict(color="#ef4444", width=3),
            marker=dict(size=8),
            hovertemplate="<b>Issues:</b> %{y}<br>" + "%{customdata}<extra></extra>",
            customdata=hover_text,
        ),
        row=2,
        col=2,
    )

    # Update layout
    fig.update_layout(
        title_text="<b>PyCodeKG Temporal Metrics Evolution</b><br><sub>Snapshots across commits</sub>",
        title_font_size=20,
        height=800,
        width=1400,
        hovermode="x unified",
        template="plotly_dark",
        showlegend=False,
    )

    # Update X axes
    for i in range(1, 5):
        row = (i - 1) // 2 + 1
        col = (i - 1) % 2 + 1
        fig.update_xaxes(title_text="Commit", row=row, col=col)

    # Update Y axes
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    fig.update_yaxes(title_text="Percentage", row=2, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=2)

    return fig


def create_3d_timeline_figure(snapshots_dir: Path) -> go.Figure:
    """
    Create 3D surface plot showing metrics evolution.

    X: Commit index
    Y: Metric value (normalized)
    Z: Different metrics stacked

    :param snapshots_dir: Path to .pycodekg/snapshots/
    :return: Plotly 3D Figure.
    """
    timeline = load_snapshots_timeline(snapshots_dir)

    if not timeline["commits"]:
        return go.Figure().add_annotation(text="No snapshots found")

    # Normalize metrics to 0-100 scale for comparison
    max_nodes = max(timeline["nodes"]) if timeline["nodes"] else 100
    max_edges = max(timeline["edges"]) if timeline["edges"] else 100
    max_issues = max(timeline["critical_issues"]) if timeline["critical_issues"] else 1

    normalized_nodes = [n / max_nodes * 100 for n in timeline["nodes"]]
    normalized_edges = [e / max_edges * 100 for e in timeline["edges"]]
    normalized_coverage = timeline["coverage"]  # Already 0-100
    normalized_issues = [i / max_issues * 100 for i in timeline["critical_issues"]]

    fig = go.Figure()

    # Commit indices for X axis
    commits_idx = list(range(len(timeline["commits"])))

    # Add surface traces for each metric
    # Nodes (green)
    fig.add_trace(
        go.Scatter3d(
            x=commits_idx,
            y=normalized_nodes,
            z=[0] * len(commits_idx),
            mode="lines+markers",
            name="Nodes (normalized)",
            line=dict(color="#22c55e", width=4),
            marker=dict(size=6),
            hovertemplate="<b>Commit:</b> %{customdata}<br><b>Nodes:</b> %{y:.0f}%<extra></extra>",
            customdata=timeline["commits"],
        )
    )

    # Edges (blue)
    fig.add_trace(
        go.Scatter3d(
            x=commits_idx,
            y=normalized_edges,
            z=[1] * len(commits_idx),
            mode="lines+markers",
            name="Edges (normalized)",
            line=dict(color="#3b82f6", width=4),
            marker=dict(size=6),
            hovertemplate="<b>Commit:</b> %{customdata}<br><b>Edges:</b> %{y:.0f}%<extra></extra>",
            customdata=timeline["commits"],
        )
    )

    # Coverage (cyan)
    fig.add_trace(
        go.Scatter3d(
            x=commits_idx,
            y=normalized_coverage,
            z=[2] * len(commits_idx),
            mode="lines+markers",
            name="Coverage %",
            line=dict(color="#06b6d4", width=4),
            marker=dict(size=6),
            hovertemplate="<b>Commit:</b> %{customdata}<br><b>Coverage:</b> %{y:.0f}%<extra></extra>",
            customdata=timeline["commits"],
        )
    )

    # Critical Issues (red - inverted so lower is up)
    fig.add_trace(
        go.Scatter3d(
            x=commits_idx,
            y=[100 - v for v in normalized_issues],  # Invert so lower is better (up)
            z=[3] * len(commits_idx),
            mode="lines+markers",
            name="Health (inverse issues)",
            line=dict(color="#ef4444", width=4),
            marker=dict(size=6),
            hovertemplate="<b>Commit:</b> %{customdata}<br><b>Health:</b> %{y:.0f}%<extra></extra>",
            customdata=timeline["commits"],
        )
    )

    fig.update_layout(
        title="<b>PyCodeKG 3D Temporal Metrics</b><br><sub>Evolution across commits</sub>",
        scene=dict(
            xaxis_title="Commit Index",
            yaxis_title="Metric (0-100%)",
            zaxis=dict(
                title="Metric Type",
                tickvals=[0, 1, 2, 3],
                ticktext=["Nodes", "Edges", "Coverage", "Health"],
            ),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.3),
            ),
        ),
        width=1200,
        height=800,
        template="plotly_dark",
        hovermode="closest",
    )

    return fig


def display_timeline_summary(snapshots_dir: Path) -> str:
    """
    Generate text summary of timeline metrics.

    :param snapshots_dir: Path to .pycodekg/snapshots/
    :return: Formatted summary string.
    """
    timeline = load_snapshots_timeline(snapshots_dir)

    if not timeline["commits"]:
        return "No snapshots found"

    # Calculate deltas
    nodes_delta = timeline["nodes"][-1] - timeline["nodes"][0]
    edges_delta = timeline["edges"][-1] - timeline["edges"][0]
    coverage_delta = timeline["coverage"][-1] - timeline["coverage"][0]
    issues_delta = timeline["critical_issues"][-1] - timeline["critical_issues"][0]

    summary = f"""
+================================================================+
|         PyCodeKG Temporal Metrics Summary                        |
+================================================================+
| Snapshots Captured: {len(timeline["commits"]):<41} |
| Time Range: {timeline["commits"][0]} → {timeline["commits"][-1]:<44} |
| Versions: {timeline["versions"][0]} → {timeline["versions"][-1]:<48} |
+================================================================+
| NODES:                                                         |
|   First:   {timeline["nodes"][0]:<47} |
|   Latest:  {timeline["nodes"][-1]:<47} |
|   Δ:       {nodes_delta:+d:<46} |
+================================================================+
| EDGES:                                                         |
|   First:   {timeline["edges"][0]:<47} |
|   Latest:  {timeline["edges"][-1]:<47} |
|   Δ:       {edges_delta:+d:<46} |
+================================================================+
| DOCSTRING COVERAGE:                                            |
|   First:   {timeline["coverage"][0]:.1f}%<{45} |
|   Latest:  {timeline["coverage"][-1]:.1f}%<{45} |
|   Δ:       {coverage_delta:+.1f}%<{44} |
+================================================================+
| CRITICAL ISSUES:                                               |
|   First:   {timeline["critical_issues"][0]:<47} |
|   Latest:  {timeline["critical_issues"][-1]:<47} |
|   Δ:       {issues_delta:+d:<46} |
|   Trend:   {"Improving" if issues_delta <= 0 else "Regressing":<43} |
+================================================================+
"""
    return summary
