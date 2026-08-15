"""
Legacy module — functionality moved to CLI.

This module is deprecated. Use the CLI command instead::

    poetry run pycodekg build-sqlite --repo /path/to/repo

Or import from the CLI module directly::

    from pycode_kg.cli.cmd_build import build_sqlite

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

from pycode_kg.cli.cmd_build import build_sqlite

__all__ = ["build_sqlite"]
