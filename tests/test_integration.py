"""
test_integration.py

End-to-end integration tests using the real SentenceTransformerEmbedder,
SemanticIndex, and PyCodeKG pipeline.  These tests load (or download) the
default embedding model, so they are slow and require either a cached model
or network access.

Run with:
    pytest -m integration
Skip in normal CI:
    pytest -m "not integration"
"""

from __future__ import annotations

import math
import textwrap
from pathlib import Path

import pytest

from pycode_kg.graph import CodeGraph
from pycode_kg.index import (
    SeedHit,
    SemanticIndex,
    SentenceTransformerEmbedder,
    suppress_ingestion_logging,
)
from pycode_kg.kg import PyCodeKG
from pycode_kg.module.types import QueryResult, SnippetPack
from pycode_kg.store import GraphStore

suppress_ingestion_logging()

# ---------------------------------------------------------------------------
# Synthetic repo
# ---------------------------------------------------------------------------

_SAMPLE_CODE = textwrap.dedent(
    """\
    def fetch_user_from_database(user_id: int) -> dict:
        \"\"\"Retrieve a user record from the database by primary key.\"\"\"
        return {}


    def compute_fibonacci(n: int) -> int:
        \"\"\"Calculate the nth Fibonacci number using recursion.\"\"\"
        if n <= 1:
            return n
        return compute_fibonacci(n - 1) + compute_fibonacci(n - 2)


    class AuthenticationManager:
        \"\"\"Handles user authentication and session management.\"\"\"

        def login(self, username: str, password: str) -> bool:
            \"\"\"Authenticate a user with username and password credentials.\"\"\"
            return True

        def logout(self, session_id: str) -> None:
            \"\"\"Terminate an active user session by session ID.\"\"\"
    """
)


@pytest.fixture(scope="module")
def sample_repo(tmp_path_factory) -> Path:
    repo = tmp_path_factory.mktemp("repo")
    (repo / "sample.py").write_text(_SAMPLE_CODE)
    return repo


# ---------------------------------------------------------------------------
# Real embedder — skip if model unavailable
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_embedder():
    """Load the default SentenceTransformerEmbedder; skip if model is absent."""
    try:
        return SentenceTransformerEmbedder()
    except (ImportError, OSError, RuntimeError) as exc:
        pytest.skip(f"Embedding model not available: {exc}")


# ---------------------------------------------------------------------------
# SentenceTransformerEmbedder — real model
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.integration
def test_ste_real_embed_texts_shape(real_embedder):
    vecs = real_embedder.embed_texts(["hello world", "foo bar"])
    assert len(vecs) == 2
    assert len(vecs[0]) == real_embedder.dim
    assert len(vecs[1]) == real_embedder.dim


@pytest.mark.slow
@pytest.mark.integration
def test_ste_real_embed_texts_normalized(real_embedder):
    vecs = real_embedder.embed_texts(["normalize me"])
    norm = math.sqrt(sum(x * x for x in vecs[0]))
    assert norm == pytest.approx(1.0, abs=1e-4)


@pytest.mark.slow
@pytest.mark.integration
def test_ste_real_embed_query_shape(real_embedder):
    vec = real_embedder.embed_query("database connection")
    assert len(vec) == real_embedder.dim


@pytest.mark.slow
@pytest.mark.integration
def test_ste_real_similar_texts_closer_than_dissimilar(real_embedder):
    """Cosine similarity: database/SQL pair should score higher than database/fibonacci."""

    def cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb)

    db1 = real_embedder.embed_query("retrieve user from database")
    db2 = real_embedder.embed_query("fetch record from SQL table")
    unrelated = real_embedder.embed_query("compute fibonacci sequence")

    assert cosine(db1, db2) > cosine(db1, unrelated)


# ---------------------------------------------------------------------------
# SemanticIndex — real embedder
# ---------------------------------------------------------------------------


def _build_store_and_index(tmp_path: Path, sample_repo: Path, embedder) -> tuple:
    """Extract graph, write to SQLite, build LanceDB index. Returns (store, idx)."""
    graph = CodeGraph(sample_repo)
    nodes, edges = graph.extract(force=True).result()
    store = GraphStore(tmp_path / "graph.sqlite")
    store.write(nodes, edges, wipe=True)
    idx = SemanticIndex(tmp_path / "ldb", embedder=embedder)
    idx.build(store)
    return store, idx


