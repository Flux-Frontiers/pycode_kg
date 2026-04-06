#!/usr/bin/env python3
"""
kg.py

CodeKG — concrete KGModule implementation for Python codebases.

Owns the Python-specific extraction layer (CodeGraph / AST) and delegates
all generic infrastructure (SQLite, LanceDB, hybrid query, snippet packing)
to the KGModule base class.

Also re-exports the result types (BuildStats, QueryResult, Snippet,
SnippetPack) from module.types for backwards API compatibility.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

from pathlib import Path

from code_kg.codekg import DEFAULT_MODEL
from code_kg.graph import CodeGraph
from code_kg.module.base import KGModule
from code_kg.module.extractor import CodeKGExtractor, KGExtractor
from code_kg.module.types import (
    BuildStats,
    QueryResult,
    Snippet,
    SnippetPack,
)
from code_kg.store import GraphStore

# ---------------------------------------------------------------------------
# Re-export result types for backwards compatibility
# (code that does ``from code_kg.kg import BuildStats`` keeps working)
# ---------------------------------------------------------------------------

__all__ = [
    "CodeKG",
    "BuildStats",
    "QueryResult",
    "Snippet",
    "SnippetPack",
]

# ---------------------------------------------------------------------------
# Python-specific kind priority
# ---------------------------------------------------------------------------

_CODEKG_KIND_PRIORITY: dict[str, int] = {
    "function": 0,
    "method": 1,
    "class": 2,
    "module": 3,
    "symbol": 4,
}


# ---------------------------------------------------------------------------
# CodeKG — concrete KGModule for Python
# ---------------------------------------------------------------------------


class CodeKG(KGModule):
    """
    Top-level orchestrator for the Code Knowledge Graph.

    Subclasses :class:`~code_kg.module.base.KGModule` and provides the
    Python-AST-specific extraction layer via :class:`CodeKGExtractor`.
    All generic infrastructure — SQLite persistence, LanceDB indexing,
    hybrid query, snippet packing, snapshots — is inherited from
    :class:`~code_kg.module.base.KGModule`.

    Typical usage::

        kg = CodeKG(repo_root="/path/to/repo")
        stats = kg.build(wipe=True)
        print(stats)

        result = kg.query("database connection setup", k=8, hop=1)
        result.print_summary()

        pack = kg.pack("configuration loading", k=8, hop=1)
        pack.save("context.md")

    :param repo_root: Repository root directory.
    :param db_path: SQLite database path (defaults to
        ``<repo_root>/.codekg/graph.sqlite``).
    :param lancedb_dir: LanceDB directory (defaults to
        ``<repo_root>/.codekg/lancedb``).
    :param model: Sentence-transformer model name.
    :param table: LanceDB table name.
    """

    _default_dir = ".codekg"

    def __init__(
        self,
        repo_root: str | Path,
        db_path: str | Path | None = None,
        lancedb_dir: str | Path | None = None,
        *,
        model: str = DEFAULT_MODEL,
        table: str = "codekg_nodes",
    ) -> None:
        """Initialise ``CodeKG`` and resolve all paths.

        :param repo_root: Repository root directory; resolved to an absolute path.
        :param db_path: Path to the SQLite database file.
        :param lancedb_dir: Directory used by LanceDB for the vector index.
        :param model: Sentence-transformer model name used for embedding.
        :param table: LanceDB table name for the node index.
        """
        super().__init__(
            repo_root,
            db_path=db_path,
            lancedb_dir=lancedb_dir,
            model=model,
            table=table,
        )
        # Backwards-compatible cached CodeGraph (direct access still works)
        self._graph: CodeGraph | None = None

    # ------------------------------------------------------------------
    # KGModule abstract interface
    # ------------------------------------------------------------------

    def make_extractor(self) -> KGExtractor:
        """Return a CodeKGExtractor for this repository.

        :return: :class:`CodeKGExtractor` targeting :attr:`repo_root`.
        """
        return CodeKGExtractor(self.repo_root)

    def kind(self) -> str:
        """Return the KG kind string.

        :return: ``"code"``
        """
        return "code"

    def analyze(self, *, include_edge_provenance: bool = False) -> str:
        """Run full nine-phase architectural analysis and return Markdown.

        Delegates to :class:`~code_kg.codekg_thorough_analysis.CodeKGAnalyzer`.
        This is the same analysis produced by ``codekg analyze``.

        :param include_edge_provenance: Annotate edges with confidence metadata.
        :return: Markdown-formatted architectural analysis report.
        """
        try:
            from io import StringIO  # pylint: disable=import-outside-toplevel

            from rich.console import Console  # pylint: disable=import-outside-toplevel

            from code_kg.codekg_thorough_analysis import (  # pylint: disable=import-outside-toplevel
                CodeKGAnalyzer,
            )

            silent = Console(file=StringIO(), highlight=False)
            analyzer = CodeKGAnalyzer(self, console=silent)
            analyzer.run_analysis()
            return analyzer.to_markdown()
        except Exception as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            return f"# CodeKG Analysis\n\nAnalysis failed: {exc}\n"

    # ------------------------------------------------------------------
    # Python-specific overrides
    # ------------------------------------------------------------------

    def _kind_priority(self, kind: str) -> int:
        """Return Python-specific node kind sort priority.

        :param kind: Node kind string.
        :return: Integer priority (lower = ranked first).
        """
        return _CODEKG_KIND_PRIORITY.get(kind, 99)

    def _post_build_hook(self, store: GraphStore) -> None:
        """Resolve Python symbol stubs after writing nodes/edges.

        Called by :meth:`~code_kg.module.base.KGModule.build_graph` after
        ``store.write()``.  Links ``sym:`` import stubs to their definitions
        via ``RESOLVES_TO`` edges.

        :param store: The :class:`~code_kg.store.GraphStore` just written to.
        """
        store.resolve_symbols()

    # ------------------------------------------------------------------
    # Backwards-compatible CodeGraph property
    # ------------------------------------------------------------------

    @property
    def graph(self) -> CodeGraph:
        """Python AST extraction layer (lazy, cached).

        Kept for backwards compatibility with code that accesses
        ``kg.graph`` directly.  The build pipeline uses
        :meth:`make_extractor` instead.
        """
        if self._graph is None:
            self._graph = CodeGraph(self.repo_root)
        return self._graph

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return an unambiguous string representation.

        :return: ``CodeKG(repo_root=..., db_path=..., lancedb_dir=..., model=...)``.
        """
        return (
            f"CodeKG(repo_root={self.repo_root!r}, "
            f"db_path={self.db_path!r}, "
            f"lancedb_dir={self.lancedb_dir!r}, "
            f"model={self.model_name!r})"
        )
