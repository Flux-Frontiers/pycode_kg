#!/usr/bin/env python3
"""
store.py

GraphStore — SQLite persistence layer for the Code Knowledge Graph.

SQLite is the authoritative, canonical store.
No embeddings, no LanceDB, no AST.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Sequence
from pathlib import Path

from code_kg.codekg import Edge, Node
from code_kg.utils import node_id

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS nodes (
  id           TEXT PRIMARY KEY,
  kind         TEXT NOT NULL,
  name         TEXT NOT NULL,
  qualname     TEXT,
  module_path  TEXT,
  lineno       INTEGER,
  end_lineno   INTEGER,
  docstring    TEXT
);

CREATE TABLE IF NOT EXISTS edges (
  src      TEXT NOT NULL,
  rel      TEXT NOT NULL,
  dst      TEXT NOT NULL,
  evidence TEXT,
  PRIMARY KEY (src, rel, dst)
);

CREATE INDEX IF NOT EXISTS idx_nodes_kind   ON nodes(kind);
CREATE INDEX IF NOT EXISTS idx_nodes_name   ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_nodes_module ON nodes(module_path);

CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
CREATE INDEX IF NOT EXISTS idx_edges_rel ON edges(rel);
"""

# Default edge types used for graph expansion
DEFAULT_RELS: tuple[str, ...] = ("CONTAINS", "CALLS", "IMPORTS", "INHERITS")


def _module_to_dotted_variants(module_path: str | None) -> tuple[str, ...]:
    """Convert module path to dotted notation, including common src-layout alias.

    :param module_path: Path like ``src/pkg/mod.py``.
    :return: Tuple of dotted variants, e.g. ``("src.pkg.mod", "pkg.mod")``.
    """
    if not module_path:
        return ()
    if module_path.endswith(".py"):
        module_path = module_path[:-3]
    dotted = module_path.replace("/", ".")
    variants = [dotted]
    if dotted.startswith("src."):
        variants.append(dotted[4:])
    return tuple(dict.fromkeys(v for v in variants if v))


# ---------------------------------------------------------------------------
# Provenance metadata returned by expand()
# ---------------------------------------------------------------------------


class ProvMeta:
    """
    Provenance metadata for a node returned by :meth:`GraphStore.expand`.

    :param best_hop: Minimum hop distance from any seed node.
    :param via_seed: ID of the seed node that yielded the shortest path.
    """

    __slots__ = ("best_hop", "via_seed")

    def __init__(self, best_hop: int, via_seed: str) -> None:
        """Initialise provenance metadata for a graph node.

        :param best_hop: Minimum hop distance from any seed node.
        :param via_seed: ID of the seed node that yielded the shortest path.
        """
        self.best_hop = best_hop
        self.via_seed = via_seed

    def __repr__(self) -> str:
        """Return a developer-readable representation of this ProvMeta.

        :return: String of the form ``ProvMeta(best_hop=..., via_seed=...)``.
        """
        return f"ProvMeta(best_hop={self.best_hop}, via_seed={self.via_seed!r})"


# ---------------------------------------------------------------------------
# GraphStore
# ---------------------------------------------------------------------------


