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
    ``db_path``/``lancedb_path`` to ``.pycodekg/graph.sqlite`` and
    ``.pycodekg/lancedb``.
- Logging approach: uses Rich console output for user-facing status and
    standard ``logging`` for non-fatal diagnostic warnings.
- Error handling strategy: degrades gracefully when optional data is missing
    (for example missing database, git metadata, or snapshot history) and emits
    actionable warnings instead of failing hard where possible.

Usage:
    python pycodekg_thorough_analysis.py /path/to/repo /path/to/db .pycodekg/lancedb
"""

import datetime
import json
import logging
import os
import platform
import subprocess
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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
                from pycode_kg.analysis.centrality import (  # pylint: disable=import-outside-toplevel
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
            # --- Option A: seed from CodeRank top nodes (deterministic, no LanceDB) ---
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
                        caller_list = self.kg.callers(node_id, rel="CALLS")
                        caller_count = len(caller_list)
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
                        caller_list = self.kg.callers(node_id, rel="CALLS")
                        caller_count = len(caller_list)
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

    def _analyze_fan_out(self) -> None:
        """Phase 3: Find functions that call many others (fan-out).

        Analyzes functions in the function_metrics already identified,
        computing their actual fan-out by reverse-querying callee lists.
        Also identifies additional high-fanout orchestrator functions.
        """

        try:
            # For functions already identified, compute their fan-out
            for node_id, metrics in self.function_metrics.items():
                try:
                    # Get the node to see what it calls
                    node = self.kg.node(node_id)
                    if node is None:
                        continue

                    # Count CALLS edges outgoing from this node
                    # This is a rough estimate via the store; exact count requires
                    # querying the store directly
                    fanout_count = 0
                    # Try to get edges from the node
                    if hasattr(self.kg, "_store"):
                        edges = self.kg._store.edges_from(node_id, rel="CALLS", limit=100)
                        fanout_count = len(edges) if edges else 0

                    metrics.fan_out = fanout_count

                except (AttributeError, ValueError, RuntimeError) as e:
                    logger.debug(f"Could not compute fan-out for {node_id}: {e}")

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

                    # Estimate fan-out for new functions
                    fanout_count = 0
                    if hasattr(self.kg, "_store"):
                        try:
                            edges = self.kg._store.edges_from(node_id, rel="CALLS", limit=100)
                            fanout_count = len(edges) if edges else 0
                        except (AttributeError, ValueError, RuntimeError):
                            pass

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

    def _is_special_entry_point(self, node: dict) -> bool:
        """Check if a function is a special entry point that should be excluded from orphan detection.

        Special entry points are intentional zero-callers that serve as:
        - Protocol methods (__init__, __str__, __exit__, __enter__, etc.)
        - Property methods (@property decorator, accessed as attributes)
        - MCP tool functions decorated with @mcp.tool() in mcp_server.py
        - CLI command handlers decorated with @click.command or @cli.command

        These functions have zero internal callers because they're invoked by
        external frameworks (MCP protocol, Click CLI, Python runtime), not by
        regular code. Flagging them as orphans is a false positive.

        :param node: Node dictionary with keys: name, module, kind
        :return: True if this node should be excluded from orphan detection
        """
        name = node.get("name", "")
        module = node.get("module_path", "")

        # ===== PROTOCOL METHODS =====
        # Special methods like __init__, __str__, __exit__, __enter__, etc.
        # are invoked by Python's runtime machinery, not explicit code calls.
        if name.startswith("__") and name.endswith("__"):
            return True

        # ===== PROPERTY METHODS =====
        # Methods decorated with @property are accessed as attributes (snapshot.key),
        # not called as functions. The call graph only captures func() invocations,
        # so properties appear to have zero callers even when used extensively.
        # Known properties in the codebase:
        property_names = {"key"}  # Snapshot.key (accessed in snapshots.py: 3+ places)
        if name in property_names:
            return True

        # ===== MCP TOOL FUNCTIONS =====
        # Functions in mcp_server.py decorated with @mcp.tool() are dispatched
        # by the MCP protocol router, not by explicit Python call sites.
        if "mcp_server" in module:
            return True

        # ===== CLI COMMAND HANDLERS =====
        # Functions in cli modules that serve as command entry points.
        # These are decorated with @click.command or @cli.command and are
        # dispatched by Click's CLI router when users invoke the tool.
        if "/cli/" in module or module.endswith("cli.py"):
            return True

        return False

    def _analyze_dependencies(self) -> None:
        """Phase 4: Analyze module-level dependencies.

        Detects orphaned functions (zero callers), import cycles,
        and tight coupling patterns. Excludes special entry points (protocol
        methods and CLI commands) which have zero callers by design.
        """

        try:
            # Query for potential orphaned code
            result = self.kg.query(
                "unused dead code deprecated helper utility internal",
                k=15,
                hop=0,
                rels=("CONTAINS",),
            )

            for node in result.nodes:
                if node.get("kind") not in ["function", "method", "class"]:
                    continue

                node_id = node.get("id")
                if not node_id:
                    continue

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

                    # Functions with zero callers are flagged as orphaned,
                    # UNLESS they're special entry points (skip these).
                    if len(caller_list) == 0 and len(attr_list) == 0:
                        # Exclude protocol methods and CLI entry points
                        if self._is_special_entry_point(node):
                            logger.debug(
                                f"Skipping {node.get('name')} — "
                                f"special entry point (framework-driven)"
                            )
                            continue

                        metrics = FunctionMetrics(
                            node_id=node_id,
                            name=node.get("name", "unknown"),
                            module=node.get("module_path", "unknown"),
                            kind=node.get("kind", "unknown"),
                            fan_in=0,
                            fan_out=0,
                            lines=max(
                                0,
                                (node.get("end_lineno") or 0) - (node.get("lineno") or 0),
                            ),
                        )
                        self.orphaned_functions.append(metrics)

                except (AttributeError, ValueError, RuntimeError) as e:
                    logger.debug(f"Could not check callers for {node_id}: {e}")

            self._phase_result = f"{len(self.orphaned_functions)} orphaned functions"

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
                cohesion = min(1.0, len(outgoing) / (len(incoming) + len(outgoing) + 1))
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

                    # Trace forward from func through real CALLS edges.
                    chain_names = [func.name]
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
                            chain_names.append(callee.get("name", "?"))
                            chain_modules.append(callee.get("module_path", ""))
                        else:
                            break

                    # Prepend top caller to give the chain context.
                    if callers:
                        caller_module = callers[0].get("module_path", "")
                        chain_names = [callers[0].get("name", "?"), *chain_names]
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
        1. Parse every ``__init__.py`` under the repo root with AST to find
           re-exported names (``from X import Y`` / ``__all__`` entries).
           Look each name up in the graph and record it as a public API.
        2. Supplement with non-private functions/classes in ``function_metrics``
           that have at least one caller and are not already included.
        """

        try:
            import ast as _ast  # pylint: disable=import-outside-toplevel

            already_ids: set[str] = set()

            # --- Step 1: walk __init__.py files and collect re-exported names ---
            try:
                repo_root = Path(self.kg.repo_root)
                for init_path in sorted(repo_root.rglob("__init__.py")):
                    try:
                        src = init_path.read_text(encoding="utf-8")
                        tree = _ast.parse(src)
                    except (OSError, SyntaxError):
                        continue

                    exported_names: set[str] = set()

                    for node in _ast.walk(tree):
                        # from X import Y, Z  →  Y, Z are re-exported
                        if isinstance(node, _ast.ImportFrom):
                            for alias in node.names:
                                name = alias.asname or alias.name
                                if name and not name.startswith("_"):
                                    exported_names.add(name)
                        # __all__ = ["Foo", "bar"]
                        elif (
                            isinstance(node, _ast.Assign)
                            and any(
                                isinstance(t, _ast.Name) and t.id == "__all__" for t in node.targets
                            )
                            and isinstance(node.value, _ast.List | _ast.Tuple)
                        ):
                            for elt in node.value.elts:
                                if isinstance(elt, _ast.Constant) and isinstance(elt.value, str):
                                    exported_names.add(elt.value)

                    for name in exported_names:
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
            from pycode_kg.ranking.coderank import (  # pylint: disable=import-outside-toplevel
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
    # Option D: Phase 14 — CodeRank top-nodes report section
    # -------------------------------------------------------------------------

    def _analyze_coderank_section(self) -> None:
        """Phase 14: Prepare CodeRank top-nodes for the report.

        ``self.coderank_top_nodes`` was already populated by ``_compute_coderank``
        in Phase 1b.  This phase is a no-op if CodeRank failed; it exists so
        the report-writing logic has a clear hook and the phase numbering stays
        consistent.
        """
        if self.coderank_top_nodes:
            self._phase_result = f"{len(self.coderank_top_nodes)} top nodes"
        else:
            self._phase_result = "skipped (no data)"

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

        Requires the LanceDB vector index to be available (``self.kg`` must
        support ``query()``).  Degrades gracefully if the index is unavailable.
        """

        CONCERNS = [
            "configuration loading initialization setup",
            "data persistence storage database",
            "query search retrieval semantic",
            "graph traversal node edge",
        ]

        try:
            from pycode_kg.ranking.coderank import (  # pylint: disable=import-outside-toplevel
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

            for concern in CONCERNS:
                try:
                    # Get semantic scores from the vector index.
                    # Suppress tqdm progress bars from LanceDB embedding model loading.
                    import os as _os  # pylint: disable=import-outside-toplevel

                    _old_disable = _os.environ.get("TQDM_DISABLE")
                    _os.environ["TQDM_DISABLE"] = "1"
                    try:
                        query_result = self.kg.query(concern, k=8, hop=0, rels=("CONTAINS",))
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
                        logger.debug(f"No semantic seeds for concern: {concern!r}")
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
                        results.append({"concern": concern, "top_nodes": top_nodes})

                except (AttributeError, ValueError, RuntimeError) as e:
                    logger.debug(f"Concern query failed for {concern!r}: {e}")

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
            from pycode_kg.analysis.centrality import (  # pylint: disable=import-outside-toplevel
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
            names = ", ".join(f"`{f.name}`" for f in self.orphaned_functions)
            self.issues.append(
                f"[WARN] {len(self.orphaned_functions)} orphaned functions found "
                f"({names}) -- consider archiving or documenting"
            )

        if len(self.high_fanout_functions) > 0:
            self.issues.append(
                f"[WARN] {len(self.high_fanout_functions)} functions with high fan-out "
                "-- potential orchestrators or god objects"
            )

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

        Scoring (100 points total):
        - Docstring coverage (0–40 pts): ≥80% → 40, ≥50% → 20, else 0
        - Orphaned functions (0–25 pts): 0 → 25, 1–2 → 15, 3–5 → 5, else 0
        - High fan-out functions (0–20 pts): 0 → 20, 1–2 → 12, else 4
        - Circular dependencies (0–15 pts): 0 → 15, 1 → 8, else 0

        :return: Tuple of (score 0–100, letter grade A–F, label string)
        """
        score = 0.0

        # Docstring coverage
        cov = self.docstring_coverage
        if cov:
            pct = cov.get("coverage_pct", 0)
            if pct >= 80:
                score += 40
            elif pct >= 50:
                score += 20

        # Orphaned functions
        n_orphaned = len(self.orphaned_functions)
        if n_orphaned == 0:
            score += 25
        elif n_orphaned <= 2:
            score += 15
        elif n_orphaned <= 5:
            score += 5

        # High fan-out functions
        n_fanout = len(self.high_fanout_functions)
        if n_fanout == 0:
            score += 20
        elif n_fanout <= 2:
            score += 12
        else:
            score += 4

        # Circular dependencies
        n_circular = len(self.circular_deps)
        if n_circular == 0:
            score += 15
        elif n_circular == 1:
            score += 8

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
                f"**Remove or archive orphaned functions** — {names}{suffix} have zero callers "
                "and add maintenance burden"
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
            from pycode_kg import (  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
                __version__ as _v,
            )

            version = f"pycode-kg {_v}"
        except (ImportError, AttributeError):
            try:
                from importlib.metadata import (  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
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
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
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
        """Generate comprehensive markdown report with tables and analysis.

        :param report_path: Path to write the markdown report to
        :param elapsed_seconds: Total analysis duration in seconds
        """
        report_date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        stats = self.stats
        repo_name = self.kg.repo_root.name
        quality_score, quality_grade, quality_label = self._compute_quality_grade()
        grade_emoji = {"A": "[A]", "B": "[B]", "C": "[C]", "D": "[D]", "F": "[F]"}.get(
            quality_grade, "[ ]"
        )

        metadata_block = self._get_report_metadata(elapsed_seconds=elapsed_seconds)

        # Build comprehensive report
        report = (
            metadata_block
            + f"""# {repo_name} Analysis

**Generated:** {report_date}

---

## Executive Summary

This report provides a comprehensive architectural analysis of the **{repo_name}** repository using PyCodeKG's knowledge graph. The analysis covers complexity hotspots, module coupling, key call chains, and code quality signals to guide refactoring and architecture decisions.

| Overall Quality | Grade | Score |
|----------------|-------|-------|
| {grade_emoji} **{quality_label}** | **{quality_grade}** | {quality_score:.0f} / 100 |

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| **Total Nodes** | {stats.get("total_nodes", "N/A")} |
| **Total Edges** | {stats.get("total_edges", "N/A")} |
| **Modules** | {len(self.module_metrics)} (of {stats.get("node_counts", {}).get("module", "?")} total) |
| **Functions** | {stats.get("node_counts", {}).get("function", "N/A")} |
| **Classes** | {stats.get("node_counts", {}).get("class", "N/A")} |
| **Methods** | {stats.get("node_counts", {}).get("method", "N/A")} |

### Edge Distribution

| Relationship Type | Count |
|-------------------|-------|
| CALLS | {stats.get("edge_counts", {}).get("CALLS", 0)} |
| CONTAINS | {stats.get("edge_counts", {}).get("CONTAINS", 0)} |
| IMPORTS | {stats.get("edge_counts", {}).get("IMPORTS", 0)} |
| ATTR_ACCESS | {stats.get("edge_counts", {}).get("ATTR_ACCESS", 0)} |
| INHERITS | {stats.get("edge_counts", {}).get("INHERITS", 0)} |

---

## Fan-In Ranking

Most-called functions are potential bottlenecks or core functionality. These functions are heavily depended upon across the codebase.

| # | Function | Module | Callers |
|---|----------|--------|---------|
"""
        )

        for i, metrics in enumerate(
            sorted(self.function_metrics.values(), key=lambda m: m.fan_in, reverse=True)[:15],
            1,
        ):
            report += f"| {i} | `{metrics.name}()` | {metrics.module} | **{metrics.fan_in}** |\n"

        report += """

**Insight:** Functions with high fan-in are either core APIs or bottlenecks. Review these for:
- Thread safety and performance
- Clear documentation and contracts
- Potential for breaking changes

---

## High Fan-Out Functions (Orchestrators)

Functions that call many others may indicate complex orchestration logic or poor separation of concerns.

"""

        if self.high_fanout_functions:
            report += """| # | Function | Module | Calls | Type |
|---|----------|--------|-------|------|
"""
            for i, func in enumerate(
                sorted(self.high_fanout_functions, key=lambda f: f.fan_out, reverse=True)[:10],
                1,
            ):
                func_type = "Orchestrator" if func.fan_out > 50 else "Coordinator"
                report += (
                    f"| {i} | `{func.name}()` | {func.module} | "
                    f"**{func.fan_out}** | {func_type} |\n"
                )
            report += "\n"
        else:
            report += "No extreme high fan-out functions detected. Well-balanced architecture.\n\n"

        report += """---

## Module Architecture

Top modules by dependency coupling and cohesion (showing up to 10 with activity).
Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.

"""

        if self.module_metrics:
            report += """| Module | Functions | Classes | Incoming | Outgoing | Cohesion |
|--------|-----------|---------|----------|----------|----------|
"""
            for module, module_metric in sorted(
                self.module_metrics.items(),
                key=lambda x: x[1].functions + x[1].classes + x[1].methods,
                reverse=True,
            )[:10]:
                report += (
                    f"| `{module}` | {module_metric.functions} | {module_metric.classes} | "
                    f"{len(module_metric.incoming_deps)} | {len(module_metric.outgoing_deps)} | "
                    f"{module_metric.cohesion_score:.2f} |\n"
                )
            report += "\n"

        report += """---

## Key Call Chains

Deepest call chains in the codebase.

"""

        if self.critical_paths:
            for i, chain in enumerate(self.critical_paths[:5], 1):
                chain_str = " → ".join(chain.chain)
                report += f"**Chain {i}** (depth: {chain.depth})\n\n```\n{chain_str}\n```\n\n"
        else:
            report += "No deep call chains detected.\n\n"

        report += """---

## Public API Surface

Identified public APIs (module-level functions with high usage).

"""

        if self.public_apis:
            report += """| Function | Module | Fan-In | Type |
|----------|--------|--------|------|
"""
            for api in sorted(self.public_apis, key=lambda a: a.fan_in, reverse=True)[:10]:
                report += f"| `{api.name}()` | {api.module} | {api.fan_in} | {api.kind} |\n"
        else:
            report += "No public APIs identified.\n\n"

        # --- Docstring Coverage section ---
        cov = self.docstring_coverage
        if cov:
            overall_pct = cov["coverage_pct"]
            pct_bar = "[OK]" if overall_pct >= 80 else "[WARN]" if overall_pct >= 50 else "[LOW]"
            report += """---

## Docstring Coverage

Docstring coverage directly determines semantic retrieval quality. Nodes without
docstrings embed only structured identifiers (`KIND/NAME/QUALNAME/MODULE`), where
keyword search is as effective as vector embeddings. The semantic model earns its
value only when a docstring is present.

| Kind | Documented | Total | Coverage |
|------|-----------|-------|----------|
"""
            for kind in ("function", "method", "class", "module"):
                if kind in cov["by_kind"]:
                    k = cov["by_kind"][kind]
                    kind_pct = (k["with_doc"] / k["total"] * 100) if k["total"] else 0.0
                    kind_bar = "[OK]" if kind_pct >= 80 else "[WARN]" if kind_pct >= 50 else "[LOW]"
                    report += (
                        f"| `{kind}` | {k['with_doc']} | {k['total']} | "
                        f"{kind_bar} {kind_pct:.1f}% |\n"
                    )
            report += (
                f"| **total** | **{cov['with_doc']}** | **{cov['total']}** | "
                f"**{pct_bar} {overall_pct:.1f}%** |\n\n"
            )

            if overall_pct < 80:
                undocumented = cov["total"] - cov["with_doc"]
                report += (
                    f"> **Recommendation:** {undocumented} nodes lack docstrings. "
                    "Prioritize documenting high-fan-in functions and public API surface "
                    "first — these have the highest impact on query accuracy.\n\n"
                )
        else:
            report += "---\n\n## Docstring Coverage\n\nCoverage data not available.\n\n"

        # --- Structural Importance Ranking section (module-level) ---
        report += "---\n\n## Structural Importance Ranking (SIR)\n\n"
        if self.centrality_modules:
            report += (
                "Weighted PageRank aggregated by module — reveals architectural spine. "
                "Cross-module edges boosted 1.5×; private symbols penalized 0.85×. "
                "Node-level detail: `pycodekg centrality --top 25`\n\n"
            )
            report += "| Rank | Score | Members | Module |\n"
            report += "|------|-------|---------|--------|\n"
            for m in self.centrality_modules[:15]:
                report += (
                    f"| {m['rank']} | {m['score']:.6f} | {m['member_count']} "
                    f"| `{m['module_path']}` |\n"
                )
            report += "\n"
        else:
            report += "Centrality data not available.\n\n"

        issues_text = (
            "\n".join(f"- {issue}" for issue in self.issues)
            if self.issues
            else "- No major issues detected"
        )
        strengths_text = (
            "\n".join(f"- {strength}" for strength in self.strengths)
            if self.strengths
            else "- Continue monitoring code quality"
        )

        report += f"""

---

## Code Quality Issues

{issues_text}

---

## Architectural Strengths

{strengths_text}

---

## Recommendations

{self._build_recommendations()}

---

## Inheritance Hierarchy

"""
        inh = self.inheritance_analysis
        if inh and inh.get("total_inherits_edges", 0) > 0:
            report += (
                f"**{inh['total_inherits_edges']}** INHERITS edges across "
                f"**{len(inh['classes'])}** classes. "
                f"Max depth: **{inh['max_depth']}**.\n\n"
            )
            report += "| Class | Module | Depth | Parents | Children |\n"
            report += "|-------|--------|-------|---------|----------|\n"
            for cls in inh["classes"][:20]:
                report += (
                    f"| `{cls['name']}` | {cls['module']} "
                    f"| {cls['depth']} | {cls['parent_count']} | {cls['child_count']} |\n"
                )
            if inh.get("multiple_inheritance"):
                report += (
                    f"\n### Multiple Inheritance ({len(inh['multiple_inheritance'])} classes)\n\n"
                )
                for mi in inh["multiple_inheritance"]:
                    bases = ", ".join(f"`{b}`" for b in mi["bases"])
                    report += f"- `{mi['class']}` ({mi['module']}) inherits from {bases}\n"
            if inh.get("diamonds"):
                report += f"\n### Diamond Patterns ({len(inh['diamonds'])} detected)\n\n"
                for d in inh["diamonds"]:
                    common = ", ".join(f"`{a}`" for a in d["common_ancestors"])
                    report += f"- `{d['class']}` ({d['module']}) — common ancestor(s): {common}\n"
        else:
            report += "No inheritance edges (no class hierarchies).\n"

        # --- Snapshot History section ---
        report += "\n\n---\n\n## Snapshot History\n\n"
        if self.snapshot_history:
            report += (
                "Recent snapshots in reverse chronological order. "
                "Δ columns show change vs. the immediately preceding snapshot.\n\n"
            )
            report += (
                "| # | Timestamp | Branch | Version | Nodes | Edges | Coverage"
                " | Δ Nodes | Δ Edges | Δ Coverage |\n"
            )
            report += (
                "|---|-----------|--------|---------|-------|-------|----------"
                "|---------|---------|------------|\n"
            )
            for i, snap in enumerate(self.snapshot_history, 1):
                ts = snap.get("timestamp", "")[:19].replace("T", " ")
                branch = snap.get("branch", "?")
                version = snap.get("version", "?")
                m = snap.get("metrics", {})
                nodes = m.get("total_nodes", "?")
                edges = m.get("total_edges", "?")
                cov_raw = m.get("docstring_coverage", None)
                cov_str = f"{cov_raw * 100:.1f}%" if cov_raw is not None else "?"

                delta = (snap.get("deltas") or {}).get("vs_previous") or {}
                dn = delta.get("nodes")
                de = delta.get("edges")
                dc = delta.get("coverage_delta")
                dn_str = f"{dn:+d}" if dn is not None else "—"
                de_str = f"{de:+d}" if de is not None else "—"
                dc_str = f"{dc * 100:+.1f}%" if dc is not None else "—"

                report += (
                    f"| {i} | {ts} | {branch} | {version} | {nodes} | {edges}"
                    f" | {cov_str} | {dn_str} | {de_str} | {dc_str} |\n"
                )
        else:
            report += "No snapshots found. Run `pycodekg snapshot save <version>` to capture one.\n"

        report += """

---

## Appendix: Orphaned Code

Functions with zero callers (potential dead code):

"""

        if self.orphaned_functions:
            report += """| Function | Module | Lines |
|----------|--------|-------|
"""
            for func in sorted(self.orphaned_functions, key=lambda f: f.lines, reverse=True)[:15]:
                report += f"| `{func.name}()` | {func.module} | {func.lines} |\n"
        else:
            report += "No orphaned functions detected.\n"

        # --- CodeRank Top Nodes section (Option D) ---
        report += "---\n\n## CodeRank -- Global Structural Importance\n\n"
        if self.coderank_top_nodes:
            report += (
                "Weighted PageRank over CALLS + IMPORTS + INHERITS edges "
                "(test paths excluded). Scores are normalized to sum to 1.0. "
                "This ranking seeds Phase 2 fan-in discovery and Phase 15 concern queries.\n\n"
            )
            report += "| Rank | Score | Kind | Name | Module |\n"
            report += "|------|-------|------|------|--------|\n"
            for i, n in enumerate(self.coderank_top_nodes[:20], 1):
                report += (
                    f"| {i} | {n['score']:.6f} | {n['kind']} "
                    f"| `{n['qualname'] or n['name']}` | {n['module_path']} |\n"
                )
            report += "\n"
        else:
            report += "CodeRank data not available.\n\n"

        # --- Concern-based Hybrid Ranking section (Option D) ---
        report += "---\n\n## Concern-Based Hybrid Ranking\n\n"
        if self.concern_analysis:
            report += (
                "Top structurally-dominant nodes per architectural concern "
                "(0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).\n\n"
            )
            for entry in self.concern_analysis:
                concern = entry["concern"]
                report += f"### {concern.title()}\n\n"
                report += "| Rank | Score | Kind | Name | Module |\n"
                report += "|------|-------|------|------|--------|\n"
                for n in entry["top_nodes"]:
                    report += (
                        f"| {n['rank']} | {n['score']} | {n['kind']} "
                        f"| `{n['name']}` | {n['module']} |\n"
                    )
                report += "\n"
        else:
            report += "Concern analysis not available.\n\n"

        elapsed_str = (
            f"{elapsed_seconds:.1f}s" if elapsed_seconds < 60 else f"{elapsed_seconds / 60:.1f}m"
        )
        report += f"""

---

*Report generated by PyCodeKG Thorough Analysis Tool — analysis completed in {elapsed_str}*
"""

        Path(report_path).write_text(report)
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
        return {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "statistics": self.stats,
            "docstring_coverage": self.docstring_coverage,
            "function_metrics": {k: asdict(v) for k, v in sorted_fn},
            "module_metrics": {k: asdict(v) for k, v in active_modules.items()},
            "orphaned_functions": [asdict(f) for f in self.orphaned_functions],
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

    def to_markdown(self) -> str:
        """
        Render the analysis results as a Markdown context document.

        Similar to `SnippetPack.to_markdown()`, this produces a structured
        Markdown document with sections for each analysis phase:
        baseline metrics, complexity hotspots, high fan-out functions,
        module architecture, critical paths, public APIs, docstring coverage,
        issues, and strengths.

        The output is optimized for LLM ingestion with clear headers, tables,
        and organized sections.

        :return: Markdown-formatted string representing the full analysis.
        """
        out: list[str] = []
        stats = self.stats

        out.append("# PyCodeKG Repository Analysis\n")
        out.append(f"**Generated:** {datetime.datetime.now(datetime.UTC).isoformat()}  \n")
        out.append("\n---\n")

        # Baseline Metrics
        out.append("## Baseline Metrics\n")
        out.append("| Metric | Value |")
        out.append("|--------|-------|")
        out.append(f"| Total Nodes | {stats.get('total_nodes', 'N/A')} |")
        out.append(f"| Total Edges | {stats.get('total_edges', 'N/A')} |")
        total_modules = stats.get("node_counts", {}).get("module", "?")
        out.append(f"| Modules | {len(self.module_metrics)} (of {total_modules} total) |")
        out.append(f"| Functions | {stats.get('node_counts', {}).get('function', 'N/A')} |")
        out.append(f"| Classes | {stats.get('node_counts', {}).get('class', 'N/A')} |")
        out.append(f"| Methods | {stats.get('node_counts', {}).get('method', 'N/A')} |")
        out.append("")

        out.append("### Edge Distribution")
        out.append("| Relationship | Count |")
        out.append("|---|---|")
        for rel in ("CALLS", "CONTAINS", "IMPORTS", "ATTR_ACCESS", "INHERITS"):
            count = stats.get("edge_counts", {}).get(rel, 0)
            out.append(f"| {rel} | {count} |")
        out.append("")

        # Fan-In Ranking
        out.append("## Fan-In Ranking\n")
        if self.function_metrics:
            out.append(
                "Most-called functions and methods "
                "(classes omitted — instantiation counts are not architectural signals).\n"
            )
            out.append("| # | Kind | Function | Module | Callers |")
            out.append("|---|---|---|---|---|")
            ranked_fan_in = [
                m
                for m in sorted(
                    self.function_metrics.values(), key=lambda m: m.fan_in, reverse=True
                )
                if m.kind != "class"
            ][:15]
            for i, metrics in enumerate(ranked_fan_in, 1):
                out.append(
                    f"| {i} | {metrics.kind} | `{metrics.name}()` | {metrics.module} | {metrics.fan_in} |"
                )
        else:
            out.append("No high fan-in functions identified.\n")
        out.append("")

        # High Fan-Out Functions
        out.append("## High Fan-Out Functions (Orchestrators)\n")
        if self.high_fanout_functions:
            out.append(
                "Functions that call many others may indicate complex orchestration logic.\n"
            )
            out.append("| # | Function | Module | Calls | Type |")
            out.append("|---|---|---|---|---|")
            for i, func in enumerate(
                sorted(self.high_fanout_functions, key=lambda f: f.fan_out, reverse=True)[:10],
                1,
            ):
                func_type = "Orchestrator" if func.fan_out > 50 else "Coordinator"
                out.append(
                    f"| {i} | `{func.name}()` | {func.module} | {func.fan_out} | {func_type} |"
                )
        else:
            out.append("No high fan-out functions detected. Well-balanced architecture.\n")
        out.append("")

        # Module Architecture
        out.append("## Module Architecture\n")
        out.append(
            "Cohesion = incoming / (incoming + outgoing + 1); higher = more internally focused.\n"
        )
        if self.module_metrics:
            total_modules = len(self.module_metrics)
            cap = min(10, total_modules)
            out.append(
                f"Top modules by dependency coupling and cohesion (showing {cap} of {total_modules} total).\n"
            )
            out.append("| Module | Functions | Classes | Incoming | Outgoing | Cohesion |")
            out.append("|---|---|---|---|---|---|")
            for module, module_metric in sorted(
                self.module_metrics.items(),
                key=lambda x: x[1].functions + x[1].classes + x[1].methods,
                reverse=True,
            )[:cap]:
                out.append(
                    f"| `{module}` | {module_metric.functions} | {module_metric.classes} | "
                    f"{len(module_metric.incoming_deps)} | {len(module_metric.outgoing_deps)} | "
                    f"{module_metric.cohesion_score:.2f} |"
                )
        else:
            out.append("No module metrics available.\n")
        out.append("")

        # Key Call Chains
        out.append("## Key Call Chains\n")
        if self.critical_paths:
            out.append("Deepest call chains in the codebase.\n")
            for i, chain in enumerate(self.critical_paths[:5], 1):
                chain_str = " → ".join(chain.chain)
                out.append(f"**Chain {i}** (depth: {chain.depth})\n")
                out.append(f"```\n{chain_str}\n```\n")
        else:
            out.append("No deep call chains detected.\n")
        out.append("")

        # Public API Surface
        out.append("## Public API Surface\n")
        if self.public_apis:
            out.append("| Function | Module | Fan-In |")
            out.append("|---|---|---|")
            for api in sorted(self.public_apis, key=lambda a: a.fan_in, reverse=True)[:10]:
                out.append(f"| `{api.name}()` | {api.module} | {api.fan_in} |")
        else:
            out.append("No public APIs identified.\n")
        out.append("")

        # Docstring Coverage
        out.append("## Docstring Coverage\n")
        cov = self.docstring_coverage
        if cov:
            overall_pct = cov["coverage_pct"]
            pct_bar = "[OK]" if overall_pct >= 80 else "[WARN]" if overall_pct >= 50 else "[LOW]"
            out.append("| Kind | Documented | Total | Coverage |")
            out.append("|---|---|---|---|")
            for kind in ("function", "method", "class", "module"):
                if kind in cov["by_kind"]:
                    k = cov["by_kind"][kind]
                    kind_pct = (k["with_doc"] / k["total"] * 100) if k["total"] else 0.0
                    kind_bar = "[OK]" if kind_pct >= 80 else "[WARN]" if kind_pct >= 50 else "[LOW]"
                    out.append(
                        f"| `{kind}` | {k['with_doc']} | {k['total']} | {kind_bar} {kind_pct:.1f}% |"
                    )
            out.append(
                f"| **total** | **{cov['with_doc']}** | **{cov['total']}** | "
                f"**{pct_bar} {overall_pct:.1f}%** |"
            )
        else:
            out.append("Coverage data not available.\n")
        out.append("")

        # Structural Importance Ranking (module-level)
        out.append("## Structural Importance Ranking (SIR)\n")
        if self.centrality_modules:
            out.append(
                "Weighted PageRank aggregated by module — reveals architectural spine. "
                "Cross-module edges boosted 1.5×; private symbols penalized 0.85×. "
                "Node-level detail: `pycodekg centrality --top 25`\n"
            )
            out.append("| Rank | Score | Members | Module |")
            out.append("|------|-------|---------|--------|")
            for m in self.centrality_modules[:15]:
                out.append(
                    f"| {m['rank']} | {m['score']:.6f} | {m['member_count']} "
                    f"| `{m['module_path']}` |"
                )
        else:
            out.append("Centrality data not available.\n")
        out.append("")

        # Issues
        out.append("## Code Quality Issues\n")
        if self.issues:
            for issue in self.issues:
                out.append(f"- {issue}")
        else:
            out.append("- No major issues detected")
        out.append("")

        # Strengths
        out.append("## Architectural Strengths\n")
        if self.strengths:
            for strength in self.strengths:
                out.append(f"- {strength}")
        else:
            out.append("- Continue monitoring code quality")
        out.append("")

        # Inheritance Hierarchy
        inh = self.inheritance_analysis
        out.append("## Inheritance Hierarchy\n")
        if inh and inh.get("total_inherits_edges", 0) > 0:
            out.append(
                f"**{inh['total_inherits_edges']}** INHERITS edges across "
                f"**{len(inh['classes'])}** classes. "
                f"Max depth: **{inh['max_depth']}**.\n"
            )
            out.append("| Class | Module | Depth | Parents | Children |")
            out.append("|-------|--------|-------|---------|----------|")
            for cls in inh["classes"][:20]:
                out.append(
                    f"| `{cls['name']}` | {cls['module']} "
                    f"| {cls['depth']} | {cls['parent_count']} | {cls['child_count']} |"
                )
            out.append("")
            if inh.get("multiple_inheritance"):
                out.append(
                    f"### Multiple Inheritance ({len(inh['multiple_inheritance'])} classes)\n"
                )
                for mi in inh["multiple_inheritance"]:
                    bases = ", ".join(f"`{b}`" for b in mi["bases"])
                    out.append(f"- `{mi['class']}` ({mi['module']}) inherits from {bases}")
                out.append("")
            if inh.get("diamonds"):
                out.append(f"### Diamond Patterns ({len(inh['diamonds'])} detected)\n")
                for d in inh["diamonds"]:
                    common = ", ".join(f"`{a}`" for a in d["common_ancestors"])
                    out.append(f"- `{d['class']}` ({d['module']}) — common ancestor(s): {common}")
                out.append("")
        else:
            out.append("No inheritance edges (no class hierarchies in this codebase).\n")
        out.append("")

        # Snapshot History
        out.append("## Snapshot History\n")
        if self.snapshot_history:
            out.append(
                "Recent snapshots (reverse chronological). "
                "Δ columns show change vs. the immediately preceding snapshot.\n"
            )
            out.append(
                "| # | Timestamp | Branch | Version | Nodes | Edges | Coverage"
                " | Δ Nodes | Δ Edges | Δ Coverage |"
            )
            out.append(
                "|---|-----------|--------|---------|-------|-------|----------"
                "|---------|---------|------------|"
            )
            for i, snap in enumerate(self.snapshot_history, 1):
                ts = snap.get("timestamp", "")[:19].replace("T", " ")
                branch = snap.get("branch", "?")
                version = snap.get("version", "?")
                m = snap.get("metrics", {})
                nodes = m.get("total_nodes", "?")
                edges = m.get("total_edges", "?")
                cov_raw = m.get("docstring_coverage", None)
                cov_str = f"{cov_raw * 100:.1f}%" if cov_raw is not None else "?"

                delta = (snap.get("deltas") or {}).get("vs_previous") or {}
                dn = delta.get("nodes")
                de = delta.get("edges")
                dc = delta.get("coverage_delta")
                dn_str = f"{dn:+d}" if dn is not None else "—"
                de_str = f"{de:+d}" if de is not None else "—"
                dc_str = f"{dc * 100:+.1f}%" if dc is not None else "—"

                out.append(
                    f"| {i} | {ts} | {branch} | {version} | {nodes} | {edges}"
                    f" | {cov_str} | {dn_str} | {de_str} | {dc_str} |"
                )
        else:
            out.append(
                "No snapshots found. Run `pycodekg snapshot save <version>` to capture one.\n"
            )
        out.append("")

        # Orphaned Functions
        out.append("## Orphaned Code\n")
        if self.orphaned_functions:
            out.append("Functions with zero callers (potential dead code).\n")
            out.append("| Function | Module | Lines |")
            out.append("|---|---|---|")
            for func in sorted(self.orphaned_functions, key=lambda f: f.lines, reverse=True)[:15]:
                out.append(f"| `{func.name}()` | {func.module} | {func.lines} |")
        else:
            out.append("No orphaned functions detected.\n")
        out.append("")

        # CodeRank Top Nodes (Option D)
        out.append("## CodeRank -- Global Structural Importance\n")
        if self.coderank_top_nodes:
            out.append(
                "Weighted PageRank over CALLS + IMPORTS + INHERITS edges "
                "(test paths excluded). Scores normalized to sum to 1.0.\n"
            )
            out.append("| Rank | Score | Kind | Name | Module |")
            out.append("|------|-------|------|------|--------|")
            for i, n in enumerate(self.coderank_top_nodes[:20], 1):
                out.append(
                    f"| {i} | {n['score']:.6f} | {n['kind']} "
                    f"| `{n['qualname'] or n['name']}` | {n['module_path']} |"
                )
        else:
            out.append("CodeRank data not available.\n")
        out.append("")

        # Concern-based Hybrid Ranking (Option D)
        out.append("## Concern-Based Hybrid Ranking\n")
        if self.concern_analysis:
            out.append(
                "Top structurally-dominant nodes per architectural concern "
                "(0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).\n"
            )
            for entry in self.concern_analysis:
                concern = entry["concern"]
                out.append(f"### {concern.title()}\n")
                out.append("| Rank | Score | Kind | Name | Module |")
                out.append("|------|-------|------|------|--------|")
                for n in entry["top_nodes"]:
                    out.append(
                        f"| {n['rank']} | {n['score']} | {n['kind']} "
                        f"| `{n['name']}` | {n['module']} |"
                    )
                out.append("")
        else:
            out.append("Concern analysis not available.\n")
        out.append("")

        return "\n".join(out)

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
    lancedb_path: str | None = None,
    report_path: str | None = None,
    json_path: str | None = None,
    quiet: bool = False,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
    persist_centrality: bool = False,
) -> None:
    """Main entry point.

    Paths for ``db_path`` and ``lancedb_path`` default to the standard
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
    :param lancedb_path: Path to LanceDB vector index; default ``.pycodekg/lancedb``
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
    lancedb = Path(lancedb_path) if lancedb_path else root / ".pycodekg" / "lancedb"
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
        from pycode_kg import PyCodeKG  # pylint: disable=import-outside-toplevel

        console.print(f"[dim]Repo   : {root}[/dim]")
        console.print(f"[dim]DB     : {db}[/dim]")
        console.print(f"[dim]LanceDB: {lancedb}[/dim]")
        console.print(f"[dim]Report : {md_out}[/dim]")
        console.print()

        kg = PyCodeKG(repo_root=root, db_path=db, lancedb_dir=lancedb)

        snapshots_dir = root / ".pycodekg" / "snapshots"
        snap_mgr = SnapshotManager(snapshots_dir) if snapshots_dir.exists() else None

        # Resolve effective include/exclude dirs: prefer explicit args, fall back to pyproject.toml
        from pycode_kg.config import (  # pylint: disable=import-outside-toplevel
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
