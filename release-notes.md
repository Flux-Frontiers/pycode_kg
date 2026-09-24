# Release Notes -- v0.28.1

> Released: 2026-09-23

Analysis no longer aborts on a knowledge graph that has no vector index.
`pycodekg analyze`, `snapshot save`, `init` and the MCP `analyze_repo` tool
now finish and write their report or snapshot, naming the parts they could
not compute instead of exiting with a traceback.

## What changed

**Analysis degrades instead of failing.** `pycodekg build-sqlite` builds the
graph without the vector index, by design. Two of the fifteen analysis phases,
fan-out and concern-based ranking, seed on a semantic query, and the missing
index raised an error that escaped the analyzer. Every phase that had already
run was lost, and `snapshot save` wrote nothing. Each phase now runs under a
guard, the same way `tscode-kg`'s analyzer does. A phase that fails is
skipped, the rest run, and the report opens with an *Incomplete Analysis*
section that lists the skipped phases and the command that builds the index.
The dictionary `run_analysis()` returns carries the same list under
`phase_failures`.

**Dependencies relocked.** The lock moves to kgmodule-utils 0.24.0 and
quiltwright 0.15.1. Declared floors are unchanged.

## Upgrading

Nothing to do. A graph built with `pycodekg build` has its vector index and
behaves exactly as before. To fill in the skipped sections of a
graph-only analysis, run `pycodekg build-index` and analyze again.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
