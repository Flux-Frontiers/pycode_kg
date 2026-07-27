"""
test_mcp_cold_start.py

Regression tests for MCP tools called first in a fresh server session.

``KGModule.store`` is a lazy property: ``_store`` stays ``None`` until the
property is first read.  Tools that reached for the private ``_store`` field
instead saw ``None`` and bailed out with "No database store available", so
whichever tool an agent happened to call first would fail.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pycode_kg.mcp_server as mcp_server
from pycode_kg.kg import PyCodeKG

SAMPLE = {
    "pkg/__init__.py": "",
    "pkg/core.py": """
        class Widget:
            def spin(self):
                return helper()

        def helper():
            return 42
    """,
}


def _cold_kg(tmp_path: Path) -> PyCodeKG:
    """
    Build a graph, then hand back a *fresh* handle whose store is untouched.

    :param tmp_path: pytest temp directory.
    :return: A PyCodeKG whose ``_store`` is still ``None``.
    """
    repo = tmp_path / "repo"
    for rel, src in SAMPLE.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))

    db = tmp_path / "pycodekg.sqlite"
    vectors = tmp_path / "vectors.sqlite"
    PyCodeKG(repo_root=repo, db_path=db, vectors_path=vectors).build_graph(wipe=True)

    # A new handle over the same DB — as a fresh server process would have.
    return PyCodeKG(repo_root=repo, db_path=db, vectors_path=vectors)


def _call(tool, **kwargs):
    """Invoke an MCP tool, unwrapping the FastMCP decorator if present."""
    return getattr(tool, "fn", tool)(**kwargs)


def test_list_nodes_works_on_cold_session(tmp_path, monkeypatch):
    kg = _cold_kg(tmp_path)
    assert kg._store is None, "precondition: store must be uninitialised"
    monkeypatch.setattr(mcp_server, "_kg", kg)

    payload = json.loads(_call(mcp_server.list_nodes, kind="class"))

    assert not (isinstance(payload, dict) and "error" in payload), payload
    assert any(n["name"] == "Widget" for n in payload)


def test_find_node_works_on_cold_session(tmp_path, monkeypatch):
    kg = _cold_kg(tmp_path)
    assert kg._store is None
    monkeypatch.setattr(mcp_server, "_kg", kg)

    payload = json.loads(_call(mcp_server.find_node, name="helper"))

    assert not (isinstance(payload, dict) and "error" in payload), payload
    assert any(n["name"] == "helper" for n in payload)


def test_store_property_initialises_on_first_access(tmp_path):
    kg = _cold_kg(tmp_path)
    assert kg._store is None
    assert kg.store is not None
    assert kg._store is not None
