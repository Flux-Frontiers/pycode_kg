# Release Notes — v0.19.3

> Released: 2026-06-01

### Changed

- **Migrated type checker from mypy → [ty](https://github.com/astral-sh/ty)** (`^0.0.41`) across `pyproject.toml`, `.pre-commit-config.yaml`, and CI (`poetry run ty check src/`). Resolved the resulting diagnostics:
  - `graph.py`: narrow `nodes`/`edges` properties with `assert ... is not None` instead of `# type: ignore[return-value]`.
  - `viz3d.py` / `snapshots.py`: converted the remaining mypy `# type: ignore[code]` suppressions to ty `# ty: ignore[code]` for third-party false positives (pyvista `functools.wraps` self-binding, PyQt5 `Qt` enum attributes, `param` descriptor declarations, and intentional `closeEvent`/`capture` LSP overrides).
  - `pyproject.toml`: replaced `[tool.mypy]` with `[tool.ty.environment]`/`[tool.ty.rules]` (`unresolved-import = "ignore"` mirrors mypy's `ignore_missing_imports`; `unused-ignore-comment = "ignore"` so the optional-dependency `# ty: ignore` suppressions in `viz3d.py` don't fail the lean CI install, where `param`/`PyQt5`/`pyvista` are absent); bumped the `ruff-pre-commit` hook to `v0.15.13` (`ruff` → `ruff-check`).

- **Migrated infrastructure to `kgmodule-utils>=0.3.0`** — `store.py`, `index.py`, `module/base.py`, `module/types.py`, and `module/extractor.py` now delegate to `kg_utils` instead of carrying duplicate implementations. Net reduction of ~2,660 lines. All public APIs are preserved via re-export shims so existing callers are unaffected.
  - `store.py` (766 → 7 lines): re-exports `GraphStore`, `DEFAULT_RELS`, `ProvMeta` from `kg_utils.store`.
  - `index.py` (575 → 11 lines): re-exports `SemanticIndex`, `Embedder`, `SentenceTransformerEmbedder`, `SeedHit`, `DEFAULT_MODEL`, and helpers from `kg_utils.semantic`.
  - `module/base.py` (720 → 34 lines): thin `KGModule` subclass of `kg_utils.pipeline.KGModule`; retains `.pycodekg` default dir and `resolve_symbols()` post-build hook.
  - `module/types.py` (532 → 31 lines): re-exports `BuildStats`, `QueryResult`, `SnippetPack` from `kg_utils.specs` and pipeline utilities from `kg_utils.pipeline`; keeps `Snippet` dataclass as a backward-compat shim.
  - `module/extractor.py` (276 → 129 lines): `NodeSpec`, `EdgeSpec`, `KGExtractor` now imported from `kg_utils.specs`/`kg_utils.extractor`; `PyCodeKGExtractor` body unchanged.
- **`pyproject.toml`** — bumped `kgmodule-utils` to `[semantic]>=0.3.0`; dropped `lancedb` direct dependency (pulled in transitively); updated `doc-kg` floor to `>=0.15.2`.
- **CLI build commands** — `cmd_build.py` and `cmd_build_full.py` now use `PyCodeKGExtractor` to produce `NodeSpec`/`EdgeSpec` before writing to `GraphStore`, replacing the old `CodeGraph` → raw `Node`/`Edge` path.
- **`pycodekg.py`** — `DEFAULT_MODEL` now imported directly from `kg_utils.semantic` instead of the local `index.py` shim.
- **`cli/cmd_model.py`, `cli/cmd_init.py`** — `_local_model_path` now imported from `kg_utils.semantic`.

### Removed

- **Stray `uv.lock`** — removed an accidental uv-generated lockfile (the project is Poetry-managed; `poetry.lock` is the source of truth) and added `uv.lock` to `.gitignore` to prevent it returning.

### Added

- **`docs/exercises.md` + `scripts/exercise_runner.py`** — guided exercise set and runner script for hands-on PyCodeKG exploration; covers orientation, query, pack, callers, analyze, and snapshot workflows.
- **`docs/case_study_refactor_validation.md`** — case study documenting the refactor validation workflow using PyCodeKG snapshots and structural analysis.
- **Six new metric snapshots** in `.pycodekg/snapshots/` — temporal coverage extended with snapshots from earlier in the v0.19.0 cycle.

### Changed (prior)

- **`README.md` — `pycodekg analyze` section expanded** — replaced the bullet-list summary with the full 15-phase pipeline table (baseline → CodeRank → fan-in/out → dependencies → patterns → coupling → critical paths → public API → docstring coverage → inheritance → insights → snapshots → centrality → concern ranking); added personal origin note and numpy/matplotlib anecdote; added viz3d active-development caveat to the feature table.
- **Announcements updated to v0.19.0** — all three announcement files (`GITHUB.md`, `HACKERNEWS.md`, `REDDIT.md`) now reference the current version, use `pip install pycode-kg` instead of stale git-URL installs, lead with the 15-phase analyze pipeline, and note that `viz3d` is actively in development.
- **Asset files renamed** — `assets/codeKG_arch_*.{png,jpg}` renamed to `assets/PyCodeKG_arch_*` (four files: `_9x16.png`, `_banana.png`, `_square-web.jpg`, `_square.png`) for naming consistency; references updated in `article/pycode_kg.tex` and `article/pycode_kg_medium.md`.

### Fixed

- **`scripts/exercise_runner.py`** — removed unused `snap_keys: list[str] = []` local variable (ruff F841).

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
