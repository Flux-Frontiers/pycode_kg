# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Note: older entries preserve the API names used at that release (for example commit-based snapshot parameters) and may differ from current key/tree-hash terminology.

## [Unreleased]

### Added

### Changed

### Removed

### Fixed

## [0.17.1] - 2026-04-27

### Changed

- **`snapshots.py` migrated to `kg_utils.snapshots`** — Imports now come from `kgmodule-utils` (`kg_utils.snapshots`) instead of the old `kg_snapshot` package. The `Snapshot` subclass was simplified to use `__dict__`-based property accessors (matching the `doc_kg` pattern) rather than private `_metrics_raw` backing fields. `SnapshotManager._wrap_snapshot` replaced by a module-level `_rewrap` helper; `save_snapshot` now normalises typed properties to raw dicts before delegating to the base class.
- **`resolve_model_path` and `DEFAULT_MODEL` vendored into `index.py`** — No longer imported from `kg_utils.embed`; the logic is now inlined directly in `index.py` to remove the runtime dependency on the `kg_utils.embed` module. `pycodekg.py` updated to re-export `DEFAULT_MODEL` from `pycode_kg.index`.
- **`kgmodule-utils>=0.2.1` replaces `kg-snapshot>=0.3.0`** — `pyproject.toml` dependency updated to `kgmodule-utils>=0.2.1` (PyPI), which bundles the shared snapshot infrastructure previously split across `kg-snapshot` and the git-sourced `kg-utils`. `0.2.1` includes the `get_baseline` / `get_previous` `KeyError: 'key'` fix for legacy manifest entries.
- **KG snapshots updated** — `.pycodekg/snapshots/` and `.dockg/snapshots/` refreshed to capture metrics at this release.

## [0.17.0] - 2026-04-25

### Added

- **`kg-utils` dependency** — `kg_utils.embed.resolve_model_path` and `DEFAULT_MODEL` are now sourced from the shared `kg-utils` library (git source: `Flux-Frontiers/KG_utils`), unifying model-path resolution logic across all KG projects.
- **`tests/conftest.py`** — `pytest_configure` hook sets `TQDM_DISABLE=1` before any tqdm instance is created, silencing all progress bars across the entire test session.
- **13 new unit tests in `tests/test_index.py`** — Cover all three `SentenceTransformerEmbedder` loading paths (local cache hit, HF `local_files_only`, download fallback), `KGRAG_MODEL_DIR` override, `cwd` fallback, model alias resolution, `TQDM_DISABLE` set/restore behavior (including failure path), `disable_progress_bar()` call verification, and task-prompt detection.

### Changed

- **`_local_model_path` migrated to `kg_utils.embed.resolve_model_path`** — Removed duplicated path-resolution logic in `index.py`; now delegates to the shared utility which handles `KGRAG_MODEL_DIR`, alias expansion (`bge-small` → `BAAI/bge-small-en-v1.5`), and local fallback.
- **`DEFAULT_MODEL` re-exported from `kg_utils.embed`** — `pycodekg.py` re-exports the canonical default model name from `kg_utils` to maintain the public API contract.
- **`disable_progress_bar()` added to `suppress_ingestion_logging()` and `SentenceTransformerEmbedder.__init__`** — Suppresses the "loading weights" tqdm bar emitted by `transformers` during model loading, in addition to the existing verbosity-error log suppression.

## [0.16.1] - 2026-04-25

### Added

- **`workflow_dispatch` trigger in CI** — GitHub Actions workflow can now be triggered manually from the Actions UI.
- **Integration test suite** (`tests/test_integration.py`) — 14 end-to-end tests covering `SentenceTransformerEmbedder`, `SemanticIndex`, and `PyCodeKG` with the real embedding model. Tests are marked `@pytest.mark.integration` and `@pytest.mark.slow`; excluded from CI via `pytest -m "not integration"`.
- **`slow` and `integration` pytest markers** registered in `[tool.pytest.ini_options]` to prevent unknown-mark warnings.

### Changed

- **Pre-commit hook reordered and enhanced** — Ruff now runs before detect-secrets and local hooks; ruff hooks gain `exclude: '^\.claude/'`, `pass_filenames: false`, and `always_run: true` for consistent behaviour. Pylint moved from the upstream PyCQA repo hook to a local `poetry run pylint src/` hook. `poetry-check` hook removed.
- **`cmd_init.py` imports moved to module level** — Lazy function-level imports of `_run_pipeline`, `_PRE_COMMIT_HOOK`, `PyCodeKG`, `PyCodeKGAnalyzer`, `SnapshotManager`, `GraphStore`, and `importlib.metadata` promoted to top-level to resolve pylint `C0415` warnings.
- **CI test step excludes integration tests** — `poetry run pytest` now runs as `poetry run pytest -m "not integration"` to avoid pulling the embedding model in GitHub Actions.

## [0.16.0] - 2026-04-24

### Changed

- **`pyproject.toml` migrated to PEP 621 `[project]` table format** — Replaced `[tool.poetry.dependencies]` with the standard `[project]` metadata block; dependency specs, extras, and classifiers restructured for full PEP 621 compliance and compatibility with modern build tooling.
- **`kg-snapshot` dependency switched from git source to PyPI** — Was `{ git = "https://github.com/Flux-Frontiers/kg_snapshot.git" }`; now `kg-snapshot>=0.3.0`. Required for publishing to PyPI (git-source deps are rejected by the PyPI index).
- **`poetry.lock` regenerated** — Fresh resolution after pyproject.toml restructure and git-dep removal.

### Removed

- **`SNAPSHOT_PRUNE_SUMMARY.md`** — Stale one-off summary file; no longer relevant.
- **`architecture.md`** — Replaced by `assets/architecture_description.md` introduced in v0.15.0.
- **`scripts/rebuild-pycodekg.sh`** — Superseded by `pycodekg build` CLI command.

## [0.15.2] - 2026-04-24

### Fixed

