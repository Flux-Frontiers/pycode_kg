"""pycode_kg/module/types.py — Re-exports from kg_utils for backward compat.

License: Elastic 2.0
"""

from dataclasses import dataclass

from kg_utils.pipeline import (  # noqa: F401
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
from kg_utils.specs import BuildStats, QueryResult, SnippetPack  # noqa: F401


@dataclass
class Snippet:
    """Backward-compat shim. Snippets are now dicts on node["snippet"]."""

    path: str
    start: int
    end: int
    text: str

    def to_dict(self) -> dict:
        return {"path": self.path, "start": self.start, "end": self.end, "text": self.text}
