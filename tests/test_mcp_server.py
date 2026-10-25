"""
test_mcp_server.py

The PyCodeKG MCP server on the fleet's shared base, ``kg_utils.mcp``.

Import-level regression tests first: the server's import of ``mcp`` breaks at
import time, not call time, when an incompatible ``mcp`` release is installed
(mcp 2.0 removed ``mcp.server.fastmcp``), and only for people who installed
from PyPI. Ported from agent_kg, where the same gap let mcp 2.0 through CI.

Then the surface step 1 of kgrag_priv's MCP centralization plan promises: the
five canonical tools first, under the same names as every fleet server, then
PyCodeKG's own; ``query`` and ``pack`` keep PyCodeKG's richer search; the
manifest answers without a graph and fast; ``pycodekg``'s other commands do
not pay for importing ``mcp``; and a real stdio subprocess serves.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import anyio
import pytest
from click.testing import CliRunner
from kg_utils.mcp import CANONICAL_TOOLS, manifest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import pycode_kg
from pycode_kg import PyCodeKG
from pycode_kg.cli import cli
from pycode_kg.mcp_server import EXTRA_TOOLS, build_server

_SRC = str(Path(pycode_kg.__file__).resolve().parents[1])

SAMPLE = {
    "pkg/__init__.py": "",
    "pkg/core.py": """
        class Widget:
            def spin(self):
                return helper()

        def helper():
            return 42
    """,
}


def _built_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    for rel, src in SAMPLE.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))
    kg = PyCodeKG(repo)
    kg.build_graph(wipe=True)
    kg.close()
    return repo


# ---------------------------------------------------------------------------
# Import level
# ---------------------------------------------------------------------------


def test_server_module_imports():
    """The module must import cleanly against the installed mcp release."""
    importlib.import_module("pycode_kg.mcp_server")


def test_fastmcp_import_path_exists():
    """``mcp.server.fastmcp`` must exist -- mcp 2.0 removed it.

    Asserted directly so the failure names the actual incompatibility rather
    than surfacing as an opaque ImportError from kg_utils.mcp.
    """
    importlib.import_module("mcp.server.fastmcp")


def test_entry_point_target_exists():
    """``pycodekg-mcp`` resolves to pycode_kg.mcp_server:main."""
    server = importlib.import_module("pycode_kg.mcp_server")
    assert callable(server.main)


# ---------------------------------------------------------------------------
# The tool surface
# ---------------------------------------------------------------------------


def test_canonical_tools_come_first_then_pycodekgs_own(tmp_path):
    names = [t["name"] for t in manifest(build_server(tmp_path))["tools"]]
    assert names == [*CANONICAL_TOOLS, *(fn.__name__ for fn in EXTRA_TOOLS)]
    assert len(names) == 20


def test_query_and_pack_keep_pycodekgs_richer_search(tmp_path):
    """Swapping in the plain canonical pair would have regressed ranking."""
    tools = {
        t["name"]: t["input_schema"]["properties"]
        for t in manifest(build_server(tmp_path))["tools"]
    }
    for name in ("query", "pack"):
        props = tools[name]
        assert props["rerank_mode"]["default"] == "hybrid", name
        assert props["max_per_module"]["default"] == 3, name
        assert "include_symbols" in props and "include_edge_provenance" in props, name
    assert "paths" in tools["query"]
    assert "missing_lineno_policy" in tools["pack"]


def test_instructions_carry_the_workflows_and_every_tool(tmp_path):
    server = build_server(tmp_path)
    text = server.instructions or ""
    assert "Recommended workflows" in text
    for name in (*CANONICAL_TOOLS, *(fn.__name__ for fn in EXTRA_TOOLS)):
        assert f"- `{name}`:" in text, name


# ---------------------------------------------------------------------------
# The command
# ---------------------------------------------------------------------------


def test_manifest_answers_without_a_graph_and_creates_nothing(tmp_path):
    result = CliRunner().invoke(cli, ["mcp", "--repo", str(tmp_path), "--manifest"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["canonical"] == list(CANONICAL_TOOLS)
    assert not (tmp_path / ".pycodekg").exists()


def test_manifest_is_fast(tmp_path):
    """Step 1's budget is one second; the bound here leaves CI headroom."""
    start = time.perf_counter()
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from pycode_kg.mcp_server import main; main()",
            "--repo",
            str(tmp_path),
            "--manifest",
        ],
        check=True,
        capture_output=True,
    )
    assert time.perf_counter() - start < 5.0


