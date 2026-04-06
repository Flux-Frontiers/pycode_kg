#!/usr/bin/env python3
"""
Dispatcher for python -m code_kg <command> [args...]

Routes to Click group-based CLI.
"""

from code_kg.cli.main import cli

if __name__ == "__main__":
    cli()
