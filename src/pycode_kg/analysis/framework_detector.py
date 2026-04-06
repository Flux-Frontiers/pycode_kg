"""
Framework Detector for PyCodeKG.
Identifies repo-defining abstractions using centrality and cross-module signals.
"""

import sqlite3


def detect_framework_nodes(limit=25, db_path="pycodekg.sqlite"):
    """
    Detect framework-like nodes using SIR and module connectivity.

    Combines Structural Importance Ranking (SIR — importance within the graph)
    with module connectivity (interaction complexity) to identify modules that are
    both architecturally central AND highly connected to other modules.

    Framework score = 0.6 × normalized SIR + 0.4 × normalized connectivity.
    High-scoring modules are critical hubs: important AND complex.

    :param limit: Number of top framework nodes to return (default 25).
    :param db_path: Path to SQLite database (default "pycodekg.sqlite").
    :return: List of (node_id, framework_score, label) tuples, sorted by score descending.
    """
    with sqlite3.connect(db_path) as con:
        # Get SIR (structural importance) and connectivity (interaction complexity) scores
        sir = dict(
            con.execute(
                "SELECT node_id, score FROM centrality_scores WHERE metric = 'sir_pagerank'"
            )
        )
        connectivity = dict(
            con.execute(
                "SELECT node_id, score FROM centrality_scores WHERE metric = 'module_connectivity'"
            )
        )
        # Get module names
        names = dict(con.execute("SELECT id, name FROM nodes WHERE kind = 'module'"))

    # Normalize scores to [0, 1]
    def norm(d):
        if not d:
            return {}
        vals = list(d.values())
        mn, mx = min(vals), max(vals)
        return {k: (v - mn) / (mx - mn) if mx > mn else 0.0 for k, v in d.items()}

    nsir = norm(sir)
    nconnectivity = norm(connectivity)

    # Framework score: weighted sum (SIR 60% — importance, connectivity 40% — coupling)
    framework = {}
    for k in set(nsir) | set(nconnectivity):
        framework[k] = 0.6 * nsir.get(k, 0.0) + 0.4 * nconnectivity.get(k, 0.0)

    ranked = sorted(framework.items(), key=lambda x: x[1], reverse=True)
    result = []
    for node_id, score in ranked[:limit]:
        label = names.get(node_id, node_id)
        result.append((node_id, score, label))
    return result
