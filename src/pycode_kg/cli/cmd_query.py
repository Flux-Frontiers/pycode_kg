"""
cmd_query.py

Click subcommands for querying and packing snippets from the PyCodeKG:

  query   — hybrid semantic + graph query, prints a ranked result summary
  pack    — hybrid query + source-grounded snippet packing, outputs markdown or JSON
"""

from __future__ import annotations

from pathlib import Path

import click

from pycode_kg.cli.main import cli
from pycode_kg.cli.options import lancedb_option, model_option, sqlite_option
from pycode_kg.kg import PyCodeKG
from pycode_kg.store import DEFAULT_RELS

_DEFAULT_RELS_STR = ",".join(DEFAULT_RELS)


@cli.command("query")
@click.argument("query_text", metavar="QUERY")
@sqlite_option
@lancedb_option
@click.option(
    "--table",
    default="pycodekg_nodes",
    show_default=True,
    help="LanceDB table name.",
)
@model_option
@click.option("--k", type=int, default=8, show_default=True, help="Top-k semantic hits.")
@click.option("--hop", type=int, default=1, show_default=True, help="Graph expansion hops.")
@click.option(
    "--rels",
    default=_DEFAULT_RELS_STR,
    show_default=True,
    help="Comma-separated edge types to expand.",
)
@click.option("--include-symbols", is_flag=True, help="Include symbol nodes in output.")
def query(
    query_text: str,
    sqlite: str,
    lancedb: str,
    table: str,
    model: str,
    k: int,
    hop: int,
    rels: str,
    include_symbols: bool,
) -> None:
    """Run a hybrid semantic + graph query and print a ranked result summary.

    Performs vector-similarity seeding followed by graph expansion to find the
    most relevant nodes (modules, classes, functions, methods) in the knowledge
    graph, then prints a ranked summary table to stdout.

    :param query_text: Natural-language query, e.g. ``"database connection setup"``.
    :param sqlite: Path to the SQLite graph database.
    :param lancedb: Directory for the LanceDB vector index.
    :param table: LanceDB table name (default ``pycodekg_nodes``).
    :param model: Sentence-transformer embedding model name.
    :param k: Number of semantic seed nodes (default 8).
    :param hop: Graph expansion hops from each seed (default 1).
    :param rels: Comma-separated edge types to follow during expansion.
    :param include_symbols: When set, include low-level symbol nodes in results.
    """
    rels_tuple = tuple(r.strip() for r in rels.split(",") if r.strip())

    # query-only does not need repo_root for source reading; use sqlite parent as placeholder
    repo_root = Path(sqlite).parent

    kg = PyCodeKG(
        repo_root=repo_root,
        db_path=Path(sqlite),
        lancedb_dir=Path(lancedb),
        model=model,
        table=table,
    )

    result = kg.query(
        query_text,
        k=k,
        hop=hop,
        rels=rels_tuple,
        include_symbols=include_symbols,
    )
    result.print_summary()
    kg.close()


@cli.command("pack")
@click.argument("query_text", metavar="QUERY")
@click.option(
    "--repo-root",
    default=".",
    type=click.Path(),
    show_default=True,
    help="Repository root directory.",
)
@sqlite_option
@lancedb_option
@click.option(
    "--table",
    default="pycodekg_nodes",
    show_default=True,
    help="LanceDB table name.",
)
@model_option
@click.option("--k", type=int, default=8, show_default=True, help="Top-k semantic hits.")
@click.option("--hop", type=int, default=1, show_default=True, help="Graph expansion hops.")
@click.option(
    "--rels",
    default=_DEFAULT_RELS_STR,
    show_default=True,
    help="Comma-separated edge types to expand.",
)
@click.option("--include-symbols", is_flag=True, help="Include symbol nodes.")
@click.option(
    "--context",
    type=int,
    default=5,
    show_default=True,
    help="Extra context lines before/after each definition span.",
)
@click.option(
    "--max-lines",
    type=int,
    default=160,
    show_default=True,
    help="Max lines per snippet block.",
)
@click.option(
    "--max-nodes",
    type=int,
    default=None,
    help="Max nodes returned in pack (default: no limit).",
)
@click.option(
    "--out",
    type=click.Path(),
    default=None,
    help="Output file path (default: stdout).",
)
def pack(
    query_text: str,
    repo_root: str,
    sqlite: str,
    lancedb: str,
    table: str,
    model: str,
    k: int,
    hop: int,
    rels: str,
    include_symbols: bool,
    context: int,
    max_lines: int,
    max_nodes: int | None,
    out: str | None,
) -> None:
    """Run a hybrid query and emit source-grounded snippet packs.

    Performs vector-similarity seeding, graph expansion, and source snippet
    extraction, then outputs a Markdown context pack with ranked, deduplicated
    code snippets and line numbers — ready for direct LLM ingestion.

    :param query_text: Natural-language query, e.g. ``"configuration loading"``.
    :param repo_root: Repository root directory used for source file lookup.
    :param sqlite: Path to the SQLite graph database.
    :param lancedb: Directory for the LanceDB vector index.
    :param table: LanceDB table name (default ``pycodekg_nodes``).
    :param model: Sentence-transformer embedding model name.
    :param k: Number of semantic seed nodes (default 8).
    :param hop: Graph expansion hops from each seed (default 1).
    :param rels: Comma-separated edge types to follow during expansion.
    :param include_symbols: When set, include low-level symbol nodes.
    :param context: Extra context lines before/after each definition span.
    :param max_lines: Maximum lines per snippet block (default 160).
    :param max_nodes: Maximum nodes to include in the pack (``None`` for no limit).
    :param out: Output file path; when omitted, writes to stdout.
    """
    rels_tuple = tuple(r.strip() for r in rels.split(",") if r.strip())

    kg = PyCodeKG(
        repo_root=Path(repo_root),
        db_path=Path(sqlite),
        lancedb_dir=Path(lancedb),
        model=model,
        table=table,
    )

    snippet_pack = kg.pack(
        query_text,
        k=k,
        hop=hop,
        rels=rels_tuple,
        include_symbols=include_symbols,
        context=context,
        max_lines=max_lines,
        max_nodes=max_nodes,
    )
    kg.close()

    if out:
        snippet_pack.save(out)
        print(f"OK: wrote pack to {out}")
    else:
        print(snippet_pack.to_markdown())
