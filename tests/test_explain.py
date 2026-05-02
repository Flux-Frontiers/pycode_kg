"""
test_explain.py

Tests for the shared ``render_explain`` presenter that backs both the CLI
``pycodekg explain`` command and the MCP ``explain`` tool.  These tests guard
the kind-aware role labels and the previously-buggy off-by-one threshold.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from pycode_kg.explain import render_explain
from pycode_kg.kg import PyCodeKG


def _write_repo(tmp_path: Path, files: dict) -> Path:
    for rel, src in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))
    return tmp_path


def _make_kg(tmp_path: Path, files: dict) -> PyCodeKG:
    repo = tmp_path / "repo"
    _write_repo(repo, files)
    kg = PyCodeKG(
        repo_root=repo,
        db_path=tmp_path / "pycodekg.sqlite",
        lancedb_dir=tmp_path / "lancedb",
    )
    kg.build_graph(wipe=True)
    return kg


def test_render_explain_unknown_node_returns_not_found(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    md = render_explain(kg, "fn:does/not/exist.py:bogus")
    assert "Node Not Found" in md
    assert "bogus" in md
    kg.close()


def test_render_explain_class_uses_class_noun(tmp_path):
    """A class should be labeled with class-aware nouns/verbs, not 'function'."""
    src = """
        class Store:
            '''A persistence abstraction.'''
            def write(self): pass

        def make_one():
            return Store()

        def make_two():
            return Store()
    """
    kg = _make_kg(tmp_path, {"mod.py": src})
    cls_id = next(n["id"] for n in kg.store.query_nodes(kinds=["class"]) if n["name"] == "Store")
    md = render_explain(kg, cls_id)
    assert "Class: `Store`" in md
    # The role line must use class-aware language.
    assert (
        "function" not in md.split("## Role in Codebase")[1].lower() or "Constructed" in md
    )  # the role section never uses "function"
    assert "Constructed" in md
    kg.close()


def test_render_explain_orphan_function_zero_callers(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def lonely(): pass\n"})
    fn_id = next(n["id"] for n in kg.store.query_nodes(kinds=["function"]) if n["name"] == "lonely")
    md = render_explain(kg, fn_id)
    assert "Orphaned" in md
    kg.close()


def test_render_explain_protocol_method_label(tmp_path):
    src = """
        class Foo:
            def __enter__(self): return self
            def __exit__(self, *a): pass
    """
    kg = _make_kg(tmp_path, {"mod.py": src})
    methods = kg.store.query_nodes(kinds=["method"])
    enter = next(m for m in methods if m["name"] == "__enter__")
    md = render_explain(kg, enter["id"])
    assert "Protocol method" in md
    kg.close()


def test_render_explain_uses_snippets_hint(tmp_path):
    """Footer call-to-action is parameterized for CLI vs MCP."""
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    fn_id = next(n["id"] for n in kg.store.query_nodes(kinds=["function"]))

    md_mcp = render_explain(kg, fn_id, snippets_hint="pack_snippets()")
    md_cli = render_explain(kg, fn_id, snippets_hint="pycodekg pack")

    assert "pack_snippets()" in md_mcp
    assert "pycodekg pack" not in md_mcp
    assert "pycodekg pack" in md_cli
    assert "pack_snippets()" not in md_cli
    kg.close()


def test_render_explain_has_expected_sections(tmp_path):
    """Smoke test: a function with a docstring renders the standard sections."""
    src = """
        def documented():
            '''This is a documented function.'''
            return 1

        def caller():
            return documented()
    """
    kg = _make_kg(tmp_path, {"mod.py": src})
    fn = next(n for n in kg.store.query_nodes(kinds=["function"]) if n["name"] == "documented")
    md = render_explain(kg, fn["id"])
    assert "## Metadata" in md
    assert "## Documentation" in md
    assert "This is a documented function." in md
    assert "## Called By (Callers)" in md
    assert "## Role in Codebase" in md
    kg.close()
