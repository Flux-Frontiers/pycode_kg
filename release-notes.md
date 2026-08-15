# Release Notes — v0.23.1

> Released: 2026-08-15

A cleanup release for two loose ends left by 0.23.0. The repo-analysis helper
script still called console scripts that release deleted, and the
`kgmodule-utils` floor was low enough to let `pycodekg snapshot save` write a
user's home directory into their own version control.

## What changed

**`scripts/analyze_repo.sh` works again.** 0.23.0 removed the per-subcommand
console scripts in favour of `pycodekg <subcommand>`, but this script was
missed: it invoked `pycodekg-build-sqlite`, `pycodekg-build-index` and
`pycodekg-analyze`, so on any 0.23.0 install it cloned the target repository
and then died at the first build step. It now uses the subcommand form
throughout, and its startup check no longer probes for the removed alias
before falling back.

**The `kgmodule-utils` floor moves to 0.13.1.** That is the release where
`SnapshotManager` stopped writing absolute paths into snapshot JSON. It
matters here because `pycodekg snapshot save` writes those files into the
user's own repository, where they get committed — so against an older
`kgmodule-utils` a routine snapshot leaks a home directory and a username into
version control. Declaring the floor is the only way a consumer finds out
before the commit rather than after.

**Housekeeping.** `poetry.lock` refreshed (`charset-normalizer` 3.5.0 →
3.5.1), the per-file `Last Revision` headers now reflect each file's actual
last commit rather than a stale bulk stamp, and the committed analysis report
is regenerated as `docs/analysis_v0.23.1.md`.

## Upgrading

Nothing to do beyond the upgrade itself. Installing 0.23.1 pulls
`kgmodule-utils>=0.13.1` if you are below it; if you have snapshots already
committed that contain absolute paths, re-saving them with the new floor in
place rewrites them relative. No rebuild is required — the graph and vector
index formats are unchanged. No new flags or commands.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
