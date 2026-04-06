"""
utils.py

Shared primitive utilities used by both codekg.py and visitor.py.
Kept in a separate module to avoid circular imports.
"""

from __future__ import annotations

from pathlib import Path


def rel_module_path(path: Path, repo_root: Path) -> str:
    """Convert file path to repo-relative module path.

    :param path: Absolute file path
    :param repo_root: Repo root
    """
    return str(path.relative_to(repo_root)).replace("\\", "/")


def node_id(kind: str, module: str, qualname: str | None) -> str:
    """Construct stable node id.

    :param kind: Node kind
    :param module: Repo-relative module path
    :param qualname: Qualified name
    """
    if kind == "module":
        return f"mod:{module}"

    prefix = {
        "class": "cls",
        "function": "fn",
        "method": "m",
        "symbol": "sym",
    }[kind]

    return f"{prefix}:{module}:{qualname}" if qualname else f"{prefix}:{module}"
