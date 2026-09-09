# Release Notes — v0.27.0

> Released: 2026-09-08

This release fixes a snapshot-provenance bug where the CLI could read one
repo's graph and file it under another repo's identity, and finishes the
snapshot cleanup started in 0.26.0 by retiring the last hand-written overrides
in favor of `kgmodule-utils` 0.20.0's extension points.

## What changed

**`snapshot save --repo` could silently mislabel another project's metrics as
this repo's own.** `--repo` decides where a snapshot is written, but
`--sqlite` defaulted to the relative path `.pycodekg/graph.sqlite`, which
click resolves against the current working directory rather than `--repo`.
Running the command from this repo against a `--repo` elsewhere read
pycode_kg's own graph and wrote it into the other project's snapshots
directory, keyed and subject-labelled as if it described that project, with
no error either way. The default now resolves against `--repo`; an explicit
`--sqlite` is still honored verbatim. `query` and `explain` take no `--repo`
and are unaffected.

**`pycode_kg.snapshots` configures the shared snapshot manager instead of
overriding it.** The `__init__`, `capture`, and `diff_snapshots` overrides are
gone, replaced by `kgmodule-utils` 0.20.0's extension points
(`package_name`, `_domain_metrics()`, `dict_metric_deltas`). One side effect:
the docstring-coverage keyword in `capture()`'s output is now
`docstring_coverage` rather than `coverage` — a `capture_aliases` entry keeps
the old name working with a deprecation warning. The `kgmodule-utils` floor
moves to `>=0.20.0`; against 0.19.x the manager reports itself as `kg-utils`
and drops the `module_node_counts` metric entirely, so this is a hard
requirement rather than a preference.

## Upgrading

Run `poetry install --with dev --all-extras --sync` (or your ecosystem's
equivalent) to pick up the `kgmodule-utils` floor. If your code reads
`capture()`'s `coverage` key directly, switch to `docstring_coverage` — the
old key still works but warns.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