- **`CITATION.cff` Zenodo compatibility** — Replaced `license: "Elastic-2.0"` with `license-url:` (Zenodo's license allowlist does not include `Elastic-2.0`); removed `name-suffix: PhD` which some CFF validators reject; moved PhD credential into `given-names`.

## [0.15.1] - 2026-04-24

### Added

- **`CITATION.cff` enriched with ORCID and release date** — Added `orcid: "https://orcid.org/0009-0009-0891-1507"` and `date-released: "2026-04-24"` to satisfy Zenodo archival requirements and enable DOI minting on tagged releases.
- **`## Citation` section in `README.md`** — Added APA and BibTeX citation blocks, Zenodo DOI badge, and link to `CITATION.cff` so users and downstream projects can cite PyCodeKG correctly.

## [0.15.0] - 2026-04-24

### Added

- **`CITATION.cff` added** (`CITATION.cff`) — Zenodo/software citation metadata for the project; enables "Cite this repository" on GitHub and automatic Zenodo archival on tagged releases.

- **Domain metrics in `GraphStore.stats()`** (`src/pycode_kg/store.py`) — `stats()` now returns `module_count`, `class_count`, `function_count`, `method_count`, `docstring_coverage` (fraction of functions/methods with non-empty docstrings), and `snapshot_count` (entries in the adjacent snapshot manifest). Avoids a redundant SQL round-trip by reusing the already-fetched `node_counts` dict.
- **`graph_stats` MCP tool enriched with domain metrics** (`src/pycode_kg/mcp_server.py`) — Output now includes `Docstring coverage` and `Snapshots` lines when present, giving agents a quick health signal without a separate `analyze` call. Tool description and `FastMCP` instructions block updated to match.
- **Architecture description document** (`assets/architecture_description.md`) — Canonical source-of-truth document describing every layer, component, data flow, and output surface; used to regenerate the architecture diagram without reading source files.
- **`stats()` test suite** (`tests/test_store.py`) — Seven new parametric tests covering kind counts, full/partial/zero docstring coverage, missing manifest, valid manifest, and corrupt manifest; guard against division-by-zero and silent JSON-parse failures.

### Changed

- **Version bumped to 0.15.0** (`pyproject.toml`, `src/pycode_kg/__init__.py`).

- **`find_node(name, kind)` MCP tool** (`src/pycode_kg/mcp_server.py`) — New tool that resolves a function or class name to its stable node ID via case-insensitive SQL search against `name` and `qualname` columns. Sym: stubs excluded. Accepts optional `kind` filter (`function`, `class`, `method`, `module`). Eliminates the need to know a node's full stable ID before calling `explain()` or `callers()`. MCP instructions and recommended workflows updated accordingly.
- **`format` parameter for `query_codebase`** (`src/pycode_kg/mcp_server.py`) — Pass `format='markdown'` to receive a compact ranked Markdown table instead of raw JSON. Default `'json'` unchanged.
- **Task-prompt auto-detection in `SentenceTransformerEmbedder`** (`src/pycode_kg/index.py`) — On load, inspects `model.prompts` dict and stores `_query_prompt` / `_doc_prompt`. When present, `embed_query()` passes `prompt_name='search_query'` and `embed_texts()` passes `prompt_name='search_document'`, enabling correct behaviour for models like `nomic-ai/nomic-embed-text-v1.5` that require task-instruction prefixes.
- **`trust_remote_code=True` on all `SentenceTransformer` instantiation paths** (`src/pycode_kg/index.py`) — Required for `nomic-ai/nomic-embed-text-v1.5` and similar models that ship custom pooling or encoding code.
- **Truncation annotation in `SnippetPack.to_markdown()`** (`src/pycode_kg/module/types.py`) — When a snippet is clipped by `max_lines`, a `*(truncated: showing lines X–Y of A–B)*` notice is emitted before the code block so readers know they are not seeing the full function.
- **Boilerplate exclusion in `detect_framework_nodes`** (`src/pycode_kg/analysis/framework_detector.py`) — `_BOILERPLATE_NAMES` frozenset defines 21 lifecycle/dunder methods (`close`, `__init__`, `__exit__`, etc.) that are filtered out before framework score ranking, preventing teardown boilerplate from outranking genuine architectural hubs.
- **Large-module warning in `PyCodeKGAnalyzer`** (`src/pycode_kg/pycodekg_thorough_analysis.py`) — Modules with more than 30 functions/methods/classes are now flagged as `[WARN]` issues, prompting decomposition into focused submodules.
- **Nomic benchmark runs** (`analysis/embedder_benchmark_20260421_*.md/.json`) — Two runs of `nomic-ai/nomic-embed-text-v1.5`: one without task prompts (41.91s build), one with (8.53s build). Both added to `analysis/` with full JSON + Markdown reports.
- **Analysis report for 2026-04-19** (`analysis/pycode_kg_analysis_20260419.md`) — Full architectural analysis snapshot generated by `pycodekg analyze`; grade A (92/100), 7178 nodes, 92.6% docstring coverage.

### Changed

- **`max_per_module` default raised from 0 to 3** (`src/pycode_kg/mcp_server.py`) — Both `query_codebase` and `pack_snippets` now cap results at 3 nodes per module by default, preventing a single popular module from dominating hop-1 expansion. Pass `max_per_module=0` to restore uncapped behaviour for broad coverage queries. Docstrings updated accordingly.
- **Score normalization in `KGModule.query`** (`src/pycode_kg/module/base.py`) — Composite relevance scores are normalized so the top result always approaches 1.0, making `min_score` thresholds consistent across queries with different embedding distance distributions.
- **`nomic-ai/nomic-embed-text-v1.5` added to benchmark default model list** (`scripts/benchmark_embedders.py`) — Now included in the default `--models` string alongside the existing five candidates.
- **Embedder benchmark summary updated with nomic findings** (`analysis/embedder_benchmark_summary.md`) — Two new runs documented, hybrid score comparison table extended, new finding section added. Verdict: nomic wins NL queries (Q1: 0.922, Q3: 0.964 vs BGE-small's 0.648/0.564) but fails identifier queries (Q2 degenerate, ~0.493 uniform semantic scores) even with task prompts, and builds 7× slower. `BAAI/bge-small-en-v1.5` remains canonical.
- **Analysis and assessment files renamed from CodeKG to PyCodeKG** — `analysis/CodeKG_Assessment.md` → `PyCodeKG_Assessment.md`; assessment protocol and historical assessments renamed from `CodeKG_*` to `PyCodeKG_*` throughout.
- **Stale analysis files removed** (`analysis/`) — Deleted `bug_pre_commit_snapshot_ordering_20260318.md`, `bug_relative_path_defaults_20260317.md`, and eight `code_kg_analysis_2026031*.md` files now superseded by current analysis tooling.

### Fixed

- **`find_definition_at` entry added to MCP module docstring and FastMCP instructions** (`src/pycode_kg/mcp_server.py`) — Tool was implemented but not documented in the module-level Tools list or the instructions block; both updated.
- **`test_ste_init` assertion updated** (`tests/test_index.py`) — Test now expects `trust_remote_code=True` in the `SentenceTransformer` call, matching the updated `SentenceTransformerEmbedder.__init__` signature.

### Changed

- **Article renamed from CodeKG to PyCodeKG throughout** (`article/pycode_kg.tex`, `article/pycode_kg_medium.md`) — Title, author URL, all class and CLI references updated to use the correct `PyCodeKG` / `pycodekg` names, including `PyCodeKGVisitor`, `PyCodeKGExtractor`, and `.pycodekg/` directory paths.
- **Build Pipeline section restructured as multi-pass knowledge compiler** (`article/pycode_kg.tex`) — Section rewritten to articulate that the five enrichment phases (structural extraction → call graph → data flow → symbol resolution → semantic indexing) are semantically ordered by the Python ontology. Each phase is now a named subsection with a motivated role (skeleton, nervous system, metabolic layer, cross-module bridge, cognitive layer). A new framing paragraph distinguishes knowledge compilation from retrieval augmentation.
- **Design Principles expanded to six** (`article/pycode_kg.tex`) — Added sixth principle: *Compilation over retrieval*, explaining why enrichment ordering is determined by semantic dependency rather than implementation convenience.
- **New comparison subsection: Knowledge Compilation vs. Retrieval Augmentation** (`article/pycode_kg.tex`) — Added subsection in the GraphRAG comparison making the compiler analogy explicit: PyCodeKG produces a new artifact rather than searching an existing corpus, analogous to the stages of a language compiler whose output is a queryable structural substrate.
- **Abstract rewritten around knowledge-compiler thesis** (`article/pycode_kg.tex`) — Opens with "PyCodeKG is a knowledge compiler", names all five phases, and replaces "derived" with "compiled" in the Structural KG-RAG characterisation.
- **Architecture figure added** (`article/pycode_kg.tex`, `article/pycode_kg_medium.md`) — `assets/codeKG_arch_banana.png` inserted at the Architecture section with a descriptive caption; `\usepackage{graphicx,float}` added; `[H]` placement pin used; scaled to `0.85\linewidth`.
- **MCP tool list updated** (`article/pycode_kg_medium.md`) — Updated from four to ten tools with accurate descriptions matching the current server implementation.
- **Embedding model corrected** (`article/pycode_kg_medium.md`) — Changed `all-MiniLM-L6-v2` to `BAAI/bge-small-en-v1.5` throughout.
- **GitHub URL corrected** (`article/pycode_kg_medium.md`) — Footer URL updated from `suchanek/pycode_kg` to `Flux-Frontiers/pycode_kg`.
- **README CLI examples simplified** (`README.md`) — Removed redundant explicit `--db`/`--sqlite`/`--lancedb` path arguments from all commands where `.pycodekg/` defaults apply; MCP prerequisites consolidated to single `pycodekg build` call; installation snippet and script alias block updated accordingly.

### Fixed

- **`SentenceTransformerEmbedder` deprecation warning** (`src/pycode_kg/index.py`) — Replaced deprecated `get_sentence_embedding_dimension()` with `get_embedding_dimension()` to silence `FutureWarning` from `sentence-transformers` ≥ 4.x.

## [0.13.0] - 2026-04-07

### Added

- **`_wrap_snapshot` helper on `SnapshotManager`** (`snapshots.py`) — Replaces the duplicated 9-field copy-constructor in `capture` and `load_snapshot` with a single static method, eliminating a fragile pattern that would silently break if the base `Snapshot` added fields.
- **`_as_metrics_dict` helper on `SnapshotManager`** (`snapshots.py`) — Normalises a metrics value to a plain dict whether it arrives as a `SnapshotMetrics` dataclass or already a dict; used by `_compute_delta` and `diff_snapshots` to handle both base and local `Snapshot` instances correctly.
- **Analysis report for 0.12.0** (`analysis/pycode_kg_analysis_20260407.md`) — Full architectural analysis generated by `pycodekg analyze`.

### Changed

- **`Snapshot` subclass cleaned up** (`snapshots.py`) — Replaced `class Snapshot(Snapshot)` shadow-import pattern with `class Snapshot(_BaseSnapshot)`, eliminating the `# type: ignore[no-redef]` hack. All `object.__getattribute__` / `object.__setattr__` low-level bypasses replaced with plain `self._metrics_raw` / `self._vs_previous_raw` / `self._vs_baseline_raw` attribute access. `__init__` collapsed from a triple-store/re-read pattern to three typed assignments followed by one `super().__init__` call.
- **`save_snapshot` restored base dedup logic** (`snapshots.py`) — The previous override silently omitted the base class's refresh-in-place behaviour (when version + metrics are unchanged). The override now includes the full dedup path, accepts the `force` keyword argument, and returns `Path | None` matching the base signature.
- **`datetime` import moved to module top** (`snapshots.py`) — Removed the stray `from datetime import UTC, datetime` inside `save_snapshot`; now imported with the rest of the stdlib at the top of the file.
- **Version bumped to 0.12.0** (`pyproject.toml`, `__init__.py`).
- **VSCode pytest path configured** (`.vscode/settings.json`) — `python.testing.pytestPath` now points to the venv pytest binary for reliable test discovery.
- **`.mcp.json.bak` updated** — MCP server entries corrected to reference `pycodekg` instead of `codekg` and the pycode_kg repo path.

### Fixed

- **Dead `isinstance(…, dict)` branches removed** (`snapshots.py`) — `_compute_delta` and `diff_snapshots` previously checked `isinstance(snap.metrics, dict)` but `Snapshot.metrics` always returns a `SnapshotMetrics` via the property. Replaced with `_as_metrics_dict` which correctly handles both base-class (dict) and local-subclass (dataclass) instances.

### Added

- **`doc-kg`, `ftree-kg`, `agent-kg` in dev group** (`pyproject.toml`) — Sister KG packages moved from optional `kg` extra to the `dev` dependency group, ensuring they are always available in a development environment without extra flags.
- **TestPyPI source declared** (`pyproject.toml`) — Added `[[tool.poetry.source]]` entry for `testpypi` (supplemental priority) so `kg-snapshot` resolves correctly via `poetry lock`.

### Changed

- **`kg-snapshot` pinned from TestPyPI** (`pyproject.toml`) — Switched from a git source reference to `version = ">=0.3.0", source = "testpypi"` now that the package is published there.
- **`kg` extra removed** (`pyproject.toml`) — The `kg` extra is no longer needed; all KG sister packages are now in the dev group.
- **Installation docs updated** (`README.md`) — Development setup instructions and the consumer note now reflect `poetry install --with dev` as the canonical install command, documenting that it includes `doc-kg`, `ftree-kg`, and `agent-kg`.

### Fixed

### Added

- **`snapshot prune` CLI subcommand** (`cli/cmd_snapshot.py`) — New `pycodekg snapshot prune` command wires through `SnapshotManager.prune_snapshots()` from `kg_snapshot`. Removes metric-duplicate interior snapshots, broken manifest entries (JSON file missing on disk), and orphaned JSON files not referenced by the manifest. Baseline (oldest) and latest snapshots are always preserved. Supports `--dry-run` to preview what would be removed. `PruneResult` re-exported from `snapshots.py` and added to `__all__`.
- **Snapshot manifest pruned** (`.pycodekg/snapshots/`) — 57 vestigial snapshot files (56 metric-duplicates + 1 orphaned file) removed by running `pycodekg snapshot prune`.

### Removed

## [0.11.0] - 2026-04-03

### Added

- **`SnapshotManifest` exported from public API** (`__init__.py`) — `SnapshotManifest` is now importable from the top-level `pycode_kg` package and listed in `__all__`.
- **`__all__` re-export list in `snapshots.py`** — Explicit `__all__` added to `snapshots` module so `from pycode_kg.snapshots import X` is unambiguous for all public types.
- **New PyCodeKG snapshots for branches `main` and `claude/poetry-install-setup`** — Five snapshot JSON files added to `.pycodekg/snapshots/` covering versions 0.9.2 and 0.9.3.
- **`doc-kg` and `kg-rag` as direct dependencies** (`pyproject.toml`) — Sister repos `doc-kg` (0.4.1) and `kg-rag` (0.3.3) are now required direct dependencies (previously optional/commented-out), enabling a unified KGRAG install.
- **`ftree-kg` as optional `kg` extra** (`pyproject.toml`) — FTree_kg (0.2.0) added as an optional dependency under the `kg` extra for full multi-KG installs.
- **Architecture analysis report** (`analysis/pycode_kg_analysis_20260320.md`) — Full nine-phase analysis generated by `pycodekg analyze`, covering complexity hotspots, module coupling, call chains, SIR rankings, and CodeRank scores. Re-run after orphan and fan-out fixes: **Grade A — 100/100 (Excellent)**.

### Changed

- **`pycodekg build` always wipes; new `pycodekg update` for incremental upsert** (`cmd_build_full.py`, `pyproject.toml`) — `pycodekg build` now unconditionally clears both SQLite and LanceDB before rebuilding — no `--wipe` flag needed. A new `pycodekg update` command (also available as `pycodekg-update`) performs the incremental upsert path (no wipe). This eliminates the phantom-node footgun where renamed or deleted nodes silently persisted across builds.

- **`pycodekg build` output stripped of Rich markup** (`cmd_build_full.py`) — Removed the `rich.console.Console`, `rich.panel.Panel`, and `rich.table.Table` imports entirely. All build output now uses plain `click.echo`. Replaced the two-call `_step_header` + `_step_ok` pattern with a single `_step_result` per step and a compact `done (Ns)` footer. Output drops from ~15 coloured lines to 5 plain lines. Also factored shared CLI options and pipeline logic into `_common_options` and `_run_pipeline` to avoid duplication between `build` and `update`.

- **`MainWindow.__init__` refactored into focused builder methods** (`viz3d.py`) — Extracted the 260-line inline Qt UI construction into seven focused helpers: `_build_input_params`, `_build_module_filter`, `_build_render_options`, `_build_action_buttons`, `_build_control_panel`, `_build_viewport_panel`, `_setup_mesh_picking`, and `_connect_signals`. Also promoted `_h2`/`_lbl` inner functions to `@staticmethod` class methods. `__init__` fan-out drops from 95 to ~15 unique callees, eliminating the high-fan-out architectural warning (+8 pts to quality score).

- **Upgrade `sentence-transformers` to `^5.2.0`** (`pyproject.toml`) — Previously pinned to `==4.1.0`; now resolves to `5.3.0`. Relaxes the upper bound on `transformers` from `<5.0.0` to `<6.0.0`.
- **Explicit `safetensors = "^0.5.0"` dependency** (`pyproject.toml`) — Added as a direct dependency to prevent silent downgrades; resolves to `0.5.3` replacing the previous `0.7.0` transitive pin.
- **`transformers` constraint updated to `^4.57.6`** (`pyproject.toml`) — Replaces the bare `<5.0.0` upper-bound cap with a proper caret constraint.
- **`kg` extra now contains only `ftree-kg`** (`pyproject.toml`) — `doc-kg` and `kg-rag` moved from optional extra to direct dependencies; `kg` extra reduced to the ftree-kg component.
- **`diff_snapshots` uses dict-based metrics access** (`snapshots.py`) — Replaced typed `SnapshotMetrics` attribute access with `metrics_to_dict()` normalization, making the diff robust to both legacy and current snapshot formats.
- **Removed redundant helper methods from `SnapshotManager`** (`snapshots.py`) — `get_baseline`, `list_snapshots`, `_compute_delta`, `_get_current_tree_hash`, and `_get_current_branch` removed; equivalent logic moved to the KGModule base class.

### Fixed

- **`.gitignore` DS_Store glob** — Changed `.DS_Store` to `**/.DS_Store` so macOS metadata files are excluded at all directory depths, not just the repo root.

- **Orphan false-positive in `_analyze_dependencies`** (`pycodekg_thorough_analysis.py`) — The orphan checker now also checks `ATTR_ACCESS` edges alongside `CALLS` edges. Methods passed as callbacks via bound-method references (e.g. `self._analyze_dependencies` to `_run_phase`) produce `ATTR_ACCESS` edges, not `CALLS` edges, and were previously misclassified as dead code. Eliminating this false positive removes the orphan penalty (+10 pts to quality score). Combined with the `MainWindow` fan-out fix, overall quality grade rises from **B (82/100)** to **A (100/100)**.

### Removed

## [0.9.3] - 2026-03-19

### Added

- PyCodeKG snapshot captured for branch `fix/snapshots`, version `0.9.2` (tree hash: 13ccf5691b60c09a52f3de6558036e676655d13c, timestamp: 2026-03-19T02:28:28). Metrics: 6975 nodes, 6937 edges, docstring coverage 93%, 2 critical issues.
- Monolithic install-hooks command and snapshot-first ordering (`cli.py`, `cmd_hooks.py`): Added `install-hooks` directly to `cli.py` and embedded `_PRE_COMMIT_HOOK` with snapshot-first ordering. No rebuild step; corpus is source-of-truth. Skip env var: `DIARYKG_SKIP_SNAPSHOT`. Install via `diarykg install-hooks --repo . --force`.
- Orchestrating hook for multi-KG snapshot (`src/kg_rag/cli/cmd_hooks.py`): New orchestrator snapshots all registered KGs before quality checks. Order: PyCodeKG, DocKG, FTreeKG, DiaryKG, then `pre-commit run`. Skip env var: `KGRAG_SKIP_SNAPSHOT`. Install via `kgrag install-hooks --repo . --force`.
- Bug and analysis reports: Added `analysis/bug_pre_commit_snapshot_ordering_20260318.md`, `analysis/pycode_kg_analysis_20260319.md`, and `analysis/snapshots_consistency_20260318.md`.

### Changed

- Snapshot ordering and skip env vars: Updated pre-commit hooks to snapshot before quality checks. Documented skip env vars for each tool: `PYCODEKG_SKIP_SNAPSHOT`, `DOCKG_SKIP_SNAPSHOT`, `FTREEKG_SKIP_SNAPSHOT`, `DIARYKG_SKIP_SNAPSHOT`, `KGRAG_SKIP_SNAPSHOT`.
- Dependency update: Updated `poetry.lock` and pinned `transformers>=5.3.0` in `pyproject.toml` to prevent incompatibility with `torch>=2.10.0`.

### Fixed

### Removed

## [0.9.2] - 2026-03-18

### Changed

- **`snapshot save` VERSION argument is now optional** (`cmd_snapshot.py`) — The positional `VERSION` argument is no longer required; it defaults to `""`. When omitted, the version is auto-detected from the installed `pycode-kg` package via `importlib.metadata`.
- **`SnapshotManager.capture` auto-detects version** (`snapshots.py`) — `version` parameter now defaults to `None`. If falsy, `_package_version()` resolves it from `importlib.metadata.version("pycode-kg")`, falling back to `"unknown"` if the package is not installed.
- **`Snapshot.version` is now optional with default `""`** (`snapshots.py`) — Moved `version` field after `metrics` to allow a default value; `from_dict` now calls `setdefault("version", "")` for forward compatibility with snapshots that omit the field.
- **Pre-commit hook no longer extracts version from `pyproject.toml`** (`cmd_hooks.py`) — Removed the `VERSION=$(grep …)` shell line; `pycodekg snapshot save` and `dockg snapshot save` are now invoked without a positional version argument, relying on each tool's own auto-detection. DocKG hook now passes `--tree-hash` for consistency.
- **`transformers>=5.3.0` pinned as a direct dependency** (`pyproject.toml`) — Previously an unpinned transitive dependency of `sentence-transformers`; `poetry lock` could resolve `5.2.0`, which is incompatible with `torch>=2.10.0` and causes a `RuntimeError` in `torch/overrides.py`. The explicit lower bound prevents this silent downgrade.

### Added

- **`poetry-check` pre-commit hook** (`.pre-commit-config.yaml`) — Runs `poetry install --check` before mypy and pytest, failing fast if the installed environment is out of sync with `poetry.lock`. Catches dependency version mismatches (e.g., a `poetry lock` downgrade) before tests run.

## [0.9.1] - 2026-03-17

### Added

- **`scripts/analyze_repo.sh`** — New shell script to clone any GitHub repo (`owner/repo` or URL), build a PyCodeKG knowledge graph, run thorough analysis, and save the report to `analysis/<repo>_analysis_<YYYYMMDD>.md`. Auto-detects the Python package subdirectory (`<repo>/`, `src/`, or all) and forwards extra flags to `pycodekg-build-sqlite`.
- **Per-phase progress timing in `run_analysis`** (`pycodekg_thorough_analysis.py`) — Each of the 15 analysis phases now prints `▶ Phase N/15: <name>… (Xs)` using a `_run_phase` helper, showing elapsed time per phase after completion.
- **Bug note: relative CLI path defaults** (`analysis/bug_relative_path_defaults_20260317.md`) — Detailed write-up of the systemic `--db`/`--sqlite`/`--lancedb` relative-path default bug across `pycode_kg`, `doc_kg`, and `FTreeKG`, including root cause, failure mode, fix checklist, and recommended helper pattern.

### Fixed

- **`build-sqlite` and `build` write SQLite/LanceDB to wrong directory** (`cmd_build.py`, `cmd_build_full.py`) — `--db` defaulted to the relative path `.pycodekg/graph.sqlite`, resolved against CWD rather than `--repo`. Running `pycodekg build-sqlite --repo /other/repo` would silently overwrite the CWD repo's own graph. Fixed by defaulting `--db` and `--lancedb` to `None` and resolving them against `repo_root` in the function body, consistent with how `build-lancedb` already worked.
- **Infinite recursion in `_compute_depth` on cyclic inheritance graphs** (`pycodekg_thorough_analysis.py`) — Large repos with circular INHERITS edges (introduced via sym: resolution) caused a `RecursionError`. Fixed with a `-1` in-progress sentinel in the memo dict: if a class is encountered during its own recursion, `max(-1, 0)` returns 0 and breaks the cycle.
- **Phase 6 (module coupling) hangs on large repos** (`_analyze_module_coupling`) — Replaced per-module loop (N × 3 SQL round-trips, each a 4-table join through sym:/RESOLVES_TO edges) with two bulk queries: one for all importer/importee pairs, one for all node-kind counts. Phase now runs in O(1) DB round-trips regardless of module count; confirmed on matplotlib (~400 modules). Removed now-unused `rich.progress` imports.
- **"Loading weights" tqdm progress bar suppressed** (`SentenceTransformerEmbedder.__init__`) — Safetensors weight-materialization tqdm bar during `SentenceTransformer` init now suppressed via `TQDM_DISABLE=1` (restored afterward). `hf_logging.set_verbosity_error()` was already present but does not affect tqdm output.
- **`analyze` continues silently with empty report when DB is missing** (`pycodekg_thorough_analysis.py`) — Missing database now prints a clear `ERROR` message and exits early instead of proceeding with 0 nodes and generating a misleading report.

### Changed

- **Richer platform info in analysis report metadata** (`_get_report_metadata`) — Platform line now includes macOS version, architecture, processor family, and hostname in addition to Python version. Enables distinguishing reports generated on different machines.

## [0.10.0] - 2026-03-14

### Added

- **KGModule SDK** (`src/pycode_kg/module/`) — A base infrastructure layer for building production-grade knowledge graphs for any domain. Implement a single `KGExtractor` class and get SQLite persistence, LanceDB vector indexing, hybrid query, snapshot management, and MCP server automatically. Includes `KGModule` (base class), `KGExtractor` (extraction interface), `NodeSpec`/`EdgeSpec` (declarative schema), and `PyCodeKGExtractor` (Python-specific implementation).
- **KGModule Developer Guide** (`docs/KGMODULE.md`) — Comprehensive guide for building custom knowledge graphs with the new KGModule SDK, including quick-start example and architecture overview.

### Changed

- **PyCodeKG refactored to inherit from KGModule** (`src/pycode_kg/kg.py`) — `PyCodeKG` now inherits from `KGModule` instead of reimplementing all infrastructure. Focuses on Python-specific extraction (CodeGraph / AST parsing) while delegating SQLite, LanceDB, query engine, and snapshot management to the base class. Result types (`BuildStats`, `QueryResult`, `Snippet`, `SnippetPack`) moved to `pycode_kg.module.types` and re-exported from `kg.py` for backwards compatibility.
- **Exports updated** (`src/pycode_kg/__init__.py`) — Added KGModule SDK classes to the public API: `KGModule`, `KGExtractor`, `PyCodeKGExtractor`, `NodeSpec`, `EdgeSpec`. Documentation updated to highlight the new SDK import pattern.

## [0.9.0] - 2026-03-14

### Added

- **Claude Desktop/Chat MCP integration reference** (`docs/claude_chat_global_mcp.json`) — Example configuration for Claude Chat and Claude Desktop showing proper MCP server setup patterns for future reference.
- **PyCodeKG analysis document** (`analysis/pycode_kg_analysis_20260314.md`) — Current state analysis of codebase metrics and architectural assessment.

### Added (Previous)

- **`explain(node_id, limit=10)` parameter** (`mcp_server.py`) — New `limit` parameter controls the maximum number of callers and callees displayed in the explanation output. Pass `limit=0` to show all callers and callees without truncation (default 10). Updated MCP tool documentation and FastMCP instructions to reflect the new parameter.
- **Per-module node count tracking in snapshots** (`snapshots.py`, `mcp_server.py`) — `SnapshotMetrics` now includes `module_node_counts` field mapping module paths to node counts. `SnapshotManager` accepts optional `db_path` parameter; when provided, `capture()` queries per-module node counts from the SQLite graph. `snapshot_diff()` returns `module_node_counts_delta` showing per-module node count changes between snapshots.
- **PyCodeKG assessment documents** (`assessments/`) — Independent evaluations comparing PyCodeKG's MCP tools against Claude Sonnet 4.6 and GPT-4.1 across all 17 tools, including per-tool ratings, architectural insights, and strengths/weaknesses analysis.
- **Test suite for snapshot functionality** (`tests/test_snapshots.py`) — 128 new lines of comprehensive tests for snapshot capture, retrieval, and comparison operations.

### Changed

- **MCP server configuration documentation** (`docs/MCP.md`) — Added prominent warnings and guidance on the critical requirement that `.mcp.json`, `.vscode/mcp.json`, and `claude_desktop_config.json` must use absolute paths for all commands and arguments. MCP clients do not inherit shell working directory. Added notes that `.mcp.json` should be frozen after setup and regenerated via `/setup-mcp` rather than hand-edited. Enhanced troubleshooting section with explicit path checks.
- **Output cleanup: removed emoji characters** (`app.py`, `architecture.py`, `pycodekg_thorough_analysis.py`, `viz3d_timeline.py`, CLI commands) — Systematically removed emoji (🔥, ⚠️, ✨, ✅, 📄, 📂, 🔨, etc.) from Markdown output, Streamlit UI, and terminal messages. Replaced with text equivalents for better compatibility across tools and platforms. This supports better output handling in non-emoji-aware contexts.
- **Call chain analysis depth increased** (`pycodekg_thorough_analysis.py`) — Analysis now traces up to 6 hops in call chains (previously 3) for more comprehensive detection of complex dependencies across multiple module boundaries.
- **Snapshot analysis concerns refined** (`pycodekg_thorough_analysis.py`) — Removed "error handling exception recovery" from the concerns list to focus on the most impactful analysis categories. Concerns docstring simplified for clarity.
- **`doc-kg` dependency** (`pyproject.toml`) — Replaced local path reference (`../doc_kg`) with git source (`https://github.com/Flux-Frontiers/doc_kg.git`) so CI runners can install it without requiring a sibling checkout.

### Removed

- **Large embedder benchmark JSON files** (`analysis/`) — Removed `embedder_benchmark_20260311_000046.json` and `embedder_benchmark_20260311_005014.json` (7418 lines combined) in favor of summary documentation. Benchmark data is preserved in `analysis/embedder_benchmark_summary.md`.

### Fixed

- **`hybrid_rank.py` syntax error** — Removed orphaned `def rerank_hybrid(...)` stub (no body) that caused a parse error blocking ruff and CI. Replaced inline `lambda` with a proper `def norm()` to satisfy `E731`.
- **Ruff formatting** — Applied `ruff format` across 14 files (`bridge.py`, `centrality.py`, `cmd_bridges.py`, `cmd_build.py`, `cmd_build_full.py`, `cmd_framework_nodes.py`, `pycodekg_thorough_analysis.py`, `mcp_server.py`, `coderank.py`, `snapshots.py`, `store.py`, `cli_rank.py`, `test_coderank.py`, `test_snapshots.py`, `test_centrality.py`).
- **Ruff lint auto-fixes** — Resolved 14 lint errors: unsorted import blocks (`I001`), unused `defaultdict` import (`F401`), `typing` → `collections.abc` upgrades (`UP035`), `timezone.utc` → `datetime.UTC` alias (`UP017`), unused `exc` variable in broad except (`F841`).
- **mypy `src`-layout duplicate module error** — `bridge_tools.py` and `framework_tools.py` used `from src.pycode_kg...` imports; corrected to `from pycode_kg...`. Added `mypy_path = "src"` and `explicit_package_bases = true` to `[tool.mypy]`.
- **mypy type errors** — Fixed pre-existing type errors: annotated `contributors` as `list[dict[str, Any]]` in `centrality.py`; renamed `payload` to `node_payload` in `cmd_centrality.py`; used typed `contained_nodes` variable in `kg.py`.

## [0.8.0] - 2026-03-12

### Added

- **`--exclude-dir` / `[tool.pycodekg].exclude` directory exclusion** (`config.py`, `graph.py`, `pycodekg.py`, `cli/options.py`, `cli/cmd_build.py`, `cli/cmd_build_full.py`, `cli/cmd_analyze.py`, `pycodekg_thorough_analysis.py`) — Complementary counterpart to the existing `--include-dir` allowlist. A new `exclude_option` reusable Click decorator adds `--exclude-dir DIR` (repeatable) to `build-sqlite`, `build`, and `analyze` commands. Excluded directory names are pruned at every depth of the walk, combined with the built-in `SKIP_DIRS`. CLI flags are merged with `[tool.pycodekg].exclude` from `pyproject.toml`. `load_exclude_dirs()` added to `config.py` alongside `load_include_dirs()`; both now share a private `_load_dir_list()` helper. `CodeGraph`, `iter_python_files`, and `extract_repo` all accept the new `exclude` parameter. `PyCodeKGAnalyzer` and analysis report metadata now record `exclude_dirs` alongside `include_dirs`.
- **DocKG MCP server registered** (`.mcp.json`) — `dockg` server entry added alongside `pycodekg`, enabling cross-querying of code and document knowledge graphs within the same Claude Code session.
- **`.dockg/` gitignore pattern** (`.gitignore`) — Transient DocKG artifacts (LanceDB vectors, SQLite graph, model cache) are excluded, mirroring the `.pycodekg/` pattern. `.dockg/snapshots/` is intentionally left untracked to allow snapshot commits once that feature is added to DocKG.
- **Structural Importance Ranking (SIR)** (`src/pycode_kg/analysis/centrality.py`, `src/pycode_kg/cli/cmd_centrality.py`, `src/pycode_kg/sql/004_add_centrality_table.sql`, `tests/test_centrality.py`) — Deterministic weighted PageRank over the sym-stub-resolved PyCodeKG graph. Edge weights are tuned per relation type (`CALLS` 1.0 > `INHERITS` 0.8 > `IMPORTS` 0.45 > `CONTAINS` 0.15) with a 1.5× cross-module boost and a 0.85× private-symbol penalty. Supports node-level and module-level (`--group-by module`) rankings, configurable top-N, and optional persistence to a `centrality_scores` SQLite table. Exposed as `pycodekg centrality` CLI command and `pycodekg-centrality` script entry point.
- **`centrality` MCP tool** (`mcp_server.py`) — New `centrality(top, kinds, group_by)` tool exposing SIR PageRank scores directly to AI agents. Returns a Markdown ranking table with scores, member counts, and module paths. Documented in CLAUDE.md MCP tools table and FastMCP instructions block.
- **`src/pycode_kg/analysis/` package** (`analysis/__init__.py`) — New analysis sub-package exporting `CentralityConfig`, `CentralityRecord`, `StructuralImportanceRanker`, and `aggregate_module_scores`.
- **SIR module-level ranking in `analyze_repo()` and analysis report** (`pycodekg_thorough_analysis.py`, `analysis/pycode_kg_analysis_20260311.md`) — Thorough analysis now includes a "Structural Importance Ranking" section showing per-module weighted PageRank scores. Analysis report regenerated against current graph (5503 nodes, 5372 edges).
- **SIR algorithm documentation** (`docs/structural_importance.md`) — Full specification of the SIR algorithm: graph construction, edge weighting, cross-module boosting, private-symbol penalty, module aggregation, and integration point in the build pipeline.
- **SIR integration notes and PR template** (`docs/integration_notes.md`, `docs/pull_request_template.md`) — Guides for wiring SIR into the PyCodeKG repo and a ready-made PR description.
- **GPT-4.1 and Haiku 4.5 assessments** (`assessments/PyCodeKG_assessment_gpt-4.1_2026-03-11.md`, `assessments/PyCodeKG_assessment_haiku_4-5_2026-03-11.md`) — Independent agent evaluations of all PyCodeKG MCP tools; both award 5/5 overall.
- **PyCodeKG Agent Assessment Protocol** (`assessments/AssessmentProtocol_PyCodeKG.md`) — Standardized evaluation framework for assessing PyCodeKG's utility across all MCP tools. Includes four phases (orientation, semantic search, structural navigation, temporal analysis), eight evaluation dimensions (accuracy, relevance, completeness, efficiency, insight generation, usability, architectural value, uniqueness), and required sections for reproducible agent-based assessments.
- **`list_nodes` MCP tool** (`mcp_server.py`, `docs/MCP.md`, `.claude/skills/pycodekg/SKILL.md`, `CHEATSHEET.md`) — New tool to list nodes filtered by module path prefix and/or kind (e.g. `function`, `class`), returning a JSON array of matching nodes. Useful for enumerating module contents before focused inspection.
- **Claude Sonnet 4.6 and GPT-5 assessments** (`assessments/`) — Two new independent agent evaluations of all PyCodeKG MCP tools against a real codebase, surfacing actionable weaknesses and confirming tool strengths.
- **Global CodeRank structural ranking** (`src/pycode_kg/ranking/`, `tests/test_coderank.py`) — New deterministic PageRank-based scoring over the repository graph, exposed via `pycodekg rank` CLI command and three MCP tools (`rank_nodes`, `query_ranked`, `explain_rank`). Includes support for hybrid/code-aware scoring, persistence metric option, and explanatory score components. A companion documentation bundle (`docs/CODERANK.md`, `docs/RANKING_INTEGRATION.md`, `docs/BUNDLE_NOTES.md`) explains usage and integration, while CLI helpers `cmd_bridges.py` and `cmd_framework_nodes.py` power bridge-centrality and framework-node analysis. Core algorithms live in `src/pycode_kg/ranking/` and new MCP helpers in `src/pycode_kg/mcp/bridge_tools.py` and `framework_tools.py`.
- **Embedder benchmark and canonical model selection** (`analysis/embedder_benchmark_summary.md`, `scripts/benchmark_embedders.py`) — Benchmarked five embedding models (`all-MiniLM-L6-v2`, `all-MiniLM-L12-v2`, `BAAI/bge-small-en-v1.5`, `all-mpnet-base-v2`, `microsoft/codebert-base`) across two independent runs (350 indexed nodes, three query types, all rerank modes). `BAAI/bge-small-en-v1.5` is confirmed as the canonical model — highest discriminative hybrid scores across all query types, compact 384-dim space, sub-1.5s build. `microsoft/codebert-base` produces a degenerate embedding space for metadata-based retrieval (uniform ~0.90 cosine scores; zero discrimination) and is explicitly ruled out. Results and rationale documented in `analysis/embedder_benchmark_summary.md`.
- **Claude Opus 4 assessment** (`analysis/PyCodeKG_assessment_claude_opus_4_2026-03-10.md`) — Independent multi-agent evaluation of all PyCodeKG MCP tools.
- **`_normalize_query_text` helper** (`kg.py`) — New preprocessing function that converts `_` and `-` separators to spaces before embedding, giving the sentence-transformer token-level signal for identifier-style and CLI queries such as `missing_lineno_policy` or `pycodekg-build-lancedb`.
- **Analysis report 2026-03-10** (`analysis/pycode_kg_analysis_20260310.md`) — Self-analysis of pycode_kg post-rebuild on `src/`-only graph. Grade A (100/100), 96.8% docstring coverage, zero orphaned functions.
- **Hybrid lexical reranking for `query_codebase` and `pack_snippets`** (`kg.py`, `mcp_server.py`) — Both query paths now accept `rerank_mode` (`legacy` / `semantic` / `hybrid`), `rerank_semantic_weight`, and `rerank_lexical_weight` parameters. `legacy` preserves existing hop-first ordering; `semantic` ranks by vector similarity score; `hybrid` blends semantic and lexical overlap scores using the supplied weights. Added `_query_tokens()`, `_docstring_signal()`, and `_lexical_overlap_score()` helper functions.
- **Per-result relevance metadata on returned nodes** (`kg.py`) — Each node in `QueryResult` and `SnippetPack` now carries a `relevance` dict with `score`, `semantic`, `lexical`, `docstring_signal`, `hop`, `via_seed`, and `mode` fields. `SnippetPack.to_markdown()` renders these as a relevance line per node header.
- **`missing_lineno_policy` and `SnippetPack.warnings`** (`kg.py`, `mcp_server.py`) — `pack_snippets` accepts a `missing_lineno_policy` parameter (`cap_or_skip` by default). When a non-module node lacks `lineno`, the policy falls back to the parent's span (capped to `min(max_lines, max(20, context * 4))`) or omits the snippet if no parent span is available. All such decisions emit a warning string collected in the new `warnings` field on `SnippetPack` and rendered in the Markdown output.
- **Edge provenance enrichment via `include_edge_provenance`** (`mcp_server.py`) — Both `query_codebase` and `pack_snippets` accept `include_edge_provenance: bool = False`. When enabled, inferred edges (RESOLVES_TO or edges involving `sym:` stubs) are annotated with `inferred`, `confidence`, and `provenance` fields derived from stored resolution evidence metadata.
- **Snapshot freshness indicators** (`mcp_server.py`) — `snapshot_list`, `snapshot_show`, and `snapshot_diff` responses now include a `freshness` payload comparing each snapshot's `total_nodes` count against the currently loaded graph DB: `snapshot_total_nodes`, `current_total_nodes`, `delta_nodes`, `is_fresh`, and `status` (`fresh` / `behind` / `ahead`).
- **Visitor now populates source metadata eagerly** (`visitor.py`, `pycodekg.py`) — `PyCodeKGVisitor._get_node_id()` initializes node records with `lineno`, `end_lineno`, and `docstring` fields (previously absent). New `_set_node_source_meta()` method patches these fields from the AST node on `visit_ClassDef` and function visits. `extract_repo()` reads and forwards `lineno`, `end_lineno`, and `docstring` from visitor props instead of hardcoding `None`.
- **GPT-5.3 Codex assessment** (`analysis/PyCodeKG_assessment_gpt_5_3_codex_2026-03-09.md`) — Independent evaluation of all PyCodeKG MCP tools by GPT-5.3 Codex, covering per-tool ratings, comparison vs. default workflow, and architectural observations.
- **Test: nested function nodes carry line metadata** (`tests/test_kg.py`) — New `test_nested_function_nodes_have_line_metadata` verifies that `outer.inner`-style nested function nodes have non-None `lineno` and `end_lineno` after graph construction.
- **Inheritance hierarchy analysis — Phase 10** (`pycodekg_thorough_analysis.py`) — `_analyze_inheritance()` queries all `INHERITS` edges from the SQLite store, resolves `sym:` stubs via `RESOLVES_TO`, computes per-class inheritance depth, detects multiple-inheritance usage, and flags diamond patterns (shared ancestors that can cause MRO surprises). Results are stored in `PyCodeKGAnalyzer.inheritance_analysis`, surfaced in `_generate_insights()` (diamonds → issue, multiple-inheritance-without-diamonds → strength), included in `to_dict()`, and rendered in full detail by both `to_markdown()` and the CLI print path.
- **Claude Sonnet 4.6 assessment** (`analysis/PyCodeKG_assessment_claude_sonnet_4_6_20260309.md`) — Independent evaluation of all PyCodeKG MCP tools using Claude Sonnet 4.6, including per-tool ratings, quantified comparison vs. default workflow, and architectural insights from the assessor's perspective.

### Changed

- **`doc-kg` dependency switched to editable path install** (`pyproject.toml`, `poetry.lock`) — Changed from `file://` URI snapshot to `{path = "../doc_kg", develop = true}`. Changes pushed to the `doc_kg` repo are now immediately live in the `pycode_kg` venv without reinstalling. Dependency name corrected from `dock-kg` to `doc-kg` to match the package name.
- **`[tool.dockg]` exclude config added to `pyproject.toml`** — Documents the active exclude list (`.dockg`, `.pycodekg`, `src`, etc.) for DocKG builds run from the `pycode_kg` repo root. This config is now read by DocKG's `load_exclude_dirs()` (added in the companion `doc_kg` change).
- **numpy analysis report refreshed** (`analysis/numpy_analysis_20260312.md`) — Re-run against a broader graph (126 666 nodes, 252 449 edges, 14 475 meaningful) after rebuilding with `--include-dir numpy --exclude-dir tests --exclude-dir benchmarks`. Elapsed time now included in report metadata.
- **Relevance score confidence tiers** (`kg.py`) — `SnippetPack.to_markdown()` now annotates each node's relevance score with a `[HIGH]`, `[MEDIUM]`, or `[LOW]` confidence label (thresholds: ≥0.60 HIGH, ≥0.45 MEDIUM, <0.45 LOW), making result quality immediately readable without requiring score interpretation.
- **`explain()` orchestrator detection** (`mcp_server.py`) — Role assessment now tracks callee count (fan-out) in addition to caller count. Nodes with ≥8 callees and at least one caller are labeled "🟡 Core orchestrator" — catching top-level entry points that have low fan-in but high coordination burden, rather than mis-classifying them as utilities.
- **`query_codebase` precision tip in MCP instructions** (`mcp_server.py`) — Tool description now recommends `min_score=0.5` for queries where the concept is well-known, to filter incidental docstring matches.
- **"Critical call chains" → "key call chains"** (`mcp_server.py`) — Toned down dramatic language in `analyze_repo()` tool description and docstring; matches terminology used in the analysis output.
- **`list_nodes` added to recommended workflow** (`mcp_server.py`) — "Explore unfamiliar code" workflow now includes `list_nodes` between `query_codebase` and `explain` for module enumeration.
- **Analysis report refreshed** (`analysis/pycode_kg_analysis_20260311.md`) — Re-generated against current graph (5503 nodes, 5372 edges, commit `3adc0f5`).
- **`get_node` returns Markdown instead of JSON** (`mcp_server.py`) — `get_node()` now renders a structured Markdown report (heading, module path, line range, stable ID, docstring) instead of a raw JSON blob. When `include_edges=True`, outgoing edges and incoming callers are rendered as labelled Markdown sections. The error response is also Markdown. Docstring, `:param:`, and `:return:` updated to match. The `FastMCP` instructions block and module-level `Tools` docstring updated accordingly (example workflow added; `graph_stats` and `callers` descriptions clarified).
- **`graph_stats` returns Markdown instead of JSON** (`mcp_server.py`) — `graph_stats()` now returns a formatted Markdown summary with bullet-point totals and two tables (nodes by kind, edges by relation). `meaningful_nodes` is highlighted with an explanatory annotation. Docstring and `FastMCP` instructions updated.
- **Default embedding model changed to `BAAI/bge-small-en-v1.5`** (`pycodekg.py`, `app.py`, `README.md`) — `DEFAULT_MODEL` and all UI defaults updated from `all-MiniLM-L6-v2`; `PYCODEKG_MODEL` env-var override is still supported.
- **`_query_tokens` splits snake_case for lexical matching** (`kg.py`) — Tokens like `missing_lineno_policy` now expand into constituent parts (`missing`, `lineno`, `policy`) in addition to the full token, improving hybrid lexical overlap scores for parameter-style and CLI queries.
- **`.gitignore` extended for alternative LanceDB directories** — Added `.pycodekg/lancedb-*` to cover variant index paths created during benchmarking and model comparison workflows.
- **Directory filtering replaced: `exclude` → `include`** (`config.py`, `graph.py`, `pycodekg.py`, `cli/options.py`, `cli/cmd_build.py`, `cli/cmd_build_full.py`, `cli/cmd_analyze.py`, `pycodekg_thorough_analysis.py`) — The `--exclude-dir`/`[tool.pycodekg].exclude` mechanism is replaced by `--include-dir`/`[tool.pycodekg].include`. Users now specify which top-level directories to index (allowlist) rather than which to skip (denylist). When no `include` is configured, all directories are walked, preserving backward-compatible defaults. `load_exclude_dirs()` → `load_include_dirs()`; `CodeGraph(exclude=...)` → `CodeGraph(include=...)`; `iter_python_files(exclude=...)` → `iter_python_files(include=...)`. `pyproject.toml` updated from `exclude = ["tests", "scripts"]` to `include = ["src"]`. README and CLAUDE.md updated accordingly.
- **`tests/test_exclusions.py` updated for include semantics** — All fixtures, test names, and assertions migrated from exclude to include model.
- **MCP tool signatures and instructions updated** (`mcp_server.py`, docs, skills, cheatsheets) — `query_codebase` and `pack_snippets` module docstring and `FastMCP` instructions block updated to reflect new parameters (`rerank_mode`, `rerank_semantic_weight`, `rerank_lexical_weight`, `missing_lineno_policy`, `include_edge_provenance`). All skills, cheatsheets, and documentation files updated to match.
- **MCP docs-sync policy made explicit for contributors** (`CLAUDE.md`, `README.md`, `.claude/commands/sync-mcp-docs.md`) — Added a required rule and checklist: any MCP API change in `src/pycode_kg/mcp_server.py` must update the module `Tools` docstring list and the `FastMCP(..., instructions=...)` block in the same commit.
- **Fan-in risk thresholds are now relative** (`pycodekg_thorough_analysis.py`) — The three fan-in risk bands (critical / high / medium) previously used hard-coded absolute thresholds (`>1000`, `>500`, `>100`) that were never triggered on realistic codebases. They are now computed as a fraction of the graph's `meaningful_nodes` count: critical ≥ 5%, high ≥ 2%, medium ≥ 0.5% (with sensible absolute floors of 15, 5, and 2 respectively).
- **`explain()` role assessment uses relative thresholds** (`mcp_server.py`) — The "high-value" and "important" labels in `explain()` now use the same relative threshold logic (top 5% / top 2% of meaningful nodes) instead of the previous static caller-count limits of 50 and 10. The emitted description now includes the computed threshold so readers understand the scale.
- **Analysis files consolidation** (`analysis/`) — Old dated analysis files from 2026-03-02 through 2026-03-06 removed; `pycode_kg_analysis_20260309.md` refreshed with latest run output (updated timestamps, relative-risk table, new inheritance section); assessment file renamed to canonical `snake_case` filename.
- **Snapshot API documentation finalized** (`README.md`, `docs/SNAPSHOTS.md`, `docs/MCP.md`, `docs/CHEATSHEET.md`) — All references updated to reflect tree-hash-only snapshot model; removed mentions of commit hash as snapshot key; clarified that tree hash is the sole stable identifier for snapshots.
- **Symbol resolution now prefers exact qualified matches and records confidence** (`store.py`) — `resolve_symbols()` now attempts dotted qualified-name matching before name-only fallback, supports `src/` layout module aliases, and writes evidence metadata (`resolution_mode`, `confidence`, and ambiguity count) on `RESOLVES_TO` edges.
- **Caller resolution uses import-aware filtering for ambiguous stubs** (`store.py`) — `callers_of()` now validates stub-based callers against the caller module's matching import symbols, reducing false-positive fan-in links when multiple same-name definitions exist.
- **Hybrid query and snippet pack gained precision controls** (`kg.py`, `mcp_server.py`) — Added `min_score` (seed threshold from `1 - distance`) and `max_per_module` (module diversity cap) to both query paths and exposed them via MCP tool signatures.
- **Legacy snapshot deltas are now backfilled on load** (`snapshots.py`) — `load_snapshot()` computes missing `vs_previous`/`vs_baseline` from manifest chronology so older snapshot files still return complete delta information.

### Removed

- **GitHub composite action removed** (`.github/actions/pycodekg-action/`) — The `action.yml` and `README.md` for the GitHub composite action have been removed; the pre-commit hook workflow is the supported snapshot capture path.
- **Backward compatibility for commit field in snapshots** (`snapshots.py`) — Removed `from_dict()` fallback that handled deserialization of old snapshot JSON containing a `commit` field. Snapshots now require `tree_hash` as the sole key. Old snapshot files should be migrated or regenerated using `pycodekg snapshot save`.

### Fixed

- **Snapshot diff explicit issue tracking** (`snapshots.py`, `mcp_server.py`, `cmd_snapshot.py`) — `snapshot_diff` and the `pycodekg snapshot diff` CLI now explicitly compute and list newly introduced and resolved issues between snapshots.
- **Snapshot freshness tolerance** (`mcp_server.py`) — `_snapshot_freshness` now reports a `near_fresh` status with an explanatory note when the node count delta is >0 but <50, reducing false "behind" signals caused by `sym:` stub accumulation between rebuilds.
- **Architectural analysis risk levels simplified** (`pycodekg_thorough_analysis.py`) — Removed arbitrary critical/high/medium risk tiering for fan-in and fan-out metrics. Functions are now ranked purely by absolute caller count for greater objectivity. Call chains spanning multiple modules are now reliably detected.
- **Snapshot list display now shows timestamps** (`cmd_snapshot.py`) — The `pycodekg snapshot list` table output now includes a `Timestamp` column formatted as `YYYY-MM-DD HH:MM`, improving usability when reviewing snapshot history. Table header and widths adjusted for readability.
- **Snapshot API field `tree_hash` renamed to `key`** (`snapshots.py`, `cmd_snapshot.py`, `mcp_server.py`, `tests/test_snapshots.py`) — Aligns snapshot serialization with MCP tool parameter naming (`snapshot_show`, `snapshot_diff` use `key`, `key_a`, `key_b`). Old snapshots with `tree_hash` field are automatically migrated to `key` on load, with backward-compatible deserialization.
- **`_semantic_score_from_distance` bounded transform** (`kg.py`) — Distance values from `BAAI/bge-small-en-v1.5` and other models can exceed 1.0; the previous `1 - distance` formula collapsed those scores to 0, silently dropping valid seeds. Changed to `1 / (1 + d)`, a monotonic bounded transform that keeps all seeds in `(0, 1]` and makes `min_score` filtering behave correctly for any metric.

## [0.7.1] - 2026-03-09

### Changed

- **Snapshot identifiers migrated fully to tree hashes** (`snapshots.py`, `cmd_snapshot.py`, `mcp_server.py`) — Removed the `commit` field from `Snapshot` entirely; `tree_hash` is now the sole stable key. `capture()` no longer accepts a `commit` parameter and auto-detects the tree hash via `git rev-parse HEAD^{tree}`. `snapshot_show` and `snapshot_diff` MCP tools rename their parameters from `commit`/`commit_a`/`commit_b` to `key`/`key_a`/`key_b`. CLI `snapshot show` and `snapshot diff` arguments likewise renamed. `from_dict()` handles backward-compat deserialization of old JSON that contained a `commit` field, using it as the `tree_hash` value when `tree_hash` is absent.
- **`pycodekg snapshot save` drops `--commit` option** (`cmd_snapshot.py`) — The `--commit` CLI flag is removed; commit hash is no longer stored or displayed. The save output now shows `Key:` instead of `Commit:`.
- **Default embedding model reverted to all-MiniLM-L6-v2** (`pycodekg.py`) — Changed from `microsoft/codebert-base` to `all-MiniLM-L6-v2` (default from `PYCODEKG_MODEL` env var). CodeBERT is a masked LM optimized for code understanding tasks, not semantic similarity retrieval; MiniLM provides better semantic search quality for query/pack operations.
- **Logging suppression refactored** (`index.py`) — `suppress_ingestion_logging()` no longer monkey-patches `tqdm.__init__`. Instead, sets `os.environ["TQDM_DISABLE"] = "1"` at runtime, which is more reliable and cleaner.
- **Module coupling Incoming/Outgoing now uses direct SQL** (`pycodekg_thorough_analysis.py`) — Replaced `callers(rel="IMPORTS")` and `kg.query("imports from …")` (both of which returned empty results because IMPORTS edges point to `sym:` stubs, not module nodes) with parameterized SQL queries that traverse the `IMPORTS → RESOLVES_TO` chain to find true inter-module dependencies. Incoming and outgoing dependency counts are now accurate.
- **Critical call chains trace forward through CALLS edges** (`pycodekg_thorough_analysis.py`) — `_analyze_critical_paths()` previously built chains by listing callers of a function in reverse, producing misleading output. It now follows `CALLS` edges forward from each high-fan-in function (resolving `sym:` stubs via `RESOLVES_TO`), building an actual execution path up to 4 nodes deep and prepending one representative caller for context.
- **`scripts/` excluded from analysis** (`pyproject.toml`) — Added `"scripts"` to `[tool.pycodekg] exclude` list alongside `"tests"` so utility scripts are not indexed into the knowledge graph.

### Removed

### Fixed

- **`explain()` callees no longer include builtins** (`mcp_server.py`) — Added `and dst_node.get("module_path")` guard to filter out stdlib/builtin symbol nodes from the callee list in natural-language node explanations.
- **`snapshot_list()` `vs_previous` deltas no longer null** (`snapshots.py`) — `list_snapshots()` now computes `vs_previous` on-the-fly for entries that lack persisted deltas, so all entries in the list carry accurate metric comparisons.
- **`snapshot_diff()` now includes per-kind node/edge breakdown** (`snapshots.py`) — `diff_snapshots()` returns `node_counts_delta` and `edge_counts_delta` dicts (by kind/relation) in addition to aggregate totals.
- **`analyze_repo()` public API detection expanded** (`pycodekg_thorough_analysis.py`) — Phase 8 now includes non-private classes with `fan_in >= 1` and performs a SQL scan of `__init__.py` `__all__` exports, in addition to top-level functions.
- **`analyze_repo()` fan-in phase uses `k=500`** (`pycodekg_thorough_analysis.py`) — Prevents silent cutoff of indexed nodes when the repository has more than the default `k` entries.
- **Embedding index text augmented with KEYWORDS** (`index.py`) — `_build_index_text()` now appends a `KEYWORDS:` section with snake_case tokens derived from the node's name and module path, improving recall for abstract queries.
- **Embedder initialization now suppresses ingestion logging** (`kg.py`) — `suppress_ingestion_logging()` is now called before initializing `SentenceTransformerEmbedder` in the embedder property getter, ensuring verbose model loading output is silenced.

## [0.7.0] - 2026-03-08

### Added

- **`--tree-hash` option for `pycodekg snapshot save`** (`cmd_snapshot.py`) — New CLI flag accepts a git tree hash as the snapshot file key, enabling pre-commit mode. The hook always passes `--tree-hash "$(git write-tree)"`, making tree hash the primary key; commit hash is auto-detected as display metadata only.
- **`Snapshot.key` property and `tree_hash` field** (`snapshots.py`) — `Snapshot` gains a `tree_hash: str` field and a `key` property (`tree_hash or commit`). `save_snapshot` uses `snapshot.key` as the filename; manifest entries now include `key` and `tree_hash` fields. All lookup methods (`get_previous`, `get_baseline`, `load_snapshot`, `diff_snapshots`) resolve by `key` with fallback to `commit` for backward compatibility.

### Changed

- **Git hook migrated from post-commit to pre-commit** (`cmd_hooks.py`) — `pycodekg install-hooks` now installs a `pre-commit` hook instead of `post-commit`. The hook uses `git write-tree` to key the snapshot by the staged tree hash (removing the dependency on the commit hash as the file key), then stages `.pycodekg/snapshots/` so the snapshot ships atomically inside the commit that produced it.
- **`.pycodekg/snapshots/` is now tracked in git** — Removed from `.gitignore`; the pre-commit hook stages snapshot files automatically, no manual `git add` needed. Added `.pycodekg/graph.sqlite*` to cover WAL/SHM sidecar files.
- **Removed GitHub Actions snapshot workflow** (`.github/workflows/snapshots.yml`) — CI capture workflow is superseded by the pre-commit hook; snapshots now ship with every commit.
- **Documentation updated throughout** (`docs/SNAPSHOTS.md`, `docs/MCP.md`, `docs/CHEATSHEET.md`) — All references to post-commit hook, commit-hash keys, and local-only artifacts updated to reflect pre-commit mode, tree-hash keys, and git-tracked snapshots.
- **VS Code pytest settings** (`.vscode/settings.json`) — Added `python.testing.pytestArgs`, `pytestEnabled`, and `unittestEnabled` for test discovery.
- **Analysis filtering fix** (`pycodekg_thorough_analysis.py`) — Excluded `@property` methods from orphan detection to prevent spurious warnings for decorated methods with minimal direct callers.

### Removed

### Fixed

## [0.6.1] - 2026-03-08

### Added

- **`snapshot_list`, `snapshot_show`, `snapshot_diff` MCP tools** (`mcp_server.py`) — Three new temporal snapshot tools exposed via the MCP server. At this release, the tool signatures used commit-style parameter names (`snapshot_show(commit)`, `snapshot_diff(commit_a, commit_b)`); these were later renamed to key-based parameters in `0.7.1` (`snapshot_show(key)`, `snapshot_diff(key_a, key_b)`). `snapshot_list(limit)` returns snapshots in reverse chronological order with per-snapshot deltas. `SnapshotManager` is now initialised in `main()` alongside `PyCodeKG`.
- **`get_node(include_edges)` enhancement** (`mcp_server.py`) — `get_node` gains an optional `include_edges: bool = False` parameter. When `True`, the response includes the node's immediate neighborhood: outgoing edges grouped by relation type (CALLS, CONTAINS, IMPORTS, INHERITS) and resolved incoming CALLS callers — eliminating a separate `callers()` round-trip for routine node inspection.
- **Snapshot types in public API** (`__init__.py`) — `Snapshot`, `SnapshotDelta`, `SnapshotManager`, and `SnapshotMetrics` are now exported from the top-level `pycode_kg` package.
- **Claude Opus 4.6 assessment** (`analysis/Opus_Assessment.md`) — New independent evaluation of all six PyCodeKG MCP tools by Claude Opus 4.6, including per-tool ratings, quantified comparison against the model's default (non-PyCodeKG) workflow (~5× tool-call reduction), and architectural analysis of the tool's design. Confirms PyCodeKG is unique among MCP code-analysis tools.
- **MCP server description updated** (`mcp_server.py`) — `FastMCP` instructions string extended with documentation for the three new snapshot tools and updated `get_node` description; recommended workflow updated to reflect `get_node(include_edges=True)` and the new `snapshot_list → snapshot_diff` pattern.

### Changed

- **Analysis report refreshed** (`analysis/pycode_kg_analysis_20260308.md`) — Metrics updated to latest rebuild: 4,911 nodes (+129), 4,834 edges (+109), 101 functions (+7), 167 methods (+1), 96.5% docstring coverage; commit ref updated to `7f80d09`.

## [0.6.0] - 2026-03-08

### Added

- **`viz` optional extra** — `streamlit`, `pyvis`, and `plotly` are now optional dependencies. Install with `pip install "pycode-kg[viz]"`. The `pycodekg viz` and `pycodekg viz-timeline` commands emit a clear error if the extra is not installed.
- **`publish` skill** (`.claude/skills/publish/SKILL.md`) — New skill documenting the step-by-step release workflow for publishing pycode-kg to PyPI using Poetry. Covers version bumping (semantic versioning), CHANGELOG updates, git tagging, building distributions, publishing, and rollback procedures.
- **`pycodekg install-hooks` CLI command** (`src/pycode_kg/cli/cmd_hooks.py`) — New command that, at this release, installed a post-commit git hook to capture a metrics snapshot automatically after every commit. The hook ran silently in the background, tagging each snapshot with the real commit hash and storing it in `.pycodekg/snapshots/` as a local artifact. Supports `PYCODEKG_SKIP_SNAPSHOT=1` env var to skip the hook. Use `--force` to overwrite an existing hook. (This behavior was later migrated to pre-commit tree-hash mode in `0.7.0`.)
- **`explain()` MCP tool** (`mcp_server.py`) — New tool that returns a natural-language explanation of a code node by its ID. Returns a markdown-formatted explanation with metadata (module, location), docstring, callers (top 10), and callees. Ideal for understanding node roles without reading full source code. Use with `pack_snippets()` for implementation details.
- **`pycodekg explain` CLI command** (`src/pycode_kg/cli/cmd_explain.py`) — New subcommand to explain code nodes from the command line. Accepts a node ID (e.g., `fn:src/pycode_kg/store.py:GraphStore.expand`) and outputs markdown-formatted explanation to stdout or file.
- **`GraphStore.edges_from()` method** (`store.py`) — New method to query edges originating from a node with a specific relation type. Supports `limit` parameter for capping results. Powers the `explain` tool's "Calls (Callees)" section.
- **`PyCodeKGAnalyzer.to_markdown()` method** (`pycodekg_thorough_analysis.py`) — New method to render architectural analysis results as a Markdown context document (similar to `SnippetPack.to_markdown()`). Returns sections for baseline metrics, complexity hotspots, high fan-out functions, module architecture, critical paths, public APIs, docstring coverage, issues, and strengths — optimized for LLM ingestion.
- **VS Code integration** (`.vscode/`) — Added `tasks.json` with PyCodeKG workflow tasks (Rebuild, Build SQLite, Build LanceDB, Query Interactive, List Snapshots, Save Snapshot, Generate Architecture, Run Thorough Analysis); `settings.json` pointing Python interpreter to `.venv`; `copilot-instructions.md` documenting available tasks and MCP tools for GitHub Copilot. `.vscode/` is now tracked in git (removed from `.gitignore`).

### Changed

- **Python version constraint** — Widened from `>=3.12,<3.13` to `>=3.12,<3.14`, adding support for Python 3.13.
- **`.gitignore`** — Simplified snapshot tracking: replaced `.pycodekg/*` + `!.pycodekg/snapshots/` with a flat `.pycodekg/` exclusion. Snapshots are local-only artifacts — no staging friction, no commit loop. Commit them manually at milestones with `PYCODEKG_SKIP_SNAPSHOT=1 git commit`. Removed `.vscode/` exclusion — project-specific VS Code config is now tracked.
- **Snapshot CI workflow** (`.github/workflows/snapshots.yml`) — Removed the auto-commit-and-push step. Snapshots are uploaded as build artifacts only; the post-commit hook handles local capture.
- **Snapshot documentation** (`docs/SNAPSHOTS.md`, `docs/MCP.md`, `.claude/skills/pycodekg/SKILL.md`) — Updated `.gitignore` guidance and best practices to reflect the local-only snapshot model. Untracked previously-committed snapshot JSON files from git index.
- **`analyze_repo()` MCP tool** (`mcp_server.py`) — Changed return type from JSON to Markdown-formatted string. Output is now optimized for LLM ingestion with clear sections for metrics, hotspots, issues, strengths, and recommendations — matching the format of `pack_snippets()` and `explain()` tools.
- **MCP server instructions** (`mcp_server.py`) — Expanded `FastMCP` `instructions` string from a brief 4-line summary to a full structured reference: per-tool documentation for all 7 tools (`graph_stats`, `query_codebase`, `pack_snippets`, `get_node`, `explain`, `callers`, `analyze_repo`) with parameter notes and usage guidance, plus recommended workflow patterns.
- **Documentation** — Updated README.md and docs/CHEATSHEET.md to document all six MCP tools (`graph_stats`, `query_codebase`, `pack_snippets`, `get_node`, `callers`, `explain`). Added dedicated sections in CHEATSHEET for `callers()` (fan-in lookup) and `explain()` (natural-language explanation). Renumbered sections accordingly.
- **PyCodeKG CLI rules** (`.claude/skills/pycodekg/clinerules.md`) — Added documentation for `explain()` and `analyze_repo()` MCP tools. Simplified build command examples from poetry-run format (`poetry run pycodekg-build-sqlite`) to direct CLI format (`pycodekg build-sqlite`), and added shorthand unified `pycodekg build` command.
- **PyCodeKG installation reference** (`.claude/skills/pycodekg/references/installation.md`) — Updated MCP configuration examples across GitHub Copilot, Claude Desktop, and Cline to use absolute venv path directly (e.g., `/absolute/path/to/venv/bin/pycodekg`) instead of routing through Poetry. Added guidance on retrieving venv path (`poetry env info --path`). Simplified config structure by removing `poetry run` wrapper and environment variables. Corrected Agent Config Matrix: Claude Code uses `.mcp.json` (not `.claude/claude_code_config.json`).
- **Copilot instructions** (`.vscode/copilot-instructions.md`) — Enhanced PyCodeKG MCP tool descriptions with parameter names and use cases. Added documentation for `explain()` and `analyze_repo()` tools. Updated `pack_snippets()` and `callers()` descriptions for clarity.
- **Skill documentation** (`.claude/skills/pycodekg/SKILL.md`) — Extended skill trigger description to include new CLI commands (`viz3d`, `viz-timeline`, `explain`, `snapshot`, `architecture`, `download-model`, `install-hooks`). Added "Additional CLI Commands" reference table.
- **Installation reference** (`.claude/skills/pycodekg/references/installation.md`) — Updated default embedding model from `all-MiniLM-L6-v2` to `microsoft/codebert-base` in both `build-lancedb` and `mcp` parameter tables.
- **Architecture analysis report** — Renamed `pycode_kg_analysis_20260307.md` → `pycode_kg_analysis_20260308.md` and refreshed metrics from latest rebuild (4,704 nodes, 4,666 edges, 97.6% docstring coverage).

### Removed

### Fixed

- **Type errors in `mcp_server.py`** — Fixed mypy union-type errors by adding local variable assignment after None checks to narrow types before method calls.
- **Type errors in `cmd_explain.py`** — Changed truthy checks (`if dst_id:`) to explicit None checks (`if dst_id is not None:`) to satisfy mypy's strict type narrowing requirements.
- **`detect-secrets` false positive on snapshot commit hashes** (`.pre-commit-config.yaml`) — Added `--exclude-files '\.pycodekg/snapshots/.*'` to the `detect-secrets` hook. Commit SHAs in snapshot JSON triggered `HexHighEntropyString` detection; the path exclusion prevents this permanently for all future snapshots.

## [0.5.2] - 2026-03-06

### Added

- **`analysis/` directory** — Analysis reports moved from the repo root into a dedicated `analysis/` subdirectory (`pycode_kg_analysis_20260302.md`, `pycode_kg_analysis_20260305.md`); new reports `pycode_kg_analysis_20260306.md` and `pycode_kg_analysis_20260306b.md` added documenting the v0.5.1 stale-graph investigation and the corrected clean-graph re-analysis.

### Changed

- **`query_codebase` MCP tool** (`mcp_server.py`) — New `paths` parameter (comma-separated module path prefixes) filters returned nodes and edges to the specified subtrees. Enables agents to scope queries to production code only (e.g. `paths="src/pycode_kg"`) without changing the underlying graph traversal.
- **`callers` MCP tool** (`mcp_server.py`) — New `paths` parameter mirrors the `query_codebase` filter, allowing callers to be restricted to specific path prefixes (e.g. `paths="src/"` to exclude test callers). Docstring expanded with `rel="INHERITS"` / `rel="IMPORTS"` usage examples.
- **`query_codebase` docstring** (`mcp_server.py`) — Added hop-heuristic guidance (`hop=0` pure semantic, `hop=1` default, `hop=2` broad coverage) to help agents choose the right expansion depth.
- **`GraphStore.graph_stats()`** (`store.py`) — Now returns a `meaningful_nodes` field (total nodes minus `sym:` infrastructure stubs) alongside `total_nodes`, giving agents an accurate count of real code entities.
- **`_compile_results()`** (`pycodekg_thorough_analysis.py`) — Function metrics are now sorted by risk descending (critical → high → medium → low) so the most dangerous functions appear first in JSON output. Module metrics exclude empty modules (zero fan-in and no outgoing deps) to avoid cluttering output with `__init__.py` stubs.
- **`_analyze_critical_paths()`** (`pycodekg_thorough_analysis.py`) — Dunder methods (`__init__`, `__str__`, etc.) are now excluded from the top-5 high-fan-in seed set; they appear everywhere and produced meaningless "critical path" entries.
- **`mcp_server.py` — MCP invocation docs** — Module docstring and `.mcp.json` example updated from `pycodekg-mcp --repo` to `pycodekg mcp --repo` (unified CLI form) and from bare `pycodekg-mcp` command to `/path/to/.venv/bin/pycodekg` with `["mcp", "--repo", ...]` args.
- **`cmd_model.py`** — Docstring corrected: `pycodekg-build-lancedb` / `pycodekg-query` references updated to `pycodekg build-lancedb` / `pycodekg query` (unified CLI subcommand form).
- **`PyCodeKGVisitor` class docstring** (`visitor.py`) — Added class-level docstring describing scope tracking, edge kinds emitted, and constructor parameters. `_qualname()` docstring expanded with `:param` / `:return:` annotations.
- **`index.py`** — Blank lines added around `_local_model_path()` and the `TYPE_CHECKING` guard for PEP 8 / ruff compliance.
- **`.gitignore`** — Replaced the two specific `.pycodekg/graph.sqlite-shm` / `.pycodekg/graph.sqlite-wal` entries with a blanket `.pycodekg/` exclusion; `commit.txt` entry deduplicated (was listed twice).

### Removed

### Fixed

## [0.5.1] - 2026-03-06

### Added

### Changed

- **Python version constraint** (`pyproject.toml`) — Relaxed from `^3.12,<3.13` to `>=3.12,<3.13` for better compatibility with Poetry resolvers.

### Removed

### Fixed

## [0.5.0] - 2026-03-04

### Added

- **Directory exclusion support** — New `--exclude-dir` CLI flag (repeatable) and `[tool.pycodekg].exclude` config option in `pyproject.toml` to skip directories during indexing. Useful for ignoring `vendor/`, `.venv/`, `node_modules/`, test fixtures, and other non-essential directories.
- **`src/pycode_kg/config.py`** — New module for loading and validating PyCodeKG configuration from `pyproject.toml`, including exclusion patterns and storage paths.
- **Comprehensive exclusion tests** (`tests/test_exclusions.py`) — 318 lines of unit tests covering directory matching, pattern validation, recursive filtering, and edge cases.
- **`pdoc` dev dependency** (`pyproject.toml`) — Added `pdoc >=14.0.0` to the dev group for generating API documentation. Documentation can be generated via `poe docs` task.
- **Generated API documentation** (`docs/pycode_kg.html`, `docs/index.html`, `docs/search.js`) — Initial pdoc-generated HTML documentation for the `pycode_kg` package, indexed and searchable.
- **`PyCodeKGAnalyzer._analyze_docstring_coverage()`** (`pycodekg_thorough_analysis.py`) — New Phase 9 in the analysis pipeline. Queries the SQLite `nodes` table directly to compute docstring coverage by kind (`function`, `method`, `class`, `module`) and overall. Results flow into `_generate_insights()` (issues/strengths thresholded at 50%/80%) and `_write_report()` (new "📝 Docstring Coverage" table section with per-kind breakdown and recommendation). Coverage data is also included in the JSON snapshot output via `_compile_results()`.
- **`[tool.pycodekg]` default exclude config** (`pyproject.toml`) — Added `exclude = ["tests"]` as the project default so every `pycodekg build` and `pycodekg analyze` run excludes the test suite automatically. Test directories skew architectural metrics: pytest entry points appear as orphaned code, test helpers dominate fan-in rankings, and undocumented test functions suppress docstring coverage well below production reality.
- **Docstrings for 5 previously undocumented functions** (`store.py`, `viz3d.py`) — `ProvMeta.__init__`, `KGVisualizer.visualize` nested `subtree`, `MainWindow.__init__` nested `_h2` and `_lbl`, and `MainWindow._stats_text`. Source `src/` function/method coverage is now 100%.
- **`mcp` promoted to base dependency** (`pyproject.toml`) — `mcp >=1.0.0` moved from optional extra to core dependencies; `poetry install --extras mcp` is no longer required.
- **Offline model cache** (`index.py`) — `SentenceTransformerEmbedder` now passes `cache_folder` to `SentenceTransformer`, defaulting to `.pycodekg/models/` relative to the repo root. Keeps embedding models local to the project and supports air-gapped environments.
- **`pycodekg-download-model` CLI command** (`src/pycode_kg/cli/cmd_model.py`) — New command to pre-download the embedding model into the local `.pycodekg/models/` cache before first use. Useful in CI/CD pipelines and offline environments.
- **`poetry.toml`** — Added `[virtualenvs] in-project = true` so Poetry creates the `.venv` directory inside the project root, giving a stable, predictable path for MCP client configuration.

### Changed

- **SQLite indexing** — `build-sqlite` now respects exclusion patterns from `[tool.pycodekg].exclude` in `pyproject.toml` and `--exclude-dir` CLI flags.
- **LanceDB indexing** — `build-lancedb` now respects exclusion patterns when filtering code snippets for semantic indexing.
- **`pycodekg_thorough_analysis.py`** — Updated to respect directory exclusions during analysis.
- **README.md** — Expanded with directory exclusion feature documentation and examples.
- **CLAUDE.md** — Added directory exclusion examples to CLI quick reference.
- **Architecture diagrams migrated to `assets/`** — Moved `pycode_kg_arch_*.png` and `pycode_kg_arch_*.jpg` from `docs/` to `assets/` for better organizational structure and easier asset management.
- **`docs/Architecture-brief.md`**, **`docs/Architecture-plain.md`**, **`docs/Architecture.md`** — Updated image references to reflect `assets/` reorganization; added retrieval quality notes documenting docstring coverage as the primary semantic retrieval quality lever.
- **README.md — exclude use cases** — Added `tests/` as the first and recommended entry in the exclude use-cases list, with an explanation of the three metric distortions it causes.
- **`docs/CHEATSHEET.md`** — Added new section 9 "Excluding Directories from Indexing". Old section 9 renumbered to 10.
- **`scripts/install-skill.sh` — Cline MCP entry uses resolved binary path** — Uses the fully-resolved `$PYCODEKG_BIN` path (from `command -v pycodekg`) instead of the bare string `"pycodekg"`, ensuring Cline can locate the executable regardless of `PATH` at launch time.
- **Python version pinned to `^3.12,<3.13`** (`pyproject.toml`) — Narrows the supported range to Python 3.12 only, matching `ruff`, `mypy`, and `pylint` target configurations.

### Removed

### Fixed

## [0.4.1] - 2026-03-02

### Added

- **`pycodekg-mcp` entry point** — `pyproject.toml` now exposes a dedicated `pycodekg-mcp` script (`pycode_kg.mcp_server:main`) alongside the unified `pycodekg` CLI. MCP clients invoke `pycodekg-mcp --repo /path/to/repo` directly, without going through the `pycodekg mcp` subcommand.
- **`src/pycode_kg/cli/` subpackage** — New Click-based CLI layer with one file per command group: `cmd_build.py` (`build-sqlite`, `build-lancedb`), `cmd_build_full.py` (`build`), `cmd_query.py` (`query`, `pack`), `cmd_viz.py` (`viz`, `viz3d`), `cmd_mcp.py` (`mcp`), `cmd_analyze.py` (`analyze`).
- **`src/pycode_kg/cli/options.py`** — Shared Click option decorators (`sqlite_option`, `lancedb_option`, `model_option`, `repo_option`) for consistent flag names and defaults across all subcommands.
- **`click >=8.1.0`** runtime dependency added to `pyproject.toml`.

### Changed

- **MCP configuration layout revised** — PyCodeKG MCP server config relocated to `.mcp.json` (shared by Claude Code and Kilo Code). `.claude/claude_code_config.json` is now reserved exclusively for Claude Copilot servers (copilot-memory, skills-copilot, task-copilot). This matches how each tool actually discovers per-project MCP servers and eliminates the previous split that required Claude Code users to maintain two files.
- **Simplified `pycodekg-mcp` invocation** — `--db` and `--lancedb` arguments are now optional; they default to `.pycodekg/graph.sqlite` and `.pycodekg/lancedb` relative to `--repo`. Per-project MCP config only requires `"args": ["--repo", "/absolute/path"]`.
- **Unified `pycodekg` entry point** — Eight separate `pycodekg-*` scripts replaced by a single `pycodekg` command with subcommands (`build-sqlite`, `build-lancedb`, `build`, `query`, `pack`, `viz`, `viz3d`, `mcp`, `analyze`). `pyproject.toml` `[tool.poetry.scripts]` consolidated accordingly.
- **`src/pycode_kg/__main__.py`** — Custom argparse dispatcher removed; now delegates directly to the Click CLI group (`from pycode_kg.cli.main import cli`).
- **`build_pycodekg_sqlite.py`, `build_pycodekg_lancedb.py`, `pycodekg_query.py`, `pycodekg_snippet_packer.py`, `pycodekg_viz.py`, `pycodekg_viz3d.py`, `pycodekg_thorough_analysis.py`** — `argparse`/`sys.argv` CLI boilerplate stripped out; modules now expose only their core logic functions. Entry points live exclusively in `cli/`.
- **`docs/MCP.md`** — Section 4 and the Claude Copilot integration section updated to reflect the revised config layout: `.mcp.json` for PyCodeKG, `.claude/claude_code_config.json` for Copilot servers. Config examples updated to use `pycodekg-mcp --repo` form.
- **`scripts/install-skill.sh`** — Updated to write the `pycodekg-mcp` command to `.mcp.json` for both Claude Code and Kilo Code selections. Separate `.claude/claude_code_config.json` generation step removed; that file is now managed by Claude Copilot setup, not this script.
- **`.claude/skills/pycodekg/references/installation.md`** — Updated agent config matrix to reflect new file locations and clarify which tools use which config files. Added full config templates for Claude Code and updated templates for all clients.
- **CLAUDE.md** — CLI examples updated from `poetry run pycodekg-*` to the unified `pycodekg <subcommand>` form.
- **`tests/test_index.py`** — Updated `SentenceTransformerEmbedder` mock assertion to include `local_files_only=True`.

### Removed

- **`pycodekg-build-sqlite`, `pycodekg-build-lancedb`, `pycodekg-query`, `pycodekg-pack`, `pycodekg-viz`, `pycodekg-analyze`, `pycodekg-viz3d`** script entry points removed from `pyproject.toml`.

### Fixed

## [0.4.0] - 2026-03-01

### Added

- **`src/pycode_kg/utils.py`** — New shared primitives module containing `rel_module_path()` and `node_id()`, extracted from `pycodekg.py` to break the `pycodekg ↔ visitor` circular import without relying on a local import inside the hot `extract_repo()` path.
- **Pylint dev dependency** (`pyproject.toml`, `.pre-commit-config.yaml`) — Added `pylint ^4.0.5` and a pre-commit hook targeting `src/` with a focused ruleset: `cyclic-import`, `broad-exception-caught`, `cell-var-from-loop`, `undefined-variable`, and `import-outside-toplevel`.
- **`_enclosing_def()` and `_owner_id()`** (`pycodekg.py`) — Nested closure helpers inside `extract_repo()` promoted to module-level functions, eliminating `cell-var-from-loop` lint violations and improving readability.

### Changed

- **`pycodekg.py`** — `PyCodeKGVisitor` and `Counter` imports moved to module top-level; `node_id` / `rel_module_path` now imported from `utils`; local import of `PyCodeKGVisitor` inside `extract_repo()` removed.
- **`visitor.py`** — `node_id` import source changed from `pycode_kg.pycodekg` to `pycode_kg.utils`, resolving the circular dependency cleanly.
- **`index.py`** — `GraphStore` forward reference replaced with a proper `TYPE_CHECKING` guard, eliminating `type: ignore[name-defined]` workarounds.
- **`app.py`, `pycodekg_thorough_analysis.py`** — Broad `except Exception` clauses replaced with specific exception types (`AttributeError`, `ValueError`, `RuntimeError`, `OSError`, etc.) throughout.
- **`pycodekg_thorough_analysis.py`** — `datetime.timezone.utc` replaced with `datetime.UTC` (Python 3.12 alias); `import argparse` / `import sys` moved to module top-level.
- **`pyproject.toml`** — `ruff` and `mypy` target versions bumped from py310 → py312; pylint `[tool.pylint.messages_control]` section added with selective enable/disable rules.
- **`LICENSE`** — Copyright year updated 2024 → 2026.

### Removed

- **`PyCodeKG_Analysis_Report.md`**, **`pycodekg_report.md`**, **`pycodekg_results.json`** — Stale analysis artifacts removed from the repository root; analysis outputs are now generated on demand and kept out of version control.

## [0.3.3] - 2026-02-28

### Added

- **`announcements/` directory** — HackerNews, Reddit, and GitHub release announcement posts highlighting deterministic knowledge graph approach, hybrid semantic+structural query model, source-grounded snippets with line numbers, symbol resolution for cross-module calls, MCP server integration, and comparison with probabilistic (GraphRAG) and embedding-only (Amplify) approaches.
- **3D Knowledge Graph Visualizer documentation** (`README.md`) — New section documenting PyVista/PyQt5-based 3D visualization with Allium (radial/onion) and LayerCake (hierarchical) layout strategies, interactive features (rotate, zoom, click nodes, filter edges), and export options (HTML, PNG).

### Changed

- **`.gitignore`** — Added `.pycodekg/graph.sqlite-shm`, `.pycodekg/graph.sqlite-wal`, and `.pycodekg/lancedb/` to ignore transient SQLite WAL/SHM files and derived semantic index, preventing them from being committed to version control.

---

## [0.3.2] - 2026-02-25

### Added

- **`docs/Architecture-brief.md`** — Comprehensive condensed architecture document (219 lines) covering design principles, layered architecture (primitives, CodeGraph, GraphStore, SemanticIndex, PyCodeKG), build pipeline, hybrid query model, ranking, deduplication, interfaces (Streamlit, MCP, CLI), data flow, and dependencies. Companion to the longer Architecture.md.
- **`docs/Architecture-plain.md`** — Plain-text version of the architecture (75 lines) formatted for accessibility without markdown. Covers design principles, layered architecture, orchestrator, result types, build pipeline phases, hybrid query model, ranking/deduplication, interfaces, source layout, data flow, and dependencies.
- **`docs/pycode_kg_arch_9x16.png`** and **`docs/pycode_kg_arch_banana.png`** — Architecture workflow diagrams generated via PaperBanana from PyCodeKG's own analysis output (`pycodekg-analyze`), demonstrating the system's ability to ingest its own structured output for visualization.
- **`.github/actions/pycodekg-action/`** — GitHub composite action for automated PyCodeKG analysis. Builds SQLite + LanceDB indexes, runs architectural analysis, caches the `.pycodekg/` directory, uploads artifacts, optionally posts PR comments, and can fail the workflow when issues are detected. Configurable via `python-version`, `repo-path`, `report-path`, `json-path`, `model`, `post-comment`, and `fail-on-issues` inputs.
- **`_get_report_metadata()` method** (`pycodekg_thorough_analysis.py`) — Generates a Markdown metadata block with generation timestamp (UTC), PyCodeKG package version, Git commit SHA (7-char short form), and branch. Falls back gracefully to "unknown" when Git is unavailable or running outside a Git repository. Detects CI environment variables (`GITHUB_SHA`, `GITHUB_REF`) for accurate metadata in GitHub Actions workflows.
- **`trame-vtk` dependency** (`pyproject.toml`) — Added optional visualization dependency for enhanced 3D rendering capabilities.
- **`scripts/rebuild-pycodekg.sh`** — Script to rebuild the SQLite knowledge graph and LanceDB semantic index on demand (invoked manually or via `/pycodekg-rebuild`).
- **`docs/analysis_v0.3.1.md`** — Versioned PyCodeKG architecture analysis (complexity hotspots, call chains, module coupling, orphaned code) stamped with v0.3.1.
- **Step 4c in `/release` workflow** (`.claude/commands/release.md`) — Rebuilds the index, runs `pycodekg-analyze`, writes `docs/analysis_v<version>.md`, and re-stages `.pycodekg/` artifacts as part of every release.
- **Cline MCP settings support** (`scripts/install-skill.sh`) — Installer now writes a repo-keyed entry (`pycodekg-<repo-name>`) to Cline's global `cline_mcp_settings.json` and installs `setup-mcp.md` as a Claude command.

### Changed

- **`README.md`** — Added architecture diagram image and references section. New "End-to-End Workflow" section embeds `pycode_kg_arch_9x16.png` with explanation from PaperBanana. New "References" section documents tools (PaperBanana) and related work (Microsoft GraphRAG, Amplify, LanceDB, Streamlit) with comparisons.
- **`LICENSE` field** (`pyproject.toml`) — Changed from `LicenseRef-PolyForm-Noncommercial-1.0.0` to `Elastic-2.0`, aligning with the project's Elastic License 2.0 adoption.
- **`.gitignore`** — Consolidated `.DS_Store` entries (removed redundant `.DS_Store/**` entry) and removed outdated PyCodeKG artifact placeholder comments.
- **DateTime handling** (`pycodekg_thorough_analysis.py`) — All datetime calls upgraded to use `datetime.datetime.now(datetime.timezone.utc)` for consistent UTC timestamps across local, CI, and cloud environments. Affects `_write_report()`, `main()`, `_default_report_name()`, and JSON snapshot generation.
- **Report generation** (`pycodekg_thorough_analysis.py`) — Markdown report now includes metadata block at the top (timestamp, version, commit ref) prepended to the analysis sections.
- **CLI error handling** (`pycodekg_thorough_analysis.py`) — `cli()` function wrapped in try-except, logging exceptions and exiting with status code 1 on failure. Explicit `sys.exit(0)` added on success.
- **3D visualization enhancements** (`viz3d.py`, `layout3d.py`) — Node sizes doubled for improved visibility (module: 0.6→1.2, class: 0.45→0.9, function: 0.35→0.7, method: 0.25→0.5, symbol: 0.2→0.4). Ground plane and cake stand geometry added to create_kg_visualization(). CONTAINS edge color darkened (#BDC3C7→#555555). Removed unused QTimer import and "Spin" button reference. Code formatting updated to ruff standards.
- **PyVista dependency** (`pyproject.toml`) — Added `jupyter` extras to enable enhanced PyVista features.
- **LayerCakeLayout default parameter** (`layout3d.py`) — Disc radius increased from 18.0 to 28.0 for better node spacing.
- **`PyCodeKG.__init__`** (`kg.py`) — `db_path` and `lancedb_dir` are now optional; both default to `<repo_root>/.pycodekg/graph.sqlite` and `<repo_root>/.pycodekg/lancedb`. Existing callers that pass explicit paths continue to work unchanged.
- **All CLI commands and MCP configs** (`pycodekg-rebuild.md`, `setup-mcp.md`, `install-skill.sh`, `README.md`) — Simplified to `--repo`-only invocation; `--db`, `--sqlite`, and `--lancedb` flags are now optional everywhere.
- **`.gitignore`** — Removed `.pycodekg/` so the pre-built knowledge graph and vector index are committed with the repo, enabling zero-setup MCP after cloning.
- **`README.md`** — Updated all CLI examples to reflect optional flags; added manual Cline setup instructions with repo-keyed server naming; simplified `.mcp.json` examples to use `poetry run`.
- **`cli()` upgraded to `argparse`** (`pycodekg_thorough_analysis.py`) — Replaced the manual `sys.argv` parser with `argparse.ArgumentParser` (using `ArgumentDefaultsHelpFormatter`), adding `--help` support and the new `--db`, `--lancedb`, `--output`, `--json`, and `--quiet` flags.
- **`main()` signature** (`pycodekg_thorough_analysis.py`) — All positional parameters are now keyword-only with sensible defaults; added `json_path` and `quiet`; JSON output variable renamed `output_file` → `json_out`.

### Removed

### Fixed

- **Removed `pycodekg-rebuild` pre-commit hook** (`.pre-commit-config.yaml`) — The hook generated new `.pycodekg/` artifacts on every commit attempt, causing a dirty-working-tree loop. Rebuild is now a manual step via `scripts/rebuild-pycodekg.sh` or `/pycodekg-rebuild`.
- **`.pycodekg/` WAL files cleaned up** — Stale `graph.sqlite-shm` and `graph.sqlite-wal` write-ahead log files removed from the committed index.

### Added

- **`scripts/rebuild-pycodekg.sh`** — Script to rebuild the SQLite knowledge graph and LanceDB semantic index on demand (invoked manually or via `/pycodekg-rebuild`).
- **`docs/analysis_v0.3.1.md`** — Versioned PyCodeKG architecture analysis (complexity hotspots, call chains, module coupling, orphaned code) stamped with v0.3.1.
- **Step 4c in `/release` workflow** (`.claude/commands/release.md`) — Rebuilds the index, runs `pycodekg-analyze`, writes `docs/analysis_v<version>.md`, and re-stages `.pycodekg/` artifacts as part of every release.
- **Cline MCP settings support** (`scripts/install-skill.sh`) — Installer now writes a repo-keyed entry (`pycodekg-<repo-name>`) to Cline's global `cline_mcp_settings.json` and installs `setup-mcp.md` as a Claude command.

### Fixed

- **Removed `pycodekg-rebuild` pre-commit hook** (`.pre-commit-config.yaml`) — The hook generated new `.pycodekg/` artifacts on every commit attempt, causing a dirty-working-tree loop. Rebuild is now a manual step via `scripts/rebuild-pycodekg.sh` or `/pycodekg-rebuild`.
- **`.pycodekg/` WAL files cleaned up** — Stale `graph.sqlite-shm` and `graph.sqlite-wal` write-ahead log files removed from the committed index.

### Changed

- **`PyCodeKG.__init__`** (`kg.py`) — `db_path` and `lancedb_dir` are now optional; both default to `<repo_root>/.pycodekg/graph.sqlite` and `<repo_root>/.pycodekg/lancedb`. Existing callers that pass explicit paths continue to work unchanged.
- **All CLI commands and MCP configs** (`pycodekg-rebuild.md`, `setup-mcp.md`, `install-skill.sh`, `README.md`) — Simplified to `--repo`-only invocation; `--db`, `--sqlite`, and `--lancedb` flags are now optional everywhere.
- **`.gitignore`** — Removed `.pycodekg/` so the pre-built knowledge graph and vector index are committed with the repo, enabling zero-setup MCP after cloning.
- **`README.md`** — Updated all CLI examples to reflect optional flags; added manual Cline setup instructions with repo-keyed server naming; simplified `.mcp.json` examples to use `poetry run`.

### Added

- **`_default_report_name()`** (`pycodekg_thorough_analysis.py`) — Helper that derives a timestamped markdown filename (`<repo>_analysis_<YYYYMMDD>.md`) from the resolved repo root, used as the automatic output name when `--output` is not supplied.
- **`pycodekg-analyze` — zero-argument invocation** (`pycodekg_thorough_analysis.py`) — `repo_root` is now optional (defaults to `"."`); `db_path` and `lancedb_path` default to `.pycodekg/graph.sqlite` and `.pycodekg/lancedb` respectively, matching the standard project layout.
- **`pycodekg-analyze --output`/`-o`** — Writes the markdown analysis report to the specified path (auto-named when omitted).
- **`pycodekg-analyze --json`/`-j`** — Overrides the JSON snapshot output path (default: `~/.claude/pycodekg_analysis_latest.json`).
- **`pycodekg-analyze --quiet`/`-q`** — Suppresses the Rich console summary table, useful in CI or scripted contexts.
- **DB existence pre-flight check** (`pycodekg_thorough_analysis.py`) — `main()` now warns and exits early when the SQLite database file is not found, rather than raising a cryptic import or file error.
- **Startup path summary** (`pycodekg_thorough_analysis.py`) — `main()` prints the resolved repo, DB, LanceDB, and report paths before analysis begins for easier debugging.

### Changed

- **`cli()` upgraded to `argparse`** (`pycodekg_thorough_analysis.py`) — Replaced the manual `sys.argv` parser with `argparse.ArgumentParser` (using `ArgumentDefaultsHelpFormatter`), adding `--help` support and the new `--db`, `--lancedb`, `--output`, `--json`, and `--quiet` flags.
- **`main()` signature** (`pycodekg_thorough_analysis.py`) — All positional parameters are now keyword-only with sensible defaults; added `json_path` and `quiet`; JSON output variable renamed `output_file` → `json_out`.

### Removed

### Fixed

---

## [0.3.1] - 2026-02-24

### Added

- **`pycodekg-analyze` CLI entry point** (`pyproject.toml`) — New Poetry script exposing `pycodekg_thorough_analysis:cli` as the `pycodekg-analyze` command. Runs a comprehensive structural and semantic analysis of a PyCodeKG knowledge graph and saves results to `~/.claude/pycodekg_analysis_latest.json`.
- **`cli()` entry point** (`pycodekg_thorough_analysis.py`) — Zero-argument wrapper around `main()` that parses `sys.argv` for `<repo_root>`, `<db_path>`, and `<lancedb_path>`, enabling the module to be registered as a Poetry script entry point. `__main__` block updated to call `cli()`.
- **`README.md` — CLI Usage section 7** — Documents `pycodekg-analyze` usage, arguments, and output location.

---

## [0.3.0] - 2026-02-23

### Added

- **`GraphStore.resolve_symbols()`** (`store.py`) — Post-build step that adds `RESOLVES_TO` edges from `sym:` stub nodes to their matching first-party definitions (`fn:`, `cls:`, `m:`, `mod:`) by name. Called automatically after `GraphStore.write()` in `PyCodeKG.build_graph()` and `pycodekg-build-sqlite`. Enables fan-in queries across module boundaries by connecting import-alias call sites to their canonical definition nodes. Idempotent.
- **`GraphStore.callers_of(node_id, *, rel="CALLS")`** (`store.py`) — Two-phase reverse lookup (fan-in): returns direct incoming `rel` edges plus callers that reach the target through `sym:` stubs resolved via `RESOLVES_TO`. Returns deduplicated caller node dicts.
- **`PyCodeKG.callers(node_id, *, rel="CALLS")`** (`kg.py`) — Thin orchestrator-level wrapper around `GraphStore.callers_of()`.
- **`callers(node_id, rel)` MCP tool** (`mcp_server.py`) — New fifth tool exposing precise fan-in lookup to agents. Returns JSON with `node_id`, `rel`, `caller_count`, and `callers` list. Cross-module callers (those referencing the target via an import alias) are resolved automatically.
- **`RESOLVES_TO` edge relation** — New graph edge type linking `sym:` stubs to in-repo definitions. Not emitted by the AST extractor; added by `resolve_symbols()` post-build.
- **`article/pycode_kg.tex`** — LaTeX source for the technical paper "PyCodeKG: Deterministic Code Navigation via Knowledge Graphs, Semantic Indexing, and Grounded Context Packing". Covers the four-layer architecture, hybrid query model, fan-in lookup, and a detailed comparison with Microsoft GraphRAG (Structural KG-RAG).
- **`article/pycode_kg_medium.md`** — Medium.com companion article "Your Codebase Has a Shape. Most Tools Can't See It." — an accessible overview of PyCodeKG's design, query model, and MCP integration.
- **`article/logo.png`** — Project logo added to the `article/` directory alongside the paper assets.

### Changed

- **`build_pycodekg_sqlite.py`** — Now calls `store.resolve_symbols()` after `store.write()` and reports the resolved edge count in the output line (`resolved=N`).
- **`docs/Architecture.md`** — Updated to document `RESOLVES_TO`, `resolve_symbols()`, `callers_of()`, `callers()`, the updated build pipeline data flow, and the new MCP tool.
- **`docs/MCP.md`** — Added `callers` tool reference section, updated overview (4 → 5 tools), added fan-in step to the typical workflow, updated summary table.
- **`.claude/skills/pycodekg/SKILL.md`** — Added `callers` to tools table and workflow; added `RESOLVES_TO` to rels reference.
- **`README.md`** — Added `RESOLVES_TO` edge to the edges table; expanded "Caller Lookup" section to "Caller Lookup (Fan-In)" with two-phase lookup explanation and code examples; added symbol resolution as build pipeline step 4; added `callers(node_id)` to the MCP tools table; updated docs file structure listing.

### Removed

- **`docs/pycode_kg.pdf`** — Moved to `article/pycode_kg.pdf` alongside the paper source.

### Fixed

- **`SemanticIndex._open_table()` LanceDB wipe bug** (`index.py`) — When `wipe=True`, the table is now dropped and recreated instead of deleting rows from the existing table. Row deletion preserved the stale schema, causing an Arrow `ListType → FixedSizeListType` cast error on the first `tbl.add()` call after an embedding model change. Dropping the table ensures a clean schema on every wipe.

---

## [0.2.3] - 2026-02-23

### Added

- **`.claude/commands/pycodekg-rebuild.md`** — New `/pycodekg-rebuild` slash command that wipes and rebuilds the PyCodeKG SQLite knowledge graph and LanceDB semantic index for any repository. Guides the agent through path resolution, `--wipe` builds of both layers, verification, and a structured summary report.
- **`docs/CHEATSHEET.md`** — Public-facing PyCodeKG query cheatsheet covering all four MCP tools (`graph_stats`, `query_codebase`, `pack_snippets`, `get_node`) with worked examples, data-flow query patterns, edge type reference table, parameter quick reference, and live codebase stats.
- **`.claude/skills/pycodekg/references/CHEATSHEET.md`** — Skill-level copy of the cheatsheet, co-located with the PyCodeKG skill for agent-side reference.
- **`README.md` — Caller Lookup section** — Documents bidirectional edge traversal in `expand()` for precise reverse call lookup.
- **`README.md` — Development section** — Clone + `poetry install --extras mcp` + `pytest` workflow for contributors.

### Changed

- **`scripts/install-skill.sh`** — New Step 2 installs both Claude Code slash commands (`pycodekg.md`, `pycodekg-rebuild.md`) to `~/.claude/commands/`, copying from the local repo or downloading from GitHub. Subsequent steps renumbered (3→4 through 7→8). Final summary now reports installed commands. Variable renamed `LOCAL_CMD` → `_LOCAL_CMD` to avoid collision with the new loop variable.
- **`README.md`** — `symbol` node description updated to mention the data-flow pass; `ATTR_ACCESS`, `READS`, and `WRITES` edge types added to the edges table; Phase 1 description expanded to cover the three sequential AST passes; embedding model updated to `jinaai/jina-embeddings-v3` in CLI examples; Installation section restructured (pip-first, Poetry simplified); MCP configuration section headings clarified; `visitor.py` added to file structure listing; redundant dev-workflow callouts removed.

### Removed

- **`docs/pycode_kg.pdf`** — Legacy PDF removed; superseded by `docs/CHEATSHEET.md` and `docs/Architecture.md`.

---

## [0.2.2] - 2026-02-23

### Added

- **`docs/pycode_kg.pdf`** — Technical paper added to repository and linked from README.
- **`.claude/commands/release.md`** — New `/release` slash command for the release workflow.
- **`tests/test_index.py` — `test_semanticindex_open_table_existing`** — Regression test that exercises the "table already exists" branch of `_open_table`, ensuring the `list_tables().tables` API check is covered on every run.

### Changed

- **`src/pycode_kg/pycodekg.py`** — `DEFAULT_MODEL` reverted to `all-MiniLM-L6-v2` (384-dim); `jinaai/jina-embeddings-v3` caused GPU memory exhaustion on large repositories.
- **`src/pycode_kg/index.py`** — Removed `trust_remote_code=True` (not needed for MiniLM); embedding dimension fallback reverted to `384`.
- **`src/pycode_kg/app.py`** — `all-MiniLM-L6-v2` restored as the first (default) option in the embedding model selector.
- **`LICENSE`** — Switched from PolyForm Noncommercial 1.0.0 to Elastic License 2.0.
- **`README.md`** — Embedding model updated to `all-MiniLM-L6-v2` in Phase 2 description and CLI example; license badge and footer updated to Elastic 2.0; version badge updated to `0.2.2`; technical paper link added.
- **`docs/CHEATSHEET.md`** + **`.claude/skills/pycodekg/references/CHEATSHEET.md`** — Model in sample `graph_stats` output updated to `all-MiniLM-L6-v2`.
- **`release-notes.md`** — Added v0.2.2 section; jina references scrubbed from v0.2.1.
- **`.gitignore`** — Removed `*.pdf` exclusion so `docs/pycode_kg.pdf` is tracked.
- **`pyproject.toml`** + **`src/pycode_kg/__init__.py`** — Version bumped to `0.2.2`; lancedb dependency tightened to `>=0.29.0`; `einops` and `transformers` removed (were only required by jina v3).

---

## [0.2.1] - 2026-02-23

### Added

- **`src/pycode_kg/pycodekg.py` — `DEFAULT_MODEL` constant** — Sentence-transformer model name centralised in a single constant (`jinaai/jina-embeddings-v3`), overridable via the `PYCODEKG_MODEL` environment variable. Exported from the top-level `pycode_kg` package.
- **`src/pycode_kg/pycodekg.py` — data-flow edge kinds** — Four new edge relation types added to `EDGE_KINDS`: `READS`, `WRITES`, `ATTR_ACCESS`, `DEPENDS_ON`, extending the knowledge graph beyond structural edges.
- **`src/pycode_kg/pycodekg.py` — Pass 3 data-flow extraction** — `extract_repo()` now runs a third AST pass using `PyCodeKGVisitor` to emit data-flow edges (`READS`, `WRITES`, `ATTR_ACCESS`) alongside the existing structural and call-graph passes. New symbol/var nodes and edges are merged non-destructively.
- **`src/pycode_kg/visitor.py` — `visit_AsyncFunctionDef`** — Async functions now receive the same scope-tracking, parameter-seeding, and data-flow extraction treatment as synchronous functions.
- **`src/pycode_kg/visitor.py` — `_seed_params`** — All function/method parameters (positional, keyword-only, `*args`, `**kwargs`) are seeded into the local variable scope at function entry, preventing spurious `READS` edges for parameter names.
- **`tests/test_visitor.py`** — New test suite (158 lines) for `PyCodeKGVisitor`, covering scope management, assignment tracking, `READS`/`WRITES`/`ATTR_ACCESS` edge emission, and async function handling.
- **`pyproject.toml`** — Added `einops ^0.8.2` and `transformers >=4.44,<5.0` as runtime dependencies (required by `jinaai/jina-embeddings-v3`).

### Changed

- **Default embedding model** — Switched from `all-MiniLM-L6-v2` (384-dim) to `jinaai/jina-embeddings-v3` (1024-dim) across `index.py`, `kg.py`, `mcp_server.py`, and `app.py`. Fallback embedding dimension updated from 384 → 1024.
- **`src/pycode_kg/index.py` — `SentenceTransformerEmbedder`** — `trust_remote_code=True` passed to `SentenceTransformer` constructor to support models that ship custom pooling code (e.g. Jina v3).
- **`src/pycode_kg/visitor.py` — `_get_node_id`** — Now uses the project's canonical `kind:module:qualname` node-ID convention via `node_id()` from `pycodekg.py`, replacing a placeholder string identity.
- **`src/pycode_kg/visitor.py` — `_qualname`** — Simplified to use `current_scope[-1]` as the parent prefix, fixing spurious double-scoping.
- **`src/pycode_kg/pycodekg.py` — `SKIP_DIRS`** — Added `.pycodekg` to the set of directories excluded from AST traversal.
- **`src/pycode_kg/app.py`** — `jinaai/jina-embeddings-v3` added as the first (default) option in the embedding model selector.
- **`README.md`** — Version badge updated to `0.2.1`; Streamlit visualizer port corrected from `8501` to `8500`; Docker section and docker-related project structure entries removed.
- **`docs/Architecture.md`** — Docker Image section removed; Streamlit visualizer port corrected from `8501` to `8500`; Docker files removed from source layout listing.
- **`docs/deployment.md`** — Fly.io `internal_port` corrected from `8501` to `8500`.
- **`pyproject.toml`** + **`src/pycode_kg/__init__.py`** — Version bumped to `0.2.1`.
- **`tests/test_index.py`** — Updated assertion for `SentenceTransformerEmbedder` initialisation to expect `trust_remote_code=True`.

### Removed

- **`docker/Dockerfile`** + **`docker/docker-compose.yml`** + **`.dockerignore`** — Docker deployment infrastructure removed entirely.
- **`docs/docker.md`** — Docker setup reference removed.
- **`docs/pycode_kg.md`** + **`docs/pycode_kg.tex`** + **`docs/pycode_kg_medium.md`** — Legacy design documents and LaTeX source removed; architecture is covered by `docs/Architecture.md`.

---

## [0.2.0] - 2026-02-21

### Added

- **`src/pycode_kg/__main__.py`** — Subcommand dispatcher enabling `python -m pycode_kg <subcommand>` invocation without an activated venv. Maps `build-sqlite`, `build-lancedb`, `query`, `pack`, `viz`, and `mcp` to their respective `main()` entry points; rewrites `sys.argv` so each module's argparse sees the correct `prog` name in `--help` output.
- **`src/pycode_kg/mcp_server.py`** — MCP server exposing `graph_stats`, `query_codebase`, `pack_snippets`, and `get_node` tools for AI agent integration via the Model Context Protocol. `query_codebase` now accepts a `max_nodes` parameter (default 25) that caps the number of nodes returned, preventing unbounded result sets from flooding agent context windows.
- **`src/pycode_kg/graph.py`** — `CodeGraph`: OOP wrapper around `extract_repo()` providing a cached, chainable interface to pure AST extraction with no side effects.
- **`src/pycode_kg/store.py`** — `GraphStore`: SQLite persistence layer replacing the removed `pycodekg_sqlite.py`; exposes `write()`, `query_neighbors()`, and provenance-aware graph traversal via `ProvMeta`.
- **`src/pycode_kg/index.py`** — `SemanticIndex` + pluggable `Embedder` abstraction replacing `pycodekg_lancedb.py`; includes `SentenceTransformerEmbedder` and `SeedHit` result type for typed semantic search results.
- **`src/pycode_kg/kg.py`** — `PyCodeKG` top-level orchestrator owning the full pipeline (repo → `CodeGraph` → `GraphStore` → `SemanticIndex` → results); defines structured result types `BuildStats`, `QueryResult`, `Snippet`, and `SnippetPack`.
- **`tests/test_index.py`** — Comprehensive test suite (348 lines) covering `Embedder` ABC, `SentenceTransformerEmbedder` (fully mocked), `_build_index_text`, `_escape`, `_extract_distance`, and `SemanticIndex` build/search/cache integration tests using a lightweight `FakeEmbedder`.
- **`tests/test_graph.py`**, **`tests/test_kg.py`**, **`tests/test_store.py`** — Full unit test suites for the three new layered classes.
- **`.github/workflows/ci.yml`** — CI pipeline: ruff format/lint, mypy type-check, and pytest on every push and PR to `main`.
- **`.github/workflows/publish.yml`** — Release workflow: triggered on `v*` tags; runs tests, builds wheel + sdist via `poetry build`, and creates a GitHub Release with both artifacts attached. Distribution via GitHub Releases (not PyPI).
- **`.pre-commit-config.yaml`** — Pre-commit hooks: trailing-whitespace, end-of-file-fixer, YAML/TOML validation, merge-conflict detection, large-file guard, debug-statement detection, ruff lint+format, local mypy and pytest hooks.
- **`.mcp.json`** — Project-level MCP server configuration for Claude Code, wiring `copilot-memory`, `skills-copilot`, `task-copilot`, and `pycodekg` servers.
- **`CLAUDE.md`** — Project instructions for Claude Code with "Agent Identity" section, agent roster, session management, and project-specific rules.
- **`.claude/agents/`** — Thirteen specialized Claude agent configurations: `cco`, `cw`, `do`, `doc`, `kc`, `me`, `qa`, `sd`, `sec`, `ta`, `uid`, `uids`, `uxd`.
- **`.claude/commands/`** — Custom Claude command definitions: `changelog-commit`, `continue`, `protocol`, `setup-mcp`.
- **`docs/Architecture.md`** — Comprehensive architecture document covering design principles, data model, build pipeline, hybrid query model, ranking, snippet packing, call-site extraction, MCP layer, and deployment topology.
- **`docs/MCP.md`** — MCP server reference documentation covering tool signatures, usage examples, and client configuration.
- **`docs/deployment.md`** — Deployment guide covering local, Docker, and Claude Desktop/Code integration.
- **`docs/docker.md`** — Docker setup and usage guide.
- **`docs/logo.png`** — Project logo added to repository and displayed in README.
- **`docker/Dockerfile`** + **`docker/docker-compose.yml`** — Containerized deployment for the Streamlit visualizer app.
- **`.vscode/extensions.json`** — Recommended VSCode extensions for the project.

### Changed

- **`src/pycode_kg/kg.py`**, **`src/pycode_kg/mcp_server.py`** — `pack_snippets` defaults tightened: `max_lines` reduced from 160 → 60 and `max_nodes` from 50 → 15, keeping snippet packs concise and token-efficient by default.
- **`app.py` → `src/pycode_kg/app.py`** — Moved Streamlit visualizer into the package so it is bundled in the wheel and accessible after `pip install`. Major enhancements: interactive pyvis graph with gold-bordered seed nodes, rich tooltips, floating detail panel, tabbed UI (Graph / Query / Snippets). Default port changed from 8501 to 8500.
- **`scripts/install-skill.sh`** — Full rewrite into an AI integration layer installer. Replaced `PYCODEKG_BIN`/`_POETRY_RUN` with `PYTHON_BIN` detection (`.venv/bin/python` → `python3` on PATH → `pip install`). Build commands use `"${PYTHON_BIN}" -m pycode_kg`. MCP configs written with absolute python path and `-m pycode_kg mcp` args. Added `--providers` flag (`claude`, `kilo`, `copilot`, `cline`, `all`), `--dry-run`, and `--wipe` flags. `LANCEDB_DIR` unconditionally set to `.pycodekg/lancedb`; removed legacy path detection.
- **`.pycodekg/` unified artifact directory** — All generated files (SQLite graph and LanceDB vector index) now live under `.pycodekg/` (`graph.sqlite`, `lancedb/`). Updated across all CLI tools, the MCP server, `.mcp.json`, skills docs, command definitions, `.gitignore`, and all documentation.
- **CLI defaults (zero-config)** — `--repo`, `--db`, `--lancedb`, and `--repo-root` args on all CLI entry points are no longer required; they default to `.` / `.pycodekg/graph.sqlite` / `.pycodekg/lancedb`.
- **`__init__.py`** — Public API overhauled to expose `CodeGraph`, `GraphStore`, `SemanticIndex`, `PyCodeKG`, and all result types as top-level imports; low-level `Node`/`Edge` primitives retained under the locked v0 contract.
- **`tests/test_kg.py`** — Extended with 341 lines of new tests: `_compute_span`, `_read_lines`, `Snippet.to_dict()`, `QueryResult.print_summary()`, `SnippetPack.to_markdown()`, and `PyCodeKG` lazy-property and pipeline-method tests with mocked `SemanticIndex`.
- **`pyproject.toml`** — Development status upgraded from `3 - Alpha` to `4 - Beta`; added MCP and Docker-related dependencies.
- **`README.md`** — Completely rewritten with full project overview, MCP server documentation, Docker deployment, Claude Code integration guide, and `python -m pycode_kg` as the primary CLI invocation.
- **`docs/Architecture.md`**, **`docs/MCP.md`**, **`docs/deployment.md`** — All CLI examples and artifact references updated to `.pycodekg/` paths; MCP layer architecture and deployment topology expanded.
- **`.github/workflows/ci.yml`** — Simplified test matrix to Python 3.12 only; coverage upload unconditional.
- **`.vscode/mcp.json`** — Updated PyCodeKG MCP server args to use `.pycodekg/graph.sqlite` and `.pycodekg/lancedb`.
- **`tests/test_pycodekg_v0.py`** — Renamed to `tests/test_primitives.py` to reflect its scope.
- **`__version__`** — Bumped to `0.2.0`.

### Removed

- **`pycodekg_sqlite.py`** — Replaced by `src/pycode_kg/store.py` (`GraphStore`).
- **`pycodekg_lancedb.py`** — Replaced by `src/pycode_kg/index.py` (`SemanticIndex`).
- **`.streamlit/config.toml`** — Streamlit server configuration no longer bundled; app is part of the installed package.
- **`pyproject.old.toml`** — Stale backup removed.
- **`docs/pycode_kg.synctex.gz`** — Generated LaTeX artifact removed from version control.

### Fixed

- **`src/pycode_kg/index.py`** — Fixed LanceDB table-existence check: replaced deprecated `db.table_names()` with `db.list_tables().tables`; added fallback (`or 384`) for `get_sentence_embedding_dimension()` which can return `None`.
- **`src/pycode_kg/app.py`** — vis-network 9.x+ renders string `title` values as plain text; added `fixHtmlTitles()` to replace HTML string titles with DOM elements so rich tooltips render correctly.
- **`src/pycode_kg/pycodekg.py`** — Tightened `enclosing_def`/`owner_id` type annotations; simplified `dst_id` assignment.
- **`src/pycode_kg/kg.py`** — Replaced `file_cache.get()` + re-assign pattern with `if mp not in file_cache` for correct cache population.

---

## [0.1.0] - 2026-02-21

Initial release. See [release notes](release-notes.md) for full details.
