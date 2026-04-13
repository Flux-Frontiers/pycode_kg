# Snapshot Prune — Implementation Summary

**Date:** 2026-04-07
**Version:** pycode_kg bumped 0.12.0 → 0.13.0

---

## What Was Done

The `kg_snapshot` base class (`SnapshotManager.prune_snapshots()`) was already fully implemented and returns a `PruneResult` dataclass. It was not wired through to any adapter CLI or re-exported from any adapter's public API.

This session wired it through to all six KG adapters.

---

## What `prune_snapshots()` Does

Removes three categories of junk from a snapshot directory:

1. **Metric-duplicates** — interior snapshots whose metrics are unchanged from the previous kept entry. Baseline (oldest) and latest snapshots are always preserved.
2. **Broken manifest entries** — entries in `manifest.json` whose `.json` file no longer exists on disk.
3. **Orphaned JSON files** — `.json` files in the snapshot directory not referenced by any manifest entry.

Supports `--dry-run` to preview removals without deleting anything.

---

## Files Changed

### pycode_kg (`/Users/egs/repos/pycode_kg`)

| File | Change |
|------|--------|
| `src/pycode_kg/snapshots.py` | Re-export `PruneResult` from `kg_snapshot`; add to `__all__` |
| `src/pycode_kg/cli/cmd_snapshot.py` | Add `pycodekg snapshot prune [--dry-run]` subcommand |
| `src/pycode_kg/__init__.py` | Version bumped `0.12.0` → `0.13.0` |
| `pyproject.toml` | Version bumped `0.12.0` → `0.13.0` |
| `poetry.lock` | Regenerated for new version |
| `CHANGELOG.md` | Added entry under `[Unreleased]` + promoted to `[0.13.0] - 2026-04-07` |
| `.mcp.json` | Created — per-repo MCP config for `pycodekg` + `dockg` servers |
| `.pycodekg/snapshots/` | 57 vestigial snapshots pruned (56 metric-duplicates + 1 orphaned file) |
| `.pycodekg/snapshots/manifest.json` | Updated to reflect pruned state |
| `commit.txt` | Commit message prepared |

---

### code_kg (`/Users/egs/repos/code_kg`)

| File | Change |
|------|--------|
| `src/code_kg/snapshots.py` | Re-export `PruneResult` from `kg_snapshot`; add to `__all__` |
| `src/code_kg/cli/cmd_snapshot.py` | Add `codekg snapshot prune [--dry-run]` subcommand |

---

### doc_kg (`/Users/egs/repos/doc_kg`)

| File | Change |
|------|--------|
| `src/doc_kg/snapshots.py` | Re-export `PruneResult` from `kg_snapshot`; add to `__all__` |
| `src/doc_kg/cli/cmd_snapshot.py` | Add `dockg snapshot prune [--dry-run]` subcommand |

---

### ftreekg (`/Users/egs/repos/ftreekg`)

| File | Change |
|------|--------|
| `src/ftree_kg/snapshots.py` | Re-export `PruneResult` from `kg_snapshot`; add to `__all__` |
| `src/ftree_kg/cli/cmd_snapshot.py` | Add `ftreekg snapshot prune [--dry-run]` subcommand |

---

### Metabo_kg (`/Users/egs/repos/Metabo_kg`)

| File | Change |
|------|--------|
| `src/metabokg/snapshots.py` | Re-export `PruneResult` from `kg_snapshot` |
| `src/metabokg/cli/cmd_snapshot.py` | Add `metabokg snapshot prune [--dry-run]` subcommand |

---

### diary_kg (`/Users/egs/repos/diary_kg`)

| File | Change |
|------|--------|
| `src/diary_kg/snapshots.py` | Re-export `PruneResult` from `kg_snapshot` |
| `src/diary_kg/cli.py` | Add `diarykg snapshot prune [ROOT] [--dry-run]` subcommand (Rich output style); update module docstring |

> **Note:** diary_kg uses a single `cli.py` with Rich console output rather than a split `cmd_snapshot.py`. It also has its own `DiarySnapshotManifest` / `DiarySnapshotManager` implementations. The inherited `prune_snapshots()` works correctly because `DiarySnapshotManager` properly overrides `load_manifest` and `_save_manifest`, so the base-class prune logic operates through polymorphism.

---

## CLI Usage (all adapters)

```bash
# Preview — shows what would be removed without deleting
pycodekg snapshot prune --dry-run
codekg snapshot prune --dry-run
dockg snapshot prune --dry-run
ftreekg snapshot prune --dry-run
metabokg snapshot prune --dry-run
diarykg snapshot prune --dry-run

# Execute — removes duplicates, broken entries, orphaned files
pycodekg snapshot prune
codekg snapshot prune
dockg snapshot prune
ftreekg snapshot prune
metabokg snapshot prune
diarykg snapshot prune
```

---

## No Changes Required In

- `kg_snapshot` — `prune_snapshots()` and `PruneResult` were already fully implemented there.
- Any test files — no new logic introduced, pure delegation to base class.
- Any MCP server tools — snapshot tools (`snapshot_list`, `snapshot_show`, `snapshot_diff`) unchanged.

---

## Commit Ready

```bash
cd /Users/egs/repos/pycode_kg
git commit -F commit.txt
```

The other five repos (code_kg, doc_kg, ftreekg, Metabo_kg, diary_kg) have unstaged changes — commit separately in each repo as needed.
