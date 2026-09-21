"""The MCP server's lifespan hook closes the graph's SQLite connection on
shutdown -- the resource-cleanup pattern genealogy_kg set and kgrag_priv's
FLEET_STANDARDS.md records (sweep item 5). FastMCP's ``lifespan=`` fires on
both the stdio and SSE transports, since both route through the same
underlying ``Server.run()``.

Drives the real server through ``mcp.shared.memory``'s in-process transport:
an actual ``Server.run()``/lifespan cycle, not a mock of ``close``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from pycode_kg import PyCodeKG, mcp_server

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_lifespan_closes_kg_on_server_shutdown(tmp_path: Path) -> None:
    # An unbuilt repo is enough. The tool may report an error on an empty
    # graph; what matters is that reaching stats() opens the store, and that
    # the server's shutdown closes it again.
    kg = PyCodeKG(tmp_path)
    mcp_server._kg = kg
    try:
        async with create_connected_server_and_client_session(mcp_server.mcp) as session:
            await session.call_tool("graph_stats", {})

        # The server task has fully unwound by the time the block above
        # exits, so the lifespan's `finally: kg.close()` has already run.
        assert kg._store is not None  # noqa: SLF001 - the tool call opened it
        assert kg._store._con is None  # noqa: SLF001 - and the lifespan closed it
    finally:
        mcp_server._kg = None


async def test_lifespan_is_a_noop_when_kg_was_never_set() -> None:
    assert mcp_server._kg is None
    async with create_connected_server_and_client_session(mcp_server.mcp):
        pass
    assert mcp_server._kg is None
