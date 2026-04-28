"""
cmd_viz.py

Click subcommands for launching PyCodeKG visualizers:

  viz          — Streamlit-based interactive graph explorer
  viz3d        — PyVista/PyQt5 3-D interactive knowledge-graph visualizer
  viz-timeline — Interactive temporal metrics visualization from snapshots
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import click

from pycode_kg.cli.main import cli

_VIZ_EXTRA = 'pip install "pycode-kg[viz]"'


@cli.command("viz")
@click.option(
    "--db",
    default=".pycodekg/graph.sqlite",
    show_default=True,
    help="SQLite database path.",
)
@click.option(
    "--port",
    default="8500",
    show_default=True,
    help="Streamlit server port.",
)
@click.option(
    "--no-browser",
    is_flag=True,
    help="Do not open a browser window automatically.",
)
def viz(db: str, port: str, no_browser: bool) -> None:
    """Launch the PyCodeKG Streamlit visualizer."""
    if importlib.util.find_spec("streamlit") is None:
        raise click.UsageError(
            f"streamlit is not installed. Install viz dependencies with:\n  {_VIZ_EXTRA}"
        )

    app_path = Path(__file__).parent.parent / "app.py"

    if not app_path.exists():
        click.echo(f"ERROR: Could not find app.py at {app_path}", err=True)
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port),
        "--",
        "--db",
        db,
    ]
    if no_browser:
        cmd[5:5] = ["--server.headless", "true"]

    click.echo(f"Launching PyCodeKG Explorer on http://localhost:{port}")
    click.echo(f"  app   : {app_path}")
    click.echo(f"  db    : {db}")
    click.echo("  Press Ctrl+C to stop.\n")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("\nStopped.")


@cli.command("viz3d")
@click.option(
    "--db",
    default=".pycodekg/graph.sqlite",
    show_default=True,
    help="SQLite database path.",
)
@click.option(
    "--layout",
    type=click.Choice(["allium", "funnel"]),
    default="allium",
    show_default=True,
    help=(
        "3-D layout strategy. "
        "'allium' renders each module as a Giant Allium plant; "
        "'funnel' stratifies nodes by kind across Z layers."
    ),
)
@click.option(
    "--width",
    type=int,
    default=1400,
    show_default=True,
    help="Window width in pixels.",
)
@click.option(
    "--height",
    type=int,
    default=900,
    show_default=True,
    help="Window height in pixels.",
)
def viz3d(db: str, layout: str, width: int, height: int) -> None:
    """Launch the PyCodeKG 3-D PyVista knowledge-graph visualizer."""
    db_path = Path(db)
    if not db_path.exists():
        raise click.UsageError(
            f"Database not found: {db_path}\n"
            "Run 'pycodekg build-sqlite' first to index your repository."
        )

    from pycode_kg.viz3d import launch  # pylint: disable=import-outside-toplevel

    launch(
        db_path=str(db_path),
        layout_name=layout,
        width=width,
        height=height,
    )


@cli.command("viz-timeline")
@click.option(
    "--snapshots",
    default=".pycodekg/snapshots",
    show_default=True,
    help="Snapshots directory path.",
)
@click.option(
    "--type",
    type=click.Choice(["2d", "3d"]),
    default="2d",
    show_default=True,
    help="Visualization type: 2d (subplots) or 3d (scatter plot).",
)
def viz_timeline(snapshots: str, type: str) -> None:
    """Display temporal metrics evolution across commits."""
    snapshots_path = Path(snapshots)
    if not snapshots_path.exists():
        raise click.UsageError(
            f"Snapshots directory not found: {snapshots_path}\n"
            "Run 'pycodekg snapshot save' first to capture snapshots."
        )

    if importlib.util.find_spec("plotly") is None:
        raise click.UsageError(
            f"plotly is not installed. Install viz dependencies with:\n  {_VIZ_EXTRA}"
        )

    from pycode_kg.viz3d_timeline import (  # pylint: disable=import-outside-toplevel
        create_3d_timeline_figure,
        create_timeline_figure,
        display_timeline_summary,
    )

    # Display text summary
    summary = display_timeline_summary(snapshots_path)
    click.echo(summary)

    # Create and display visualization
    if type == "3d":
        fig = create_3d_timeline_figure(snapshots_path)
    else:
        fig = create_timeline_figure(snapshots_path)

    try:
        fig.show()
    except (OSError, AttributeError, ImportError) as e:
        click.echo(f"Could not display visualization: {e}", err=True)
