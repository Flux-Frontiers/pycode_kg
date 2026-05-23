"""pycode_kg/module/base.py — KGModule for pycode_kg: thin subclass of kg_utils.pipeline."""

from __future__ import annotations

from abc import abstractmethod

from kg_utils.extractor import KGExtractor
from kg_utils.pipeline import KGModule as _KGModuleBase
from kg_utils.store import GraphStore


class KGModule(_KGModuleBase):
    """Abstract base for Python code knowledge graphs.

    Domain authors implement :meth:`make_extractor`, :meth:`kind`, and
    :meth:`analyze`.  Build/query/pack infrastructure comes from
    :class:`kg_utils.pipeline.KGModule`.
    """

    _default_dir: str = ".pycodekg"

    def _post_build_hook(self, store: GraphStore) -> None:
        """Run symbol resolution after the graph is written."""
        store.resolve_symbols()

    @abstractmethod
    def make_extractor(self) -> KGExtractor: ...

    @abstractmethod
    def kind(self) -> str: ...

    @abstractmethod
    def analyze(self) -> str: ...
