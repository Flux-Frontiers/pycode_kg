"""
Framework Detector for PyCodeKG.
Identifies repo-defining abstractions using centrality and cross-module signals.

Author: Eric G. Suchanek, PhD
Last Revision: 2026-03-12 17:30:35
License: Elastic 2.0
"""

import sqlite3

# Short method names that are structurally high fan-in but architecturally trivial.
# Excluded from framework-node ranking so hubs surface over lifecycle boilerplate.
_BOILERPLATE_NAMES: frozenset[str] = frozenset(
    {
        "close",
        "__init__",
        "__exit__",
        "__enter__",
        "__del__",
        "__repr__",
        "__str__",
        "__len__",
        "__iter__",
        "__next__",
        "__contains__",
        "__bool__",
        "__hash__",
        "__eq__",
        "__ne__",
        "__lt__",
        "__gt__",
        "__le__",
        "__ge__",
        "__call__",
    }
)


def detect_framework_nodes(
    limit: int = 25, db_path: str = "pycodekg.sqlite"
) -> list[tuple[str, float, str]]:
    """
    Detect framework-like nodes using SIR and module connectivity.

    Combines Structural Importance Ranking (SIR — importance within the graph)
    with module connectivity (interaction complexity) to identify modules that are
    both architecturally central AND highly connected to other modules.

    Framework score = 0.6 × normalized SIR + 0.4 × normalized connectivity.
    High-scoring modules are critical hubs: important AND complex.

    Lifecycle / protocol boilerplate (``close``, ``__init__``, ``__exit__``, etc.)
    is excluded so the ranking surfaces meaningful orchestrators rather than
    the most-called teardown methods.

    :param limit: Number of top framework nodes to return (default 25).
    :param db_path: Path to SQLite database (default "pycodekg.sqlite").
    :return: List of (node_id, framework_score, label) tuples, sorted by score descending.
    """
    # Aggregate node-level SIR up to module level so we compare like-for-like
    # against the module_connectivity metric.  Both signals end up keyed by
    # bare module path (e.g. "src/pycode_kg/store.py"), which we map to "mod:..."
    # IDs for output.
    from pycode_kg.analysis.centrality import (  # noqa: PLC0415
        StructuralImportanceRanker,
        aggregate_module_scores,
    )

    with sqlite3.connect(db_path) as con:
        connectivity = dict(
            con.execute(
                "SELECT node_id, score FROM centrality_scores WHERE metric = 'module_connectivity'"
            )
        )
        module_id_by_path: dict[str, str] = dict(
            con.execute("SELECT module_path, id FROM nodes WHERE kind = 'module'")
        )

    ranker = StructuralImportanceRanker(db_path)
    sir_records = ranker.compute()
    sir_by_path: dict[str, float] = {
        row["module_path"]: row["score"] for row in aggregate_module_scores(sir_records)
    }

    def norm(d: dict) -> dict:
        if not d:
            return {}
        vals = list(d.values())
        mn, mx = min(vals), max(vals)
        return {k: (v - mn) / (mx - mn) if mx > mn else 0.0 for k, v in d.items()}

    nsir = norm(sir_by_path)
    nconnectivity = norm(connectivity)

    # Framework score: weighted sum (SIR 60% — importance, connectivity 40% — coupling).
    # Restrict to module paths only — the tool advertises "Framework-like Modules",
    # so methods/functions must not leak into the ranking.  The previous implementation
    # mixed key spaces (typed node IDs from SIR with bare paths from connectivity),
    # which let methods like ``GraphStore.con`` appear in a "Modules" table.
    framework: dict[str, float] = {}
    for path in set(nsir) | set(nconnectivity):
        framework[path] = 0.6 * nsir.get(path, 0.0) + 0.4 * nconnectivity.get(path, 0.0)

    ranked = sorted(framework.items(), key=lambda x: x[1], reverse=True)
    result: list[tuple[str, float, str]] = []
    for path, score in ranked[:limit]:
        node_id = module_id_by_path.get(path, f"mod:{path}")
        result.append((node_id, score, path))
    # _BOILERPLATE_NAMES retained for backward-compat at the import site.
    _ = _BOILERPLATE_NAMES
    return result
