#!/usr/bin/env python3
"""
Dispatcher for python -m pycode_kg <command> [args...]

Routes to Click group-based CLI.
"""

from pycode_kg.cli.main import cli

if __name__ == "__main__":
    cli()
