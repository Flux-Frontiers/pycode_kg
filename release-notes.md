# Release Notes — v0.26.0

> Released: 2026-09-06

This release removes a fragile pattern from snapshot handling and fixes a
crash in dependency analysis. Both were found while retiring a class of bug
that had already shipped twice this month.

## What changed

**The `Snapshot` subclass is gone.** PyCodeKG used to subclass the shared
`kg_utils.snapshots.Snapshot` to expose `metrics`, `vs_previous`, and
`vs_baseline` as typed properties instead of plain dicts. That forced a
hand-written copy of nine manager methods — `capture`, `save_snapshot`,
`load_snapshot`, `get_previous`, `get_baseline`, `diff_snapshots`,
`_compute_delta`, `to_dict`, and `from_dict` — and one of those copies is what
dropped the snapshot key and provenance fields in 0.25.0, patched same-day in
0.25.1. Removing the subclass removes the whole class of bug instead of the
one instance of it: those methods and the `Snapshot` class itself are gone,
and the shared implementations run unmodified.

A snapshot's `metrics`, `vs_previous`, and `vs_baseline` are now plain dicts.
`SnapshotMetrics` and `SnapshotDelta` remain available as converters for code
that wants attribute access — `metrics_from_dict(snap.metrics).total_nodes`
instead of `snap.metrics.total_nodes`. Snapshot files, manifests, CLI output,
and the `snapshot_show` / `snapshot_diff` MCP tools are unchanged.

**A stale graph can no longer crash dependency analysis.** The property-family
detector used a line number from the knowledge graph to index into the current
source file. If the graph was older than the working tree — the normal state
between an edit and a rebuild — a shortened file could put that index past the
end of the list, raising an `IndexError` and aborting the whole analysis phase
instead of returning a wrong answer. It now treats an out-of-range line number
as "not a property," so a stale graph degrades gracefully instead of crashing.

**The delta-backfill fix in `kgmodule-utils` 0.19.1 now reaches PyCodeKG.**
Loading a saved snapshot previously reported `coverage_delta` and
`critical_issues_delta` as absent even though `list_snapshots()` and
`diff_snapshots()` computed them correctly for the same pair — the read path
that `snapshot show` uses was the one giving the wrong answer. With the
`kgmodule-utils` floor resolving to 0.19.1, `snapshot show` now reports the
same numbers as every other view of a snapshot.

## Upgrading

No action required for normal use — snapshot files, the CLI, and the MCP
tools are unchanged. If your code accessed `Snapshot.metrics` as an object
with attributes (`snap.metrics.total_nodes`), switch to dict access
(`snap.metrics["total_nodes"]`) or call `metrics_from_dict(snap.metrics)` for
the old style with attribute access.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
