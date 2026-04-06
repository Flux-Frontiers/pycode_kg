"""
Legacy module — functionality moved to CLI.

This module is deprecated. Use the CLI command instead::

    poetry run codekg build-lancedb --repo /path/to/repo

Or import from the CLI module directly::

    from code_kg.cli.cmd_build import build_lancedb
"""

from code_kg.cli.cmd_build import build_lancedb

__all__ = ["build_lancedb"]
