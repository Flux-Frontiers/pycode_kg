#!/usr/bin/env python3
"""Benchmark candidate embedding models for CodeKG query quality.

This script rebuilds a LanceDB index for each model, runs a fixed query suite
across one or more rerank modes, and writes a machine-readable JSON report plus
an analyst-friendly Markdown summary.

Usage example:

    python scripts/benchmark_embedders.py \
      --repo-root . \
      --sqlite .codekg/graph.sqlite \
      --models "all-MiniLM-L6-v2,all-MiniLM-L12-v2,BAAI/bge-small-en-v1.5,all-mpnet-base-v2" \
      --modes "hybrid,semantic,legacy"
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Allow direct execution from repo root without requiring installation.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from code_kg import CodeKG  # noqa: E402


@dataclass(frozen=True)
class QueryCase:
    """A benchmark query specification.

    :param name: Short human-readable label.
    :param text: Natural-language query text.
    :param k: Number of semantic seeds.
    :param hop: Expansion hop count.
    :param max_nodes: Maximum returned nodes.
    """

    name: str
    text: str
    k: int
    hop: int
    max_nodes: int


DEFAULT_QUERY_CASES = [
    QueryCase(
        name="snapshot freshness comparison",
        text="snapshot freshness comparison",
        k=8,
        hop=1,
        max_nodes=10,
    ),
    QueryCase(
        name="missing lineno fallback",
        text="missing_lineno_policy cap_or_skip fallback",
        k=6,
        hop=0,
        max_nodes=6,
    ),
    QueryCase(
        name="graph build from source",
        text="how does the graph get built from source code",
        k=8,
        hop=1,
        max_nodes=8,
    ),
]


def _slugify_model(model: str) -> str:
    """Convert model id into a stable filesystem-safe slug.

    :param model: Model identifier.
    :return: Slug string.
    """

    return re.sub(r"[^a-zA-Z0-9._-]+", "_", model).strip("_")


def _top_metrics(nodes: list[dict], top_n: int) -> dict[str, float | int]:
    """Compute compact quality metrics from ranked nodes.

    :param nodes: Ranked node dictionaries from ``CodeKG.query``.
    :param top_n: Prefix length to summarize.
    :return: Metrics dictionary.
    """

    top = nodes[:top_n]
    if not top:
        return {
            "returned": 0,
            "mean_score": 0.0,
            "mean_semantic": 0.0,
            "mean_lexical": 0.0,
            "mean_docstring_signal": 0.0,
            "mean_hop": 0.0,
        }

    def _field(name: str) -> list[float]:
        vals: list[float] = []
        for node in top:
            rel = node.get("relevance") or {}
            vals.append(float(rel.get(name, 0.0)))
        return vals

    scores = _field("score")
    sem = _field("semantic")
    lex = _field("lexical")
    ds = _field("docstring_signal")
    hops = _field("hop")

    return {
        "returned": len(nodes),
        "mean_score": float(statistics.fmean(scores)),
        "mean_semantic": float(statistics.fmean(sem)),
        "mean_lexical": float(statistics.fmean(lex)),
        "mean_docstring_signal": float(statistics.fmean(ds)),
        "mean_hop": float(statistics.fmean(hops)),
    }


def _run_benchmark(
    repo_root: Path,
    sqlite_path: Path,
    lancedb_root: Path,
    models: list[str],
    modes: list[str],
    query_cases: list[QueryCase],
    top_n: int,
    semantic_weight: float,
    lexical_weight: float,
) -> dict:
    """Run the full benchmark matrix.

    :param repo_root: Repository root.
    :param sqlite_path: SQLite graph path.
    :param lancedb_root: Root output dir for per-model LanceDB indexes.
    :param models: Candidate model names.
    :param modes: Rerank modes to evaluate.
    :param query_cases: Query set.
    :param top_n: Prefix size for summary metrics.
    :param semantic_weight: Hybrid semantic weight.
    :param lexical_weight: Hybrid lexical weight.
    :return: Structured benchmark result.
    """

    started = datetime.now(UTC).isoformat()
    out: dict = {
        "started_utc": started,
        "repo_root": str(repo_root),
        "sqlite": str(sqlite_path),
        "lancedb_root": str(lancedb_root),
        "models": models,
        "modes": modes,
        "top_n": top_n,
        "hybrid_weights": {
            "semantic": semantic_weight,
            "lexical": lexical_weight,
        },
        "query_cases": [qc.__dict__ for qc in query_cases],
        "results": [],
    }

    for model in models:
        model_slug = _slugify_model(model)
        model_lancedb = lancedb_root / model_slug
        model_lancedb.mkdir(parents=True, exist_ok=True)

        print(f"\n=== Model: {model} ===")
        print(f"Rebuilding LanceDB at {model_lancedb} ...")
        t0 = time.perf_counter()
        kg = CodeKG(
            repo_root=repo_root,
            db_path=sqlite_path,
            lancedb_dir=model_lancedb,
            model=model,
        )
        idx_stats = kg.build_index(wipe=True)
        build_seconds = time.perf_counter() - t0
        print(
            f"Indexed {idx_stats.indexed_rows} rows (dim={idx_stats.index_dim}) in {build_seconds:.2f}s"
        )

        model_result: dict = {
            "model": model,
            "model_slug": model_slug,
            "lancedb_dir": str(model_lancedb),
            "build_index": {
                "seconds": build_seconds,
                "indexed_rows": idx_stats.indexed_rows,
                "index_dim": idx_stats.index_dim,
            },
            "queries": [],
        }

        for qc in query_cases:
            case_result: dict = {
                "name": qc.name,
                "query": qc.text,
                "k": qc.k,
                "hop": qc.hop,
                "max_nodes": qc.max_nodes,
                "modes": [],
            }

            for mode in modes:
                t1 = time.perf_counter()
                qr = kg.query(
                    qc.text,
                    k=qc.k,
                    hop=qc.hop,
                    max_nodes=qc.max_nodes,
                    rerank_mode=mode,
                    rerank_semantic_weight=semantic_weight,
                    rerank_lexical_weight=lexical_weight,
                )
                query_seconds = time.perf_counter() - t1

                top_nodes: list[dict] = []
                for rank, node in enumerate(qr.nodes[:top_n], start=1):
                    rel = node.get("relevance") or {}
                    top_nodes.append(
                        {
                            "rank": rank,
                            "id": node.get("id"),
                            "kind": node.get("kind"),
                            "qualname": node.get("qualname") or node.get("name"),
                            "module_path": node.get("module_path"),
                            "score": float(rel.get("score", 0.0)),
                            "semantic": float(rel.get("semantic", 0.0)),
                            "lexical": float(rel.get("lexical", 0.0)),
                            "docstring_signal": float(rel.get("docstring_signal", 0.0)),
                            "hop": int(rel.get("hop", 0)),
                        }
                    )

                case_result["modes"].append(
                    {
                        "mode": mode,
                        "seconds": query_seconds,
                        "seeds": qr.seeds,
                        "expanded_nodes": qr.expanded_nodes,
                        "returned_nodes": qr.returned_nodes,
                        "summary": _top_metrics(qr.nodes, top_n=top_n),
                        "top_nodes": top_nodes,
                    }
                )

            model_result["queries"].append(case_result)

        kg.close()
        out["results"].append(model_result)

    out["completed_utc"] = datetime.now(UTC).isoformat()
    return out


def _to_markdown(report: dict) -> str:
    """Render a concise markdown summary.

    :param report: Report dictionary from ``_run_benchmark``.
    :return: Markdown string.
    """

    lines: list[str] = []
    lines.append("# Embedder Benchmark Report")
    lines.append("")
    lines.append(f"- Started (UTC): {report['started_utc']}")
    lines.append(f"- Completed (UTC): {report.get('completed_utc', 'n/a')}")
    lines.append(f"- Repo: `{report['repo_root']}`")
    lines.append(f"- SQLite: `{report['sqlite']}`")
    lines.append(f"- LanceDB root: `{report['lancedb_root']}`")
    lines.append(
        "- Hybrid weights: "
        f"semantic={report['hybrid_weights']['semantic']}, "
        f"lexical={report['hybrid_weights']['lexical']}"
    )
    lines.append("")

    for model_result in report["results"]:
        model = model_result["model"]
        build = model_result["build_index"]
        lines.append(f"## Model: `{model}`")
        lines.append(
            f"- Build: {build['seconds']:.2f}s, indexed_rows={build['indexed_rows']}, dim={build['index_dim']}"
        )
        lines.append("")

        for case in model_result["queries"]:
            lines.append(f"### Query: `{case['query']}`")
            lines.append(
                f"- Params: k={case['k']}, hop={case['hop']}, max_nodes={case['max_nodes']}"
            )
            lines.append("")
            lines.append(
                "| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | "
                "Mean semantic | Mean lexical |"
            )
            lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

            for mode_data in case["modes"]:
                s = mode_data["summary"]
                lines.append(
                    "| "
                    f"`{mode_data['mode']}` | {mode_data['seconds']:.3f} | {mode_data['seeds']} "
                    f"| {mode_data['expanded_nodes']} | {mode_data['returned_nodes']} "
                    f"| {s['mean_score']:.3f} | {s['mean_semantic']:.3f} | {s['mean_lexical']:.3f} |"
                )

            lines.append("")
            for mode_data in case["modes"]:
                lines.append(f"#### Top nodes ({mode_data['mode']})")
                for node in mode_data["top_nodes"]:
                    lines.append(
                        f"- {node['rank']}. `{node['qualname']}` "
                        f"(score={node['score']:.3f}, sem={node['semantic']:.3f}, "
                        f"lex={node['lexical']:.3f}, hop={node['hop']})"
                    )
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root path.")
    parser.add_argument(
        "--sqlite",
        default=".codekg/graph.sqlite",
        help="Path to existing CodeKG SQLite graph.",
    )
    parser.add_argument(
        "--lancedb-root",
        default=".codekg/lancedb-benchmark",
        help="Root dir for per-model LanceDB indexes.",
    )
    parser.add_argument(
        "--models",
        default=(
            "all-MiniLM-L6-v2,all-MiniLM-L12-v2,"
            "BAAI/bge-small-en-v1.5,all-mpnet-base-v2,microsoft/codebert-base"
        ),
        help="Comma-separated model ids.",
    )
    parser.add_argument(
        "--modes",
        default="hybrid,semantic,legacy",
        help="Comma-separated rerank modes.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Top nodes to capture per query/mode.",
    )
    parser.add_argument(
        "--hybrid-semantic-weight",
        type=float,
        default=0.7,
        help="Hybrid semantic weight.",
    )
    parser.add_argument(
        "--hybrid-lexical-weight",
        type=float,
        default=0.3,
        help="Hybrid lexical weight.",
    )
    parser.add_argument(
        "--out-json",
        default="",
        help="Output JSON file path (default: analysis/embedder_benchmark_<timestamp>.json).",
    )
    parser.add_argument(
        "--out-md",
        default="",
        help="Output Markdown file path (default: analysis/embedder_benchmark_<timestamp>.md).",
    )
    return parser.parse_args()


def main() -> int:
    """Run the benchmark and write reports."""

    args = _parse_args()

    repo_root = Path(args.repo_root).resolve()
    sqlite_path = (repo_root / args.sqlite).resolve()
    lancedb_root = (repo_root / args.lancedb_root).resolve()

    if not sqlite_path.exists():
        print(f"ERROR: SQLite graph not found at {sqlite_path}")
        print("Build it first, e.g.: .venv/bin/codekg build-sqlite --repo . --wipe")
        return 2

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    out_json = (
        Path(args.out_json)
        if args.out_json
        else repo_root / "analysis" / f"embedder_benchmark_{ts}.json"
    )
    out_md = (
        Path(args.out_md) if args.out_md else repo_root / "analysis" / f"embedder_benchmark_{ts}.md"
    )

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    lancedb_root.mkdir(parents=True, exist_ok=True)

    print("Starting embedder benchmark ...")
    report = _run_benchmark(
        repo_root=repo_root,
        sqlite_path=sqlite_path,
        lancedb_root=lancedb_root,
        models=models,
        modes=modes,
        query_cases=DEFAULT_QUERY_CASES,
        top_n=args.top_n,
        semantic_weight=args.hybrid_semantic_weight,
        lexical_weight=args.hybrid_lexical_weight,
    )

    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(_to_markdown(report), encoding="utf-8")

    print(f"Wrote JSON report: {out_json}")
    print(f"Wrote Markdown report: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
