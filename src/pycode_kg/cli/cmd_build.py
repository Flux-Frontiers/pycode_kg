"""
cmd_build.py

Click subcommands for building the PyCodeKG knowledge graph:

    build-sqlite  - repo -> AST -> graph store
    build-index   - graph store -> sqlite-vec vector index
"""

from __future__ import annotations

from pathlib import Path

import click
from kg_utils.semantic import META_COLUMNS
from kg_utils.vector_backend import SqliteVecBackend

from pycode_kg.cli.main import cli
from pycode_kg.cli.options import exclude_option, include_option, repo_option
from pycode_kg.config import load_exclude_dirs, load_include_dirs
from pycode_kg.index import (
    SemanticIndex,
    SentenceTransformerEmbedder,
    suppress_ingestion_logging,
)
from pycode_kg.module.extractor import EdgeSpec, NodeSpec, PyCodeKGExtractor
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

    extractor = PyCodeKGExtractor(
        repo_root,
        include=include if include else None,
        exclude=exclude if exclude else None,
    )
    node_specs: list[NodeSpec] = []
    edge_specs: list[EdgeSpec] = []
    for item in extractor.extract():
        if isinstance(item, NodeSpec):
            node_specs.append(item)
        else:
            edge_specs.append(item)

    store = GraphStore(db_path)
    store.write(node_specs, edge_specs, wipe=wipe)
    resolved = store.resolve_symbols()
    store.close()

    print(f"OK: nodes={len(node_specs)} edges={len(edge_specs)} resolved={resolved} db={db_path}")


@cli.command("build-index")
@repo_option
@click.option(
    "--sqlite",
    default=None,
    type=click.Path(),
    show_default=False,
    help="Path to graph.sqlite (default: <repo>/.pycodekg/graph.sqlite).",
)
@click.option(
    "--vectors",
    default=None,
    type=click.Path(),
    show_default=False,
    help="sqlite-vec store path (default: <repo>/.pycodekg/vectors.sqlite).",
)
@click.option(
    "--model",
    default=DEFAULT_MODEL,
    show_default=True,
    help="SentenceTransformer model name.",
)
@click.option("--wipe", is_flag=True, help="Delete existing vectors first.")
@click.option("-v", "--verbose", is_flag=True, help="Show embedder progress output.")
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
def build_index(
    repo: str,
    sqlite: str | None,
    vectors: str | None,
    model: str,
    wipe: bool,
    verbose: bool,
    kinds: str,
    batch: int,
) -> None:
    """Build the sqlite-vec semantic index from an existing pycodekg SQLite database."""
    repo_root = Path(repo).resolve()
    sqlite_path = Path(sqlite) if sqlite else repo_root / ".pycodekg" / "graph.sqlite"
    vectors_path = Path(vectors) if vectors else repo_root / ".pycodekg" / "vectors.sqlite"

    if not verbose:
        suppress_ingestion_logging()

    kinds_tuple = tuple(k.strip() for k in kinds.split(",") if k.strip())
    embedder = SentenceTransformerEmbedder(model)

    backend = SqliteVecBackend(vectors_path, dim=embedder.dim, meta_columns=META_COLUMNS)

    store = GraphStore(sqlite_path)
    idx = SemanticIndex(
        vectors_path.parent,
        embedder=embedder,
        index_kinds=kinds_tuple,
        backend=backend,
    )
    stats = idx.build(store, wipe=wipe, batch_size=batch, quiet=not verbose)
    store.close()

    print(
        "OK:",
        f"indexed_rows={stats['indexed_rows']}",
        f"embedder={model}",
        f"dim={stats['dim']}",
        f"vectors={vectors_path}",
        f"kinds={','.join(stats['kinds'])}",
    )
