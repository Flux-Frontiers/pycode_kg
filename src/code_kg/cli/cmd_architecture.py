"""
cmd_architecture.py

Click subcommand for generating coherent architecture descriptions:

  architecture  — analyze codebase architecture, emit Markdown or JSON descriptions
"""

from __future__ import annotations

import importlib.metadata
import subprocess
from pathlib import Path

import click

from code_kg.architecture import ArchitectureAnalyzer
from code_kg.cli.main import cli
from code_kg.store import GraphStore


@cli.command("architecture")
@click.argument("repo_root", default=".", required=False)
@click.option(
    "--db",
    default=None,
    type=click.Path(),
    help="SQLite knowledge graph path (default: <repo>/.codekg/graph.sqlite).",
)
@click.option(
    "--markdown",
    "-m",
    "markdown_path",
    default=None,
    type=click.Path(),
    help="Save architecture description as Markdown.",
)
@click.option(
    "--json",
    "-j",
    "json_path",
    default=None,
    type=click.Path(),
    help="Save architecture description as JSON (infographic-ready).",
)
@click.option(
    "--analysis",
    type=click.Path(),
    default=None,
    help="Path to thorough analysis JSON (from 'codekg analyze') to incorporate.",
)
@click.option(
    "--load-latest",
    is_flag=True,
    help="Auto-load latest thorough analysis from ~/.claude/codekg_analysis_latest.json.",
)
def architecture(
    repo_root: str,
    db: str | None,
    markdown_path: str | None,
    json_path: str | None,
    analysis: str | None,
    load_latest: bool,
) -> None:
    """Generate a coherent architecture description of a Python repository.

    Produces human-readable Markdown and machine-friendly JSON suitable for
    infographics. Can incorporate insights from 'codekg analyze' output.

    If neither --markdown nor --json is specified, prints Markdown to console.
    """
    repo_path = Path(repo_root).resolve()
    db_path = Path(db or repo_path / ".codekg" / "graph.sqlite")

    if not db_path.exists():
        raise click.UsageError(
            f"SQLite graph not found: {db_path}\nRun 'codekg build' first to index your repository."
        )

    store = GraphStore(db_path)
    try:
        # Get version and commit for provenance
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
            ).strip()[:10]
        except (subprocess.CalledProcessError, FileNotFoundError):
            commit = "unknown"

        # Try to get version from package
        version = "unknown"
        try:
            version = importlib.metadata.version("code-kg")
        except importlib.metadata.PackageNotFoundError:
            pass

        analyzer = ArchitectureAnalyzer(store, repo_path, version=version, commit=commit)

        # Load thorough analysis - try in order: explicit path, auto-load latest, skip
        import json  # pylint: disable=import-outside-toplevel

        analysis_loaded = False
        if analysis:
            try:
                with open(analysis) as f:
                    analysis_data = json.load(f)
                analyzer.incorporate_thorough_analysis(analysis_data)
                click.echo(f"OK Loaded analysis: {analysis}")
                analysis_loaded = True
            except (FileNotFoundError, json.JSONDecodeError) as e:
                click.echo(f"Warning: Could not load analysis file: {e}", err=True)

        elif load_latest:
            latest_path = Path.home() / ".claude" / "codekg_analysis_latest.json"
            if latest_path.exists():
                try:
                    with open(latest_path) as f:
                        analysis_data = json.load(f)
                    analyzer.incorporate_thorough_analysis(analysis_data)
                    click.echo("OK Auto-loaded latest analysis")
                    analysis_loaded = True
                except json.JSONDecodeError as e:
                    click.echo(f"Warning: Could not parse analysis file: {e}", err=True)

        if not analysis_loaded:
            click.echo("Tip: Run 'codekg analyze --json' then 'codekg architecture --load-latest'")
            click.echo("    for richer architectural insights.")

        # Generate outputs
        if markdown_path:
            arch_md = analyzer.analyze_to_markdown()
            with open(markdown_path, "w") as f:
                f.write(arch_md)
            click.echo(f"OK Architecture Markdown: {markdown_path}")

        if json_path:
            arch_json = analyzer.analyze_to_json()
            with open(json_path, "w") as f:
                f.write(arch_json)
            click.echo(f"OK Architecture JSON: {json_path}")

        if not markdown_path and not json_path:
            # Print to console
            arch_md = analyzer.analyze_to_markdown()
            click.echo(arch_md)

    finally:
        store.close()
