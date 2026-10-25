"""
cmd_mcp.py

``pycodekg mcp`` -- the fleet's standard MCP command, from :mod:`kg_utils.mcp`:

    pycodekg mcp [--repo DIR] [--db FILE] [--vectors FILE] [--model NAME]
                 [--transport stdio|streamable-http] [--host H] [--port N]
                 [--manifest]

Registering it imports neither ``mcp`` nor the server module, so every other
``pycodekg`` command starts as fast as before.

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from kg_utils.mcp import add_mcp_command

from pycode_kg.cli.main import cli

if TYPE_CHECKING:
    from kg_utils.mcp import KGServer


def _build_server(repo: Path, db: Path | None, vectors: Path | None, model: str | None) -> KGServer:
    from pycode_kg.mcp_server import build_server  # noqa: PLC0415 -- see the module docstring

    return build_server(repo, db, vectors, model)


mcp_command = add_mcp_command(cli, _build_server)
