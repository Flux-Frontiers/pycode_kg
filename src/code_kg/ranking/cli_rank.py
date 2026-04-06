"""CLI wrapper for CodeRank and hybrid query ranking."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .coderank import (
    DEFAULT_GLOBAL_RELS,
    build_code_graph,
    compute_coderank,
    persist_metric_scores,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute CodeRank metrics for CodeKG graphs.")
    parser.add_argument("--sqlite", required=True, help="Path to CodeKG SQLite graph.")
    parser.add_argument("--top", type=int, default=25, help="Number of top results to print.")
    parser.add_argument(
        "--rels",
        default=",".join(DEFAULT_GLOBAL_RELS),
        help="Comma-separated relations to include.",
    )
    parser.add_argument(
        "--kinds",
        default="function,method,class,module",
        help="Comma-separated node kinds to include.",
    )
    parser.add_argument(
        "--persist-metric",
        default=None,
        help="Optional metric name to persist into node_metrics.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit results as JSON rather than plain text.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    sqlite_path = Path(args.sqlite)
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite file does not exist: {sqlite_path}")

    rels = tuple(rel.strip() for rel in args.rels.split(",") if rel.strip())
    kinds = tuple(kind.strip() for kind in args.kinds.split(",") if kind.strip())

    graph = build_code_graph(
        str(sqlite_path),
        include_relations=rels,
        include_kinds=kinds,
        exclude_test_paths=True,
    )
    scores = compute_coderank(graph)

    if args.persist_metric:
        persist_metric_scores(str(sqlite_path), args.persist_metric, scores)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[: args.top]
    rows = []
    for rank, (node_id, score) in enumerate(ranked, start=1):
        attrs = graph.nodes[node_id]
        rows.append(
            {
                "rank": rank,
                "node_id": node_id,
                "score": score,
                "kind": attrs.get("kind"),
                "qualname": attrs.get("qualname"),
                "module_path": attrs.get("module_path"),
            }
        )

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print(
                f"{row['rank']:>3}  {row['score']:.6f}  "
                f"{row['kind']:<8}  {row['qualname']}  [{row['module_path']}]"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
