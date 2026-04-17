"""
cmd_build.py

Click subcommands for building the PyCodeKG knowledge graph:

    build-sqlite   - repo -> AST -> graph store
    build-lancedb  - graph store -> vector index
"""

from __future__ import annotations

from pathlib import Path

import click

from pycode_kg.cli.main import cli
from pycode_kg.cli.options import exclude_option, include_option, repo_option
from pycode_kg.config import load_exclude_dirs, load_include_dirs
from pycode_kg.graph import CodeGraph
from pycode_kg.index import (
    SemanticIndex,
    SentenceTransformerEmbedder,
    suppress_ingestion_logging,
)
from pycode_kg.pycodekg import DEFAULT_MODEL
from pycode_kg.store import GraphStore


@cli.command("build-sqlite")
@repo_option
@click.option(
    "--db",
    default=None,
    type=click.Path(),
    show_default=False,
    help="SQLite database path (default: <repo>/.pycodekg/graph.sqlite).",
)
@click.option("--wipe", is_flag=True, help="Delete existing graph first.")
@include_option
@exclude_option
def build_sqlite(
    repo: str,
    db: str | None,
    wipe: bool,
    include_dir: tuple[str, ...],
    exclude_dir: tuple[str, ...],
) -> None:
    """Extract a code knowledge graph from a Python repo and store it in SQLite."""
    repo_root = Path(repo).resolve()
    db_path = Path(db) if db else repo_root / ".pycodekg" / "graph.sqlite"

    # Merge pyproject.toml config with CLI flags
    include = load_include_dirs(repo_root) | set(include_dir)
    exclude = load_exclude_dirs(repo_root) | set(exclude_dir)

    graph = CodeGraph(
        repo_root,
        include=include if include else None,
        exclude=exclude if exclude else None,
    )
    nodes, edges = graph.extract().result()

    store = GraphStore(db_path)
    store.write(nodes, edges, wipe=wipe)
    resolved = store.resolve_symbols()
    store.close()

    print(f"OK: nodes={len(nodes)} edges={len(edges)} resolved={resolved} db={db_path}")


@cli.command("build-lancedb")
@repo_option
@click.option(
    "--sqlite",
    default=None,
    type=click.Path(),
    show_default=False,
    help="Path to graph.sqlite (default: <repo>/.pycodekg/graph.sqlite).",
)
@click.option(
    "--lancedb",
    default=None,
    type=click.Path(),
    show_default=False,
    help="Directory for LanceDB (default: <repo>/.pycodekg/lancedb).",
)
@click.option(
    "--table",
    default="pycodekg_nodes",
    show_default=True,
    help="LanceDB table name.",
)
@click.option(
    "--model",
    default=DEFAULT_MODEL,
    show_default=True,
    help="SentenceTransformer model name.",
)
@click.option("--wipe", is_flag=True, help="Delete existing vectors first.")
@click.option("-v", "--verbose", is_flag=True, help="Show LanceDB and embedder progress output.")
@click.option(
    "--kinds",
    default="module,class,function,method",
    show_default=True,
    help="Comma-separated node kinds to index.",
)
@click.option(
    "--batch",
    type=int,
    default=256,
    show_default=True,
    help="Embedding batch size.",
)
def build_lancedb(
    repo: str,
    sqlite: str | None,
    lancedb: str | None,
    table: str,
    model: str,
    wipe: bool,
    verbose: bool,
    kinds: str,
    batch: int,
) -> None:
    """Build a LanceDB semantic index from an existing pycodekg SQLite database."""
    repo_root = Path(repo).resolve()
    sqlite_path = Path(sqlite) if sqlite else repo_root / ".pycodekg" / "graph.sqlite"
    lancedb_dir = Path(lancedb) if lancedb else repo_root / ".pycodekg" / "lancedb"

    if not verbose:
        suppress_ingestion_logging()

    kinds_tuple = tuple(k.strip() for k in kinds.split(",") if k.strip())
    embedder = SentenceTransformerEmbedder(model)

    store = GraphStore(sqlite_path)
    idx = SemanticIndex(
        lancedb_dir,
        embedder=embedder,
        table=table,
        index_kinds=kinds_tuple,
    )
    stats = idx.build(store, wipe=wipe, batch_size=batch, quiet=not verbose)
    store.close()

    print(
        "OK:",
        f"indexed_rows={stats['indexed_rows']}",
        f"embedder={model}",
        f"dim={stats['dim']}",
        f"table={stats['table']}",
        f"lancedb_dir={stats['lancedb_dir']}",
        f"kinds={','.join(stats['kinds'])}",
    )
