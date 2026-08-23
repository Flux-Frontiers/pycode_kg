"""report.py — Markdown renderer for the thorough-analysis report.

The analyzer (:class:`~pycode_kg.pycodekg_thorough_analysis.PyCodeKGAnalyzer`)
computes metrics into plain dataclasses and dicts; this module turns that
state into the Markdown report.  Keeping the ~550 lines of section emitters
here means the analyzer holds only analysis phases, and the two halves are
testable independently.  Tables come from :func:`pycode_kg.render.md_table`.

``render_markdown(analyzer)`` is duck-typed on the analyzer's attributes —
it imports nothing from the analyzer module, so there is no import cycle.

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

from __future__ import annotations

import datetime
from pathlib import Path

from pycode_kg.render import md_table

_EDGE_RELS = ("CALLS", "CONTAINS", "IMPORTS", "ATTR_ACCESS", "INHERITS")

# A single depth-3 chain carries no signal — show the section only once the
# chains clear one of these bars.
_MIN_CALL_CHAIN_DEPTH = 4
_MIN_CALL_CHAIN_COUNT = 3


def _sym(name: str, kind: str) -> str:
    """Render a symbol as inline code, with call parens only for callables.

    :param name: Symbol name or qualname.
    :param kind: Node kind (``function``, ``method``, ``class``, ...).
    :return: Backticked name, suffixed with ``()`` for functions and methods.
    """
    return f"`{name}()`" if kind in ("function", "method") else f"`{name}`"


def _bar(pct: float) -> str:
    """Render a coverage percentage as a severity tag.

    :param pct: Coverage percentage in the range 0-100.
    :return: ``[OK]`` at 80+, ``[WARN]`` at 50+, otherwise ``[LOW]``.
    """
    return "[OK]" if pct >= 80 else "[WARN]" if pct >= 50 else "[LOW]"


def _snapshot_row(index: int, snap: dict) -> tuple:
    """Flatten one snapshot record into a Snapshot History table row.

    :param index: 1-based row number.
    :param snap: Snapshot dict with ``timestamp``, ``branch``, ``version``,
        ``metrics``, and an optional ``deltas.vs_previous`` block.
    :return: Tuple of pre-formatted cells matching the history table columns.
    """
    m = snap.get("metrics", {})
    cov_raw = m.get("docstring_coverage")
    delta = (snap.get("deltas") or {}).get("vs_previous") or {}
    dn, de, dc = delta.get("nodes"), delta.get("edges"), delta.get("coverage_delta")
    return (
        index,
        snap.get("timestamp", "")[:19].replace("T", " "),
        snap.get("branch", "?"),
        snap.get("version", "?"),
        m.get("total_nodes", "?"),
        m.get("total_edges", "?"),
        f"{cov_raw * 100:.1f}%" if cov_raw is not None else "?",
        f"{dn:+d}" if dn is not None else "—",
        f"{de:+d}" if de is not None else "—",
        f"{dc * 100:+.1f}%" if dc is not None else "—",
    )


def render_markdown(analyzer, *, metadata: str = "", elapsed_seconds: float | None = None) -> str:
    """
    Render the full analysis as a Markdown document.

    This is the single renderer behind every output surface: the CLI report
    file (via :meth:`_write_report`), the ``analyze_repo()`` MCP tool, and
    :meth:`PyCodeKG.analyze`.  One implementation is deliberate — the report
    and the MCP tool previously rendered the same data through two separate
    bodies, and they drifted (classes leaked into the fan-in table on one
    path but not the other) with nothing to catch it.

    :param metadata: Optional run-provenance blockquote to prepend (version,
        commit, platform).  Omitted when empty.
    :param elapsed_seconds: Analysis duration.  When given, a timing footer
        is appended; when ``None`` the footer is omitted.
    :return: Markdown-formatted string representing the full analysis.
    """
    stats = analyzer.stats
    repo_name = Path(analyzer.kg.repo_root).name
    quality_score, quality_grade, quality_label = analyzer._compute_quality_grade()
    grade_tag = {"A": "[A]", "B": "[B]", "C": "[C]", "D": "[D]", "F": "[F]"}.get(
        quality_grade, "[ ]"
    )
    generated = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    out: list[str] = []
    if metadata:
        out += [metadata.rstrip("\n"), ""]

    def rule() -> None:
        out.extend(["", "---", ""])

    out += [f"# {repo_name} Analysis", "", f"**Generated:** {generated}"]
    rule()

    # ── Executive Summary ────────────────────────────────────────────────
    out += [
        "## Executive Summary",
        "",
        f"This report provides a comprehensive architectural analysis of the "
        f"**{repo_name}** repository using PyCodeKG's knowledge graph. The analysis "
        "covers complexity hotspots, module coupling, key call chains, and code "
        "quality signals to guide refactoring and architecture decisions.",
        "",
    ]
    out += md_table(
        ["Overall Quality", "Grade", "Score"],
        [
            (
                f"{grade_tag} **{quality_label}**",
                f"**{quality_grade}**",
                f"{quality_score:.1f} / 100",
            )
        ],
    )
    if analyzer.grade_components:
        out += [
            "",
            "Score components:",
            "",
        ]
        out += md_table(
            ["Component", "Points", "Max", "Basis"],
            [
                (c["name"], f"{c['points']:.1f}", c["max"], c["basis"])
                for c in analyzer.grade_components
            ],
            aligns="lrrl",
        )
    rule()

    # ── Baseline Metrics ─────────────────────────────────────────────────
    node_counts = stats.get("node_counts", {})
    out += ["## Baseline Metrics", ""]
    out += md_table(
        ["Metric", "Value"],
        [
            ("**Total Nodes**", stats.get("total_nodes", "N/A")),
            ("**Total Edges**", stats.get("total_edges", "N/A")),
            (
                "**Modules**",
                f"{len(analyzer.module_metrics)} (of {node_counts.get('module', '?')} total)",
            ),
            ("**Functions**", node_counts.get("function", "N/A")),
            ("**Classes**", node_counts.get("class", "N/A")),
            ("**Methods**", node_counts.get("method", "N/A")),
        ],
    )
    out += ["", "### Edge Distribution", ""]
    edge_counts = stats.get("edge_counts", {})
    out += md_table(
        ["Relationship Type", "Count"],
        [(rel, edge_counts.get(rel, 0)) for rel in _EDGE_RELS],
        aligns="lr",
    )
    rule()

    # ── Fan-In Ranking ───────────────────────────────────────────────────
    # Classes are excluded deliberately: their "callers" are instantiation
    # sites, which measure how often the type is constructed, not how central
    # the definition is.  Mixing them into a callable fan-in ranking makes a
    # frequently-constructed dataclass outrank the real hot paths.
    out += [
        "## Fan-In Ranking",
        "",
        "Most-called functions and methods — potential bottlenecks or core "
        "functionality.  Classes are omitted: instantiation counts are not "
        "architectural fan-in.",
        "",
    ]
    all_fan_in = [
        m
        for m in sorted(analyzer.function_metrics.values(), key=lambda m: m.fan_in, reverse=True)
        if m.kind != "class"
    ]
    ranked_fan_in = all_fan_in[:15]
    if len(all_fan_in) > len(ranked_fan_in):
        out[-2] += f"  Top {len(ranked_fan_in)} of {len(all_fan_in)} shown."
    if ranked_fan_in:
        out += md_table(
            ["#", "Kind", "Function", "Module", "Callers"],
            [
                (i, m.kind, _sym(m.name, m.kind), m.module, f"**{m.fan_in}**")
                for i, m in enumerate(ranked_fan_in, 1)
            ],
            aligns="rllr",
        )
        out += [
            "",
            "**Insight:** Functions with high fan-in are either core APIs or "
            "bottlenecks. Review these for:",
            "",
            "- Thread safety and performance",
            "- Clear documentation and contracts",
            "- Potential for breaking changes",
        ]
    else:
        out.append("No high fan-in functions identified.")
    rule()

    # ── High Fan-Out ─────────────────────────────────────────────────────
    out += [
        "## High Fan-Out Functions (Orchestrators)",
        "",
        "Functions that call many others may indicate complex orchestration "
        "logic or poor separation of concerns.  Only repo-internal callees "
        "are counted — stdlib and third-party calls are not orchestration.",
        "",
    ]
    if analyzer.high_fanout_functions:
        top_fanout = sorted(analyzer.high_fanout_functions, key=lambda f: f.fan_out, reverse=True)
        out += md_table(
            ["#", "Function", "Module", "Internal Calls", "Type"],
            [
                (
                    i,
                    _sym(f.name, f.kind),
                    f.module,
                    f"**{f.fan_out}**",
                    "Orchestrator" if f.fan_out > 50 else "Coordinator",
                )
                for i, f in enumerate(top_fanout[:10], 1)
            ],
            aligns="rllrl",
        )
    else:
        out.append("No extreme high fan-out functions detected. Well-balanced architecture.")
    rule()

    # ── Module Architecture ──────────────────────────────────────────────
    out += ["## Module Architecture", ""]
    if analyzer.module_metrics:
        total_modules = len(analyzer.module_metrics)
        cap = min(10, total_modules)
        out += [
            f"Top modules by dependency coupling and cohesion "
            f"(showing {cap} of {total_modules} with activity).",
            "Cohesion = incoming / (incoming + outgoing + 1); higher = more "
            "internally focused.  Modules with no in-repo callers are "
            "externally driven (MCP router, CLI, GUI event loop) — their "
            "0.00 cohesion is expected, not a coupling problem.",
            "",
        ]
        ranked_modules = sorted(
            analyzer.module_metrics.items(),
            key=lambda kv: kv[1].functions + kv[1].classes + kv[1].methods,
            reverse=True,
        )[:cap]
        out += md_table(
            ["Module", "Functions", "Classes", "Incoming", "Outgoing", "Cohesion", "Note"],
            [
                (
                    f"`{module}`",
                    mm.functions,
                    mm.classes,
                    len(mm.incoming_deps),
                    len(mm.outgoing_deps),
                    f"{mm.cohesion_score:.2f}",
                    "externally driven" if not mm.incoming_deps else "",
                )
                for module, mm in ranked_modules
            ],
            aligns="lrrrrrl",
        )
    else:
        out.append("No module metrics available.")
    rule()

    # ── Key Call Chains ──────────────────────────────────────────────────
    out += ["## Key Call Chains", ""]
    if analyzer.critical_paths and (
        max(c.depth for c in analyzer.critical_paths) >= _MIN_CALL_CHAIN_DEPTH
        or len(analyzer.critical_paths) >= _MIN_CALL_CHAIN_COUNT
    ):
        out += ["Deepest call chains in the codebase.", ""]
        for i, chain in enumerate(analyzer.critical_paths[:5], 1):
            out += [
                f"**Chain {i}** (depth: {chain.depth})",
                "",
                "```",
                " → ".join(chain.chain),
                "```",
                "",
            ]
        out.pop()
    else:
        out.append("No deep call chains detected.")
    rule()

    # ── Public API Surface ───────────────────────────────────────────────
    out += ["## Public API Surface", ""]
    if analyzer.public_apis:
        top_apis = sorted(analyzer.public_apis, key=lambda a: a.fan_in, reverse=True)[:10]
        shown = (
            f"  Top {len(top_apis)} of {len(analyzer.public_apis)} shown."
            if len(analyzer.public_apis) > len(top_apis)
            else ""
        )
        out += [
            "Definitions re-exported from an `__init__.py` or otherwise "
            f"reachable as public entry points, ranked by fan-in.{shown}",
            "",
        ]
        out += md_table(
            ["Name", "Module", "Fan-In", "Kind"],
            [(_sym(a.name, a.kind), a.module, a.fan_in, a.kind) for a in top_apis],
            aligns="llrl",
        )
    else:
        out.append("No public APIs identified.")
    rule()

    # ── Docstring Coverage ───────────────────────────────────────────────
    out += [
        "## Docstring Coverage",
        "",
        "Docstring coverage directly determines semantic retrieval quality. Nodes "
        "without docstrings embed only structured identifiers "
        "(`KIND/NAME/QUALNAME/MODULE`), where keyword search is as effective as "
        "vector embeddings. The semantic model earns its value only when a "
        "docstring is present.",
        "",
    ]
    cov = analyzer.docstring_coverage
    if cov:
        overall_pct = cov["coverage_pct"]
        cov_rows = []
        for kind in ("function", "method", "class", "module"):
            if kind in cov["by_kind"]:
                k = cov["by_kind"][kind]
                kind_pct = (k["with_doc"] / k["total"] * 100) if k["total"] else 0.0
                cov_rows.append(
                    (
                        f"`{kind}`",
                        k["with_doc"],
                        k["total"],
                        f"{_bar(kind_pct)} {kind_pct:.1f}%",
                    )
                )
        cov_rows.append(
            (
                "**total**",
                f"**{cov['with_doc']}**",
                f"**{cov['total']}**",
                f"**{_bar(overall_pct)} {overall_pct:.1f}%**",
            )
        )
        out += md_table(["Kind", "Documented", "Total", "Coverage"], cov_rows, aligns="lrrl")
        if overall_pct < 80:
            undocumented = cov["total"] - cov["with_doc"]
            out += [
                "",
                f"> **Recommendation:** {undocumented} nodes lack docstrings. "
                "Prioritize documenting high-fan-in functions and public API "
                "surface first — these have the highest impact on query accuracy.",
            ]
    else:
        out.append("Coverage data not available.")
    rule()

    # ── Structural Importance Ranking ────────────────────────────────────
    out += ["## Structural Importance Ranking (SIR)", ""]
    if analyzer.centrality_modules:
        out += [
            "Weighted PageRank aggregated by module — reveals architectural spine. "
            "Cross-module edges boosted 1.5×; private symbols penalized 0.85×. "
            "Node-level detail: `pycodekg centrality --top 25`",
            "",
        ]
        out += md_table(
            ["Rank", "Score", "Members", "Module"],
            [
                (m["rank"], f"{m['score']:.6f}", m["member_count"], f"`{m['module_path']}`")
                for m in analyzer.centrality_modules[:15]
            ],
            aligns="rrrl",
        )
    else:
        out.append("Centrality data not available.")
    rule()

    # ── Issues / Strengths / Recommendations ─────────────────────────────
    out += ["## Code Quality Issues", ""]
    out += [f"- {issue}" for issue in analyzer.issues] or ["- No major issues detected"]
    rule()

    out += ["## Architectural Strengths", ""]
    out += [f"- {s}" for s in analyzer.strengths] or ["- Continue monitoring code quality"]
    rule()

    out += ["## Recommendations", "", analyzer._build_recommendations().strip()]
    rule()

    # ── Inheritance Hierarchy ────────────────────────────────────────────
    out += ["## Inheritance Hierarchy", ""]
    inh = analyzer.inheritance_analysis
    if inh and inh.get("total_inherits_edges", 0) > 0:
        out += [
            f"**{inh['total_inherits_edges']}** INHERITS edges across "
            f"**{len(inh['classes'])}** classes. Max depth: **{inh['max_depth']}**.",
            "",
        ]
        out += md_table(
            ["Class", "Module", "Depth", "Parents", "Children"],
            [
                (
                    f"`{cls['name']}`",
                    cls["module"],
                    cls["depth"],
                    cls["parent_count"],
                    cls["child_count"],
                )
                for cls in inh["classes"][:20]
            ],
            aligns="llrrr",
        )
        if inh.get("multiple_inheritance"):
            out += [
                "",
                f"### Multiple Inheritance ({len(inh['multiple_inheritance'])} classes)",
                "",
            ]
            for mi in inh["multiple_inheritance"]:
                bases = ", ".join(f"`{b}`" for b in mi["bases"])
                out.append(f"- `{mi['class']}` ({mi['module']}) inherits from {bases}")
        if inh.get("diamonds"):
            out += ["", f"### Diamond Patterns ({len(inh['diamonds'])} detected)", ""]
            for d in inh["diamonds"]:
                common = ", ".join(f"`{a}`" for a in d["common_ancestors"])
                out.append(f"- `{d['class']}` ({d['module']}) — common ancestor(s): {common}")
    else:
        out.append("No inheritance edges (no class hierarchies).")
    rule()

    # ── Snapshot History ─────────────────────────────────────────────────
    out += ["## Snapshot History", ""]
    if analyzer.snapshot_history:

        def _unchanged(snap: dict) -> bool:
            """A snapshot whose Δ vs. the previous one is all zeros."""
            delta = (snap.get("deltas") or {}).get("vs_previous")
            if not delta:
                return False  # no baseline — always show
            return (
                delta.get("nodes") == 0
                and delta.get("edges") == 0
                and not delta.get("coverage_delta")
            )

        # Keep the most recent snapshot (current state) and every row that
        # actually changed; collapse runs of +0/+0/+0.0% rows to a note.
        rows = [
            (i, snap)
            for i, snap in enumerate(analyzer.snapshot_history, 1)
            if i == 1 or not _unchanged(snap)
        ]
        elided = len(analyzer.snapshot_history) - len(rows)
        note = f"  {elided} unchanged snapshot(s) elided." if elided else ""
        out += [
            "Recent snapshots in reverse chronological order. Δ columns show "
            f"change vs. the immediately preceding snapshot.{note}",
            "",
        ]
        out += md_table(
            [
                "#",
                "Timestamp",
                "Branch",
                "Version",
                "Nodes",
                "Edges",
                "Coverage",
                "Δ Nodes",
                "Δ Edges",
                "Δ Coverage",
            ],
            [_snapshot_row(i, snap) for i, snap in rows],
            aligns="rlllrrrrrr",
        )
    else:
        out.append("No snapshots found. Run `pycodekg snapshot save <version>` to capture one.")
    rule()

    # ── Orphaned Code ────────────────────────────────────────────────────
    out += ["## Orphaned Code", ""]
    if analyzer.orphaned_functions:
        top_orphans = analyzer.orphaned_functions[:15]
        shown = (
            f"  Top {len(top_orphans)} of {len(analyzer.orphaned_functions)} by size shown."
            if len(analyzer.orphaned_functions) > len(top_orphans)
            else ""
        )
        out += [
            f"{len(analyzer.orphaned_functions)} definitions have no callers in code "
            "or tests (dead-code candidates).  Framework-dispatched entry points — "
            "dunder/protocol methods, properties, Click commands, MCP tools, "
            "`ast.NodeVisitor` dispatch, SDK protocol overrides, console scripts, "
            f"`__main__` guards — are already excluded.{shown}",
            "",
        ]
        out += md_table(
            ["Name", "Kind", "Module", "Lines"],
            [(_sym(f.name, f.kind), f.kind, f.module, f.lines) for f in top_orphans],
            aligns="lllr",
        )
    else:
        out.append("No dead-code candidates detected.")
    if analyzer.test_covered_orphans:
        top_tested = analyzer.test_covered_orphans[:15]
        shown = (
            f"  Top {len(top_tested)} of {len(analyzer.test_covered_orphans)} by size shown."
            if len(analyzer.test_covered_orphans) > len(top_tested)
            else ""
        )
        out += [
            "",
            f"{len(analyzer.test_covered_orphans)} further definitions are unused in "
            "production code but exercised by tests — likely public API consumed "
            "by downstream packages.  Not counted against the quality grade; "
            f"review for intentional export.{shown}",
            "",
        ]
        out += md_table(
            ["Name", "Kind", "Module", "Lines"],
            [(_sym(f.name, f.kind), f.kind, f.module, f.lines) for f in top_tested],
            aligns="lllr",
        )
    rule()

    # ── CodeRank ─────────────────────────────────────────────────────────
    out += ["## CodeRank — Global Structural Importance", ""]
    if analyzer.coderank_top_nodes:
        top_ranked = analyzer.coderank_top_nodes[:20]
        shown = (
            f"  Top {len(top_ranked)} of {len(analyzer.coderank_top_nodes)} shown."
            if len(analyzer.coderank_top_nodes) > len(top_ranked)
            else ""
        )
        out += [
            "Weighted PageRank over CALLS + IMPORTS + INHERITS edges (test paths "
            "excluded). Scores are normalized to sum to 1.0. This ranking seeds "
            f"fan-in discovery and the concern queries below.{shown}",
            "",
        ]
        out += md_table(
            ["Rank", "Score", "Kind", "Name", "Module"],
            [
                (
                    i,
                    f"{n['score']:.6f}",
                    n["kind"],
                    _sym(n["qualname"] or n["name"], n["kind"]),
                    n["module_path"],
                )
                for i, n in enumerate(top_ranked, 1)
            ],
            aligns="rrlll",
        )
    else:
        out.append("CodeRank data not available.")
    rule()

    # ── Concern-Based Hybrid Ranking ─────────────────────────────────────
    out += ["## Concern-Based Hybrid Ranking", ""]
    if analyzer.concern_analysis:
        out += [
            "Top structurally-dominant nodes per architectural concern "
            "(0.60 × semantic + 0.25 × CodeRank + 0.15 × graph proximity).",
            "",
        ]
        for entry in analyzer.concern_analysis:
            out += [f"### {entry['concern'].title()}", ""]
            out += md_table(
                ["Rank", "Score", "Kind", "Name", "Module"],
                [
                    (n["rank"], n["score"], n["kind"], _sym(n["name"], n["kind"]), n["module"])
                    for n in entry["top_nodes"]
                ],
                aligns="rrlll",
            )
            out.append("")
        out.pop()
    else:
        out.append("Concern analysis not available.")

    if elapsed_seconds is not None:
        elapsed_str = (
            f"{elapsed_seconds:.1f}s" if elapsed_seconds < 60 else f"{elapsed_seconds / 60:.1f}m"
        )
        rule()
        out.append(
            f"*Report generated by PyCodeKG Thorough Analysis Tool — "
            f"analysis completed in {elapsed_str}*"
        )

    return "\n".join(out) + "\n"
