# Release Notes -- v0.29.1

> Released: 2026-11-01

Local variables no longer resolve to definitions that share their name. On
this repo the fix removes 576 false `RESOLVES_TO` edges, every one from a
local variable, and no call edge is lost. On large repos the false edges
dominated the graph: 84% of them on ansible, where a 7,920-file checkout
grew an 18 GB graph and did not finish building.

## What changed

**Local variables are flagged.** The data-flow visitor makes a node for every
local variable and `obj.attr` target. Those nodes now carry
`scope_local: true` in their metadata, and symbol resolution skips them.
Before, a local named `kg` linked to the module `kg.py` and a local named
`callers` linked to the `callers` tool, purely on the name.

**kgmodule-utils 0.29.1.** It is the release that reads the flag, and it
also leaves an ambiguous name unresolved instead of guessing. Against 0.29.0
the flag is written and ignored.

## Upgrading

Install the release and rebuild the graph with `pycodekg build`; an existing
graph keeps its false edges until it is rebuilt. Nothing else changes.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
