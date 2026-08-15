"""
Shared Click option decorators for PyCodeKG CLI commands.

Each symbol is a reusable decorator factory that can be stacked onto any
Click command to provide consistent option names, defaults, and help text::

    @cli.command()
    @sqlite_option
    @vectors_option
    def my_command(sqlite, vectors):
        ...

License: Elastic 2.0
"""

import click

from pycode_kg.pycodekg import DEFAULT_MODEL

sqlite_option = click.option(
    "--sqlite",
    default=".pycodekg/graph.sqlite",
    type=click.Path(),
    show_default=True,
    help="SQLite database path.",
)

vectors_option = click.option(
    "--vectors",
    default=".pycodekg/vectors.sqlite",
    type=click.Path(),
    show_default=True,
    help="sqlite-vec vector store path.",
)

model_option = click.option(
    "--model",
    default=DEFAULT_MODEL,
    show_default=True,
    help="Sentence-transformer model name.",
)

repo_option = click.option(
    "--repo",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    show_default=True,
    help="Repository root directory.",
)

include_option = click.option(
    "--include-dir",
    multiple=True,
    help="Top-level directory names to include in indexing. Can be used multiple times. "
    "When none are specified, all directories are indexed. "
    "Also reads [tool.pycodekg].include from pyproject.toml.",
)

exclude_option = click.option(
    "--exclude-dir",
    multiple=True,
    help="Directory names to exclude at every depth during indexing. Can be used multiple times. "
    "E.g. --exclude-dir tests --exclude-dir benchmarks. "
    "Also reads [tool.pycodekg].exclude from pyproject.toml.",
)
