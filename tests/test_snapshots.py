"""
test_snapshots.py

Tests for temporal snapshot capture, storage, and comparison:
  SnapshotMetrics, SnapshotDelta, Snapshot, SnapshotManager
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from pycode_kg.snapshots import (
    Snapshot,
    SnapshotDelta,
    SnapshotManager,
    SnapshotManifest,
    SnapshotMetrics,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def snapshot_dir(tmp_path: Path) -> Path:
    """Create temporary snapshots directory."""
    snapshots_path = tmp_path / "snapshots"
    snapshots_path.mkdir(parents=True, exist_ok=True)
    return snapshots_path


@pytest.fixture
def sample_metrics() -> SnapshotMetrics:
    """Create sample metrics for testing."""
    return SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={"function": 30, "class": 10, "method": 40},
        edge_counts={"CALLS": 80, "CONTAINS": 50, "IMPORTS": 20},
        critical_issues=2,
        complexity_median=3.5,
    )


@pytest.fixture
def sample_snapshot(sample_metrics: SnapshotMetrics) -> Snapshot:
    """Create sample snapshot for testing."""
    return Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.1",
        metrics=sample_metrics,
        hotspots=[{"name": "func_a", "callers": 5}, {"name": "func_b", "callers": 3}],
        tree_hash="abc123def456",  # pragma: allowlist secret
    )


# ---------------------------------------------------------------------------
# SnapshotMetrics Tests
# ---------------------------------------------------------------------------


def test_snapshot_metrics_creation(sample_metrics: SnapshotMetrics) -> None:
    """Test SnapshotMetrics creation and properties."""
    assert sample_metrics.total_nodes == 100
    assert sample_metrics.total_edges == 150
    assert sample_metrics.meaningful_nodes == 80
    assert sample_metrics.docstring_coverage == 0.85
    assert sample_metrics.critical_issues == 2
    assert sample_metrics.complexity_median == 3.5


def test_snapshot_metrics_node_counts(sample_metrics: SnapshotMetrics) -> None:
    """Test node count breakdown."""
    assert sample_metrics.node_counts["function"] == 30
    assert sample_metrics.node_counts["class"] == 10
    assert sample_metrics.node_counts["method"] == 40


def test_snapshot_metrics_edge_counts(sample_metrics: SnapshotMetrics) -> None:
    """Test edge count breakdown."""
    assert sample_metrics.edge_counts["CALLS"] == 80
    assert sample_metrics.edge_counts["CONTAINS"] == 50
    assert sample_metrics.edge_counts["IMPORTS"] == 20


# ---------------------------------------------------------------------------
# SnapshotDelta Tests
# ---------------------------------------------------------------------------


def test_snapshot_delta_creation() -> None:
    """Test SnapshotDelta creation."""
    delta = SnapshotDelta(nodes=10, edges=15, coverage_delta=0.02, critical_issues_delta=-1)
    assert delta.nodes == 10
    assert delta.edges == 15
    assert delta.coverage_delta == 0.02
    assert delta.critical_issues_delta == -1


def test_snapshot_delta_defaults() -> None:
    """Test SnapshotDelta defaults."""
    delta = SnapshotDelta()
    assert delta.nodes == 0
    assert delta.edges == 0
    assert delta.coverage_delta == 0.0
    assert delta.critical_issues_delta == 0


# ---------------------------------------------------------------------------
# Snapshot Tests
# ---------------------------------------------------------------------------


def test_snapshot_creation(sample_snapshot: Snapshot) -> None:
    """Test Snapshot creation and properties."""
    assert sample_snapshot.tree_hash == "abc123def456"  # pragma: allowlist secret
    assert sample_snapshot.key == "abc123def456"  # pragma: allowlist secret
    assert sample_snapshot.branch == "develop"
    assert sample_snapshot.version == "0.5.1"
    assert sample_snapshot.metrics.total_nodes == 100
    assert len(sample_snapshot.hotspots) == 2


def test_snapshot_to_dict(sample_snapshot: Snapshot) -> None:
    """Test Snapshot serialization to dict."""
    snap_dict = sample_snapshot.to_dict()
    assert snap_dict["key"] == "abc123def456"  # pragma: allowlist secret
    assert "commit" not in snap_dict
    assert snap_dict["branch"] == "develop"
    assert snap_dict["version"] == "0.5.1"
    assert snap_dict["metrics"]["total_nodes"] == 100
    assert len(snap_dict["hotspots"]) == 2


def test_snapshot_from_dict(sample_snapshot: Snapshot) -> None:
    """Test Snapshot deserialization from dict."""
    snap_dict = sample_snapshot.to_dict()
    restored = Snapshot.from_dict(snap_dict)
    assert restored.tree_hash == sample_snapshot.tree_hash
    assert restored.branch == sample_snapshot.branch
    assert restored.version == sample_snapshot.version
    assert restored.metrics.total_nodes == sample_snapshot.metrics.total_nodes


def test_snapshot_roundtrip(sample_snapshot: Snapshot) -> None:
    """Test Snapshot serialize/deserialize roundtrip."""
    original_dict = sample_snapshot.to_dict()
    # Make a copy since from_dict modifies the input dict via pop()
    dict_copy = json.loads(json.dumps(original_dict))
    restored = Snapshot.from_dict(dict_copy)
    restored_dict = restored.to_dict()
    assert original_dict == restored_dict


def test_snapshot_with_deltas() -> None:
    """Test Snapshot with delta information."""
    metrics = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=2,
        complexity_median=3.5,
    )
    vs_prev = SnapshotDelta(nodes=10, edges=5, coverage_delta=0.01)
    vs_base = SnapshotDelta(nodes=20, edges=30, coverage_delta=0.05)

    snap = Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.1",
        metrics=metrics,
        vs_previous=vs_prev,
        vs_baseline=vs_base,
        tree_hash="abc123",
    )

    snap_dict = snap.to_dict()
    assert snap_dict["vs_previous"] is not None
    assert snap_dict["vs_baseline"] is not None

    restored = Snapshot.from_dict(snap_dict)
    assert restored.vs_previous is not None
    assert restored.vs_baseline is not None
    assert restored.vs_previous.nodes == 10


# ---------------------------------------------------------------------------
# SnapshotManager Tests
# ---------------------------------------------------------------------------


def test_snapshot_manager_creation(snapshot_dir: Path) -> None:
    """Test SnapshotManager initialization."""
    mgr = SnapshotManager(snapshot_dir)
    assert mgr.snapshots_dir == snapshot_dir
    assert mgr.manifest_path == snapshot_dir / "manifest.json"


def test_snapshot_manager_creates_directory(tmp_path: Path) -> None:
    """Test SnapshotManager creates directory if missing."""
    snapshots_path = tmp_path / "new_snapshots"
    assert not snapshots_path.exists()

    SnapshotManager(snapshots_path)
    assert snapshots_path.exists()
    assert snapshots_path.is_dir()


def test_snapshot_manager_capture(snapshot_dir: Path, sample_metrics: SnapshotMetrics) -> None:
    """Test snapshot capture."""
    mgr = SnapshotManager(snapshot_dir)

    with patch(
        "pycode_kg.snapshots.SnapshotManager._get_current_tree_hash",
        return_value="abc123tree",  # pragma: allowlist secret
    ):
        with patch(
            "pycode_kg.snapshots.SnapshotManager._get_current_branch",
            return_value="develop",
        ):
            snap = mgr.capture(
                version="0.5.1",
                graph_stats_dict={
                    "total_nodes": 100,
                    "total_edges": 150,
                    "meaningful_nodes": 80,
                    "node_counts": {},
                    "edge_counts": {},
                },
                coverage=0.85,
                critical_issues=2,
                complexity_median=3.5,
            )

    assert snap.tree_hash == "abc123tree"  # pragma: allowlist secret
    assert snap.branch == "develop"
    assert snap.version == "0.5.1"
    assert snap.metrics.total_nodes == 100


def test_snapshot_manager_capture_coverage_counts(
    snapshot_dir: Path, sample_metrics: SnapshotMetrics
) -> None:
    """coverage_documented/coverage_total ride alongside the coverage fraction."""
    mgr = SnapshotManager(snapshot_dir)

    with patch(
        "pycode_kg.snapshots.SnapshotManager._get_current_tree_hash",
        return_value="abc123tree",  # pragma: allowlist secret
    ):
        with patch(
            "pycode_kg.snapshots.SnapshotManager._get_current_branch",
            return_value="develop",
        ):
            snap = mgr.capture(
                version="0.5.1",
                graph_stats_dict={"total_nodes": 100, "total_edges": 150},
                coverage=0.85,
                coverage_documented=68,
                coverage_total=80,
                critical_issues=0,
                complexity_median=1.0,
            )

    assert snap.metrics.coverage_documented == 68
    assert snap.metrics.coverage_total == 80


def test_snapshot_metrics_coverage_counts_default_to_zero() -> None:
    """A SnapshotMetrics built without the new fields (old call sites) stays valid."""
    m = SnapshotMetrics(
        total_nodes=1,
        total_edges=1,
        meaningful_nodes=1,
        docstring_coverage=0.5,
        node_counts={},
        edge_counts={},
        critical_issues=0,
        complexity_median=0.0,
    )
    assert m.coverage_documented == 0
    assert m.coverage_total == 0


def test_snapshot_metrics_from_dict_missing_coverage_counts() -> None:
    """A snapshot saved before this field existed loads with zero defaults, not KeyError."""
    from pycode_kg.snapshots import metrics_from_dict

    m = metrics_from_dict({"total_nodes": 1, "docstring_coverage": 0.5})
    assert m.coverage_documented == 0
    assert m.coverage_total == 0


def test_snapshot_manager_save_and_load(snapshot_dir: Path, sample_snapshot: Snapshot) -> None:
    """Test saving and loading snapshots."""
    mgr = SnapshotManager(snapshot_dir)

    # Save snapshot
    saved_path = mgr.save_snapshot(sample_snapshot)
    assert saved_path.exists()
    assert saved_path.name == f"{sample_snapshot.key}.json"

    # Load snapshot
    loaded = mgr.load_snapshot(sample_snapshot.key)
    assert loaded is not None
    assert loaded.tree_hash == sample_snapshot.tree_hash
    assert loaded.version == sample_snapshot.version


def test_snapshot_manager_manifest_created(snapshot_dir: Path, sample_snapshot: Snapshot) -> None:
    """Test manifest.json is created."""
    mgr = SnapshotManager(snapshot_dir)
    mgr.save_snapshot(sample_snapshot)

    assert mgr.manifest_path.exists()
    with open(mgr.manifest_path) as f:
        manifest_data = json.load(f)

    assert manifest_data["format"] == "1.0"
    assert len(manifest_data["snapshots"]) == 1
    assert manifest_data["snapshots"][0]["key"] == sample_snapshot.key


def test_snapshot_manager_list_snapshots(snapshot_dir: Path) -> None:
    """Test listing snapshots."""
    mgr = SnapshotManager(snapshot_dir)

    metrics = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=2,
        complexity_median=3.5,
    )

    # Create and save multiple snapshots
    snap1 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T10:00:00+00:00",
        version="0.5.0",
        metrics=metrics,
        tree_hash="treehash1",
    )
    snap2 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.1",
        metrics=metrics,
        tree_hash="treehash2",
    )

    mgr.save_snapshot(snap1)
    mgr.save_snapshot(snap2)

    snapshots = mgr.list_snapshots()
    assert len(snapshots) == 2
    # Should be in reverse chronological order
    assert snapshots[0]["timestamp"] > snapshots[1]["timestamp"]


def test_snapshot_manager_diff_snapshots(snapshot_dir: Path) -> None:
    """Test snapshot diff."""
    mgr = SnapshotManager(snapshot_dir)

    metrics1 = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=2,
        complexity_median=3.5,
    )
    metrics2 = SnapshotMetrics(
        total_nodes=120,
        total_edges=170,
        meaningful_nodes=95,
        docstring_coverage=0.87,
        node_counts={},
        edge_counts={},
        critical_issues=1,
        complexity_median=3.8,
    )

    snap1 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T10:00:00+00:00",
        version="0.5.0",
        metrics=metrics1,
        tree_hash="treehash1",
    )
    snap2 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.1",
        metrics=metrics2,
        tree_hash="treehash2",
    )

    mgr.save_snapshot(snap1)
    mgr.save_snapshot(snap2)

    diff = mgr.diff_snapshots("treehash1", "treehash2")
    assert "a" in diff
    assert "b" in diff
    assert "delta" in diff
    assert diff["delta"]["nodes"] == 20
    assert diff["delta"]["edges"] == 20
    assert diff["delta"]["critical_issues_delta"] == -1


def test_snapshot_manager_get_previous(snapshot_dir: Path) -> None:
    """Test getting previous snapshot."""
    mgr = SnapshotManager(snapshot_dir)

    metrics = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=2,
        complexity_median=3.5,
    )

    snap1 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T10:00:00+00:00",
        version="0.5.0",
        metrics=metrics,
        tree_hash="treehash1",
    )
    snap2 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.1",
        metrics=metrics,
        tree_hash="treehash2",
    )

    mgr.save_snapshot(snap1)
    mgr.save_snapshot(snap2)

    prev = mgr.get_previous("treehash2")
    assert prev is not None
    assert prev.tree_hash == "treehash1"


def test_snapshot_manager_get_baseline(snapshot_dir: Path) -> None:
    """Test getting baseline (oldest) snapshot."""
    mgr = SnapshotManager(snapshot_dir)

    metrics = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=2,
        complexity_median=3.5,
    )

    snap1 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T10:00:00+00:00",
        version="0.5.0",
        metrics=metrics,
        tree_hash="treehash1",
    )
    snap2 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.1",
        metrics=metrics,
        tree_hash="treehash2",
    )

    mgr.save_snapshot(snap1)
    mgr.save_snapshot(snap2)

    baseline = mgr.get_baseline()
    assert baseline is not None
    assert baseline.tree_hash == "treehash1"


def test_snapshot_manager_delta_computation(snapshot_dir: Path) -> None:
    """Test automatic delta computation on capture."""
    mgr = SnapshotManager(snapshot_dir)

    metrics1 = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=2,
        complexity_median=3.5,
    )

    snap1 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T10:00:00+00:00",
        version="0.5.0",
        metrics=metrics1,
        tree_hash="treehash1",
    )
    mgr.save_snapshot(snap1)

    # Capture second snapshot - should compute deltas
    snap2 = mgr.capture(
        version="0.5.1",
        branch="develop",
        graph_stats_dict={
            "total_nodes": 110,
            "total_edges": 160,
            "meaningful_nodes": 88,
            "node_counts": {},
            "edge_counts": {},
        },
        coverage=0.87,
        critical_issues=1,
        complexity_median=3.7,
    )

    # The captured snapshot should have deltas computed (it finds previous by timestamp)
    # But since capture uses current time, we need to check vs_baseline instead
    # which is computed regardless
    assert snap2.vs_baseline is not None
    assert snap2.vs_baseline.nodes == 10
    assert snap2.vs_baseline.edges == 10
    assert abs(snap2.vs_baseline.coverage_delta - 0.02) < 0.01
    assert snap2.vs_baseline.critical_issues_delta == -1


# ---------------------------------------------------------------------------
# SnapshotManifest Tests
# ---------------------------------------------------------------------------


def test_snapshot_manifest_creation() -> None:
    """Test SnapshotManifest creation."""
    manifest = SnapshotManifest(format_version="1.0", last_update="2026-03-07T12:00:00+00:00")
    assert manifest.format_version == "1.0"
    assert len(manifest.snapshots) == 0


def test_snapshot_manifest_roundtrip() -> None:
    """Test SnapshotManifest serialize/deserialize."""
    manifest = SnapshotManifest(
        format_version="1.0",
        last_update="2026-03-07T12:00:00+00:00",
        snapshots=[{"key": "abc123tree", "version": "0.5.1"}],
    )

    manifest_dict = manifest.to_dict()
    restored = SnapshotManifest.from_dict(manifest_dict)

    assert restored.format_version == manifest.format_version
    assert len(restored.snapshots) == 1
    assert restored.snapshots[0]["key"] == "abc123tree"


# ---------------------------------------------------------------------------
# Tests for recent changes (tree-hash-only migration)
# ---------------------------------------------------------------------------


def test_snapshot_from_dict_drops_legacy_commit_field(
    sample_metrics: SnapshotMetrics,
) -> None:
    """from_dict silently discards the legacy 'commit' field."""
    snap_dict = {
        "tree_hash": "newhash123",
        "commit": "oldhash456",  # legacy — must be dropped
        "branch": "main",
        "timestamp": "2026-03-07T12:00:00+00:00",
        "version": "0.5.0",
        "metrics": {
            "total_nodes": 100,
            "total_edges": 150,
            "meaningful_nodes": 80,
            "docstring_coverage": 0.85,
            "node_counts": {},
            "edge_counts": {},
            "critical_issues": 2,
            "complexity_median": 3.5,
        },
        "hotspots": [],
        "vs_previous": None,
        "vs_baseline": None,
    }
    snap = Snapshot.from_dict(snap_dict)
    assert snap.tree_hash == "newhash123"
    assert snap.key == "newhash123"


def test_save_snapshot_manifest_has_full_metrics(
    snapshot_dir: Path, sample_snapshot: Snapshot
) -> None:
    """Manifest entry stores the full SnapshotMetrics dict, not a summary."""
    mgr = SnapshotManager(snapshot_dir)
    mgr.save_snapshot(sample_snapshot)

    with open(mgr.manifest_path) as f:
        manifest_data = json.load(f)

    metrics = manifest_data["snapshots"][0]["metrics"]
    # Full metrics fields must be present
    assert "total_nodes" in metrics
    assert "total_edges" in metrics
    assert "docstring_coverage" in metrics
    assert "node_counts" in metrics
    assert "edge_counts" in metrics
    # Old summary-only keys must not appear at the top level
    assert "nodes" not in metrics
    assert "edges" not in metrics
    assert "coverage" not in metrics


def test_save_snapshot_zero_nodes_raises(snapshot_dir: Path) -> None:
    """save_snapshot raises ValueError for a degenerate (0-node) snapshot."""
    mgr = SnapshotManager(snapshot_dir)
    empty_metrics = SnapshotMetrics(
        total_nodes=0,
        total_edges=0,
        meaningful_nodes=0,
        docstring_coverage=0.0,
        node_counts={},
        edge_counts={},
        critical_issues=0,
        complexity_median=0.0,
    )
    snap = Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.0",
        metrics=empty_metrics,
        tree_hash="emptyhash",
    )
    with pytest.raises(ValueError, match="0 nodes"):
        mgr.save_snapshot(snap)


def test_save_snapshot_same_key_updates_manifest_entry(
    snapshot_dir: Path, sample_metrics: SnapshotMetrics
) -> None:
    """Saving a snapshot with the same tree_hash updates the manifest entry in place."""
    mgr = SnapshotManager(snapshot_dir)

    snap_v1 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.0",
        metrics=sample_metrics,
        tree_hash="samehash",
    )
    mgr.save_snapshot(snap_v1)

    snap_v2 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.1",  # updated version
        metrics=sample_metrics,
        tree_hash="samehash",  # same key
    )
    mgr.save_snapshot(snap_v2)

    with open(mgr.manifest_path) as f:
        manifest_data = json.load(f)

    assert len(manifest_data["snapshots"]) == 1
    assert manifest_data["snapshots"][0]["version"] == "0.5.1"


def test_list_snapshots_with_limit(snapshot_dir: Path) -> None:
    """list_snapshots(limit=N) returns at most N entries."""
    mgr = SnapshotManager(snapshot_dir)
    metrics = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=0,
        complexity_median=1.0,
    )
    for i in range(5):
        mgr.save_snapshot(
            Snapshot(
                branch="develop",
                timestamp=f"2026-03-0{i + 1}T12:00:00+00:00",
                version=f"0.5.{i}",
                metrics=metrics,
                tree_hash=f"hash{i}",
            )
        )

    assert len(mgr.list_snapshots(limit=3)) == 3
    assert len(mgr.list_snapshots()) == 5


def test_list_snapshots_branch_filter(snapshot_dir: Path) -> None:
    """list_snapshots(branch=...) returns only snapshots for that branch."""
    mgr = SnapshotManager(snapshot_dir)
    metrics = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=0,
        complexity_median=1.0,
    )
    mgr.save_snapshot(
        Snapshot(
            branch="main",
            timestamp="2026-03-01T12:00:00+00:00",
            version="0.5.0",
            metrics=metrics,
            tree_hash="main1",
        )
    )
    mgr.save_snapshot(
        Snapshot(
            branch="develop",
            timestamp="2026-03-02T12:00:00+00:00",
            version="0.5.1",
            metrics=metrics,
            tree_hash="dev1",
        )
    )
    mgr.save_snapshot(
        Snapshot(
            branch="main",
            timestamp="2026-03-03T12:00:00+00:00",
            version="0.5.2",
            metrics=metrics,
            tree_hash="main2",
        )
    )

    main_snaps = mgr.list_snapshots(branch="main")
    assert len(main_snaps) == 2
    assert all(s["branch"] == "main" for s in main_snaps)

    dev_snaps = mgr.list_snapshots(branch="develop")
    assert len(dev_snaps) == 1
    assert dev_snaps[0]["key"] == "dev1"


def test_diff_snapshots_missing_key_returns_error(snapshot_dir: Path) -> None:
    """diff_snapshots returns an error dict when a key is not found."""
    mgr = SnapshotManager(snapshot_dir)
    result = mgr.diff_snapshots("nonexistent_a", "nonexistent_b")
    assert "error" in result


def test_diff_snapshots_node_edge_kind_breakdown(snapshot_dir: Path) -> None:
    """diff_snapshots includes per-kind node and edge count deltas."""
    mgr = SnapshotManager(snapshot_dir)

    snap1 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T10:00:00+00:00",
        version="0.5.0",
        metrics=SnapshotMetrics(
            total_nodes=100,
            total_edges=150,
            meaningful_nodes=80,
            docstring_coverage=0.85,
            node_counts={"function": 30, "class": 10},
            edge_counts={"CALLS": 80, "IMPORTS": 20},
            critical_issues=2,
            complexity_median=3.5,
        ),
        tree_hash="kinda1",
    )
    snap2 = Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.1",
        metrics=SnapshotMetrics(
            total_nodes=120,
            total_edges=160,
            meaningful_nodes=90,
            docstring_coverage=0.90,
            node_counts={"function": 40, "class": 10},
            edge_counts={"CALLS": 90, "IMPORTS": 20},
            critical_issues=1,
            complexity_median=3.8,
        ),
        tree_hash="kinda2",
    )
    mgr.save_snapshot(snap1)
    mgr.save_snapshot(snap2)

    diff = mgr.diff_snapshots("kinda1", "kinda2")
    assert "node_counts_delta" in diff
    assert "edge_counts_delta" in diff
    assert diff["node_counts_delta"]["function"] == 10
    assert diff["node_counts_delta"]["class"] == 0
    assert diff["edge_counts_delta"]["CALLS"] == 10


def test_get_previous_oldest_returns_none(snapshot_dir: Path) -> None:
    """get_previous on the oldest snapshot returns None (no predecessor)."""
    mgr = SnapshotManager(snapshot_dir)
    metrics = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=0,
        complexity_median=1.0,
    )
    snap = Snapshot(
        branch="develop",
        timestamp="2026-03-07T10:00:00+00:00",
        version="0.5.0",
        metrics=metrics,
        tree_hash="onlyhash",
    )
    mgr.save_snapshot(snap)
    assert mgr.get_previous("onlyhash") is None


def test_get_baseline_empty_manifest_returns_none(snapshot_dir: Path) -> None:
    """get_baseline with no snapshots returns None."""
    mgr = SnapshotManager(snapshot_dir)
    assert mgr.get_baseline() is None


def test_capture_none_graph_stats_defaults_to_empty(snapshot_dir: Path) -> None:
    """capture(graph_stats_dict=None) uses empty dict without crashing."""
    mgr = SnapshotManager(snapshot_dir)
    with patch(
        "pycode_kg.snapshots.SnapshotManager._get_current_tree_hash",
        return_value="treehashX",
    ):
        with patch("pycode_kg.snapshots.SnapshotManager._get_current_branch", return_value="main"):
            snap = mgr.capture(version="0.5.0", graph_stats_dict=None, coverage=0.9)
    assert snap.metrics.total_nodes == 0
    assert snap.tree_hash == "treehashX"


def test_capture_computes_vs_previous_when_prior_snapshot_exists(
    snapshot_dir: Path,
) -> None:
    """capture sets vs_previous delta when a snapshot with matching tree_hash exists."""
    mgr = SnapshotManager(snapshot_dir)
    metrics = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=2,
        complexity_median=3.5,
    )
    existing = Snapshot(
        branch="develop",
        timestamp="2026-03-07T10:00:00+00:00",
        version="0.5.0",
        metrics=metrics,
        tree_hash="prevhash",
    )
    mgr.save_snapshot(existing)

    # Capture a new snapshot whose previous lookup will resolve to 'prevhash'
    with patch(
        "pycode_kg.snapshots.SnapshotManager._get_current_tree_hash",
        return_value="nexthash",
    ):
        with patch(
            "pycode_kg.snapshots.SnapshotManager._get_current_branch",
            return_value="develop",
        ):
            with patch("pycode_kg.snapshots.SnapshotManager.get_previous", return_value=existing):
                snap = mgr.capture(
                    version="0.5.1",
                    graph_stats_dict={
                        "total_nodes": 110,
                        "total_edges": 160,
                        "meaningful_nodes": 88,
                        "node_counts": {},
                        "edge_counts": {},
                    },
                    coverage=0.87,
                    critical_issues=1,
                    complexity_median=3.7,
                )

    assert snap.vs_previous is not None
    assert snap.vs_previous.nodes == 10
    assert snap.vs_previous.edges == 10


def test_get_current_tree_hash_git_failure_returns_empty(snapshot_dir: Path) -> None:
    """_get_current_tree_hash returns '' when git is unavailable."""

    mgr = SnapshotManager(snapshot_dir)
    with patch("subprocess.check_output", side_effect=FileNotFoundError):
        result = mgr._get_current_tree_hash()
    assert result == ""


def test_get_current_branch_git_failure_returns_unknown(snapshot_dir: Path) -> None:
    """_get_current_branch returns 'unknown' when git is unavailable."""
    mgr = SnapshotManager(snapshot_dir)
    with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git")):
        result = mgr._get_current_branch()
    assert result == "unknown"


def test_load_snapshot_backfills_missing_vs_previous(snapshot_dir: Path) -> None:
    """load_snapshot computes vs_previous from manifest ordering when missing in file."""
    mgr = SnapshotManager(snapshot_dir)
    metrics_old = SnapshotMetrics(
        total_nodes=100,
        total_edges=150,
        meaningful_nodes=80,
        docstring_coverage=0.85,
        node_counts={},
        edge_counts={},
        critical_issues=2,
        complexity_median=3.5,
    )
    metrics_new = SnapshotMetrics(
        total_nodes=120,
        total_edges=170,
        meaningful_nodes=95,
        docstring_coverage=0.87,
        node_counts={},
        edge_counts={},
        critical_issues=1,
        complexity_median=3.8,
    )

    old_snap = Snapshot(
        branch="develop",
        timestamp="2026-03-07T10:00:00+00:00",
        version="0.5.0",
        metrics=metrics_old,
        tree_hash="older",
    )
    new_snap = Snapshot(
        branch="develop",
        timestamp="2026-03-07T12:00:00+00:00",
        version="0.5.1",
        metrics=metrics_new,
        tree_hash="newer",
    )

    mgr.save_snapshot(old_snap)
    mgr.save_snapshot(new_snap)

    loaded = mgr.load_snapshot("newer")
    assert loaded is not None
    assert loaded.vs_previous is not None
    assert loaded.vs_previous.nodes == 20
    assert loaded.vs_previous.edges == 20


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pycodekg_snapshot(tree_hash: str, timestamp: str, nodes: int = 10) -> Snapshot:
    metrics = SnapshotMetrics(
        total_nodes=nodes,
        total_edges=nodes * 2,
        meaningful_nodes=nodes,
        docstring_coverage=0.5,
        node_counts={},
        edge_counts={},
        critical_issues=0,
        complexity_median=1.0,
    )
    return Snapshot(
        branch="main", timestamp=timestamp, version="0.1.0", metrics=metrics, tree_hash=tree_hash
    )


# ---------------------------------------------------------------------------
# SnapshotManifest — from_dict missing keys
# ---------------------------------------------------------------------------


def test_snapshot_manifest_from_dict_missing_keys() -> None:
    """from_dict({}) should fall back to safe defaults without raising."""
    restored = SnapshotManifest.from_dict({})
    assert restored.format_version == "1.0"
    assert restored.last_update == ""
    assert restored.snapshots == []


# ---------------------------------------------------------------------------
# SnapshotManager — list_snapshots empty
# ---------------------------------------------------------------------------


def test_list_snapshots_empty(snapshot_dir: Path) -> None:
    """list_snapshots returns [] when no snapshots have been saved."""
    mgr = SnapshotManager(snapshot_dir)
    assert mgr.list_snapshots() == []


# ---------------------------------------------------------------------------
# SnapshotManager — capture does not auto-save
# ---------------------------------------------------------------------------


def test_capture_does_not_auto_save(snapshot_dir: Path) -> None:
    """capture() returns a Snapshot but does NOT persist it to disk."""
    mgr = SnapshotManager(snapshot_dir)
    with patch(
        "pycode_kg.snapshots.SnapshotManager._get_current_tree_hash", return_value="unsaved_hash"
    ):
        with patch("pycode_kg.snapshots.SnapshotManager._get_current_branch", return_value="main"):
            mgr.capture(version="0.1.0")
    assert mgr.load_snapshot("unsaved_hash") is None
    assert mgr.list_snapshots() == []


# ---------------------------------------------------------------------------
# SnapshotManager — diff coverage_delta
# ---------------------------------------------------------------------------


def test_diff_snapshots_coverage_delta(snapshot_dir: Path) -> None:
    """diff_snapshots includes coverage_delta and critical_issues_delta."""
    mgr = SnapshotManager(snapshot_dir)

    def _metrics(cov: float, issues: int) -> SnapshotMetrics:
        return SnapshotMetrics(
            total_nodes=50,
            total_edges=80,
            meaningful_nodes=50,
            docstring_coverage=cov,
            node_counts={},
            edge_counts={},
            critical_issues=issues,
            complexity_median=2.0,
        )

    s1 = Snapshot(
        branch="main",
        timestamp="2026-01-01T00:00:00+00:00",
        version="0.1.0",
        metrics=_metrics(0.60, 5),
        tree_hash="cov_a",
    )
    s2 = Snapshot(
        branch="main",
        timestamp="2026-02-01T00:00:00+00:00",
        version="0.2.0",
        metrics=_metrics(0.80, 2),
        tree_hash="cov_b",
    )
    mgr.save_snapshot(s1)
    mgr.save_snapshot(s2)

    result = mgr.diff_snapshots("cov_a", "cov_b")
    assert result["delta"]["coverage_delta"] == pytest.approx(0.20)
    assert result["delta"]["critical_issues_delta"] == -3


# ---------------------------------------------------------------------------
# SnapshotManager._compute_delta — negative regression
# ---------------------------------------------------------------------------


def test_compute_delta_negative_regression(snapshot_dir: Path) -> None:
    """Delta is negative when the new snapshot has fewer nodes/edges."""
    mgr = SnapshotManager(snapshot_dir)
    s_big = _make_pycodekg_snapshot("big", "2026-01-01T00:00:00+00:00", nodes=100)
    s_small = _make_pycodekg_snapshot("small", "2026-02-01T00:00:00+00:00", nodes=60)
    mgr.save_snapshot(s_big)
    mgr.save_snapshot(s_small)

    result = mgr.diff_snapshots("big", "small")
    assert result["delta"]["nodes"] == -40
    assert result["delta"]["edges"] < 0


# ---------------------------------------------------------------------------
# module_node_counts — collection and diff
# ---------------------------------------------------------------------------


def test_module_node_counts_default_empty() -> None:
    """SnapshotMetrics.module_node_counts defaults to empty dict."""
    m = SnapshotMetrics(
        total_nodes=10,
        total_edges=5,
        meaningful_nodes=8,
        docstring_coverage=0.5,
        node_counts={},
        edge_counts={},
        critical_issues=0,
        complexity_median=1.0,
    )
    assert m.module_node_counts == {}


def test_module_node_counts_from_dict_legacy() -> None:
    """from_dict on a legacy snapshot without module_node_counts deserializes cleanly."""
    data = {
        "key": "abc",
        "branch": "main",
        "timestamp": "2026-01-01T00:00:00+00:00",
        "version": "0.1.0",
        "metrics": {
            "total_nodes": 10,
            "total_edges": 5,
            "meaningful_nodes": 8,
            "docstring_coverage": 0.5,
            "node_counts": {},
            "edge_counts": {},
            "critical_issues": 0,
            "complexity_median": 1.0,
            # no module_node_counts key — legacy snapshot
        },
        "hotspots": [],
        "issues": [],
        "tree_hash": "abc",
        "vs_previous": None,
        "vs_baseline": None,
    }
    snap = Snapshot.from_dict(data)
    assert snap.metrics.module_node_counts == {}


def test_diff_snapshots_module_node_counts_delta(snapshot_dir: Path) -> None:
    """diff_snapshots returns module_node_counts_delta with only changed modules."""
    mgr = SnapshotManager(snapshot_dir)

    def _m(module_counts: dict) -> SnapshotMetrics:
        return SnapshotMetrics(
            total_nodes=sum(module_counts.values()),
            total_edges=10,
            meaningful_nodes=sum(module_counts.values()),
            docstring_coverage=0.8,
            node_counts={},
            edge_counts={},
            critical_issues=0,
            complexity_median=1.0,
            module_node_counts=module_counts,
        )

    s1 = Snapshot(
        branch="main",
        timestamp="2026-01-01T00:00:00+00:00",
        version="0.1.0",
        metrics=_m({"src/a.py": 5, "src/b.py": 10}),
        tree_hash="mod_a",
    )
    s2 = Snapshot(
        branch="main",
        timestamp="2026-02-01T00:00:00+00:00",
        version="0.2.0",
        metrics=_m({"src/a.py": 5, "src/b.py": 12, "src/c.py": 3}),
        tree_hash="mod_b",
    )
    mgr.save_snapshot(s1)
    mgr.save_snapshot(s2)

    result = mgr.diff_snapshots("mod_a", "mod_b")
    delta = result["module_node_counts_delta"]

    # src/a.py unchanged — must not appear
    assert "src/a.py" not in delta
    # src/b.py grew by 2
    assert delta["src/b.py"] == 2
    # src/c.py is new
    assert delta["src/c.py"] == 3


def test_collect_module_node_counts_no_db(snapshot_dir: Path) -> None:
    """_collect_module_node_counts returns {} when no db_path is set."""
    mgr = SnapshotManager(snapshot_dir)
    assert mgr._collect_module_node_counts() == {}


def test_collect_module_node_counts_missing_db(snapshot_dir: Path, tmp_path: Path) -> None:
    """_collect_module_node_counts returns {} when db_path does not exist."""
    mgr = SnapshotManager(snapshot_dir, db_path=tmp_path / "nonexistent.sqlite")
    assert mgr._collect_module_node_counts() == {}


def test_collect_module_node_counts_from_sqlite(snapshot_dir: Path, tmp_path: Path) -> None:
    """_collect_module_node_counts queries SQLite and returns per-module counts."""
    import sqlite3

    db = tmp_path / "graph.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE nodes (module_path TEXT)")
        conn.executemany(
            "INSERT INTO nodes VALUES (?)",
            [
                ("src/a.py",),
                ("src/a.py",),
                ("src/b.py",),
                ("src/b.py",),
                ("src/b.py",),
                (None,),  # null module_path should be ignored
            ],
        )
    mgr = SnapshotManager(snapshot_dir, db_path=db)
    counts = mgr._collect_module_node_counts()
    assert counts == {"src/a.py": 2, "src/b.py": 3}


# ---------------------------------------------------------------------------
# Typed-property layer: Snapshot.metrics / .vs_previous / .vs_baseline
# ---------------------------------------------------------------------------


def test_snapshot_metrics_property_returns_typed_dataclass(sample_metrics: SnapshotMetrics) -> None:
    """Snapshot.metrics must return a SnapshotMetrics dataclass, not a raw dict."""
    snap = Snapshot(
        branch="main",
        timestamp="2026-01-01T00:00:00+00:00",
        version="1.0",
        metrics=sample_metrics,
        tree_hash="h1",
    )
    assert isinstance(snap.metrics, SnapshotMetrics)
    assert snap.metrics.total_nodes == sample_metrics.total_nodes
    assert snap.metrics.docstring_coverage == pytest.approx(sample_metrics.docstring_coverage)


def test_snapshot_vs_previous_property_returns_typed_delta() -> None:
    """Snapshot.vs_previous must return a SnapshotDelta, not a raw dict."""
    delta_dict = {"nodes": 5, "edges": 10, "coverage_delta": 0.05, "critical_issues_delta": -1}
    snap = Snapshot(
        branch="main",
        timestamp="2026-01-01T00:00:00+00:00",
        version="1.0",
        metrics=SnapshotMetrics(
            total_nodes=10,
            total_edges=20,
            meaningful_nodes=8,
            docstring_coverage=0.9,
            node_counts={},
            edge_counts={},
            critical_issues=0,
            complexity_median=1.0,
        ),
        tree_hash="h1",
        vs_previous=delta_dict,
    )
    assert isinstance(snap.vs_previous, SnapshotDelta)
    assert snap.vs_previous.nodes == 5
    assert snap.vs_previous.coverage_delta == pytest.approx(0.05)
    assert snap.vs_previous.critical_issues_delta == -1


def test_snapshot_vs_baseline_none_when_unset() -> None:
    """Snapshot.vs_baseline must be None when not provided."""
    snap = Snapshot(
        branch="main",
        timestamp="2026-01-01T00:00:00+00:00",
        version="1.0",
        metrics=SnapshotMetrics(
            total_nodes=10,
            total_edges=20,
            meaningful_nodes=8,
            docstring_coverage=0.9,
            node_counts={},
            edge_counts={},
            critical_issues=0,
            complexity_median=1.0,
        ),
        tree_hash="h1",
    )
    assert snap.vs_baseline is None


def test_snapshot_metrics_setter_accepts_dict() -> None:
    """Setting Snapshot.metrics to a plain dict stores it transparently."""
    snap = Snapshot(
        branch="main",
        timestamp="2026-01-01T00:00:00+00:00",
        version="1.0",
        metrics={
            "total_nodes": 5,
            "total_edges": 8,
            "meaningful_nodes": 4,
            "docstring_coverage": 0.5,
            "node_counts": {},
            "edge_counts": {},
            "critical_issues": 0,
            "complexity_median": 0.0,
            "module_node_counts": {},
        },
        tree_hash="h1",
    )
    assert isinstance(snap.metrics, SnapshotMetrics)
    assert snap.metrics.total_nodes == 5


# ---------------------------------------------------------------------------
# save_snapshot dedup and force
# ---------------------------------------------------------------------------


def _minimal_snap(
    mgr: SnapshotManager, *, nodes: int, tree_hash: str, version: str = "1.0", branch: str = "main"
) -> Snapshot:
    return mgr.capture(
        version=version,
        branch=branch,
        tree_hash=tree_hash,
        graph_stats_dict={
            "total_nodes": nodes,
            "total_edges": nodes * 2,
            "meaningful_nodes": nodes,
            "node_counts": {},
            "edge_counts": {},
        },
    )


def test_save_dedup_refresh_same_version_same_metrics(snapshot_dir: Path) -> None:
    """Saving identical version+metrics under a new hash refreshes the manifest entry."""
    mgr = SnapshotManager(snapshot_dir)
    s1 = _minimal_snap(mgr, nodes=100, tree_hash="h1")
    mgr.save_snapshot(s1)
    s2 = _minimal_snap(mgr, nodes=100, tree_hash="h2")  # same metrics
    mgr.save_snapshot(s2)
    manifest = mgr.load_manifest()
    assert len(manifest.snapshots) == 1, "dedup must keep only one entry"
    assert manifest.snapshots[0]["key"] == "h2"


def test_save_force_bypasses_dedup(snapshot_dir: Path) -> None:
    """save_snapshot(force=True) always creates a new manifest entry."""
    mgr = SnapshotManager(snapshot_dir)
    s1 = _minimal_snap(mgr, nodes=100, tree_hash="h1")
    mgr.save_snapshot(s1)
    s2 = _minimal_snap(mgr, nodes=100, tree_hash="h2")
    mgr.save_snapshot(s2, force=True)
    assert len(mgr.load_manifest().snapshots) == 2


def test_save_different_metrics_creates_new_entry(snapshot_dir: Path) -> None:
    """Changing any metric (nodes, coverage, etc.) must produce a new history entry."""
    mgr = SnapshotManager(snapshot_dir)
    s1 = _minimal_snap(mgr, nodes=100, tree_hash="h1")
    mgr.save_snapshot(s1)
    s2 = _minimal_snap(mgr, nodes=150, tree_hash="h2")  # node count changed
    mgr.save_snapshot(s2)
    assert len(mgr.load_manifest().snapshots) == 2


# ---------------------------------------------------------------------------
# prune_snapshots
# ---------------------------------------------------------------------------


def _save_seq(mgr: SnapshotManager, specs: list[dict]) -> None:
    """Save a sequence of snapshots from spec dicts (nodes, tree_hash, version)."""
    for spec in specs:
        snap = Snapshot(
            branch="main",
            timestamp=spec["ts"],
            version=spec.get("version", "1.0"),
            metrics=SnapshotMetrics(
                total_nodes=spec["nodes"],
                total_edges=spec["nodes"] * 2,
                meaningful_nodes=spec["nodes"],
                docstring_coverage=0.8,
                node_counts={},
                edge_counts={},
                critical_issues=0,
                complexity_median=1.0,
            ),
            tree_hash=spec["hash"],
        )
        mgr.save_snapshot(snap, force=True)


def test_prune_dry_run_changes_nothing(snapshot_dir: Path) -> None:
    """prune_snapshots(dry_run=True) must not delete any files or manifest entries."""
    mgr = SnapshotManager(snapshot_dir)
    _save_seq(
        mgr,
        [
            {"nodes": 100, "hash": "h0", "ts": "2026-01-01T00:00:00+00:00"},
            {"nodes": 100, "hash": "h1", "ts": "2026-01-02T00:00:00+00:00"},  # duplicate
            {"nodes": 200, "hash": "h2", "ts": "2026-01-03T00:00:00+00:00"},
        ],
    )
    result = mgr.prune_snapshots(dry_run=True)
    assert result.dry_run is True
    assert len(mgr.load_manifest().snapshots) == 3, "dry_run must not mutate manifest"


def test_prune_removes_metric_duplicate_interior(snapshot_dir: Path) -> None:
    """Metric-duplicate interior entries (same nodes+edges as predecessor) are pruned."""
    mgr = SnapshotManager(snapshot_dir)
    _save_seq(
        mgr,
        [
            {"nodes": 100, "hash": "h0", "ts": "2026-01-01T00:00:00+00:00"},
            {"nodes": 100, "hash": "h1", "ts": "2026-01-02T00:00:00+00:00"},  # duplicate interior
            {"nodes": 200, "hash": "h2", "ts": "2026-01-03T00:00:00+00:00"},
        ],
    )
    result = mgr.prune_snapshots()
    assert "h1" in result.removed
    keys = {e["key"] for e in mgr.load_manifest().snapshots}
    assert "h1" not in keys
    assert "h0" in keys  # baseline preserved
    assert "h2" in keys  # latest preserved


def test_prune_preserves_baseline_and_latest(snapshot_dir: Path) -> None:
    """Baseline (oldest) and latest entries are never pruned even if metrics match."""
    mgr = SnapshotManager(snapshot_dir)
    _save_seq(
        mgr,
        [
            {"nodes": 100, "hash": "base", "ts": "2026-01-01T00:00:00+00:00"},
            {"nodes": 100, "hash": "last", "ts": "2026-01-02T00:00:00+00:00"},
        ],
    )
    result = mgr.prune_snapshots()
    assert "base" not in result.removed
    assert "last" not in result.removed


def test_prune_removes_orphaned_json_files(snapshot_dir: Path) -> None:
    """JSON files in the snapshots directory with no manifest entry must be deleted."""
    mgr = SnapshotManager(snapshot_dir)
    _save_seq(mgr, [{"nodes": 100, "hash": "h0", "ts": "2026-01-01T00:00:00+00:00"}])
    orphan = mgr.snapshots_dir / "orphan_deadbeef.json"
    orphan.write_text('{"key": "orphan"}')
    result = mgr.prune_snapshots()
    assert "orphan_deadbeef.json" in result.orphaned_files
    assert not orphan.exists()


def test_prune_cleans_broken_manifest_entries(snapshot_dir: Path) -> None:
    """Manifest entries whose JSON file is missing are marked broken and removed."""
    mgr = SnapshotManager(snapshot_dir)
    _save_seq(mgr, [{"nodes": 100, "hash": "h0", "ts": "2026-01-01T00:00:00+00:00"}])
    manifest = mgr.load_manifest()
    manifest.snapshots.append(
        {
            "key": "ghost",
            "branch": "main",
            "timestamp": "2020-01-01T00:00:00+00:00",
            "file": "ghost.json",
            "version": "0.1",
            "metrics": {},
        }
    )
    mgr._save_manifest(manifest)
    result = mgr.prune_snapshots()
    assert "ghost" in result.broken_entries


# ---------------------------------------------------------------------------
# diff_snapshots — issues_delta (introduced / resolved)
# ---------------------------------------------------------------------------


def test_diff_snapshots_issues_delta_introduced(snapshot_dir: Path) -> None:
    """diff_snapshots must report issues present in B but not A as 'introduced'."""
    mgr = SnapshotManager(snapshot_dir)

    def _snap_with_issues(nodes, tree_hash, ts, issues):
        snap = Snapshot(
            branch="main",
            timestamp=ts,
            version="1.0",
            metrics=SnapshotMetrics(
                total_nodes=nodes,
                total_edges=nodes * 2,
                meaningful_nodes=nodes,
                docstring_coverage=0.9,
                node_counts={},
                edge_counts={},
                critical_issues=len(issues),
                complexity_median=1.0,
            ),
            tree_hash=tree_hash,
            issues=issues,
        )
        mgr.save_snapshot(snap, force=True)
        return snap

    _snap_with_issues(100, "a", "2026-01-01T00:00:00+00:00", ["orphan module: foo"])
    _snap_with_issues(
        120, "b", "2026-01-02T00:00:00+00:00", ["orphan module: foo", "high coupling: bar"]
    )

    diff = mgr.diff_snapshots("a", "b")
    assert "issues_delta" in diff
    assert "high coupling: bar" in diff["issues_delta"]["introduced"]
    assert "orphan module: foo" not in diff["issues_delta"]["introduced"]


def test_diff_snapshots_issues_delta_resolved(snapshot_dir: Path) -> None:
    """diff_snapshots must report issues present in A but not B as 'resolved'."""
    mgr = SnapshotManager(snapshot_dir)

    def _snap_with_issues(nodes, tree_hash, ts, issues):
        snap = Snapshot(
            branch="main",
            timestamp=ts,
            version="1.0",
            metrics=SnapshotMetrics(
                total_nodes=nodes,
                total_edges=nodes * 2,
                meaningful_nodes=nodes,
                docstring_coverage=0.9,
                node_counts={},
                edge_counts={},
                critical_issues=len(issues),
                complexity_median=1.0,
            ),
            tree_hash=tree_hash,
            issues=issues,
        )
        mgr.save_snapshot(snap, force=True)

    _snap_with_issues(
        100, "a", "2026-01-01T00:00:00+00:00", ["orphan module: foo", "high coupling: bar"]
    )
    _snap_with_issues(120, "b", "2026-01-02T00:00:00+00:00", ["orphan module: foo"])

    diff = mgr.diff_snapshots("a", "b")
    assert "high coupling: bar" in diff["issues_delta"]["resolved"]
    assert "orphan module: foo" not in diff["issues_delta"]["resolved"]


# ---------------------------------------------------------------------------
# Key scheme (kgmodule-utils >= 0.19.0)
# ---------------------------------------------------------------------------


def test_capture_does_not_key_on_the_tree_hash(snapshot_dir: Path) -> None:
    """The tree hash is provenance, not an identifier.

    It is read before ``git add`` stages the snapshot, so it names a tree that
    is never committed.
    """
    mgr = SnapshotManager(snapshot_dir)
    snap = mgr.capture(
        version="0.25.0",
        branch="main",
        graph_stats_dict={"total_nodes": 3, "total_edges": 2},
        tree_hash="a" * 40,
    )
    assert snap.key != "a" * 40
    assert snap.tree_hash == "a" * 40


def test_capture_forwards_an_explicit_release_key(snapshot_dir: Path) -> None:
    mgr = SnapshotManager(snapshot_dir)
    snap = mgr.capture(
        version="0.25.0",
        branch="main",
        graph_stats_dict={"total_nodes": 3, "total_edges": 2},
        key="v0.25.0",
        subject="repo:pycode-kg",
    )
    assert snap.key == "v0.25.0"
    assert snap.subject == "repo:pycode-kg"


def test_to_dict_is_not_overridden_and_uses_the_current_key(snapshot_dir: Path) -> None:
    """The base to_dict is what supplies the key scheme.

    An override here would keep writing tree-hash keys no matter what the SDK
    does, which is the reason this class no longer has one.
    """
    assert "to_dict" not in Snapshot.__dict__

    mgr = SnapshotManager(snapshot_dir)
    snap = mgr.capture(
        version="0.25.0",
        branch="main",
        graph_stats_dict={"total_nodes": 3, "total_edges": 2},
        coverage=0.5,
        key="v0.25.0",
    )
    d = snap.to_dict()
    assert d["key"] == "v0.25.0"
    assert d["metrics"]["docstring_coverage"] == 0.5  # typed property still serializes
