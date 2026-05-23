"""pycode_kg/index.py — Re-exports semantic index from kg_utils.semantic."""

from kg_utils.semantic import (  # noqa: F401
    DEFAULT_MODEL,
    Embedder,
    SeedHit,
    SemanticIndex,
    SentenceTransformerEmbedder,
    resolve_model_path,
    suppress_ingestion_logging,
)
