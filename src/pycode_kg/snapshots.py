"""
snapshots.py — Temporal Snapshots of PyCodeKG Metrics

Thin layer over the shared ``kg_utils.snapshots`` module.

``Snapshot``, ``SnapshotManifest`` and ``PruneResult`` are re-exported from
``kg_utils.snapshots`` unchanged.  A snapshot's ``metrics``, ``vs_previous``
and ``vs_baseline`` are plain dicts, which is what the shared manager reads
and writes.

This module adds:

  - ``SnapshotMetrics`` / ``SnapshotDelta`` — domain dataclasses, used as
    converters by callers that want attribute access.  Convert with
    ``metrics_from_dict`` / ``metrics_to_dict`` and ``delta_from_dict`` /
    ``delta_to_dict``; a ``Snapshot`` never holds one.
  - a ``SnapshotManager`` subclass that sets ``package_name="pycode-kg"``,
    names the pycode-kg metric fields in ``capture()``, adds
    ``coverage_delta`` and ``critical_issues_delta`` to deltas, collects
    per-module node counts from SQLite, and extends a diff with
    ``module_node_counts_delta``, ``issues_delta`` and ``timestamp``.

Do not subclass ``Snapshot`` here.  A subclass that exposes ``metrics``,
``vs_previous`` or ``vs_baseline`` as properties breaks every shared manager
method that reads those fields by attribute, and each one then needs a
hand-written copy.  One such copy dropped ``snapshot_key``, ``subject`` and
``tool`` on the way to disk, which shipped in 0.25.0.

Usage
-----
>>> from pycode_kg.snapshots import SnapshotManager, metrics_from_dict
>>> mgr = SnapshotManager(".pycodekg/snapshots")
>>> snapshot = mgr.capture(version="0.5.1", key="v0.5.1", subject="repo:pycode-kg")
>>> mgr.save_snapshot(snapshot)
>>> metrics_from_dict(snapshot.metrics).docstring_coverage
0.0

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Re-export shared base types (backwards-compat public API)
# ---------------------------------------------------------------------------
from kg_utils.snapshots import (
    PruneResult,  # noqa: F401  re-exported
    Snapshot,  # noqa: F401  re-exported
    SnapshotManifest,  # noqa: F401  re-exported
)
from kg_utils.snapshots import SnapshotManager as _BaseSnapshotManager

__all__ = [
    "SnapshotMetrics",
    "SnapshotDelta",
    "Snapshot",
    "SnapshotManifest",
    "SnapshotManager",
    "PruneResult",
    "metrics_to_dict",
    "metrics_from_dict",
    "delta_to_dict",
    "delta_from_dict",
]


# ---------------------------------------------------------------------------
# Domain-specific dataclasses (used by CLI and tests)
# ---------------------------------------------------------------------------


@dataclass
class SnapshotMetrics:
    """Core metrics captured in a pycode-kg snapshot."""

    total_nodes: int
    total_edges: int
    meaningful_nodes: int
    docstring_coverage: float  # 0.0 to 1.0
    node_counts: dict[str, int]
    edge_counts: dict[str, int]
    critical_issues: int
    complexity_median: float  # median fan-in across functions
    module_node_counts: dict[str, int] = field(default_factory=dict)
    coverage_documented: int = 0  # nodes with a docstring
    coverage_total: int = 0  # nodes eligible for docstring coverage


@dataclass
class SnapshotDelta:
    """Deltas comparing this snapshot to a baseline or previous snapshot."""

    nodes: int = 0
    edges: int = 0
    coverage_delta: float = 0.0
    critical_issues_delta: int = 0


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def metrics_to_dict(m: SnapshotMetrics) -> dict[str, Any]:
    """Convert a ``SnapshotMetrics`` dataclass to a plain dict."""
    return {
        "total_nodes": m.total_nodes,
        "total_edges": m.total_edges,
        "meaningful_nodes": m.meaningful_nodes,
        "docstring_coverage": m.docstring_coverage,
        "node_counts": m.node_counts,
        "edge_counts": m.edge_counts,
        "critical_issues": m.critical_issues,
        "complexity_median": m.complexity_median,
        "module_node_counts": m.module_node_counts,
        "coverage_documented": m.coverage_documented,
        "coverage_total": m.coverage_total,
    }


def metrics_from_dict(d: dict[str, Any]) -> SnapshotMetrics:
    """Reconstruct a ``SnapshotMetrics`` dataclass from a plain dict."""
    return SnapshotMetrics(
        total_nodes=int(d.get("total_nodes", 0)),
        total_edges=int(d.get("total_edges", 0)),
        meaningful_nodes=int(d.get("meaningful_nodes", 0)),
        docstring_coverage=float(d.get("docstring_coverage", 0.0)),
        node_counts=d.get("node_counts", {}),
        edge_counts=d.get("edge_counts", {}),
        critical_issues=int(d.get("critical_issues", 0)),
        complexity_median=float(d.get("complexity_median", 0.0)),
        module_node_counts=d.get("module_node_counts", {}),
        coverage_documented=int(d.get("coverage_documented", 0)),
        coverage_total=int(d.get("coverage_total", 0)),
    )


def delta_to_dict(delta: SnapshotDelta | None) -> dict[str, Any] | None:
    """Convert a ``SnapshotDelta`` to a plain dict, or return None."""
    if delta is None:
        return None
    return {
        "nodes": delta.nodes,
        "edges": delta.edges,
        "coverage_delta": delta.coverage_delta,
        "critical_issues_delta": delta.critical_issues_delta,
    }


def delta_from_dict(d: dict[str, Any] | None) -> SnapshotDelta | None:
    """Reconstruct a ``SnapshotDelta`` from a plain dict, or return None."""
    if d is None:
        return None
    return SnapshotDelta(
        nodes=int(d.get("nodes", 0)),
        edges=int(d.get("edges", 0)),
        coverage_delta=float(d.get("coverage_delta", 0.0)),
        critical_issues_delta=int(d.get("critical_issues_delta", 0)),
    )


# ---------------------------------------------------------------------------
# SnapshotManager — pycode-kg specialisation of the shared manager
# ---------------------------------------------------------------------------


class SnapshotManager(_BaseSnapshotManager):
    """pycode-kg snapshot manager.

    Subclasses the shared ``kg_utils.snapshots.SnapshotManager`` and adds:

    * ``package_name="pycode-kg"`` default for version detection.
    * A ``capture()`` naming the pycode-kg metric fields (``coverage``,
      ``critical_issues``, ``complexity_median`` and the coverage numerator
      and denominator) and collecting per-module node counts.
    * ``_compute_delta_from_metrics`` extended with ``coverage_delta`` and
      ``critical_issues_delta``.
    * ``diff_snapshots`` extended with ``module_node_counts_delta``,
      ``issues_delta`` and ``timestamp``.
    * ``_collect_module_node_counts()`` — SQLite per-module node counts.

    Everything else -- saving, loading, listing, pruning, key handling -- is
    inherited unchanged.  Overriding those to convert between dicts and the
    domain dataclasses is what this module used to do, and is what let the
    0.25.0 snapshot key regression through.
    """

    def __init__(
        self,
        snapshots_dir: Path | str,
        *,
        db_path: Path | str | None = None,
        package_name: str = "pycode-kg",
    ) -> None:
        """Initialize the manager rooted at ``snapshots_dir``.

        :param snapshots_dir: Directory where snapshot JSON files live; created
            on first save if it does not exist.
        :param db_path: PyCodeKG SQLite graph path; required for collecting
            per-module node counts during ``capture()``. Optional otherwise.
        :param package_name: Package name used for version detection in saved
            snapshots. Defaults to ``"pycode-kg"``.
        """
        super().__init__(snapshots_dir, package_name=package_name, db_path=db_path)

    # ------------------------------------------------------------------
    # capture — name the pycode-kg metric fields
    # ------------------------------------------------------------------

    def capture(  # ty: ignore[invalid-method-override]
        self,
        version: str | None = None,
        branch: str | None = None,
        graph_stats_dict: dict[str, Any] | None = None,
        coverage: float = 0.0,
        coverage_documented: int = 0,
        coverage_total: int = 0,
        critical_issues: int = 0,
        complexity_median: float = 0.0,
        hotspots: list[dict[str, Any]] | None = None,
        issues: list[str] | None = None,
        tree_hash: str = "",
        key: str = "",
        subject: str = "",
    ) -> Snapshot:
        """Capture a pycode-kg snapshot.

        Names the pycode-kg metric fields explicitly rather than taking them
        through ``**extra_metrics``, and adds per-module node counts, then
        delegates to the shared implementation.

        :param version: Version string (e.g., "0.5.1").
        :param branch: Git branch name; auto-detected if None.
        :param graph_stats_dict: Output from ``graph_stats()`` / ``store.stats()``.
        :param coverage: Docstring coverage fraction (0.0-1.0).
        :param coverage_documented: Nodes with a non-empty docstring — the
            numerator behind ``coverage``.  Shown beside the percentage in
            Snapshot History so a coverage drop caused by adding undocumented
            nodes reads differently from one caused by removing docstrings.
        :param coverage_total: Nodes eligible for docstring coverage — the
            denominator behind ``coverage``.
        :param critical_issues: Number of critical issues detected.
        :param complexity_median: Median fan-in across functions.
        :param hotspots: Top hotspot entries.
        :param issues: Issue description strings.
        :param tree_hash: Git tree hash, recorded as provenance; auto-detected
            if not provided. It is not the snapshot's key.
        :param key: Snapshot identifier. Pass the release tag at release time;
            omit it and the base assigns a UTC timestamp.
        :param subject: What was measured, e.g. ``repo:pycode-kg``.
        :return: New :class:`~kg_utils.snapshots.Snapshot` (not yet persisted).
        """
        return super().capture(
            version=version,
            branch=branch,
            graph_stats_dict=graph_stats_dict,
            tree_hash=tree_hash,
            key=key,
            subject=subject,
            hotspots=hotspots,
            issues=issues,
            docstring_coverage=coverage,
            coverage_documented=coverage_documented,
            coverage_total=coverage_total,
            critical_issues=critical_issues,
            complexity_median=complexity_median,
            module_node_counts=self._collect_module_node_counts(),
        )

    # ------------------------------------------------------------------
    # diff_snapshots — adds module_node_counts_delta, issues_delta, timestamp
    # ------------------------------------------------------------------

    def diff_snapshots(self, key_a: str, key_b: str) -> dict[str, Any]:
        """Compare two snapshots side-by-side.

        Extends the shared diff with ``module_node_counts_delta``,
        ``issues_delta`` (introduced / resolved issue strings) and the
        ``timestamp`` of each side, which the CLI prints.

        :param key_a: Earlier snapshot key.
        :param key_b: Later snapshot key.
        :return: The shared diff result with the pycode-kg additions.
        """
        result = super().diff_snapshots(key_a, key_b)
        if "error" in result:
            return result

        for side, key in (("a", key_a), ("b", key_b)):
            snap = self.load_snapshot(key)
            if snap is not None:
                result[side]["timestamp"] = snap.timestamp

        m_a: dict[str, Any] = result["a"]["metrics"]
        m_b: dict[str, Any] = result["b"]["metrics"]
        counts_a: dict[str, int] = m_a.get("module_node_counts", {})
        counts_b: dict[str, int] = m_b.get("module_node_counts", {})
        result["module_node_counts_delta"] = {
            mod: counts_b.get(mod, 0) - counts_a.get(mod, 0)
            for mod in set(counts_a) | set(counts_b)
            if counts_b.get(mod, 0) != counts_a.get(mod, 0)
        }

        issues_a = set(result["a"]["issues"])
        issues_b = set(result["b"]["issues"])
        result["issues_delta"] = {
            "introduced": list(issues_b - issues_a),
            "resolved": list(issues_a - issues_b),
        }
        return result

    # ------------------------------------------------------------------
    # Delta computation — adds coverage_delta and critical_issues_delta
    # ------------------------------------------------------------------

    def _compute_delta_from_metrics(
        self, new_m: dict[str, Any], old_m: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute delta dict including pycode-kg specific fields."""
        return {
            "nodes": new_m.get("total_nodes", 0) - old_m.get("total_nodes", 0),
            "edges": new_m.get("total_edges", 0) - old_m.get("total_edges", 0),
            "coverage_delta": (
                new_m.get("docstring_coverage", 0.0) - old_m.get("docstring_coverage", 0.0)
            ),
            "critical_issues_delta": (
                new_m.get("critical_issues", 0) - old_m.get("critical_issues", 0)
            ),
        }

    # ------------------------------------------------------------------
    # SQLite per-module node counts
    # ------------------------------------------------------------------

    def _collect_module_node_counts(self) -> dict[str, int]:
        """Query SQLite for per-module node counts.

        :return: Dict mapping ``module_path`` to node count, or ``{}`` if the
                 database is unavailable or the query fails.
        """
        if not self.db_path or not self.db_path.exists():
            return {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute(
                    "SELECT module_path, COUNT(*) FROM nodes GROUP BY module_path"
                ).fetchall()
            return {row[0]: row[1] for row in rows if row[0]}
        except sqlite3.Error:
            return {}
