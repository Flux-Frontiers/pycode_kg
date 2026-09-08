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
    collects the pycode-kg metric fields in ``_domain_metrics()``, adds
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

    Subclasses the shared ``kg_utils.snapshots.SnapshotManager``. Three of the
    four additions are class attributes rather than methods, because the base
    supplies the behaviour and this module only names the domain values:

    * ``package_name = "pycode-kg"`` for version detection.
    * ``dict_metric_deltas`` naming ``module_node_counts``, which the base
      turns into ``module_node_counts_delta`` in ``diff_snapshots``.
    * ``_domain_metrics()`` collecting per-module node counts at capture time.
    * ``_compute_delta_from_metrics`` extended with ``coverage_delta`` and
      ``critical_issues_delta`` — the one genuinely domain-specific method.
    * ``_collect_module_node_counts()`` — SQLite per-module node counts.

    Everything else -- capture, saving, loading, listing, pruning, diffing, key
    handling -- is inherited unchanged. Overriding those is what this module
    used to do, and is what let the 0.25.0 snapshot key regression through.

    Note that ``capture()`` takes the coverage fraction as
    ``docstring_coverage``, the name it is stored under. Until 0.27.0 this
    class overrode ``capture()`` to accept it as ``coverage`` and rename it on
    the way through; that override is gone, and with it the signature-restating
    pattern that let a ``key=`` go missing. ``coverage=`` still works and warns
    -- see ``capture_aliases`` below.
    """

    #: Version detection reads this; the base uses it as the snapshot's ``tool``.
    package_name = "pycode-kg"

    #: ``diff_snapshots`` emits ``module_node_counts_delta`` from this, holding
    #: only the modules whose node count actually changed.
    dict_metric_deltas = ("module_node_counts",)

    #: Until 0.27.0 this class overrode ``capture()`` to accept the docstring
    #: coverage fraction as ``coverage`` and rename it on the way through. The
    #: override is gone, and the stored name is the only name. Without this
    #: entry a caller still passing ``coverage=`` would get no error: the base
    #: ``**extra_metrics`` would record a ``coverage`` metric nobody reads and
    #: leave ``docstring_coverage`` absent.
    capture_aliases = {"coverage": "docstring_coverage"}

    # ------------------------------------------------------------------
    # Capture-time metrics collected by this module
    # ------------------------------------------------------------------

    def _domain_metrics(self, stats: dict[str, Any]) -> dict[str, Any]:
        """Collect the metrics this module gathers for itself.

        Called by the inherited ``capture()``. Overriding this rather than
        ``capture()`` is deliberate: a ``capture()`` override has to restate the
        base signature, and restating it is what let ``key=`` fall into
        ``**extra_metrics`` and ship 0.25.0 with every snapshot keyed on a tree
        hash.

        :param stats: Graph stats passed to ``capture()``; unused here, the
            counts come from SQLite.
        :return: ``{"module_node_counts": {module_path: node_count}}``, empty
                 if no SQLite graph is configured.
        """
        return {"module_node_counts": self._collect_module_node_counts()}

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
