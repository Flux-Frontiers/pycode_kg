"""The server opens the graph per session and closes it after.

kg_utils.mcp's lifespan replaces the module-level ``_kg`` this file used to
patch: the graph is opened when a session starts and closed when it ends, the
resource-cleanup pattern genealogy_kg set and kgrag_priv's FLEET_STANDARDS.md
records (sweep item 5). A repository with no graph is refused at session start
rather than served empty.

Drives the real server through ``mcp.shared.memory``'s in-process transport:
an actual ``Server.run()``/lifespan cycle, not a mock of the lifecycle.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from pycode_kg import PyCodeKG
from pycode_kg.mcp_server import build_server

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "core.py").write_text(textwrap.dedent("def helper():\n    return 42\n"))
    kg = PyCodeKG(root)
    kg.build_graph(wipe=True)
    kg.close()
    return root


async def test_the_session_opens_the_graph_and_closes_it(repo: Path, monkeypatch) -> None:
    closed: list[PyCodeKG] = []
    real_close = PyCodeKG.close

    def counting_close(self: PyCodeKG) -> None:
        closed.append(self)
        real_close(self)

    monkeypatch.setattr(PyCodeKG, "close", counting_close)
    async with create_connected_server_and_client_session(build_server(repo)) as session:
        result = await session.call_tool("stats", {})
        assert not result.isError
        assert closed == [], "the graph stays open for the whole session"

    # The server task has unwound by the time the block exits.
    assert len(closed) == 1
    assert closed[0]._store is not None and closed[0]._store._con is None  # noqa: SLF001


async def test_a_repo_without_a_graph_is_refused_not_served_empty(tmp_path: Path) -> None:
    with pytest.raises(BaseException) as info:  # noqa: PT011 -- an ExceptionGroup from the task group
        async with create_connected_server_and_client_session(build_server(tmp_path)) as session:
            await session.call_tool("stats", {})
    assert "no graph at" in repr(info.value) or any(
        "no graph at" in str(e) for e in getattr(info.value, "exceptions", ())
    )
    assert not (tmp_path / ".pycodekg" / "graph.sqlite").exists()
