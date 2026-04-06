# Bug: Relative Path Defaults in CLI `--db` / `--sqlite` / `--lancedb` Options

**Date:** 2026-03-17
**Severity:** High — silently corrupts data, produces 0-node analyses
**Status:** Fixed in `pycode_kg`; pending fix in `doc_kg`, `FTreeKG`
**Affects:** `pycode_kg`, `doc_kg`, `FTreeKG` (systemic across all KG CLI tools)

---

## Summary

All three KG CLI tools define their database path options with **relative path defaults**
(e.g. `default=".pycodekg/graph.sqlite"`). When a command is run against an external repo
(`--repo /some/other/path`), the database is silently written to **CWD**, not to the
target repo. Downstream commands (`analyze`, `mcp`, `query`) then look in the correct
repo-relative location and find nothing — producing 0-node graphs with no error.

---

## Root Cause

Click resolves `default=` values at call time using the **current working directory**,
not relative to any other argument. There is no linkage between `--repo` and `--db`.

```python
# BROKEN — resolves relative to CWD, not --repo
@click.option("--db", default=".pycodekg/graph.sqlite", ...)
def build_sqlite(repo, db, ...):
    store = GraphStore(Path(db))   # Path(".pycodekg/graph.sqlite") → CWD/.pycodekg/
```

If the user runs `pycodekg build-sqlite --repo ~/repos/pandas` from `~/repos/pycode_kg`,
the SQLite is written to `~/repos/pycode_kg/.pycodekg/graph.sqlite` — overwriting pycode_kg's
own graph — while `~/repos/pandas/.pycodekg/graph.sqlite` never gets created.

---

## Affected Files

### `pycode_kg` — **FIXED 2026-03-17**

| File | Option | Old default | Fix |
|------|--------|-------------|-----|
| `src/pycode_kg/cli/cmd_build.py` | `--db` on `build-sqlite` | `".pycodekg/graph.sqlite"` | `None` → resolved to `repo_root / ".pycodekg" / "graph.sqlite"` in body |
| `src/pycode_kg/cli/cmd_build_full.py` | `--db` on `build` | `".pycodekg/graph.sqlite"` | same |
| `src/pycode_kg/cli/cmd_build_full.py` | `--lancedb` on `build` | `".pycodekg/lancedb"` | `None` → resolved to `repo_root / ".pycodekg" / "lancedb"` in body |

Note: `build-lancedb` in `cmd_build.py` was **already correct** — it used
`repo_root / ".pycodekg" / "graph.sqlite"` in the function body, which is the pattern
to replicate everywhere.

### `doc_kg` — **NEEDS FIX**

| File | Option | Bad default |
|------|--------|-------------|
| `src/doc_kg/cli/options.py` | `sqlite_option` | `".dockg/graph.sqlite"` |
| `src/doc_kg/cli/options.py` | `lancedb_option` | `".dockg/lancedb"` |

The shared `sqlite_option` and `lancedb_option` decorators in `options.py` are reused
across `cmd_build`, `cmd_query`, `cmd_viz`, `cmd_mcp`, `cmd_snapshot`, and `cmd_analyze`.
All commands that **write** the database are affected. Read-only commands (query, viz,
mcp, snapshot) are also affected but typically fail loudly rather than silently
overwriting data.

### `FTreeKG` — **NEEDS FIX**

| File | Option | Bad default |
|------|--------|-------------|
| `filetreekg/cli/options.py` | `sqlite_option` | `".filetreekg/graph.sqlite"` |
| `filetreekg/cli/options.py` | `lancedb_option` | `".filetreekg/lancedb"` |

Same pattern as `doc_kg` — shared option decorators with relative defaults.

---

## Correct Pattern

Change the default to `None` and resolve the path in the function body, anchored to
`repo_root` (the resolved `--repo` argument):

```python
# CORRECT
@click.option(
    "--db",
    default=None,
    type=click.Path(),
    show_default=False,
    help="SQLite database path (default: <repo>/.pycodekg/graph.sqlite).",
)
def build_sqlite(repo: str, db: str | None, ...) -> None:
    repo_root = Path(repo).resolve()
    db_path = Path(db) if db else repo_root / ".pycodekg" / "graph.sqlite"
    ...
    store = GraphStore(db_path)
```

This matches the pattern already used correctly in `pycodekg build-lancedb`:

```python
# Already correct in cmd_build.py:build_lancedb
sqlite_path = Path(sqlite) if sqlite else repo_root / ".pycodekg" / "graph.sqlite"
lancedb_dir = Path(lancedb) if lancedb else repo_root / ".pycodekg" / "lancedb"
```

---

## Failure Mode

The bug is **silent** — no error, no warning. The failure chain:

1. `pycodekg build-sqlite --repo /target/repo` writes SQLite to `CWD/.pycodekg/graph.sqlite`
2. `pycodekg build-lancedb --repo /target/repo` reads from `repo_root/.pycodekg/graph.sqlite` ✓
   → file not found or empty → zero vectors indexed
3. `pycodekg analyze /target/repo` reads from `repo_root/.pycodekg/graph.sqlite` ✓
   → finds empty or missing DB → reports 0 nodes
4. Analysis output file is created with 0-node content — no crash, no warning

Secondary effect: if CWD happens to be another KG repo (e.g. running the script from
`~/repos/pycode_kg`), **that repo's own SQLite is silently wiped and replaced** with the
target repo's data (or nothing, if `--wipe` is passed).

---

## Discovery

Discovered 2026-03-17 while debugging `scripts/analyze_repo.sh` producing a 0-node
analysis of `pandas-dev/pandas`. The script correctly passed `--include-dir pandas`,
but the SQLite landed in `~/repos/pycode_kg/.pycodekg/graph.sqlite` instead of
`~/repos/pandas/.pycodekg/graph.sqlite`.

---

## Fix Checklist

- [x] `pycode_kg` — `cmd_build.py:build_sqlite` `--db`
- [x] `pycode_kg` — `cmd_build_full.py:build` `--db`
- [x] `pycode_kg` — `cmd_build_full.py:build` `--lancedb`
- [ ] `doc_kg` — `cli/options.py` `sqlite_option` default
- [ ] `doc_kg` — `cli/options.py` `lancedb_option` default
- [ ] `doc_kg` — audit all commands consuming these options for body-level resolution
- [ ] `FTreeKG` — `cli/options.py` `sqlite_option` default
- [ ] `FTreeKG` — `cli/options.py` `lancedb_option` default
- [ ] `FTreeKG` — audit all commands consuming these options for body-level resolution

---

## Notes

- Any new KGModule-derived tool must **never** use a relative string literal as a Click
  `default=` for path options that are logically relative to `--repo`. Always default to
  `None` and resolve in the function body.
- Consider adding a shared helper `resolve_db_path(repo_root, db_arg, subdir, filename)`
  to enforce this pattern once and eliminate copy-paste risk across all KG tools.
- The `--corpus-root` option in `doc_kg/options.py` also defaults to `"."` — evaluate
  whether this has the same class of problem in write commands.
