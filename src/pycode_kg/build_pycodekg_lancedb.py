"""
Legacy module — functionality moved to CLI.

This module is deprecated. Use the CLI command instead::

    poetry run pycodekg build-lancedb --repo /path/to/repo

Or import from the CLI module directly::

    from pycode_kg.cli.cmd_build import build_lancedb
"""

from pycode_kg.cli.cmd_build import build_lancedb

__all__ = ["build_lancedb"]
