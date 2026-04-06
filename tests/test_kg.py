"""
test_kg.py

Tests for CodeKG orchestrator and result types:
  BuildStats, QueryResult, SnippetPack, CodeKG
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from code_kg.graph import CodeGraph
from code_kg.index import Embedder, SeedHit, SemanticIndex
from code_kg.kg import (
    BuildStats,
    CodeKG,
    QueryResult,
    Snippet,
    SnippetPack,
)
from code_kg.module.types import (
    compute_span,
    make_snippet,
    normalize_query_text,
    query_tokens,
    read_lines,
    safe_join,
    semantic_score_from_distance,
    spans_overlap,
)
from code_kg.store import GraphStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_repo(tmp_path: Path, files: dict) -> Path:
    for rel, src in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))
    return tmp_path


def _make_kg(tmp_path: Path, files: dict) -> CodeKG:
    """Build a CodeKG (graph only, no LanceDB) from a synthetic repo."""
    repo = tmp_path / "repo"
    _write_repo(repo, files)
    kg = CodeKG(
        repo_root=repo,
        db_path=tmp_path / "codekg.sqlite",
        lancedb_dir=tmp_path / "lancedb",
    )
    kg.build_graph(wipe=True)
    return kg


# ---------------------------------------------------------------------------
# BuildStats
# ---------------------------------------------------------------------------


def test_buildstats_to_dict(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    s = kg.store.stats()
    bs = BuildStats(
        repo_root=str(tmp_path),
        db_path=str(tmp_path / "codekg.sqlite"),
        total_nodes=s["total_nodes"],
        total_edges=s["total_edges"],
        node_counts=s["node_counts"],
        edge_counts=s["edge_counts"],
    )
    d = bs.to_dict()
    assert "total_nodes" in d
    assert "node_counts" in d
    kg.close()


def test_buildstats_str(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    s = kg.store.stats()
    bs = BuildStats(
        repo_root=str(tmp_path),
        db_path=str(tmp_path / "codekg.sqlite"),
        total_nodes=s["total_nodes"],
        total_edges=s["total_edges"],
        node_counts=s["node_counts"],
        edge_counts=s["edge_counts"],
        indexed_rows=42,
        index_dim=384,
    )
    text = str(bs)
    assert "indexed" in text
    assert "42" in text
    kg.close()


# ---------------------------------------------------------------------------
# CodeKG — build_graph
# ---------------------------------------------------------------------------


def test_codekg_build_graph_returns_buildstats(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    assert isinstance(kg.store.stats(), dict)
    kg.close()


def test_codekg_build_graph_populates_store(tmp_path):
    kg = _make_kg(
        tmp_path,
        {"mod.py": "class Foo:\n    def run(self): pass\ndef bar(): pass\n"},
    )
    s = kg.store.stats()
    assert s["total_nodes"] > 0
    assert s["total_edges"] > 0
    assert s["node_counts"].get("class", 0) >= 1
    assert s["node_counts"].get("function", 0) >= 1
    assert s["node_counts"].get("method", 0) >= 1
    kg.close()


def test_codekg_build_graph_wipe(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    count1 = kg.store.stats()["total_nodes"]
    kg.build_graph(wipe=True)
    count2 = kg.store.stats()["total_nodes"]
    assert count1 == count2  # same repo → same count
    kg.close()


# ---------------------------------------------------------------------------
# CodeKG — layer accessors
# ---------------------------------------------------------------------------


def test_codekg_graph_property(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "x = 1\n"})
    assert isinstance(kg.graph, CodeGraph)
    kg.close()


def test_codekg_store_property(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "x = 1\n"})
    assert isinstance(kg.store, GraphStore)
    kg.close()


def test_codekg_node_method(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    fns = kg.store.query_nodes(kinds=["function"])
    assert fns
    n = kg.node(fns[0]["id"])
    assert n is not None
    assert n["kind"] == "function"
    kg.close()


def test_codekg_stats(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    s = kg.stats()
    assert "total_nodes" in s
    kg.close()


def test_codekg_context_manager(tmp_path):
    repo = tmp_path / "repo"
    _write_repo(repo, {"mod.py": "x = 1\n"})
    with CodeKG(repo, tmp_path / "codekg.sqlite", tmp_path / "lancedb") as kg:
        kg.build_graph(wipe=True)
        assert kg.stats()["total_nodes"] > 0


def test_codekg_repr(tmp_path):
    kg = CodeKG(tmp_path, tmp_path / "db.sqlite", tmp_path / "ldb")
    r = repr(kg)
    assert "CodeKG" in r
    assert "repo_root" in r


# ---------------------------------------------------------------------------
# QueryResult
# ---------------------------------------------------------------------------


def test_queryresult_to_dict():
    qr = QueryResult(
        query="test",
        seeds=3,
        expanded_nodes=10,
        returned_nodes=5,
        hop=1,
        rels=["CONTAINS", "CALLS"],
        nodes=[
            {
                "id": "fn:mod.py:foo",
                "kind": "function",
                "name": "foo",
                "qualname": "foo",
                "module_path": "mod.py",
                "lineno": 1,
                "end_lineno": 3,
                "docstring": None,
            }
        ],
        edges=[],
    )
    d = qr.to_dict()
    assert d["query"] == "test"
    assert d["seeds"] == 3
    assert len(d["nodes"]) == 1


def test_queryresult_to_json():
    qr = QueryResult(
        query="test",
        seeds=1,
        expanded_nodes=2,
        returned_nodes=1,
        hop=1,
        rels=["CALLS"],
        nodes=[],
        edges=[],
    )
    text = qr.to_json()
    parsed = json.loads(text)
    assert parsed["query"] == "test"


# ---------------------------------------------------------------------------
# SnippetPack
# ---------------------------------------------------------------------------


def test_snippetpack_to_dict():
    sp = SnippetPack(
        query="q",
        seeds=1,
        expanded_nodes=2,
        returned_nodes=1,
        hop=1,
        rels=["CALLS"],
        model="all-MiniLM-L6-v2",
        nodes=[],
        edges=[],
    )
    d = sp.to_dict()
    assert d["model"] == "all-MiniLM-L6-v2"


def test_snippetpack_to_json():
    sp = SnippetPack(
        query="q",
        seeds=1,
        expanded_nodes=2,
        returned_nodes=1,
        hop=1,
        rels=["CALLS"],
        model="all-MiniLM-L6-v2",
        nodes=[],
        edges=[],
    )
    text = sp.to_json()
    assert json.loads(text)["query"] == "q"


def test_snippetpack_to_markdown_contains_query():
    sp = SnippetPack(
        query="find the thing",
        seeds=2,
        expanded_nodes=5,
        returned_nodes=2,
        hop=1,
        rels=["CONTAINS"],
        model="all-MiniLM-L6-v2",
        nodes=[
            {
                "id": "fn:mod.py:foo",
                "kind": "function",
                "name": "foo",
                "qualname": "foo",
                "module_path": "mod.py",
                "lineno": 1,
                "end_lineno": 3,
                "docstring": "Does foo.",
                "snippet": {
                    "path": "mod.py",
                    "start": 1,
                    "end": 3,
                    "text": "    1: def foo():\n    2:     pass",
                },
            },
        ],
        edges=[],
    )
    md = sp.to_markdown()
    assert "find the thing" in md
    assert "foo" in md
    assert "```" in md


def test_snippetpack_save_md(tmp_path):
    sp = SnippetPack(
        query="q",
        seeds=1,
        expanded_nodes=1,
        returned_nodes=1,
        hop=1,
        rels=[],
        model="m",
        nodes=[],
        edges=[],
    )
    out = tmp_path / "out.md"
    sp.save(out, fmt="md")
    assert out.exists()
    assert "KGModule" in out.read_text()


def test_snippetpack_save_json(tmp_path):
    sp = SnippetPack(
        query="q",
        seeds=1,
        expanded_nodes=1,
        returned_nodes=1,
        hop=1,
        rels=[],
        model="m",
        nodes=[],
        edges=[],
    )
    out = tmp_path / "out.json"
    sp.save(out, fmt="json")
    assert out.exists()
    assert json.loads(out.read_text())["query"] == "q"


# ---------------------------------------------------------------------------
# Snippet utilities
# ---------------------------------------------------------------------------


def testsafe_join_valid(tmp_path):
    p = safe_join(tmp_path, "sub/mod.py")
    assert str(p).startswith(str(tmp_path))


def testsafe_join_traversal_raises(tmp_path):
    with pytest.raises(ValueError, match="Unsafe"):
        safe_join(tmp_path, "../../etc/passwd")


def testcompute_span_module():
    start, end = compute_span("module", 1, 100, context=5, max_lines=50, file_nlines=200)
    assert start == 1
    assert end == 50  # capped at max_lines


def testcompute_span_function_with_ast_span():
    start, end = compute_span("function", 10, 20, context=3, max_lines=100, file_nlines=200)
    assert start == 7  # 10 - 3
    assert end == 23  # 20 + 3


def testcompute_span_caps_at_max_lines():
    start, end = compute_span("function", 1, 200, context=0, max_lines=50, file_nlines=300)
    assert (end - start + 1) <= 50


def testcompute_span_empty_file():
    start, end = compute_span("function", 5, 10, context=2, max_lines=50, file_nlines=0)
    assert end < start  # sentinel for empty


def testmake_snippet_line_numbers():
    lines = ["def foo():", "    pass", ""]
    sn = make_snippet("mod.py", lines, 1, 2)
    assert sn["path"] == "mod.py"
    assert sn["start"] == 1
    assert sn["end"] == 2
    assert "1:" in sn["text"]
    assert "2:" in sn["text"]


def testspans_overlap_overlapping():
    assert spans_overlap((1, 10), (8, 20)) is True


def testspans_overlap_adjacent_within_gap():
    assert spans_overlap((1, 5), (7, 15), gap=2) is True


def testspans_overlap_non_overlapping():
    assert spans_overlap((1, 5), (10, 20), gap=2) is False


def testspans_overlap_identical():
    assert spans_overlap((5, 10), (5, 10)) is True


# ---------------------------------------------------------------------------
# compute_span — missing branches
# ---------------------------------------------------------------------------


def testcompute_span_lineno_none_returns_whole_file():
    # kind != "module", lineno=None → fallback to (1, min(file, max))
    start, end = compute_span("function", None, None, context=5, max_lines=50, file_nlines=100)
    assert start == 1
    assert end == 50


def testcompute_span_end_lineno_none_uses_lineno_only():
    # end_lineno is None → use lineno ± context
    start, end = compute_span("function", 10, None, context=3, max_lines=100, file_nlines=200)
    assert start == 7  # 10 - 3
    assert end == 13  # 10 + 3


def testcompute_span_end_lineno_none_caps_at_max_lines():
    start, end = compute_span("function", 10, None, context=100, max_lines=5, file_nlines=200)
    assert (end - start + 1) <= 5


# ---------------------------------------------------------------------------
# read_lines
# ---------------------------------------------------------------------------


def testread_lines_utf8_file(tmp_path):
    p = tmp_path / "src.py"
    p.write_text("line1\nline2\n", encoding="utf-8")
    assert read_lines(p) == ["line1", "line2"]


def testread_lines_missing_file(tmp_path):
    assert read_lines(tmp_path / "nonexistent.py") == []


def testread_lines_invalid_utf8_fallback(tmp_path):
    p = tmp_path / "bad.py"
    p.write_bytes(b"good line\n\xff\xfe bad bytes\n")
    lines = read_lines(p)
    assert len(lines) >= 1  # must not raise; invalid bytes silently dropped


# ---------------------------------------------------------------------------
# Snippet
# ---------------------------------------------------------------------------


def test_snippet_to_dict():
    sn = Snippet(path="mod.py", start=1, end=5, text="    1: def foo():\n    2:     pass")
    d = sn.to_dict()
    assert d == {"path": "mod.py", "start": 1, "end": 5, "text": sn.text}


# ---------------------------------------------------------------------------
# QueryResult — print_summary
# ---------------------------------------------------------------------------


def test_queryresult_print_summary_no_nodes(capsys):
    qr = QueryResult(
        query="empty query",
        seeds=0,
        expanded_nodes=0,
        returned_nodes=0,
        hop=1,
        rels=["CALLS"],
        nodes=[],
        edges=[],
    )
    qr.print_summary()
    out = capsys.readouterr().out
    assert "empty query" in out
    assert "EDGES" in out


def test_queryresult_print_summary_with_nodes_and_edges(capsys):
    qr = QueryResult(
        query="find connection",
        seeds=1,
        expanded_nodes=3,
        returned_nodes=2,
        hop=1,
        rels=["CALLS", "CONTAINS"],
        nodes=[
            {
                "kind": "function",
                "module_path": "mod.py",
                "qualname": "foo",
                "name": "foo",
                "id": "fn:mod.py:foo",
                "docstring": "Does something useful.",
            },
            {
                "kind": "class",
                "module_path": "mod.py",
                "qualname": "Bar",
                "name": "Bar",
                "id": "cls:mod.py:Bar",
                "docstring": None,
            },
        ],
        edges=[{"rel": "CONTAINS", "src": "cls:mod.py:Bar", "dst": "fn:mod.py:foo"}],
    )
    qr.print_summary()
    out = capsys.readouterr().out
    assert "find connection" in out
    assert "fn:mod.py:foo" in out
    assert "Does something useful." in out
    assert "CONTAINS" in out


# ---------------------------------------------------------------------------
# SnippetPack — to_markdown with edges
# ---------------------------------------------------------------------------


def test_snippetpack_to_markdown_with_edges():
    sp = SnippetPack(
        query="q",
        seeds=1,
        expanded_nodes=2,
        returned_nodes=1,
        hop=1,
        rels=["CALLS"],
        model="m",
        nodes=[],
        edges=[{"rel": "CALLS", "src": "fn:a.py:foo", "dst": "fn:b.py:bar"}],
    )
    md = sp.to_markdown()
    assert "fn:a.py:foo" in md
    assert "fn:b.py:bar" in md
    assert "CALLS" in md


# ---------------------------------------------------------------------------
# Fake embedder reused from index tests (avoid real model loading)
# ---------------------------------------------------------------------------


class _FakeEmbedder(Embedder):
    dim = 4

    def embed_texts(self, texts):
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]


# ---------------------------------------------------------------------------
# CodeKG — embedder property
# ---------------------------------------------------------------------------


def test_codekg_embedder_property_lazy_init(tmp_path):
    fake_emb = _FakeEmbedder()
    with patch("code_kg.module.base.SentenceTransformerEmbedder", return_value=fake_emb):
        kg = CodeKG(tmp_path, tmp_path / "db.sqlite", tmp_path / "ldb")
        emb = kg.embedder
        assert emb is fake_emb
        # Second access must return the cached instance (no second construction)
        assert kg.embedder is fake_emb


# ---------------------------------------------------------------------------
# CodeKG — index property
# ---------------------------------------------------------------------------


def test_codekg_index_property_lazy_init(tmp_path):
    kg = CodeKG(tmp_path, tmp_path / "db.sqlite", tmp_path / "ldb")
    kg._embedder = _FakeEmbedder()  # skip real embedder init

    idx = kg.index
    assert isinstance(idx, SemanticIndex)
    # Cached on second access
    assert kg.index is idx


# ---------------------------------------------------------------------------
# CodeKG — build_index (mock SemanticIndex.build to skip real LanceDB)
# ---------------------------------------------------------------------------


def test_codekg_build_index(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})

    mock_idx = MagicMock()
    mock_idx.build.return_value = {"indexed_rows": 7, "dim": 384}
    kg._index = mock_idx

    stats = kg.build_index()
    assert stats.indexed_rows == 7
    assert stats.index_dim == 384
    kg.close()


def test_codekg_build_index_wipe_flag(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})

    mock_idx = MagicMock()
    mock_idx.build.return_value = {"indexed_rows": 3, "dim": 4}
    kg._index = mock_idx

    kg.build_index(wipe=True)
    mock_idx.build.assert_called_once_with(kg.store, wipe=True)
    kg.close()


# ---------------------------------------------------------------------------
# CodeKG — build (full pipeline, LanceDB mocked)
# ---------------------------------------------------------------------------


def test_codekg_build(tmp_path):
    repo = tmp_path / "repo"
    _write_repo(repo, {"mod.py": "def foo(): pass\n"})
    kg = CodeKG(repo, tmp_path / "codekg.sqlite", tmp_path / "ldb")

    mock_idx = MagicMock()
    mock_idx.build.return_value = {"indexed_rows": 3, "dim": 384}
    kg._index = mock_idx

    stats = kg.build(wipe=True)
    assert stats.indexed_rows == 3
    assert stats.index_dim == 384
    kg.close()


# ---------------------------------------------------------------------------
# CodeKG — query (real store, mocked index.search)
# ---------------------------------------------------------------------------


def test_codekg_query_returns_query_result(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    fns = kg.store.query_nodes(kinds=["function"])
    assert fns
    fn_id = fns[0]["id"]

    mock_idx = MagicMock()
    mock_idx.search.return_value = [
        SeedHit(
            id=fn_id,
            kind="function",
            name="foo",
            qualname="foo",
            module_path="mod.py",
            distance=0.1,
            rank=0,
        )
    ]
    kg._index = mock_idx

    result = kg.query("find foo", k=3)
    assert result.query == "find foo"
    assert result.seeds == 1
    assert result.returned_nodes >= 1
    assert any(n["id"] == fn_id for n in result.nodes)
    kg.close()


def test_codekg_query_include_symbols_flag(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    fns = kg.store.query_nodes(kinds=["function"])
    fn_id = fns[0]["id"]

    mock_idx = MagicMock()
    mock_idx.search.return_value = [
        SeedHit(
            id=fn_id,
            kind="function",
            name="foo",
            qualname="foo",
            module_path="mod.py",
            distance=0.1,
            rank=0,
        )
    ]
    kg._index = mock_idx

    # include_symbols=True should not raise and still return a QueryResult
    result = kg.query("find foo", k=3, include_symbols=True)
    assert result.returned_nodes >= 1
    kg.close()


def test_codekg_query_min_score_filters_seeds(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo(): pass\n"})
    fns = kg.store.query_nodes(kinds=["function"])
    fn_id = fns[0]["id"]

    mock_idx = MagicMock()
    mock_idx.search.return_value = [
        SeedHit(
            id=fn_id,
            kind="function",
            name="foo",
            qualname="foo",
            module_path="mod.py",
            distance=2.0,
            rank=0,
        )
    ]
    kg._index = mock_idx

    result = kg.query("find foo", k=3, min_score=0.5)
    assert result.seeds == 0
    assert result.returned_nodes == 0
    kg.close()


def testsemantic_score_from_distance_above_one_stays_positive():
    score = semantic_score_from_distance(1.2)
    assert 0.0 < score < 1.0


def testquery_tokens_split_snake_case():
    toks = query_tokens("missing_lineno_policy cap_or_skip fallback")
    assert "missing_lineno_policy" in toks
    assert "missing" in toks
    assert "lineno" in toks
    assert "policy" in toks
    assert "cap" in toks
    assert "skip" in toks


def testnormalize_query_text_identifier_separators():
    assert normalize_query_text("missing_lineno-policy") == "missing lineno policy"


# ---------------------------------------------------------------------------
# CodeKG — pack (real store + files, mocked index.search)
# ---------------------------------------------------------------------------


def test_codekg_pack_returns_snippet_pack(tmp_path):
    kg = _make_kg(tmp_path, {"mod.py": "def foo():\n    pass\n"})
    fns = kg.store.query_nodes(kinds=["function"])
    assert fns
    fn_id = fns[0]["id"]

    mock_idx = MagicMock()
    mock_idx.search.return_value = [
        SeedHit(
            id=fn_id,
            kind="function",
            name="foo",
            qualname="foo",
            module_path="mod.py",
            distance=0.1,
            rank=0,
        )
    ]
    kg._index = mock_idx

    pack = kg.pack("find foo", k=3)
    assert isinstance(pack, SnippetPack)
    assert pack.query == "find foo"
    assert isinstance(pack.nodes, list)
    assert isinstance(pack.edges, list)
    # Internal keys must be stripped
    for n in pack.nodes:
        assert not any(k.startswith("_") for k in n)
    kg.close()


def test_nested_function_nodes_have_line_metadata(tmp_path):
    kg = _make_kg(
        tmp_path,
        {"mod.py": ("def outer():\n    def inner():\n        return 1\n    return inner()\n")},
    )

    nested = [
        n
        for n in kg.store.query_nodes(kinds=["function"])
        if (n.get("qualname") or "").endswith("outer.inner")
    ]
    assert nested, "expected nested function node to exist"
    assert nested[0]["lineno"] is not None
    assert nested[0]["end_lineno"] is not None
    kg.close()


def test_codekg_pack_max_nodes_limit(tmp_path):
    src = "\n".join(f"def fn{i}(): pass" for i in range(10))
    kg = _make_kg(tmp_path, {"mod.py": src})
    fns = kg.store.query_nodes(kinds=["function"])
    assert len(fns) >= 3

    mock_idx = MagicMock()
    mock_idx.search.return_value = [
        SeedHit(
            id=n["id"],
            kind="function",
            name=n["name"],
            qualname=n["qualname"] or "",
            module_path="mod.py",
            distance=float(i) * 0.1,
            rank=i,
        )
        for i, n in enumerate(fns)
    ]
    kg._index = mock_idx

    pack = kg.pack("many functions", k=len(fns), max_nodes=2)
    assert pack.returned_nodes <= 2
    kg.close()


def test_codekg_pack_max_per_module_limit(tmp_path):
    kg = _make_kg(
        tmp_path,
        {
            "a.py": "def a1():\n    pass\ndef a2():\n    pass\n",
            "b.py": "def b1():\n    pass\ndef b2():\n    pass\n",
        },
    )
    fns = kg.store.query_nodes(kinds=["function"])
    mock_idx = MagicMock()
    mock_idx.search.return_value = [
        SeedHit(
            id=n["id"],
            kind="function",
            name=n["name"],
            qualname=n["qualname"] or "",
            module_path=n["module_path"] or "",
            distance=float(i) * 0.01,
            rank=i,
        )
        for i, n in enumerate(fns)
    ]
    kg._index = mock_idx

    pack = kg.pack("functions", k=len(fns), max_nodes=10, max_per_module=1)
    module_counts: dict[str, int] = {}
    for n in pack.nodes:
        mp = n.get("module_path") or ""
        module_counts[mp] = module_counts.get(mp, 0) + 1
    assert all(count <= 1 for count in module_counts.values())
    kg.close()
