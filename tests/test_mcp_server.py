"""
test_mcp_server.py

Import-level regression tests for pycode_kg.mcp_server.

The MCP server builds its ``FastMCP`` instance and registers every tool with
module-level decorators, so an incompatible ``mcp`` release breaks it at
*import* time rather than at call time — and only for people who installed
from PyPI, since a developer's pinned lock file keeps working.

mcp 2.0 removed the bundled ``mcp.server.fastmcp`` module (FastMCP was split
out into the standalone ``fastmcp`` package), which makes the import at
``mcp_server.py`` line 145 fail outright. `pyproject.toml` pins ``mcp<2`` for
that reason; these tests fail loudly if the pin is lifted without porting the
server, instead of shipping a broken console script.

Ported from agent_kg's ``tests/test_mcp_server.py``, where the same gap let
mcp 2.0 through CI and left ``agentkg-mcp`` crashing for every installer.
"""

from __future__ import annotations

import importlib


def test_server_module_imports():
    """The module must import cleanly against the installed mcp release."""
    importlib.import_module("pycode_kg.mcp_server")


def test_fastmcp_import_path_exists():
    """``mcp.server.fastmcp`` must exist — mcp 2.0 removed it.

    Asserted directly so the failure names the actual incompatibility rather
    than surfacing as an opaque ImportError from our own module.
    """
    importlib.import_module("mcp.server.fastmcp")


def test_entry_point_target_exists():
    """``pycodekg-mcp`` resolves to pycode_kg.mcp_server:main."""
    server = importlib.import_module("pycode_kg.mcp_server")
    assert callable(server.main)


def test_tools_are_registered():
    """The tool list survives registration and covers the documented surface."""
    server = importlib.import_module("pycode_kg.mcp_server")
    names = {t.name for t in _list_tools(server)}
    assert names, "no tools registered"
    # A representative slice across the tool groups; a registration failure
    # tends to drop everything rather than one name.
    for expected in ("graph_stats", "query_codebase", "pack_snippets", "get_node"):
        assert expected in names, f"{expected} missing from registered tools"


def test_tool_count_matches_documented_surface():
    """The server advertises 19 tools, as stated in docs/MCP.md and the README."""
    server = importlib.import_module("pycode_kg.mcp_server")
    assert len(_list_tools(server)) == 19


def _list_tools(server):
    """Return the registered FastMCP tools.

    ``FastMCP.list_tools()`` is async; run it on a private loop rather than
    depending on an async test plugin.
    """
    import asyncio

    return asyncio.run(server.mcp.list_tools())
