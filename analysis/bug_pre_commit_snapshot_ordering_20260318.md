# Bug Fix: Pre-Commit Snapshot Ordering — 2026-03-18

## Summary

Snapshots were not being captured before commits across all KG repos. The root
cause was a hook ordering bug: quality checks ran *before* the snapshot, so any
failing check (ruff, mypy, pytest, etc.) caused the hook to exit early and the
snapshot was never taken.

---

## Root Cause

Every `_PRE_COMMIT_HOOK` script followed this broken order:

```
1. pre-commit run   ← quality checks (can fail → exit 1)
2. git write-tree   ← tree hash captured too late
3. pycodekg build
4. pycodekg snapshot save   ← NEVER REACHED if step 1 fails
```

The fix reorders the hook so snapshots always happen first:

```
1. git write-tree           ← capture staged tree hash immediately
2. <tool> build --wipe      ← rebuild index from staged content
3. <tool> snapshot save     ← capture snapshot (non-fatal on failure)
4. git add <snapshots-dir>  ← stage snapshot files
5. pre-commit run           ← quality checks run last; can still block commit
```

---

## Changes Made

### `pycode_kg` — `src/pycode_kg/cli/cmd_hooks.py`

- Moved `pre-commit run` to the **end** of `_PRE_COMMIT_HOOK`
- `git write-tree` now runs **first**, before any tool can modify files
- Skip env var: `PYCODEKG_SKIP_SNAPSHOT=1 git commit ...`
- Reinstalled live: `pycodekg install-hooks --repo . --force`

---

### `doc_kg` — `src/doc_kg/cli/cmd_hooks.py`

- Same ordering fix applied
- Renamed skip env var from `PYCODEKG_SKIP_SNAPSHOT` → **`DOCKG_SKIP_SNAPSHOT`**
- Reinstall: `dockg install-hooks --repo . --force`

---

### `FTreeKG` — `src/cli/cmd_hooks.py` *(new file)*

- Created `cmd_hooks.py` with correct snapshot-first ordering
- Binary: `ftreekg`; KG dir: `.filetreekg/snapshots/`
- Skip env var: **`FTREEKG_SKIP_SNAPSHOT`**
- Registered in `src/cli/main.py` as `import src.cli.cmd_hooks`
- Install: `ftreekg install-hooks --repo . --force`

---

### `diary_kg` — `src/diary_kg/cli.py`

- Added `install-hooks` command directly to the monolithic `cli.py`
- Embedded `_PRE_COMMIT_HOOK` with snapshot-first ordering
- No rebuild step (corpus is source-of-truth; snapshot only)
- Skip env var: **`DIARYKG_SKIP_SNAPSHOT`**
- Install: `diarykg install-hooks --repo . --force`

---

### `kgrag` — `src/kg_rag/cli/cmd_hooks.py` *(new file)*

- Created orchestrating hook that snapshots **all** registered KGs in the
  workspace before running quality checks
- Order of operations per KG (each conditional on `.{kg}` dir existing):
  1. PyCodeKG — rebuild + snapshot → stage `.pycodekg/snapshots/`
  2. DocKG  — rebuild + snapshot → stage `.dockg/snapshots/`
  3. FTreeKG — rebuild + snapshot → stage `.filetreekg/snapshots/`
  4. DiaryKG — snapshot only → stage `.diarykg/snapshots/`
  5. `pre-commit run` — quality checks last
- Skip env var: **`KGRAG_SKIP_SNAPSHOT`**
- Registered in `src/kg_rag/cli/main.py` as `import kg_rag.cli.cmd_hooks`
- Install: `kgrag install-hooks --repo . --force`

---

## Skip Env Vars (per-tool)

| Tool      | Skip variable              |
|-----------|---------------------------|
| pycodekg    | `PYCODEKG_SKIP_SNAPSHOT=1`  |
| dockg     | `DOCKG_SKIP_SNAPSHOT=1`   |
| ftreekg   | `FTREEKG_SKIP_SNAPSHOT=1` |
| diarykg   | `DIARYKG_SKIP_SNAPSHOT=1` |
| kgrag     | `KGRAG_SKIP_SNAPSHOT=1`   |

Usage: `DOCKG_SKIP_SNAPSHOT=1 git commit -m "wip: skip snapshot"`

---

## Reinstalling Hooks

After `poetry install` in each repo, run:

```bash
# pycode_kg (already reinstalled)
pycodekg install-hooks --repo . --force

# doc_kg
cd ~/repos/doc_kg && dockg install-hooks --repo . --force

# FTreeKG
cd ~/repos/FTreeKG && ftreekg install-hooks --repo . --force

# diary_kg
cd ~/repos/diary_kg && diarykg install-hooks --repo . --force

# kgrag
cd ~/repos/kgrag && kgrag install-hooks --repo . --force
```
