"""Tests for orphan-detection exclusions in the thorough-analysis module.

Each exclusion class that keeps a framework-dispatched definition out of the
dead-code list gets a regression test: ``ast.NodeVisitor`` dispatch, SDK
protocol overrides, INHERITS-as-usage, console-script targets, ``__main__``
guards, and property decorators.  The 2026-08-13 analysis run flagged 31
orphans of which ~26 were false positives in exactly these classes.
"""

from types import SimpleNamespace

import pytest

from pycode_kg.pycodekg_thorough_analysis import (
    PyCodeKGAnalyzer,
    _console_script_targets,
    _dotted_module,
    _has_property_decorator,
    _main_guard_block,
    _protocol_attr_names,
)

# ── module-level helpers ─────────────────────────────────────────────────────


def test_dotted_module_strips_src_layout() -> None:
    """src/ layout paths map to their importable dotted form."""
    assert _dotted_module("src/pycode_kg/mcp_server.py") == "pycode_kg.mcp_server"


def test_dotted_module_passes_other_roots_through() -> None:
    """Non-src layouts keep their full path as the dotted form."""
    assert _dotted_module("lib/pkg/mod.py") == "lib.pkg.mod"


def test_protocol_attr_names_cover_the_sdk_interface() -> None:
    """The kg_utils dispatch surface is present, from introspection or fallback."""
    names = _protocol_attr_names()
    assert {"make_extractor", "analyze", "edge_kinds", "node_kinds", "_post_build_hook"} <= names


