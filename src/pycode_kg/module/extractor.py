#!/usr/bin/env python3
"""
module/extractor.py

KGExtractor — abstract extraction protocol for any knowledge graph domain.

NodeSpec and EdgeSpec are imported from kg_utils.specs and re-exported here.
PyCodeKGExtractor is the Python-AST-backed implementation.

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from kg_utils.extractor import KGExtractor  # noqa: F401
from kg_utils.specs import EdgeSpec, NodeSpec  # noqa: F401

# ---------------------------------------------------------------------------
# PyCodeKGExtractor — Python-AST-backed extractor
# ---------------------------------------------------------------------------


class PyCodeKGExtractor(KGExtractor):
    """KGExtractor backed by CodeGraph (Python AST analysis).

    Wraps :class:`~pycode_kg.graph.CodeGraph` and converts its :class:`Node`
    and :class:`Edge` v0 primitives to :class:`NodeSpec` / :class:`EdgeSpec`
    for the generic :class:`~pycode_kg.module.base.KGModule` build pipeline.

    This is the extractor used by :class:`~pycode_kg.kg.PyCodeKG` and is the
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
        """Return the node kinds indexed in the vector store and counted in coverage.

        Excludes ``'symbol'`` (unresolved import stubs).

        :return: ``['module', 'class', 'function', 'method']``
        """
        return ["module", "class", "function", "method"]

    def extract(self) -> Iterator[NodeSpec | EdgeSpec]:
        """Run Python AST extraction and yield NodeSpec / EdgeSpec objects.

        Delegates to :class:`~pycode_kg.graph.CodeGraph` for the AST walk, then
        converts the v0-locked :class:`~pycode_kg.pycodekg.Node` and
        :class:`~pycode_kg.pycodekg.Edge` primitives to the generic spec types.

        :return: Iterator of :class:`NodeSpec` and :class:`EdgeSpec` objects.
        """
        from pycode_kg.graph import CodeGraph  # noqa: PLC0415

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
