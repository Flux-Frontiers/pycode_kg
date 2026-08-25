"""Tests for orphan-detection exclusions in the thorough-analysis module.

Each exclusion class that keeps a framework-dispatched definition out of the
dead-code list gets a regression test: ``ast.NodeVisitor`` dispatch, SDK
protocol overrides, INHERITS-as-usage, console-script targets, ``__main__``
guards, property decorators, and declared exports (``__all__`` / ``__init__.py``
re-exports).  The 2026-08-13 analysis run flagged 31 orphans of which ~26
were false positives in exactly these classes.
"""

import io
from pathlib import Path
from types import SimpleNamespace

import pytest

from pycode_kg.pycodekg_thorough_analysis import (
    PyCodeKGAnalyzer,
    _console_script_targets,
    _counts_table,
    _declared_export_names,
    _dotted_module,
    _format_stat,
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


def test_declared_export_names_collects_all_from_any_module(tmp_path) -> None:
    """__all__ is a declared export wherever it appears, not just __init__.py."""
    mod = tmp_path / "src" / "p" / "core.py"
    mod.parent.mkdir(parents=True)
    mod.write_text('__all__ = ["Widget", "helper"]\n\nclass Widget: ...\ndef helper(): ...\n')
    assert _declared_export_names(tmp_path) == {"Widget", "helper"}


def test_declared_export_names_collects_init_reexports(tmp_path) -> None:
    """from X import Y inside a package __init__.py re-exports Y."""
    pkg = tmp_path / "src" / "p"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("from p.core import Widget, _private\n")
    assert _declared_export_names(tmp_path) == {"Widget"}


def test_declared_export_names_ignores_reexports_outside_init(tmp_path) -> None:
    """The same import in a non-__init__.py module is an ordinary import, not a re-export."""
    mod = tmp_path / "src" / "p" / "user.py"
    mod.parent.mkdir(parents=True)
    mod.write_text("from p.core import Widget\n")
    assert _declared_export_names(tmp_path) == set()


def test_declared_export_names_skips_venv(tmp_path) -> None:
    """.venv is pruned rather than walked -- installed dependencies aren't repo exports."""
    mod = tmp_path / "src" / "p" / "core.py"
    mod.parent.mkdir(parents=True)
    mod.write_text('__all__ = ["Widget"]\n\nclass Widget: ...\n')

    vendored = tmp_path / ".venv" / "lib" / "pkg" / "mod.py"
    vendored.parent.mkdir(parents=True)
    vendored.write_text('__all__ = ["Vendored"]\n\nclass Vendored: ...\n')

    assert _declared_export_names(tmp_path) == {"Widget"}


def test_declared_export_names_tolerates_non_utf8_file(tmp_path) -> None:
    """A file that isn't valid UTF-8 is skipped, not fatal to the whole scan."""
    mod = tmp_path / "src" / "p" / "core.py"
    mod.parent.mkdir(parents=True)
    mod.write_text('__all__ = ["Widget"]\n\nclass Widget: ...\n')

    bogus = tmp_path / "src" / "p" / "bad_encoding.py"
    bogus.write_bytes(b"# -*- coding: big5 -*-\n" + b"\xa4\x40" * 4)

    assert _declared_export_names(tmp_path) == {"Widget"}


def test_tests_corpus_skips_non_utf8_file(tmp_path) -> None:
    """One undecodable test file is skipped; the rest of the corpus survives."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_good.py").write_text("def test_widget(): helper()\n")
    (tests_dir / "test_bad.py").write_bytes(b"# -*- coding: big5 -*-\n" + b"\xa4\x40" * 4)

    analyzer = PyCodeKGAnalyzer(kg=SimpleNamespace(repo_root=str(tmp_path)))
    assert "helper" in analyzer._tests_corpus()


def test_module_source_returns_none_for_non_utf8_file(tmp_path) -> None:
    """An undecodable module reads as None rather than raising."""
    mod = tmp_path / "bad.py"
    mod.write_bytes(b"# -*- coding: big5 -*-\n" + b"\xa4\x40" * 4)

    analyzer = PyCodeKGAnalyzer(kg=SimpleNamespace(repo_root=str(tmp_path)))
    assert analyzer._module_source("bad.py") is None


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
    "exported_names": set(),
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


def test_unverifiable_override_on_external_base_is_flagged(analyzer) -> None:
    """A method on a class with an external base can't be judged — not dead, not confirmed."""
    ctx = dict(
        EMPTY_CTX,
        class_of={"m:src/p/widget.py:W.render": "cls:src/p/widget.py:W"},
        external_bases={"cls:src/p/widget.py:W": {"pyvista.Plotter"}},
    )
    node = _node(
        node_id="m:src/p/widget.py:W.render",
        name="render",
        kind="method",
        module_path="src/p/widget.py",
    )
    assert not analyzer._is_special_entry_point(node, ctx)
    assert analyzer._is_unverifiable_override(node, ctx)


def test_method_on_purely_internal_class_is_not_unverifiable(analyzer) -> None:
    """A class with no external base gives a confident dead/alive answer."""
    ctx = dict(
        EMPTY_CTX,
        class_of={"m:src/p/a.py:A.helper": "cls:src/p/a.py:A"},
    )
    node = _node(
        node_id="m:src/p/a.py:A.helper", name="helper", kind="method", module_path="src/p/a.py"
    )
    assert not analyzer._is_unverifiable_override(node, ctx)


def test_functions_are_never_unverifiable_overrides(analyzer) -> None:
    """Only methods can override a base class; module-level functions can't."""
    node = _node(node_id="fn:src/p/a.py:helper", name="helper", module_path="src/p/a.py")
    assert not analyzer._is_unverifiable_override(node, EMPTY_CTX)


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


def test_exported_class_with_no_callers_is_excluded(analyzer) -> None:
    """A class named in __all__ has zero callers by design — not dead code."""
    ctx = dict(EMPTY_CTX, exported_names={"Widget"})
    node = _node(
        node_id="cls:src/p/core.py:Widget", name="Widget", kind="class", module_path="src/p/core.py"
    )
    assert analyzer._is_special_entry_point(node, ctx)


def test_reexported_function_with_no_callers_is_excluded(analyzer) -> None:
    """A function re-exported by a package __init__.py is a declared export."""
    ctx = dict(EMPTY_CTX, exported_names={"helper"})
    node = _node(node_id="fn:src/p/core.py:helper", name="helper", module_path="src/p/core.py")
    assert analyzer._is_special_entry_point(node, ctx)


def test_undeclared_name_is_not_excluded_by_exports(analyzer) -> None:
    """A name absent from every __all__ and every __init__.py stays a candidate."""
    ctx = dict(EMPTY_CTX, exported_names={"Widget"})
    node = _node(node_id="fn:src/p/core.py:other", name="other", module_path="src/p/core.py")
    assert not analyzer._is_special_entry_point(node, ctx)


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


# ── console summary formatting ───────────────────────────────────────────────


def test_format_stat_renders_coverage_as_percentage() -> None:
    """A 0-1 coverage ratio reads as a percentage, not a bare float."""
    assert _format_stat("docstring_coverage", 0.935) == "93.5%"


def test_format_stat_groups_large_counts() -> None:
    """Node/edge totals get thousands separators."""
    assert _format_stat("total_nodes", 6904) == "6,904"


def test_format_stat_passes_strings_through() -> None:
    """Non-numeric metrics are untouched."""
    assert _format_stat("vector_backend", "sqlite-vec") == "sqlite-vec"


def test_counts_table_orders_by_count_descending() -> None:
    """The breakdown leads with the largest bucket."""
    from rich.console import Console as _Console

    table = _counts_table("Nodes by Kind", "Kind", {"class": 32, "symbol": 6491, "module": 56})
    console = _Console(file=io.StringIO(), width=80)
    console.print(table)
    rendered = console.file.getvalue()

    assert "6,491" in rendered
    assert rendered.index("symbol") < rendered.index("module") < rendered.index("class")


def test_print_summary_has_no_raw_dict_reprs(capsys) -> None:
    """node_counts/edge_counts render as tables, not Python dict reprs.

    The raw ``str(dict)`` dump wrapped across the value column and buried
    the numbers in quotes and braces.
    """
    analyzer = PyCodeKGAnalyzer(kg=SimpleNamespace(repo_root=""))
    analyzer.stats = {
        "db_path": "/tmp/graph.sqlite",
        "total_nodes": 6904,
        "total_edges": 6443,
        "docstring_coverage": 0.935,
        "node_counts": {"symbol": 6491, "class": 32},
        "edge_counts": {"CALLS": 2430, "INHERITS": 11},
        "class_count": 32,
    }
    analyzer.print_summary()
    out = capsys.readouterr().out

    assert "{'" not in out
    assert "Nodes by Kind" in out and "Edges by Relation" in out
    assert "6,491" in out and "2,430" in out
    assert "93.5%" in out


def test_print_summary_shows_unrecognized_stats(capsys) -> None:
    """A stat key with no label still appears rather than vanishing."""
    analyzer = PyCodeKGAnalyzer(kg=SimpleNamespace(repo_root=""))
    analyzer.stats = {"total_nodes": 5, "some_future_metric": 42}
    analyzer.print_summary()
    out = capsys.readouterr().out
    assert "some_future_metric" in out and "42" in out


# ── internal fan-out counting ────────────────────────────────────────────────


def _edges_kg(edges: list[tuple[str, str, str]]):
    """Stub KG exposing a real in-memory edges table."""
    import sqlite3

    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE edges (src TEXT, dst TEXT, rel TEXT)")
    con.executemany("INSERT INTO edges VALUES (?, ?, ?)", edges)
    return SimpleNamespace(store=SimpleNamespace(con=con), repo_root="")


def test_internal_fan_out_counts_repo_callees_only() -> None:
    """click.echo / path.exists / dict.get syms do not count as orchestration."""
    kg = _edges_kg(
        [
            ("fn:a.py:init", "fn:a.py:_step_one", "CALLS"),  # direct internal
            ("fn:a.py:init", "sym:click.echo", "CALLS"),  # external, unresolved
            ("fn:a.py:init", "sym:hook_path.exists", "CALLS"),  # external, unresolved
            ("fn:a.py:init", "sym:helper", "CALLS"),  # resolves internally
            ("sym:helper", "fn:b.py:helper", "RESOLVES_TO"),
            ("fn:a.py:init", "sym:visited.update", "CALLS"),  # builtin lookalike
            ("sym:visited.update", "fn:c.py:update", "RESOLVES_TO"),  # bad edge
        ]
    )
    analyzer = PyCodeKGAnalyzer(kg=kg)
    counts = analyzer._internal_fan_out_counts()
    # _step_one + resolved helper; echo/exists external, visited.update skipped
    assert counts["fn:a.py:init"] == 2


def test_internal_fan_out_deduplicates_targets() -> None:
    """Calling the same internal function five times is fan-out 1."""
    kg = _edges_kg([("fn:a.py:f", "fn:a.py:g", "CALLS")] * 5)
    analyzer = PyCodeKGAnalyzer(kg=kg)
    assert analyzer._internal_fan_out_counts()["fn:a.py:f"] == 1


# ── end-to-end against this repo's own graph ─────────────────────────────────


@pytest.mark.skipif(
    not Path(".pycodekg/graph.sqlite").exists(),
    reason="needs this repo's own graph; .pycodekg/*.sqlite is gitignored",
)
def test_repo_orphan_scan_has_no_framework_false_positives() -> None:
    """Run Phase 4 on the live graph: the 2026-08-13 false positives stay out.

    Conditional rather than marked ``integration``: the marker deselected this
    everywhere, including on a machine that *has* a graph.  A skipif states the
    actual precondition, so it runs whenever one is present and reports why when
    it is not.  Making it run in CI as well would mean building the graph there
    first — worth doing, but it is a CI-runtime decision, not a test one.
    """
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
