"""
test_index.py

Tests for SemanticIndex, Embedder ABC, SentenceTransformerEmbedder,
and the private utility functions in index.py.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from code_kg.index import (
    Embedder,
    SeedHit,
    SemanticIndex,
    _build_index_text,
    _escape,
    _extract_distance,
)

# ---------------------------------------------------------------------------
# Shared fake embedder (no real model loading)
# ---------------------------------------------------------------------------


class FakeEmbedder(Embedder):
    """Deterministic 4-d embedder; no external dependencies."""

    dim = 4

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]


# ---------------------------------------------------------------------------
# Embedder ABC
# ---------------------------------------------------------------------------


def test_embedder_embed_texts_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        Embedder().embed_texts(["hello"])


def test_embedder_embed_query_delegates_to_embed_texts():
    assert FakeEmbedder().embed_query("anything") == [0.1, 0.2, 0.3, 0.4]


# ---------------------------------------------------------------------------
# SentenceTransformerEmbedder — mocked to avoid loading real ML models
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_sentence_transformers():
    """Patch sentence_transformers AND transformers in sys.modules for the duration of the test.

    Both must be mocked together: SentenceTransformerEmbedder.__init__ imports
    ``from transformers import logging as hf_logging`` immediately after importing
    sentence_transformers.  If only sentence_transformers is mocked, the real
    ``transformers`` package is imported, which in turn does ``import torch`` at
    module level.  When torch's C extension is partially initialised by a previous
    test that also used this fixture, the second import attempt raises:
        RuntimeError: function '_has_torch_function' already has a docstring
    Mocking transformers prevents torch from being touched at all in these unit tests.
    """
    mock_st = MagicMock()
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 384
    mock_st.SentenceTransformer.return_value = mock_model

    mock_tf = MagicMock()
    mock_tf_logging = MagicMock()
    mock_tf.logging = mock_tf_logging

    with patch.dict(
        "sys.modules",
        {
            "sentence_transformers": mock_st,
            "transformers": mock_tf,
            "transformers.logging": mock_tf_logging,
        },
    ):
        yield mock_st, mock_model


def test_ste_init(mock_sentence_transformers):
    mock_st, mock_model = mock_sentence_transformers
    from code_kg.index import SentenceTransformerEmbedder

    emb = SentenceTransformerEmbedder("test-model")
    assert emb.model_name == "test-model"
    assert emb.dim == 384
    mock_st.SentenceTransformer.assert_called_once_with("test-model", local_files_only=True)


def test_ste_embed_texts(mock_sentence_transformers):
    mock_st, mock_model = mock_sentence_transformers
    mock_model.encode.return_value = [np.array([0.1, 0.2, 0.3], dtype="float32")]
    from code_kg.index import SentenceTransformerEmbedder

    emb = SentenceTransformerEmbedder()
    result = emb.embed_texts(["hello"])
    assert len(result) == 1
    assert result[0] == pytest.approx([0.1, 0.2, 0.3], abs=1e-6)


def test_ste_embed_query(mock_sentence_transformers):
    mock_st, mock_model = mock_sentence_transformers
    mock_model.encode.return_value = np.array([[0.5, 0.6]], dtype="float32")
    from code_kg.index import SentenceTransformerEmbedder

    emb = SentenceTransformerEmbedder()
    result = emb.embed_query("hello")
    assert result == pytest.approx([0.5, 0.6], abs=1e-6)


def test_ste_repr(mock_sentence_transformers):
    from code_kg.index import SentenceTransformerEmbedder

    emb = SentenceTransformerEmbedder("my-model")
    r = repr(emb)
    assert "SentenceTransformerEmbedder" in r
    assert "my-model" in r


# ---------------------------------------------------------------------------
# _build_index_text
# ---------------------------------------------------------------------------


def test_build_index_text_minimal():
    n = {
        "kind": "function",
        "name": "foo",
        "qualname": None,
        "module_path": None,
        "lineno": None,
        "docstring": None,
    }
    text = _build_index_text(n)
    assert text.startswith("KIND: function\nNAME: foo")
    assert "QUALNAME" not in text
    assert "MODULE" not in text
    assert "LINE" not in text
    assert "DOCSTRING" not in text


def test_build_index_text_all_fields():
    n = {
        "kind": "method",
        "name": "run",
        "qualname": "Foo.run",
        "module_path": "src/mod.py",
        "lineno": 10,
        "docstring": "  Does stuff.  ",
    }
    text = _build_index_text(n)
    assert "QUALNAME: Foo.run" in text
    assert "MODULE: src/mod.py" in text
    assert "LINE: 10" in text
    assert "DOCSTRING:" in text
    assert "Does stuff." in text


def test_build_index_text_lineno_zero():
    # lineno=0 is not None, so LINE should appear even though 0 is falsy
    n = {
        "kind": "function",
        "name": "f",
        "qualname": None,
        "module_path": None,
        "lineno": 0,
        "docstring": None,
    }
    text = _build_index_text(n)
    assert "LINE: 0" in text


# ---------------------------------------------------------------------------
# _extract_distance
# ---------------------------------------------------------------------------


def test_extract_distance_underscore_key():
    assert _extract_distance({"_distance": 0.42}, 99) == pytest.approx(0.42)


def test_extract_distance_plain_key():
    assert _extract_distance({"distance": 0.7}, 99) == pytest.approx(0.7)


def test_extract_distance_score_key():
    # score → 1 / (1 + 1.0) = 0.5
    assert _extract_distance({"score": 1.0}, 99) == pytest.approx(0.5)


def test_extract_distance_fallback_rank():
    assert _extract_distance({}, 7) == pytest.approx(7.0)


def test_extract_distance_none_values_fall_through_to_rank():
    row = {"_distance": None, "distance": None, "score": None}
    assert _extract_distance(row, 3) == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# _escape
# ---------------------------------------------------------------------------


def test_escape_no_quotes():
    assert _escape("hello") == "hello"


def test_escape_single_quote():
    assert _escape("it's") == "it''s"


def test_escape_multiple_quotes():
    assert _escape("a'b'c") == "a''b''c"


# ---------------------------------------------------------------------------
# SemanticIndex — init and repr (no LanceDB required)
# ---------------------------------------------------------------------------


def test_semanticindex_init(tmp_path):
    emb = FakeEmbedder()
    idx = SemanticIndex(tmp_path / "ldb", embedder=emb, table="mytbl")
    assert idx.lancedb_dir == tmp_path / "ldb"
    assert idx.table_name == "mytbl"
    assert idx.embedder is emb
    assert idx._tbl is None


def test_semanticindex_custom_kinds(tmp_path):
    idx = SemanticIndex(tmp_path, embedder=FakeEmbedder(), index_kinds=["function"])
    assert idx.index_kinds == ("function",)


def test_semanticindex_repr(tmp_path):
    emb = FakeEmbedder()
    idx = SemanticIndex(tmp_path, embedder=emb)
    r = repr(idx)
    assert "SemanticIndex" in r
    assert "codekg_nodes" in r


def test_semanticindex_read_nodes_empty_store(tmp_path):
    from code_kg.store import GraphStore

    store = GraphStore(tmp_path / "test.sqlite")
    idx = SemanticIndex(tmp_path / "ldb", embedder=FakeEmbedder())
    nodes = idx._read_nodes(store)
    assert nodes == []
    store.close()


# ---------------------------------------------------------------------------
# Helpers for LanceDB integration tests
# ---------------------------------------------------------------------------


def _make_populated_store(tmp_path: Path):
    """Build a small real graph in a GraphStore."""
    from code_kg.graph import CodeGraph
    from code_kg.store import GraphStore

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "mod.py").write_text(
        textwrap.dedent(
            """\
            def foo():
                pass

            class Bar:
                def baz(self):
                    pass
            """
        )
    )
    graph = CodeGraph(repo)
    nodes, edges = graph.extract(force=True).result()
    store = GraphStore(tmp_path / "codekg.sqlite")
    store.write(nodes, edges, wipe=True)
    return store


# ---------------------------------------------------------------------------
# SemanticIndex — build / search / table helpers (real LanceDB, fake embedder)
# ---------------------------------------------------------------------------


def test_semanticindex_build_returns_stats(tmp_path):
    store = _make_populated_store(tmp_path)
    idx = SemanticIndex(tmp_path / "ldb", embedder=FakeEmbedder())

    stats = idx.build(store)

    assert stats["indexed_rows"] > 0
    assert stats["dim"] == 4
    assert stats["table"] == "codekg_nodes"
    assert "lancedb_dir" in stats
    assert "kinds" in stats
    store.close()


def test_semanticindex_build_wipe_rebuilds(tmp_path):
    store = _make_populated_store(tmp_path)
    idx = SemanticIndex(tmp_path / "ldb", embedder=FakeEmbedder())
    idx.build(store)

    stats = idx.build(store, wipe=True)
    assert stats["indexed_rows"] > 0
    store.close()


def test_semanticindex_build_empty_store_returns_zero(tmp_path):
    from code_kg.store import GraphStore

    store = GraphStore(tmp_path / "empty.sqlite")
    idx = SemanticIndex(tmp_path / "ldb", embedder=FakeEmbedder())
    stats = idx.build(store)
    assert stats["indexed_rows"] == 0
    store.close()


def test_semanticindex_search_returns_seed_hits(tmp_path):
    store = _make_populated_store(tmp_path)
    idx = SemanticIndex(tmp_path / "ldb", embedder=FakeEmbedder())
    idx.build(store)

    hits = idx.search("database connection", k=3)

    assert isinstance(hits, list)
    assert all(isinstance(h, SeedHit) for h in hits)
    for i, h in enumerate(hits):
        assert h.rank == i
    store.close()


def test_semanticindex_get_table_cached_after_build(tmp_path):
    store = _make_populated_store(tmp_path)
    idx = SemanticIndex(tmp_path / "ldb", embedder=FakeEmbedder())
    idx.build(store)

    tbl_after_build = idx._tbl
    tbl_via_get = idx._get_table()
    assert tbl_after_build is tbl_via_get  # same object, no re-open
    store.close()


def test_semanticindex_get_table_opens_when_none(tmp_path):
    store = _make_populated_store(tmp_path)
    idx = SemanticIndex(tmp_path / "ldb", embedder=FakeEmbedder())
    idx.build(store)
    idx._tbl = None  # evict cache

    tbl = idx._get_table()
    assert tbl is not None
    store.close()


def test_semanticindex_open_table_existing(tmp_path):
    """_open_table must use table_names() (LanceDB >=0.23.0) when the table already exists."""
    store = _make_populated_store(tmp_path)
    ldb_dir = tmp_path / "ldb"
    idx = SemanticIndex(ldb_dir, embedder=FakeEmbedder())
    first_stats = idx.build(store)

    # Second build on the same directory: _open_table hits the "table exists" branch.
    idx2 = SemanticIndex(ldb_dir, embedder=FakeEmbedder())
    second_stats = idx2.build(store)

    assert second_stats["indexed_rows"] == first_stats["indexed_rows"]
    store.close()
