"""
Hybrid Search Ranking for CodeKG.
Combines semantic relevance with structural importance (SIR).
"""

import math
import sqlite3


def get_sir_scores(metric="sir_pagerank", db_path="codekg.sqlite"):
    """Fetch SIR centrality scores from the database."""
    with sqlite3.connect(db_path) as con:
        rows = con.execute(
            "SELECT node_id, score FROM centrality_scores WHERE metric = ?", (metric,)
        ).fetchall()
    scores = {node_id: score for node_id, score in rows}
    if not scores:
        return {}
    max_score = max(scores.values())
    min_score = min(scores.values())

    # Normalize to [0,1]
    def norm(s):
        return (s - min_score) / (max_score - min_score) if max_score > min_score else 0.0

    return {k: norm(v) for k, v in scores.items()}


def rerank_hybrid(
    results, centrality_metric="sir_pagerank", lambda_weight=0.15, db_path="codekg.sqlite"
):
    """
    Rerank search results using hybrid score.
    :param results: List of dicts with 'node_id' and 'semantic_score'
    :param centrality_metric: Centrality metric to use (default 'sir_pagerank')
    :param lambda_weight: Weight for structural term (default 0.15)
    :param db_path: Path to SQLite database
    :return: List of dicts with hybrid scores
    """
    sir_scores = get_sir_scores(centrality_metric, db_path)
    reranked = []
    for r in results:
        node_id = r.get("node_id")
        sem = r.get("semantic_score", 0.0)
        struct = sir_scores.get(node_id, 0.0)
        # Hybrid score: semantic + lambda * log(1 + struct)
        hybrid = sem + lambda_weight * math.log(1 + struct)
        out = dict(r)
        out["structural_score"] = struct
        out["hybrid_score"] = hybrid
        reranked.append(out)
    reranked.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return reranked
