#!/usr/bin/env python3
"""
kg.py

PyCodeKG — concrete KGModule implementation for Python codebases.

Owns the Python-specific extraction layer (CodeGraph / AST) and delegates
all generic infrastructure (SQLite, sqlite-vec, hybrid query, snippet packing)
to the KGModule base class.

Also re-exports the result types (BuildStats, QueryResult, Snippet,
SnippetPack) from module.types for backwards API compatibility.

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

from __future__ import annotations

from pathlib import Path

from pycode_kg.graph import CodeGraph
from pycode_kg.module.base import KGModule
from pycode_kg.module.extractor import KGExtractor, PyCodeKGExtractor
from pycode_kg.module.types import (
    BuildStats,
    QueryResult,
    Snippet,
    SnippetPack,
)
from pycode_kg.pycodekg import DEFAULT_MODEL

# ---------------------------------------------------------------------------
# Re-export result types for backwards compatibility
# (code that does ``from pycode_kg.kg import BuildStats`` keeps working)
# ---------------------------------------------------------------------------

__all__ = [
    "PyCodeKG",
    "BuildStats",
    "QueryResult",
    "Snippet",
    "SnippetPack",
]

# ---------------------------------------------------------------------------
# Python-specific kind priority
# ---------------------------------------------------------------------------

_PYCODEKG_KIND_PRIORITY: dict[str, int] = {
    "function": 0,
    "method": 1,
    "class": 2,
    "module": 3,
    "symbol": 4,
}


# ---------------------------------------------------------------------------
# PyCodeKG — concrete KGModule for Python
# ---------------------------------------------------------------------------


class PyCodeKG(KGModule):
    """
    Top-level orchestrator for the Code Knowledge Graph.

    Subclasses :class:`~pycode_kg.module.base.KGModule` and provides the
    Python-AST-specific extraction layer via :class:`PyCodeKGExtractor`.
    All generic infrastructure — SQLite persistence, sqlite-vec indexing,
    hybrid query, snippet packing, snapshots — is inherited from
    :class:`~pycode_kg.module.base.KGModule`.

    Typical usage::

        kg = PyCodeKG(repo_root="/path/to/repo")
        stats = kg.build(wipe=True)
        print(stats)

        result = kg.query("database connection setup", k=8, hop=1)
        result.print_summary()

        pack = kg.pack("configuration loading", k=8, hop=1)
        pack.save("context.md")

    :param repo_root: Repository root directory.
    :param db_path: SQLite database path (defaults to
        ``<repo_root>/.pycodekg/graph.sqlite``).
    :param vectors_path: sqlite-vec vector store path (defaults to
        ``<repo_root>/.pycodekg/vectors.sqlite``).
    :param model: Sentence-transformer model name.
    """

    _default_dir = ".pycodekg"

    def __init__(
        self,
        repo_root: str | Path,
        db_path: str | Path | None = None,
        vectors_path: str | Path | None = None,
        *,
        model: str = DEFAULT_MODEL,
    ) -> None:
        """Initialise ``PyCodeKG`` and resolve all paths.

        :param repo_root: Repository root directory; resolved to an absolute path.
        :param db_path: Path to the SQLite database file.
        :param vectors_path: Path to the sqlite-vec vector store file.
        :param model: Sentence-transformer model name used for embedding.
        """
        super().__init__(
            repo_root,
            db_path=db_path,
            model=model,
            vector_backend="sqlite-vec",
        )
        if vectors_path is not None:
            self.vectors_path = Path(vectors_path)
        # Backwards-compatible cached CodeGraph (direct access still works)
        self._graph: CodeGraph | None = None

    # ------------------------------------------------------------------
    # KGModule abstract interface
    # ------------------------------------------------------------------

    def make_extractor(self) -> KGExtractor:
        """Return a PyCodeKGExtractor for this repository.

        :return: :class:`PyCodeKGExtractor` targeting :attr:`repo_root`.
        """
        return PyCodeKGExtractor(self.repo_root)

    def kind(self) -> str:
        """Return the KG kind string.

        :return: ``"code"``
        """
        return "code"

    def analyze(self, *, include_edge_provenance: bool = False) -> str:
        """Run full nine-phase architectural analysis and return Markdown.

        Delegates to :class:`~pycode_kg.pycodekg_thorough_analysis.PyCodeKGAnalyzer`.
        This is the same analysis produced by ``pycodekg analyze``.

        :param include_edge_provenance: Annotate edges with confidence metadata.
        :return: Markdown-formatted architectural analysis report.
        """
        try:
            from io import StringIO  # noqa: PLC0415

            from rich.console import Console  # noqa: PLC0415

            from pycode_kg.pycodekg_thorough_analysis import (  # noqa: PLC0415
                PyCodeKGAnalyzer,
            )

            silent = Console(file=StringIO(), highlight=False)
            analyzer = PyCodeKGAnalyzer(self, console=silent)
            analyzer.run_analysis()
            return analyzer.to_markdown()
        except Exception as exc:  # noqa: BLE001
            return f"# PyCodeKG Analysis\n\nAnalysis failed: {exc}\n"

    # ------------------------------------------------------------------
    # Python-specific overrides
    # ------------------------------------------------------------------

    def _kind_priority(self, kind: str) -> int:
        """Return Python-specific node kind sort priority.

        :param kind: Node kind string.
        :return: Integer priority (lower = ranked first).
        """
        return _PYCODEKG_KIND_PRIORITY.get(kind, 99)

    # _post_build_hook is inherited from module.base.KGModule, which runs
    # resolve_symbols_pruned() — resolution plus builtin-method-lookalike
    # pruning (see pycode_kg.resolution).  A local override existed here that
    # merely duplicated the base behaviour; it is gone.

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

        :return: ``PyCodeKG(repo_root=..., db_path=..., vectors_path=..., model=...)``.
        """
        return (
            f"PyCodeKG(repo_root={self.repo_root!r}, "
            f"db_path={self.db_path!r}, "
            f"vectors_path={self.vectors_path!r}, "
            f"model={self.model_name!r})"
        )
