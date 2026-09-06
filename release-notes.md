# Release Notes — v0.25.1

> Released: 2026-09-05

v0.25.0's headline fix never actually reached disk. This release fixes that.

## What changed

**Snapshot key, subject, and tool provenance are no longer silently dropped
on save.** `capture()` correctly set `snapshot_key`, `subject`, `tool`, and
`tool_version` on the in-memory snapshot, but `SnapshotManager.save_snapshot`
rebuilds a bare base `Snapshot` object before writing, to normalize this
class's typed `metrics`/`vs_previous`/`vs_baseline` properties back into raw
dicts for the shared base implementation. That rebuild listed every base
field except these four. Every snapshot saved under v0.25.0 therefore fell
back to a tree-hash-derived key with empty subject and tool fields,
regardless of what was passed to `capture()` — the exact VERSION-keying and
`--subject` behavior v0.25.0 introduced never actually landed on disk. The
rebuild now copies all four fields, and a regression test saves a snapshot
and reads both the file and the manifest back to confirm the key and
subject survive.

## Upgrading

`pip install --upgrade pycode-kg`. Any snapshot saved while running v0.25.0
was written with a tree-hash key and no subject/tool metadata; re-save it
under v0.25.1 if you need the correct key and provenance recorded.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
