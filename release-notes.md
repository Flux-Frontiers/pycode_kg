# Release Notes — v0.21.1

> Released: 2026-07-29

A hotfix for 0.21.0. That release went out with an unbounded `mcp>=1.0.0`, and `mcp` 2.0 landed on PyPI shortly afterwards — so a clean `pip install pycode-kg` now resolves a combination that `pycodekg-mcp` cannot import. If you installed 0.21.0 from PyPI, upgrade. If you work from a checkout with a lock file you were never affected, which is precisely why this reached the index unnoticed.

## What changed

**`mcp` is pinned below 2.0.** mcp 2.0 removed the bundled `mcp.server.fastmcp` module — FastMCP now ships as the standalone `fastmcp` package — and rebuilt `mcp.server` around a new set of submodules. PyCodeKG's MCP server imports `FastMCP` from `mcp`, so the import fails outright and the console script dies before registering a single tool. The constraint is now `>=1.0.0,<2`; lifting it means porting to the standalone package rather than simply widening a range.

**The gap that let it ship is closed.** The server builds its `FastMCP` instance and registers all nineteen tools with module-level decorators, so an incompatible release breaks at *import* time. Nothing in the suite asserted that import directly, and a developer's pinned lock file masks the problem entirely — the failure is visible only to someone installing fresh from PyPI. A new test module imports the server, checks the entry point resolves, and asserts the tool surface survives registration. One test asserts `mcp.server.fastmcp` exists on its own, so the next incompatibility names itself instead of surfacing as an opaque `ImportError` from our own code.

**The break was reproduced, not inferred.** The pin was chosen after installing mcp 2.0 into a clean environment and confirming that `mcp.server.fastmcp` raises `ModuleNotFoundError` while the low-level `mcp.server.Server` API still imports cleanly. That distinction matters across the fleet: sibling packages break for different reasons, or not at all, depending on which API each one uses.

## Upgrading

`pip install --upgrade pycode-kg`. Nothing to rebuild — no graph, index, or snapshot format changed, and the only difference in resolved dependencies is that `mcp` stays on the 1.x line.

If you pinned `pycode-kg==0.21.0` and your MCP server stopped starting, this is the fix. If you install PyCodeKG alongside other KGRAG packages, note that several are still published with an unbounded `mcp` floor and may pull 2.0 independently of this release.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
