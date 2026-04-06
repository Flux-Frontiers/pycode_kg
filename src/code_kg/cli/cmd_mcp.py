"""
cmd_mcp.py

Click subcommand for starting the CodeKG MCP server:

  mcp  — start the MCP server (thin wrapper around mcp_server.main)
"""

from __future__ import annotations

import click

from code_kg.cli.main import cli
from code_kg.codekg import DEFAULT_MODEL


@cli.command("mcp")
@click.option(
    "--repo",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Repository root directory.",
)
@click.option(
    "--db",
    default=".codekg/graph.sqlite",
    type=click.Path(),
    help="SQLite database path.",
)
@click.option(
    "--lancedb",
    default=".codekg/lancedb",
    type=click.Path(),
    help="LanceDB directory path.",
)
@click.option(
    "--model",
    default=DEFAULT_MODEL,
    help="Sentence-transformer model name.",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="MCP transport protocol.",
)
def mcp(repo: str, db: str, lancedb: str, model: str, transport: str) -> None:
    """Start the CodeKG MCP server."""
    try:
        from mcp.server.fastmcp import (  # pylint: disable=import-outside-toplevel
            FastMCP,  # noqa: F401
        )
    except ImportError:
        raise click.ClickException("'mcp' package not found. Install with: pip install mcp")

    argv = [
        "--repo",
        repo,
        "--db",
        db,
        "--lancedb",
        lancedb,
        "--model",
        model,
        "--transport",
        transport,
    ]

    from code_kg.mcp_server import main  # pylint: disable=import-outside-toplevel

    main(argv=argv)
