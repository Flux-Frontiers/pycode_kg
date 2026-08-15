"""
Root Click group for the PyCodeKG CLI.

Usage::

    python -m pycode_kg --help
    python -m pycode_kg --version

License: Elastic 2.0
"""

import importlib.metadata

import click


@click.group()
@click.version_option(version=importlib.metadata.version("pycode-kg"))
def cli():
    """PyCodeKG — knowledge graph tools for Python codebases."""
    pass


if __name__ == "__main__":
    cli()
