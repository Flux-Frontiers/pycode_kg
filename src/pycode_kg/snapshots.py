"""
snapshots.py — Temporal Snapshots of PyCodeKG Metrics

Thin compatibility layer over ``kg_snapshot``.  The shared module provides
the canonical ``Snapshot``, ``SnapshotManifest``, and ``SnapshotManager``
implementations.  This module:

  - Re-exports ``Snapshot`` and ``SnapshotManifest`` from ``kg_snapshot``
    for backwards compatibility.
  - Keeps domain-specific ``SnapshotMetrics`` and ``SnapshotDelta`` dataclasses
    (used by the CLI and tests) as local types.
  - Provides ``metrics_to_dict`` / ``metrics_from_dict`` helpers to convert
    between the dataclass representation and the dict-based shared model.
  - Subclasses ``SnapshotManager`` to set ``package_name="pycode-kg"``, override
    ``_compute_delta`` / ``_compute_delta_from_metrics`` with the
    pycode-kg-specific delta fields, and expose ``_collect_module_node_counts``.

Existing ``from pycode_kg.snapshots import ...`` call-sites continue to work
unchanged.

Usage
-----
>>> from pycode_kg.snapshots import SnapshotManager
>>> mgr = SnapshotManager(".pycodekg/snapshots")
>>> snapshot = mgr.capture("v0.5.1", "develop", graph_stats_dict)
>>> mgr.save_snapshot(snapshot)
>>> manifest = mgr.load_manifest()
>>> prev = mgr.get_previous(tree_hash)

Author: Eric G. Suchanek, PhD
Last Revision: 2026-04-07 09:13:36

License: Elastic 2.0
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Re-export shared data models
# ---------------------------------------------------------------------------
from kg_snapshot.snapshots import PruneResult as PruneResult  # noqa: F401 — re-export
from kg_snapshot.snapshots import Snapshot as _BaseSnapshot
from kg_snapshot.snapshots import SnapshotManager as _BaseSnapshotManager
from kg_snapshot.snapshots import (  # noqa: F401 — re-export
    SnapshotManifest as SnapshotManifest,
)

# ---------------------------------------------------------------------------
# Domain-specific dataclasses  (used by cmd_snapshot.py and tests)
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
    critical_issues: int  # number of critical issues found
    complexity_median: float  # median fan-in across functions
    module_node_counts: dict[str, int] = field(default_factory=dict)  # nodes per module path


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


def metrics_to_dict(metrics: SnapshotMetrics) -> dict[str, Any]:
    """Convert a ``SnapshotMetrics`` dataclass to a plain dict for storage."""
    return {
        "total_nodes": metrics.total_nodes,
        "total_edges": metrics.total_edges,
        "meaningful_nodes": metrics.meaningful_nodes,
        "docstring_coverage": metrics.docstring_coverage,
        "node_counts": metrics.node_counts,
        "edge_counts": metrics.edge_counts,
        "critical_issues": metrics.critical_issues,
        "complexity_median": metrics.complexity_median,
        "module_node_counts": metrics.module_node_counts,
    }


def metrics_from_dict(data: dict[str, Any]) -> SnapshotMetrics:
    """Reconstruct a ``SnapshotMetrics`` from a plain dict (e.g. loaded from JSON)."""
    return SnapshotMetrics(
        total_nodes=data.get("total_nodes", 0),
        total_edges=data.get("total_edges", 0),
        meaningful_nodes=data.get("meaningful_nodes", 0),
        docstring_coverage=data.get("docstring_coverage", 0.0),
        node_counts=data.get("node_counts", {}),
        edge_counts=data.get("edge_counts", {}),
        critical_issues=data.get("critical_issues", 0),
        complexity_median=data.get("complexity_median", 0.0),
        module_node_counts=data.get("module_node_counts", {}),
    )


def delta_to_dict(delta: SnapshotDelta) -> dict[str, Any]:
    """Convert a ``SnapshotDelta`` dataclass to a plain dict for storage."""
    return {
        "nodes": delta.nodes,
        "edges": delta.edges,
        "coverage_delta": delta.coverage_delta,
        "critical_issues_delta": delta.critical_issues_delta,
    }


def delta_from_dict(data: dict[str, Any] | None) -> SnapshotDelta | None:
    """Reconstruct a ``SnapshotDelta`` from a plain dict, or return ``None``."""
    if data is None:
        return None
    return SnapshotDelta(
        nodes=data.get("nodes", 0),
        edges=data.get("edges", 0),
        coverage_delta=data.get("coverage_delta", 0.0),
        critical_issues_delta=data.get("critical_issues_delta", 0),
    )


# ---------------------------------------------------------------------------
# Backwards-compat Snapshot wrapper
#
# The shared kg_rag.snapshots.Snapshot stores metrics as a plain dict and
# vs_previous/vs_baseline as plain dicts.  Legacy pycode-kg callers expect
# attribute access on these fields (snapshot.metrics.total_nodes, delta.nodes).
#
# We subclass Snapshot to override attribute access so that .metrics returns a
# SnapshotMetrics view and .vs_previous / .vs_baseline return SnapshotDelta
# views, while keeping the underlying dict storage for JSON serialization.
# ---------------------------------------------------------------------------


class Snapshot(_BaseSnapshot):
    """pycode-kg Snapshot with attribute-accessible metrics and delta fields.

    Subclasses the shared ``kg_rag.snapshots.Snapshot`` so that:

    - ``snapshot.metrics`` returns a :class:`SnapshotMetrics` dataclass built
      lazily from the underlying metrics dict.
    - ``snapshot.vs_previous`` / ``snapshot.vs_baseline`` return
      :class:`SnapshotDelta` dataclasses (or ``None``) built lazily from the
      underlying delta dicts.
    - All serialization goes through the shared ``to_dict`` / ``from_dict``
      which store plain dicts, ensuring on-disk format compatibility.
    """

    # Class-level type declarations for the raw storage attributes
    _metrics_raw: dict[str, Any]
    _vs_previous_raw: dict[str, Any] | None
    _vs_baseline_raw: dict[str, Any] | None

    # ------------------------------------------------------------------
    # Attribute-access shims
    # ------------------------------------------------------------------

    @property  # type: ignore[override]
    def metrics(self) -> SnapshotMetrics:  # type: ignore[override]
        return metrics_from_dict(self._metrics_raw)

    @metrics.setter
    def metrics(self, value: SnapshotMetrics | dict[str, Any]) -> None:
        self._metrics_raw = metrics_to_dict(value) if isinstance(value, SnapshotMetrics) else value

    @property  # type: ignore[override]
    def vs_previous(self) -> SnapshotDelta | None:  # type: ignore[override]
        return delta_from_dict(self._vs_previous_raw)

    @vs_previous.setter
    def vs_previous(self, value: SnapshotDelta | dict[str, Any] | None) -> None:
        self._vs_previous_raw = delta_to_dict(value) if isinstance(value, SnapshotDelta) else value

    @property  # type: ignore[override]
    def vs_baseline(self) -> SnapshotDelta | None:  # type: ignore[override]
        return delta_from_dict(self._vs_baseline_raw)

    @vs_baseline.setter
    def vs_baseline(self, value: SnapshotDelta | dict[str, Any] | None) -> None:
        self._vs_baseline_raw = delta_to_dict(value) if isinstance(value, SnapshotDelta) else value

    # ------------------------------------------------------------------
    # __init__: store raw dicts, pass them to super
    # ------------------------------------------------------------------

    def __init__(
        self,
        branch: str,
        timestamp: str,
        metrics: SnapshotMetrics | dict[str, Any],
        version: str = "",
        hotspots: list[dict[str, Any]] | None = None,
        issues: list[str] | None = None,
        vs_previous: SnapshotDelta | dict[str, Any] | None = None,
        vs_baseline: SnapshotDelta | dict[str, Any] | None = None,
        tree_hash: str = "",
    ) -> None:
        self._metrics_raw = (
            metrics_to_dict(metrics) if isinstance(metrics, SnapshotMetrics) else (metrics or {})
        )
        self._vs_previous_raw = (
            delta_to_dict(vs_previous) if isinstance(vs_previous, SnapshotDelta) else vs_previous
        )
        self._vs_baseline_raw = (
            delta_to_dict(vs_baseline) if isinstance(vs_baseline, SnapshotDelta) else vs_baseline
        )
        super().__init__(
            branch=branch,
            timestamp=timestamp,
            metrics=self._metrics_raw,
            version=version,
            hotspots=hotspots or [],
            issues=issues or [],
            vs_previous=self._vs_previous_raw,
            vs_baseline=self._vs_baseline_raw,
            tree_hash=tree_hash,
        )

    # ------------------------------------------------------------------
    # to_dict / from_dict — keep shared dict format on disk
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict (plain dicts for all nested fields)."""
        return {
            "key": self.tree_hash,
            "branch": self.branch,
            "timestamp": self.timestamp,
            "version": self.version,
            "metrics": self._metrics_raw,
            "hotspots": self.hotspots,
            "issues": self.issues,
            "vs_previous": self._vs_previous_raw,
            "vs_baseline": self._vs_baseline_raw,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Snapshot:
        """Reconstruct from a dict loaded from JSON."""
        raw = dict(data)

        metrics_data = raw.pop("metrics", {})
        vs_prev_data = raw.pop("vs_previous", None)
        vs_base_data = raw.pop("vs_baseline", None)

        # Normalise legacy 'tree_hash' field → 'key'
        if "key" not in raw and "tree_hash" in raw:
            raw["key"] = raw.pop("tree_hash")
        else:
            raw.pop("tree_hash", None)

        key = raw.pop("key", "")
        raw.pop("commit", None)  # drop legacy field
        raw.setdefault("version", "")

        return Snapshot(
            tree_hash=key,
            metrics=metrics_data,
            vs_previous=vs_prev_data,
            vs_baseline=vs_base_data,
            branch=raw.pop("branch", ""),
            timestamp=raw.pop("timestamp", ""),
            version=raw.pop("version", ""),
            hotspots=raw.pop("hotspots", []),
            issues=raw.pop("issues", []),
        )


# ---------------------------------------------------------------------------
# pycode-kg SnapshotManager subclass
# ---------------------------------------------------------------------------


class SnapshotManager(_BaseSnapshotManager):
    """pycode-kg specific snapshot manager.

    Extends the shared :class:`kg_rag.snapshots.SnapshotManager` with:

    - ``package_name="pycode-kg"`` for automatic version detection.
    - Domain-specific delta fields: ``coverage_delta`` and
      ``critical_issues_delta`` in addition to the base ``nodes`` / ``edges``.
    - ``_collect_module_node_counts()`` — SQLite query for per-module node
      counts, stored in snapshot metrics under ``"module_node_counts"``.

    The ``capture()`` signature is extended with named keyword arguments
    (``coverage``, ``critical_issues``, ``complexity_median``) so that
    existing call-sites in the CLI do not need to be changed.
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
    # Helper: wrap a base Snapshot in the local subclass
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap_snapshot(base: _BaseSnapshot) -> Snapshot:
        return Snapshot(
            branch=base.branch,
            timestamp=base.timestamp,
            version=base.version,
            metrics=base.metrics,
            hotspots=base.hotspots,
            issues=base.issues,
            vs_previous=base.vs_previous,
            vs_baseline=base.vs_baseline,
            tree_hash=base.tree_hash,
        )

    # ------------------------------------------------------------------
    # capture — extended signature for backwards compat
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

        Merges ``graph_stats_dict`` with pycode-kg-specific metric fields
        (``docstring_coverage``, ``critical_issues``, ``complexity_median``,
        ``module_node_counts``) into a single metrics dict, then delegates to
        the shared manager and returns a pycode-kg :class:`Snapshot` instance.

        :param version: Version string; auto-detected from package if None.
        :param branch: Git branch; auto-detected if None.
        :param graph_stats_dict: Output from the KG ``stats()`` method.
        :param coverage: Docstring coverage fraction (0.0–1.0).
        :param critical_issues: Number of critical issues detected.
        :param complexity_median: Median fan-in across functions.
        :param hotspots: Top hotspot entries.
        :param issues: Issue description strings.
        :param tree_hash: Git tree hash; auto-detected if not provided.
        :return: New :class:`Snapshot` instance (not yet persisted).
        """
        # Collect per-module counts from SQLite (returns {} if db unavailable)
        module_node_counts = self._collect_module_node_counts()

        # Call the base implementation passing extra fields via **extra_metrics
        base_snap = super().capture(
            version=version,
            branch=branch,
            graph_stats_dict=graph_stats_dict,
            tree_hash=tree_hash,
            hotspots=hotspots,
            issues=issues,
            # Extra domain-specific metric fields:
            docstring_coverage=coverage,
            critical_issues=critical_issues,
            complexity_median=complexity_median,
            module_node_counts=module_node_counts,
        )

        return self._wrap_snapshot(base_snap)

    # ------------------------------------------------------------------
    # Override load_snapshot to return pycode-kg Snapshot instances
    # ------------------------------------------------------------------

    def load_snapshot(self, key: str) -> Snapshot | None:
        """Load a snapshot by key, returning a pycode-kg Snapshot instance."""
        base_snap = super().load_snapshot(key)
        return self._wrap_snapshot(base_snap) if base_snap is not None else None

    # ------------------------------------------------------------------
    # save_snapshot — convert dataclass fields to plain dicts for manifest
    # ------------------------------------------------------------------

    def save_snapshot(self, snapshot: Snapshot, *, force: bool = False) -> Path | None:  # type: ignore[override]
        """Persist snapshot, normalising metrics to a plain dict for the manifest.

        The base :meth:`~kg_snapshot.snapshots.SnapshotManager.save_snapshot`
        writes ``snapshot.metrics`` directly into the manifest dict.  For
        pycode-kg :class:`Snapshot` instances that property returns a
        :class:`SnapshotMetrics` dataclass — not JSON-serializable.  This
        override uses the raw dict for manifest entries while preserving the
        base's dedup behaviour.

        :param snapshot: Snapshot to persist.
        :param force: If ``True``, always write a new history entry.
        :return: Path to the saved JSON file, or ``None`` if unchanged (dedup).
        :raises ValueError: If ``total_nodes`` is 0.
        """
        metrics_dict = snapshot._metrics_raw
        if metrics_dict.get("total_nodes", 0) == 0:
            raise ValueError(
                "Refusing to save degenerate snapshot with 0 nodes. "
                "Build the KG before capturing a snapshot."
            )

        manifest = self.load_manifest()

        # Dedup: if version + metrics unchanged, refresh the latest entry in-place.
        if not force and manifest.snapshots:
            latest = max(manifest.snapshots, key=lambda x: x.get("timestamp", ""))
            if snapshot.version == latest.get("version", "") and not self._metrics_changed(
                metrics_dict, latest.get("metrics", {})
            ):
                old_key = latest["key"]
                old_file = self.snapshots_dir / latest.get("file", f"{old_key}.json")
                snapshot_file = self.snapshots_dir / f"{snapshot.key}.json"
                snapshot_file.write_text(
                    json.dumps(snapshot.to_dict(), indent=2) + "\n",
                    encoding="utf-8",
                )
                if old_key != snapshot.key and old_file.exists():
                    old_file.unlink()
                latest.update(
                    key=snapshot.key,
                    branch=snapshot.branch,
                    timestamp=snapshot.timestamp,
                    file=snapshot_file.name,
                )
                manifest.last_update = datetime.now(UTC).isoformat()
                self._save_manifest(manifest)
                return snapshot_file

        # Normal path: new or changed snapshot.
        snapshot_file = self.snapshots_dir / f"{snapshot.key}.json"
        snapshot_file.write_text(json.dumps(snapshot.to_dict(), indent=2) + "\n", encoding="utf-8")

        existing_idx = next(
            (i for i, s in enumerate(manifest.snapshots) if s.get("key") == snapshot.key),
            None,
        )
        vs_prev = snapshot._vs_previous_raw
        vs_base = snapshot._vs_baseline_raw
        manifest_entry: dict[str, Any] = {
            "key": snapshot.key,
            "branch": snapshot.branch,
            "timestamp": snapshot.timestamp,
            "version": snapshot.version,
            "file": snapshot_file.name,
            "metrics": metrics_dict,
            "deltas": {"vs_previous": vs_prev, "vs_baseline": vs_base},
        }
        if existing_idx is not None:
            manifest.snapshots[existing_idx] = manifest_entry
        else:
            manifest.snapshots.append(manifest_entry)
        manifest.last_update = datetime.now(UTC).isoformat()
        self._save_manifest(manifest)
        return snapshot_file

    # ------------------------------------------------------------------
    # Delta computation — adds coverage_delta and critical_issues_delta
    # ------------------------------------------------------------------

    @staticmethod
    def _as_metrics_dict(m: SnapshotMetrics | dict[str, Any]) -> dict[str, Any]:
        """Return a plain metrics dict whether ``m`` is a dataclass or already a dict."""
        return metrics_to_dict(m) if isinstance(m, SnapshotMetrics) else m  # type: ignore[arg-type]

    def _compute_delta(self, snap_new: Snapshot, snap_old: Snapshot) -> dict[str, Any]:
        """Compute pycode-kg metrics delta including coverage and issue count."""
        return self._compute_delta_from_metrics(
            self._as_metrics_dict(snap_new.metrics),
            self._as_metrics_dict(snap_old.metrics),
        )

    def _compute_delta_from_metrics(
        self, new_m: dict[str, Any], old_m: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute delta dict from two raw metrics dicts.

        Includes the base ``nodes`` / ``edges`` plus the pycode-kg-specific
        ``coverage_delta`` and ``critical_issues_delta`` fields.
        """
        return {
            "nodes": new_m.get("total_nodes", 0) - old_m.get("total_nodes", 0),
            "edges": new_m.get("total_edges", 0) - old_m.get("total_edges", 0),
            "coverage_delta": new_m.get("docstring_coverage", 0.0)
            - old_m.get("docstring_coverage", 0.0),
            "critical_issues_delta": new_m.get("critical_issues", 0)
            - old_m.get("critical_issues", 0),
        }

    # ------------------------------------------------------------------
    # diff_snapshots — includes module_node_counts_delta and issues_delta
    # ------------------------------------------------------------------

    def diff_snapshots(self, key_a: str, key_b: str) -> dict[str, Any]:
        """Compare two snapshots side-by-side.

        Extends the shared diff with ``module_node_counts_delta`` and
        ``issues_delta`` (introduced / resolved issue strings).

        :param key_a: First snapshot key (tree hash).
        :param key_b: Second snapshot key (tree hash).
        :return: Dict with metrics from both, computed deltas.
        """
        snap_a = self.load_snapshot(key_a)
        snap_b = self.load_snapshot(key_b)

        if not snap_a or not snap_b:
            return {"error": "One or both snapshots not found"}

        m_a = self._as_metrics_dict(snap_a.metrics)
        m_b = self._as_metrics_dict(snap_b.metrics)

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
            "a": {"key": snap_a.key, "metrics": m_a, "issues": snap_a.issues},
            "b": {"key": snap_b.key, "metrics": m_b, "issues": snap_b.issues},
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
# Public re-exports (so ``from pycode_kg.snapshots import X`` keeps working)
# ---------------------------------------------------------------------------

__all__ = [
    "Snapshot",
    "SnapshotManifest",
    "SnapshotManager",
    "SnapshotMetrics",
    "SnapshotDelta",
    "PruneResult",
    "metrics_to_dict",
    "metrics_from_dict",
    "delta_to_dict",
    "delta_from_dict",
]
