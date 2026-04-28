"""
Module Connectivity Centrality for PyCodeKG.
Measures module interaction complexity: how many unique modules each module calls/imports.
For well-modularized codebases, identifies orchestrator and hub modules.

Author: Eric G. Suchanek, PhD
Last Revision: 2026-03-12 17:30:35
License: Elastic 2.0
"""

import sqlite3
from collections import defaultdict

from pycode_kg.analysis.centrality import CentralityRecord, StructuralImportanceRanker


def compute_bridge_centrality(
    kind: str = "module",
    include_imports: bool = True,
    top: int = 25,
    db_path: str = "pycodekg.sqlite",
) -> list[tuple[str, float]]:
    """
    Compute module connectivity: unique module interactions per module.

    For well-modularized codebases with strong module boundaries, connectivity
    identifies which modules are hubs (calling many others) or widely depended upon
    (called by many modules).

    Replaces betweenness centrality which is meaningless when inter-module edges are zero.

    :param kind: Node kind (default 'module', currently unused but kept for compatibility)
    :param include_imports: Whether to include IMPORTS in connectivity (default True)
    :param top: Number of top modules to return (default 25)
    :param db_path: Path to SQLite database
    :return: List of (module_path, connectivity_score) tuples
    """
    with sqlite3.connect(db_path) as con:
        rows = con.execute(
            """
            SELECT src.module_path, dst.module_path, rel
            FROM edges
            JOIN nodes AS src ON edges.src = src.id
            JOIN nodes AS dst ON edges.dst = dst.id
            WHERE rel IN ('CALLS', 'IMPORTS')
              AND src.module_path IS NOT NULL
              AND dst.module_path IS NOT NULL
            """
        ).fetchall()

    # Compute unique modules called + unique modules calling this module
    outbound: dict[str, set[str]] = defaultdict(set)  # modules this module calls
    inbound: dict[str, set[str]] = defaultdict(set)  # modules that call this module
    call_counts: dict[str, int] = defaultdict(int)  # total call frequency

    for src_mod, dst_mod, rel in rows:
        if not src_mod or not dst_mod:
            continue
        if rel == "IMPORTS" and not include_imports:
            continue

        # Record outbound: src_mod calls/imports dst_mod
        outbound[src_mod].add(dst_mod)
        # Record inbound: dst_mod is called/imported by src_mod
        inbound[dst_mod].add(src_mod)
        call_counts[src_mod] += 1

    # Collect all modules
    all_modules = set(outbound.keys()) | set(inbound.keys())

    # Compute connectivity score: unique modules touched (fan-out + fan-in)
    # Higher score = more coupled with other modules
    scores: dict[str, float] = {}
    for mod in all_modules:
        unique_outbound = len(outbound[mod])
        unique_inbound = len(inbound[mod])
        total_calls = call_counts[mod]

        # Normalize: average of outbound and inbound diversity + call frequency
        # Scale to [0, 1]: assume typical module touches ~15 others
        connectivity_score = (
            (unique_outbound + unique_inbound) / 30.0  # diversity (60%)
            + min(total_calls / 50.0, 1.0) * 0.4  # frequency (40%)
        ) / 1.4  # normalize to roughly [0, 1]
        scores[mod] = min(connectivity_score, 1.0)

    # Persist scores
    records = [
        CentralityRecord(
            node_id=mod,
            kind="module",
            name=mod.split(".")[-1],
            module_path=mod,
            score=score,
            rank=idx + 1,
            inbound_count=len(inbound.get(mod, set())),
            cross_module_inbound=len(inbound.get(mod, set())),  # all are cross-module
            rel_breakdown={
                "calls_to_modules": len(outbound.get(mod, set())),
                "called_by_modules": len(inbound.get(mod, set())),
            },
            top_contributors=[],
        )
        for idx, (mod, score) in enumerate(sorted(scores.items(), key=lambda x: x[1], reverse=True))
    ]

    if records:
        StructuralImportanceRanker(db_path).write_scores(records, metric="module_connectivity")

    # Return top modules by connectivity
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top]
