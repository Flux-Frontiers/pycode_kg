#!/usr/bin/env python3
"""
module/extractor.py

KGExtractor — abstract extraction protocol for any knowledge graph domain.

NodeSpec and EdgeSpec are the canonical intermediate types between
domain-specific source parsing and the generic GraphStore / SemanticIndex
infrastructure provided by KGModule.

Also provides CodeKGExtractor — the Python-AST-backed implementation that
drives the existing CodeKG build pipeline.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Intermediate node / edge representations
# ---------------------------------------------------------------------------


@dataclass
class NodeSpec:
    """Specification for a single graph node emitted by a KGExtractor.

    This is the canonical intermediate type between domain-specific source
    parsing and the generic GraphStore persistence layer.

    :param node_id: Stable unique ID (e.g. ``'fn:src/foo.py:bar'``).
    :param kind: Domain node type (``'function'``, ``'gene'``, ``'statute'``, …).
    :param name: Human-readable short name.
    :param qualname: Fully-qualified name within its source (may equal ``name``).
    :param source_path: Repo-relative path to source file or document.
    :param lineno: 1-based start line (source-code KGs); ``None`` for doc/domain KGs.
    :param end_lineno: 1-based end line; ``None`` if not applicable.
    :param docstring: Docstring, description, or excerpt used for embedding.
    :param metadata: Domain-specific extension data (serialized as JSON in the store).
    """

    node_id: str
    kind: str
    name: str
    qualname: str
    source_path: str
    lineno: int | None = None
    end_lineno: int | None = None
    docstring: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EdgeSpec:
    """Specification for a single directed graph edge emitted by a KGExtractor.

    :param source_id: ``node_id`` of the source node.
    :param target_id: ``node_id`` of the target node (may be an unresolved stub ID).
    :param relation: Edge type (``'CALLS'``, ``'IMPORTS'``, ``'CONTAINS'``, …).
    :param weight: Edge weight for PageRank (default 1.0).
    :param metadata: Domain-specific edge data (serialized as evidence JSON in the store).
    """

    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# KGExtractor — abstract domain extraction protocol
# ---------------------------------------------------------------------------


class KGExtractor(ABC):
    """Abstract extraction protocol for a knowledge graph domain.

    Subclass this to teach :class:`~code_kg.module.base.KGModule` how to
    traverse your source and emit :class:`NodeSpec` / :class:`EdgeSpec`
    objects.  The base infrastructure (:class:`~code_kg.store.GraphStore`,
    :class:`~code_kg.index.SemanticIndex`, snapshot management, MCP server,
    CLI) is provided by :class:`~code_kg.module.base.KGModule` — you only
    implement the domain-specific parsing.

    Minimal subclass::

        class MyExtractor(KGExtractor):
            def node_kinds(self): return ["entity", "relation"]
            def edge_kinds(self): return ["LINKED_TO"]
            def extract(self):
                for item in my_parser(self.repo_path):
                    yield NodeSpec(node_id=item.id, kind="entity", ...)

    :param repo_path: Absolute path to the repository or corpus root.
    :param config: Domain-specific configuration dict.
    """

    def __init__(self, repo_path: Path, config: dict[str, Any] | None = None) -> None:
        """Initialise the extractor.

        :param repo_path: Path to the repository or corpus root.
        :param config: Optional domain-specific configuration dict.
        """
        self.repo_path = Path(repo_path).resolve()
        self.config = config or {}

    @abstractmethod
    def node_kinds(self) -> list[str]:
        """Return the canonical list of node kinds this extractor emits.

        Example: ``['module', 'class', 'function', 'method']``

        Used to parameterize the LanceDB ``index_kinds`` and the MCP
        ``graph_stats`` tool enum.
        """

    @abstractmethod
    def edge_kinds(self) -> list[str]:
        """Return the canonical list of edge relation types this extractor emits.

        Example: ``['CALLS', 'IMPORTS', 'CONTAINS', 'INHERITS']``
        """

    @abstractmethod
    def extract(self) -> Iterator[NodeSpec | EdgeSpec]:
        """Traverse the source and yield nodes and edges.

        May yield :class:`NodeSpec` and :class:`EdgeSpec` objects in any
        order.  The build pipeline separates them into two lists before
        calling :meth:`~code_kg.store.GraphStore.write`.

        Implementations should be deterministic: the same source should
        produce the same stream on every call.
        """

    def meaningful_node_kinds(self) -> list[str]:
        """Return the subset of ``node_kinds()`` that are indexed semantically.

        Default: all of :meth:`node_kinds`.  Override to exclude structural
        stubs (e.g., unresolved import placeholders, synthetic wrapper nodes)
        from the LanceDB index and from coverage metrics.

        :return: List of node kind strings to index and measure.
        """
        return self.node_kinds()

    def coverage_metric(self, nodes: list[NodeSpec]) -> float:
        """Compute a coverage quality metric for snapshots (0.0–1.0).

        Default: fraction of meaningful nodes that have a non-empty docstring.
        Override for domain-appropriate metrics (e.g., pathway annotation
        completeness, legal cross-reference density).

        :param nodes: All extracted :class:`NodeSpec` objects.
        :return: Coverage score in ``[0.0, 1.0]``.
        """
        meaningful = [n for n in nodes if n.kind in self.meaningful_node_kinds()]
        if not meaningful:
            return 0.0
        covered = sum(1 for n in meaningful if n.docstring.strip())
        return covered / len(meaningful)


# ---------------------------------------------------------------------------
# CodeKGExtractor — Python-AST-backed extractor
# ---------------------------------------------------------------------------


class CodeKGExtractor(KGExtractor):
    """KGExtractor backed by CodeGraph (Python AST analysis).

    Wraps :class:`~code_kg.graph.CodeGraph` and converts its :class:`Node`
    and :class:`Edge` v0 primitives to :class:`NodeSpec` / :class:`EdgeSpec`
    for the generic :class:`~code_kg.module.base.KGModule` build pipeline.

    This is the extractor used by :class:`~code_kg.kg.CodeKG` and is the
    reference implementation for source-code KG extractors.

    :param repo_path: Path to the Python repository root.
    :param include: Set of top-level directory names to include (all if empty).
    :param exclude: Set of directory names to exclude at every depth.
    :param config: Optional config dict (forwarded to super).
    """

    def __init__(
        self,
        repo_path: Path,
        *,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialise the extractor for a Python repository.

        :param repo_path: Path to the Python repository root.
        :param include: Top-level directory names to include (empty = all).
        :param exclude: Directory names to exclude at every walk depth.
        :param config: Optional domain-specific configuration dict.
        """
        super().__init__(repo_path, config)
        self._include: set[str] = include or set()
        self._exclude: set[str] = exclude or set()

    def node_kinds(self) -> list[str]:
        """Return the Python AST node kinds.

        :return: ``['module', 'class', 'function', 'method', 'symbol']``
        """
        return ["module", "class", "function", "method", "symbol"]

    def edge_kinds(self) -> list[str]:
        """Return the Python AST edge relation types.

        :return: List of all relation strings emitted by the Python extractor.
        """
        return [
            "CONTAINS",
            "CALLS",
            "IMPORTS",
            "INHERITS",
            "READS",
            "WRITES",
            "ATTR_ACCESS",
            "DEPENDS_ON",
            "RESOLVES_TO",
        ]

    def meaningful_node_kinds(self) -> list[str]:
        """Return the node kinds indexed by LanceDB and counted in coverage.

        Excludes ``'symbol'`` (unresolved import stubs).

        :return: ``['module', 'class', 'function', 'method']``
        """
        return ["module", "class", "function", "method"]

    def extract(self) -> Iterator[NodeSpec | EdgeSpec]:
        """Run Python AST extraction and yield NodeSpec / EdgeSpec objects.

        Delegates to :class:`~code_kg.graph.CodeGraph` for the AST walk, then
        converts the v0-locked :class:`~code_kg.codekg.Node` and
        :class:`~code_kg.codekg.Edge` primitives to the generic spec types.

        :return: Iterator of :class:`NodeSpec` and :class:`EdgeSpec` objects.
        """
        from code_kg.graph import CodeGraph  # pylint: disable=import-outside-toplevel

        graph = CodeGraph(self.repo_path, include=self._include, exclude=self._exclude)
        nodes, edges = graph.result()

        for n in nodes:
            yield NodeSpec(
                node_id=n.id,
                kind=n.kind,
                name=n.name,
                qualname=n.qualname or "",
                source_path=n.module_path or "",
                lineno=n.lineno,
                end_lineno=n.end_lineno,
                docstring=n.docstring or "",
            )

        for e in edges:
            yield EdgeSpec(
                source_id=e.src,
                target_id=e.dst,
                relation=e.rel,
                metadata={"evidence": e.evidence} if e.evidence else {},
            )
