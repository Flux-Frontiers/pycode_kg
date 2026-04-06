"""
Root Click group for the CodeKG CLI.

Usage::

    python -m code_kg --help
    python -m code_kg --version
"""

import importlib.metadata

import click


@click.group()
@click.version_option(version=importlib.metadata.version("code-kg"))
def cli():
    """CodeKG — knowledge graph tools for Python codebases."""
    pass


if __name__ == "__main__":
    cli()
