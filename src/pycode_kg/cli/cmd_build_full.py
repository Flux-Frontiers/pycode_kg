"""
cmd_build_full.py

Click subcommand for building the full PyCodeKG pipeline in one step:

    build   - repo -> AST -> SQLite -> LanceDB (full pipeline, always wipes)
    update  - repo -> AST -> SQLite -> LanceDB (incremental upsert, no wipe)
"""

from __future__ import annotations

import time
from pathlib import Path

import click

from pycode_kg.cli.main import cli
from pycode_kg.cli.options import (
    exclude_option,
    include_option,
    model_option,
    repo_option,
)
from pycode_kg.config import load_exclude_dirs, load_include_dirs
from pycode_kg.graph import CodeGraph
from pycode_kg.index import (
    SemanticIndex,
    SentenceTransformerEmbedder,
    suppress_ingestion_logging,
)
from pycode_kg.store import GraphStore


def _banner(repo_root: Path, label: str) -> None:
    """Print the build header banner."""
    click.echo()
    click.echo(f"  PyCodeKG  {label}")
    click.echo("  repo - AST - SQLite - LanceDB")
    click.echo(f"  repo  {repo_root}")
    click.echo()


def _step_result(n: int, label: str, pairs: list[tuple[str, str]], elapsed: float) -> None:
    """Print a single-line step result after the step completes."""
    kv = "  ".join(f"{k}={v}" for k, v in pairs)
    click.echo(f"  Step {n}  {label}  {kv}  ({elapsed:.1f}s)")


def _done(elapsed: float) -> None:
    """Print a compact build-complete summary."""
    click.echo()
    click.echo(f"  done  ({elapsed:.1f}s)")
    click.echo()


def _common_options(fn):
    """Shared Click options for build and update commands."""
    fn = repo_option(fn)
    fn = click.option(
        "--db",
        default=None,
        type=click.Path(),
        show_default=False,
        help="SQLite database path (default: <repo>/.pycodekg/graph.sqlite).",
    )(fn)
    fn = click.option(
        "--lancedb",
        default=None,
        type=click.Path(),
        show_default=False,
        help="LanceDB directory path (default: <repo>/.pycodekg/lancedb).",
    )(fn)
    fn = click.option(
        "--table",
        default="pycodekg_nodes",
        show_default=True,
        help="LanceDB table name.",
    )(fn)
    fn = model_option(fn)
    fn = click.option(
        "-v", "--verbose", is_flag=True, help="Show LanceDB and embedder progress output."
    )(fn)
    fn = click.option(
        "--kinds",
        default="module,class,function,method",
        show_default=True,
        help="Comma-separated node kinds to index.",
    )(fn)
    fn = click.option(
        "--batch",
        type=int,
        default=256,
        show_default=True,
        help="Embedding batch size.",
    )(fn)
    fn = include_option(fn)
    fn = exclude_option(fn)
    return fn


def _run_pipeline(
    repo: str,
    db: str | None,
    lancedb: str | None,
    table: str,
    model: str,
    verbose: bool,
    kinds: str,
    batch: int,
    include_dir: tuple[str, ...],
    exclude_dir: tuple[str, ...],
    *,
    wipe: bool,
    label: str,
) -> None:
    """Execute the full build pipeline (shared by build and update)."""
    repo_root = Path(repo).resolve()
    db_path = Path(db) if db else repo_root / ".pycodekg" / "graph.sqlite"
    lancedb_dir = Path(lancedb) if lancedb else repo_root / ".pycodekg" / "lancedb"

    include = load_include_dirs(repo_root) | set(include_dir)
    exclude = load_exclude_dirs(repo_root) | set(exclude_dir)

    _banner(repo_root, label)
    t_total = time.monotonic()

    # Step 1: Build SQLite graph
    t1 = time.monotonic()
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

    _step_result(
        1,
        "SQLite",
        [
            ("nodes", str(len(nodes))),
            ("edges", str(len(edges))),
            ("resolved", str(resolved)),
        ],
        elapsed=time.monotonic() - t1,
    )

    # Step 2: Build LanceDB semantic index
    if not verbose:
        suppress_ingestion_logging()

    t2 = time.monotonic()
    kinds_tuple = tuple(k.strip() for k in kinds.split(",") if k.strip())
    embedder = SentenceTransformerEmbedder(model)

    store = GraphStore(db_path)
    idx = SemanticIndex(
        lancedb_dir,
        embedder=embedder,
        table=table,
        index_kinds=kinds_tuple,
    )
    stats = idx.build(store, wipe=wipe, batch_size=batch, quiet=not verbose)
    store.close()

    _step_result(
        2,
        "LanceDB",
        [
            ("indexed", str(stats["indexed_rows"])),
            ("model", Path(model).name),
        ],
        elapsed=time.monotonic() - t2,
    )

    _done(elapsed=time.monotonic() - t_total)


@cli.command("build")
@_common_options
def build(
    repo: str,
    db: str | None,
    lancedb: str | None,
    table: str,
    model: str,
    verbose: bool,
    kinds: str,
    batch: int,
    include_dir: tuple[str, ...],
    exclude_dir: tuple[str, ...],
) -> None:
    """Build knowledge graph from scratch: wipes existing data, then extracts AST -> SQLite -> LanceDB."""
    _run_pipeline(
        repo,
        db,
        lancedb,
        table,
        model,
        verbose,
        kinds,
        batch,
        include_dir,
        exclude_dir,
        wipe=True,
        label="Full Build",
    )


@cli.command("update")
@_common_options
def update(
    repo: str,
    db: str | None,
    lancedb: str | None,
    table: str,
    model: str,
    verbose: bool,
    kinds: str,
    batch: int,
    include_dir: tuple[str, ...],
    exclude_dir: tuple[str, ...],
) -> None:
    """Update knowledge graph incrementally: upserts changes without wiping existing data."""
    _run_pipeline(
        repo,
        db,
        lancedb,
        table,
        model,
        verbose,
        kinds,
        batch,
        include_dir,
        exclude_dir,
        wipe=False,
        label="Update",
    )
