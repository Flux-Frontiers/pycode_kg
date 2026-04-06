"""
code_kg.module — KGModule SDK for building production-grade knowledge graph modules.

This subpackage provides the abstract base class and supporting types that
enable any knowledge domain (Python code, TypeScript, genomics, legal text, …)
to be expressed as a full-featured knowledge graph with:

  - SQLite graph storage  (:class:`~code_kg.store.GraphStore`)
  - LanceDB vector index  (:class:`~code_kg.index.SemanticIndex`)
  - Hybrid semantic + structural query (:meth:`~KGModule.query`)
  - Source-grounded snippet packing (:meth:`~KGModule.pack`)
  - Snapshot management  (:class:`~code_kg.snapshots.SnapshotManager`)

Usage — building a new domain KG::

    from code_kg.module import KGModule, KGExtractor, NodeSpec, EdgeSpec

    class MyExtractor(KGExtractor):
        def node_kinds(self): return ["entity", "relation"]
        def edge_kinds(self): return ["LINKED_TO"]
        def extract(self):
            for item in parse_my_domain(self.repo_path):
                yield NodeSpec(node_id=item.id, kind="entity", ...)

    class MyKG(KGModule):
        def make_extractor(self): return MyExtractor(self.repo_root)
        def kind(self): return "meta"
        def analyze(self): return "# My KG Analysis\\n..."

    kg = MyKG("/path/to/data")
    kg.build(wipe=True)
    result = kg.query("some concept")

The existing Python-backed :class:`~code_kg.kg.CodeKG` is a concrete
implementation of :class:`KGModule` using :class:`CodeKGExtractor`.
"""

from code_kg.module.base import KGModule
from code_kg.module.extractor import CodeKGExtractor, EdgeSpec, KGExtractor, NodeSpec
from code_kg.module.types import (
    BuildStats,
    QueryResult,
    Snippet,
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

__all__ = [
    # Core abstractions
    "KGModule",
    "KGExtractor",
    "CodeKGExtractor",
    # Intermediate spec types
    "NodeSpec",
    "EdgeSpec",
    # Result types
    "BuildStats",
    "QueryResult",
    "Snippet",
    "SnippetPack",
    # Utilities (exported for subclass use)
    "semantic_score_from_distance",
    "query_tokens",
    "normalize_query_text",
    "docstring_signal",
    "lexical_overlap_score",
    "safe_join",
    "read_lines",
    "compute_span",
    "make_snippet",
    "make_module_summary",
    "spans_overlap",
]