def test_console_script_targets_parses_project_scripts(tmp_path) -> None:
    """[project.scripts] entries resolve to (dotted_module, function) pairs."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\n\n[project.scripts]\n'
        'x-cli = "x.cli.main:cli"\nx-mcp = "x.mcp_server:main"\n'
    )
    targets = _console_script_targets(tmp_path / "pyproject.toml")
    assert targets == {("x.cli.main", "cli"), ("x.mcp_server", "main")}


def test_console_script_targets_empty_on_missing_file(tmp_path) -> None:
    """A repo without pyproject.toml yields no targets rather than an error."""
    assert _console_script_targets(tmp_path / "pyproject.toml") == set()


def test_main_guard_block_returns_guarded_tail() -> None:
    """Everything from the guard line on is returned for name matching."""
    source = 'def main() -> None: ...\n\n\nif __name__ == "__main__":\n    main()\n'
    block = _main_guard_block(source)
    assert block.startswith("if __name__")
    assert "main()" in block


def test_main_guard_block_empty_without_guard() -> None:
    """Modules without a guard contribute no exclusion text."""
    assert _main_guard_block("def main() -> None: ...\n") == ""


@pytest.mark.parametrize(
    "decorator",
    ["@property", "@cached_property", "@functools.cached_property", "@key.setter"],
)
def test_has_property_decorator_matches_property_family(decorator: str) -> None:
    """property/cached_property/setter decorators mark attribute-style access."""
    lines = ["class C:", f"    {decorator}", "    def key(self):", "        return 1"]
    assert _has_property_decorator(lines, def_lineno=3)


def test_has_property_decorator_ignores_other_decorators() -> None:
    """Unrelated decorators (e.g. @staticmethod) do not trigger the exclusion."""
    lines = ["class C:", "    @staticmethod", "    def key():", "        return 1"]
    assert not _has_property_decorator(lines, def_lineno=3)


# ── _is_special_entry_point ──────────────────────────────────────────────────


@pytest.fixture
def analyzer(tmp_path) -> PyCodeKGAnalyzer:
    """Analyzer wired to a stub KG rooted at tmp_path (no graph needed)."""
    return PyCodeKGAnalyzer(kg=SimpleNamespace(repo_root=str(tmp_path)))


EMPTY_CTX = {
    "class_of": {},
    "external_bases": {},
    "inherited_classes": set(),
    "script_targets": set(),
}


def _node(**kwargs) -> dict:
    node = {"node_id": "", "name": "", "kind": "function", "module_path": "", "lineno": 1}
    node.update(kwargs)
    return node


def test_visit_methods_on_nodevisitor_subclass_are_excluded(analyzer) -> None:
    """ast.NodeVisitor getattr-dispatch produces no CALLS edges — not orphans."""
    ctx = dict(
        EMPTY_CTX,
        class_of={"m:src/p/visitor.py:V.visit_Call": "cls:src/p/visitor.py:V"},
        external_bases={"cls:src/p/visitor.py:V": {"ast.NodeVisitor"}},
    )
    node = _node(
        node_id="m:src/p/visitor.py:V.visit_Call",
        name="visit_Call",
        kind="method",
        module_path="src/p/visitor.py",
    )
    assert analyzer._is_special_entry_point(node, ctx)


def test_visit_prefix_without_nodevisitor_base_is_not_excluded(analyzer) -> None:
    """A visit_* name alone is not enough — the class must derive NodeVisitor."""
    ctx = dict(
        EMPTY_CTX,
        class_of={"m:src/p/x.py:C.visit_Thing": "cls:src/p/x.py:C"},
        external_bases={"cls:src/p/x.py:C": {"SomeBase"}},
    )
    node = _node(
        node_id="m:src/p/x.py:C.visit_Thing",
        name="visit_Thing",
        kind="method",
        module_path="src/p/x.py",
    )
    assert not analyzer._is_special_entry_point(node, ctx)


def test_sdk_protocol_overrides_are_excluded(analyzer) -> None:
    """Overrides of the kg_utils interface on external-base classes are dispatched by the SDK."""
    ctx = dict(
        EMPTY_CTX,
        class_of={"m:src/p/kg.py:KG.make_extractor": "cls:src/p/kg.py:KG"},
        external_bases={"cls:src/p/kg.py:KG": {"_KGModuleBase"}},
    )
    node = _node(
        node_id="m:src/p/kg.py:KG.make_extractor",
        name="make_extractor",
        kind="method",
        module_path="src/p/kg.py",
    )
    assert analyzer._is_special_entry_point(node, ctx)


def test_protocol_name_without_external_base_is_not_excluded(analyzer) -> None:
    """A method merely named like the interface, on a purely internal class, stays a candidate."""
    ctx = dict(
        EMPTY_CTX,
        class_of={"m:src/p/a.py:A.analyze": "cls:src/p/a.py:A"},
    )
    node = _node(
        node_id="m:src/p/a.py:A.analyze", name="analyze", kind="method", module_path="src/p/a.py"
    )
    assert not analyzer._is_special_entry_point(node, ctx)


def test_inherited_class_is_excluded(analyzer) -> None:
    """A class with incoming INHERITS edges is in use even with zero CALLS."""
    ctx = dict(EMPTY_CTX, inherited_classes={"cls:src/p/base.py:Base"})
    node = _node(
        node_id="cls:src/p/base.py:Base", name="Base", kind="class", module_path="src/p/base.py"
    )
    assert analyzer._is_special_entry_point(node, ctx)


def test_console_script_target_is_excluded(analyzer) -> None:
    """[project.scripts] targets are called by generated shims, not repo code."""
    ctx = dict(EMPTY_CTX, script_targets={("p.tool", "main")})
    node = _node(node_id="fn:src/p/tool.py:main", name="main", module_path="src/p/tool.py")
    assert analyzer._is_special_entry_point(node, ctx)


def test_main_guard_function_is_excluded(analyzer, tmp_path) -> None:
    """Functions called under `if __name__ == "__main__"` are entry points."""
    mod = tmp_path / "src" / "p" / "app.py"
    mod.parent.mkdir(parents=True)
    mod.write_text('def main() -> None: ...\n\nif __name__ == "__main__":\n    main()\n')
    node = _node(node_id="fn:src/p/app.py:main", name="main", module_path="src/p/app.py")
    assert analyzer._is_special_entry_point(node, EMPTY_CTX)


def test_plain_module_function_is_not_excluded(analyzer, tmp_path) -> None:
    """An ordinary unguarded function stays an orphan candidate."""
    mod = tmp_path / "src" / "p" / "util.py"
    mod.parent.mkdir(parents=True)
    mod.write_text("def helper() -> None: ...\n")
    node = _node(node_id="fn:src/p/util.py:helper", name="helper", module_path="src/p/util.py")
    assert not analyzer._is_special_entry_point(node, EMPTY_CTX)


def test_property_method_is_excluded(analyzer, tmp_path) -> None:
    """@property methods are accessed as attributes; the graph sees no calls."""
    mod = tmp_path / "src" / "p" / "snap.py"
    mod.parent.mkdir(parents=True)
    mod.write_text("class S:\n    @property\n    def key(self):\n        return 1\n")
    node = _node(
        node_id="m:src/p/snap.py:S.key",
        name="key",
        kind="method",
        module_path="src/p/snap.py",
        lineno=3,
    )
    assert analyzer._is_special_entry_point(node, EMPTY_CTX)


def test_callback_referenced_function_is_excluded(analyzer, tmp_path) -> None:
    """Passing a function by bare name (resolve_kind=_fn) is a reference."""
    mod = tmp_path / "src" / "p" / "html.py"
    mod.parent.mkdir(parents=True)
    mod.write_text("def _resolve_kind(node): ...\n\nSTYLE = dict(resolve_kind=_resolve_kind)\n")
    node = _node(
        node_id="fn:src/p/html.py:_resolve_kind",
        name="_resolve_kind",
        module_path="src/p/html.py",
    )
    assert analyzer._is_special_entry_point(node, EMPTY_CTX)


def test_function_mentioned_only_at_def_site_stays_candidate(analyzer, tmp_path) -> None:
    """A function whose name appears nowhere else in its module stays flagged."""
    mod = tmp_path / "src" / "p" / "legacy.py"
    mod.parent.mkdir(parents=True)
    mod.write_text("def rerank(results): ...\n\ndef other(): ...\n")
    node = _node(node_id="fn:src/p/legacy.py:rerank", name="rerank", module_path="src/p/legacy.py")
    assert not analyzer._is_special_entry_point(node, EMPTY_CTX)


# ── end-to-end against this repo's own graph ─────────────────────────────────


@pytest.mark.integration
def test_repo_orphan_scan_has_no_framework_false_positives() -> None:
    """Run Phase 4 on the live graph: the 2026-08-13 false positives stay out."""
    from pycode_kg.kg import PyCodeKG

    analyzer = PyCodeKGAnalyzer(kg=PyCodeKG("."))
    analyzer._analyze_dependencies()

    dead = {f.name for f in analyzer.orphaned_functions}
    assert not any(n.startswith("visit_") for n in dead)
    assert "KGModule" not in dead
    assert {"make_extractor", "_post_build_hook", "edge_kinds", "main"}.isdisjoint(dead)
    # graph_html passes these as callback values — referenced, not dead
    assert {"_resolve_kind", "_line_range"}.isdisjoint(dead)
    # with_alpha has dedicated tests: prod-orphaned but test-covered, not dead
    tested = {f.name for f in analyzer.test_covered_orphans}
    assert "with_alpha" not in dead
    if "with_alpha" in tested | dead:
        assert "with_alpha" in tested
