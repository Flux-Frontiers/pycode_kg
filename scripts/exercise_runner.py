#!/usr/bin/env python3
"""exercise_runner.py — Run all 19 PyCodeKG tool exercises with real output.

Companion to docs/exercises.md. Initialises a PyCodeKG instance against a
built repository and exercises every MCP tool in the same order as the
exercises document, printing the function call and its output.

Usage::

    # Run against the current repo (graph must already be built)
    python scripts/exercise_runner.py

    # Run against another repo
    python scripts/exercise_runner.py --repo /path/to/repo

    # Build the graph first, then run all exercises
    python scripts/exercise_runner.py --build

    # Redirect to a file for later review
    python scripts/exercise_runner.py > exercise_output.md 2>&1
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# ── display helpers ────────────────────────────────────────────────────────────

WIDTH = 72


def banner(title: str) -> None:
    print(f"\n{'#' * WIDTH}")
    print(f"# {title}")
    print(f"{'#' * WIDTH}\n")


def section(title: str) -> None:
    print(f"\n{'─' * WIDTH}")
    print(f"  {title}")
    print(f"{'─' * WIDTH}\n")


def call_header(call: str) -> None:
    print(f">>> {call}")
    print()


def show(call: str, result: str, truncate: int = 120) -> None:
    call_header(call)
    lines = result.splitlines()
    if truncate and len(lines) > truncate:
        for line in lines[:truncate]:
            print(line)
        print(
            f"\n... [{len(lines) - truncate} more lines — re-run with a file redirect to see all]"
        )
    else:
        print(result)
    print()


def run_exercise(label: str, call_str: str, fn, *args, **kwargs) -> str | None:
    section(label)
    call_header(call_str)
    try:
        result = fn(*args, **kwargs)
        lines = (result or "").splitlines()
        limit = 100
        if len(lines) > limit:
            for line in lines[:limit]:
                print(line)
            print(f"\n... [{len(lines) - limit} more lines]")
        else:
            print(result or "(no output)")
        print()
        return result
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}\n")
        return None


# ── initialisation ─────────────────────────────────────────────────────────────


def build_graph(repo: Path) -> None:
    print(f"Building knowledge graph for {repo} ...")
    result = subprocess.run(
        ["pycodekg", "build", "--repo", str(repo)],
        check=False,
    )
    if result.returncode != 0:
        print("ERROR: 'pycodekg build' failed — check output above.", file=sys.stderr)
        sys.exit(1)
    print("Build complete.\n")


def init_kg(repo: Path) -> None:
    """Initialise the PyCodeKG global state used by mcp_server tool functions."""
    import pycode_kg.mcp_server as _srv  # noqa: PLC0415
    from pycode_kg import PyCodeKG  # noqa: PLC0415
    from pycode_kg.pycodekg import DEFAULT_MODEL  # noqa: PLC0415
    from pycode_kg.snapshots import SnapshotManager  # noqa: PLC0415

    db = repo / ".pycodekg" / "graph.sqlite"
    vectors = repo / ".pycodekg" / "vectors.sqlite"

    if not db.exists():
        print(
            f"ERROR: No graph database at {db}\n"
            "Run: pycodekg build --repo <repo>  (or pass --build)",
            file=sys.stderr,
        )
        sys.exit(1)

    kg = PyCodeKG(repo_root=repo, db_path=db, vectors_path=vectors, model=DEFAULT_MODEL)
    _srv._kg = kg  # type: ignore[attr-defined]
    _srv._snapshot_mgr = SnapshotManager(  # type: ignore[attr-defined]
        repo / ".pycodekg" / "snapshots", db_path=db
    )
    print(f"Knowledge graph loaded from {db}\n")


# ── exercises ──────────────────────────────────────────────────────────────────


def run_exercises(repo: Path) -> None:
    import pycode_kg.mcp_server as srv  # noqa: PLC0415

    # State extracted from early exercises to feed into later ones
    node_id: str | None = None
    file_path: str | None = None
    file_lineno: int | None = None
    class_id: str | None = None
    class_module: str | None = None

    # ═══════════════════════════════════════════════════════════════════════════
    banner("Part 1 — Orientation")
    # ═══════════════════════════════════════════════════════════════════════════

    run_exercise(
        "Exercise 1.1 — Get your bearings",
        "graph_stats()",
        srv.graph_stats,
    )

    run_exercise(
        "Exercise 1.2 — Architectural spine (module view)",
        "centrality(top=15, group_by='module')",
        srv.centrality,
        top=15,
        group_by="module",
    )

    run_exercise(
        "Exercise 1.2 — Architectural spine (node view)",
        "centrality(top=15, group_by='node')",
        srv.centrality,
        top=15,
        group_by="node",
    )

    run_exercise(
        "Exercise 1.3 — Bridge centrality",
        "bridge_centrality(top=10)",
        srv.bridge_centrality,
        top=10,
    )

    run_exercise(
        "Exercise 1.3 — Framework nodes (architectural load-bearers)",
        "framework_nodes(top=10)",
        srv.framework_nodes,
        top=10,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    banner("Part 2 — Exploration")
    # ═══════════════════════════════════════════════════════════════════════════

    section("Exercise 2.1 — Semantic search: storage persistence database")
    call_header("query_codebase('storage persistence database')")
    try:
        raw_json = srv.query_codebase("storage persistence database", format="json")
        result_data = json.loads(raw_json)
        # Extract a node_id + file location for subsequent exercises
        nodes = result_data.get("nodes", [])
        if nodes:
            first = nodes[0]
            node_id = first["id"]
            file_path = first.get("module_path") or ""
            file_lineno = first.get("lineno") or 1
            # Find a class node if available
            for n in nodes:
                if n.get("kind") == "class":
                    class_id = n["id"]
                    class_module = n.get("module_path", "")
                    break
            print(f"[node_id extracted for subsequent exercises: {node_id}]\n")
        # Display as markdown
        md = srv.query_codebase("storage persistence database", format="markdown")
        print(md)
        print()
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}\n")

    run_exercise(
        "Exercise 2.1 — Same query, CALLS edges only",
        "query_codebase('storage persistence database', rels='CALLS')",
        srv.query_codebase,
        "storage persistence database",
        rels="CALLS",
        format="markdown",
    )

    run_exercise(
        "Exercise 2.2 — Error handling: hop=2 (broad)",
        "query_codebase('error handling retry backoff', hop=2)",
        srv.query_codebase,
        "error handling retry backoff",
        hop=2,
        format="markdown",
    )

    run_exercise(
        "Exercise 2.2 — Error handling: hop=1 (default, for comparison)",
        "query_codebase('error handling retry backoff', hop=1)",
        srv.query_codebase,
        "error handling retry backoff",
        hop=1,
        format="markdown",
    )

    run_exercise(
        "Exercise 2.3 — Module structure via CONTAINS edges",
        "query_codebase('query pipeline', rels='CONTAINS', hop=2)",
        srv.query_codebase,
        "query pipeline",
        rels="CONTAINS",
        hop=2,
        format="markdown",
    )

    run_exercise(
        "Exercise 2.4 — Import graph",
        "query_codebase('imports dependencies external', rels='IMPORTS')",
        srv.query_codebase,
        "imports dependencies external",
        rels="IMPORTS",
        format="markdown",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    banner("Part 3 — Source Reading")
    # ═══════════════════════════════════════════════════════════════════════════

    run_exercise(
        "Exercise 3.1 — Source for a concept",
        "pack_snippets('query pipeline semantic search ranking')",
        srv.pack_snippets,
        "query pipeline semantic search ranking",
    )

    run_exercise(
        "Exercise 3.2 — Cross-module comparison (max_per_module=1)",
        "pack_snippets('normalize string identifier', max_per_module=1)",
        srv.pack_snippets,
        "normalize string identifier",
        max_per_module=1,
    )

    run_exercise(
        "Exercise 3.3 — Broaden seed set (k=12)",
        "pack_snippets('write reference metadata sidecar', k=12)",
        srv.pack_snippets,
        "write reference metadata sidecar",
        k=12,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    banner("Part 4 — Pinpoint Lookups")
    # ═══════════════════════════════════════════════════════════════════════════

    if node_id:
        run_exercise(
            f"Exercise 4.1 — Resolve a node ID: {node_id}",
            f"get_node('{node_id}')",
            srv.get_node,
            node_id,
        )
        run_exercise(
            "Exercise 4.1 — Same node with edges",
            f"get_node('{node_id}', include_edges=True)",
            srv.get_node,
            node_id,
            include_edges=True,
        )
    else:
        print("  [skipped — no node_id extracted from Part 2]\n")

    run_exercise(
        "Exercise 4.2 — Search by name: functions named 'fetch'",
        "find_node('fetch', kind='function')",
        srv.find_node,
        "fetch",
        kind="function",
    )

    if file_path and file_lineno:
        run_exercise(
            f"Exercise 4.3 — Reverse-lookup from {file_path}:{file_lineno}",
            f"find_definition_at('{file_path}', {file_lineno})",
            srv.find_definition_at,
            file_path,
            file_lineno,
        )
    else:
        print("  [Exercise 4.3 skipped — no file/line from Part 2 results]\n")

    # ═══════════════════════════════════════════════════════════════════════════
    banner("Part 5 — Fan-In and Explanations")
    # ═══════════════════════════════════════════════════════════════════════════

    if node_id:
        run_exercise(
            f"Exercise 5.1 — Who calls: {node_id}",
            f"callers('{node_id}')",
            srv.callers,
            node_id,
        )
        run_exercise(
            f"Exercise 5.2 — Explain: {node_id}",
            f"explain('{node_id}')",
            srv.explain,
            node_id,
        )
    else:
        print("  [Exercises 5.1–5.2 skipped — no node_id from Part 2]\n")

    # Find a class for 5.3 — try query if we didn't find one in Part 2
    if not class_id:
        section("Exercise 5.3 — Searching for a class node ...")
        call_header("query_codebase('class', format='json')")
        try:
            cls_raw = srv.query_codebase("class object", format="json")
            cls_data = json.loads(cls_raw)
            for n in cls_data.get("nodes", []):
                if n.get("kind") == "class":
                    class_id = n["id"]
                    class_module = n.get("module_path", "")
                    print(f"[class_id found: {class_id}]\n")
                    break
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {exc}\n")

    if class_id:
        run_exercise(
            f"Exercise 5.3 — Trace a class: {class_id}",
            f"explain('{class_id}')",
            srv.explain,
            class_id,
        )
        if class_module:
            run_exercise(
                f"Exercise 5.3 — Methods in {class_module}",
                f"list_nodes('{class_module}', kind='method')",
                srv.list_nodes,
                class_module,
                kind="method",
            )
    else:
        print("  [Exercise 5.3 skipped — no class node found]\n")

    # ═══════════════════════════════════════════════════════════════════════════
    banner("Part 6 — Structural Ranking (CodeRank)")
    # ═══════════════════════════════════════════════════════════════════════════

    # rank_nodes returns JSON — extract a node_id from it for explain_rank
    rank_node_id: str | None = None
    section("Exercise 6.1 — Global PageRank: rank_nodes(top=25)")
    call_header("rank_nodes(top=25)")
    try:
        rank_raw = srv.rank_nodes(top=25)
        rank_data = json.loads(rank_raw)
        if isinstance(rank_data, list) and rank_data:
            rank_node_id = rank_data[0].get("node_id")
        # Print as formatted table
        if isinstance(rank_data, list):
            print(f"{'Rank':<6} {'Score':<12} {'Kind':<12} {'Name':<35} Module")
            print("-" * 80)
            for r in rank_data[:20]:
                name = (r.get("qualname") or "")[:34]
                module = r.get("module_path") or ""
                score = r.get("score", 0)
                kind = r.get("kind") or ""
                print(f"{r['rank']:<6} {score:<12.8f} {kind:<12} {name:<35} {module}")
        else:
            print(rank_raw)
        print()
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}\n")

    section("Exercise 6.2 — Structure-aware search: hybrid mode")
    call_header("query_ranked('database connection storage', mode='hybrid')")
    try:
        qr_raw = srv.query_ranked("database connection storage", mode="hybrid")
        qr_data = json.loads(qr_raw)
        results = qr_data.get("results", [])
        print(
            f"Query: {qr_data.get('query')}  |  Mode: {qr_data.get('mode')}  |  Returned: {qr_data.get('returned')}\n"
        )
        print(f"{'Rank':<6} {'Final':<10} {'Semantic':<10} {'Centrality':<12} {'Name':<35} Module")
        print("-" * 90)
        for r in results[:15]:
            name = (r.get("qualname") or "")[:34]
            module = r.get("module_path") or ""
            print(
                f"{r['rank']:<6} {r['final_score']:<10.4f} "
                f"{r['semantic_score']:<10.4f} {r['centrality_score']:<12.4f} "
                f"{name:<35} {module}"
            )
        print()
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}\n")

    section("Exercise 6.2 — Structure-aware search: ppr mode")
    call_header("query_ranked('database connection storage', mode='ppr')")
    try:
        qr_raw = srv.query_ranked("database connection storage", mode="ppr")
        qr_data = json.loads(qr_raw)
        results = qr_data.get("results", [])
        print(
            f"Query: {qr_data.get('query')}  |  Mode: {qr_data.get('mode')}  |  Returned: {qr_data.get('returned')}\n"
        )
        print(f"{'Rank':<6} {'Final':<10} {'Semantic':<10} {'Name':<35} Module")
        print("-" * 80)
        for r in results[:15]:
            name = (r.get("qualname") or "")[:34]
            module = r.get("module_path") or ""
            print(
                f"{r['rank']:<6} {r['final_score']:<10.4f} {r['semantic_score']:<10.4f} {name:<35} {module}"
            )
        print()
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}\n")

    explain_id = rank_node_id or node_id
    if explain_id:
        run_exercise(
            f"Exercise 6.3 — Explain structural rank: {explain_id}",
            f"explain_rank('{explain_id}')",
            srv.explain_rank,
            explain_id,
        )
        run_exercise(
            "Exercise 6.3 — Explain rank with query context",
            f"explain_rank('{explain_id}', q='database connection')",
            srv.explain_rank,
            explain_id,
            q="database connection",
        )
    else:
        print("  [Exercise 6.3 skipped — no node_id available]\n")

    # ═══════════════════════════════════════════════════════════════════════════
    banner("Part 7 — Architecture Analysis")
    # ═══════════════════════════════════════════════════════════════════════════

    run_exercise(
        "Exercise 7.1 — Full health check",
        "analyze_repo()",
        srv.analyze_repo,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    banner("Part 8 — Temporal Tracking")
    # ═══════════════════════════════════════════════════════════════════════════

    section("Exercise 8.1 — Snapshot history")
    call_header("snapshot_list()")
    try:
        snap_md = srv.snapshot_list()
        print(snap_md)
        print()
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}\n")

    section("Exercise 8.2 — Latest snapshot")
    call_header("snapshot_show('latest')")
    try:
        snap_show = srv.snapshot_show("latest")
        print(snap_show)
        print()
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR or no snapshots] {exc}\n")

    # snapshot_diff requires two real keys — skip with an informative message
    section("Exercise 8.3 — Snapshot diff (requires two saved snapshots)")
    print(
        "  To run a diff:\n"
        "    1. snapshot_list()                         — copy two 'key' values\n"
        "    2. snapshot_diff('older_key', 'newer_key') — compare before/after\n"
        "\n"
        "  Save snapshots with:\n"
        "    pycodekg snapshot save <label>\n"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    banner("Part 9 — Data Flow (Advanced)")
    # ═══════════════════════════════════════════════════════════════════════════

    run_exercise(
        "Exercise 9.1 — Attribute access patterns (ATTR_ACCESS edges)",
        "query_codebase('self attribute property access', rels='ATTR_ACCESS', include_symbols=True)",
        srv.query_codebase,
        "self attribute property access",
        rels="ATTR_ACCESS",
        include_symbols=True,
        format="markdown",
    )

    run_exercise(
        "Exercise 9.2 — Variable resolution (RESOLVES_TO edges)",
        "query_codebase('variable assignment name binding resolved', rels='RESOLVES_TO', include_symbols=True)",
        srv.query_codebase,
        "variable assignment name binding resolved",
        rels="RESOLVES_TO",
        include_symbols=True,
        format="markdown",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    banner("All Exercises Complete")
    # ═══════════════════════════════════════════════════════════════════════════

    print(
        "Tools exercised (19 total):\n"
        "  graph_stats, centrality, bridge_centrality, framework_nodes,\n"
        "  query_codebase, pack_snippets, get_node, find_node,\n"
        "  find_definition_at, callers, explain, list_nodes,\n"
        "  rank_nodes, query_ranked, explain_rank, analyze_repo,\n"
        "  snapshot_list, snapshot_show, snapshot_diff\n"
        "\n"
        "See docs/exercises.md for the full exercise guide.\n"
    )


# ── entry point ────────────────────────────────────────────────────────────────


def main() -> None:
    p = argparse.ArgumentParser(
        description="Run all 19 PyCodeKG exercises with real output against a built repo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/exercise_runner.py\n"
            "  python scripts/exercise_runner.py --repo /path/to/repo\n"
            "  python scripts/exercise_runner.py --build > exercise_output.md\n"
        ),
    )
    p.add_argument(
        "--repo",
        default=".",
        help="Repository root directory (default: current directory)",
    )
    p.add_argument(
        "--build",
        action="store_true",
        help="Run 'pycodekg build --repo <repo>' before running exercises",
    )
    args = p.parse_args()

    repo = Path(args.repo).resolve()

    print("PyCodeKG Exercise Runner")
    print(f"Repository: {repo}")
    print("See docs/exercises.md for the full exercise guide.\n")

    if args.build:
        build_graph(repo)

    init_kg(repo)
    run_exercises(repo)


if __name__ == "__main__":
    main()
