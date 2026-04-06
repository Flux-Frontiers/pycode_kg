"""
cmd_analyze.py

Click subcommand for running a thorough codebase analysis:

  analyze  — run CodeKGAnalyzer, emit a Markdown report (JSON optional via --json)
"""

from __future__ import annotations

from pathlib import Path

import click

from code_kg.cli.main import cli
from code_kg.cli.options import exclude_option, include_option
from code_kg.codekg_thorough_analysis import main as run_analysis
from code_kg.config import load_exclude_dirs, load_include_dirs


@cli.command("analyze")
@click.argument("repo_root", default=".", required=False)
@click.option(
    "--db",
    default=None,
    type=click.Path(),
    help="SQLite knowledge graph path (default: <repo>/.codekg/graph.sqlite).",
)
@click.option(
    "--lancedb",
    default=None,
    type=click.Path(),
    help="LanceDB vector index directory (default: <repo>/.codekg/lancedb).",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(),
    help="Markdown report output path (default: <repo>_analysis_<YYYYMMDD>.md).",
)
@click.option(
    "--json",
    "-j",
    "json_path",
    default=None,
    type=click.Path(),
    help="Write JSON snapshot to this path (omit to skip JSON output).",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress the Rich console summary table.",
)
@click.option(
    "--write-centrality",
    is_flag=True,
    help="Persist SIR centrality scores to the centrality_scores table in the SQLite graph.",
)
@include_option
@exclude_option
def analyze(
    repo_root: str,
    db: str | None,
    lancedb: str | None,
    output: str | None,
    json_path: str | None,
    quiet: bool,
    write_centrality: bool,
    include_dir: tuple[str, ...],
    exclude_dir: tuple[str, ...],
) -> None:
    """Run a thorough analysis of a Python repository.

    Analyzes complexity, hotspots, docstring coverage, circular dependencies,
    and other health signals. Outputs a Markdown report. Pass --json PATH to
    also write a JSON snapshot.
    """
    # Merge pyproject.toml config with CLI flags
    repo_path = Path(repo_root).resolve()
    include = load_include_dirs(repo_path) | set(include_dir)
    exclude = load_exclude_dirs(repo_path) | set(exclude_dir)

    # Run thorough analysis
    run_analysis(
        repo_root=repo_root,
        db_path=db,
        lancedb_path=lancedb,
        report_path=output,
        json_path=json_path,
        quiet=quiet,
        include=include if include else None,
        exclude=exclude if exclude else None,
        persist_centrality=write_centrality,
    )