@pytest.mark.slow
@pytest.mark.integration
def test_semantic_index_real_build(tmp_path, sample_repo, real_embedder):
    store, idx = _build_store_and_index(tmp_path, sample_repo, real_embedder)
    stats = idx.build(store, wipe=True)
    assert stats["indexed_rows"] > 0
    assert stats["dim"] == real_embedder.dim
    store.close()


@pytest.mark.slow
@pytest.mark.integration
def test_semantic_index_real_search_returns_ranked_hits(tmp_path, sample_repo, real_embedder):
    store, idx = _build_store_and_index(tmp_path, sample_repo, real_embedder)
    hits = idx.search("database user retrieval", k=5)

    assert len(hits) > 0
    assert all(isinstance(h, SeedHit) for h in hits)
    assert [h.rank for h in hits] == list(range(len(hits)))
    store.close()


@pytest.mark.slow
@pytest.mark.integration
def test_semantic_index_real_search_ranks_relevant_node_first(tmp_path, sample_repo, real_embedder):
    """fetch_user_from_database should be the top hit for a database retrieval query."""
    store, idx = _build_store_and_index(tmp_path, sample_repo, real_embedder)
    hits = idx.search("retrieve user record from database", k=5)

    top_id = hits[0].id
    assert "fetch_user_from_database" in top_id or "fetch_user" in top_id
    store.close()


# ---------------------------------------------------------------------------
# PyCodeKG — full pipeline
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def built_kg(tmp_path_factory, sample_repo, real_embedder):
    """Build a real PyCodeKG against sample_repo; shared across all PyCodeKG tests."""
    tmp = tmp_path_factory.mktemp("kg")
    kg = PyCodeKG(
        repo_root=sample_repo,
        db_path=tmp / "graph.sqlite",
        lancedb_dir=tmp / "lancedb",
    )
    kg._embedder = real_embedder  # inject pre-loaded embedder to avoid double load
    kg.build(wipe=True)
    return kg


@pytest.mark.slow
@pytest.mark.integration
def test_pycodekg_real_build_stats(built_kg):
    stats = built_kg.store.stats()
    assert stats["total_nodes"] > 0
    assert stats["total_edges"] >= 0


@pytest.mark.slow
@pytest.mark.integration
def test_pycodekg_real_query_returns_results(built_kg):
    result = built_kg.query("database user retrieval", k=5)
    assert isinstance(result, QueryResult)
    assert len(result.nodes) > 0


@pytest.mark.slow
@pytest.mark.integration
def test_pycodekg_real_query_finds_database_function(built_kg):
    result = built_kg.query("retrieve user from database", k=5)
    node_names = [n["name"] for n in result.nodes]
    assert any("fetch_user" in name or "database" in name for name in node_names)


@pytest.mark.slow
@pytest.mark.integration
def test_pycodekg_real_query_finds_authentication(built_kg):
    result = built_kg.query("user authentication login session", k=5)
    node_names = [n["name"] for n in result.nodes]
    assert any("login" in name or "auth" in name.lower() or "logout" in name for name in node_names)


@pytest.mark.slow
@pytest.mark.integration
def test_pycodekg_real_pack_returns_source(built_kg):
    pack = built_kg.pack("database user retrieval", k=5)
    assert isinstance(pack, SnippetPack)
    assert len(pack.nodes) > 0
    combined = "\n".join((n.get("snippet") or {}).get("text", "") for n in pack.nodes)
    assert "def" in combined or "class" in combined


@pytest.mark.slow
@pytest.mark.integration
def test_pycodekg_real_pack_contains_relevant_source(built_kg):
    pack = built_kg.pack("retrieve user from database", k=5)
    combined = "\n".join((n.get("snippet") or {}).get("text", "") for n in pack.nodes)
    assert "fetch_user_from_database" in combined


@pytest.mark.slow
@pytest.mark.integration
def test_pycodekg_real_query_hop0_vs_hop1(built_kg):
    """hop=1 graph expansion should return at least as many nodes as hop=0 pure semantic."""
    result_hop0 = built_kg.query("authentication", k=5, hop=0)
    result_hop1 = built_kg.query("authentication", k=5, hop=1)
    assert len(result_hop1.nodes) >= len(result_hop0.nodes)
