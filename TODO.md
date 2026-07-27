# Fleet TODO — sqlite-vec migration & kgmodule-utils 0.6.2 rollout

**Status as of 2026-07-15.** Driver repo: `pycode_kg`. Touches `../KG_utils`,
`../doc_kg`, `../kgrag`, `../kgrag_priv`, and every sister KG repo.

## ✅ Done (working trees — nothing committed unless noted)

### pycode_kg (this repo, `feat/sql-vec`, bumped to **0.20.0**)
- **LanceDB fully retired** — sqlite-vec is the only backend.
  `PyCodeKG(repo_root, db_path, vectors_path)`; `build-lancedb` → `build-index`
  (hard rename, incl. `pycodekg-build-index` console script); `--lancedb` →
  `--vectors` everywhere; `--table`/`--vector-backend` removed; legacy
  `build_pycodekg_lancedb` shim deleted; MCP server takes `--vectors` and warns
  if the store is missing; Streamlit env `PYCODEKG_LANCEDB` → `PYCODEKG_VECTORS`.
- Backend parity verified pre-switch (identical top-5 on 8 real queries) +
  committed regression test. 313 tests green; ruff clean; e2e build/query/pack/
  explain/MCP verified against published kgmodule-utils.
- Deps: `kgmodule-utils[semantic,sqlite-vec]>=0.6.2` core; `doc-kg>=0.18.1`
  (dev + kgdeps, harmonized); docs/scripts/CHANGELOG updated; version 0.20.0
  everywhere (pyproject, `__init__`, README, CITATION.cff, CHANGELOG heading).
- `.pycodekg/lancedb/` deleted locally; live index rebuilt as
  `.pycodekg/vectors.sqlite` (378 vectors).

### KG_utils (published: 0.6.0, 0.6.1, 0.6.2)
- 0.6.0: `vector_backend` seam threaded through fleet `KGModule`.
- 0.6.1: `vectors_path` derives from `lancedb_dir.parent` (fixed the
  build-then-query CLI crash).
- 0.6.2: removed `ty` from runtime deps (dev-tool leak that broke downstream
  resolution).

### doc_kg (`main`, 0.18.1 staged)
- **Fixed `dockg build` embeddings.json leak** — the intermediate cache is now
  deleted after indexing (`--keep-cache/--delete-cache` opt-out, matching
  `build-two-phase`). 390 tests green; e2e verified in doc_kg's own venv.
- Version consistency: deleted stray `src/__init__.py` (unpackaged, frozen at
  0.5.1); CHANGELOG Unreleased promoted to `[0.18.1] - 2026-07-15`.

### kgrag + kgrag_priv (both were broken against pycode-kg 0.20.0)
- `CodeKGAdapter` passed `lancedb_dir=` → TypeError on 0.20.0. Fixed in both
  repos: derives `vectors.sqlite` next to the registry entry's lancedb path.
  kgrag 430 pass; kgrag_priv 363 pass.
- Floors: `pycode-kg>=0.20.0`, `doc-kg>=0.18.1` in both.
- kgrag_priv `ty` pin fixed (`^0.0.41` → `>=0.0.44,<0.0.45`).

### Fleet pins (all 13 repos)
- `kgmodule-utils>=0.6.2` everywhere; 11 lock files regenerated and verified
  resolving 0.6.2 (tscode_kg has no lock). ia_kg's dead `doc-kg>=0.12.3` floor
  bumped to `>=0.18.0`.

## ⏳ Remaining — ordered

1. ~~Publish doc-kg 0.18.1~~ — ✅ **published 2026-07-15**.
2. ~~Publish pycode-kg 0.20.0~~ — ✅ **published 2026-07-15** (tag `v0.20.0`
   pushed; 0.20.0 release snapshot saved; pycodekg SKILL.md scrubbed of
   `build-lancedb`/LanceDB references). Upgrade note for users: run
   `pycodekg build` once (index rebuild, seconds; no converter needed).
3. ~~Re-lock kgrag and kgrag_priv~~ — ✅ both locked at pycode-kg 0.20.0 /
   doc-kg 0.18.1 / kgmodule-utils 0.6.2.
4. ~~gutenberg_kg lock~~ — 🔄 **user re-locking it directly**.
5. **Commits across the sister repos** — 11 repos still carry uncommitted
   pyproject/lock bumps on their branches (gutenberg_kg on `feat/macos-app`,
   rest on `main`); kgrag/kgrag_priv additionally carry the adapter fix.
   KG_utils has the 0.6.x work committed through 0.6.2; pycode_kg is
   committed and released.
6. ~~pycode_kg staging hygiene~~ — ✅ verified: `.dockg/embeddings.json` is
   not in the merged history and is gitignored going forward.
7. **pycode_kg post-release loose ends (uncommitted):** `.secrets.baseline`
   refresh from pre-commit, `analysis/` report touch-up, SKILL.md scrub,
   `TODO.md` itself, and the 0.20.0 snapshot manifest.

## 📌 Follow-ups (not blocking)

- **KG_utils 0.7.0 (later):** split `lancedb` out of the `[semantic]` extra so
  the package stops installing transitively. One-line fix needed in tscode_kg
  when it upgrades. doc_kg keeps its LanceDB fallback independently.
- **kgrag registry schema:** `KGEntry.lancedb_path` still models the old store;
  the adapter derives the sqlite-vec sibling as a stopgap. Rename/extend the
  field in a future kgrag release.
- **doc_kg lancedb retirement:** doc_kg still ships LanceDB as a core dep by
  design (fallback for un-migrated corpora, RunPod handler). Retire in a later
  coordinated pass once corpora are converted.
- **RunPod push** for gutenberg_kg (deferred since the doc_kg migration plan).
