"""
config.py — Configuration utilities for CodeKG.

Reads and parses CodeKG configuration from pyproject.toml.
"""

from __future__ import annotations

import tomllib
from pathlib import Path


def _load_dir_list(repo_root: Path | str, key: str) -> set[str]:
    """Load a directory name list from ``[tool.codekg].<key>`` in pyproject.toml.

    :param repo_root: Repository root directory.
    :param key: Key name under ``[tool.codekg]`` (e.g. ``"include"`` or ``"exclude"``).
    :return: Set of directory names, or an empty set if not found.
    """
    repo_root = Path(repo_root)
    pyproject_path = repo_root / "pyproject.toml"

    if not pyproject_path.exists():
        return set()

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, ValueError):
        # OSError: file read error, ValueError: invalid TOML
        return set()

    value = data.get("tool", {}).get("codekg", {}).get(key, [])
    if isinstance(value, list):
        return {d.rstrip("/") for d in value if isinstance(d, str)}
    return set()


def load_include_dirs(repo_root: Path | str) -> set[str]:
    """
    Load include directory patterns from pyproject.toml.

    Looks for [tool.codekg].include in pyproject.toml at repo_root.
    If not found, returns an empty set (meaning all directories are indexed).

    Example::

        # pyproject.toml
        [tool.codekg]
        include = ["src", "lib"]

    :param repo_root: Repository root directory.
    :return: Set of directory names to include (e.g., {"src", "lib"}).
             An empty set means no filter — all directories are indexed.
    """
    return _load_dir_list(repo_root, "include")


def load_exclude_dirs(repo_root: Path | str) -> set[str]:
    """
    Load exclude directory patterns from pyproject.toml.

    Looks for [tool.codekg].exclude in pyproject.toml at repo_root.
    Excluded directory names are pruned at every level during the file walk,
    just like the built-in ``SKIP_DIRS`` constant.

    Example::

        # pyproject.toml
        [tool.codekg]
        include = ["numpy"]
        exclude = ["tests", "benchmarks"]

    :param repo_root: Repository root directory.
    :return: Set of directory names to exclude (e.g., {"tests", "benchmarks"}).
             An empty set means no extra exclusions beyond ``SKIP_DIRS``.
    """
    return _load_dir_list(repo_root, "exclude")
