#!/usr/bin/env python3
"""Click command for Structural Importance Ranking (SIR)."""

from __future__ import annotations

import json
from pathlib import Path

import click

from code_kg.analysis.centrality import (
    StructuralImportanceRanker,
    aggregate_module_scores,
)
from code_kg.cli.main import cli


@cli.command("centrality")
@click.option(
    "--db",
    type=click.Path(path_type=Path, dir_okay=False),
    default=Path(".codekg/graph.sqlite"),
    show_default=True,
    help="Path to the CodeKG SQLite graph.",
)
@click.option(
    "--kind",
    "kinds",
    multiple=True,
    type=click.Choice(["module", "class", "function", "method"], case_sensitive=False),
    help="Restrict output to one or more node kinds.",
)
@click.option("--top", type=int, default=25, show_default=True, help="Maximum rows to show.")
@click.option(
    "--group-by",
    type=click.Choice(["node", "module"], case_sensitive=False),
    default="node",
    show_default=True,
    help="Return node-level or module-level rankings.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON instead of a table.")
@click.option("--write-db", is_flag=True, help="Persist node-level scores into centrality_scores.")
def cmd_centrality(
    db: Path,
    kinds: tuple[str, ...],
    top: int,
    group_by: str,
    as_json: bool,
    write_db: bool,
) -> None:
    """Compute Structural Importance Ranking over the resolved CodeKG graph."""
    ranker = StructuralImportanceRanker(db)
    records = ranker.compute(kinds=set(kinds) if kinds else None, top=None)

    if write_db:
        ranker.write_scores(records)

    if group_by == "module":
        payload = aggregate_module_scores(records)[:top]
        if as_json:
            click.echo(json.dumps(payload, indent=2))
            return
        _print_module_table(payload)
        return

    node_payload = records[:top]
    if as_json:
        click.echo(json.dumps([_record_to_dict(r) for r in node_payload], indent=2))
        return
    _print_node_table(node_payload)


def _record_to_dict(record) -> dict:
    return {
        "node_id": record.node_id,
        "kind": record.kind,
        "name": record.name,
        "module_path": record.module_path,
        "score": record.score,
        "rank": record.rank,
        "inbound_count": record.inbound_count,
        "cross_module_inbound": record.cross_module_inbound,
        "rel_breakdown": record.rel_breakdown,
        "top_contributors": record.top_contributors,
    }


def _print_node_table(records) -> None:
    headers = (
        "Rank",
        "Score",
        "Kind",
        "Name",
        "Inbound",
        "XMod",
        "Module",
    )
    rows = [
        (
            r.rank,
            f"{r.score:.6f}",
            r.kind,
            r.name,
            r.inbound_count,
            r.cross_module_inbound,
            r.module_path or "",
        )
        for r in records
    ]
    click.echo(click.format_filename(""))
    click.echo(_format_table(headers, rows))


def _print_module_table(payload) -> None:
    headers = ("Rank", "Score", "Members", "Module")
    rows = [
        (row["rank"], f"{row['score']:.6f}", row["member_count"], row["module_path"])
        for row in payload
    ]
    click.echo(_format_table(headers, rows))


def _format_table(headers, rows) -> str:
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(str(value)))
    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    lines = [fmt.format(*headers), fmt.format(*["-" * w for w in widths])]
    lines.extend(fmt.format(*[str(v) for v in row]) for row in rows)
    return "\n".join(lines)
