# Release Notes — v0.20.0

> Released: 2026-07-15

PyCodeKG 0.20.0 replaces LanceDB with **sqlite-vec** as the vector store. The semantic index now lives in a single `.pycodekg/vectors.sqlite` file next to the graph database — no more directory-based index, no more table names, and search is an exact scan with recall 1.0. This is a breaking release: rebuild your index once after upgrading and you're done.

## What changed

**Vector store migrated to sqlite-vec.** The whole semantic layer now runs on the `VectorBackend` seam in `kgmodule-utils` 0.6.2 (`[semantic,sqlite-vec]` is a core dependency). Before the switch, backend parity was verified on this repo's own index — identical top-5 results across 8 real queries on both backends — and that guarantee is pinned by a committed regression test. For code-KG-sized corpora the exact scan is fast, and one SQLite file is far easier to ship, back up, and gitignore than a LanceDB directory.

**API and CLI surface renamed to match.** `PyCodeKG` now takes `vectors_path` instead of `lancedb_dir`/`table`. On the CLI, `build-lancedb` is now `build-index`, and every command that took `--lancedb` takes `--vectors`. The MCP server follows suit and now warns at startup when the vector store is missing instead of failing silently on the first query. The Streamlit app reads `PYCODEKG_VECTORS` in place of `PYCODEKG_LANCEDB`.

**Linting consolidated on ruff.** The pylint pre-commit hook — by far the slowest in the chain — is gone. Its checks moved into ruff (`B023`, `BLE001`, `PLC0415`; `F821` already covered undefined names), and the one check ruff can't do, cyclic-import detection, is covered by `pycodekg analyze` itself. Dependency floors were also raised: `kgmodule-utils>=0.6.2`, `doc-kg>=0.18.1`.

## Upgrading

After upgrading the package, rebuild your knowledge graph once:

```bash
pycodekg build --repo .
```

Indexes rebuild in seconds; there is no conversion step. If you script against the CLI or API, rename `build-lancedb` → `build-index`, `--lancedb`/`lancedb_dir` → `--vectors`/`vectors_path`, and drop any `--table` arguments. MCP configs that pass `--lancedb` need the same one-line change. Old `.pycodekg/lancedb/` directories can be deleted.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