def test_both_entry_points_are_the_same_command(tmp_path):
    via_cli = CliRunner().invoke(cli, ["mcp", "--repo", str(tmp_path), "--manifest"]).output
    via_script = subprocess.run(
        [
            sys.executable,
            "-c",
            "from pycode_kg.mcp_server import main; main()",
            "--repo",
            str(tmp_path),
            "--manifest",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert json.loads(via_cli) == json.loads(via_script)


def test_sse_is_no_longer_offered(tmp_path):
    result = CliRunner().invoke(cli, ["mcp", "--repo", str(tmp_path), "--transport", "sse"])
    assert result.exit_code == 2


def test_other_commands_do_not_import_mcp():
    """Registering ``pycodekg mcp`` must not slow every other command."""
    out = subprocess.run(
        [sys.executable, "-c", "import sys, pycode_kg.cli; print('mcp' in sys.modules)"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert out == "False"


# ---------------------------------------------------------------------------
# A real stdio subprocess
# ---------------------------------------------------------------------------


def test_stdio_subprocess_initializes_and_serves(tmp_path):
    repo = _built_repo(tmp_path)
    params = StdioServerParameters(
        command=sys.executable,
        args=["-c", "from pycode_kg.mcp_server import main; main()", "--repo", str(repo)],
        env={**os.environ, "PYTHONPATH": _SRC},
    )

    async def session():
        with open(tmp_path / "stderr.log", "w", encoding="utf-8") as errlog:
            async with stdio_client(params, errlog=errlog) as (read, write):
                async with ClientSession(read, write) as client:
                    init = await client.initialize()
                    tools = await client.list_tools()
                    stats = await client.call_tool("stats", {})
                    found = await client.call_tool("find_node", {"name": "helper"})
                    return init, tools, stats, found

    init, tools, stats, found = anyio.run(session)
    assert (init.serverInfo.name, init.serverInfo.version) == ("pycodekg", pycode_kg.__version__)
    assert [t.name for t in tools.tools][:5] == list(CANONICAL_TOOLS)
    assert not stats.isError and stats.structuredContent["nodes"]["total"] > 0
    assert not found.isError and "helper" in found.content[0].text


# ---------------------------------------------------------------------------
# With the real model: query and pack through MCP
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.integration
def test_query_and_pack_with_the_real_model(tmp_path):
    from mcp.shared.memory import create_connected_server_and_client_session

    repo = tmp_path / "repo"
    for rel, src in SAMPLE.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))
    kg = PyCodeKG(repo)
    kg.build(wipe=True)
    kg.close()

    async def session():
        async with create_connected_server_and_client_session(build_server(repo)) as client:
            return (
                await client.call_tool("query", {"q": "spin the widget", "k": 3}),
                await client.call_tool(
                    "query", {"q": "spin the widget", "k": 3, "paths": "nowhere/"}
                ),
                await client.call_tool("pack", {"q": "helper returns 42", "k": 3}),
            )

    found, filtered, packed = anyio.run(session)
    assert not found.isError and found.structuredContent["returned_nodes"] >= 1
    assert found.structuredContent["nodes"][0]["relevance"]["mode"] == "hybrid"
    assert filtered.structuredContent["returned_nodes"] == 0
    assert not packed.isError and "def helper" in packed.content[0].text
