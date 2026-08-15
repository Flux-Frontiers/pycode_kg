"""
cmd_explain.py

Click subcommand for explaining code nodes:

  explain  — get a natural-language explanation of a code node by its ID

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

from __future__ import annotations

from pathlib import Path

import click

from pycode_kg.cli.main import cli
from pycode_kg.cli.options import model_option, sqlite_option, vectors_option
from pycode_kg.explain import render_explain
from pycode_kg.kg import PyCodeKG


@cli.command("explain")
@click.argument("node_id", metavar="NODE_ID")
@sqlite_option
@vectors_option
@model_option
@click.option(
    "--out",
    type=click.Path(),
    default=None,
    help="Output file path (default: stdout).",
)
def explain(
    node_id: str,
    sqlite: str,
    vectors: str,
    model: str,
    out: str | None,
) -> None:
    """Get a natural-language explanation of a code node.

    NODE_ID is the stable identifier of a node, e.g.:
    fn:src/pycode_kg/store.py:GraphStore.expand
    """
    # explain-only does not need repo_root for source reading; use sqlite parent as placeholder
    repo_root = Path(sqlite).parent

    kg = PyCodeKG(
        repo_root=repo_root,
        db_path=Path(sqlite),
        vectors_path=Path(vectors),
        model=model,
    )

    # Fail fast for scripting: distinguish missing-node from rendered output.
    if kg.node(node_id) is None:
        click.echo(f"[ERROR] Node not found: {node_id}", err=True)
        kg.close()
        raise SystemExit(1)

    markdown_output = render_explain(
        kg,
        node_id,
        snippets_hint="pycodekg pack",
    )

    if out:
        Path(out).write_text(markdown_output)
        click.echo(f"[OK] Explanation written to {out}")
    else:
        click.echo(markdown_output)

    kg.close()
