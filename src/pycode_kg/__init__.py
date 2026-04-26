"""
pycode_kg: A tool to build a searchable knowledge graph from Python repositories.

Pure AST extraction → SQLite (authoritative) → LanceDB (semantic index).

Public API
----------
Primary entry point::

    from pycode_kg import PyCodeKG

    kg = PyCodeKG(repo_root, db_path, lancedb_dir)
    stats = kg.build(wipe=True)
    result = kg.query("database connection setup")
    pack = kg.pack("configuration loading")
    pack.save("context.md")

Individual layers::

    from pycode_kg import CodeGraph, GraphStore, SemanticIndex

Result types::

    from pycode_kg import BuildStats, QueryResult, SnippetPack, Snippet

Low-level primitives (v0 contract, locked)::

    from pycode_kg import Node, Edge

KGModule SDK (build new domain KGs)::

    from pycode_kg import KGModule, KGExtractor, PyCodeKGExtractor, NodeSpec, EdgeSpec
"""

__version__ = "0.17.0"
__author__ = "Eric G. Suchanek, PhD"

# Low-level primitives (locked v0 contract)
# Layered classes
from pycode_kg.graph import CodeGraph
from pycode_kg.index import Embedder, SeedHit, SemanticIndex, SentenceTransformerEmbedder

# Orchestrator + result types
from pycode_kg.kg import BuildStats, PyCodeKG, QueryResult, Snippet, SnippetPack

# KGModule SDK
from pycode_kg.module import EdgeSpec, KGExtractor, KGModule, NodeSpec, PyCodeKGExtractor
from pycode_kg.pycodekg import DEFAULT_MODEL, Edge, Node
from pycode_kg.snapshots import (
    Snapshot,
    SnapshotDelta,
    SnapshotManager,
    SnapshotManifest,
    SnapshotMetrics,
)
from pycode_kg.store import DEFAULT_RELS, GraphStore, ProvMeta

__all__ = [
    # primitives
    "Node",
    "Edge",
    "DEFAULT_MODEL",
    # layers
    "CodeGraph",
    "GraphStore",
    "ProvMeta",
    "DEFAULT_RELS",
    "Embedder",
    "SentenceTransformerEmbedder",
    "SemanticIndex",
    "SeedHit",
    # KGModule SDK
    "KGModule",
    "KGExtractor",
    "PyCodeKGExtractor",
    "NodeSpec",
    "EdgeSpec",
    # orchestrator
    "PyCodeKG",
    # result types
    "BuildStats",
    "QueryResult",
    "Snippet",
    "SnippetPack",
    # snapshots
    "Snapshot",
    "SnapshotDelta",
    "SnapshotManifest",
    "SnapshotManager",
    "SnapshotMetrics",
]
