"""
CLI command for bridge centrality in CodeKG.
"""

import argparse

from code_kg.analysis.bridge import compute_bridge_centrality


def main():
    parser = argparse.ArgumentParser(
        description="Show top bridge modules by betweenness centrality."
    )
    parser.add_argument("--db", default="codekg.sqlite", help="Path to CodeKG SQLite DB")
    parser.add_argument("--top", type=int, default=25, help="Number of top bridges to show")
    parser.add_argument("--no-imports", action="store_true", help="Ignore IMPORTS edges")
    args = parser.parse_args()
    bridges = compute_bridge_centrality(
        kind="module",
        include_imports=not args.no_imports,
        top=args.top,
        db_path=args.db,
    )
    print(f"Top {args.top} bridge modules:")
    for mod, score in bridges:
        print(f"{mod:50s}  {score:.5f}")
