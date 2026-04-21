#!/usr/bin/env python3
"""
module/types.py

Shared result types and pure utility functions for the KGModule pipeline.

These are domain-agnostic and used by both KGModule (base) and any
concrete implementation (PyCodeKG, TypeScriptKG, GenomicsKG, …).

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class BuildStats:
    """
    Statistics returned by :meth:`KGModule.build` and related methods.

    :param repo_root: Repository root that was analysed.
    :param db_path: Path to the SQLite database.
    :param total_nodes: Total nodes written to SQLite.
    :param total_edges: Total edges written to SQLite.
    :param node_counts: Node counts broken down by kind.
    :param edge_counts: Edge counts broken down by relation.
    :param indexed_rows: Number of nodes embedded into LanceDB
                         (``None`` if the index was not built).
    :param index_dim: Embedding dimension (``None`` if not built).
    """

    repo_root: str
    db_path: str
    total_nodes: int
    total_edges: int
    node_counts: dict[str, int]
    edge_counts: dict[str, int]
    indexed_rows: int | None = None
    index_dim: int | None = None

    def to_dict(self) -> dict:
        """Serialise the stats to a plain dictionary.

        :return: Dictionary containing all ``BuildStats`` fields.
        """
        return {
            "repo_root": self.repo_root,
            "db_path": self.db_path,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "node_counts": self.node_counts,
            "edge_counts": self.edge_counts,
            "indexed_rows": self.indexed_rows,
            "index_dim": self.index_dim,
        }

    def __str__(self) -> str:
        """Render a human-readable multi-line summary of the build statistics.

        :return: Formatted string with repo root, db path, node/edge counts,
                 and (if available) indexed vector count and dimension.
        """
        lines = [
            f"repo_root   : {self.repo_root}",
            f"db_path     : {self.db_path}",
            f"nodes       : {self.total_nodes}  {self.node_counts}",
            f"edges       : {self.total_edges}  {self.edge_counts}",
        ]
        if self.indexed_rows is not None:
            lines.append(f"indexed     : {self.indexed_rows} vectors  dim={self.index_dim}")
        return "\n".join(lines)


@dataclass
class QueryResult:
    """
    Result of a hybrid query (:meth:`KGModule.query`).

    :param query: Original query string.
    :param seeds: Number of semantic seed nodes.
    :param expanded_nodes: Total nodes after graph expansion.
    :param returned_nodes: Nodes returned after filtering.
    :param hop: Hop count used.
    :param rels: Edge relations used for expansion.
    :param nodes: List of node dicts (sorted by rank).
    :param edges: List of edge dicts within the returned node set.
    """

    query: str
    seeds: int
    expanded_nodes: int
    returned_nodes: int
    hop: int
    rels: list[str]
    nodes: list[dict]
    edges: list[dict]

    def to_dict(self) -> dict:
        """Serialise the query result to a plain dictionary.

        :return: Dictionary containing all ``QueryResult`` fields.
        """
        return {
            "query": self.query,
            "seeds": self.seeds,
            "expanded_nodes": self.expanded_nodes,
            "returned_nodes": self.returned_nodes,
            "hop": self.hop,
            "rels": self.rels,
            "nodes": self.nodes,
            "edges": self.edges,
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Serialise to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def print_summary(self) -> None:
        """Print a human-readable summary of the query result to stdout."""
        sep = "=" * 80
        print(sep)
        print(f"QUERY: {self.query}")
        print(
            f"Seeds: {self.seeds} | Expanded: {self.expanded_nodes} "
            f"| Returned: {self.returned_nodes} | hop={self.hop}"
        )
        print(f"Rels: {', '.join(self.rels)}")
        print(sep)
        for n in self.nodes:
            print(
                f"{n['kind']:8s} {(n.get('module_path') or ''):40s} "
                f"{n.get('qualname') or n['name']}  [{n['id']}]"
            )
            if n.get("docstring"):
                ds0 = n["docstring"].strip().splitlines()[0]
                print(f"    {ds0[:120]}")
            print()
        print("-" * 80)
        print(f"EDGES (within returned set): {len(self.edges)}")
        print("-" * 80)
        for e in sorted(self.edges, key=lambda x: (x["rel"], x["src"], x["dst"])):
            print(f"  {e['src']} -[{e['rel']}]-> {e['dst']}")
        print(sep)


@dataclass
class Snippet:
    """
    A source-grounded snippet.

    :param path: Repo-relative file path.
    :param start: 1-based start line (inclusive).
    :param end: 1-based end line (inclusive).
    :param text: Line-numbered source text.
    """

    path: str
    start: int
    end: int
    text: str

    def to_dict(self) -> dict:
        """Serialise the snippet to a plain dictionary.

        :return: Dictionary with ``path``, ``start``, ``end``, and ``text`` keys.
        """
        return {"path": self.path, "start": self.start, "end": self.end, "text": self.text}


@dataclass
class SnippetPack:
    """
    Result of :meth:`KGModule.pack` — nodes with attached source snippets.

    :param query: Original query string.
    :param seeds: Number of semantic seed nodes.
    :param expanded_nodes: Total nodes after graph expansion.
    :param returned_nodes: Nodes returned after deduplication.
    :param hop: Hop count used.
    :param rels: Edge relations used for expansion.
    :param model: Embedding model name.
    :param nodes: Node dicts, each optionally containing a ``snippet`` key.
    :param edges: Edge dicts within the returned node set.
    :param warnings: Non-fatal issues encountered during packing.
    """

    query: str
    seeds: int
    expanded_nodes: int
    returned_nodes: int
    hop: int
    rels: list[str]
    model: str
    nodes: list[dict]
    edges: list[dict]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise the snippet pack to a plain dictionary."""
        return {
            "query": self.query,
            "seeds": self.seeds,
            "expanded_nodes": self.expanded_nodes,
            "returned_nodes": self.returned_nodes,
            "hop": self.hop,
            "rels": self.rels,
            "model": self.model,
            "nodes": self.nodes,
            "edges": self.edges,
            "warnings": self.warnings,
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Serialise to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_markdown(self) -> str:
        """Render the snippet pack as a Markdown context document.

        :return: Markdown-formatted string representing the full context pack.
        """
        out: list[str] = []
        out.append("# KGModule Snippet Pack\n")
        out.append(f"**Query:** `{self.query}`  ")
        out.append(f"**Seeds:** {self.seeds}  ")
        out.append(f"**Expanded nodes:** {self.expanded_nodes} (returned: {self.returned_nodes})  ")
        out.append(f"**hop:** {self.hop}  ")
        out.append(f"**rels:** {', '.join(self.rels)}  ")
        out.append(f"**model:** {self.model}  ")
        out.append("\n---\n")

        if self.warnings:
            out.append("## Warnings\n")
            for w in self.warnings:
                out.append(f"- {w}")
            out.append("")

        out.append("## Nodes\n")
        for n in self.nodes:
            out.append(f"### {n['kind']} — `{n.get('qualname') or n['name']}`")
            out.append(f"- id: `{n['id']}`")
            if n.get("module_path"):
                out.append(f"- module: `{n['module_path']}`")
            if n.get("lineno") is not None:
                out.append(f"- line: {n['lineno']}")
            if n.get("docstring"):
                ds0 = n["docstring"].strip().splitlines()[0]
                out.append(f"- doc: {ds0[:140]}")
            if n.get("relevance"):
                rel = n["relevance"]
                _score = rel.get("score", 0.0)
                _tier = "HIGH" if _score >= 0.60 else ("MEDIUM" if _score >= 0.45 else "LOW")
                out.append(
                    "- relevance: "
                    f"{_score:.3f} [{_tier}] "
                    f"(semantic={rel.get('semantic', 0.0):.3f}, "
                    f"lexical={rel.get('lexical', 0.0):.3f}, "
                    f"docstring_signal={rel.get('docstring_signal', 0.0):.3f}, "
                    f"hop={rel.get('hop', 0)})"
                )
            sn = n.get("snippet")
            if sn:
                end_lineno = n.get("end_lineno")
                if end_lineno is not None and sn["end"] < end_lineno:
                    out.append(
                        f"*(truncated: showing lines {sn['start']}–{sn['end']} "
                        f"of {n.get('lineno', sn['start'])}–{end_lineno})*"
                    )
                out.append("")
                out.append(f"```\n{sn['text']}\n```")
            out.append("")

        out.append("\n---\n")
        out.append("## Edges\n")
        for e in self.edges:
            out.append(f"- `{e['src']}` -[{e['rel']}]-> `{e['dst']}`")
        out.append("")
        return "\n".join(out)

    def save(self, path: str | Path, *, fmt: str = "md") -> None:
        """Write the pack to a file.

        :param path: Output file path.
        :param fmt: ``"md"`` for Markdown or ``"json"`` for JSON.
        """
        text = self.to_markdown() if fmt == "md" else self.to_json()
        Path(path).write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Scoring utilities (domain-agnostic)
# ---------------------------------------------------------------------------


def semantic_score_from_distance(distance: float) -> float:
    """Convert embedding distance to a bounded similarity-like score.

    :param distance: Distance value returned by vector search.
    :return: Score in ``[0, 1]`` where higher is better.
    """
    d = max(0.0, float(distance))
    return 1.0 / (1.0 + d)


def query_tokens(query: str) -> set[str]:
    """Tokenize a natural-language query for lightweight lexical overlap scoring.

    :param query: Raw query text.
    :return: Lower-cased alphanumeric tokens with length >= 2.
    """
    tokens: set[str] = set()
    for tok in re.findall(r"[A-Za-z0-9_]+", query.lower()):
        if len(tok) >= 2:
            tokens.add(tok)
        if "_" in tok:
            for part in tok.split("_"):
                if len(part) >= 2:
                    tokens.add(part)
    return tokens


def normalize_query_text(query: str) -> str:
    """Normalize query text for semantic retrieval.

    :param query: Raw user query.
    :return: Normalized query string.
    """
    return re.sub(r"[_-]+", " ", query).strip()


def docstring_signal(docstring: str | None) -> float:
    """Estimate docstring signal quality in ``[0, 1]``.

    :param docstring: Node docstring text.
    :return: Signal score in ``[0, 1]``.
    """
    if not docstring:
        return 0.0
    tokens = re.findall(r"[A-Za-z0-9_]+", docstring.lower())
    if not tokens:
        return 0.0
    unique_ratio = len(set(tokens)) / max(1, len(tokens))
    length_score = min(1.0, len(tokens) / 40.0)
    return max(0.0, min(1.0, 0.6 * length_score + 0.4 * unique_ratio))


def lexical_overlap_score(query_tokens_set: set[str], node: dict) -> float:
    """Compute lexical overlap between query tokens and node text features.

    :param query_tokens_set: Tokenized query terms.
    :param node: Node dictionary from the store.
    :return: Overlap score in ``[0, 1]``.
    """
    if not query_tokens_set:
        return 0.0
    haystack = " ".join(
        [
            str(node.get("name") or ""),
            str(node.get("qualname") or ""),
            str(node.get("module_path") or ""),
            str(node.get("docstring") or ""),
        ]
    ).lower()
    node_toks = set(re.findall(r"[A-Za-z0-9_]+", haystack))
    if not node_toks:
        return 0.0
    return len(query_tokens_set & node_toks) / len(query_tokens_set)


# ---------------------------------------------------------------------------
# Snippet / span utilities (domain-agnostic)
# ---------------------------------------------------------------------------


def safe_join(repo_root: Path, rel_path: str) -> Path:
    """Safely join a repo-relative path to the repository root.

    :param repo_root: Absolute path to the repository root directory.
    :param rel_path: Repository-relative path to join.
    :return: Resolved absolute ``Path`` within ``repo_root``.
    :raises ValueError: If the resolved path escapes ``repo_root``.
    """
    p = (repo_root / rel_path).resolve()
    rr = repo_root.resolve()
    if rr not in p.parents and p != rr:
        raise ValueError(f"Unsafe path outside repo_root: {rel_path!r}")
    return p


def read_lines(path: Path) -> list[str]:
    """Read all lines from a file, returning ``[]`` if the file is missing.

    :param path: Absolute path to the file.
    :return: List of lines (without newlines) or ``[]`` on error.
    """
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except FileNotFoundError:
        return []


def compute_span(
    kind: str,
    lineno: int | None,
    end_lineno: int | None,
    *,
    context: int,
    max_lines: int,
    file_nlines: int,
) -> tuple[int, int]:
    """Compute the 1-based ``(start, end)`` line span for a node's source snippet.

    :param kind: Node kind (e.g. ``"module"``, ``"function"``, ``"class"``).
    :param lineno: 1-based start line of the definition, or ``None``.
    :param end_lineno: 1-based end line of the definition, or ``None``.
    :param context: Number of extra lines to include before and after the span.
    :param max_lines: Maximum number of lines the span may contain.
    :param file_nlines: Total number of lines in the source file.
    :return: ``(start, end)`` tuple of 1-based line numbers.
    """
    if file_nlines <= 0:
        return (1, 0)
    if kind == "module":
        return (1, min(file_nlines, max_lines))
    if lineno is None:
        return (1, min(file_nlines, max_lines))
    if end_lineno is not None and end_lineno >= lineno:
        start = max(1, lineno - context)
        end = min(file_nlines, end_lineno + context)
        if (end - start + 1) > max_lines:
            end = min(file_nlines, start + max_lines - 1)
        return (start, end)
    start = max(1, lineno - context)
    end = min(file_nlines, lineno + context)
    if (end - start + 1) > max_lines:
        end = min(file_nlines, start + max_lines - 1)
    return (start, end)


def make_snippet(rel_path: str, lines: list[str], start: int, end: int) -> dict:
    """Build a snippet dictionary from a slice of source lines.

    :param rel_path: Repository-relative file path.
    :param lines: Full list of source lines for the file (0-indexed).
    :param start: 1-based first line of the snippet (inclusive).
    :param end: 1-based last line of the snippet (inclusive).
    :return: Dictionary with ``path``, ``start``, ``end``, and ``text`` keys.
    """
    s0 = max(0, start - 1)
    e0 = max(0, end)
    chunk = lines[s0:e0]
    numbered = "\n".join(f"{i:>5d}: {line}" for i, line in enumerate(chunk, start=start))
    return {"path": rel_path, "start": start, "end": end, "text": numbered}


def make_module_summary(
    rel_path: str,
    lines: list[str],
    docstring: str | None,
    contained_nodes: list[dict],
    max_lines: int,
) -> dict:
    """Build a summary snippet for a module-level node.

    :param rel_path: Repository-relative file path.
    :param lines: Full list of source lines for the file.
    :param docstring: Module docstring text, or ``None``.
    :param contained_nodes: List of node dicts directly contained by this module.
    :param max_lines: Maximum lines for the summary.
    :return: Snippet dict with ``is_summary=True``.
    """
    out: list[str] = []
    if docstring:
        for dl in docstring.strip().splitlines():
            out.append(dl)
        out.append("")

    by_kind: dict[str, list[dict]] = {}
    for cn in contained_nodes:
        k = cn.get("kind", "unknown")
        by_kind.setdefault(k, []).append(cn)

    for kind in ("class", "function", "method"):
        group = by_kind.get(kind, [])
        if not group:
            continue
        out.append(f"# {kind}s ({len(group)}):")
        for cn in sorted(group, key=lambda x: x.get("lineno") or 0):
            name = cn.get("qualname") or cn.get("name", "?")
            ln = cn.get("lineno")
            ds = cn.get("docstring") or ""
            ds_first = ds.strip().splitlines()[0][:80] if ds.strip() else ""
            loc = f"L{ln}" if ln else "?"
            if ds_first:
                out.append(f"#   {name} ({loc}) — {ds_first}")
            else:
                out.append(f"#   {name} ({loc})")
        out.append("")

    summary_lines = out[:max_lines]
    text = "\n".join(f"{'':>5s}  {line}" for line in summary_lines)
    return {
        "path": rel_path,
        "start": 1,
        "end": min(len(lines), max_lines),
        "text": text,
        "is_summary": True,
    }


def spans_overlap(a: tuple[int, int], b: tuple[int, int], gap: int = 2) -> bool:
    """Return ``True`` when two line spans are considered overlapping.

    :param a: First span as a ``(start, end)`` tuple of 1-based line numbers.
    :param b: Second span as a ``(start, end)`` tuple of 1-based line numbers.
    :param gap: Minimum separation lines for non-overlapping spans.
    :return: ``True`` if the spans overlap or are within ``gap`` lines of each other.
    """
    a0, a1 = a
    b0, b1 = b
    return not (a1 + gap < b0 or b1 + gap < a0)
