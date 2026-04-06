"""
test_visitor.py

Tests for CodeKGVisitor — scope tracking and argument handling.
"""

from __future__ import annotations

import ast

from code_kg.visitor import CodeKGVisitor


def _visit(src: str, module_id: str = "mod") -> CodeKGVisitor:
    """Parse *src*, run the visitor, and return it for inspection."""
    tree = ast.parse(src)
    vis = CodeKGVisitor(module_id=module_id, file_path="mod.py")
    vis.visit(tree)
    return vis


def _scope(vis: CodeKGVisitor, name: str) -> set[str]:
    """Return ``vars_in_scope`` for the first scope whose key contains *name*."""
    for key, vars_ in vis.vars_in_scope.items():
        if name in key:
            return vars_
    raise KeyError(f"No scope containing {name!r}")


# ---------------------------------------------------------------------------
# _seed_params — positional and variadic args
# ---------------------------------------------------------------------------


def test_seed_positional_args():
    vis = _visit("def f(a, b, c): pass")
    assert {"a", "b", "c"} <= _scope(vis, "f")


def test_seed_vararg_and_kwarg():
    vis = _visit("def f(*args, **kwargs): pass")
    scope = _scope(vis, "f")
    assert "args" in scope
    assert "kwargs" in scope


def test_seed_posonly_args():
    vis = _visit("def f(a, b, /, c): pass")
    scope = _scope(vis, "f")
    assert {"a", "b", "c"} <= scope


def test_seed_kwonly_args():
    vis = _visit("def f(*, x, y): pass")
    scope = _scope(vis, "f")
    assert {"x", "y"} <= scope


def test_seed_kwonly_some_with_defaults():
    # kw_defaults has None for keyword-only args that have no default
    vis = _visit("def f(*, x, y=1): pass")
    scope = _scope(vis, "f")
    assert {"x", "y"} <= scope


def test_seed_all_arg_kinds_together():
    vis = _visit("def f(a, b=1, /, c=2, *args, d, e=3, **kwargs): pass")
    scope = _scope(vis, "f")
    assert {"a", "b", "c", "args", "d", "e", "kwargs"} <= scope


# ---------------------------------------------------------------------------
# Method self seeded correctly
# ---------------------------------------------------------------------------


def test_seed_self_in_method():
    vis = _visit(
        """\
class MyClass:
    def method(self, x):
        pass
"""
    )
    scope = _scope(vis, "method")
    assert "self" in scope
    assert "x" in scope


# ---------------------------------------------------------------------------
# async def handled identically to def
# ---------------------------------------------------------------------------


def test_async_funcdef_seeds_params():
    vis = _visit("async def fetch(url, *, timeout=30): pass")
    scope = _scope(vis, "fetch")
    assert {"url", "timeout"} <= scope


def test_async_funcdef_variadics():
    vis = _visit("async def f(*args, **kwargs): pass")
    scope = _scope(vis, "f")
    assert {"args", "kwargs"} <= scope


# ---------------------------------------------------------------------------
# Default expressions attributed to enclosing scope, not the function
# ---------------------------------------------------------------------------


def test_default_not_in_function_scope():
    # DEFAULT_VAL is used as a default — it should NOT appear in f's scope
    # (it's a read in the module scope, not a local var of f).
    vis = _visit(
        """\
DEFAULT_VAL = 10
def f(x=DEFAULT_VAL):
    pass
"""
    )
    scope = _scope(vis, "f")
    # x is a parameter and should be in scope; DEFAULT_VAL should not be
    assert "x" in scope
    assert "DEFAULT_VAL" not in scope


def test_kwonly_default_not_in_function_scope():
    vis = _visit(
        """\
SENTINEL = object()
def f(*, key=SENTINEL):
    pass
"""
    )
    scope = _scope(vis, "f")
    assert "key" in scope
    assert "SENTINEL" not in scope


# ---------------------------------------------------------------------------
# Body locals still tracked alongside params
# ---------------------------------------------------------------------------


def test_body_assignment_added_to_scope():
    vis = _visit(
        """\
def f(x):
    y = x + 1
    return y
"""
    )
    scope = _scope(vis, "f")
    assert "x" in scope  # param
    assert "y" in scope  # body assignment
