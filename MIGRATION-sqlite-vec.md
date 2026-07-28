# Migration notes: LanceDB → sqlite-vec

**For:** `doc_kg`, `memory_kg`, `Metabo_kg`, `ftree_kg`, `diary_kg`, `agent_kg`, `ia_kg`
**Reference implementation:** `pycode_kg` v0.20.0 (2026-07-15) — completed, in production
**Companion doc:** [`handoff_skills.md`](handoff_skills.md) — how to clean up the docs/config drift a migration leaves behind
**Date:** 2026-07-28

---

## The one thing to understand first

`KGModule.__init__` takes `vector_backend: str = "auto"`, and **`"auto"` already prefers sqlite-vec**:

```python
# kg_utils/vector_backend.py :: resolve_backend_name
if requested != "auto":                                  return requested
if Path(sqlite_path).exists():                           return "sqlite-vec"
if Path(lancedb_dir).exists() and any(...iterdir()):     return "lancedb"   # ← keeps existing corpora working
return "sqlite-vec"
```

So a repo on the default is **not** pinned to LanceDB by code — it stays on LanceDB purely because a populated `lancedb/` directory exists on disk. A fresh clone builds sqlite-vec today.

**Consequence:** the minimum viable migration is *delete the store and rebuild*. Everything else — pinning the backend, renaming CLI flags, dropping the dependency — is about making that state explicit and permanent rather than accidental.

---

## Current fleet state (measured 2026-07-28)

| Repo | `vector_backend` | own `index.py` | `--lancedb` CLI flags | `lancedb` src refs | Effort |
|---|---|---|---|---|---|
| `ia_kg` | default | none | 0 | **0** | ✅ nothing to do |
| `gutenberg_kg` | `"sqlite-vec"` ✅ | none | 0 | — | ✅ done |
| `kgrag` | n/a — registry | none | 0 | 136 (metadata) | ⏸️ **last**, see below |
| `agent_kg` | default | 135 lines | 0 | 18 | 🟢 small |
| `diary_kg` | default | none | 2 | 24 | 🟢 small |
| `ftree_kg` | default | none | 1 | 45 | 🟢 small |
| `Metabo_kg` | default | 251 lines | 4 | 116 | 🟡 medium |
| `memory_kg` | default | **697 lines** | 6 | 78 | 🟠 large |
| `doc_kg` | `"auto"` (explicit) | **1370+ lines** | 6 | 138 | 🔴 largest |

`doc_kg` and `memory_kg` carry **local forks** of the index layer rather than re-exporting from `kg_utils`. `pycode_kg`'s `index.py` is an 11-line re-export shim — that difference is most of the effort gap.

> **`doc_kg` is already half-migrated.** It has *both* backends wired: `LanceDBBackend` at `src/doc_kg/index.py:249`, `SqliteVecBackend` at `:1453`, and an `sqlite-vec` extra in `pyproject.toml:112`. The work there is selection and cleanup, not implementation.

### `kgrag` — not a migration target

`kgrag` is the federation **registry**, not a KG. It declares no `lancedb` dependency and constructs no vector backend; its 136 `lancedb` source references are schema and metadata describing *other* KGs' stores.

It is already designed to span both backends. `src/kg_rag/registry.py:54-55`:

```sql
lancedb_path TEXT,
vectors_path TEXT,
```

with an in-place upgrade at `registry.py:85` (`ALTER TABLE kg_entries ADD COLUMN vectors_path`), and `primitives.py:56` documenting the intent:

> `:param lancedb_path:` … **Deprecated** for builders that have migrated to sqlite-vec — use `vectors_path`. Still written for kinds that ship a LanceDB index (doc/memory/gutenberg corpora built by pre-sqlite-vec builders).

**So do not touch `kgrag` now.** Dropping `lancedb_path` is the *final* step of the fleet migration, valid only once every registered KG reports a `vectors_path`. Until then the column is load-bearing. Re-register KGs after each repo migrates so the registry picks up the new path.

### Rebuild every store — they are disposable artifacts

Vector stores are derived from SQLite and rebuildable; there is no conversion step and nothing to preserve. **Delete and rebuild them all.**

Every repo hosts several KG stores, not just its own — the KGRAG fleet indexes each repo with `.pycodekg/`, `.dockg/`, `.agentkg/` alongside the repo's native store. All of them need rebuilding, not just the native one, because `auto` resolves per-store: a stale `.dockg/lancedb/` keeps *that* store on LanceDB even after the repo's own store has moved.

```bash
# from each repo root — drop every LanceDB store, whoever owns it
find . -maxdepth 2 -type d -name lancedb -not -path './.venv/*' -print -exec rm -rf {} +

# then rebuild each KG that indexes this repo, e.g.
pycodekg build --repo . --wipe
dockg    build --repo . --wipe
# …plus the repo's own builder
```

