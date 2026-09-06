# Release Notes — v0.25.0

> Released: 2026-09-05

Snapshots now key on the release they measure rather than the git tree they
happened to be taken against, fixing a fleet-wide problem where most
snapshot keys silently pointed nowhere.

## What changed

**Snapshot keys no longer resolve to nothing.** `pycodekg snapshot save`
used to key each snapshot on the working tree's git hash, but that hash was
read before `git add` staged the snapshot file itself — so the key named a
tree that was never actually committed. Across the fleet, only 63 of 605
snapshot keys resolved. `kgmodule-utils` 0.19.0 fixed the underlying scheme,
but this repo couldn't inherit the fix on its own: `Snapshot` overrode
`to_dict()` with a hardcoded tree-hash key, so it kept writing the broken
value regardless of what the SDK did underneath it. That override is now
gone — it existed only because the base class couldn't serialize this
class's typed `metrics`/`vs_previous`/`vs_baseline` properties, and 0.19.0's
base reads those directly.

**`pycodekg snapshot save VERSION` now keys on VERSION.** Pass the version
explicitly at release time — an omitted VERSION falls back to the installed
pycode-kg package version, which names the tool doing the measuring rather
than the repo being measured, so it still gets recorded but is no longer
used as the key. Leaving VERSION off entirely keys on a UTC timestamp
instead, which is the right default for a corpus snapshot rather than a
release snapshot.

**New `--subject` records what was measured.** `snapshot save --subject
repo:pycode-kg` (or `SnapshotManager.capture(subject=...)`) separates "what
this snapshot is of" from "what tool took it," so a corpus snapshot and the
tool version that produced it no longer share one field.

## Upgrading

`pip install --upgrade pycode-kg` pulls the raised `kgmodule-utils>=0.19.0`
floor with it. Existing snapshot files are unaffected — this only changes
how new snapshots are keyed going forward. If you script around
`pycodekg snapshot save`, pass the release version explicitly rather than
relying on the old auto-detected default.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
