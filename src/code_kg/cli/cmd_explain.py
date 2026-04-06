"""
cmd_explain.py

Click subcommand for explaining code nodes:

  explain  — get a natural-language explanation of a code node by its ID
"""

from __future__ import annotations

from pathlib import Path

import click

from code_kg.cli.main import cli
from code_kg.cli.options import lancedb_option, model_option, sqlite_option
from code_kg.kg import CodeKG


@cli.command("explain")
@click.argument("node_id", metavar="NODE_ID")
@sqlite_option
@lancedb_option
@click.option(
    "--table",
    default="codekg_nodes",
    show_default=True,
    help="LanceDB table name.",
)
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
    lancedb: str,
    table: str,
    model: str,
    out: str | None,
) -> None:
    """Get a natural-language explanation of a code node.

    NODE_ID is the stable identifier of a node, e.g.:
    fn:src/code_kg/store.py:GraphStore.expand
    """
    # explain-only does not need repo_root for source reading; use sqlite parent as placeholder
    repo_root = Path(sqlite).parent

    kg = CodeKG(
        repo_root=repo_root,
        db_path=Path(sqlite),
        lancedb_dir=Path(lancedb),
        model=model,
        table=table,
    )

    node = kg.node(node_id)

    if node is None:
        click.echo(f"[ERROR] Node not found: {node_id}", err=True)
        kg.close()
        raise SystemExit(1)

    markdown_output = _explain_node(kg, node_id, node)

    if out:
        Path(out).write_text(markdown_output)
        click.echo(f"[OK] Explanation written to {out}")
    else:
        click.echo(markdown_output)

    kg.close()


def _explain_node(kg: CodeKG, node_id: str, node: dict) -> str:
    """Generate markdown explanation for a node.

    :param kg: CodeKG instance
    :param node_id: Node identifier
    :param node: Node dict from kg.node()
    :return: Markdown-formatted explanation
    """
    out: list[str] = []

    # Header with kind and name
    kind = node.get("kind", "unknown")
    name = node.get("qualname") or node.get("name", "unknown")
    out.append(f"# {kind.capitalize()}: `{name}`\n")

    # Metadata
    out.append("## Metadata\n")
    if node.get("module_path"):
        out.append(f"- **Module**: `{node['module_path']}`")
    if node.get("lineno") is not None:
        out.append(
            f"- **Location**: line {node['lineno']}"
            + (f"–{node['end_lineno']}" if node.get("end_lineno") else "")
        )
    out.append(f"- **ID**: `{node_id}`")
    out.append("")

    # Docstring
    docstring = node.get("docstring", "").strip()
    if docstring:
        out.append("## Documentation\n")
        out.append(docstring)
        out.append("")

    # Get callers
    try:
        caller_list = kg.callers(node_id, rel="CALLS")
        if caller_list:
            out.append("## Called By (Callers)\n")
            out.append(f"This {kind} is called by **{len(caller_list)}** other function(s):\n")
            for caller in caller_list[:10]:
                caller_name = caller.get("qualname") or caller.get("name", "unknown")
                caller_module = caller.get("module_path", "")
                out.append(f"- `{caller_name}` ({caller_module})")
            if len(caller_list) > 10:
                out.append(f"- ... and {len(caller_list) - 10} more")
            out.append("")
    except (AttributeError, ValueError, RuntimeError):
        pass

    # Get callees (what this function calls)
    try:
        if hasattr(kg, "_store") and kg._store is not None:
            edges = kg._store.edges_from(node_id, rel="CALLS", limit=50)
            if edges:
                out.append("## Calls (Callees)\n")
                out.append(f"This {kind} calls **{len(edges)}** other function(s):\n")
                callees = set()
                for edge in edges:
                    dst_id = edge.get("dst")
                    if dst_id is not None:
                        dst_node = kg.node(dst_id)
                        if dst_node:
                            dst_name = dst_node.get("qualname") or dst_node.get("name", "unknown")
                            callees.add(f"- `{dst_name}`")
                for callee in sorted(list(callees))[:10]:
                    out.append(callee)
                if len(callees) > 10:
                    out.append(f"- ... and {len(callees) - 10} more")
                out.append("")
    except (AttributeError, ValueError, RuntimeError):
        pass

    # Role assessment
    out.append("## Role in Codebase\n")
    try:
        caller_count = len(kg.callers(node_id, rel="CALLS"))
        if caller_count > 50:
            out.append(
                f"**High-value function**: Called {caller_count} times. "
                "This is likely a core API or bottleneck. Changes here may have wide impact."
            )
        elif caller_count > 10:
            out.append(
                f"**Important function**: Called {caller_count} times. "
                "Part of the essential infrastructure."
            )
        elif caller_count > 0:
            out.append(
                f"**Utility function**: Called {caller_count} time(s). "
                "Specific to particular use cases."
            )
        else:
            out.append("**Orphaned**: Never called. This may be dead code or internal utility.")
    except (AttributeError, ValueError, RuntimeError):
        out.append("Unable to determine call graph role.")

    out.append("")
    out.append("---\n")
    out.append("*Use `codekg pack` to retrieve the full source code.*")

    return "\n".join(out)
