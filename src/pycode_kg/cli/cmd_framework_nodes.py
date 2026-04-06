"""
CLI command for framework node detection in PyCodeKG.
"""

import argparse

from pycode_kg.analysis.framework_detector import detect_framework_nodes


def main():
    parser = argparse.ArgumentParser(description="Show top framework-like modules.")
    parser.add_argument("--db", default="pycodekg.sqlite", help="Path to PyCodeKG SQLite DB")
    parser.add_argument("--top", type=int, default=25, help="Number of top framework nodes to show")
    args = parser.parse_args()
    nodes = detect_framework_nodes(limit=args.top, db_path=args.db)
    print(f"Top {args.top} framework-like modules:")
    for node_id, score, label in nodes:
        print(f"{label:50s}  {score:.5f}  ({node_id})")
