"""
test_store.py

Tests for GraphStore — SQLite persistence and graph traversal.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from pycode_kg.pycodekg import extract_repo
from pycode_kg.store import GraphStore, ProvMeta


def _make_store(tmp_path: Path, files: dict) -> GraphStore:
    """Write a synthetic repo, extract it, and persist to a temp SQLite."""
    repo = tmp_path / "repo"
    repo.mkdir()
    for rel, src in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))

    nodes, edges = extract_repo(repo)
    db = tmp_path / "pycodekg.sqlite"
    store = GraphStore(db)
    store.write(nodes, edges, wipe=True)
    return store


# ---------------------------------------------------------------------------
# Construction / connection
# ---------------------------------------------------------------------------


def test_store_creates_db(tmp_path):
    db = tmp_path / "test.sqlite"
    store = GraphStore(db)
    _ = store.con  # trigger lazy connect
    assert db.exists()
    store.close()


def test_store_context_manager(tmp_path):
    db = tmp_path / "test.sqlite"
    with GraphStore(db) as store:
        _ = store.con
    assert db.exists()


def test_store_repr(tmp_path):
    db = tmp_path / "test.sqlite"
    store = GraphStore(db)
    assert "GraphStore" in repr(store)
    store.close()


# ---------------------------------------------------------------------------
# write() / clear()
# ---------------------------------------------------------------------------


def test_store_write_and_stats(tmp_path):
    store = _make_store(
        tmp_path,
        {"mod.py": "class Foo:\n    def run(self): pass\ndef bar(): pass\n"},
    )
    s = store.stats()
    assert s["total_nodes"] > 0
    assert s["total_edges"] > 0
    assert "class" in s["node_counts"]
    assert "function" in s["node_counts"]
    store.close()


def test_store_wipe(tmp_path):
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    assert store.stats()["total_nodes"] > 0

    # wipe by writing an empty graph
    store.write([], [], wipe=True)
    assert store.stats()["total_nodes"] == 0
    store.close()


def test_store_clear(tmp_path):
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    store.clear()
    assert store.stats()["total_nodes"] == 0
    assert store.stats()["total_edges"] == 0
    store.close()


def test_store_upsert_idempotent(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "mod.py").write_text("def foo(): pass\n")
    nodes, edges = extract_repo(repo)

    db = tmp_path / "pycodekg.sqlite"
    store = GraphStore(db)
    store.write(nodes, edges)
    count1 = store.stats()["total_nodes"]
    store.write(nodes, edges)  # write again — should upsert, not duplicate
    count2 = store.stats()["total_nodes"]
    assert count1 == count2
    store.close()


# ---------------------------------------------------------------------------
# node()
# ---------------------------------------------------------------------------


def test_store_node_fetch(tmp_path):
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    nodes = store.query_nodes(kinds=["function"])
    assert nodes
    nid = nodes[0]["id"]
    n = store.node(nid)
    assert n is not None
    assert n["id"] == nid
    assert n["kind"] == "function"
    store.close()


def test_store_node_missing_returns_none(tmp_path):
    db = tmp_path / "empty.sqlite"
    store = GraphStore(db)
    assert store.node("fn:nonexistent.py:ghost") is None
    store.close()


# ---------------------------------------------------------------------------
# query_nodes()
# ---------------------------------------------------------------------------


def test_store_query_nodes_by_kind(tmp_path):
    store = _make_store(
        tmp_path,
        {"mod.py": "class Foo:\n    def run(self): pass\ndef bar(): pass\n"},
    )
    fns = store.query_nodes(kinds=["function"])
    assert all(n["kind"] == "function" for n in fns)
    methods = store.query_nodes(kinds=["method"])
    assert all(n["kind"] == "method" for n in methods)
    store.close()


def test_store_query_nodes_by_module(tmp_path):
    store = _make_store(
        tmp_path,
        {
            "a.py": "def alpha(): pass\n",
            "b.py": "def beta(): pass\n",
        },
    )
    a_nodes = store.query_nodes(module="a.py")
    assert all(n["module_path"] == "a.py" for n in a_nodes)
    store.close()


def test_store_query_nodes_no_filter_returns_all(tmp_path):
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    all_nodes = store.query_nodes()
    assert len(all_nodes) == store.stats()["total_nodes"]
    store.close()


# ---------------------------------------------------------------------------
# edges_within()
# ---------------------------------------------------------------------------


def test_store_edges_within(tmp_path):
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    all_nodes = store.query_nodes()
    node_ids = {n["id"] for n in all_nodes}
    edges = store.edges_within(node_ids)
    assert isinstance(edges, list)
    # All returned edges must have both endpoints in the set
    for e in edges:
        assert e["src"] in node_ids
        assert e["dst"] in node_ids
    store.close()


def test_store_edges_within_empty_set(tmp_path):
    db = tmp_path / "empty.sqlite"
    store = GraphStore(db)
    assert store.edges_within(set()) == []
    store.close()


# ---------------------------------------------------------------------------
# expand()
# ---------------------------------------------------------------------------


def test_store_expand_hop0(tmp_path):
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    fns = store.query_nodes(kinds=["function"])
    seed = {fns[0]["id"]}
    meta = store.expand(seed, hop=0)
    # hop=0 → only the seeds themselves
    assert set(meta.keys()) == seed
    assert meta[fns[0]["id"]].best_hop == 0
    store.close()


def test_store_expand_hop1_reaches_neighbors(tmp_path):
    store = _make_store(
        tmp_path,
        {"mod.py": "class Foo:\n    def run(self): pass\n"},
    )
    cls_nodes = store.query_nodes(kinds=["class"])
    seed = {cls_nodes[0]["id"]}
    meta = store.expand(seed, hop=1)
    # Should reach the method via CONTAINS
    assert len(meta) > 1
    store.close()


def test_store_expand_provmeta_types(tmp_path):
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    fns = store.query_nodes(kinds=["function"])
    seed = {fns[0]["id"]}
    meta = store.expand(seed, hop=1)
    for nid, prov in meta.items():
        assert isinstance(prov, ProvMeta)
        assert isinstance(prov.best_hop, int)
        assert isinstance(prov.via_seed, str)
    store.close()


def test_store_expand_seed_has_hop0(tmp_path):
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    fns = store.query_nodes(kinds=["function"])
    seed_id = fns[0]["id"]
    meta = store.expand({seed_id}, hop=2)
    assert meta[seed_id].best_hop == 0
    assert meta[seed_id].via_seed == seed_id
    store.close()


def test_store_expand_non_seed_hop_positive(tmp_path):
    store = _make_store(
        tmp_path,
        {"mod.py": "class Foo:\n    def run(self): pass\n"},
    )
    mod_nodes = store.query_nodes(kinds=["module"])
    seed = {mod_nodes[0]["id"]}
    meta = store.expand(seed, hop=2)
    non_seeds = {nid: p for nid, p in meta.items() if nid not in seed}
    assert all(p.best_hop > 0 for p in non_seeds.values())
    store.close()


# ---------------------------------------------------------------------------
# stats() — domain-specific fields
# ---------------------------------------------------------------------------


def test_stats_kind_counts(tmp_path):
    """module_count, class_count, function_count, method_count match actual nodes."""
    store = _make_store(
        tmp_path,
        {
            "mod.py": (
                "class Foo:\n"
                "    def run(self): pass\n"
                "    def stop(self): pass\n"
                "def helper(): pass\n"
            )
        },
    )
    s = store.stats()
    assert s["module_count"] == 1
    assert s["class_count"] == 1
    assert s["function_count"] == 1
    assert s["method_count"] == 2
    store.close()


def test_stats_docstring_coverage_full(tmp_path):
    """All functions/methods have docstrings → coverage == 1.0."""
    store = _make_store(
        tmp_path,
        {
            "mod.py": (
                "def alpha():\n"
                '    """Does alpha."""\n'
                "    pass\n"
                "def beta():\n"
                '    """Does beta."""\n'
                "    pass\n"
            )
        },
    )
    s = store.stats()
    assert s["docstring_coverage"] == 1.0
    store.close()


def test_stats_docstring_coverage_partial(tmp_path):
    """Half with docstrings → coverage == 0.5."""
    store = _make_store(
        tmp_path,
        {
            "mod.py": (
                'def with_doc():\n    """Has a docstring."""\n    pass\ndef no_doc():\n    pass\n'
            )
        },
    )
    s = store.stats()
    assert s["docstring_coverage"] == 0.5
    store.close()


def test_stats_docstring_coverage_none(tmp_path):
    """No functions/methods → coverage == 0.0 (not a division error)."""
    store = _make_store(tmp_path, {"mod.py": "X = 1\n"})
    s = store.stats()
    assert s["docstring_coverage"] == 0.0
    store.close()


def test_stats_snapshot_count_no_manifest(tmp_path):
    """snapshot_count is 0 when no manifest exists adjacent to the DB."""
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    assert store.stats()["snapshot_count"] == 0
    store.close()


def test_stats_snapshot_count_with_manifest(tmp_path):
    """snapshot_count reflects the number of entries in the manifest."""
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    snapshots_dir = store.db_path.parent / "snapshots"
    snapshots_dir.mkdir()
    manifest = {
        "snapshots": [
            {"key": "abc123", "timestamp": "2025-01-01T00:00:00Z"},
            {"key": "def456", "timestamp": "2025-01-02T00:00:00Z"},
            {"key": "ghi789", "timestamp": "2025-01-03T00:00:00Z"},
        ]
    }
    (snapshots_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert store.stats()["snapshot_count"] == 3
    store.close()


def test_stats_snapshot_count_corrupt_manifest(tmp_path):
    """snapshot_count is 0 when the manifest is unreadable; no exception raised."""
    store = _make_store(tmp_path, {"mod.py": "def foo(): pass\n"})
    snapshots_dir = store.db_path.parent / "snapshots"
    snapshots_dir.mkdir()
    (snapshots_dir / "manifest.json").write_text("not json {{", encoding="utf-8")
    assert store.stats()["snapshot_count"] == 0
    store.close()


def test_callers_of_prefers_import_disambiguation_for_same_name(tmp_path):
    """Caller resolution should avoid linking same-name functions across modules."""
    store = _make_store(
        tmp_path,
        {
            "mcp_server.py": "def main():\n    return 'mcp'\n",
            "app.py": "def main():\n    return 'app'\n",
            "cli/cmd_mcp.py": ("from mcp_server import main\n\ndef mcp():\n    return main()\n"),
        },
    )
    store.resolve_symbols()

    mcp_main = store.query_nodes(kinds=["function"], module="mcp_server.py")
    app_main = store.query_nodes(kinds=["function"], module="app.py")
    assert mcp_main and app_main

    callers_mcp = store.callers_of(mcp_main[0]["id"], rel="CALLS")
    callers_app = store.callers_of(app_main[0]["id"], rel="CALLS")

    caller_ids_mcp = {c["id"] for c in callers_mcp}
    caller_ids_app = {c["id"] for c in callers_app}
    assert any("cmd_mcp.py:mcp" in cid for cid in caller_ids_mcp)
    assert not any("cmd_mcp.py:mcp" in cid for cid in caller_ids_app)
    store.close()
