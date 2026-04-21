#!/usr/bin/env python3
"""
index.py

SemanticIndex — LanceDB vector index for the Code Knowledge Graph.

Derived from SQLite; disposable and rebuildable at any time.
SQLite (GraphStore) remains the authoritative source of truth.

Author: Eric G. Suchanek, PhD
Last Revision: 2026-03-13 22:53:21
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from pycode_kg.pycodekg import DEFAULT_MODEL

# ---------------------------------------------------------------------------
# Local model cache
# ---------------------------------------------------------------------------


def _local_model_path(model_name: str) -> Path:
    """Return the local cache path for *model_name*.

    Defaults to ``.pycodekg/models/<model>`` under the current working directory
    so the cache lives alongside the rest of the PyCodeKG artefacts.
    Override via the ``PYCODEKG_MODEL_DIR`` environment variable.

    Slashes in the model name (e.g. ``org/model``) are replaced with ``--``
    so the path is always a single directory level under the cache root.

    :param model_name: HuggingFace model identifier or short name.
    :return: Absolute :class:`~pathlib.Path` to the cached model directory.
    """
    import os  # pylint: disable=import-outside-toplevel

    default = str(Path.cwd() / ".pycodekg" / "models")
    cache_root = Path(os.environ.get("PYCODEKG_MODEL_DIR", default))
    safe_name = model_name.replace("/", "--")
    return cache_root / safe_name


if TYPE_CHECKING:
    from pycode_kg.store import GraphStore

# ---------------------------------------------------------------------------
# Logging / progress suppression
# ---------------------------------------------------------------------------


def suppress_ingestion_logging() -> None:
    """Suppress verbose progress output during model loading and ingestion.

    Suppresses Python logging, transformers/HuggingFace verbosity, and all
    tqdm progress bars (including sentence_transformers' internal "Batches:"
    bars) for the lifetime of the process.
    """
    for name in (
        "sentence_transformers",
        "transformers",
        "huggingface_hub",
        "lancedb",
        "pylance",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)

    try:
        import transformers  # pylint: disable=import-outside-toplevel

        transformers.logging.set_verbosity_error()
    except (ImportError, AttributeError):
        pass

    # tqdm checks TQDM_DISABLE at instantiation time, so setting it here
    # silences all subclasses regardless of when they were imported.
    os.environ["TQDM_DISABLE"] = "1"


# ---------------------------------------------------------------------------
# Embedder interface (pluggable)
# ---------------------------------------------------------------------------


class Embedder:
    """
    Abstract embedding backend.

    Subclass and implement :meth:`embed_texts` to plug in any model.

    :param dim: Embedding dimension (must be set by subclass ``__init__``).
    """

    dim: int

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of strings.

        :param texts: Input strings.
        :return: List of float32 vectors, one per input.
        """
        raise NotImplementedError

    def embed_query(self, query: str) -> list[float]:
        """
        Embed a single query string.

        Default implementation calls :meth:`embed_texts` with a one-element list.

        :param query: Query string.
        :return: Float32 vector.
        """
        return self.embed_texts([query])[0]


