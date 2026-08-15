"""pycode_kg/index.py — Re-exports semantic index from kg_utils.semantic.

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

from kg_utils.semantic import (  # noqa: F401
    DEFAULT_MODEL,
    Embedder,
    SeedHit,
    SemanticIndex,
    SentenceTransformerEmbedder,
    resolve_model_path,
    suppress_ingestion_logging,
)