Capture a few query results *before* deleting — see [Per-repo verification](#per-repo-verification). Parity is the one thing that regresses silently, and you cannot compare against a store you have already removed.

| Repo | Stores still on LanceDB |
|---|---|
| `doc_kg` | `.agentkg` 68M · `.dockg` 6.5M · `.pycodekg` 760K *(has vectors.sqlite too)* |
| `diary_kg` | `.diarykg` **78M** · `.agentkg` 28M · `.filetreekg` 16M · `.dockg` 3.2M · `.pycodekg` 2.2M |
| `Metabo_kg` | `.agentkg` 11M · `.dockg` 7.9M · `.pycodekg` 2.1M |
| `memory_kg` | `.memorykg` 5.8M · `.agentkg` 4.4M · `.dockg` 4.3M · `.pycodekg` 788K |
| `ftree_kg` | `.agentkg` 5.7M · `.dockg` 2.5M · `.filetreekg` 128K |
| `agent_kg` | `.agentkg` 5.7M · `.dockg` 3.1M |
| `gutenberg_kg` | `.dockg` 6.5M · `.pycodekg` 884K |

Note several repos already have `.pycodekg/vectors.sqlite` — those switched automatically once `pycode_kg` 0.20.0 pinned `sqlite-vec`. That's the mechanism working as designed.

---

## What `pycode_kg` actually changed

Use this as the checklist. From `CHANGELOG.md` `[0.20.0]`:

### 1. Pin the backend at the `KGModule` seam

`src/pycode_kg/kg.py:115`:

```python
super().__init__(
    repo_root,
    db_path=db_path,
    model=model,
    vector_backend="sqlite-vec",   # ← was absent (defaulted to "auto")
)
if vectors_path is not None:
    self.vectors_path = Path(vectors_path)
```

### 2. Change the public constructor signature

```python
# before
PyCodeKG(repo_root, db_path, lancedb_dir, model, table)
# after
PyCodeKG(repo_root, db_path=None, vectors_path=None, *, model=DEFAULT_MODEL)
```

`lancedb_dir`, `table`, and `vector_backend` parameters removed.

### 3. Build the backend explicitly where the index is constructed

`src/pycode_kg/cli/cmd_build.py:137`:

```python
embedder = SentenceTransformerEmbedder(model)
backend  = SqliteVecBackend(vectors_path, dim=embedder.dim, meta_columns=META_COLUMNS)
store    = GraphStore(sqlite_path)
idx = SemanticIndex(
    vectors_path.parent,        # NB: directory, not the file
    embedder=embedder,
    index_kinds=kinds_tuple,
    backend=backend,
)
```

Imports: `from kg_utils.semantic import META_COLUMNS`, `from kg_utils.vector_backend import SqliteVecBackend`.

> ⚠️ **`SemanticIndex`'s first positional parameter is still named `lancedb_dir`** and takes a *directory*. It is a pre-0.20.0 leftover in `kg_utils` — not something you rename. Pass `vectors_path.parent`; the file path goes to `SqliteVecBackend`.

### 4. Rename the CLI surface

| Before | After |
|---|---|
| `<cli> build-lancedb` | `<cli> build-index` |
| `<cli>-build-lancedb` script | `<cli>-build-index` script |
| `--lancedb PATH` | `--vectors PATH` |
| `--table`, `--vector-backend` | removed |
| `<PKG>_LANCEDB` env var | `<PKG>_VECTORS` |

Applies to `build` / `update` / `query` / `pack` / `explain` / `analyze` / `mcp`.

### 5. Change the artifact path

`.<pkg>/lancedb/` (directory) → `.<pkg>/vectors.sqlite` (single file). Update `.gitignore` accordingly.

### 6. Dependencies

```toml
# remove
"lancedb>=0.29.0",
# ensure the extra
"kgmodule-utils[semantic,sqlite-vec,...]>=0.8.0",
```

Also drop any `[project.optional-dependencies] sqlite-vec = [...]` extra — it becomes core.

> `pycode_kg` noted that `lancedb` still installs *transitively* via `kgmodule-utils[semantic]` until KG_utils splits its extras. Removing your direct dependency is still correct; it just won't shrink the venv yet.

### 7. Delete the legacy shim module

`pycode_kg` removed `build_pycodekg_lancedb`. **Check what actually still imports** before documenting either way — `pycode_kg`'s docs claimed both legacy stubs existed when only one did:

```bash
poetry run python -c "import importlib; importlib.import_module('your_pkg.build_yourpkg_lancedb')"
```

### 8. Adapt tests

- Index tests run against `SqliteVecBackend`.
- Obsolete LanceDB table-cache tests removed.
- **Keep a parity guard.** `pycode_kg` retains `test_lancedb_and_sqlite_vec_agree_on_topk` behind `pytest.importorskip("lancedb")` — it verified identical top-5 results across 8 real queries on both backends before the switch. Worth doing *before* you commit to the migration, not after.

---

## Recommended order

Ascending difficulty, so the pattern is established on cheap repos first.

### Phase 1 — `agent_kg`, `diary_kg`, `ftree_kg` (small)

No local index fork; 0–2 CLI flags. Roughly:

1. Add `vector_backend="sqlite-vec"` at the `KGModule` super-init.
2. Rename the 1–2 `--lancedb` flags to `--vectors`.
3. Swap artifact path to `vectors.sqlite`; update `.gitignore`.
4. Drop `lancedb` from `pyproject.toml`.
5. Delete `.{yourkg}/lancedb/`; rebuild; verify query results are sane.
6. Sweep docs/skills/config per [`handoff_skills.md`](handoff_skills.md).

`diary_kg` has a 78M `.diarykg/lancedb` store — the largest rebuild in the fleet. Time the rebuild before assuming it's quick.

### Phase 2 — `Metabo_kg` (medium)

Same as Phase 1, plus a 251-line `index.py` to reconcile and 4 CLI flags. `Metabo_kg` is the only repo pinning `lancedb>=0.29.0` explicitly with a version floor — check nothing depends on LanceDB-specific behaviour first.

### Phase 3 — `memory_kg` (large)

697-line local `index.py` fork, 6 CLI flags, `SemanticIndex` constructed in two places (`index.py:193`, `kg.py:439`).

> ⚠️ `memory_kg` depends on `kgmodule-utils` via a **path dependency**, not a version range. Confirm which checkout it resolves to before assuming it has the 0.8.0 backend seam.

The real question here: can the fork be replaced by a re-export shim like `pycode_kg`'s 11-line `index.py`? If the fork exists only to add the LanceDB backend, migration and de-forking are the same task.

### Phase 4 — `doc_kg` (largest, but furthest along)

1370+ line fork, 138 source references, 6 CLI flags — but **both backends are already implemented**. Steps: default `vector_backend` to `"sqlite-vec"` instead of `"auto"`, promote the `sqlite-vec` extra to core, delete the `LanceDBBackend` path, collapse the fork toward `kg_utils` where possible.

`doc_kg` is the one repo where **keeping** LanceDB temporarily is defensible — `pycode_kg`'s own changelog notes "doc_kg retains its LanceDB fallback independently." Decide deliberately whether that fallback is still wanted.

---

## Per-repo verification

Migration is done when all of these hold:

```bash
# 1. Backend is pinned, not inferred
grep -rn 'vector_backend' src/          # expect "sqlite-vec", not "auto"

# 2. Fresh build produces the sqlite-vec artifact
rm -rf .yourkg/lancedb && <cli> build --repo . --wipe
ls -la .yourkg/vectors.sqlite           # must exist and be non-trivial

# 3. Queries still return sensible results
<cli> query "some real query"           # compare against notes taken pre-migration

# 4. No LanceDB surface remains
grep -rn -i lancedb src/ --include='*.py'
<cli> --help; <cli> build-index --help  # no --lancedb, no build-lancedb

# 5. Dependency gone
grep -n lancedb pyproject.toml

# 6. Full suite
poetry run pytest -q && poetry run ruff check . && poetry run ty check
```

**Capture query results before you migrate.** Backend parity is the thing most likely to regress silently, and you cannot compare against a store you already deleted.

---

## Traps

- **`auto` hides the migration.** A repo can look migrated in code and still run LanceDB because a directory exists. Always check the on-disk artifact, not just the source.
- **Multiple stores per repo.** `.pycodekg/`, `.dockg/`, `.agentkg/` all live inside each repo. Rebuilding only the native store leaves the rest on LanceDB.
- **`lancedb_dir` and `LanceDBBackend` remain real identifiers** in `kg_utils`. Do not "fix" them in docs or code — see [`handoff_skills.md`](handoff_skills.md) Step 3.
- **`--dry-run` proves nothing.** Verify by building and querying.
- **Docs/skills/config will not follow your code.** Nothing type-checks Markdown or JSON. `pycode_kg` needed two follow-up PRs (#14, #15) to finish what 0.20.0 started — budget for that, and work [`handoff_skills.md`](handoff_skills.md) as part of the migration rather than after it.
- **Sync global `~/.claude/`** once the repo skills are corrected, or every project keeps reading the stale copy.

---

## Reference

- `pycode_kg` `CHANGELOG.md` `[0.20.0]` — the authoritative change list
- `pycode_kg` `src/pycode_kg/kg.py:115` — the `vector_backend` pin
- `pycode_kg` `src/pycode_kg/cli/cmd_build.py:137` — explicit backend construction
- `pycode_kg` `src/pycode_kg/index.py` — the 11-line re-export shim to aim for
- `kg_utils/vector_backend.py :: resolve_backend_name` — `auto` resolution logic
- `pycode_kg` PRs #14 / #15 — the doc and config cleanup that follows
