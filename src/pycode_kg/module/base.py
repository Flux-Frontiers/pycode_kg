#!/usr/bin/env python3
"""
module/base.py

KGModule — abstract base class for production-grade knowledge graph modules.

Provides the full PyCodeKG-equivalent infrastructure:
  - build pipeline (extractor → GraphStore → SemanticIndex)
  - hybrid query (semantic seeding + structural graph expansion)
  - snippet packing (source-grounded context for LLMs)
  - lazy-initialised layers (store, index, embedder)
  - snapshot support (delegates to SnapshotManager)

Domain authors subclass KGModule and implement exactly two abstract methods:
  - make_extractor() → KGExtractor
  - kind() → str

Everything else is provided by this class.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from pycode_kg.index import (
    Embedder,
    SemanticIndex,
    SentenceTransformerEmbedder,
    suppress_ingestion_logging,
)
from pycode_kg.module.extractor import EdgeSpec, KGExtractor, NodeSpec
from pycode_kg.module.types import (
    BuildStats,
    QueryResult,
    SnippetPack,
    compute_span,
    docstring_signal,
    lexical_overlap_score,
    make_module_summary,
    make_snippet,
    normalize_query_text,
    query_tokens,
    read_lines,
    safe_join,
    semantic_score_from_distance,
    spans_overlap,
)
from pycode_kg.pycodekg import DEFAULT_MODEL
from pycode_kg.store import DEFAULT_RELS, GraphStore

if TYPE_CHECKING:
    from pycode_kg.pycodekg import Edge, Node


# ---------------------------------------------------------------------------
# Conversion helpers: NodeSpec/EdgeSpec → v0 Node/Edge
# ---------------------------------------------------------------------------


def _nodespec_to_node(spec: NodeSpec) -> Node:
    """Convert a NodeSpec to the v0-locked Node primitive.

    :param spec: NodeSpec from a KGExtractor.
    :return: Node dataclass instance.
    """
    from pycode_kg.pycodekg import Node  # pylint: disable=import-outside-toplevel

    return Node(
        id=spec.node_id,
        kind=spec.kind,
        name=spec.name,
        qualname=spec.qualname,
        module_path=spec.source_path,
        lineno=spec.lineno,
        end_lineno=spec.end_lineno,
        docstring=spec.docstring,
    )


def _edgespec_to_edge(spec: EdgeSpec) -> Edge:
    """Convert an EdgeSpec to the v0-locked Edge primitive.

    :param spec: EdgeSpec from a KGExtractor.
    :return: Edge dataclass instance.
    """
    from pycode_kg.pycodekg import Edge  # pylint: disable=import-outside-toplevel

    evidence = spec.metadata if spec.metadata else None
    return Edge(src=spec.source_id, dst=spec.target_id, rel=spec.relation, evidence=evidence)


# ---------------------------------------------------------------------------
# KGModule
# ---------------------------------------------------------------------------


class KGModule(ABC):
    """Abstract base class for a production-grade knowledge graph module.

    Provides the full build/query/pack infrastructure so domain authors
    only need to implement :meth:`make_extractor` and :meth:`kind`.

    Typical usage by a domain author::

        class TypeScriptKG(KGModule):
            def make_extractor(self):
                return TypeScriptExtractor(self.repo_root)
            def kind(self):
                return "code"
            def analyze(self):
                return "# TypeScript KG Analysis\\n..."

        kg = TypeScriptKG("/path/to/ts-repo")
        kg.build(wipe=True)
        result = kg.query("authentication middleware")
        pack = kg.pack("error handling")

    :param repo_root: Repository root directory.
    :param db_path: SQLite database path (defaults to ``.<kind>kg/graph.sqlite``
                    under ``repo_root``; set ``_default_dir`` in subclass to override).
    :param lancedb_dir: LanceDB directory (defaults to ``.<kind>kg/lancedb``).
    :param model: Sentence-transformer model name for embedding.
    :param table: LanceDB table name.
    """

    #: Override in subclass to change the default artefact directory name.
    #: e.g. ``_default_dir = ".tskg"`` for a TypeScript KG.
    _default_dir: str = ".pycodekg"

    def __init__(
        self,
        repo_root: str | Path,
        db_path: str | Path | None = None,
        lancedb_dir: str | Path | None = None,
        *,
        model: str = DEFAULT_MODEL,
        table: str = "kg_nodes",
    ) -> None:
        """Initialise KGModule and resolve all paths.

        :param repo_root: Repository root directory; resolved to an absolute path.
        :param db_path: Path to the SQLite database file.
        :param lancedb_dir: Directory used by LanceDB for the vector index.
        :param model: Sentence-transformer model name.
        :param table: LanceDB table name.
        """
        self.repo_root = Path(repo_root).resolve()
        _dir = self.repo_root / self._default_dir
        self.db_path = Path(db_path) if db_path is not None else _dir / "graph.sqlite"
        self.lancedb_dir = Path(lancedb_dir) if lancedb_dir is not None else _dir / "lancedb"
        self.model_name = model
        self.table_name = table

        # Lazy-initialised layers
        self._store: GraphStore | None = None
        self._index: SemanticIndex | None = None
        self._embedder: Embedder | None = None

    # ------------------------------------------------------------------
    # Abstract interface — domain authors implement these
    # ------------------------------------------------------------------

    @abstractmethod
    def make_extractor(self) -> KGExtractor:
        """Return the domain-specific extractor for this module.

        Called once per :meth:`build_graph` invocation.  The extractor
        determines what nodes and edges are harvested from the source.

        :return: A :class:`~pycode_kg.module.extractor.KGExtractor` instance.
        """

    @abstractmethod
    def kind(self) -> str:
        """Return the KG kind string for this module.

        For code KGs return ``"code"``, for document KGs ``"doc"``, for
        domain-specific KGs ``"meta"`` (or register a new value in
        ``kg_rag.primitives.KGKind``).

        :return: Kind string used in registry entries and MCP tool names.
        """

    @abstractmethod
    def analyze(self) -> str:
        """Run a full analysis of this KG and return a Markdown report.

        The report format is domain-specific but must:

        1. Begin with ``# <KG Type> Analysis Report``
        2. Include the KG name/path for identification
        3. Include structural metrics (node count, edge count)
        4. Include domain-appropriate quality signals

        Must not raise — return a Markdown error message on failure.

        :return: Markdown-formatted analysis report string.
        """

    # ------------------------------------------------------------------
    # Layer accessors (lazy init)
    # ------------------------------------------------------------------

    @property
    def store(self) -> GraphStore:
        """SQLite persistence layer (lazy-initialised)."""
        if self._store is None:
            self._store = GraphStore(self.db_path)
        return self._store

    @property
    def embedder(self) -> Embedder:
        """Embedding backend (lazy-initialised, shared between index and query)."""
        if self._embedder is None:
            suppress_ingestion_logging()
            self._embedder = SentenceTransformerEmbedder(self.model_name)
        return self._embedder

    @property
    def index(self) -> SemanticIndex:
        """LanceDB semantic index (lazy-initialised)."""
        if self._index is None:
            extractor = self.make_extractor()
            self._index = SemanticIndex(
                self.lancedb_dir,
                embedder=self.embedder,
                table=self.table_name,
                index_kinds=extractor.meaningful_node_kinds(),
            )
        return self._index

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, *, wipe: bool = False) -> BuildStats:
        """Full pipeline: extraction → SQLite → LanceDB.

        :param wipe: Clear existing data before writing.
        :return: :class:`~pycode_kg.module.types.BuildStats`.
        """
        graph_stats = self.build_graph(wipe=wipe)
        index_stats = self.build_index(wipe=wipe)
        graph_stats.indexed_rows = index_stats.indexed_rows
        graph_stats.index_dim = index_stats.index_dim
        return graph_stats

    def build_graph(self, *, wipe: bool = False) -> BuildStats:
        """Extraction → SQLite only (no vector indexing).

        Calls :meth:`make_extractor`, drains the iterator into two lists
        of :class:`~pycode_kg.module.extractor.NodeSpec` and
        :class:`~pycode_kg.module.extractor.EdgeSpec`, converts them to the
        v0 :class:`~pycode_kg.pycodekg.Node` / :class:`~pycode_kg.pycodekg.Edge`
        primitives, writes to SQLite, then calls :meth:`_post_build_hook`
        for any domain-specific post-processing (e.g. symbol resolution).

        :param wipe: Clear existing graph before writing.
        :return: :class:`~pycode_kg.module.types.BuildStats`
                 (``indexed_rows`` will be ``None``).
        """
        extractor = self.make_extractor()
        node_specs: list[NodeSpec] = []
        edge_specs: list[EdgeSpec] = []
        for item in extractor.extract():
            if isinstance(item, NodeSpec):
                node_specs.append(item)
            else:
                edge_specs.append(item)

        nodes = [_nodespec_to_node(s) for s in node_specs]
        edges = [_edgespec_to_edge(s) for s in edge_specs]

        self.store.write(nodes, edges, wipe=wipe)
        self._post_build_hook(self.store)

        s = self.store.stats()
        return BuildStats(
            repo_root=str(self.repo_root),
            db_path=str(self.db_path),
            total_nodes=s["total_nodes"],
            total_edges=s["total_edges"],
            node_counts=s["node_counts"],
            edge_counts=s["edge_counts"],
        )

    def build_index(self, *, wipe: bool = False) -> BuildStats:
        """SQLite → LanceDB only (graph must already exist).

        :param wipe: Delete existing vectors before indexing.
        :return: :class:`~pycode_kg.module.types.BuildStats` with
                 ``indexed_rows`` and ``index_dim`` set.
        """
        idx_stats = self.index.build(self.store, wipe=wipe)
        s = self.store.stats()
        return BuildStats(
            repo_root=str(self.repo_root),
            db_path=str(self.db_path),
            total_nodes=s["total_nodes"],
            total_edges=s["total_edges"],
            node_counts=s["node_counts"],
            edge_counts=s["edge_counts"],
            indexed_rows=idx_stats["indexed_rows"],
            index_dim=idx_stats["dim"],
        )

    def _post_build_hook(self, store: GraphStore) -> None:
        """Hook called after ``store.write()`` in :meth:`build_graph`.

        Override in subclasses for domain-specific post-processing, e.g.
        symbol resolution (``store.resolve_symbols()`` for Python KGs).

        :param store: The :class:`~pycode_kg.store.GraphStore` just written to.
        """

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(
        self,
        q: str,
        *,
        k: int = 8,
        hop: int = 1,
        rels: tuple[str, ...] = DEFAULT_RELS,
        include_symbols: bool = False,
        max_nodes: int = 25,
        min_score: float = 0.0,
        max_per_module: int | None = None,
        rerank_mode: str = "legacy",
        rerank_semantic_weight: float = 0.7,
        rerank_lexical_weight: float = 0.3,
    ) -> QueryResult:
        """Hybrid query: semantic seeding + structural graph expansion.

        Seeds with vector ANN search (LanceDB), expands through the graph
        (SQLite) for ``hop`` hops along ``rels`` edge types, then reranks
        results by the selected strategy.

        :param q: Natural-language query.
        :param k: Top-K semantic hits.
        :param hop: Graph expansion hops (0 = pure semantic).
        :param rels: Edge types to follow during expansion.
        :param include_symbols: Include unresolved stub nodes in results.
        :param max_nodes: Maximum nodes to return.
        :param min_score: Minimum semantic score for seed inclusion.
        :param max_per_module: Optional cap on returned nodes per module path.
        :param rerank_mode: ``'legacy'`` | ``'semantic'`` | ``'hybrid'``.
        :param rerank_semantic_weight: Semantic weight for ``'hybrid'`` mode.
        :param rerank_lexical_weight: Lexical weight for ``'hybrid'`` mode.
        :return: :class:`~pycode_kg.module.types.QueryResult`.
        """
        q_norm = normalize_query_text(q)
        hits = self.index.search(q_norm, k=k)
        if min_score > 0.0:
            hits = [h for h in hits if semantic_score_from_distance(h.distance) >= min_score]
        seed_ids: set[str] = {h.id for h in hits}
        seed_rank: dict[str, float] = {h.id: h.distance for h in hits}
        q_toks = query_tokens(q_norm)

        meta = self.store.expand(seed_ids, hop=hop, rels=rels)
        all_ids = set(meta.keys())

        nodes: list[dict] = []
        kept_ids: set[str] = set()
        module_counts: dict[str, int] = {}

        def _rank_key(nid: str) -> tuple[float, float, int, int, str]:
            prov = meta[nid]
            dist = seed_rank.get(prov.via_seed, 1e9)
            n = self.store.node(nid)
            kind = n["kind"] if n else "symbol"
            sem = semantic_score_from_distance(dist)
            lex = lexical_overlap_score(q_toks, n or {})
            hybrid = (
                rerank_semantic_weight * sem + rerank_lexical_weight * lex
                if (rerank_semantic_weight + rerank_lexical_weight) > 0
                else sem
            )
            if rerank_mode == "hybrid":
                return (-hybrid, float(prov.best_hop), self._kind_priority(kind), 0, nid)
            if rerank_mode == "semantic":
                return (-sem, float(prov.best_hop), self._kind_priority(kind), 0, nid)
            return (float(prov.best_hop), dist, self._kind_priority(kind), 0, nid)

        for nid in sorted(all_ids, key=_rank_key):
            if len(nodes) >= max_nodes:
                break
            n = self.store.node(nid)
            if not n:
                continue
            if not include_symbols and n["kind"] == "symbol":
                continue
            module_path = n.get("module_path") or ""
            if max_per_module is not None and module_path:
                if module_counts.get(module_path, 0) >= max_per_module:
                    continue
                module_counts[module_path] = module_counts.get(module_path, 0) + 1

            prov = meta[nid]
            dist = seed_rank.get(prov.via_seed, 1e9)
            sem = semantic_score_from_distance(dist)
            lex = lexical_overlap_score(q_toks, n)
            n["relevance"] = {
                "score": (
                    rerank_semantic_weight * sem + rerank_lexical_weight * lex
                    if rerank_mode == "hybrid"
                    else sem
                ),
                "semantic": sem,
                "lexical": lex,
                "docstring_signal": docstring_signal(n.get("docstring")),
                "hop": prov.best_hop,
                "via_seed": prov.via_seed,
                "mode": rerank_mode,
            }
            kept_ids.add(nid)
            nodes.append(n)

        edges = self.store.edges_within(kept_ids)
        return QueryResult(
            query=q,
            seeds=len(seed_ids),
            expanded_nodes=len(all_ids),
            returned_nodes=len(nodes),
            hop=hop,
            rels=list(rels),
            nodes=nodes,
            edges=edges,
        )

    # ------------------------------------------------------------------
    # Snippet pack
    # ------------------------------------------------------------------

    def pack(
        self,
        q: str,
        *,
        k: int = 8,
        hop: int = 1,
        rels: tuple[str, ...] = DEFAULT_RELS,
        include_symbols: bool = False,
        context: int = 5,
        max_lines: int = 60,
        max_nodes: int | None = 15,
        min_score: float = 0.0,
        max_per_module: int | None = None,
        rerank_mode: str = "legacy",
        rerank_semantic_weight: float = 0.7,
        rerank_lexical_weight: float = 0.3,
        missing_lineno_policy: str = "cap_or_skip",
    ) -> SnippetPack:
        """Hybrid query + source-grounded snippet extraction.

        :param q: Natural-language query.
        :param k: Top-K semantic hits.
        :param hop: Graph expansion hops.
        :param rels: Edge types to follow during expansion.
        :param include_symbols: Include unresolved stub nodes.
        :param context: Extra context lines around each definition span.
        :param max_lines: Maximum lines per snippet block.
        :param max_nodes: Maximum nodes to return (``None`` = no limit).
        :param min_score: Minimum semantic score for seed inclusion.
        :param max_per_module: Optional cap on returned nodes per module.
        :param rerank_mode: ``'legacy'`` | ``'semantic'`` | ``'hybrid'``.
        :param rerank_semantic_weight: Semantic weight for ``'hybrid'`` mode.
        :param rerank_lexical_weight: Lexical weight for ``'hybrid'`` mode.
        :param missing_lineno_policy: ``'cap_or_skip'`` (default) or ``'legacy'``.
        :return: :class:`~pycode_kg.module.types.SnippetPack`.
        """
        q_norm = normalize_query_text(q)
        hits = self.index.search(q_norm, k=k)
        if min_score > 0.0:
            hits = [h for h in hits if semantic_score_from_distance(h.distance) >= min_score]
        seed_rank: dict[str, dict] = {h.id: {"rank": h.rank, "dist": h.distance} for h in hits}
        seed_ids: set[str] = set(seed_rank.keys())
        q_toks = query_tokens(q_norm)
        warnings: list[str] = []

        meta = self.store.expand(seed_ids, hop=hop, rels=rels)
        all_ids = set(meta.keys())

        raw_nodes: list[dict] = []
        for nid in sorted(all_ids):
            n = self.store.node(nid)
            if not n:
                continue
            if not include_symbols and n["kind"] == "symbol":
                continue

            prov = meta[nid]
            base_dist = seed_rank.get(prov.via_seed, {"dist": 1e9})["dist"]
            kind_pri = self._kind_priority(n["kind"])
            sem = semantic_score_from_distance(base_dist)
            lex = lexical_overlap_score(q_toks, n)
            hybrid = (
                rerank_semantic_weight * sem + rerank_lexical_weight * lex
                if (rerank_semantic_weight + rerank_lexical_weight) > 0
                else sem
            )
            if rerank_mode == "hybrid":
                n["_rank_key"] = (-hybrid, float(prov.best_hop), kind_pri, 0, n["id"])
            elif rerank_mode == "semantic":
                n["_rank_key"] = (-sem, float(prov.best_hop), kind_pri, 0, n["id"])
            else:
                n["_rank_key"] = (float(prov.best_hop), base_dist, kind_pri, 0, n["id"])
            n["_best_hop"] = prov.best_hop
            n["_via_seed"] = prov.via_seed
            n["relevance"] = {
                "score": hybrid if rerank_mode == "hybrid" else sem,
                "semantic": sem,
                "lexical": lex,
                "docstring_signal": docstring_signal(n.get("docstring")),
                "hop": prov.best_hop,
                "via_seed": prov.via_seed,
                "mode": rerank_mode,
            }
            raw_nodes.append(n)

        # Attach spans (needed for dedup)
        file_cache: dict[str, list[str]] = {}
        spans_by_qualname: dict[tuple[str, str], tuple[int, int]] = {}
        for n in raw_nodes:
            mp = n.get("module_path")
            if not mp:
                n["_span"] = None
                continue
            if mp not in file_cache:
                file_cache[mp] = read_lines(safe_join(self.repo_root, mp))
            lines = file_cache[mp]
            lineno = n.get("lineno")
            if n.get("kind") != "module" and lineno is None and missing_lineno_policy != "legacy":
                qualname = n.get("qualname") or ""
                parent_span = None
                if qualname and "." in qualname:
                    parent_key = (mp, qualname.rsplit(".", 1)[0])
                    parent_span = spans_by_qualname.get(parent_key)
                if parent_span:
                    fallback_cap = min(max_lines, max(20, context * 4))
                    p_start, p_end = parent_span
                    capped_end = min(p_end, p_start + fallback_cap - 1)
                    n["_span"] = (p_start, capped_end)
                    warnings.append(
                        f"Missing line metadata for `{n['id']}`; "
                        f"using capped parent span {p_start}-{capped_end}."
                    )
                else:
                    n["_span"] = None
                    warnings.append(
                        f"Missing line metadata for `{n['id']}`; "
                        "snippet omitted (no parent span available)."
                    )
            else:
                n["_span"] = compute_span(
                    n["kind"],
                    lineno,
                    n.get("end_lineno"),
                    context=context,
                    max_lines=max_lines,
                    file_nlines=len(lines),
                )
            if n.get("qualname") and n.get("_span"):
                spans_by_qualname[(mp, n["qualname"])] = n["_span"]

        raw_nodes.sort(key=lambda x: x["_rank_key"])

        # Deduplicate by file + overlapping span
        kept: list[dict] = []
        kept_by_file: dict[str, list[tuple[tuple[int, int], str]]] = {}
        module_counts: dict[str, int] = {}

        for n in raw_nodes:
            if max_nodes is not None and len(kept) >= max_nodes:
                break
            mp = n.get("module_path") or ""
            span = n.get("_span")

            if not mp or not span or span[1] < span[0]:
                kept.append(n)
                continue

            if any(spans_overlap(span, s2) for s2, _ in kept_by_file.get(mp, [])):
                continue

            if max_per_module is not None and mp:
                if module_counts.get(mp, 0) >= max_per_module:
                    continue
                module_counts[mp] = module_counts.get(mp, 0) + 1

            kept.append(n)
            kept_by_file.setdefault(mp, []).append((span, n["id"]))

        kept_ids: set[str] = {n["id"] for n in kept}
        edges = self.store.edges_within(kept_ids)

        # Attach snippets
        for n in kept:
            mp = n.get("module_path")
            span = n.get("_span")
            if not mp or not span:
                continue
            if mp not in file_cache:
                file_cache[mp] = read_lines(safe_join(self.repo_root, mp))
            lines = file_cache[mp]
            start, end = span

            if n.get("kind") == "module" and len(lines) > max_lines:
                contained = [
                    self.store.node(cn_id)
                    for cn_id in (
                        row[0]
                        for row in self.store.con.execute(
                            "SELECT dst FROM edges WHERE src = ? AND rel = 'CONTAINS'",
                            (n["id"],),
                        ).fetchall()
                    )
                    if self.store.node(cn_id) is not None
                ]
                contained_nodes: list[dict] = [c for c in contained if c is not None]
                n["snippet"] = make_module_summary(
                    mp, lines, n.get("docstring"), contained_nodes, max_lines
                )
            elif end >= start and lines:
                n["snippet"] = make_snippet(mp, lines, start, end)

        # Strip internal keys
        for n in kept:
            for key in [k for k in n if k.startswith("_")]:
                del n[key]

        return SnippetPack(
            query=q,
            seeds=len(seed_ids),
            expanded_nodes=len(all_ids),
            returned_nodes=len(kept),
            hop=hop,
            rels=list(rels),
            model=self.model_name,
            nodes=kept,
            edges=edges,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def callers(self, node_id: str, *, rel: str = "CALLS") -> list[dict]:
        """Return all nodes that call *node_id*, resolving through stubs.

        :param node_id: Target node identifier.
        :param rel: Relation type to invert (default ``"CALLS"``).
        :return: Deduplicated list of caller node dicts.
        """
        return self.store.callers_of(node_id, rel=rel)

    def stats(self) -> dict:
        """Return store statistics (node/edge counts by kind/relation).

        :return: Dictionary from :meth:`~pycode_kg.store.GraphStore.stats`.
        """
        return self.store.stats()

    def node(self, node_id: str) -> dict | None:
        """Fetch a single node by ID from the store.

        :param node_id: Stable node identifier.
        :return: Node dict or ``None`` if not found.
        """
        return self.store.node(node_id)

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        if self._store is not None:
            self._store.close()

    def __enter__(self) -> KGModule:
        """Enter the runtime context.

        :return: This :class:`KGModule` instance.
        """
        return self

    def __exit__(self, *_: object) -> None:
        """Exit the runtime context and close the SQLite connection."""
        self.close()

    # ------------------------------------------------------------------
    # Domain hook — subclasses override for node kind ordering
    # ------------------------------------------------------------------

    def _kind_priority(self, kind: str) -> int:
        """Return the sort priority for a node kind (lower = higher priority).

        Used as a tiebreaker in query/pack ranking when scores are equal.
        Default: all unknown kinds sort last (priority 99).

        Override in subclasses for domain-specific ordering::

            def _kind_priority(self, kind):
                return {"function": 0, "class": 1, "module": 2}.get(kind, 99)

        :param kind: Node kind string.
        :return: Integer priority (lower = ranked first).
        """
        return 99