class SentenceTransformerEmbedder(Embedder):
    """
    Local embedding via ``sentence-transformers``.

    :param model_name: HuggingFace model name or local path.
                       Defaults to :data:`~pycode_kg.pycodekg.DEFAULT_MODEL`.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        """Load the sentence-transformer model.

        :param model_name: HuggingFace model name or local path.
        """
        import os  # pylint: disable=import-outside-toplevel

        from sentence_transformers import (  # pylint: disable=import-outside-toplevel
            SentenceTransformer,
        )
        from transformers import logging as hf_logging  # pylint: disable=import-outside-toplevel

        hf_logging.set_verbosity_error()

        local_path = _local_model_path(model_name)
        _prev_tqdm = os.environ.get("TQDM_DISABLE")
        os.environ["TQDM_DISABLE"] = "1"
        try:
            if local_path.exists():
                self.model = SentenceTransformer(str(local_path), trust_remote_code=True)
            else:
                try:
                    self.model = SentenceTransformer(
                        model_name, local_files_only=True, trust_remote_code=True
                    )
                except OSError:
                    self.model = SentenceTransformer(model_name, trust_remote_code=True)
        finally:
            if _prev_tqdm is None:
                os.environ.pop("TQDM_DISABLE", None)
            else:
                os.environ["TQDM_DISABLE"] = _prev_tqdm
        self.model_name = model_name
        self.dim: int = self.model.get_embedding_dimension() or 384
        # Detect task-prompt support (e.g. nomic-embed-text-v1.5).
        # sentence-transformers exposes model.prompts as a dict of name→prefix.
        _prompts: dict = getattr(self.model, "prompts", {}) or {}
        self._query_prompt: str | None = "search_query" if "search_query" in _prompts else None
        self._doc_prompt: str | None = "search_document" if "search_document" in _prompts else None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of strings into float32 vectors.

        Uses ``search_document`` task prompt when the model supports it
        (e.g. ``nomic-ai/nomic-embed-text-v1.5``).

        :param texts: Input strings to embed.
        :return: List of float32 vectors, one per input string.
        """
        kwargs: dict = {"normalize_embeddings": True, "show_progress_bar": False}
        if self._doc_prompt:
            kwargs["prompt_name"] = self._doc_prompt
        vecs = self.model.encode(texts, **kwargs)
        return [np.asarray(v, dtype="float32").tolist() for v in vecs]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string into a float32 vector.

        Uses ``search_query`` task prompt when the model supports it
        (e.g. ``nomic-ai/nomic-embed-text-v1.5``).

        :param query: Query string to embed.
        :return: Float32 vector representation of the query.
        """
        kwargs: dict = {"normalize_embeddings": True}
        if self._query_prompt:
            kwargs["prompt_name"] = self._query_prompt
        vec = self.model.encode([query], **kwargs)[0]
        return np.asarray(vec, dtype="float32").tolist()

    def __repr__(self) -> str:
        """Return a developer-readable representation of this embedder.

        :return: String of the form ``SentenceTransformerEmbedder(model=..., dim=...)``.
        """
        return f"SentenceTransformerEmbedder(model={self.model_name!r}, dim={self.dim})"


# ---------------------------------------------------------------------------
# Seed hit returned by SemanticIndex.search()
# ---------------------------------------------------------------------------


@dataclass
class SeedHit:
    """
    A single result from a semantic vector search.

    :param id: Node ID.
    :param kind: Node kind (``module``, ``class``, ``function``, ``method``).
    :param name: Short name.
    :param qualname: Qualified name.
    :param module_path: Repo-relative module path.
    :param distance: Vector distance (lower = more similar).
    :param rank: Zero-based rank in the result list.
    """

    id: str
    kind: str
    name: str
    qualname: str
    module_path: str
    distance: float
    rank: int


# ---------------------------------------------------------------------------
# SemanticIndex
# ---------------------------------------------------------------------------

_DEFAULT_TABLE = "pycodekg_nodes"
_DEFAULT_KINDS = ("module", "class", "function", "method")


class SemanticIndex:
    """
    LanceDB-backed semantic vector index for the Code Knowledge Graph.

    Reads nodes from a :class:`~pycode_kg.store.GraphStore` (via its SQLite
    database), embeds them, and stores the vectors in LanceDB.  The index
    is **derived and disposable** — it can be rebuilt from SQLite at any
    time without data loss.

    Example::

        embedder = SentenceTransformerEmbedder()
        idx = SemanticIndex("./lancedb", embedder=embedder)
        idx.build(store, wipe=True)

        hits = idx.search("database connection setup", k=8)
        for h in hits:
            print(h.id, h.distance)

    :param lancedb_dir: Directory for the LanceDB database.
    :param embedder: Embedding backend.  Defaults to
                     :class:`SentenceTransformerEmbedder` with
                     :data:`~pycode_kg.pycodekg.DEFAULT_MODEL`.
    :param table: LanceDB table name.  Defaults to ``"pycodekg_nodes"``.
    :param index_kinds: Node kinds to embed.
    """

    def __init__(
        self,
        lancedb_dir: str | Path,
        *,
        embedder: Embedder | None = None,
        table: str = _DEFAULT_TABLE,
        index_kinds: Sequence[str] = _DEFAULT_KINDS,
    ) -> None:
        """Initialise the semantic index.

        :param lancedb_dir: Directory for the LanceDB database.
        :param embedder: Embedding backend. Defaults to :class:`SentenceTransformerEmbedder`.
        :param table: LanceDB table name. Defaults to ``"pycodekg_nodes"``.
        :param index_kinds: Node kinds to include in the index.
        """
        self.lancedb_dir = Path(lancedb_dir)
        self.embedder: Embedder = embedder or SentenceTransformerEmbedder()
        self.table_name = table
        self.index_kinds = tuple(index_kinds)
        self._tbl = None  # lazy LanceDB table handle

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(
        self,
        store: GraphStore,
        *,
        wipe: bool = False,
        batch_size: int = 256,
        quiet: bool = True,
    ) -> dict:
        """
        Build (or rebuild) the vector index from *store*.

        :param store: Authoritative :class:`~pycode_kg.store.GraphStore`.
        :param wipe: If ``True``, delete all existing vectors first.
        :param batch_size: Number of nodes to embed per batch.
        :param quiet: If ``True`` (default), suppress progress output from LanceDB and
                      sentence-transformers during ingestion.
        :return: Stats dict with ``indexed_rows``, ``dim``, ``table``,
                 ``lancedb_dir``, ``kinds``.
        """
        if quiet:
            suppress_ingestion_logging()

        nodes = self._read_nodes(store)
        tbl = self._open_table(wipe=wipe)

        indexed = 0
        for i in range(0, len(nodes), batch_size):
            chunk = nodes[i : i + batch_size]
            texts = [_build_index_text(n) for n in chunk]
            vecs = self.embedder.embed_texts(texts)

            # upsert: delete existing IDs then add fresh rows
            ids = [n["id"] for n in chunk]
            if ids:
                pred = " OR ".join([f"id = '{_escape(nid)}'" for nid in ids])
                tbl.delete(pred)

            rows = [
                {
                    "id": n["id"],
                    "kind": n["kind"],
                    "name": n["name"],
                    "qualname": n["qualname"] or "",
                    "module_path": n["module_path"] or "",
                    "text": text,
                    "vector": vec,
                }
                for n, text, vec in zip(chunk, texts, vecs)
            ]
            tbl.add(rows)
            indexed += len(rows)

        self._tbl = tbl
        return {
            "indexed_rows": indexed,
            "dim": self.embedder.dim,
            "table": self.table_name,
            "lancedb_dir": str(self.lancedb_dir),
            "kinds": list(self.index_kinds),
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, k: int = 8) -> list[SeedHit]:
        """
        Semantic vector search.

        :param query: Natural-language query string.
        :param k: Number of results to return.
        :return: List of :class:`SeedHit` ordered by ascending distance.
        """
        tbl = self._get_table()
        qvec = self.embedder.embed_query(query)
        raw = tbl.search(qvec).limit(k).to_list()

        hits: list[SeedHit] = []
        for rank, row in enumerate(raw):
            dist = _extract_distance(row, rank)
            hits.append(
                SeedHit(
                    id=row["id"],
                    kind=row.get("kind", ""),
                    name=row.get("name", ""),
                    qualname=row.get("qualname", ""),
                    module_path=row.get("module_path", ""),
                    distance=dist,
                    rank=rank,
                )
            )
        return hits

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_nodes(self, store: GraphStore) -> list[dict]:
        """Read indexable nodes from the store filtered by ``index_kinds``.

        :param store: Authoritative :class:`~pycode_kg.store.GraphStore` to query.
        :return: List of node dicts for kinds in :attr:`index_kinds`.
        """
        return store.query_nodes(kinds=list(self.index_kinds))

    def _open_table(self, *, wipe: bool = False):
        """Open the LanceDB table, creating it with the correct schema if absent.

        :param wipe: If ``True``, delete all existing rows after opening.
        :return: LanceDB table handle.
        """
        import lancedb  # pylint: disable=import-outside-toplevel

        self.lancedb_dir.mkdir(parents=True, exist_ok=True)
        db = lancedb.connect(str(self.lancedb_dir))  # type: ignore[attr-defined]

        if self.table_name in db.list_tables().tables:
            if wipe:
                db.drop_table(self.table_name)
            else:
                try:
                    return db.open_table(self.table_name)
                except Exception as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                    # Table directory exists on disk but is corrupt/incomplete
                    # (e.g. from a previously interrupted build — empty _versions
                    # or data directories).  Drop and recreate it cleanly.
                    logging.getLogger(__name__).warning(
                        "LanceDB table %r appears corrupt (%s); dropping and recreating.",
                        self.table_name,
                        exc,
                    )
                    db.drop_table(self.table_name)

        # Create with a dummy row to establish schema, then remove it
        dummy = {
            "id": "__dummy__",
            "kind": "dummy",
            "name": "__dummy__",
            "qualname": "",
            "module_path": "",
            "text": "__dummy__",
            "vector": np.zeros((self.embedder.dim,), dtype="float32").tolist(),
        }
        tbl = db.create_table(self.table_name, data=[dummy])
        tbl.delete("id = '__dummy__'")
        return tbl

    def _get_table(self):
        """Return the cached LanceDB table handle, opening it if not yet loaded.

        :return: LanceDB table handle.
        """
        if self._tbl is None:
            import lancedb  # pylint: disable=import-outside-toplevel

            db = lancedb.connect(str(self.lancedb_dir))  # type: ignore[attr-defined]
            self._tbl = db.open_table(self.table_name)
        return self._tbl

    def __repr__(self) -> str:
        """Return a developer-readable representation of this SemanticIndex.

        :return: String including lancedb_dir, table name, and embedder details.
        """
        return (
            f"SemanticIndex(lancedb_dir={self.lancedb_dir!r}, "
            f"table={self.table_name!r}, embedder={self.embedder!r})"
        )


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------


def _build_index_text(n: dict) -> str:
    """Build the canonical text document used for embedding a node.

    **Format version 2** — includes a KEYWORDS section of de-duplicated word
    tokens extracted from the name, qualname, and module path.  This improves
    recall for abstract queries (for example "error handling strategy",
    "logging approach", "entry points", and "configuration") that do not
    match on names alone. Rebuilding the LanceDB index is required after this
    change (``pycodekg build-lancedb --wipe``).

    Retrieval quality depends heavily on vocabulary in node docstrings.
    Include meaningful terms for behavior, parameters, fallback semantics,
    and operational concerns so both semantic search and lexical reranking
    can surface the right nodes.

    :param n: Node dict with keys ``kind``, ``name``, ``qualname``, ``module_path``,
              ``lineno``, and optionally ``docstring``.
    :return: Newline-joined string suitable for embedding.
    """
    parts = [f"KIND: {n['kind']}", f"NAME: {n['name']}"]
    if n.get("qualname"):
        parts.append(f"QUALNAME: {n['qualname']}")
    if n.get("module_path"):
        parts.append(f"MODULE: {n['module_path']}")
    if n.get("lineno") is not None:
        parts.append(f"LINE: {n['lineno']}")
    if n.get("docstring"):
        parts.append("DOCSTRING:\n" + n["docstring"].strip())

    # Augment with word-token keywords from name/qualname/module for abstract query matching.
    # Splitting snake_case and path components gives the model more signal when the docstring
    # is absent or brief (e.g. "error" + "handler" from "_error_handler" matches "error handling").
    raw = " ".join(filter(None, [n.get("name"), n.get("qualname"), n.get("module_path")]))
    tokens = [w.lower() for w in re.findall(r"[a-zA-Z]+", raw) if len(w) > 2]
    seen_in_doc = set(re.findall(r"[a-zA-Z]+", (n.get("docstring") or "").lower()))
    extra = [t for t in dict.fromkeys(tokens) if t not in seen_in_doc]
    if extra:
        parts.append("KEYWORDS: " + " ".join(extra))

    return "\n".join(parts)


def _extract_distance(row: dict, fallback_rank: int) -> float:
    """Extract a distance value from a LanceDB result row.

    Tries ``_distance``, then ``distance``, then inverts ``score``.
    Falls back to the row's rank if no distance field is found.

    :param row: Raw result dict from LanceDB.
    :param fallback_rank: Zero-based rank to use when no distance field is present.
    :return: Float distance value (lower = more similar).
    """
    for key in ("_distance", "distance"):
        if key in row and row[key] is not None:
            return float(row[key])
    if "score" in row and row["score"] is not None:
        return 1.0 / (1.0 + float(row["score"]))
    return float(fallback_rank)


def _escape(s: str) -> str:
    """Escape single quotes in a string for use in LanceDB delete predicates.

    :param s: String to escape.
    :return: String with single quotes doubled.
    """
    return s.replace("'", "''")
