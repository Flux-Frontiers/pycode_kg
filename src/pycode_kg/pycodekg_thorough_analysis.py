#!/usr/bin/env python3
"""
PyCodeKG Thorough Repository Analysis Tool

Performs comprehensive architectural analysis of Python repositories using PyCodeKG's
graph traversal capabilities. Analyzes:
- Complexity hotspots (highest fan-in/fan-out functions)
- Architectural patterns (core modules, integration points)
- Dependency analysis (circular deps, tight coupling)
- Code quality signals (dead code, orphaned functions)

Operational behavior:
- Entry point and configuration defaults: resolves ``repo_root`` and defaults
    ``db_path``/``vectors_path`` to ``.pycodekg/graph.sqlite`` and
    ``.pycodekg/vectors.sqlite``.
- Logging approach: uses Rich console output for user-facing status and
    standard ``logging`` for non-fatal diagnostic warnings.
- Error handling strategy: degrades gracefully when optional data is missing
    (for example missing database, git metadata, or snapshot history) and emits
    actionable warnings instead of failing hard where possible.

Usage:
    python pycodekg_thorough_analysis.py /path/to/repo /path/to/db .pycodekg/vectors.sqlite

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

import datetime
import importlib
import inspect
import json
import logging
import os
import platform
import re
import subprocess
import time
import tomllib
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pycode_kg.report import render_markdown
from pycode_kg.resolution import BUILTIN_METHOD_NAMES
from pycode_kg.snapshots import SnapshotManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FunctionMetrics:
    """Metrics for a single function or class.

    :param node_id: Stable node identifier
    :param name: Function/class name
    :param module: Module path containing this definition
    :param kind: Kind of node (function, method, class)
    :param fan_in: Count of callers (how many call this)
    :param fan_out: Count of callees (how many this calls)
    :param lines: Approximate line count
    :param docstring: Docstring text if available
    :param risk_level: Risk assessment (low, medium, high, critical)
    """

    node_id: str
    name: str
    module: str
    kind: str
    fan_in: int
    fan_out: int
    lines: int
    docstring: str | None = None


@dataclass
class ModuleMetrics:
    """Metrics for a module.

    :param path: Module file path
    :param functions: Count of functions defined
    :param classes: Count of classes defined
    :param methods: Count of methods defined
    :param incoming_deps: Modules that import this one
    :param outgoing_deps: Modules this one imports
    :param total_fan_in: Sum of all callers to functions in module
    :param cohesion_score: Internal coupling strength (0-1)
    """

    path: str
    functions: int
    classes: int
    methods: int
    incoming_deps: list[str]
    outgoing_deps: list[str]
    total_fan_in: int
    cohesion_score: float


@dataclass
class CallChain:
    """Represents a notable call chain.

    :param chain: List of function names in call order
    :param depth: Length of the chain
    :param total_callers: Sum of all callers in chain
    """

    chain: list[str]
    depth: int
    total_callers: int


# ── Orphan-detection exclusion helpers ───────────────────────────────────────
#
# The exhaustive orphan scan (Phase 4) sees only edges inside the indexed
# repo, so anything invoked by an external framework — ast.NodeVisitor
# dispatch, the kg_utils pipeline, console scripts, a __main__ guard — has
# zero visible callers.  These helpers identify those populations statically;
# none of them import code from the *target* repo (the analyzer runs against
# arbitrary repositories, so importing their modules would execute arbitrary
# code and usually fail on missing dependencies anyway).

_PROPERTY_DECORATOR_RE = re.compile(
    r"@(?:functools\.)?(?:cached_)?property\b|@\w[\w.]*\.(?:setter|getter|deleter)\b"
)

# Builtin container/str method names live in pycode_kg.resolution, where the
# post-build hook prunes their bogus RESOLVES_TO edges at the source.  The
# analyzer still guards its own reads (chain tracing, fan-out) so it stays
# accurate on graphs built by older versions that never ran the prune.
_BUILTIN_METHOD_NAMES = BUILTIN_METHOD_NAMES
_MAIN_GUARD_RE = re.compile(r"^if\s+__name__\s*==\s*[\"']__main__[\"']\s*:", re.MULTILINE)

# Fallback if kg_utils is not importable in the analyzer's own environment.
_PROTOCOL_ATTRS_FALLBACK = frozenset(
    {
        "analyze",
        "build",
        "coverage_metric",
        "edge_kinds",
        "extract",
        "kind",
        "make_extractor",
        "meaningful_node_kinds",
        "node_kinds",
        "pack",
        "query",
        "stats",
        "_post_build_hook",
    }
)
_protocol_attrs_cache: frozenset[str] | None = None


def _protocol_attr_names() -> frozenset[str]:
    """Attribute names of the framework base classes the KG SDK dispatches on.

    A method overriding one of these on a class with an external base is
    invoked by the framework (``kg_utils`` pipeline/extractor machinery), not
    by in-repo call sites, so it must not be flagged as an orphan.  The names
    are introspected from the analyzer's *own* installed ``kg_utils`` — never
    from the target repo — and fall back to a static list if unavailable.

    :return: Frozen set of non-dunder attribute names across the SDK bases.
    """
    global _protocol_attrs_cache
    if _protocol_attrs_cache is not None:
        return _protocol_attrs_cache

    names: set[str] = set(_PROTOCOL_ATTRS_FALLBACK)
    for module_name in ("kg_utils.module", "kg_utils.extractor", "kg_utils.pipeline"):
        try:
            mod = importlib.import_module(module_name)
        except ImportError:  # pragma: no cover - kg_utils is a hard dependency
            continue
        for _, cls in inspect.getmembers(mod, inspect.isclass):
            if cls.__module__.startswith("kg_utils"):
                names.update(n for n in vars(cls) if not n.startswith("__"))
    _protocol_attrs_cache = frozenset(names)
    return _protocol_attrs_cache


def _console_script_targets(pyproject_path: Path) -> set[tuple[str, str]]:
    """Parse ``[project.scripts]`` into ``(dotted_module, function)`` pairs.

    Console-script targets are invoked by the generated entry-point shims, so
    they have zero in-repo callers by design.

    :param pyproject_path: Path to the target repo's ``pyproject.toml``.
    :return: Set of ``(dotted_module, attr)`` pairs; empty on any parse issue.
    """
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return set()
    scripts = data.get("project", {}).get("scripts", {})
    targets: set[tuple[str, str]] = set()
    for spec in scripts.values():
        if isinstance(spec, str) and ":" in spec:
            module, _, attr = spec.partition(":")
            targets.add((module.strip(), attr.strip().split(".")[0]))
    return targets


def _declared_export_names(repo_root: Path) -> set[str]:
    """Collect names declared as public exports anywhere in the repo.

    A name in any module's ``__all__`` list, or re-exported (``from X import
    Y``) by a package ``__init__.py``, is a declared public API. Zero
    internal callers is its expected state, not evidence of dead code.

    Two definitions sharing a name are indistinguishable to this AST-only
    walk, so a name collision excludes both from orphan detection. That is
    the safe direction to err: missing one dead orphan costs less than
    flagging a declared export as dead code.

    :param repo_root: Root directory of the repository being analyzed.
    :return: Set of exported names (unqualified), collected repo-wide.
    """
    import ast as _ast  # noqa: PLC0415

    names: set[str] = set()
    for py_path in repo_root.rglob("*.py"):
        try:
            tree = _ast.parse(py_path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in _ast.walk(tree):
            if (
                isinstance(node, _ast.Assign)
                and any(isinstance(t, _ast.Name) and t.id == "__all__" for t in node.targets)
                and isinstance(node.value, _ast.List | _ast.Tuple)
            ):
                for elt in node.value.elts:
                    if isinstance(elt, _ast.Constant) and isinstance(elt.value, str):
                        names.add(elt.value)
            elif py_path.name == "__init__.py" and isinstance(node, _ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name and not name.startswith("_"):
                        names.add(name)
    return names


def _main_guard_block(source: str) -> str:
    """Return module source from the ``if __name__ == "__main__":`` guard on.

    The guard idiomatically closes the module, so everything after it is a
    good-enough approximation of the guarded block for name matching.

    :param source: Full module source text.
    :return: Source text from the guard line to EOF, or ``""`` if no guard.
    """
    m = _MAIN_GUARD_RE.search(source)
    return source[m.start() :] if m else ""


def _has_property_decorator(source_lines: list[str], def_lineno: int) -> bool:
    """Check whether the ``def`` at *def_lineno* carries a property decorator.

    Scans upward from the line above the ``def`` while decorator lines are
    found, matching ``@property``, ``@cached_property`` (bare or via
    ``functools``), and ``@<name>.setter/getter/deleter``.

    :param source_lines: Module source split into lines.
    :param def_lineno: 1-based line number of the ``def`` statement.
    :return: True when a property-family decorator precedes the definition.
    """
    i = def_lineno - 2  # 0-based index of the line above the def
    while i >= 0:
        stripped = source_lines[i].strip()
        if not stripped.startswith("@"):
            break
        if _PROPERTY_DECORATOR_RE.match(stripped):
            return True
        i -= 1
    return False


def _dotted_module(module_path: str) -> str:
    """Convert a repo-relative module path to its dotted import path.

    ``src/pycode_kg/mcp_server.py`` → ``pycode_kg.mcp_server``.  Only the
    conventional ``src/`` layout prefix is stripped; other roots pass through.

    :param module_path: Repo-relative path to a ``.py`` file.
    :return: Dotted module path.
    """
    path = module_path.removesuffix(".py")
    path = path.removeprefix("src/")
    return path.replace("/", ".")


def _fan_in_count(kg, node_id: str, rel: str = "CALLS") -> int:
    """Count real callers of *node_id*, excluding self-loops.

    A property body that reads the attribute it backs emits a ``CALLS`` edge
    to itself; counting that inflates fan-in for a node with no real callers.

    :param kg: PyCodeKG instance for graph queries.
    :param node_id: Target node identifier.
    :param rel: Relation type to invert (default ``"CALLS"``).
    :return: Number of distinct callers, excluding *node_id* itself.
    """
    return sum(1 for c in kg.callers(node_id, rel=rel) if c.get("id") != node_id)


class PyCodeKGAnalyzer:
    """Thorough repository analyzer using PyCodeKG graph.

    :param kg: PyCodeKG instance for graph queries
    :param console: Rich console for output (creates new if None)
    :param snapshot_mgr: Optional SnapshotManager for temporal history
    :param include_dirs: Directories included in the analysis (empty = all)
    :param exclude_dirs: Directories excluded from the analysis (empty = none)
    """

    def __init__(
        self,
        kg,
        console: Console | None = None,
        snapshot_mgr: SnapshotManager | None = None,
        include_dirs: set[str] | None = None,
        exclude_dirs: set[str] | None = None,
    ):
        """Initialize analyzer with PyCodeKG instance.

        :param kg: PyCodeKG instance
        :param console: Rich console for terminal output
        :param snapshot_mgr: Optional SnapshotManager; when provided, snapshot
            history is loaded and included in the report.
        :param include_dirs: Set of top-level directory names that were indexed.
            When empty/None, all directories were analyzed.
        :param exclude_dirs: Set of directory names that were excluded from indexing.
        """
        self.kg = kg
        self.console = console or Console()
        self.snapshot_mgr = snapshot_mgr
        self.include_dirs: set[str] = include_dirs or set()
        self.exclude_dirs: set[str] = exclude_dirs or set()
        self.stats: dict = {}
        self.function_metrics: dict[str, FunctionMetrics] = {}
        self.module_metrics: dict[str, ModuleMetrics] = {}
        self.orphaned_functions: list[FunctionMetrics] = []
        self.test_covered_orphans: list[FunctionMetrics] = []  # prod-orphaned, test-covered
        self.unverifiable_overrides: list[FunctionMetrics] = []  # external base, can't judge
        self._source_cache: dict[str, str | None] = {}  # module_path → source text
        self._orphan_scan_total: int = 0  # definitions the orphan scan examined
        self.grade_components: list[dict] = []  # populated by _compute_quality_grade
        self.high_fanout_functions: list[FunctionMetrics] = []
        self.critical_paths: list[CallChain] = []
        self.circular_deps: list[tuple[str, str]] = []
        self.public_apis: list[FunctionMetrics] = []
        self.issues: list[str] = []
        self.strengths: list[str] = []
        self.docstring_coverage: dict = {}  # populated by _analyze_docstring_coverage
        self.inheritance_analysis: dict = {}  # populated by _analyze_inheritance
        self.snapshot_history: list[dict] = []  # populated by _analyze_snapshots
        self.centrality_records: list = []  # populated by _analyze_centrality (node-level)
        self.centrality_modules: list[dict] = []  # populated by _analyze_centrality (module-level)
        # Option A: CodeRank scores computed early and reused across phases
        self.coderank_scores: dict[str, float] = {}  # node_id → global PageRank score
        self.coderank_top_nodes: list[dict] = []  # top-25 real nodes by CodeRank
        # Option D: concern-based hybrid ranking results
        self.concern_analysis: list[dict] = []  # populated by _analyze_concerns
        # Single-line phase output: each phase fn writes its summary here
        self._phase_result: str = ""

    # ── total phase count (update if phases are added/removed) ────────────────
    _TOTAL_PHASES = 15

    def _run_phase(self, num: int, name: str, fn: Callable[[], None]) -> None:
        """Run ``fn()`` and emit a single summary line with elapsed time.

        Each phase function writes its result summary to ``self._phase_result``
        instead of printing directly, keeping the terminal output to one line
        per phase.

        :param num: Phase number (1-based).
        :param name: Human-readable phase label.
        :param fn: Zero-argument callable to execute.
        """
        self._phase_result = ""
        t0 = time.monotonic()
        fn()
        elapsed = time.monotonic() - t0
        result = f"  {self._phase_result}" if self._phase_result else ""
        self.console.print(
            f"  [cyan]▶ Phase {num:2d}/{self._TOTAL_PHASES}:[/cyan]"
            f" {name}{result}  [green]({elapsed:.1f}s)[/green]"
        )

    def run_analysis(
        self,
        report_path: str | None = None,
        *,
        persist_centrality: bool = False,
    ) -> dict:
        """Run complete multi-phase analysis.

        Phase ordering:
        1.  Baseline metrics
        1b. CodeRank (Option A) — computed early so all later phases can use scores
        2.  Fan-in analysis — seeded by CodeRank top nodes (not semantic search)
        3.  Fan-out analysis
        4.  Dependency analysis
        5.  Pattern detection
        6.  Module coupling
        7.  Critical paths — seeded by CodeRank-ranked top functions
        8.  Public API identification
        9.  Docstring coverage
        10. Inheritance hierarchy
        11. Generate insights
        12. Snapshot history
        13. Structural centrality (SIR PageRank)
        14. CodeRank top-nodes report section (Option D)
        15. Concern-based hybrid ranking (Option D)

        :param report_path: Optional path to write markdown report
        :param persist_centrality: When ``True``, persist centrality scores to
            the ``centrality_scores`` table in the SQLite graph DB.
        :return: dictionary of analysis results
        """
        _start_time = datetime.datetime.now(datetime.UTC)
        try:
            self._run_phase(1, "Baseline metrics", self._analyze_baseline)
            self._run_phase(2, "CodeRank (global PageRank)", self._compute_coderank)
            self._run_phase(3, "Fan-in analysis", self._analyze_fan_in)
            self._run_phase(4, "Fan-out analysis", self._analyze_fan_out)
            self._run_phase(5, "Dependency analysis", self._analyze_dependencies)
            self._run_phase(6, "Pattern detection", self._detect_patterns)
            self._run_phase(7, "Module coupling", self._analyze_module_coupling)
            self._run_phase(8, "Critical paths", self._analyze_critical_paths)
            self._run_phase(9, "Public API identification", self._identify_public_apis)
            self._run_phase(10, "Docstring coverage", self._analyze_docstring_coverage)
            self._run_phase(11, "Inheritance hierarchy", self._analyze_inheritance)
            self._run_phase(12, "Generate insights", self._generate_insights)
            self._run_phase(13, "Snapshot history", self._analyze_snapshots)
            self._run_phase(14, "Structural centrality (SIR)", self._analyze_centrality)
            if persist_centrality and self.centrality_records:
                from pycode_kg.analysis.centrality import (  # noqa: PLC0415
                    StructuralImportanceRanker,
                )

                StructuralImportanceRanker(self.kg.db_path).write_scores(self.centrality_records)

            self._run_phase(15, "Concern-based ranking", self._analyze_concerns)

            # Optional: write report
            if report_path:
                elapsed = (datetime.datetime.now(datetime.UTC) - _start_time).total_seconds()
                self._write_report(report_path, elapsed_seconds=elapsed)

            return self._compile_results()

        except (AttributeError, ValueError, RuntimeError) as e:
            self.console.print(f"[red]Analysis failed: {e}[/red]")
            logger.exception("Analysis failed")
            raise

    def _analyze_baseline(self) -> None:
        """Phase 1: Get overall codebase metrics.

        Queries graph_stats() to establish baseline counts by node kind
        and edge relationship type.
        """
        try:
            self.stats = self.kg.stats()
            n = self.stats.get("total_nodes", "?")
            e = self.stats.get("total_edges", "?")
            self._phase_result = f"nodes={n}  edges={e}"

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning(f"Could not get baseline stats: {e}")
            self.console.print(f"[yellow]WARN[/yellow] Could not get baseline stats: {e}")

    def _analyze_fan_in(self) -> None:
        """Phase 2: Find most-called functions (fan-in).

        Option A: Uses CodeRank scores (computed in Phase 1b) to seed the
        candidate set instead of fragile semantic search.  Falls back to a
        direct SQL query over all function/method/class nodes when CodeRank
        is unavailable.

        For each candidate node, the exact caller count is obtained via
        ``kg.callers(node_id, rel="CALLS")``.  The top-15 by fan-in are
        stored in ``self.function_metrics``.
        """

        try:
            # --- Option A: seed from CodeRank top nodes (deterministic, no vector search) ---
            if self.coderank_scores:
                # Pull ALL real function/method/class nodes from SQLite, sorted by
                # CodeRank score descending.  This is O(nodes) but avoids the k-limit
                # and semantic-search noise of the old approach.
                rows = self.kg.store.con.execute(
                    """
                    SELECT id, name, kind, module_path, docstring, lineno, end_lineno
                    FROM nodes
                    WHERE kind IN ('function', 'method', 'class')
                      AND id NOT LIKE 'sym:%'
                    ORDER BY module_path, name
                    """
                ).fetchall()

                # Attach CodeRank scores and sort by score descending
                scored: list[tuple[float, tuple]] = []
                for row in rows:
                    node_id = row[0]
                    score = self.coderank_scores.get(node_id, 0.0)
                    scored.append((score, row))
                scored.sort(key=lambda x: x[0], reverse=True)

                # Compute actual fan-in for top-100 by CodeRank (covers all meaningful nodes)
                fan_in_data: list[tuple] = []
                for _score, row in scored[:100]:
                    node_id, name, kind, module_path, docstring, lineno, end_lineno = row
                    try:
                        caller_count = _fan_in_count(self.kg, node_id, rel="CALLS")
                        metrics = FunctionMetrics(
                            node_id=node_id,
                            name=name or "unknown",
                            module=module_path or "unknown",
                            kind=kind or "unknown",
                            fan_in=caller_count,
                            fan_out=0,
                            lines=max(0, (end_lineno or 0) - (lineno or 0)),
                            docstring=docstring,
                        )
                        fan_in_data.append((node_id, metrics))
                    except (AttributeError, ValueError, RuntimeError, TypeError) as e:
                        logger.debug(f"Could not analyze node {node_id}: {e}")

            else:
                # --- Fallback: direct SQL over all nodes (no CodeRank available) ---
                logger.info("CodeRank unavailable — falling back to SQL fan-in scan")
                rows = self.kg.store.con.execute(
                    """
                    SELECT id, name, kind, module_path, docstring, lineno, end_lineno
                    FROM nodes
                    WHERE kind IN ('function', 'method', 'class')
                      AND id NOT LIKE 'sym:%'
                    ORDER BY module_path, name
                    """
                ).fetchall()

                fan_in_data = []
                for row in rows:
                    node_id, name, kind, module_path, docstring, lineno, end_lineno = row
                    try:
                        caller_count = _fan_in_count(self.kg, node_id, rel="CALLS")
                        metrics = FunctionMetrics(
                            node_id=node_id,
                            name=name or "unknown",
                            module=module_path or "unknown",
                            kind=kind or "unknown",
                            fan_in=caller_count,
                            fan_out=0,
                            lines=max(0, (end_lineno or 0) - (lineno or 0)),
                            docstring=docstring,
                        )
                        fan_in_data.append((node_id, metrics))
                    except (AttributeError, ValueError, RuntimeError, TypeError) as e:
                        logger.debug(f"Could not analyze node {node_id}: {e}")

            # Sort by fan-in descending, keep top 15
            fan_in_data.sort(key=lambda x: x[1].fan_in, reverse=True)
            for node_id, metrics in fan_in_data[:15]:
                self.function_metrics[node_id] = metrics

            seed = "CodeRank-seeded" if self.coderank_scores else "SQL fallback"
            self._phase_result = f"top {len(self.function_metrics)} by fan-in ({seed})"

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning(f"Fan-in analysis incomplete: {e}")
            self.console.print(f"[yellow]WARN[/yellow] Fan-in analysis incomplete: {e}")

    def _internal_fan_out_counts(self) -> dict[str, int]:
        """Distinct repo-internal callees per caller node.

        Raw CALLS-edge counts make every CLI command look like an orchestrator:
        ``click.echo``, ``path.exists`` and ``dict.get`` each contribute a
        callee even though they orchestrate nothing.  Fan-out here counts only
        callees that live in the repo — direct ``fn:``/``m:``/``cls:`` targets
        plus ``sym:`` stubs that resolve internally — and skips dotted stubs
        ending in builtin method names (see :data:`_BUILTIN_METHOD_NAMES`),
        which resolve by last-segment collision, not by receiver.

        :return: Mapping of caller node id → count of distinct internal callees.
        """
        rows = self.kg.store.con.execute(
            """
            SELECT c.src, c.dst, r.dst
            FROM edges c
            LEFT JOIN edges r
              ON r.src = c.dst AND r.rel = 'RESOLVES_TO' AND r.dst NOT LIKE 'sym:%'
            WHERE c.rel = 'CALLS'
            """
        ).fetchall()
        callees: dict[str, set[str]] = defaultdict(set)
        for src, dst, resolved_dst in rows:
            if dst.startswith("sym:"):
                sym_name = dst.removeprefix("sym:")
                if "." in sym_name and sym_name.rsplit(".", 1)[-1] in _BUILTIN_METHOD_NAMES:
                    continue
                if resolved_dst is None:
                    continue  # external call — stdlib, third-party, builtin
                callees[src].add(resolved_dst)
            else:
                callees[src].add(dst)
        return {caller: len(targets) for caller, targets in callees.items()}

    def _analyze_fan_out(self) -> None:
        """Phase 3: Find functions that call many others (fan-out).

        Fan-out counts *repo-internal* callees only (see
        :meth:`_internal_fan_out_counts`) — a linear CLI command with thirty
        ``click.echo`` progress lines is not an orchestrator.  Also identifies
        additional high-fanout orchestrator functions beyond the fan-in set.
        """

        try:
            internal_fan_out = self._internal_fan_out_counts()

            # For functions already identified, record their internal fan-out
            for node_id, metrics in self.function_metrics.items():
                metrics.fan_out = internal_fan_out.get(node_id, 0)

            # Query for additional orchestrator functions
            try:
                result = self.kg.query(
                    "coordinator orchestrator manager init constructor setup",
                    k=20,
                    hop=0,
                    rels=("CONTAINS",),
                )

                for node in result.nodes:
                    node_id = node.get("id")
                    if not node_id or node_id in self.function_metrics:
                        continue

                    if node.get("kind") not in ["function", "method"]:
                        continue

                    fanout_count = internal_fan_out.get(node_id, 0)

                    if fanout_count > 25:
                        metrics = FunctionMetrics(
                            node_id=node_id,
                            name=node.get("name", "unknown"),
                            module=node.get("module_path", "unknown"),
                            kind=node.get("kind", "unknown"),
                            fan_in=0,
                            fan_out=fanout_count,
                            lines=max(
                                0,
                                (node.get("end_lineno") or 0) - (node.get("lineno") or 0),
                            ),
                        )

                        self.high_fanout_functions.append(metrics)
            except (AttributeError, ValueError, RuntimeError) as e:
                logger.debug(f"Could not query orchestrators: {e}")

            self._phase_result = f"{len(self.high_fanout_functions)} high-fanout functions"

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning(f"Fan-out analysis incomplete: {e}")
            self.console.print(f"[yellow]WARN[/yellow] Fan-out analysis incomplete: {e}")

    def _module_source(self, module_path: str) -> str | None:
        """Read (and cache) the source of a repo-relative module path.

        :param module_path: Repo-relative path as stored on graph nodes.
        :return: Source text, or None when the file cannot be read.
        """
        if module_path not in self._source_cache:
            text: str | None = None
            repo_root = getattr(self.kg, "repo_root", None)
            if repo_root:
                try:
                    text = (Path(repo_root) / module_path).read_text(encoding="utf-8")
                except OSError:
                    text = None
            self._source_cache[module_path] = text
        return self._source_cache[module_path]

    def _tests_corpus(self) -> str:
        """Concatenate the target repo's ``tests/`` sources for name matching.

        The graph indexes production directories only (``include_dirs``), so a
        helper called solely from tests has zero visible callers.  Matching
        orphan names against the test sources separates "dead everywhere" from
        "prod-orphaned but test-covered".

        :return: All test-file text joined together; ``""`` if no tests dir.
        """
        repo_root = getattr(self.kg, "repo_root", None)
        if not repo_root:
            return ""
        tests_dir = Path(repo_root) / "tests"
        if not tests_dir.is_dir():
            return ""
        chunks: list[str] = []
        for path in sorted(tests_dir.rglob("*.py")):
            try:
                chunks.append(path.read_text(encoding="utf-8"))
            except OSError:
                continue
        return "\n".join(chunks)

    def _build_orphan_context(self) -> dict:
        """Precompute the graph context the orphan exclusions need.

        One pass over the edges table instead of per-node queries:

        - ``class_of``: method node id → containing class node id
        - ``external_bases``: class id → base names (transitive through
          internal parents) that resolve to nothing inside the graph —
          i.e. framework classes like ``ast.NodeVisitor`` or the kg_utils SDK
        - ``inherited_classes``: class ids with at least one incoming INHERITS
          edge, following sym: stubs through RESOLVES_TO
        - ``script_targets``: ``(dotted_module, function)`` pairs declared in
          ``[project.scripts]``
        - ``exported_names``: names declared public via ``__all__`` anywhere
          in the repo, or re-exported by a package ``__init__.py``

        :return: Context dict consumed by :meth:`_is_special_entry_point`.
        """
        con = self.kg.store.con
        contains = con.execute(
            "SELECT src, dst FROM edges WHERE rel = 'CONTAINS' AND src LIKE 'cls:%'"
        ).fetchall()
        inherits = con.execute("SELECT src, dst FROM edges WHERE rel = 'INHERITS'").fetchall()
        resolves = con.execute(
            "SELECT src, dst FROM edges WHERE rel = 'RESOLVES_TO' AND src LIKE 'sym:%'"
        ).fetchall()

        class_of = {dst: src for src, dst in contains}
        resolved: dict[str, list[str]] = defaultdict(list)
        for src, dst in resolves:
            if not dst.startswith("sym:"):
                resolved[src].append(dst)

        inherited_classes: set[str] = set()
        direct_external: dict[str, set[str]] = defaultdict(set)
        internal_parents: dict[str, set[str]] = defaultdict(set)
        for child, parent in inherits:
            targets = [parent] if not parent.startswith("sym:") else resolved.get(parent, [])
            if targets:
                inherited_classes.update(targets)
                internal_parents[child].update(targets)
            else:
                # sym: stub with no internal resolution — an external base
                direct_external[child].add(parent.removeprefix("sym:"))

        def _transitive_external(cls_id: str) -> set[str]:
            """Collect external base names reachable via internal parents."""
            seen: set[str] = set()
            queue = [cls_id]
            out: set[str] = set()
            while queue:
                cur = queue.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                out.update(direct_external.get(cur, set()))
                queue.extend(internal_parents.get(cur, set()))
            return out

        external_bases = {
            cls_id: _transitive_external(cls_id)
            for cls_id in set(direct_external) | set(internal_parents)
        }

        script_targets: set[tuple[str, str]] = set()
        exported_names: set[str] = set()
        repo_root = getattr(self.kg, "repo_root", None)
        if repo_root:
            script_targets = _console_script_targets(Path(repo_root) / "pyproject.toml")
            exported_names = _declared_export_names(Path(repo_root))

        return {
            "class_of": class_of,
            "external_bases": external_bases,
            "inherited_classes": inherited_classes,
            "script_targets": script_targets,
            "exported_names": exported_names,
        }

    def _is_special_entry_point(self, node: dict, ctx: dict) -> bool:
        """Check if a definition is framework-dispatched and thus never orphaned.

        Special entry points are intentional zero-callers:

        - Dunder methods (``__init__``, ``__exit__``, …) — Python runtime
        - Property-family methods — accessed as attributes, not calls
        - MCP tools in ``mcp_server.py`` — dispatched by the MCP router
        - Click handlers in CLI modules — dispatched by Click
        - ``visit_*`` on ``ast.NodeVisitor`` subclasses — ``getattr`` dispatch
        - Overrides of SDK protocol methods on classes with external bases —
          invoked by the kg_utils pipeline
        - Classes with incoming INHERITS edges — used as bases
        - ``[project.scripts]`` targets and functions called from a module's
          ``if __name__ == "__main__":`` guard
        - Declared public exports — a name in any ``__all__`` list, or
          re-exported by a package ``__init__.py``

        :param node: Dict with node_id, name, kind, module_path, lineno.
        :param ctx: Precomputed context from :meth:`_build_orphan_context`.
        :return: True if this node should be excluded from orphan detection.
        """
        name = node.get("name", "")
        kind = node.get("kind", "")
        module = node.get("module_path", "")
        node_id = node.get("node_id", "")

        # Dunder methods: invoked by Python's runtime machinery.
        if name.startswith("__") and name.endswith("__"):
            return True

        # MCP tools: dispatched by the MCP protocol router.
        if "mcp_server" in module:
            return True

        # Click handlers: dispatched by Click's CLI router.
        if "/cli/" in module or module.endswith("cli.py"):
            return True

        # Classes used as bases: INHERITS is usage, even with zero CALLS.
        if kind == "class" and node_id in ctx["inherited_classes"]:
            return True

        # Declared public exports: named in __all__ somewhere, or re-exported
        # by a package __init__.py. Zero internal callers is expected — the
        # name exists to be imported from outside the indexed graph.
        if kind in ("function", "class") and name in ctx["exported_names"]:
            return True

        if kind == "method":
            cls_id = ctx["class_of"].get(node_id)
            ext = ctx["external_bases"].get(cls_id, set()) if cls_id else set()

            # ast.NodeVisitor dispatch: visit() finds visit_* via getattr, so
            # no CALLS edge ever exists.  Matched on the base name to survive
            # both `ast.NodeVisitor` and a bare `NodeVisitor` import.
            if ext and (name.startswith("visit_") or name == "generic_visit"):
                if any(base.rsplit(".", 1)[-1] == "NodeVisitor" for base in ext):
                    return True

            # SDK protocol overrides: the kg_utils pipeline calls these on the
            # base-class interface, outside the indexed graph.
            if ext and name in _protocol_attr_names():
                return True

            # Property-family decorators: accessed as attributes, not calls.
            source = self._module_source(module)
            lineno = node.get("lineno")
            if source and lineno:
                if _has_property_decorator(source.splitlines(), lineno):
                    return True

        if kind == "function":
            # Console-script targets from [project.scripts].
            if (_dotted_module(module), name) in ctx["script_targets"]:
                return True

            # Functions invoked from the module's __main__ guard: the call is
            # at module scope, which produces no CALLS edge.
            source = self._module_source(module)
            if source:
                guard = _main_guard_block(source)
                if guard and re.search(rf"\b{re.escape(name)}\s*\(", guard):
                    return True

                # Callback/registry references: passing a function by bare
                # name (``resolve_kind=_resolve_kind``) creates no CALLS
                # edge.  Any occurrence of the name beyond its own def line
                # means the module references it.  Methods are not checked —
                # their ``self.x`` references already produce ATTR_ACCESS
                # edges.  Known blind spot: a dead function that only calls
                # itself recursively is hidden by this rule.
                if len(re.findall(rf"\b{re.escape(name)}\b", source)) > 1:
                    return True

        return False

    def _is_unverifiable_override(self, node: dict, ctx: dict) -> bool:
        """Check whether a method overrides a base class this graph cannot see.

        Called only after :meth:`_is_special_entry_point` returns ``False``,
        so this covers the override cases that check *doesn't* recognize by
        name (``_protocol_attr_names()``) or pattern (``NodeVisitor``
        dispatch): any other method on a class with an external base.  The
        graph has no visibility into that base, so the caller may live
        inside the dependency — this cannot be judged either way.

        Deleting such an override does not raise ``NameError``; it silently
        reverts behavior to the base class, so treating "unverifiable" as
        "dead" is the worse failure mode. Report it separately instead of
        excusing it into silence.

        :param node: Dict with node_id, name, kind, module_path, lineno.
        :param ctx: Precomputed context from :meth:`_build_orphan_context`.
        :return: True when the method's enclosing class has an external base.
        """
        if node.get("kind") != "method":
            return False
        cls_id = ctx["class_of"].get(node.get("node_id", ""))
        if not cls_id:
            return False
        return bool(ctx["external_bases"].get(cls_id))

    def _analyze_dependencies(self) -> None:
        """Phase 4: Detect orphaned definitions (zero callers).

        Scans **every** function, method, and class node in the graph rather
        than a semantic sample.  A semantic seed query only surfaces nodes whose
        docstrings read like dead code, which systematically misses genuinely
        unreferenced modules — the exact population this phase exists to find.

        A node is orphaned when it has no CALLS callers *and* no ATTR_ACCESS
        callers, and is not a framework-dispatched entry point (see
        ``_is_special_entry_point``).  Orphans whose name appears in the
        repo's ``tests/`` sources are reported separately as "test-covered" —
        they are unused in production code but exercised by tests, which
        usually marks public API consumed by downstream packages rather than
        dead code.  A zero-caller method whose class inherits from a base
        outside the indexed graph (see ``_is_unverifiable_override``) cannot
        be judged either way and is reported separately, not as dead code.
        """

        try:
            ctx = self._build_orphan_context()
            rows = self.kg.store.con.execute(
                """
                SELECT id, name, kind, module_path, lineno, end_lineno
                FROM nodes
                WHERE kind IN ('function', 'method', 'class')
                  AND id NOT LIKE 'sym:%'
                ORDER BY module_path, name
                """
            ).fetchall()

            self._orphan_scan_total = len(rows)
            candidates: list[FunctionMetrics] = []
            for node_id, name, kind, module_path, lineno, end_lineno in rows:
                node = {
                    "node_id": node_id,
                    "name": name,
                    "kind": kind,
                    "module_path": module_path,
                    "lineno": lineno,
                }

                try:
                    caller_list = self.kg.callers(node_id, rel="CALLS")

                    # Also check ATTR_ACCESS edges: a bound method reference
                    # (e.g. ``self._foo`` passed as a callback to ``_run_phase``)
                    # produces ATTR_ACCESS edges, not CALLS edges.  A node with
                    # ATTR_ACCESS callers is in active use and must not be flagged
                    # as orphaned.
                    try:
                        attr_list = self.kg.callers(node_id, rel="ATTR_ACCESS")
                    except (AttributeError, ValueError, RuntimeError):
                        attr_list = []

                    if caller_list or attr_list:
                        continue

                    # Exclude framework-dispatched entry points
                    if self._is_special_entry_point(node, ctx):
                        logger.debug(f"Skipping {name} — special entry point (framework-driven)")
                        continue

                    # External-base overrides: no positive evidence either
                    # way, so report separately rather than call it dead.
                    if self._is_unverifiable_override(node, ctx):
                        logger.debug(f"Skipping {name} — external base class, cannot verify")
                        self.unverifiable_overrides.append(
                            FunctionMetrics(
                                node_id=node_id,
                                name=name or "unknown",
                                module=module_path or "unknown",
                                kind=kind or "unknown",
                                fan_in=0,
                                fan_out=0,
                                lines=max(0, (end_lineno or 0) - (lineno or 0)),
                            )
                        )
                        continue

                    candidates.append(
                        FunctionMetrics(
                            node_id=node_id,
                            name=name or "unknown",
                            module=module_path or "unknown",
                            kind=kind or "unknown",
                            fan_in=0,
                            fan_out=0,
                            lines=max(0, (end_lineno or 0) - (lineno or 0)),
                        )
                    )

                except (AttributeError, ValueError, RuntimeError) as e:
                    logger.debug(f"Could not check callers for {node_id}: {e}")

            # Split: names appearing in tests/ are prod-orphaned but exercised;
            # only orphans with no callers *anywhere* count as dead code.
            tests_text = self._tests_corpus()
            for f in candidates:
                if tests_text and re.search(rf"\b{re.escape(f.name)}\b", tests_text):
                    self.test_covered_orphans.append(f)
                else:
                    self.orphaned_functions.append(f)

            self.orphaned_functions.sort(key=lambda f: f.lines, reverse=True)
            self.test_covered_orphans.sort(key=lambda f: f.lines, reverse=True)
            self.unverifiable_overrides.sort(key=lambda f: f.lines, reverse=True)
            self._phase_result = (
                f"{len(self.orphaned_functions)} dead, "
                f"{len(self.test_covered_orphans)} test-covered orphans, "
                f"{len(self.unverifiable_overrides)} unverifiable overrides"
            )

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning(f"Dependency analysis incomplete: {e}")
            self.console.print(f"[yellow]WARN[/yellow] Dependency analysis incomplete: {e}")

    def _detect_patterns(self) -> None:
        """Phase 5: Detect architectural patterns.

        Identifies core modules, integration points, layering violations,
        and design patterns (singletons, managers, etc.).
        """

        try:
            # Identify core modules by aggregating fan-in
            module_call_counts: dict[str, int] = defaultdict(int)
            for metrics in self.function_metrics.values():
                # Group by top-level module
                module = metrics.module.split("/")[0] if "/" in metrics.module else metrics.module
                module_call_counts[module] += metrics.fan_in

            core_modules = sorted(
                module_call_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5]

            if core_modules:
                self._phase_result = f"{len(core_modules)} core modules"

            # Identify tight coupling patterns
            high_fanout = sorted(
                list(self.function_metrics.values()) + self.high_fanout_functions,
                key=lambda m: m.fan_out,
                reverse=True,
            )[:10]

            for func in high_fanout:
                if func.fan_out > 50 and func.name != "__init__":
                    self.issues.append(
                        f"[HIGH] {func.name} has high fan-out ({func.fan_out} calls) "
                        "-- consider breaking into smaller functions"
                    )

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning(f"Pattern detection incomplete: {e}")

    def _analyze_module_coupling(self) -> None:
        """Phase 6: Analyze module-level coupling and dependencies.

        Uses IMPORTS edges to identify module interdependencies and
        calculate cohesion metrics.

        Two bulk SQL queries replace the former per-module loop so the phase
        runs in O(1) round-trips regardless of module count.
        """
        try:
            con = self.kg.store.con

            # Query all modules directly from the store — reliable, no semantic k-limit
            module_rows = con.execute(
                "SELECT id, module_path FROM nodes WHERE kind = 'module' ORDER BY module_path"
            ).fetchall()

            # ── Bulk import-edge query ──────────────────────────────────────────
            # One pass through IMPORTS→RESOLVES_TO to get (importer, importee)
            # module-path pairs.  Both incoming and outgoing can be derived from
            # this single result set.
            import_pairs = con.execute(
                """
                SELECT DISTINCT ni.module_path AS importer, nd.module_path AS importee
                FROM edges ei
                JOIN nodes ns ON ei.dst = ns.id
                JOIN edges er ON er.src = ns.id AND er.rel = 'RESOLVES_TO'
                JOIN nodes nd ON er.dst = nd.id AND nd.module_path IS NOT NULL
                JOIN nodes ni ON ei.src = ni.id AND ni.kind = 'module'
                WHERE ei.rel = 'IMPORTS'
                  AND ni.module_path != nd.module_path
                """
            ).fetchall()

            # Build lookup dicts from the bulk result
            incoming_map: dict[str, set[str]] = defaultdict(set)  # importee → importers
            outgoing_map: dict[str, set[str]] = defaultdict(set)  # importer → importees
            for importer, importee in import_pairs:
                if importer and importee:
                    incoming_map[importee].add(importer)
                    outgoing_map[importer].add(importee)

            # ── Bulk node-count query ───────────────────────────────────────────
            count_rows = con.execute(
                "SELECT module_path, kind, COUNT(*) FROM nodes"
                " WHERE kind IN ('function', 'class', 'method')"
                " GROUP BY module_path, kind"
            ).fetchall()

            kind_counts: dict[str, dict[str, int]] = defaultdict(dict)
            for mod_path, kind, cnt in count_rows:
                if mod_path:
                    kind_counts[mod_path][kind] = cnt

            # ── Assemble metrics ────────────────────────────────────────────────
            for _, module_path in module_rows:
                module_path = module_path or "unknown"
                incoming = list(incoming_map.get(module_path, set()))
                outgoing = list(outgoing_map.get(module_path, set()))
                # Cohesion = incoming / (incoming + outgoing + 1).  Higher = more
                # internally focused (many modules depend on it, few outward
                # dependencies).  A leaf entry-point (e.g. mcp_server.py with
                # incoming=0, outgoing=3) should score ~0, not 0.75.  The +1 in
                # the denominator keeps the score finite for orphan modules.
                cohesion = min(1.0, len(incoming) / (len(incoming) + len(outgoing) + 1))
                counts = kind_counts.get(module_path, {})
                self.module_metrics[module_path] = ModuleMetrics(
                    path=module_path,
                    functions=counts.get("function", 0),
                    classes=counts.get("class", 0),
                    methods=counts.get("method", 0),
                    incoming_deps=incoming,
                    outgoing_deps=outgoing,
                    total_fan_in=len(incoming),
                    cohesion_score=cohesion,
                )

            self._phase_result = f"{len(self.module_metrics)} modules"

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning(f"Module coupling analysis incomplete: {e}")

    def _analyze_critical_paths(self) -> None:
        """Phase 7: Identify key call chains.

        Traces real call paths: finds high-fan-in functions, follows CALLS
        edges forward to build actual execution chains, and prepends one
        representative caller for context.
        """

        try:
            # Start from high fan-in functions (exclude dunder methods).
            top_functions = [
                m
                for m in sorted(
                    self.function_metrics.values(),
                    key=lambda m: m.fan_in,
                    reverse=True,
                )
                if not (m.name.startswith("__") and m.name.endswith("__"))
            ][:5]

            for func in top_functions:
                try:
                    callers = self.kg.callers(func.node_id, rel="CALLS")

                    # Trace forward from func through real CALLS edges.  Steps
                    # are module-qualified so a cross-module hop is visible as
                    # such instead of reading like a same-file call.
                    chain_names = [f"{Path(func.module).name}:{func.name}"]
                    chain_modules = [func.module]
                    seen_ids: set[str] = {func.node_id}
                    current_id = func.node_id

                    for _ in range(6):
                        edges = self.kg.store.edges_from(current_id, rel="CALLS", limit=5)
                        callee = None
                        for edge in edges:
                            dst_id = edge["dst"]
                            # Resolve sym: stubs via RESOLVES_TO.
                            if dst_id.startswith("sym:"):
                                sym_name = dst_id.removeprefix("sym:")
                                # ``visited.update`` / ``chunks.append`` style
                                # attr calls resolve by last segment, so a repo
                                # function named ``update`` captures every dict
                                # and set mutation in the codebase.  Don't
                                # follow builtin-method lookalikes.
                                if (
                                    "." in sym_name
                                    and sym_name.rsplit(".", 1)[-1] in _BUILTIN_METHOD_NAMES
                                ):
                                    continue
                                resolved = self.kg.store.con.execute(
                                    "SELECT dst FROM edges"
                                    " WHERE src = ? AND rel = 'RESOLVES_TO' LIMIT 1",
                                    (dst_id,),
                                ).fetchone()
                                if resolved:
                                    dst_id = resolved[0]
                            if dst_id in seen_ids:
                                continue
                            node = self.kg.store.node(dst_id)
                            if node and node.get("module_path"):
                                callee = node
                                seen_ids.add(dst_id)
                                current_id = dst_id
                                break
                        if callee:
                            callee_module = callee.get("module_path", "")
                            chain_names.append(
                                f"{Path(callee_module).name}:{callee.get('name', '?')}"
                            )
                            chain_modules.append(callee_module)
                        else:
                            break

                    # Prepend top caller to give the chain context.
                    if callers:
                        caller_module = callers[0].get("module_path", "")
                        chain_names = [
                            f"{Path(caller_module).name}:{callers[0].get('name', '?')}",
                            *chain_names,
                        ]
                        chain_modules = [caller_module, *chain_modules]

                    crosses_module = len(set(chain_modules)) > 1
                    if len(chain_names) >= 4 or crosses_module:
                        call_chain = CallChain(
                            chain=chain_names,
                            depth=len(chain_names),
                            total_callers=len(callers),
                        )
                        self.critical_paths.append(call_chain)

                except (AttributeError, ValueError, RuntimeError) as e:
                    logger.debug(f"Could not trace path for {func.name}: {e}")

            self._phase_result = f"{len(self.critical_paths)} key call chains"

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning(f"Call chain analysis incomplete: {e}")

    def _identify_public_apis(self) -> None:
        """Phase 8: Identify public APIs (module-level exports).

        Strategy (in priority order):
        1. Collect declared exports (``__all__`` anywhere, ``__init__.py``
           re-exports — see :func:`_declared_export_names`) and look each
           name up in the graph as a public API.
        2. Supplement with non-private functions/classes in ``function_metrics``
           that have at least one caller and are not already included.
        """

        try:
            already_ids: set[str] = set()

            # --- Step 1: declared exports (__all__ / __init__.py re-exports) ---
            try:
                exported_names = _declared_export_names(Path(self.kg.repo_root))
                for name in sorted(exported_names):
                    rows = self.kg.store.con.execute(
                        "SELECT id, name, kind, module_path, docstring FROM nodes"
                        " WHERE name = ? AND kind IN ('class', 'function')"
                        "   AND SUBSTR(name, 1, 1) != '_'",
                        (name,),
                    ).fetchall()
                    for row in rows:
                        node_id, nm, kind, module_path, docstring = row
                        if node_id not in already_ids:
                            try:
                                fan_in = len(self.kg.callers(node_id, rel="CALLS"))
                            except (AttributeError, ValueError, RuntimeError):
                                fan_in = 0
                            self.public_apis.append(
                                FunctionMetrics(
                                    node_id=node_id,
                                    name=nm,
                                    module=module_path or "",
                                    kind=kind,
                                    fan_in=fan_in,
                                    fan_out=0,
                                    lines=0,
                                    docstring=docstring,
                                )
                            )
                            already_ids.add(node_id)
            except (OSError, AttributeError, ValueError, RuntimeError):
                pass

            # --- Step 2: supplement from function_metrics ---
            for func in sorted(
                self.function_metrics.values(), key=lambda m: m.fan_in, reverse=True
            ):
                if (
                    func.kind in ("function", "class")
                    and func.fan_in >= 1
                    and not func.name.startswith("_")
                    and func.node_id not in already_ids
                ):
                    self.public_apis.append(func)
                    already_ids.add(func.node_id)

            # Sort by fan-in descending
            self.public_apis.sort(key=lambda m: m.fan_in, reverse=True)

            self._phase_result = f"{len(self.public_apis)} public API functions"

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning(f"Public API identification incomplete: {e}")

    def _analyze_docstring_coverage(self) -> None:
        """Phase 9: Measure docstring coverage across the codebase.

        Queries the SQLite nodes table directly to count how many
        functions, methods, classes, and modules have a non-empty
        docstring versus their total. Results are stored in
        ``self.docstring_coverage`` for use by ``_generate_insights``
        and ``_write_report``.
        """

        try:
            if not hasattr(self.kg, "_store"):
                self.console.print("[yellow]WARN[/yellow] Docstring coverage skipped (no store)")
                return

            rows = self.kg._store.con.execute(
                """
                SELECT
                    kind,
                    COUNT(*) AS total,
                    SUM(
                        CASE WHEN docstring IS NOT NULL AND TRIM(docstring) != ''
                        THEN 1 ELSE 0 END
                    ) AS with_doc
                FROM nodes
                WHERE kind IN ('function', 'method', 'class', 'module')
                GROUP BY kind
                ORDER BY kind
                """
            ).fetchall()

            by_kind: dict[str, dict[str, int]] = {}
            overall_total = 0
            overall_with_doc = 0

            for kind, total, with_doc in rows:
                by_kind[kind] = {"total": total, "with_doc": with_doc}
                overall_total += total
                overall_with_doc += with_doc

            overall_pct = (overall_with_doc / overall_total * 100) if overall_total else 0.0

            self.docstring_coverage = {
                "by_kind": by_kind,
                "total": overall_total,
                "with_doc": overall_with_doc,
                "coverage_pct": round(overall_pct, 1),
            }

            self._phase_result = f"{overall_with_doc}/{overall_total} nodes ({overall_pct:.1f}%)"

        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning(f"Docstring coverage analysis incomplete: {e}")
            self.console.print(f"[yellow]WARN[/yellow] Docstring coverage incomplete: {e}")

    def _analyze_inheritance(self) -> None:
        """Phase 10: Analyze class inheritance hierarchy.

        Queries all INHERITS edges from the SQLite store and builds a complete
        class hierarchy.  Reports depth per class, multiple-inheritance usage,
        and diamond patterns (two distinct inheritance paths to a common
        ancestor, which can cause MRO surprises in Python).
        """

        try:
            rows = self.kg.store.con.execute(
                "SELECT src, dst FROM edges WHERE rel = 'INHERITS'"
            ).fetchall()
        except (AttributeError, ValueError, RuntimeError) as e:
            logger.warning(f"Inheritance analysis incomplete: {e}")
            self.console.print(f"[yellow]WARN[/yellow] Inheritance analysis incomplete: {e}")
            return

        if not rows:
            self.inheritance_analysis = {
                "total_inherits_edges": 0,
                "classes": [],
                "max_depth": 0,
                "multiple_inheritance": [],
                "diamonds": [],
            }
            self._phase_result = "no inheritance edges"
            return

        # INHERITS edge direction: src = child (the subclass), dst = parent base class.
        # Resolve sym: stubs to real class IDs via RESOLVES_TO edges (same pattern as
        # callers_of) so that in-repo inheritance (e.g. AlliumLayout → Layout3D) is
        # tracked correctly even when the base class is referenced through an import stub.
        con = self.kg.store.con

        def _resolve_dst(dst: str) -> list[str]:
            """Return real node IDs for *dst*, resolving sym: stubs if needed."""
            if not dst.startswith("sym:"):
                return [dst]
            resolved = con.execute(
                "SELECT dst FROM edges WHERE src = ? AND rel = 'RESOLVES_TO'",
                (dst,),
            ).fetchall()
            # Keep only class/module nodes; fall back to the stub if nothing resolves
            real = [r[0] for r in resolved if not r[0].startswith("sym:")]
            return real if real else [dst]

        parents: dict[str, set[str]] = {}  # child_id → set of parent_ids (resolved)
        children: dict[str, set[str]] = {}  # parent_id → set of child_ids
        all_classes: set[str] = set()
        raw_parent_count: dict[str, int] = {}  # child_id → number of declared bases

        for src, dst in rows:
            raw_parent_count[src] = raw_parent_count.get(src, 0) + 1
            for real_dst in _resolve_dst(dst):
                parents.setdefault(src, set()).add(real_dst)
                if not real_dst.startswith("sym:"):
                    children.setdefault(real_dst, set()).add(src)
                    all_classes.add(real_dst)
            all_classes.add(src)

        def _all_internal_ancestors(cls_id: str) -> set[str]:
            """BFS to collect all non-sym: ancestors of *cls_id*."""
            visited: set[str] = set()
            queue = list(parents.get(cls_id, set()))
            while queue:
                cur = queue.pop()
                if cur.startswith("sym:") or cur in visited:
                    continue
                visited.add(cur)
                queue.extend(parents.get(cur, set()))
            return visited

        def _compute_depth(cls_id: str, memo: dict[str, int]) -> int:
            if cls_id in memo:
                # -1 sentinel means "currently being computed" — cycle detected, return 0
                return max(memo[cls_id], 0)
            internal_ps = {p for p in parents.get(cls_id, set()) if not p.startswith("sym:")}
            if not internal_ps:
                memo[cls_id] = 0
                return 0
            memo[cls_id] = -1  # mark in-progress before recursing
            depth = 1 + max(_compute_depth(p, memo) for p in internal_ps)
            memo[cls_id] = depth
            return depth

        depth_memo: dict[str, int] = {}
        class_data: list[dict] = []
        multiple_inheritance: list[dict] = []
        diamonds: list[dict] = []

        for cls_id in sorted(all_classes):
            node = self.kg.node(cls_id)
            name = node.get("name", cls_id) if node else cls_id.split(":")[-1]
            module = node.get("module_path", "") if node else ""

            cls_parents = parents.get(cls_id, set())
            internal_parents = {p for p in cls_parents if not p.startswith("sym:")}
            declared_count = raw_parent_count.get(cls_id, len(cls_parents))
            depth = _compute_depth(cls_id, depth_memo)

            class_data.append(
                {
                    "node_id": cls_id,
                    "name": name,
                    "module": module,
                    "depth": depth,
                    "parent_count": declared_count,
                    "child_count": len(children.get(cls_id, set())),
                    "external_bases": max(0, declared_count - len(internal_parents)),
                }
            )

            # Multiple inheritance: more than one declared base
            if declared_count > 1:
                parent_names = []
                for p in sorted(cls_parents):
                    pn = self.kg.node(p) if not p.startswith("sym:") else None
                    parent_names.append(pn.get("name", p) if pn else p.split(":")[-1])
                multiple_inheritance.append(
                    {
                        "class": name,
                        "module": module,
                        "bases": sorted(parent_names),
                    }
                )

            # Diamond detection: two distinct internal parents sharing a common ancestor
            if len(internal_parents) >= 2:
                ip_list = sorted(internal_parents)
                ancestor_sets = [_all_internal_ancestors(p) | {p} for p in ip_list]
                reported = False
                for i in range(len(ancestor_sets)):
                    if reported:
                        break
                    for j in range(i + 1, len(ancestor_sets)):
                        shared = ancestor_sets[i] & ancestor_sets[j]
                        if shared:
                            shared_names = []
                            for s in sorted(shared):
                                sn = self.kg.node(s)
                                shared_names.append(sn.get("name", s) if sn else s.split(":")[-1])
                            diamonds.append(
                                {
                                    "class": name,
                                    "module": module,
                                    "common_ancestors": shared_names,
                                }
                            )
                            reported = True
                            break

        max_depth = max((e["depth"] for e in class_data), default=0)
        self.inheritance_analysis = {
            "total_inherits_edges": len(rows),
            "classes": sorted(class_data, key=lambda x: x["depth"], reverse=True),
            "max_depth": max_depth,
            "multiple_inheritance": multiple_inheritance,
            "diamonds": diamonds,
        }

        self._phase_result = f"{len(all_classes)} classes  max-depth={max_depth}"

    # -------------------------------------------------------------------------
    # Option A: CodeRank — computed early, reused by fan-in and critical paths
    # -------------------------------------------------------------------------

    def _compute_coderank(self) -> None:
        """Phase 1b: Compute global CodeRank (weighted PageRank) over the graph.

        Builds a directed weighted graph from the SQLite store using
        ``build_code_graph`` and runs ``compute_coderank``.  Results are stored
        in ``self.coderank_scores`` (node_id → score) and
        ``self.coderank_top_nodes`` (top-25 real nodes, sym: stubs excluded).

        These scores are reused in Phase 2 (fan-in seed discovery) and Phase 7
        (critical path prioritisation) so that both phases are driven by
        structural importance rather than fragile semantic search.
        """

        try:
            from pycode_kg.ranking.coderank import (  # noqa: PLC0415
                build_code_graph,
                compute_coderank,
            )

            graph = build_code_graph(
                str(self.kg.db_path),
                include_relations=("CALLS", "IMPORTS", "INHERITS"),
                exclude_test_paths=True,
            )
            self.coderank_scores = compute_coderank(graph)

            # Build top-25 real nodes (exclude sym: stubs) with node metadata
            sorted_nodes = sorted(self.coderank_scores.items(), key=lambda kv: kv[1], reverse=True)
            top_nodes: list[dict] = []
            for node_id, score in sorted_nodes:
                if node_id.startswith("sym:"):
                    continue
                attrs = graph.nodes.get(node_id, {})
                kind = attrs.get("kind", "")
                if kind not in ("function", "method", "class", "module"):
                    continue
                top_nodes.append(
                    {
                        "node_id": node_id,
                        "score": score,
                        "kind": kind,
                        "name": attrs.get("name", node_id.split(":")[-1]),
                        "qualname": attrs.get("qualname", ""),
                        "module_path": attrs.get("module_path", ""),
                    }
                )
                if len(top_nodes) >= 25:
                    break

            self.coderank_top_nodes = top_nodes

            if top_nodes:
                self._phase_result = (
                    f"{len(self.coderank_scores)} nodes  top=`{top_nodes[0]['name']}`"
                )
            else:
                self._phase_result = f"{len(self.coderank_scores)} nodes"

        except (AttributeError, ValueError, RuntimeError, ImportError) as e:
            logger.warning(f"CodeRank computation incomplete: {e}")
            self.console.print(f"[yellow]WARN[/yellow] CodeRank incomplete: {e}")

    # -------------------------------------------------------------------------
    # Option D: Phase 15 — Concern-based hybrid ranking
    # -------------------------------------------------------------------------

    def _analyze_concerns(self) -> None:
        """Phase 15: Run query_ranked for architectural concern queries.

        Executes ``rank_query_hybrid`` for a fixed set of architectural concern
        queries using the pre-computed global CodeRank scores as the centrality
        signal.  For each concern, the top-5 structurally-dominant nodes are
        recorded.

        Results are stored in ``self.concern_analysis`` as a list of dicts, where
        each entry contains a ``concern`` label (e.g. error handling, data
        persistence, graph traversal) and a ``top_nodes`` list of ranked result
        dicts with ``rank``, ``node_id``, ``name``, ``module``, ``kind``,
        ``score``, and ``why`` fields.

        Requires the sqlite-vec vector index to be available (``self.kg`` must
        support ``query()``).  Degrades gracefully if the index is unavailable.
        """

        # Concern entries are (display_label, embedding_query) pairs.
        #
        # The query string seeds the vector index and benefits from verb anchors
        # specific to the concern — pure noun phrases (e.g. "graph traversal
        # node edge") collapse to whatever module mentions those nouns most,
        # regardless of intent.  The "graph traversal" concern previously
        # surfaced 3-D layout ``compute()`` methods because their docstrings
        # happen to say "nodes" / "edges" / "graph"; adding ``expand`` /
        # ``callers`` / ``neighbors`` anchors the query on store-traversal
        # verbs that 3-D layout code does not contain.
        #
        # The display label is what shows up as the section heading in the
        # report — kept short and human-readable, decoupled from the query.
        CONCERNS: list[tuple[str, str]] = [
            (
                "configuration loading initialization setup",
                "configuration loading initialization setup",
            ),
            (
                "data persistence storage database",
                "data persistence storage database",
            ),
            (
                "query search retrieval semantic",
                "query search retrieval semantic",
            ),
            (
                "graph traversal node edge",
                "graph expansion traverse callers neighbors edges from seeds",
            ),
        ]

        try:
            from pycode_kg.ranking.coderank import (  # noqa: PLC0415
                build_code_graph,
                rank_query_hybrid,
            )

            # Reuse the graph if already built; otherwise build a fresh one.
            # We need the full graph object for rank_query_hybrid.
            graph = build_code_graph(
                str(self.kg.db_path),
                include_relations=("CALLS", "IMPORTS", "INHERITS"),
                exclude_test_paths=True,
            )

            results: list[dict] = []

            for label, query in CONCERNS:
                try:
                    # Get semantic scores from the vector index.
                    # Suppress tqdm progress bars from embedding model loading.
                    import os as _os  # noqa: PLC0415

                    _old_disable = _os.environ.get("TQDM_DISABLE")
                    _os.environ["TQDM_DISABLE"] = "1"
                    try:
                        query_result = self.kg.query(query, k=8, hop=0, rels=("CONTAINS",))
                    finally:
                        if _old_disable is None:
                            _os.environ.pop("TQDM_DISABLE", None)
                        else:
                            _os.environ["TQDM_DISABLE"] = _old_disable
                    semantic_scores: dict[str, float] = {}
                    for node in query_result.nodes:
                        node_id = node.get("id")
                        score = (node.get("relevance") or {}).get("score", 0.0)
                        if node_id and score > 0:
                            semantic_scores[node_id] = float(score)

                    if not semantic_scores:
                        logger.debug(f"No semantic seeds for concern: {label!r}")
                        continue

                    ranked = rank_query_hybrid(
                        graph,
                        semantic_scores,
                        global_coderank=self.coderank_scores or None,
                        radius=2,
                        top_k=5,
                    )

                    top_nodes = []
                    for rank_idx, r in enumerate(ranked, 1):
                        if r.kind not in ("function", "method", "class"):
                            continue
                        top_nodes.append(
                            {
                                "rank": rank_idx,
                                "node_id": r.node_id,
                                "name": r.qualname or r.node_id.split(":")[-1],
                                "module": r.module_path or "",
                                "kind": r.kind or "",
                                "score": round(r.adjusted_score, 4),
                                "why": list(r.why),
                            }
                        )
                        if len(top_nodes) >= 5:
                            break

                    if top_nodes:
                        results.append({"concern": label, "top_nodes": top_nodes})

                except (AttributeError, ValueError, RuntimeError) as e:
                    logger.debug(f"Concern query failed for {label!r}: {e}")

            self.concern_analysis = results
            self._phase_result = f"{len(results)}/{len(CONCERNS)} concerns resolved"

        except (AttributeError, ValueError, RuntimeError, ImportError) as e:
            logger.warning(f"Concern analysis incomplete: {e}")
            self.console.print(f"[yellow]WARN[/yellow] Concern analysis incomplete: {e}")

    # -------------------------------------------------------------------------
    # Phase 2 override: SQL-seeded fan-in using CodeRank top nodes (Option A)
    # -------------------------------------------------------------------------

    def _analyze_centrality(self) -> None:
        """Phase 13: Compute Structural Importance Ranking (SIR).

        Runs weighted PageRank over the resolved graph using CALLS, INHERITS,
        IMPORTS, and CONTAINS edges, with cross-module and private-symbol
        adjustments.  Results are stored in ``self.centrality_records`` for
        inclusion in reports and optional DB persistence.
        """

        try:
            from pycode_kg.analysis.centrality import (  # noqa: PLC0415
                StructuralImportanceRanker,
                aggregate_module_scores,
            )

            ranker = StructuralImportanceRanker(self.kg.db_path)
            # Compute all nodes (no top cap) so module aggregates are accurate,
            # then store top-25 for node-level display.
            all_records = ranker.compute()
            self.centrality_records = all_records[:25]
            self.centrality_modules = aggregate_module_scores(all_records)

            self._phase_result = f"{len(all_records)} nodes  {len(self.centrality_modules)} modules"
        except (AttributeError, ValueError, RuntimeError, ImportError) as e:
            logger.warning(f"Centrality analysis incomplete: {e}")
            self.console.print(f"[yellow]WARN[/yellow] Centrality analysis incomplete: {e}")

    def _analyze_snapshots(self) -> None:
        """Phase 12: Load snapshot history for temporal comparison.

        Calls ``list_snapshots()`` on the SnapshotManager (if provided) and
        stores the most recent entries in ``self.snapshot_history`` for
        inclusion in the report.  Silently skips when no SnapshotManager was
        supplied or the snapshots directory doesn't exist yet.
        """
        if self.snapshot_mgr is None:
            self._phase_result = "skipped (no snapshot manager)"
            return

        try:
            self.snapshot_history = self.snapshot_mgr.list_snapshots(limit=10)
            self._phase_result = f"{len(self.snapshot_history)} snapshot(s)"
        except (AttributeError, ValueError, RuntimeError, OSError) as e:
            logger.warning(f"Snapshot history unavailable: {e}")
            self.console.print(f"[yellow]WARN[/yellow] Snapshot history unavailable: {e}")

    def _generate_insights(self) -> None:
        """Phase 10: Generate actionable insights.

        Compiles issues and strengths based on metrics collected
        in earlier phases.
        """
        # Strengths
        if len(self.function_metrics) > 0:
            self.strengths.append(
                f"Well-structured with {len(self.function_metrics)} core functions identified"
            )

        if len(self.orphaned_functions) == 0:
            self.strengths.append("No obvious dead code detected")

        if len(self.high_fanout_functions) == 0:
            self.strengths.append("No god objects or god functions detected")

        # Docstring coverage signals
        cov = self.docstring_coverage
        if cov:
            pct = cov["coverage_pct"]
            if pct >= 80:
                self.strengths.append(
                    f"Good docstring coverage: {pct}% of functions/methods/classes/modules documented"
                )
            elif pct >= 50:
                self.issues.append(
                    f"[WARN] Moderate docstring coverage ({pct}%) — semantic retrieval quality is degraded "
                    "for undocumented nodes; BM25 is as effective as embeddings without docstrings"
                )
            else:
                self.issues.append(
                    f"[LOW] Low docstring coverage ({pct}%) — semantic query quality will be poor; "
                    "embedding undocumented nodes yields only structured identifiers, not NL-searchable text. "
                    "Prioritize docstrings on high-fan-in functions first."
                )

        # Centrality cross-reference insights
        if self.centrality_modules and self.module_metrics:
            # High-SIR modules that are also tightly coupled = highest architectural risk
            sir_by_path = {m["module_path"]: m for m in self.centrality_modules[:10]}
            risky = [
                m
                for path, m in sir_by_path.items()
                if path in self.module_metrics
                and (
                    len(self.module_metrics[path].incoming_deps)
                    + len(self.module_metrics[path].outgoing_deps)
                )
                > 4
            ]
            if risky:
                names = ", ".join(f"`{m['module_path'].split('/')[-1]}`" for m in risky[:3])
                self.issues.append(
                    f"[WARN] High-SIR modules with tight coupling: {names} -- "
                    "structurally central AND heavily connected; changes here ripple broadly"
                )
            else:
                top_name = self.centrality_modules[0]["module_path"].split("/")[-1]
                self.strengths.append(
                    f"Top-ranked module (`{top_name}`) has manageable coupling -- "
                    "structural importance is not compounded by excessive dependencies"
                )

        # High-SIR nodes missing docstrings = highest-priority documentation targets
        if self.centrality_records:
            top_ids = [r.node_id for r in self.centrality_records[:15]]
            try:
                placeholders = ",".join("?" * len(top_ids))
                rows = self.kg.store.con.execute(
                    f"SELECT id FROM nodes WHERE id IN ({placeholders})"  # noqa: S608
                    " AND (docstring IS NULL OR TRIM(docstring) = '')",
                    top_ids,
                ).fetchall()
                undocumented_ids = {row[0] for row in rows}
                undocumented = [
                    r for r in self.centrality_records[:15] if r.node_id in undocumented_ids
                ]
                if undocumented:
                    names = ", ".join(f"`{r.name}`" for r in undocumented[:4])
                    self.issues.append(
                        f"[WARN] High-SIR nodes lack docstrings: {names} -- "
                        "structurally critical but invisible to the semantic index; "
                        "document these first for maximum retrieval improvement"
                    )
            except (AttributeError, ValueError, RuntimeError):
                pass

        # Issues
        if len(self.orphaned_functions) > 0:
            shown = self.orphaned_functions[:8]
            names = ", ".join(f"`{f.module.rsplit('/', 1)[-1]}:{f.name}`" for f in shown)
            more = len(self.orphaned_functions) - len(shown)
            suffix = f" and {more} more" if more > 0 else ""
            self.issues.append(
                f"[WARN] {len(self.orphaned_functions)} dead-code candidates found "
                f"({names}{suffix}) -- no callers in code or tests; verify against "
                "downstream consumers, then remove or archive"
            )
        if len(self.test_covered_orphans) > 0:
            self.issues.append(
                f"[INFO] {len(self.test_covered_orphans)} definitions are unused in "
                "production code but exercised by tests -- likely public API for "
                "downstream packages; not counted against the quality grade"
            )

        if len(self.high_fanout_functions) > 0:
            self.issues.append(
                f"[WARN] {len(self.high_fanout_functions)} functions with high fan-out "
                "-- potential orchestrators or god objects"
            )

        # Module size checks — flag modules with >30 functions/methods/classes
        try:
            large_modules = self.kg.store.con.execute(
                """
                SELECT module_path, COUNT(*) AS cnt
                FROM nodes
                WHERE kind IN ('function', 'method', 'class')
                  AND module_path IS NOT NULL
                GROUP BY module_path
                HAVING cnt > 30
                ORDER BY cnt DESC
                LIMIT 5
                """
            ).fetchall()
            for mod_path, cnt in large_modules:
                mod_name = mod_path.split("/")[-1] if mod_path else "?"
                self.issues.append(
                    f"[WARN] `{mod_name}` has {cnt} functions/methods/classes "
                    "-- consider splitting into focused submodules"
                )
        except (AttributeError, ValueError, RuntimeError):
            pass

        # Inheritance insights
        inh = self.inheritance_analysis
        if inh:
            if inh.get("diamonds"):
                d_names = ", ".join(f"`{d['class']}`" for d in inh["diamonds"])
                self.issues.append(
                    f"[WARN] Diamond inheritance detected: {d_names} -- "
                    "verify MRO is intentional (C3 linearisation)"
                )
            if inh.get("max_depth", 0) > 3:
                self.issues.append(
                    f"[WARN] Deep inheritance hierarchy (max depth {inh['max_depth']}) -- "
                    "consider flattening via composition"
                )
            if inh.get("multiple_inheritance") and not inh.get("diamonds"):
                self.strengths.append(
                    f"Multiple inheritance used in {len(inh['multiple_inheritance'])} class(es) "
                    "without diamond patterns"
                )

        self._phase_result = f"{len(self.issues)} issues  {len(self.strengths)} strengths"

    def _compute_quality_grade(self) -> tuple[float, str, str]:
        """Compute an overall quality score, letter grade, and label.

        Every component is a continuous curve rather than a step function, so
        crossing a single threshold can no longer move the grade a full
        letter, and dead code is measured as a *rate* so the score does not
        punish repository growth.  Scoring (100 points total):

        - Docstring coverage (0–40 pts): linear from 0% to full marks at 90%
        - Dead-code candidates (0–25 pts): linear from 0% of scanned
          definitions (25 pts) to ≥5% (0 pts); test-covered orphans are
          excluded — they are usually public API
        - High fan-out functions (0–20 pts): 4 pts lost per orchestrator
        - Circular dependencies (0–15 pts): 5 pts lost per cycle

        The per-component breakdown is stored on :attr:`grade_components` and
        rendered in the Executive Summary, so a grade change is always
        explainable from the report alone.

        :return: Tuple of (score 0–100, letter grade A–F, label string)
        """
        # Docstring coverage: full marks at 90%+, linear below.
        pct = self.docstring_coverage.get("coverage_pct", 0) if self.docstring_coverage else 0
        doc_pts = 40.0 * min(pct, 90.0) / 90.0

        # Dead code: rate against everything the orphan scan looked at.
        n_dead = len(self.orphaned_functions)
        scanned = max(self._orphan_scan_total, 1)
        dead_rate = n_dead / scanned
        dead_pts = 25.0 * max(0.0, 1.0 - dead_rate / 0.05)

        # High fan-out orchestrators: linear penalty per finding.
        n_fanout = len(self.high_fanout_functions)
        fanout_pts = max(0.0, 20.0 - 4.0 * n_fanout)

        # Circular dependencies: linear penalty per cycle.
        n_circular = len(self.circular_deps)
        circular_pts = max(0.0, 15.0 - 5.0 * n_circular)

        self.grade_components = [
            {
                "name": "Docstring coverage",
                "points": doc_pts,
                "max": 40,
                "basis": f"{pct}% documented (full marks at 90%)",
            },
            {
                "name": "Dead code",
                "points": dead_pts,
                "max": 25,
                "basis": f"{n_dead} candidates / {scanned} definitions scanned ({dead_rate:.1%}; zero points at 5%)",
            },
            {
                "name": "High fan-out",
                "points": fanout_pts,
                "max": 20,
                "basis": f"{n_fanout} orchestrator(s); −4 pts each",
            },
            {
                "name": "Circular dependencies",
                "points": circular_pts,
                "max": 15,
                "basis": f"{n_circular} cycle(s); −5 pts each",
            },
        ]
        score = doc_pts + dead_pts + fanout_pts + circular_pts

        if score >= 90:
            grade, label = "A", "Excellent"
        elif score >= 75:
            grade, label = "B", "Good"
        elif score >= 60:
            grade, label = "C", "Fair"
        elif score >= 45:
            grade, label = "D", "Needs Work"
        else:
            grade, label = "F", "Critical"

        return score, grade, label

    def _build_recommendations(self) -> str:
        """Build tailored recommendations from actual analysis results.

        :return: Markdown string with immediate, medium-term, and long-term sections.
        """
        immediate: list[str] = []
        medium: list[str] = []
        long_term: list[str] = []

        cov = self.docstring_coverage
        if cov:
            pct = cov.get("coverage_pct", 0)
            if pct < 80:
                undocumented = cov.get("total", 0) - cov.get("with_doc", 0)
                immediate.append(
                    f"**Improve docstring coverage** — {undocumented} nodes lack docstrings; "
                    "prioritize high-fan-in functions and public APIs first for maximum semantic retrieval gain"
                )

        if self.orphaned_functions:
            names = ", ".join(f"`{f.name}`" for f in self.orphaned_functions[:5])
            suffix = (
                f" (and {len(self.orphaned_functions) - 5} more)"
                if len(self.orphaned_functions) > 5
                else ""
            )
            immediate.append(
                f"**Triage dead-code candidates** — {names}{suffix} have zero callers in "
                "code and tests; confirm no downstream package consumes them, then remove"
            )

        if self.high_fanout_functions:
            top = self.high_fanout_functions[0]
            immediate.append(
                f"**Refactor high fan-out orchestrators** — `{top.name}` calls {top.fan_out} functions; "
                "consider splitting into smaller, focused coordinators"
            )

        if self.circular_deps:
            pairs = "; ".join(f"`{a}` ↔ `{b}`" for a, b in self.circular_deps[:3])
            immediate.append(
                f"**Resolve circular dependencies** — {pairs}; introduce an abstraction layer or invert the dependency"
            )

        # High fan-in functions need documentation/thread-safety review
        top_fanin = sorted(self.function_metrics.values(), key=lambda m: m.fan_in, reverse=True)[:3]
        if top_fanin and top_fanin[0].fan_in > 1:
            names = ", ".join(f"`{m.name}`" for m in top_fanin)
            medium.append(
                f"**Harden high fan-in functions** — {names} are widely depended upon; "
                "review for thread safety, clear contracts, and stable interfaces"
            )

        if self.module_metrics:
            tightly_coupled = [
                m
                for m in self.module_metrics.values()
                if len(m.incoming_deps) + len(m.outgoing_deps) > 5
            ]
            if tightly_coupled:
                medium.append(
                    "**Reduce module coupling** — consider splitting tightly coupled modules "
                    "or introducing interface boundaries"
                )

        if self.critical_paths:
            medium.append(
                "**Add tests for key call chains** — the identified call chains represent "
                "well-traveled execution paths that benefit most from regression coverage"
            )

        if self.public_apis:
            long_term.append(
                "**Version and stabilize the public API** — document breaking-change policies "
                f"for {', '.join(f'`{a.name}`' for a in self.public_apis[:3])}"
            )

        long_term.append(
            "**Enforce layer boundaries** — add linting or CI checks to prevent unexpected "
            "cross-module dependencies as the codebase grows"
        )
        long_term.append(
            "**Monitor hot paths** — instrument the high fan-in functions identified here "
            "to catch performance regressions early"
        )

        if not immediate and not medium:
            immediate.append(
                "**Maintain current quality** — no critical issues detected; keep coverage and structure healthy"
            )

        lines = []
        if immediate:
            lines.append("### Immediate Actions")
            for i, rec in enumerate(immediate, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        if medium:
            lines.append("### Medium-term Refactoring")
            for i, rec in enumerate(medium, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        if long_term:
            lines.append("### Long-term Architecture")
            for i, rec in enumerate(long_term, 1):
                lines.append(f"{i}. {rec}")
        return "\n".join(lines)

    def _get_report_metadata(self, elapsed_seconds: float = 0.0) -> str:
        """Build a Markdown metadata block for the top of the report.

        Collects the generation timestamp, PyCodeKG package version, current Git
        commit SHA and branch, host platform details, and a summary of the
        graph snapshot metrics (total nodes/edges).  All Git, import, and
        platform operations fail gracefully so the method is safe to call
        outside of a Git working tree or before the package is installed.

        :param elapsed_seconds: Total analysis elapsed time in seconds
        :return: Formatted Markdown string to prepend to the report.
        """
        # --- timestamp ---
        now = datetime.datetime.now(datetime.UTC)
        generated = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        # --- version ---
        version = "unknown"
        try:
            from pycode_kg import (  # noqa: PLC0415
                __version__ as _v,
            )

            version = f"pycode-kg {_v}"
        except (ImportError, AttributeError):
            try:
                from importlib.metadata import (  # noqa: PLC0415
                    version as _pkg_version,
                )

                version = f"pycode-kg {_pkg_version('pycode-kg')}"
            except (ImportError, AttributeError):
                pass

        # --- git commit (prefer CI env vars, fall back to subprocess) ---
        commit = os.environ.get("GITHUB_SHA", "")
        if commit:
            commit = commit[:7]
        else:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    commit = result.stdout.strip()
            except (OSError, FileNotFoundError):
                pass
        if not commit:
            commit = "unknown"

        # --- git branch (prefer CI env vars, fall back to subprocess) ---
        branch = ""
        github_ref = os.environ.get("GITHUB_REF", "")
        if github_ref.startswith("refs/heads/"):
            branch = github_ref[len("refs/heads/") :]
        elif github_ref.startswith("refs/pull/"):
            # Pull-request ref: refs/pull/<number>/merge
            branch = github_ref
        if not branch:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    branch = result.stdout.strip()
            except (OSError, FileNotFoundError):
                pass
        if not branch:
            branch = "unknown"

        commit_ref = f"{commit} ({branch})"

        # --- platform ---
        try:
            _sys = platform.system()
            _mac = platform.mac_ver()[0]
            _os = f"macOS {_mac}" if _mac else f"{_sys} {platform.release()}"
            _arch = platform.machine()  # arm64 / x86_64
            _cpu = platform.processor() or _arch  # e.g. "arm" / "i386"
            _host = platform.node()
            _py = platform.python_version()
            plat = f"{_os} | {_arch} ({_cpu}) | {_host} | Python {_py}"
        except Exception:  # noqa: BLE001
            plat = "unknown"

        # --- graph snapshot metrics ---
        stats = self.stats or {}
        total_nodes = stats.get("total_nodes", "?")
        total_edges = stats.get("total_edges", "?")
        meaningful = stats.get("meaningful_nodes")
        graph_line = f"{total_nodes} nodes · {total_edges} edges"
        if meaningful is not None:
            graph_line += f" ({meaningful} meaningful)"

        # --- included/excluded directories ---
        if self.include_dirs:
            dirs_line = ", ".join(sorted(self.include_dirs))
        else:
            dirs_line = "all"

        if self.exclude_dirs:
            exclude_line = ", ".join(sorted(self.exclude_dirs))
        else:
            exclude_line = "none"

        # --- elapsed time ---
        elapsed_str = ""
        if elapsed_seconds > 0:
            mins, secs = divmod(int(elapsed_seconds), 60)
            if mins > 0:
                elapsed_str = f"{mins}m {secs}s"
            else:
                elapsed_str = f"{secs}s"

        return (
            "> **Analysis Report Metadata**  \n"
            f"> - **Generated:** {generated}  \n"
            f"> - **Version:** {version}  \n"
            f"> - **Commit:** {commit_ref}  \n"
            f"> - **Platform:** {plat}  \n"
            f"> - **Graph:** {graph_line}  \n"
            f"> - **Included directories:** {dirs_line}  \n"
            f"> - **Excluded directories:** {exclude_line}  \n"
            + (f"> - **Elapsed time:** {elapsed_str}  \n" if elapsed_str else "")
            + "\n"
        )

    def _write_report(self, report_path: str, elapsed_seconds: float = 0.0) -> None:
        """Render the analysis and write it to a Markdown file.

        Rendering lives entirely in :meth:`to_markdown` — this method only
        supplies run provenance and performs the write.

        :param report_path: Path to write the markdown report to
        :param elapsed_seconds: Total analysis duration in seconds
        """
        markdown = self.to_markdown(
            metadata=self._get_report_metadata(elapsed_seconds=elapsed_seconds),
            elapsed_seconds=elapsed_seconds,
        )
        Path(report_path).write_text(markdown)
        self.console.print(f"[OK] Report written to {report_path}")

    def _compile_results(self) -> dict:
        """Compile analysis results into a dictionary.

        Function metrics are sorted by risk descending (critical → high →
        medium → low) so the most dangerous functions appear first.

        Module metrics exclude empty modules (no incoming or outgoing
        dependencies) to avoid cluttering output with __init__.py stubs.

        :return: dictionary with all analysis data
        """
        sorted_fn = sorted(
            self.function_metrics.items(),
            key=lambda kv: kv[1].fan_in,
            reverse=True,
        )
        active_modules = {
            k: v
            for k, v in self.module_metrics.items()
            if v.total_fan_in > 0 or len(v.outgoing_deps) > 0
        }
        quality_score, quality_grade, quality_label = self._compute_quality_grade()
        return {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "statistics": self.stats,
            "quality": {
                "score": quality_score,
                "grade": quality_grade,
                "label": quality_label,
                "components": self.grade_components,
            },
            "docstring_coverage": self.docstring_coverage,
            "function_metrics": {k: asdict(v) for k, v in sorted_fn},
            "module_metrics": {k: asdict(v) for k, v in active_modules.items()},
            "orphaned_functions": [asdict(f) for f in self.orphaned_functions],
            "test_covered_orphans": [asdict(f) for f in self.test_covered_orphans],
            "unverifiable_overrides": [asdict(f) for f in self.unverifiable_overrides],
            "high_fanout_functions": [asdict(f) for f in self.high_fanout_functions],
            "critical_paths": [asdict(c) for c in self.critical_paths],
            "public_apis": [asdict(a) for a in self.public_apis],
            "issues": self.issues,
            "strengths": self.strengths,
            "inheritance": self.inheritance_analysis,
            "snapshot_history": self.snapshot_history,
            "centrality": [
                {
                    "rank": r.rank,
                    "node_id": r.node_id,
                    "kind": r.kind,
                    "name": r.name,
                    "module_path": r.module_path,
                    "score": r.score,
                    "inbound_count": r.inbound_count,
                    "cross_module_inbound": r.cross_module_inbound,
                    "rel_breakdown": r.rel_breakdown,
                }
                for r in self.centrality_records
            ],
            "centrality_modules": self.centrality_modules,
            # Option A: CodeRank global scores (top-25 real nodes)
            "coderank_top_nodes": self.coderank_top_nodes,
            # Option D: concern-based hybrid ranking
            "concern_analysis": self.concern_analysis,
        }

    def to_markdown(self, *, metadata: str = "", elapsed_seconds: float | None = None) -> str:
        """Render the full Markdown report from this analyzer's state.

        Thin delegation to :func:`pycode_kg.report.render_markdown`, which
        owns all section emitters; kept as a method so existing callers
        (``kg.analyze()``, the MCP ``analyze_repo`` tool) keep their API.

        :param metadata: Optional run-provenance blockquote to prepend.
        :param elapsed_seconds: Analysis duration for the timing footer.
        :return: Markdown-formatted string representing the full analysis.
        """
        return render_markdown(self, metadata=metadata, elapsed_seconds=elapsed_seconds)

    def print_summary(self) -> None:
        """Print analysis summary to console."""
        # Header
        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold cyan]PyCodeKG Repository Analysis[/bold cyan]",
                border_style="cyan",
            )
        )
        self.console.print()

        # Stats table
        stats_table = Table(title="Baseline Metrics", show_header=True)
        stats_table.add_column("Metric", style="dim")
        stats_table.add_column("Value")

        for key, value in self.stats.items():
            stats_table.add_row(key, str(value))

        self.console.print(stats_table)
        self.console.print()

        # Most called functions
        if self.function_metrics:
            calls_table = Table(title="Most Called Functions (Fan-In)", show_header=True)
            calls_table.add_column("Function", style="cyan")
            calls_table.add_column("Callers", justify="right")

            for metrics in sorted(
                self.function_metrics.values(),
                key=lambda m: m.fan_in,
                reverse=True,
            )[:10]:
                calls_table.add_row(
                    metrics.name,
                    str(metrics.fan_in),
                )

            self.console.print(calls_table)
            self.console.print()

        # Issues
        if self.issues:
            self.console.print("[bold yellow]Issues Found:[/bold yellow]")
            for issue in self.issues:
                self.console.print(f"  {issue}")
            self.console.print()

        # Strengths
        if self.strengths:
            self.console.print("[bold green]Strengths:[/bold green]")
            for strength in self.strengths:
                self.console.print(f"  {strength}")
            self.console.print()


def _default_report_name(repo_root: Path) -> str:
    """Derive a timestamped default markdown report path under ``analysis/``.

    :param repo_root: Repository root directory
    :return: Path string like ``analysis/myrepo_analysis_20260224.md``
    """
    repo_name = repo_root.resolve().name
    date_str = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d")
    return str(Path("analysis") / f"{repo_name}_analysis_{date_str}.md")


def main(
    repo_root: str = ".",
    db_path: str | None = None,
    vectors_path: str | None = None,
    report_path: str | None = None,
    json_path: str | None = None,
    quiet: bool = False,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
    persist_centrality: bool = False,
) -> None:
    """Main entry point.

    Paths for ``db_path`` and ``vectors_path`` default to the standard
    ``.pycodekg/`` layout inside ``repo_root`` when not provided.
    The markdown report defaults to ``<repo>_analysis_<YYYYMMDD>.md``
    in the current working directory.  The JSON snapshot always writes
    to ``~/.claude/pycodekg_analysis_latest.json`` unless overridden.

    Error handling strategy:
    - Missing graph database prints a warning and allows execution to continue,
        so callers still get useful diagnostics.
    - Import/runtime failures are reported with clear remediation guidance.

    Logging approach:
    - Rich console output is used for visible run status and outputs.
    - ``logging`` warnings are used for partial-analysis fallbacks.

    :param repo_root: Root directory of the repository (default: ``"."``)
    :param db_path: Path to SQLite knowledge graph; default ``.pycodekg/graph.sqlite``
    :param vectors_path: Path to sqlite-vec vector store; default ``.pycodekg/vectors.sqlite``
    :param report_path: Markdown report output path; auto-named when ``None``
    :param json_path: JSON snapshot output path; when ``None`` (default) no JSON is written
    :param quiet: Suppress console summary table when ``True``
    :param include: Set of top-level directory names to include in analysis.
                   When empty/None, all directories are analyzed.
    :param exclude: Set of directory names that were excluded during indexing.
                   Recorded in the report metadata for traceability.
    :param persist_centrality: When ``True``, persist SIR scores to the
        ``centrality_scores`` table in the SQLite graph DB.
    """
    console = Console()
    root = Path(repo_root).resolve()
    db = Path(db_path) if db_path else root / ".pycodekg" / "graph.sqlite"
    vectors = Path(vectors_path) if vectors_path else root / ".pycodekg" / "vectors.sqlite"
    md_out = report_path or _default_report_name(root)
    Path(md_out).parent.mkdir(parents=True, exist_ok=True)
    json_out = Path(json_path) if json_path else None

    if not db.exists():
        console.print(
            f"[red]ERROR[/red]  Database not found at [dim]{db}[/dim]\n"
            "Run [bold]pycodekg build --repo .[/bold] first, then re-run analyze."
        )
        return

    try:
        from pycode_kg import PyCodeKG  # noqa: PLC0415

        console.print(f"[dim]Repo   : {root}[/dim]")
        console.print(f"[dim]DB     : {db}[/dim]")
        console.print(f"[dim]Index  : {vectors}[/dim]")
        console.print(f"[dim]Report : {md_out}[/dim]")
        console.print()

        kg = PyCodeKG(repo_root=root, db_path=db, vectors_path=vectors)

        snapshots_dir = root / ".pycodekg" / "snapshots"
        snap_mgr = SnapshotManager(snapshots_dir) if snapshots_dir.exists() else None

        # Resolve effective include/exclude dirs: prefer explicit args, fall back to pyproject.toml
        from pycode_kg.config import (  # noqa: PLC0415
            load_exclude_dirs,
            load_include_dirs,
        )

        effective_include = include or load_include_dirs(root)
        effective_exclude = exclude or load_exclude_dirs(root)

        analyzer = PyCodeKGAnalyzer(
            kg,
            console,
            snapshot_mgr=snap_mgr,
            include_dirs=effective_include,
            exclude_dirs=effective_exclude,
        )
        results = analyzer.run_analysis(
            report_path=md_out,
            persist_centrality=persist_centrality,
        )

        if not quiet:
            analyzer.print_summary()

        if json_out is not None:
            json_out.parent.mkdir(parents=True, exist_ok=True)
            json_out.write_text(json.dumps(results, indent=2))
            console.print(f"[dim]JSON   : {json_out}[/dim]")

    except ImportError as e:
        console.print(
            f"[red]Error: Could not import PyCodeKG[/red]\n"
            f"Details: {e}\n\n"
            "Make sure you are running inside the pycode_kg package environment."
        )
        logger.exception("Import error")
        raise


if __name__ == "__main__":
    main()