class GraphStore:
    """
    SQLite-backed authoritative store for the Code Knowledge Graph.

    Manages the ``nodes`` and ``edges`` tables and provides graph
    traversal primitives used by the query layer.

    Example::

        store = GraphStore("codekg.sqlite")
        store.write(nodes, edges, wipe=True)
        print(store.stats())

        # fetch a single node
        n = store.node("fn:src/foo.py:bar")

        # expand from seeds
        meta = store.expand({"fn:src/foo.py:bar"}, hop=2)

    :param db_path: Path to the SQLite database file (created if absent).
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialise the store against a SQLite database file.

        :param db_path: Path to the SQLite database file (created if absent).
        """
        self.db_path = Path(db_path)
        self._con: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @property
    def con(self) -> sqlite3.Connection:
        """Lazy SQLite connection (created on first access)."""
        if self._con is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._con = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,  # safe: read-heavy; writes serialised by SQLite WAL
            )
            self._con.executescript(_SCHEMA_SQL)
        return self._con

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        if self._con is not None:
            self._con.close()
            self._con = None

    def __enter__(self) -> GraphStore:
        """Enter the context manager.

        :return: This :class:`GraphStore` instance.
        """
        return self

    def __exit__(self, *_: object) -> None:
        """Exit the context manager, closing the SQLite connection."""
        self.close()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Delete all nodes and edges."""
        self.con.execute("DELETE FROM edges;")
        self.con.execute("DELETE FROM nodes;")
        self.con.commit()

    def write(
        self,
        nodes: Sequence[Node],
        edges: Sequence[Edge],
        *,
        wipe: bool = False,
    ) -> None:
        """
        Persist a complete graph to SQLite.

        :param nodes: Node list from :class:`~code_kg.graph.CodeGraph`.
        :param edges: Edge list from :class:`~code_kg.graph.CodeGraph`.
        :param wipe: If ``True``, clear existing data before writing.
        """
        if wipe:
            self.clear()
        self._upsert_nodes(nodes)
        self._upsert_edges(edges)

    def _upsert_nodes(self, nodes: Iterable[Node]) -> None:
        """Insert or update a batch of nodes in the ``nodes`` table.

        :param nodes: Iterable of :class:`~code_kg.codekg.Node` objects to persist.
        """
        rows = [
            (
                n.id,
                n.kind,
                n.name,
                n.qualname,
                n.module_path,
                n.lineno,
                n.end_lineno,
                n.docstring,
            )
            for n in nodes
        ]
        self.con.executemany(
            """
            INSERT INTO nodes
              (id, kind, name, qualname, module_path, lineno, end_lineno, docstring)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              kind=excluded.kind,
              name=excluded.name,
              qualname=excluded.qualname,
              module_path=excluded.module_path,
              lineno=excluded.lineno,
              end_lineno=excluded.end_lineno,
              docstring=excluded.docstring
            """,
            rows,
        )
        self.con.commit()

    def _upsert_edges(self, edges: Iterable[Edge]) -> None:
        """Insert or update a batch of edges in the ``edges`` table.

        :param edges: Iterable of :class:`~code_kg.codekg.Edge` objects to persist.
        """
        rows = [
            (
                e.src,
                e.rel,
                e.dst,
                (json.dumps(e.evidence, ensure_ascii=False) if e.evidence is not None else None),
            )
            for e in edges
        ]
        self.con.executemany(
            """
            INSERT INTO edges (src, rel, dst, evidence)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(src, rel, dst) DO UPDATE SET
              evidence=excluded.evidence
            """,
            rows,
        )
        self.con.commit()

    # ------------------------------------------------------------------
    # Read — single node
    # ------------------------------------------------------------------

    def node(self, node_id: str) -> dict | None:
        """
        Fetch a single node by id.

        :param node_id: Stable node identifier.
        :return: Node dict or ``None`` if not found.
        """
        row = self.con.execute(
            """
            SELECT id, kind, name, qualname, module_path, lineno, end_lineno, docstring
            FROM nodes WHERE id = ?
            """,
            (node_id,),
        ).fetchone()
        return _row_to_node(row) if row else None

    # ------------------------------------------------------------------
    # Read — filtered node lists
    # ------------------------------------------------------------------

    def query_nodes(
        self,
        *,
        kinds: Sequence[str] | None = None,
        module: str | None = None,
    ) -> list[dict]:
        """
        Return nodes matching optional filters.

        :param kinds: Restrict to these node kinds (e.g. ``["function", "method"]``).
        :param module: Restrict to nodes in this module path (exact match).
        :return: List of node dicts.
        """
        clauses: list[str] = []
        params: list[object] = []

        if kinds:
            placeholders = ",".join("?" for _ in kinds)
            clauses.append(f"kind IN ({placeholders})")
            params.extend(kinds)

        if module is not None:
            clauses.append("module_path = ?")
            params.append(module)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.con.execute(
            f"""
            SELECT id, kind, name, qualname, module_path, lineno, end_lineno, docstring
            FROM nodes {where}
            ORDER BY module_path, lineno
            """,
            params,
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    # ------------------------------------------------------------------
    # Read — edges
    # ------------------------------------------------------------------

    def edges_within(self, node_ids: set[str]) -> list[dict]:
        """
        Return all edges where both ``src`` and ``dst`` are in *node_ids*.

        :param node_ids: Set of node IDs to restrict to.
        :return: List of edge dicts with keys ``src``, ``rel``, ``dst``, ``evidence``.
        """
        if not node_ids:
            return []

        self.con.execute("DROP TABLE IF EXISTS _tmp_ids;")
        self.con.execute("CREATE TEMP TABLE _tmp_ids (id TEXT PRIMARY KEY);")
        self.con.executemany("INSERT INTO _tmp_ids (id) VALUES (?)", [(i,) for i in node_ids])
        rows = self.con.execute(
            """
            SELECT e.src, e.rel, e.dst, e.evidence
            FROM edges e
            JOIN _tmp_ids s ON s.id = e.src
            JOIN _tmp_ids d ON d.id = e.dst
            """
        ).fetchall()
        return [{"src": r[0], "rel": r[1], "dst": r[2], "evidence": r[3]} for r in rows]

    # ------------------------------------------------------------------
    # Graph traversal
    # ------------------------------------------------------------------

    def expand(
        self,
        seed_ids: set[str],
        *,
        hop: int = 1,
        rels: tuple[str, ...] = DEFAULT_RELS,
    ) -> dict[str, ProvMeta]:
        """
        Expand the graph from *seed_ids* up to *hop* hops.

        Returns a mapping from every reachable node ID to its
        :class:`ProvMeta` (minimum hop distance and originating seed).

        :param seed_ids: Starting node IDs (hop 0).
        :param hop: Maximum number of hops to traverse.
        :param rels: Edge relation types to follow.
        :return: ``{node_id: ProvMeta}`` for all reachable nodes.
        """
        rels = tuple(rels)
        meta: dict[str, ProvMeta] = {sid: ProvMeta(best_hop=0, via_seed=sid) for sid in seed_ids}
        frontier: set[str] = set(seed_ids)

        for h in range(1, hop + 1):
            nxt: set[str] = set()
            for nid in frontier:
                rows = self.con.execute(
                    f"""
                    SELECT src, dst FROM edges
                    WHERE (src = ? OR dst = ?)
                      AND rel IN ({",".join("?" for _ in rels)})
                    """,
                    (nid, nid, *rels),
                ).fetchall()
                for src, dst in rows:
                    for cand in (src, dst):
                        if cand not in meta:
                            meta[cand] = ProvMeta(
                                best_hop=h,
                                via_seed=meta[nid].via_seed,
                            )
                            nxt.add(cand)
                        elif h < meta[cand].best_hop:
                            meta[cand] = ProvMeta(
                                best_hop=h,
                                via_seed=meta[nid].via_seed,
                            )
                            nxt.add(cand)
            frontier = nxt

        return meta

    # ------------------------------------------------------------------
    # Symbol resolution
    # ------------------------------------------------------------------

    def resolve_symbols(self) -> int:
        """
        Add ``RESOLVES_TO`` edges from ``sym:`` stub nodes to their
        first-party definitions (``fn:``, ``cls:``, ``m:``, ``mod:``).

        The AST visitor emits ``CALLS → sym:Foo`` for any call whose target
        cannot be resolved at walk time (imported names, attribute accesses,
        etc.).  This post-build step links those stubs to the canonical
        definition nodes by matching on the ``name`` field, making fan-in
        queries (who calls X?) work correctly via graph traversal.

        Matching is by name only, so a ``sym:close`` stub will acquire
        ``RESOLVES_TO`` edges to *every* in-repo node named ``close``.
        Agents can use the graph context to disambiguate.  The operation is
        idempotent — duplicate edges are silently ignored.

        :return: Number of new ``RESOLVES_TO`` edges written.
        """
        sym_rows = self.con.execute(
            "SELECT id, name, qualname FROM nodes WHERE kind = 'symbol'"
        ).fetchall()

        def_rows = self.con.execute(
            """
            SELECT id, kind, name, qualname, module_path
            FROM nodes
            WHERE kind != 'symbol' AND name IS NOT NULL
            """
        ).fetchall()

        name_to_defs: dict[str, list[str]] = {}
        dotted_to_defs: dict[str, list[str]] = {}
        for def_id, def_kind, def_name, def_qualname, def_module_path in def_rows:
            name_to_defs.setdefault(def_name, []).append(def_id)

            module_dotted_variants = _module_to_dotted_variants(def_module_path)
            if def_kind == "module":
                for module_dotted in module_dotted_variants:
                    dotted_to_defs.setdefault(module_dotted, []).append(def_id)
            elif module_dotted_variants and def_qualname:
                for module_dotted in module_dotted_variants:
                    dotted_key = f"{module_dotted}.{def_qualname}"
                    dotted_to_defs.setdefault(dotted_key, []).append(def_id)

        edges: list[tuple[str, str, str, str]] = []
        for sym_id, sym_name, sym_qualname in sym_rows:
            if not sym_name:
                continue

            candidates: list[str] = []
            mode = "name_fallback"
            confidence = "medium"

            if sym_qualname and "." in sym_qualname:
                exact = dotted_to_defs.get(sym_qualname, [])
                if exact:
                    candidates = exact
                    mode = "exact_qualname"
                    confidence = "high"

            if not candidates:
                candidates = name_to_defs.get(sym_name, [])
                if len(candidates) > 1:
                    mode = "name_fallback_ambiguous"
                    confidence = "low"

            for def_id in candidates:
                evidence = {
                    "resolution_mode": mode,
                    "confidence": confidence,
                    "symbol": sym_id,
                }
                if mode == "name_fallback_ambiguous":
                    evidence["candidate_count"] = len(candidates)
                edges.append(
                    (
                        sym_id,
                        "RESOLVES_TO",
                        def_id,
                        json.dumps(evidence, ensure_ascii=False),
                    )
                )

        if edges:
            self.con.executemany(
                """
                INSERT INTO edges (src, rel, dst, evidence)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(src, rel, dst) DO UPDATE SET
                  evidence=excluded.evidence
                """,
                edges,
            )
            self.con.commit()

        return len(edges)

    # ------------------------------------------------------------------
    # Caller lookup (fan-in)
    # ------------------------------------------------------------------

    def callers_of(self, node_id: str, *, rel: str = "CALLS") -> list[dict]:
        """
        Return all nodes that have a *rel* edge pointing at *node_id*,
        including cross-module callers that reference it via ``sym:`` stubs.

        Two-phase lookup:

        1. Direct: ``edges WHERE dst = node_id AND rel = rel``
        2. Indirect: find all ``sym:`` stubs with a ``RESOLVES_TO`` edge to
           *node_id*, then collect their incoming *rel* edges.

        Caller nodes are deduplicated and returned as node dicts.

        :param node_id: Target node identifier (e.g. ``fn:src/foo.py:bar``).
        :param rel: Relation type to invert (default ``"CALLS"``).
        :return: List of caller node dicts, deduplicated.
        """
        direct = self.con.execute(
            "SELECT src, evidence FROM edges WHERE dst = ? AND rel = ?",
            (node_id, rel),
        ).fetchall()

        stubs = self.con.execute(
            "SELECT src FROM edges WHERE dst = ? AND rel = 'RESOLVES_TO'",
            (node_id,),
        ).fetchall()

        stub_callers: list[tuple[str, str | None, str]] = []
        for (stub_id,) in stubs:
            rows = self.con.execute(
                "SELECT src, evidence FROM edges WHERE dst = ? AND rel = ?",
                (stub_id, rel),
            ).fetchall()
            for src_id, evidence in rows:
                stub_callers.append((src_id, evidence, stub_id))

        seen: set[str] = set()
        result: list[dict] = []
        for caller_id, evidence in direct:
            if caller_id in seen:
                continue
            seen.add(caller_id)
            n = self.node(caller_id)
            if n:
                lineno = _parse_call_site_lineno(evidence)
                if lineno is not None:
                    n = {**n, "call_site_lineno": lineno}
                result.append(n)

        for caller_id, evidence, _stub_id in stub_callers:
            if caller_id in seen:
                continue
            if not self._is_compatible_stub_caller(caller_id, evidence, node_id):
                continue
            seen.add(caller_id)
            n = self.node(caller_id)
            if n:
                lineno = _parse_call_site_lineno(evidence)
                if lineno is not None:
                    n = {**n, "call_site_lineno": lineno}
                result.append(n)

        return result

    def _is_compatible_stub_caller(
        self, caller_id: str, evidence: str | None, target_node_id: str
    ) -> bool:
        """Validate a stub-resolved caller against import hints from its module.

        If the call expression name is imported in the caller's module, retain
        the caller only when one such import symbol resolves to ``target_node_id``.
        When no import hints exist, caller is kept (no extra signal available).

        :param caller_id: Caller node ID from an incoming CALLS edge.
        :param evidence: JSON-encoded edge evidence from the CALLS edge.
        :param target_node_id: Target node currently being reverse-resolved.
        :return: ``True`` if caller is compatible with target resolution.
        """
        if not evidence:
            return True
        try:
            ev = json.loads(evidence)
        except (TypeError, json.JSONDecodeError):
            return True

        expr = ev.get("expr")
        if not isinstance(expr, str) or not expr:
            return True

        short_name = expr.split(".")[-1]
        caller_node = self.node(caller_id)
        if not caller_node:
            return True

        module_path = caller_node.get("module_path")
        if not module_path:
            return True

        module_id = node_id("module", module_path, None)
        import_rows = self.con.execute(
            "SELECT dst FROM edges WHERE src = ? AND rel = 'IMPORTS'",
            (module_id,),
        ).fetchall()

        matching_import_symbols = [
            sym_id
            for (sym_id,) in import_rows
            if sym_id.startswith("sym:") and sym_id.split(".")[-1] == short_name
        ]
        if not matching_import_symbols:
            return True

        for sym_id in matching_import_symbols:
            hit = self.con.execute(
                "SELECT 1 FROM edges WHERE src = ? AND rel = 'RESOLVES_TO' AND dst = ? LIMIT 1",
                (sym_id, target_node_id),
            ).fetchone()
            if hit:
                return True
        return False

    def edges_from(
        self, node_id: str, *, rel: str = "CALLS", limit: int | None = None
    ) -> list[dict]:
        """
        Return all edges originating from *node_id* with the given relation type.

        :param node_id: Source node identifier (e.g. ``fn:src/foo.py:bar``).
        :param rel: Relation type to match (default ``"CALLS"``).
        :param limit: Maximum number of edges to return (``None`` for unlimited).
        :return: List of edge dicts with keys ``src``, ``rel``, ``dst``, ``evidence``.
        """
        query = "SELECT src, rel, dst, evidence FROM edges WHERE src = ? AND rel = ?"
        params: list[object] = [node_id, rel]
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        rows = self.con.execute(query, params).fetchall()
        return [{"src": r[0], "rel": r[1], "dst": r[2], "evidence": r[3]} for r in rows]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """
        Return node and edge counts by kind/relation.

        ``meaningful_nodes`` excludes ``sym:`` infrastructure stubs so callers
        get an accurate count of real code entities (modules, classes,
        functions, methods).

        :return: dict with ``total_nodes``, ``meaningful_nodes``,
                 ``total_edges``, ``node_counts``, ``edge_counts``.
        """
        node_rows = self.con.execute("SELECT kind, COUNT(*) FROM nodes GROUP BY kind").fetchall()
        edge_rows = self.con.execute("SELECT rel, COUNT(*) FROM edges GROUP BY rel").fetchall()
        total_nodes = self.con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        total_edges = self.con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        symbol_count = self.con.execute(
            "SELECT COUNT(*) FROM nodes WHERE kind = 'symbol'"
        ).fetchone()[0]
        return {
            "db_path": str(self.db_path),
            "total_nodes": total_nodes,
            "meaningful_nodes": total_nodes - symbol_count,
            "total_edges": total_edges,
            "node_counts": {r[0]: r[1] for r in node_rows},
            "edge_counts": {r[0]: r[1] for r in edge_rows},
        }

    def __repr__(self) -> str:
        """Return a developer-readable representation of this GraphStore.

        :return: String of the form ``GraphStore(db_path=...)``.
        """
        return f"GraphStore(db_path={self.db_path!r})"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_call_site_lineno(evidence: str | None) -> int | None:
    """Parse and extract the call-site line number from a JSON evidence string.

    :param evidence: JSON-encoded edge evidence, e.g. ``'{"lineno": 42, "expr": "foo"}'``.
    :return: Line number integer, or ``None`` if unavailable or unparseable.
    """
    if not evidence:
        return None
    try:
        ev = json.loads(evidence)
        lineno = ev.get("lineno")
        return int(lineno) if lineno is not None else None
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _row_to_node(row: tuple) -> dict:
    """Convert a raw SQLite row into a node dict.

    :param row: Tuple of ``(id, kind, name, qualname, module_path, lineno, end_lineno, docstring)``.
    :return: Dict with the same keys suitable for JSON serialisation.
    """
    return {
        "id": row[0],
        "kind": row[1],
        "name": row[2],
        "qualname": row[3],
        "module_path": row[4],
        "lineno": row[5],
        "end_lineno": row[6],
        "docstring": row[7],
    }
