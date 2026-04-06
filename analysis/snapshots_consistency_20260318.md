# snapshots.py Consistency Audit — 2026-03-18

## Repos reviewed

| Repo | File |
|---|---|
| code_kg | `src/code_kg/snapshots.py` |
| doc_kg | `src/doc_kg/snapshots.py` |
| FTreeKG | `src/snapshots.py` |
| diary_kg | `src/diary_kg/snapshots.py` |
| kgrag | ❌ no snapshots.py (uses installed copies) |

---

## Consistent across all four ✅

- Git tree hash as stable key; `{key}.json` per snapshot; `manifest.json` index
- `key` property → `tree_hash`
- `to_dict` / `from_dict` round-trip
- `SnapshotManifest` shape: `format`, `last_update`, `snapshots`
- `get_previous` / `get_baseline` (sort by timestamp, find adjacent)
- `list_snapshots` with on-the-fly delta backfill, `branch` filter, `limit`
- `_get_current_tree_hash` / `_get_current_branch` static helpers (identical)
- `save_snapshot` rejects degenerate (0-node/0-chunk) snapshots with `ValueError`
- `_compute_delta` (new − old)

---

## Domain-specific differences (intentional, not bugs)

| Aspect | code_kg | doc_kg | FTreeKG | diary_kg |
|---|---|---|---|---|
| Class prefix | `Snapshot*` | `Snapshot*` | `Snapshot*` | `DiarySnapshot*` |
| Coverage field | `docstring_coverage` + `critical_issues` | `coverage_score` + `issues_count` | `total_files` + `total_dirs` | `chunk_count` + `entry_count` |
| Delta fields | `nodes/edges/coverage_delta/critical_issues_delta` | `nodes/edges/coverage_delta/issues_delta` | `nodes/edges/files_delta/dirs_delta` | `chunks/entries/nodes/edges` |
| DB query | `_collect_module_node_counts()` | — | `_collect_dir_node_counts()` | — |
| `diff_snapshots` extras | `issues_delta`, `module_node_counts_delta` | minimal | `dir_node_counts_delta` | `topic_counts_delta` |

---

## Changes made

### code_kg — `src/code_kg/snapshots.py`
- **Removed** legacy delta backfill from `load_snapshot` (no longer needed; deltas are always persisted at save time)
- **Added** `"latest"` shorthand to `load_snapshot` — resolves to the most recent snapshot by timestamp

### doc_kg — `src/doc_kg/snapshots.py`
- **Removed** legacy delta backfill from `load_snapshot`
- **Added** `"latest"` shorthand to `load_snapshot`

### diary_kg — `src/diary_kg/snapshots.py`
- **Added** `"latest"` shorthand to `load_snapshot`
- **Added** delta backfill logic to `load_snapshot` (matching FTreeKG pattern) — reconstructs `vs_previous` and `vs_baseline` from manifest entries for snapshots that predate persisted deltas

### FTreeKG — `src/snapshots.py`
- No changes; already had both `"latest"` and delta backfill

---

## Test results

```
tests/test_snapshots.py  48 passed in 0.10s
```
