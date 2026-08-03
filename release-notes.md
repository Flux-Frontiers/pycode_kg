# Release Notes — v0.21.4

> Released: 2026-08-03

A dependency-hygiene release with no behavioural change. PyCodeKG once again requests
`kgmodule-utils[semantic]` rather than re-declaring that extra's contents by hand, which
removes a set of duplicate version pins that had to be kept in step with upstream
manually. Nothing about how the graph is built or queried has changed, and a default
install still carries neither `lancedb` nor `pyvis`.

## What changed

**The `[semantic]` extra is back.** 0.21.3 dropped it for a good reason: it was the last
thing dragging `lancedb` into a clean install, long after the retired backend stopped
being reachable from any code path. Removing it meant re-declaring six of that extra's
members directly, so this project and kgmodule-utils each carried their own copy of the
same constraint — the kind of duplication that stays correct only until someone forgets
to update one side. kgmodule-utils 0.10.0 moves `lancedb` into a dedicated `[lancedb]`
extra, so `[semantic]` can be requested again without it, and the hand-maintained copies
go away.

**Two direct pins removed.** `transformers` is now inherited from `[semantic]`, which
declares the identical `>=5.5.0,<6` range established in 0.21.0 — nothing under `src/`
imports it directly, so the local entry was a second copy that could only drift.
`safetensors` is gone outright: `transformers` already requires `safetensors>=0.8.0`, so
the old `>=0.5.0` floor could never participate in resolution at all.

**`torch` stays declared directly, deliberately.** It looks like the same kind of
duplicate, but it isn't. The `[tool.poetry.dependencies]` block routes Linux `torch` to
the CPU-only wheel index, and that enrichment applies only to a dependency this project
declares itself. Inheriting `torch` from the extra would silently restore the ~3.4 GB
CUDA wheel on Linux installs and CI.

## Upgrading

Nothing to do. There is no migration, no rebuild, and no configuration change — the graph
format, CLI surface and MCP tool API are all untouched, and existing `.pycodekg/` indices
are unaffected.

Developers working from a clone should run `poetry install --all-extras` to pick up the
refreshed lock. One caveat worth knowing: a bare `poetry install --sync` will strip the
`dev`, `viz` and `viz3d` extras from an existing environment, because `--sync` treats any
extra you don't explicitly name as unwanted.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
