"""
cmd_snapshot.py

Click subcommands for managing temporal snapshots of PyCodeKG metrics:

  snapshot save   — capture current metrics and save snapshot
  snapshot list   — show all snapshots with key metrics
  snapshot show   — display full snapshot details
  snapshot diff   — compare two snapshots
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from pycode_kg.cli.main import cli
from pycode_kg.cli.options import sqlite_option
from pycode_kg.pycodekg import DEFAULT_MODEL
from pycode_kg.pycodekg_thorough_analysis import PyCodeKGAnalyzer
from pycode_kg.kg import PyCodeKG
from pycode_kg.snapshots import SnapshotManager
from pycode_kg.store import GraphStore


@cli.group("snapshot")
def snapshot() -> None:
    """Manage temporal snapshots of PyCodeKG metrics."""
    pass


@snapshot.command("save")
@click.argument("version", metavar="VERSION", default="", required=False)
@click.option(
    "--repo",
    default=".",
    type=click.Path(exists=True),
    show_default=True,
    help="Repository root path.",
)
@sqlite_option
@click.option(
    "--snapshots-dir",
    default=None,
    type=click.Path(),
    help="Snapshots directory (default: .pycodekg/snapshots).",
)
@click.option(
    "--branch",
    default=None,
    type=str,
    help="Branch name; auto-detected if not provided.",
)
@click.option(
    "--tree-hash",
    default="",
    type=str,
    help="Git tree hash; auto-detected if not provided.",
)
def save_snapshot(
    version: str | None,
    repo: str,
    sqlite: str,
    snapshots_dir: str | None,
    branch: str | None,
    tree_hash: str,
) -> None:
    """
    Capture current PyCodeKG metrics and save as a temporal snapshot.

    Reads graph statistics, docstring coverage, and complexity metrics from
    the SQLite graph, then saves a snapshot tagged with the given VERSION.
    The tree hash is auto-detected from git when not provided.

    Snapshots are stored in .pycodekg/snapshots/{tree_hash}.json, with a
    manifest.json tracking all snapshots and their metrics.

    Example:
        pycodekg snapshot save 0.5.1 --repo .
    """
    repo_root = Path(repo).resolve()
    db_path = Path(sqlite)
    snapshots_path = (
        Path(snapshots_dir).resolve() if snapshots_dir else (repo_root / ".pycodekg" / "snapshots")
    )

    # Load graph stats
    store = GraphStore(db_path)
    try:
        stats = store.stats()
    finally:
        store.close()

    # Load PyCodeKG and get docstring coverage + complexity metrics
    kg = PyCodeKG(
        repo_root=repo_root,
        db_path=db_path,
        lancedb_dir=repo_root / ".pycodekg" / "lancedb",
        model=DEFAULT_MODEL,
    )
    snap_mgr = SnapshotManager(snapshots_path, db_path=db_path)
    try:
        analyzer = PyCodeKGAnalyzer(kg, snapshot_mgr=snap_mgr)
        analysis = analyzer.run_analysis()

        # Extract metrics from analysis results
        docstring_cov = analysis.get("docstring_coverage", {})
        coverage = docstring_cov.get("coverage_pct", 0.0) / 100.0 if docstring_cov else 0.0
        issue_strings = analysis.get("issues", [])
        critical_issues = len(issue_strings)

        # Compile hotspots from function metrics
        fn_metrics = analysis.get("function_metrics", {})
        hotspots = [
            {
                "name": name,
                "callers": metrics.get("fan_in", 0),
                "callees": metrics.get("fan_out", 0),
                "risk_level": metrics.get("risk_level", "low"),
            }
            for name, metrics in list(fn_metrics.items())[:10]
        ]

        # Calculate complexity median from function metrics
        fan_ins = [m.get("fan_in", 0) for m in fn_metrics.values()]
        complexity_median = (
            (sorted(fan_ins)[len(fan_ins) // 2] if len(fan_ins) > 0 else 0.0) if fan_ins else 0.0
        )
    finally:
        kg.close()

    # Capture snapshot
    snapshot_obj = snap_mgr.capture(
        version=version,
        branch=branch,
        graph_stats_dict=stats,
        coverage=coverage,
        critical_issues=critical_issues,
        complexity_median=complexity_median,
        hotspots=hotspots,
        issues=issue_strings,
        tree_hash=tree_hash,
    )

    snapshot_file = snap_mgr.save_snapshot(snapshot_obj)
    click.echo(f"OK Snapshot saved: {snapshot_file}")
    click.echo(f"  Key:     {snapshot_obj.key}")
    click.echo(f"  Version: {snapshot_obj.version}")
    click.echo(f"  Nodes:   {snapshot_obj.metrics.total_nodes}")
    click.echo(f"  Edges:   {snapshot_obj.metrics.total_edges}")
    click.echo(f"  Coverage: {snapshot_obj.metrics.docstring_coverage:.1%}")


@snapshot.command("list")
@click.option(
    "--snapshots-dir",
    default=None,
    type=click.Path(exists=True),
    help="Snapshots directory (default: .pycodekg/snapshots).",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Max snapshots to show.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON.",
)
def list_snapshots(snapshots_dir: str | None, limit: int | None, output_json: bool) -> None:
    """
    List all temporal snapshots in reverse chronological order.

    Shows key, timestamp, version, and key metrics (nodes, edges, coverage)
    for each snapshot.
    """
    snapshots_path = (
        Path(snapshots_dir).resolve() if snapshots_dir else (Path.cwd() / ".pycodekg" / "snapshots")
    )
    mgr = SnapshotManager(snapshots_path)
    snapshots = mgr.list_snapshots(limit=limit)

    if not snapshots:
        click.echo("No snapshots found.")
        return

    if output_json:
        click.echo(json.dumps(snapshots, indent=2))
    else:
        # Table output
        click.echo(
            f"{'Key':<12} {'Timestamp':<20} {'Branch':<12} {'Version':<8} {'Nodes':<6} {'Edges':<6} {'Coverage':<9}"
        )
        click.echo("-" * 85)
        for snap in snapshots:
            key = snap["key"][:12]
            # Parse ISO timestamp and format as YYYY-MM-DD HH:MM
            ts = snap["timestamp"]
            ts_display = ts[:16].replace("T", " ") if ts else "unknown"[:20]
            branch = snap["branch"][:12]
            version = snap["version"][:8]
            nodes = snap["metrics"]["total_nodes"]
            edges = snap["metrics"]["total_edges"]
            coverage = snap["metrics"]["docstring_coverage"]
            click.echo(
                f"{key:<12} {ts_display:<20} {branch:<12} {version:<8} {nodes:<6} {edges:<6} {coverage:>6.1%}"
            )


@snapshot.command("show")
@click.argument("key", metavar="KEY")
@click.option(
    "--snapshots-dir",
    default=None,
    type=click.Path(exists=True),
    help="Snapshots directory (default: .pycodekg/snapshots).",
)
def show_snapshot(key: str, snapshots_dir: str | None) -> None:
    """
    Display full details for a single snapshot by key (tree hash).

    Shows all metrics, hotspots, and deltas vs. previous and baseline snapshots.
    """
    snapshots_path = (
        Path(snapshots_dir).resolve() if snapshots_dir else (Path.cwd() / ".pycodekg" / "snapshots")
    )
    mgr = SnapshotManager(snapshots_path)
    snapshot_obj = mgr.load_snapshot(key)

    if not snapshot_obj:
        click.echo(f"Snapshot not found: {key}", err=True)
        raise click.Abort()

    # Print snapshot details
    click.echo(f"Key:       {snapshot_obj.key}")
    click.echo(f"Branch:    {snapshot_obj.branch}")
    click.echo(f"Timestamp: {snapshot_obj.timestamp}")
    click.echo(f"Version:   {snapshot_obj.version}")
    click.echo()

    click.echo("Metrics:")
    click.echo(f"  Total Nodes:       {snapshot_obj.metrics.total_nodes}")
    click.echo(f"  Total Edges:       {snapshot_obj.metrics.total_edges}")
    click.echo(f"  Meaningful Nodes:  {snapshot_obj.metrics.meaningful_nodes}")
    click.echo(f"  Docstring Coverage: {snapshot_obj.metrics.docstring_coverage:.1%}")
    click.echo(f"  Critical Issues:   {snapshot_obj.metrics.critical_issues}")
    click.echo(f"  Complexity Median: {snapshot_obj.metrics.complexity_median:.2f}")
    click.echo()

    click.echo("Node/Edge Breakdown:")
    for kind, count in sorted(snapshot_obj.metrics.node_counts.items()):
        click.echo(f"  {kind}: {count}")
    click.echo()
    for rel, count in sorted(snapshot_obj.metrics.edge_counts.items()):
        click.echo(f"  {rel}: {count}")
    click.echo()

    if snapshot_obj.hotspots:
        click.echo("Top Hotspots (Fan-In):")
        for i, hotspot in enumerate(snapshot_obj.hotspots[:5], 1):
            name = hotspot.get("name", "unknown")
            callers = hotspot.get("callers", 0)
            click.echo(f"  {i}. {name} ({callers} callers)")
        click.echo()

    if snapshot_obj.vs_previous:
        click.echo("Delta vs. Previous:")
        delta = snapshot_obj.vs_previous
        click.echo(f"  Nodes:       {delta.nodes:+d}")
        click.echo(f"  Edges:       {delta.edges:+d}")
        click.echo(f"  Coverage:    {delta.coverage_delta:+.1%}")
        click.echo(f"  Issues:      {delta.critical_issues_delta:+d}")
        click.echo()

    if snapshot_obj.vs_baseline:
        click.echo("Delta vs. Baseline:")
        delta = snapshot_obj.vs_baseline
        click.echo(f"  Nodes:       {delta.nodes:+d}")
        click.echo(f"  Edges:       {delta.edges:+d}")
        click.echo(f"  Coverage:    {delta.coverage_delta:+.1%}")
        click.echo(f"  Issues:      {delta.critical_issues_delta:+d}")


@snapshot.command("diff")
@click.argument("key_a", metavar="KEY_A")
@click.argument("key_b", metavar="KEY_B")
@click.option(
    "--snapshots-dir",
    default=None,
    type=click.Path(exists=True),
    help="Snapshots directory (default: .pycodekg/snapshots).",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON.",
)
def diff_snapshots(key_a: str, key_b: str, snapshots_dir: str | None, output_json: bool) -> None:
    """
    Compare two snapshots side-by-side.

    Shows metrics from both snapshots and computed deltas (B - A).

    Example:
        pycodekg snapshot diff 660e4f0a 3487ed5b
    """
    snapshots_path = (
        Path(snapshots_dir).resolve() if snapshots_dir else (Path.cwd() / ".pycodekg" / "snapshots")
    )
    mgr = SnapshotManager(snapshots_path)
    diff_result = mgr.diff_snapshots(key_a, key_b)

    if "error" in diff_result:
        click.echo(f"Error: {diff_result['error']}", err=True)
        raise click.Abort()

    if output_json:
        click.echo(json.dumps(diff_result, indent=2))
    else:
        # Table output
        a = diff_result["a"]
        b = diff_result["b"]

        click.echo(f"Comparing {a['key'][:10]} vs {b['key'][:10]}")
        click.echo()
        click.echo(f"{'Metric':<20} {'A':<12} {'B':<12} {'Δ':<12}")
        click.echo("-" * 56)

        metrics_a = a["metrics"]
        metrics_b = b["metrics"]

        for key in ["total_nodes", "total_edges", "meaningful_nodes"]:
            val_a = metrics_a[key]
            val_b = metrics_b[key]
            delta_val = val_b - val_a
            click.echo(f"{key:<20} {val_a:<12} {val_b:<12} {delta_val:+d}")

        cov_a = metrics_a["docstring_coverage"]
        cov_b = metrics_b["docstring_coverage"]
        cov_delta = cov_b - cov_a
        click.echo(f"{'docstring_coverage':<20} {cov_a:<12.1%} {cov_b:<12.1%} {cov_delta:+.1%}")

        issues_a = metrics_a["critical_issues"]
        issues_b = metrics_b["critical_issues"]
        issues_delta = issues_b - issues_a
        click.echo(f"{'critical_issues':<20} {issues_a:<12} {issues_b:<12} {issues_delta:+d}")

        issues_data = diff_result.get("issues_delta", {})
        introduced = issues_data.get("introduced", [])
        resolved = issues_data.get("resolved", [])

        if introduced or resolved:
            click.echo()
            click.echo("Issue Changes:")
            for issue in introduced:
                click.echo(f"  [+] {issue}")
            for issue in resolved:
                click.echo(f"  [-] {issue}")
