"""
test_graph.py

Tests for CodeGraph — pure AST extraction class.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from code_kg.graph import CodeGraph


def _write_repo(tmp_path: Path, files: dict) -> Path:
    for rel, src in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))
    return tmp_path


# ---------------------------------------------------------------------------
# Basic construction
# ---------------------------------------------------------------------------


def test_codegraph_repr_before_extract(tmp_path):
    g = CodeGraph(tmp_path)
    assert "not yet extracted" in repr(g)


def test_codegraph_repr_after_extract(tmp_path):
    _write_repo(tmp_path, {"mod.py": "x = 1\n"})
    g = CodeGraph(tmp_path)
    g.extract()
    assert "nodes=" in repr(g)
    assert "edges=" in repr(g)


def test_codegraph_resolves_repo_root(tmp_path):
    g = CodeGraph(str(tmp_path))  # string input
    assert g.repo_root == tmp_path.resolve()


# ---------------------------------------------------------------------------
# extract() — lazy and cached
# ---------------------------------------------------------------------------


def test_codegraph_extract_returns_self(tmp_path):
    g = CodeGraph(tmp_path)
    result = g.extract()
    assert result is g


def test_codegraph_nodes_triggers_extract(tmp_path):
    _write_repo(tmp_path, {"mod.py": "def foo(): pass\n"})
    g = CodeGraph(tmp_path)
    # Access .nodes without calling extract() first
    assert len(g.nodes) > 0


def test_codegraph_edges_triggers_extract(tmp_path):
    _write_repo(tmp_path, {"mod.py": "def foo(): pass\n"})
    g = CodeGraph(tmp_path)
    assert len(g.edges) > 0


def test_codegraph_extract_cached(tmp_path):
    _write_repo(tmp_path, {"mod.py": "def foo(): pass\n"})
    g = CodeGraph(tmp_path)
    g.extract()
    nodes_first = g.nodes
    g.extract()  # second call — should use cache
    assert g.nodes is nodes_first


def test_codegraph_extract_force_reruns(tmp_path):
    _write_repo(tmp_path, {"mod.py": "def foo(): pass\n"})
    g = CodeGraph(tmp_path)
    g.extract()
    nodes_first = g.nodes
    g.extract(force=True)
    # New list object (re-extracted), but same content
    assert {n.id for n in g.nodes} == {n.id for n in nodes_first}


# ---------------------------------------------------------------------------
# result()
# ---------------------------------------------------------------------------


def test_codegraph_result_returns_tuple(tmp_path):
    _write_repo(tmp_path, {"mod.py": "class A: pass\n"})
    g = CodeGraph(tmp_path)
    nodes, edges = g.result()
    assert isinstance(nodes, list)
    assert isinstance(edges, list)
    assert any(n.kind == "class" for n in nodes)


# ---------------------------------------------------------------------------
# stats()
# ---------------------------------------------------------------------------


def test_codegraph_stats_keys(tmp_path):
    _write_repo(
        tmp_path,
        {"mod.py": "class Foo:\n    def run(self): pass\ndef bar(): pass\n"},
    )
    g = CodeGraph(tmp_path)
    s = g.stats()
    assert "total_nodes" in s
    assert "total_edges" in s
    assert "node_counts" in s
    assert "edge_counts" in s
    assert s["node_counts"]["class"] == 1
    assert s["node_counts"]["function"] == 1
    assert s["node_counts"]["method"] == 1


def test_codegraph_stats_repo_root(tmp_path):
    g = CodeGraph(tmp_path)
    g.extract()
    assert g.stats()["repo_root"] == str(tmp_path.resolve())


# ---------------------------------------------------------------------------
# Empty repo
# ---------------------------------------------------------------------------


def test_codegraph_empty_repo(tmp_path):
    g = CodeGraph(tmp_path)
    assert g.nodes == []
    assert g.edges == []
    s = g.stats()
    assert s["total_nodes"] == 0
    assert s["total_edges"] == 0
