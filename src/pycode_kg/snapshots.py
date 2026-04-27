"""
snapshots.py — Temporal Snapshots of PyCodeKG Metrics

Thin compatibility layer over the shared ``kg_utils.snapshots`` module.

The shared module provides canonical ``Snapshot``, ``SnapshotManifest``, and
``SnapshotManager`` backed by free-form dicts.  This module re-exports those
types and adds:

  - ``SnapshotMetrics`` — domain-specific dataclass (used by CLI and tests)
  - ``SnapshotDelta``   — domain-specific dataclass (used by CLI and tests)
  - ``SnapshotManager`` subclass that:
      * sets ``package_name="pycode-kg"`` by default
      * overrides ``capture()`` to accept the legacy per-field kwargs
        (``coverage``, ``critical_issues``, ``complexity_median``) and
        build the structured ``metrics`` dict
      * overrides ``_compute_delta_from_metrics`` to include
        ``coverage_delta`` and ``critical_issues_delta``
      * adds ``_collect_module_node_counts()`` — SQLite per-module counts
  - ``metrics_to_dict`` / ``metrics_from_dict`` — helpers for converting
    between ``SnapshotMetrics`` dataclass and the underlying dict
  - ``delta_to_dict`` / ``delta_from_dict`` — same for ``SnapshotDelta``

``Snapshot`` is re-exported from ``kg_utils.snapshots``.  For backwards
compatibility ``snapshot.metrics`` returns a ``SnapshotMetrics``-shaped
view object when the snapshot was constructed via this module's helpers.

Usage
-----
>>> from pycode_kg.snapshots import SnapshotManager
>>> mgr = SnapshotManager(".pycodekg/snapshots")
>>> snapshot = mgr.capture("v0.5.1", "develop", graph_stats_dict)
>>> mgr.save_snapshot(snapshot)
>>> manifest = mgr.load_manifest()
>>> prev = mgr.get_previous(tree_hash)

Author: Eric G. Suchanek, PhD
Last Revision: 2026-04-27

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
    SnapshotManifest,  # noqa: F401  re-exported
)
from kg_utils.snapshots import Snapshot as _BaseSnapshot
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
# Snapshot — thin compatibility wrapper around the shared dict-based model
# ---------------------------------------------------------------------------


class Snapshot(_BaseSnapshot):
    """pycode-kg Snapshot with attribute-style access to metrics and deltas.

    Extends the shared ``kg_utils.snapshots.Snapshot`` (which stores metrics
    as a free-form dict) with ``@property`` accessors that return the typed
    ``SnapshotMetrics`` and ``SnapshotDelta`` objects that the CLI and tests
    expect.

    The underlying ``metrics``, ``vs_previous``, and ``vs_baseline`` fields
    remain plain dicts on disk; the properties are view-only adapters.

    Implementation note
    -------------------
    Python dataclass fields are stored in ``__dict__`` under their field name.
    The properties below always read and write the raw dict stored in
    ``self.__dict__`` directly so that the shared base-class infrastructure
    (which expects plain dicts) continues to work without modification.
    """

    @property  # type: ignore[override]
    def metrics(self) -> SnapshotMetrics:  # type: ignore[override]
        """Return metrics as a ``SnapshotMetrics`` dataclass view."""
        return metrics_from_dict(self.__dict__["metrics"])

    @metrics.setter
    def metrics(self, value: SnapshotMetrics | dict[str, Any]) -> None:
        if isinstance(value, SnapshotMetrics):
            self.__dict__["metrics"] = metrics_to_dict(value)
        else:
            self.__dict__["metrics"] = value

    @property  # type: ignore[override]
    def vs_previous(self) -> SnapshotDelta | None:  # type: ignore[override]
        """Return vs_previous as a ``SnapshotDelta`` dataclass view."""
        return delta_from_dict(self.__dict__["vs_previous"])

    @vs_previous.setter
    def vs_previous(self, value: SnapshotDelta | dict[str, Any] | None) -> None:
        if isinstance(value, SnapshotDelta):
            self.__dict__["vs_previous"] = delta_to_dict(value)
        else:
            self.__dict__["vs_previous"] = value

    @property  # type: ignore[override]
    def vs_baseline(self) -> SnapshotDelta | None:  # type: ignore[override]
        """Return vs_baseline as a ``SnapshotDelta`` dataclass view."""
        return delta_from_dict(self.__dict__["vs_baseline"])

    @vs_baseline.setter
    def vs_baseline(self, value: SnapshotDelta | dict[str, Any] | None) -> None:
        if isinstance(value, SnapshotDelta):
            self.__dict__["vs_baseline"] = delta_to_dict(value)
        else:
            self.__dict__["vs_baseline"] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to a JSON-serializable dictionary."""
        return {
            "key": self.tree_hash,
            "branch": self.branch,
            "timestamp": self.timestamp,
            "version": self.version,
            "metrics": self.__dict__["metrics"],
            "hotspots": self.hotspots,
            "issues": self.issues,
            "vs_previous": self.__dict__["vs_previous"],
            "vs_baseline": self.__dict__["vs_baseline"],
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Snapshot:  # type: ignore[override]
        """Reconstruct a pycode-kg ``Snapshot`` from a dictionary."""
        base = _BaseSnapshot.from_dict(data)
        return _rewrap(base)


# ---------------------------------------------------------------------------
# SnapshotManager — pycode-kg specialisation of the shared manager
# ---------------------------------------------------------------------------


class SnapshotManager(_BaseSnapshotManager):
    """pycode-kg snapshot manager.

    Subclasses the shared ``kg_utils.snapshots.SnapshotManager`` and adds:

    * ``package_name="pycode-kg"`` default for version detection.
    * Legacy ``capture()`` kwargs: ``coverage``, ``critical_issues``,
      ``complexity_median`` — merged into the metrics dict.
    * ``_compute_delta_from_metrics`` extended with ``coverage_delta`` and
      ``critical_issues_delta``.
    * ``_collect_module_node_counts()`` — SQLite per-module node counts stored
      in snapshot metrics under ``"module_node_counts"``.
    * Returns ``pycode_kg.snapshots.Snapshot`` instances (with typed-accessor
      properties) from all load/capture methods.
    """

    def __init__(
        self,
        snapshots_dir: Path | str,
        *,
        db_path: Path | str | None = None,
        package_name: str = "pycode-kg",
    ) -> None:
        super().__init__(snapshots_dir, package_name=package_name, db_path=db_path)

    # ------------------------------------------------------------------
    # capture — backwards-compat wrapper
    # ------------------------------------------------------------------

    def capture(  # type: ignore[override]
        self,
        version: str | None = None,
        branch: str | None = None,
        graph_stats_dict: dict[str, Any] | None = None,
        coverage: float = 0.0,
        critical_issues: int = 0,
        complexity_median: float = 0.0,
        hotspots: list[dict[str, Any]] | None = None,
        issues: list[str] | None = None,
        tree_hash: str = "",
    ) -> Snapshot:
        """Capture a pycode-kg snapshot.

        Accepts the legacy per-field kwargs (``coverage``, ``critical_issues``,
        ``complexity_median``) in addition to the dict-based
        ``graph_stats_dict`` from the base class, and builds the full metrics
        dict expected by the shared infrastructure.

        :param version: Version string (e.g., "0.5.1").
        :param branch: Git branch name; auto-detected if None.
        :param graph_stats_dict: Output from ``graph_stats()`` / ``store.stats()``.
        :param coverage: Docstring coverage fraction (0.0–1.0).
        :param critical_issues: Number of critical issues detected.
        :param complexity_median: Median fan-in across functions.
        :param hotspots: Top hotspot entries.
        :param issues: Issue description strings.
        :param tree_hash: Git tree hash; auto-detected if not provided.
        :return: New :class:`Snapshot` instance (not yet persisted).
        """
        module_node_counts = self._collect_module_node_counts()

        base_snap = super().capture(
            version=version,
            branch=branch,
            graph_stats_dict=graph_stats_dict,
            tree_hash=tree_hash,
            hotspots=hotspots,
            issues=issues,
            docstring_coverage=coverage,
            critical_issues=critical_issues,
            complexity_median=complexity_median,
            module_node_counts=module_node_counts,
        )

        return _rewrap(base_snap)

    # ------------------------------------------------------------------
    # diff_snapshots — adds module_node_counts_delta and issues_delta
    # ------------------------------------------------------------------

    def diff_snapshots(self, key_a: str, key_b: str) -> dict[str, Any]:
        """Compare two snapshots side-by-side.

        Extends the base diff with ``module_node_counts_delta`` and
        ``issues_delta`` (introduced / resolved issue strings).

        :param key_a: First snapshot key (tree hash).
        :param key_b: Second snapshot key (tree hash).
        :return: Dict with metrics from both, computed deltas.
        """
        snap_a = _BaseSnapshotManager.load_snapshot(self, key_a)
        snap_b = _BaseSnapshotManager.load_snapshot(self, key_b)

        if not snap_a or not snap_b:
            return {"error": "One or both snapshots not found"}

        m_a = snap_a.metrics
        m_b = snap_b.metrics

        all_node_kinds = set(m_a.get("node_counts", {})) | set(m_b.get("node_counts", {}))
        all_edge_rels = set(m_a.get("edge_counts", {})) | set(m_b.get("edge_counts", {}))

        node_counts_delta = {
            k: m_b.get("node_counts", {}).get(k, 0) - m_a.get("node_counts", {}).get(k, 0)
            for k in all_node_kinds
        }
        edge_counts_delta = {
            k: m_b.get("edge_counts", {}).get(k, 0) - m_a.get("edge_counts", {}).get(k, 0)
            for k in all_edge_rels
        }

        all_modules = set(m_a.get("module_node_counts", {})) | set(
            m_b.get("module_node_counts", {})
        )
        module_node_counts_delta = {
            mod: m_b.get("module_node_counts", {}).get(mod, 0)
            - m_a.get("module_node_counts", {}).get(mod, 0)
            for mod in all_modules
            if m_b.get("module_node_counts", {}).get(mod, 0)
            != m_a.get("module_node_counts", {}).get(mod, 0)
        }

        issues_a = set(snap_a.issues)
        issues_b = set(snap_b.issues)

        return {
            "a": {
                "key": snap_a.key,
                "metrics": m_a,
                "issues": snap_a.issues,
                "timestamp": snap_a.timestamp,
            },
            "b": {
                "key": snap_b.key,
                "metrics": m_b,
                "issues": snap_b.issues,
                "timestamp": snap_b.timestamp,
            },
            "delta": self._compute_delta_from_metrics(m_b, m_a),
            "node_counts_delta": node_counts_delta,
            "edge_counts_delta": edge_counts_delta,
            "module_node_counts_delta": module_node_counts_delta,
            "issues_delta": {
                "introduced": list(issues_b - issues_a),
                "resolved": list(issues_a - issues_b),
            },
        }

    # ------------------------------------------------------------------
    # Delta computation — adds coverage_delta and critical_issues_delta
    # ------------------------------------------------------------------

    def _compute_delta(self, snap_new: _BaseSnapshot, snap_old: _BaseSnapshot) -> dict[str, Any]:
        """Compute delta, extracting raw metric dicts to avoid the typed-property layer."""
        new_m = snap_new.__dict__.get("metrics", snap_new.metrics)
        old_m = snap_old.__dict__.get("metrics", snap_old.metrics)
        if isinstance(new_m, SnapshotMetrics):
            new_m = metrics_to_dict(new_m)
        if isinstance(old_m, SnapshotMetrics):
            old_m = metrics_to_dict(old_m)
        return self._compute_delta_from_metrics(new_m, old_m)

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
    # save_snapshot — normalise typed properties back to raw dicts first
    # ------------------------------------------------------------------

    def save_snapshot(self, snapshot: _BaseSnapshot, *, force: bool = False) -> Any:
        """Persist snapshot, normalising any typed-property values to raw dicts.

        The base ``save_snapshot`` inspects ``snapshot.metrics`` (expects a
        dict) and ``snapshot.vs_previous`` / ``snapshot.vs_baseline`` (expects
        dicts or None) directly.  If ``snapshot`` is a pycode-kg ``Snapshot``
        the properties return typed dataclasses instead; we substitute a plain
        ``_BaseSnapshot`` carrying the raw dicts so the base implementation
        can serialise without modification.
        """
        if isinstance(snapshot, Snapshot):
            raw = _BaseSnapshot(
                branch=snapshot.branch,
                timestamp=snapshot.timestamp,
                version=snapshot.version,
                metrics=snapshot.__dict__["metrics"],
                hotspots=snapshot.hotspots,
                issues=snapshot.issues,
                vs_previous=snapshot.__dict__["vs_previous"],
                vs_baseline=snapshot.__dict__["vs_baseline"],
                tree_hash=snapshot.tree_hash,
            )
            return super().save_snapshot(raw, force=force)
        return super().save_snapshot(snapshot, force=force)

    # ------------------------------------------------------------------
    # Load helpers — re-wrap base Snapshot instances as pycode-kg Snapshots
    # ------------------------------------------------------------------

    def load_snapshot(self, key: str) -> Snapshot | None:  # type: ignore[override]
        snap = super().load_snapshot(key)
        return _rewrap(snap) if snap is not None else None

    def get_previous(self, key: str) -> Snapshot | None:  # type: ignore[override]
        snap = super().get_previous(key)
        return _rewrap(snap) if snap is not None else None

    def get_baseline(self) -> Snapshot | None:  # type: ignore[override]
        snap = super().get_baseline()
        return _rewrap(snap) if snap is not None else None

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


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _rewrap(base: _BaseSnapshot) -> Snapshot:
    """Re-wrap a base Snapshot as a pycode-kg Snapshot (no data copying)."""
    if isinstance(base, Snapshot):
        return base
    snap = Snapshot.__new__(Snapshot)
    snap.__dict__.update(base.__dict__)
    return snap
