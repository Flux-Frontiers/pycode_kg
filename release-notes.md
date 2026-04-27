# Release Notes — v0.17.2

> Released: 2026-04-27

### Fixed

- **`viz-timeline` snapshot field names** — `viz3d_timeline.py` was reading stale `kg_snapshot`-era manifest keys (`snap["commit"]`, `metrics["nodes"]`, `metrics["edges"]`, `metrics["coverage"]`). Updated to the `kg_utils` field names (`snap["key"]`, `metrics["total_nodes"]`, `metrics["total_edges"]`, `metrics["docstring_coverage"]`). The `viz-timeline` command now loads all snapshots correctly.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
