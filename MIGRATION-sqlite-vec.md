# Migration notes: LanceDB → sqlite-vec

**For:** `diary_kg`, `Metabo_kg`, `memory_kg`, `doc_kg` — then `kgrag` last
**Reference implementations:** `pycode_kg` v0.20.0 · `ftree_kg` v0.9.0 (PR #6) · `agent_kg` (PR #9)
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

## Current fleet state (re-measured 2026-07-28, after `ftree_kg` and `agent_kg`)

Counts are `grep -rn -i lancedb src/` — **case-insensitive**, so they include
`LanceDB` in prose and docstrings. (An earlier revision of this table used a
case-sensitive grep and so under-counted by ~30%; and two `index.py` lengths
were misread from grep line-numbers rather than `wc -l`. Both corrected here.)

| Repo | `vector_backend` | `KGModule` subclass | own `index.py` | `--lancedb` refs | `lancedb` src refs | Effort |
|---|---|---|---|---|---|---|
| `ia_kg` | auto | — | none | 0 | **0** | ✅ nothing to do |
| `ftree_kg` | **`"sqlite-vec"`** | ✅ `module.py` | none | 0 | 1 † | ✅ **done — v0.9.0** |
| `agent_kg` | **sqlite-vec** | ✗ bespoke | — | 0 | 2 † | ✅ **done — PR #9** |
| `gutenberg_kg` | **`"sqlite-vec"`** | — | none | 0 | 41 ‡ | ✅ own store done |
| `kgrag` | n/a — registry | — | none | 6 | 136 | ⏸️ **last**, see below |
| `diary_kg` | auto | ✗ mirrors only | none | 2 | 30 | 🟢 small |
| `Metabo_kg` | auto | ✗ | 251 | 4 | 151 | 🟡 medium |
| `memory_kg` | auto | ✗ | **738** | 6 | 114 | 🟠 large |
| `doc_kg` | `"auto"` explicit | ✗ | **1615** | 6 | 213 | 🔴 largest |

† `ftree_kg`'s single remaining hit is a deliberate comment explaining the
squared-L2 → cosine score change. Nothing stale.

‡ **`gutenberg_kg`'s 41 hits are not its own store.** It is sqlite-vec
internally, but it *orchestrates* other KGs — `ingest.py:243` builds
`.dockg/lancedb`, `:294` builds `.diarykg/lancedb`. Those references are
**correct today** and become stale only when `doc_kg` and `diary_kg` migrate.
This creates an ordering dependency: **re-audit `gutenberg_kg` after those two
land.**

`doc_kg` and `memory_kg` carry **local forks** of the index layer rather than
re-exporting from `kg_utils`. `pycode_kg`'s `index.py` is an 11-line re-export
shim — that difference is most of the effort gap.

> **`doc_kg` is already half-migrated.** It has *both* backends wired: `LanceDBBackend` at `src/doc_kg/index.py:249`, `SqliteVecBackend` at `:1453`, and an `sqlite-vec` extra in `pyproject.toml:112`. The work there is selection and cleanup, not implementation.

> **Only `ftree_kg` had a real `KGModule` subclass.** Everything remaining is
> hand-rolled, so expect each to resemble `agent_kg` — porting the index
> read/write paths by hand — rather than `ftree_kg`'s flag flip. Confirm before
> estimating: `grep -rn 'class .*(KGModule)' src/`

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

Its 6 `--lancedb` CLI references are likewise deliberate — `cmd_registry.py:148`
already emits *"`--lancedb` is deprecated"*, so the transition is handled.

> ⚠️ **One genuine bug found while auditing, unrelated to backends.**
> `cmd_health.py:92` probes code KGs with:
> ```python
> "code": "codekg query --sqlite {sqlite} --lancedb {lancedb} -k 1 health",
> ```
> `codekg` is the **retired** predecessor of `pycode_kg` and is not on PATH —
> the repo no longer exists. Every code-KG liveness probe silently fails. It
> needs `pycodekg query --sqlite {sqlite} --vectors {vectors} …`. The `doc` and
> `memory` entries on the following lines will need the same `--lancedb` →
> `--vectors` treatment once those repos migrate. Worth fixing in `kgrag`
> independently of this migration.

### Rebuild every store — they are disposable artifacts

Vector stores are derived from SQLite and rebuildable; there is no conversion step and nothing to preserve. **Delete and rebuild them all.**

Every repo hosts several KG stores, not just its own — the KGRAG fleet indexes each repo with `.pycodekg/`, `.dockg/`, `.agentkg/` alongside the repo's native store. All of them need rebuilding, not just the native one, because `auto` resolves per-store: a stale `.dockg/lancedb/` keeps *that* store on LanceDB even after the repo's own store has moved.

```bash
# from each repo root — drop every LanceDB store, whoever owns it
find . -maxdepth 2 -type d -name lancedb -not -path './.venv/*' -print -exec rm -rf {} +

# then rebuild each KG that indexes this repo, e.g.
pycodekg build --repo .      # full build always wipes — there is no --wipe flag
dockg    build --repo .
# …plus the repo's own builder
```

Capture a few query results *before* deleting — see [Per-repo verification](#per-repo-verification). Parity is the one thing that regresses silently, and you cannot compare against a store you have already removed.

Re-measured 2026-07-28, after `ftree_kg` v0.9.0 and the `agent_kg` conversion
(all 12 `.agentkg` stores re-embedded and their `lancedb/` dirs removed):

| Repo | Stores still on LanceDB | `vectors.sqlite` |
|---|---|---|
| `diary_kg` | `.diarykg` **78M** · `.filetreekg` 16M · `.dockg` 3.2M · `.pycodekg` 2.2M | 1 |
| `pycode_kg` | `.dockg` 11M | 2 |
| `Metabo_kg` | `.dockg` 7.9M · `.pycodekg` 2.1M | 2 |
| `gutenberg_kg` | `.dockg` 6.5M · `.pycodekg` 884K | 0 |
| `memory_kg` | `.memorykg` 5.8M · `.dockg` 4.3M · `.pycodekg` 788K | 1 |
| `agent_kg` | `.dockg` 3.2M · `.pycodekg` 472K | 2 |
| `doc_kg` | — | 2 |
| `ftree_kg` | — | 4 |
| `kgrag` | — | 2 |

Three things this shows:

* **`.agentkg` is fully converted fleet-wide** — 12 stores, ~440M of LanceDB
  reclaimed, zero mismatches. `doc_kg`, `ftree_kg` and `kgrag` now have no
  LanceDB at all.
* **`.dockg` is the largest remaining footprint** and appears in nearly every
  repo, because DocKG indexes them all. Nothing there converts until `doc_kg`
  itself migrates — the same leverage argument that made `agent_kg` worth doing
  early, and a reason to move `doc_kg` up despite it being the biggest job.
* **`diary_kg` still holds the single largest store** (78M). Its `.filetreekg`
  store is stale now that `ftree_kg` has shipped — rebuild with `ftreekg build`
  independently of migrating `diary_kg` itself.

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

## ✅ Learnings from the completed migrations (`ftree_kg` v0.9.0 · `agent_kg` PR #9)

`ftree_kg` went first because it is a real `KGModule` subclass. It took four
non-obvious corrections. **Read this section before starting any repo** — every
item below is something that passed local tests while being wrong.

### 1. Do NOT delete a domain-specific embed pass

The tempting simplification is to drop the repo's custom `_embed_nodes` /
embedding helper and let `KGModule.build_index` do it generically. For
`ftree_kg` that would have been a silent quality regression.

Its `_embed_text` builds *filesystem*-specific canonical text — path components
as tokens, basename split on `_`/`-`/`.`, the extension as its own token, plus
EXIF prose so `"iPhone photos from 2023"` hits a photo whose path says neither.
`KGModule.build_index` embeds `KIND/NAME/QUALNAME/MODULE/DOCSTRING`, which are
source-code concepts.

**Migrate the storage, keep the embedding logic.** Ask: does this repo build its
own canonical text? If yes, that text is the product — only swap where the
vectors are written and read.

### 2. Check what the query path reads back out of the store

`ftree_kg`'s `_semantic_query` maps `"docstring": r.get("text", "")` — the
embedded `text` *is* what query output displays. `SqliteVecBackend`'s default
`meta_columns` does **not** include `text`, so a default-configured migration
silently blanks the visible output while every test still passes.

Fix: pass an explicit column list.

```python
_META_COLUMNS = ("kind", "name", "qualname", "module_path", "text")
backend = SqliteVecBackend(vectors_path, dim=dim, meta_columns=_META_COLUMNS)
```

Grep the query path for every key it reads out of a search result before you
change backends.

### 3. The distance metric almost certainly changes — recalibrate the score

The big one. `ftree_kg` created its LanceDB table with
`db.create_table("kg_nodes", data=records)` — **no metric**, so LanceDB
defaulted to **squared L2**. `SqliteVecBackend` uses `distance_metric=cosine`.
For normalised embeddings squared-L2 = 2·(1 − cos), an exact **2.003×** factor
measured in practice.

| Metric | Score formula |
|---|---|
| LanceDB default (squared L2) | `1.0 - dist / 2.0` |
| sqlite-vec (cosine) | `1.0 - dist` |

Without the change every score returns **1.000** with ranking intact — invisible
to ranking assertions, wrong for every consumer that reads `score`.

Also: the result key is **`_distance`**, not `distance`. The backend
deliberately mirrors LanceDB's naming; don't "fix" it by reading the SQL.

### 4. Your baseline is probably not a valid control

Querying the existing LanceDB store looks like a baseline but usually is not:
that store was built weeks ago, while the query vector comes from *today's*
embedder. Any model or normalisation change contaminates the comparison.

**Rebuild LanceDB with current code first**, capture that, then migrate:

```bash
git stash                      # back to pre-migration code
rm -rf .yourkg/lancedb .yourkg/vectors.sqlite
<cli> build --repo .           # LanceDB, today's embedder
# …capture queries → control.txt
git stash pop                  # migrated code
rm -rf .yourkg/lancedb .yourkg/vectors.sqlite
<cli> build --repo .           # sqlite-vec
# …capture queries → after.txt
diff control.txt after.txt     # must be empty
```

For `ftree_kg` this diff came out empty — identical ranking *and* scores.
Nothing weaker than that is proof.

### 5. Re-lock, or CI fails before it runs a single test

Changing `pyproject.toml` dependencies without `poetry lock` failed all three CI
jobs in 23s:

> `pyproject.toml changed significantly since poetry.lock was last generated.`

The local venv already had every package, so the full suite passed locally and
hid it completely. **Run `poetry lock && poetry check --lock` as part of the
dependency step, not as an afterthought.** (This is the second time in this
workstream that local state masked a lock problem — the other was a torch pin.)

Expect `lancedb` to *remain* in the lock afterwards: it still arrives
transitively via `kgmodule-utils[semantic]`. Dropping the direct dependency is
still correct; it just won't shrink the venv until KG_utils splits its extras.

### 6. `--wipe` is gone from the full build — wiping is the default

Do not carry `--wipe` into rebuild instructions. On the full-pipeline command it
no longer exists:

```console
$ pycodekg build --repo . --wipe
Error: No such option '--wipe'.        # exit 2
```

The current shape across the fleet:

| Command | Wipe behaviour |
|---|---|
| `pycodekg build` | always wipes; **no flag** |
| `pycodekg build-sqlite` / `build-index` | individual steps still take `--wipe` |
| `ftreekg build` | wipes by default; opt out with **`--no-wipe`** |

So a rebuild is just `<cli> build --repo .`. Check `--help` per command rather
than assuming — the full build and its individual steps differ.

### 8. Audit the index for drift *before* trusting it as a control

`agent_kg`'s parity run failed with sqlite-vec returning **better** results —
higher scores, more relevant hits. A result that flatters the change is a
reason to dig, not to ship. The cause:

```
LanceDB rows (control): 474
SQLite nodes          : 620
```

The live index was missing 24% of its nodes. The "control" was an incomplete
index, so the comparison was meaningless in the migration's favour.

**Check this first, in every repo:**

```python
sqlite3.connect(db).execute("SELECT COUNT(*) FROM nodes").fetchone()[0]   # truth
backend.count()  /  lancedb_table.count_rows()                            # index
```

Fleet-wide, **every** `.agentkg` index had drifted — 15% to 100% missing
(`kgrag`: 4018 nodes, none indexed). Expect the same class of problem wherever
embedding is optional or deferred.

### 9. Deferred embedding is a design flaw, not an optimisation

`agent_kg`'s Stop hook passed `--no-embed` "for speed", relying on a
consolidation pass to catch up. That pass turned out to be the actual bug: it
covered four of six node kinds, was scoped to the *current session*, and
re-embedded every node on every run instead of only the missing ones — so it
was simultaneously incomplete and wasteful. One node kind (`intent`) had no
embed call anywhere and could never be found.

Measured cost of embedding inline: **~2.8s** against a 30s hook timeout, on a
path where a sibling hook already paid exactly that. The optimisation bought
three seconds and cost correctness.

If the repo you are migrating defers embedding anywhere, fix it at source
rather than adding a repair command. Then add the repair command anyway, as a
safety net with `--check` for CI:

```
missing_embedding_ids()  → reconcile SQLite (truth) against the index
reindex()                → embed only what is missing; idempotent
```

Exclude nodes with no embeddable text, or you will report drift that no
reindex can ever clear.

### 10. Silent failure hides everything above

`embed_node()` caught `(ImportError, Exception)` and returned. That was *not*
the cause of the drift, but it is why nobody saw it for months. Count failures
and warn once per store instance — enough signal to notice, not enough to spam
a hook that runs on every turn.

### 11. Smaller mechanical notes

- Set `_default_dir = ".<yourkg>"` on the subclass. `ftree_kg` was inheriting
  the base `.kgcache` and compensating by passing `lancedb_dir` explicitly;
  setting `_default_dir` lets the base derive `vectors_path` correctly and
  removes the argument entirely.
- `SemanticIndex`'s first positional is still literally `lancedb_dir` and takes
  a **directory**; the vector *file* goes to `SqliteVecBackend`. Not a rename.
- Bulk `sed` across CLI files will happily produce an undefined variable — it
  renamed a use in `cmd_status.py` whose definition lived on another line,
  yielding a latent `NameError`. Compile and run every touched command.
- Update the KGRAG adapter to read `entry.vectors_path`, tolerating `None` for
  entries registered before the migration.
- This is a **breaking** change: constructor parameter and CLI flag both change.
  Version accordingly.

---

## Recommended order

Ascending difficulty, so the pattern is established on cheap repos first.

> **Ranking by `lancedb` reference count is the wrong metric — architecture is
> the right one.** By reference count `agent_kg` looked smallest and `ftree_kg`
> largest; in reality `ftree_kg` was easiest (a genuine `KGModule` subclass, so
> the backend seam already existed) and `agent_kg` is hardest (a bespoke
> `ConversationIndex` that bypasses `kg_utils` entirely — a rewrite, not a flag
> flip). `diary_kg`'s `DiaryKGAdapter` only *mirrors* the `KGModule` pattern
> without subclassing it, so it is closer to `agent_kg` than to `ftree_kg`.
>
> Check first: `grep -n 'class .*(KGModule)' src/**/*.py`

> **Leverage argument for going `agent_kg`-first instead.** `.agentkg` stores
> are ~130M across the fleet and sit in *every* repo, so nothing else fully
> converts until `agent_kg` ships. It is a bespoke rewrite rather than a flag
> flip, but it unblocks the largest share of on-disk LanceDB. `diary_kg` is the
> gentler warm-up; `agent_kg` is the higher-value target. Pick per appetite.

### Phase 1 — `diary_kg`, `agent_kg` (small by size, hand-rolled by design)

Neither has a `KGModule` subclass, so **there is no seam to flip** — expect to
port the embedding write/read paths by hand, per Learning #1. `agent_kg`'s
`ConversationIndex` is LanceDB-native throughout (`index.py:26` takes
`lancedb_dir`, opens a named `"conversation"` table); `diary_kg`'s
`DiaryKGAdapter` only *mirrors* the `KGModule` lazy `_store`/`_index` pattern.

1. Port the index class to `SqliteVecBackend` — keep any domain-specific
   canonical text exactly as-is (Learning #1), and check what the query path
   reads back out (Learning #2).
2. **Recalibrate the score formula** if the old table was created without an
   explicit metric (Learning #3). Measure; do not assume.
3. Rename `--lancedb` → `--vectors` (2 in `diary_kg`, 0 in `agent_kg`).
4. Swap artifact path to `vectors.sqlite`; update `.gitignore`.
5. Drop `lancedb` from `pyproject.toml`, then **`poetry lock`** (Learning #5).
6. Capture a same-day LanceDB control *before* deleting anything (Learning #4);
   rebuild; `diff` must be empty.
7. Sweep docs/skills/config per [`handoff_skills.md`](handoff_skills.md).
8. Re-register with `kgrag` so the registry picks up `vectors_path`.

`diary_kg` has a 78M `.diarykg/lancedb` store — the largest rebuild in the fleet. Time it before assuming it is quick.

### Phase 2 — `Metabo_kg` (medium)

Same as Phase 1, plus a 251-line `index.py` to reconcile and 4 CLI flags. `Metabo_kg` is the only repo pinning `lancedb>=0.29.0` explicitly with a version floor — check nothing depends on LanceDB-specific behaviour first.

### Phase 3 — `memory_kg` (large)

738-line local `index.py` fork, 6 CLI flags, `SemanticIndex` constructed in two places (`index.py:193`, `kg.py:439`).

> ⚠️ `memory_kg` depends on `kgmodule-utils` via a **path dependency**, not a version range. Confirm which checkout it resolves to before assuming it has the 0.8.0 backend seam.

The real question here: can the fork be replaced by a re-export shim like `pycode_kg`'s 11-line `index.py`? If the fork exists only to add the LanceDB backend, migration and de-forking are the same task.

### Phase 4 — `doc_kg` (largest, but furthest along)

1615-line fork, 213 source references, 6 CLI flags — but **both backends are already implemented**. Steps: default `vector_backend` to `"sqlite-vec"` instead of `"auto"`, promote the `sqlite-vec` extra to core, delete the `LanceDBBackend` path, collapse the fork toward `kg_utils` where possible.

`doc_kg` is the one repo where **keeping** LanceDB temporarily is defensible — `pycode_kg`'s own changelog notes "doc_kg retains its LanceDB fallback independently." Decide deliberately whether that fallback is still wanted.

---

## Per-repo verification

Migration is done when all of these hold:

```bash
# 1. Backend is pinned, not inferred
grep -rn 'vector_backend' src/          # expect "sqlite-vec", not "auto"

# 2. Fresh build produces the sqlite-vec artifact
rm -rf .yourkg/lancedb && <cli> build --repo .
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
