# Release Notes -- v0.29.0

> Released: 2026-10-26

PyCodeKG's MCP server now runs on the fleet's shared base, `kg_utils.mcp`, so
its first five tools have the same names on every fleet KG server: `stats`,
`query`, `pack`, `get_node` and `neighbors`. PyCodeKG was the pilot for that
change; its 15 domain tools are unchanged. Tool names, some arguments and the
shape of `stats()` change, so read Upgrading before you install.

## What changed

**Canonical tool names.** `graph_stats` is `stats`, `query_codebase` is
`query`, `pack_snippets` is `pack`, and `get_node(include_edges=True)` is
`get_node` followed by the new `neighbors`. There are no aliases. `query` and
`pack` keep PyCodeKG's hybrid reranking, per-module cap, `paths`,
`include_symbols` and edge provenance.

**One command, standard flags.** `pycodekg mcp` and `pycodekg-mcp` are the
same command, with `--repo`, `--db`, `--vectors`, `--model`,
`--transport stdio|streamable-http`, `--host`, `--port` and `--manifest`, which
lists the tools as JSON without opening the graph. The graph opens per session
and closes after, a repository with no graph is refused instead of served
empty, and stray output can no longer corrupt the stdio stream.

**Generated instructions.** The server's instructions are built from a short
preamble and each tool's docstring, so they cannot drift from the tools.

**Statistics in the fleet shape.** `PyCodeKG.stats()` returns `kind`, `nodes`
(`total`, `by_kind`) and `edges` (`total`, `by_rel`), plus `meaningful_nodes`
and the vector backend. Snapshots keep their flat keys.

## Upgrading

Rename the tools in agent instructions, permissions and scripts, pass `rels`
as a list (`["CALLS"]`), and drop `format="markdown"` from `query` calls and
`--transport sse` from configs. Code that read
`PyCodeKG.stats()["total_nodes"]` reads `["nodes"]["total"]` instead.
pycode-kg now needs kgmodule-utils 0.29.0, whose `[mcp]` extra brings the MCP
SDK. Rebuild nothing: existing graphs and indexes work as they are.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
