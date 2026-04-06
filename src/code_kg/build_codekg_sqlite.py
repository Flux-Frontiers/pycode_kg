"""
Legacy module — functionality moved to CLI.

This module is deprecated. Use the CLI command instead::

    poetry run codekg build-sqlite --repo /path/to/repo

Or import from the CLI module directly::

    from code_kg.cli.cmd_build import build_sqlite
"""

from code_kg.cli.cmd_build import build_sqlite

__all__ = ["build_sqlite"]
