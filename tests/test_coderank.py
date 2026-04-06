import sqlite3
from pathlib import Path

from code_kg.ranking.coderank import (
    build_code_graph,
    combine_hybrid_scores,
    compute_coderank,
    compute_seed_proximity,
    induce_query_subgraph,
)


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE nodes (id TEXT, kind TEXT, name TEXT, qualname TEXT, module_path TEXT)"
    )
    cur.execute("CREATE TABLE edges (src TEXT, dst TEXT, rel TEXT)")
    cur.executemany(
        "INSERT INTO nodes VALUES (?, ?, ?, ?, ?)",
        [
            ("m1", "module", "a", "a", "src/a.py"),
            ("f1", "function", "foo", "a.foo", "src/a.py"),
            ("f2", "function", "bar", "a.bar", "src/a.py"),
            ("f3", "function", "baz", "b.baz", "src/b.py"),
        ],
    )
    cur.executemany(
        "INSERT INTO edges VALUES (?, ?, ?)",
        [
            ("m1", "f1", "CONTAINS"),
            ("m1", "f2", "CONTAINS"),
            ("f1", "f2", "CALLS"),
            ("f3", "f2", "CALLS"),
            ("m1", "f3", "IMPORTS"),
        ],
    )
    conn.commit()
    conn.close()


def test_coderank_pipeline(tmp_path):
    db = tmp_path / "graph.sqlite"
    _make_db(db)

    graph = build_code_graph(str(db))
    assert graph.number_of_nodes() == 4
    assert graph.number_of_edges() >= 3

    coderank = compute_coderank(graph)
    assert "f2" in coderank
    assert coderank["f2"] > 0

    sub = induce_query_subgraph(graph, ["f1"], radius=1)
    proximity = compute_seed_proximity(sub, ["f1"])
    assert proximity["f1"] == 1.0

    results = combine_hybrid_scores(
        sub,
        semantic_scores={"f1": 0.9, "f2": 0.4},
        centrality_scores={node: coderank.get(node, 0.0) for node in sub.nodes},
        proximity_scores=proximity,
        top_k=10,
    )
    assert results
