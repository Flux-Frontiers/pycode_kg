"""
test_primitives.py

Tests for the locked v0 primitives in codekg.py:
  Node, Edge, node_id, rel_module_path, expr_to_name, iter_python_files, extract_repo
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

from code_kg.codekg import (
    Edge,
    Node,
    expr_to_name,
    extract_repo,
    iter_python_files,
    node_id,
    rel_module_path,
)

# ---------------------------------------------------------------------------
# node_id
# ---------------------------------------------------------------------------


def test_node_id_module():
    assert node_id("module", "pkg/util.py", None) == "mod:pkg/util.py"


def test_node_id_class():
    assert node_id("class", "pkg/util.py", "MyClass") == "cls:pkg/util.py:MyClass"


def test_node_id_function():
    assert node_id("function", "pkg/util.py", "parse") == "fn:pkg/util.py:parse"


def test_node_id_method():
    assert node_id("method", "pkg/util.py", "MyClass.run") == "m:pkg/util.py:MyClass.run"


def test_node_id_symbol():
    assert node_id("symbol", "pkg/util.py", "os") == "sym:pkg/util.py:os"


def test_node_id_unknown_kind_raises():
    with pytest.raises(KeyError):
        node_id("unknown", "pkg/util.py", "foo")


# ---------------------------------------------------------------------------
# rel_module_path
# ---------------------------------------------------------------------------


def test_rel_module_path(tmp_path):
    f = tmp_path / "sub" / "mod.py"
    f.parent.mkdir()
    f.touch()
    assert rel_module_path(f, tmp_path) == "sub/mod.py"


def test_rel_module_path_top_level(tmp_path):
    f = tmp_path / "mod.py"
    f.touch()
    assert rel_module_path(f, tmp_path) == "mod.py"


# ---------------------------------------------------------------------------
# expr_to_name
# ---------------------------------------------------------------------------


def _parse_expr(code: str) -> ast.AST:
    return ast.parse(code, mode="eval").body


def test_expr_to_name_simple_name():
    assert expr_to_name(_parse_expr("foo")) == "foo"


def test_expr_to_name_attribute():
    assert expr_to_name(_parse_expr("os.path")) == "os.path"


def test_expr_to_name_nested_attribute():
    assert expr_to_name(_parse_expr("os.path.join")) == "os.path.join"


def test_expr_to_name_call():
    assert expr_to_name(_parse_expr("foo()")) == "foo"


def test_expr_to_name_subscript():
    assert expr_to_name(_parse_expr("d[key]")) == "d"


def test_expr_to_name_unknown_returns_none():
    assert expr_to_name(_parse_expr("42")) is None


# ---------------------------------------------------------------------------
# iter_python_files
# ---------------------------------------------------------------------------


def test_iter_python_files_finds_py(tmp_path):
    (tmp_path / "a.py").write_text("x = 1")
    found = list(iter_python_files(tmp_path))
    assert tmp_path / "a.py" in found


def test_iter_python_files_ignores_non_py(tmp_path):
    (tmp_path / "b.txt").write_text("not python")
    found = list(iter_python_files(tmp_path))
    assert not found


def test_iter_python_files_recurses(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.py").write_text("y = 2")
    found = list(iter_python_files(tmp_path))
    assert sub / "c.py" in found


def test_iter_python_files_skips_venv(tmp_path):
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "hidden.py").write_text("z = 3")
    found = list(iter_python_files(tmp_path))
    assert venv / "hidden.py" not in found


def test_iter_python_files_skips_pycache(tmp_path):
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "cached.py").write_text("pass")
    found = list(iter_python_files(tmp_path))
    assert cache / "cached.py" not in found


# ---------------------------------------------------------------------------
# extract_repo — integration tests against synthetic repos
# ---------------------------------------------------------------------------


def _write_repo(tmp_path: Path, files: dict) -> Path:
    for rel, src in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))
    return tmp_path


def test_extract_repo_empty(tmp_path):
    nodes, edges = extract_repo(tmp_path)
    assert nodes == []
    assert edges == []


def test_extract_repo_module_node(tmp_path):
    _write_repo(tmp_path, {"pkg/util.py": '"""A module."""\n'})
    nodes, _ = extract_repo(tmp_path)
    mod_nodes = [n for n in nodes if n.kind == "module"]
    assert any(n.module_path == "pkg/util.py" for n in mod_nodes)


def test_extract_repo_module_docstring(tmp_path):
    _write_repo(tmp_path, {"mod.py": '"""My docstring."""\n'})
    nodes, _ = extract_repo(tmp_path)
    mod = next(n for n in nodes if n.kind == "module")
    assert mod.docstring == "My docstring."


def test_extract_repo_function_node(tmp_path):
    _write_repo(tmp_path, {"mod.py": "def hello():\n    pass\n"})
    nodes, _ = extract_repo(tmp_path)
    fn_nodes = [n for n in nodes if n.kind == "function"]
    assert any(n.name == "hello" for n in fn_nodes)


def test_extract_repo_function_contains_edge(tmp_path):
    _write_repo(tmp_path, {"mod.py": "def hello():\n    pass\n"})
    _, edges = extract_repo(tmp_path)
    contains = [e for e in edges if e.rel == "CONTAINS"]
    assert any("hello" in e.dst for e in contains)


def test_extract_repo_class_node(tmp_path):
    _write_repo(tmp_path, {"mod.py": "class Foo:\n    pass\n"})
    nodes, _ = extract_repo(tmp_path)
    cls_nodes = [n for n in nodes if n.kind == "class"]
    assert any(n.name == "Foo" for n in cls_nodes)


def test_extract_repo_method_node(tmp_path):
    _write_repo(tmp_path, {"mod.py": "class Foo:\n    def bar(self):\n        pass\n"})
    nodes, _ = extract_repo(tmp_path)
    meth_nodes = [n for n in nodes if n.kind == "method"]
    assert any(n.name == "bar" for n in meth_nodes)


def test_extract_repo_class_contains_method_edge(tmp_path):
    _write_repo(tmp_path, {"mod.py": "class Foo:\n    def bar(self):\n        pass\n"})
    _, edges = extract_repo(tmp_path)
    contains = [e for e in edges if e.rel == "CONTAINS"]
    assert any(e.dst.endswith("Foo.bar") for e in contains)


def test_extract_repo_inheritance(tmp_path):
    _write_repo(tmp_path, {"mod.py": "class Child(Base):\n    pass\n"})
    _, edges = extract_repo(tmp_path)
    inherits = [e for e in edges if e.rel == "INHERITS"]
    assert any("Base" in e.dst for e in inherits)


def test_extract_repo_import(tmp_path):
    _write_repo(tmp_path, {"mod.py": "import os\n"})
    _, edges = extract_repo(tmp_path)
    imports = {e.dst for e in edges if e.rel == "IMPORTS"}
    assert "sym:os" in imports


def test_extract_repo_import_from(tmp_path):
    _write_repo(tmp_path, {"mod.py": "from pathlib import Path\n"})
    _, edges = extract_repo(tmp_path)
    imports = {e.dst for e in edges if e.rel == "IMPORTS"}
    assert "sym:pathlib.Path" in imports


def test_extract_repo_call_graph(tmp_path):
    _write_repo(
        tmp_path,
        {"mod.py": ("def helper():\n    pass\ndef main():\n    helper()\n")},
    )
    _, edges = extract_repo(tmp_path)
    calls = [e for e in edges if e.rel == "CALLS"]
    assert any("helper" in e.dst for e in calls)


def test_extract_repo_skips_syntax_error(tmp_path):
    _write_repo(
        tmp_path,
        {
            "bad.py": "def (\n",  # SyntaxError
            "good.py": "x = 1\n",
        },
    )
    nodes, _ = extract_repo(tmp_path)
    assert any(n.kind == "module" and "good.py" in (n.module_path or "") for n in nodes)
    assert not any(n.kind == "module" and "bad.py" in (n.module_path or "") for n in nodes)


def test_extract_repo_no_duplicate_edges(tmp_path):
    _write_repo(tmp_path, {"mod.py": "import os\nimport os\n"})
    _, edges = extract_repo(tmp_path)
    import_edges = [e for e in edges if e.rel == "IMPORTS" and e.dst == "sym:os"]
    assert len(import_edges) == 1


def test_extract_repo_deterministic(tmp_path):
    """Same input → same output (node/edge counts and IDs)."""
    _write_repo(
        tmp_path,
        {"mod.py": ("class Foo:\n    def run(self): pass\ndef bar(): pass\n")},
    )
    nodes1, edges1 = extract_repo(tmp_path)
    nodes2, edges2 = extract_repo(tmp_path)
    assert {n.id for n in nodes1} == {n.id for n in nodes2}
    assert {(e.src, e.rel, e.dst) for e in edges1} == {(e.src, e.rel, e.dst) for e in edges2}


# ---------------------------------------------------------------------------
# Node / Edge dataclasses
# ---------------------------------------------------------------------------


def test_node_is_frozen():
    n = Node("mod:x.py", "module", "x", None, "x.py", 1, 10, None)
    with pytest.raises(Exception):
        n.kind = "function"  # type: ignore[misc]


def test_edge_evidence_defaults_none():
    e = Edge("a", "CALLS", "b")
    assert e.evidence is None


def test_edge_with_evidence():
    e = Edge("a", "CALLS", "b", {"lineno": 5})
    assert e.evidence == {"lineno": 5}


def test_node_fields():
    n = Node(
        id="fn:mod.py:foo",
        kind="function",
        name="foo",
        qualname="foo",
        module_path="mod.py",
        lineno=10,
        end_lineno=20,
        docstring="Does foo.",
    )
    assert n.id == "fn:mod.py:foo"
    assert n.kind == "function"
    assert n.lineno == 10
    assert n.docstring == "Does foo."
