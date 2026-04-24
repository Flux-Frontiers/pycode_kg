# Release Notes — v0.16.0

> Released: 2026-04-24

### Changed

- **`pyproject.toml` migrated to PEP 621 `[project]` table format** — Replaced `[tool.poetry.dependencies]` with the standard `[project]` metadata block; dependency specs, extras, and classifiers restructured for full PEP 621 compliance and compatibility with modern build tooling.
- **`kg-snapshot` dependency switched from git source to PyPI** — Was `{ git = "https://github.com/Flux-Frontiers/kg_snapshot.git" }`; now `kg-snapshot>=0.3.0`. Required for publishing to PyPI (git-source deps are rejected by the PyPI index).
- **`poetry.lock` regenerated** — Fresh resolution after pyproject.toml restructure and git-dep removal.

### Removed

- **`SNAPSHOT_PRUNE_SUMMARY.md`** — Stale one-off summary file; no longer relevant.
- **`architecture.md`** — Replaced by `assets/architecture_description.md` introduced in v0.15.0.
- **`scripts/rebuild-pycodekg.sh`** — Superseded by `pycodekg build` CLI command.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
