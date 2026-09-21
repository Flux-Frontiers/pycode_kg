# Release Notes -- v0.28.0

> Released: 2026-09-20

The MCP server closes the graph on shutdown, `query()` and `pack()` reject
bad arguments, and the pre-commit hook `pycodekg install-hooks` writes finds
`pycodekg` on `PATH` instead of assuming a repo venv. Together they make
PyCodeKG a well-behaved global tool, which is what the fleet decided it
should be.

## What changed

**Tools are global, and the hook says so.** The hook template had
`$REPO_ROOT/.venv/bin/pycodekg` hard-wired with `|| exit 1`, the shape that
left a sibling repo's hooks failing silently for weeks. It now resolves
`pycodekg` from `PATH`, the global `uv tool` install, and falls back to a
`.venv` copy only if one exists. Re-run `pycodekg install-hooks --force` in
any repo to pick it up. The template had no test; it has seven. In the same
spirit the `kg` Poetry group is gone: it held `doc-kg`, a tool this repo runs
for `.mcp.json` but never imports.

**The server cleans up after itself.** `pycodekg-mcp` closes the graph's
SQLite connection when it shuts down, via `FastMCP(lifespan=...)`, on both
the stdio and SSE transports. Verified through the MCP SDK's in-process
transport, a real server lifecycle rather than a mocked `close`.

**Arguments are checked in the base class.** `PyCodeKG` inherits `query()`
and `pack()` from kgmodule-utils' `KGModule`, and 0.23.0 checks their
arguments there: an empty query, `k` outside 1 to 100, `hop` outside 0 to 5
or `max_nodes` outside 1 to 500 raises `ValueError` naming the parameter.
Nothing changed in this repo for it beyond the floor.

**The docs stopped pointing users at a venv.** The worked MCP examples, and
the `setup-pycodekg-mcp` command that used to hunt for a venv binary, name
the global tools now. The changelog's `[0.10.0]` and `[0.9.1]` sections are
in date order at last.

## Upgrading

No rebuild and no migration. `kgmodule-utils` must be at least 0.23.0. A
caller passing an out-of-range `k`, `hop` or `max_nodes`, or an empty query,
now gets a `ValueError` instead of a silent result. If this repo's tooling
was installed with `poetry install --with kg`, drop the `kg`: `dockg` comes
from `uv tool install doc-kg`. After upgrading the global tool, re-run
`pycodekg install-hooks --force` wherever the hook is installed.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
