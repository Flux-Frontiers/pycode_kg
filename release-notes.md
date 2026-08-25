# Release Notes — v0.24.0

> Released: 2026-08-25

The `pycodekg analyze` report gets a fidelity pass — several of its headline
numbers were quietly wrong — alongside a consolidation of the 3-D viewer onto
shared SDK code, a more reliable CI/hooks setup, and two installer fixes.

## What changed

**Analysis report fidelity.** Fan-in no longer double-counts a property
reading its own backing attribute, and the "Key Call Chains" section is
suppressed unless a chain actually clears a depth or count threshold, so a
single depth-3 artifact stops reading as a testing recommendation. Orphan
detection now recognizes names declared via `__all__` or re-exported by a
package `__init__.py` as intentional public surface rather than dead code,
and a method overriding a class this graph can't see gets its own
"unverifiable" report section instead of being called dead or silently
excused. The underlying symbol graph is more honest too: two new prunes
remove bogus `RESOLVES_TO` edges that last-segment name matching was
fabricating — one for stdlib/third-party attribute calls like
`subprocess.run(...)` resolving onto an unrelated first-party function named
`run`, the other for `self.`/`cls.` attribute-of-attribute stubs with no
receiver-type information. Public API Surface, Structural Importance, and
CodeRank seeding now exclude non-package directories (a script under
`scripts/` isn't an API-surface candidate), Snapshot History shows
documented/total counts beside the coverage percentage so growth-driven
drops read differently from regressions, and the report header now warns
when the working tree is dirty relative to what was last indexed.

**The 3-D viewer's "Cast to LG" pipeline now goes through
`kg_utils.viz3d.qt.cast_scene_to_looking_glass`** instead of a hand-copied
duplicate of gutenberg_kg's pipeline — same tile-rounding arithmetic,
different variable names. What's left here is what this repo actually owns:
which nodes get drawn, where the file lands, which button greys out while it
renders. `scene3d.py`'s `leaf_facing`/`oriented_cluster` helpers move to the
same SDK module they were promoted from. Getting here meant raising the
`kgmodule-utils` floor to `>=0.18.0` and `quiltwright` to `>=0.8.0`, both
well past what 0.23.1 declared.

**CI and the pre-commit hooks are more trustworthy.** The Test job now
installs the `viz`/`viz3d` extras and runs the full suite with nothing
deselected — 465 tests instead of the 424 a bare install silently skipped
to, including 14 real-embedder/pipeline tests a stale "too slow for CI"
marker had been hiding since before they took four seconds. The `ty` and
`pytest` pre-commit hooks call `.venv/bin/<tool>` directly instead of
`poetry run`, so an inherited `VIRTUAL_ENV` from an unrelated repo can no
longer silently redirect them. The installed git hook itself had a naming
bug — `PYCODEKG_SKIP_SNAPSHOT` was skipping the quality checks along with
the snapshot, not just the snapshot — and the per-commit snapshot it
controls is now opt-in rather than on by default, since it was recording a
tree hash that a following `git add` immediately invalidated. Snapshots also
now run only on the default branch, so feature-branch commits stay free of
generated files.

**Two installer fixes.** `scripts/install-skill.sh` was overwriting the
user's *global* `~/.claude/commands/` with its own copies of two fleet-wide
commands (`changelog-commit.md`, `release.md`) on every run, silently
replacing whatever another repo's install — or the user's own edits — had
put there; it now installs only its own commands. Separately, re-running the
installer without `--wipe` was a complete no-op whenever the graph already
existed, so new or changed source never reached the index unless you
remembered to pass `--wipe` — it now runs `pycodekg update` on a repeat
install and `pycodekg build` on a fresh one or an explicit `--wipe`.

**Snapshot privacy.** Historical snapshots that predated the path-relativization
fix in `kgmodule-utils` 0.13.2 had their `db_path` values scrubbed from
absolute paths (which published each developer's home directory and
username) to repo-relative ones.

## Upgrading

Nothing beyond the usual `pip install --upgrade pycode-kg`. Rebuild your
local graph if you want the report-fidelity fixes reflected immediately
(`pycodekg build --repo .`); the graph and vector index formats are
unchanged, so this isn't required. If you've installed the PyCodeKG skill
into other repos via `install-skill.sh`, re-running it now only touches its
own two commands — nothing else in `~/.claude/commands/` is at risk.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
