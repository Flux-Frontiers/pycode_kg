# PR: Add Structural Importance Ranking (SIR) centrality analysis

## Summary

This PR adds **Structural Importance Ranking (SIR)** to CodeKG: a deterministic weighted-PageRank analysis over the resolved structural graph.

## Why

CodeKG already builds a deterministic SQLite-backed knowledge graph from AST structure and adds `RESOLVES_TO` edges to recover cross-module call relationships. SIR extends that model with an explainable notion of architectural importance: components rank highly when many important parts of the system rely on them. citeturn438305view0turn591393view1

## Included

- `docs/structural_importance.md`
- `src/code_kg/analysis/centrality.py`
- `src/code_kg/analysis/__init__.py`
- `src/code_kg/cli/cmd_centrality.py`
- `sql/004_add_centrality_table.sql`
- `tests/test_centrality.py`

## Features

- weighted PageRank over `CALLS`, `INHERITS`, `IMPORTS`, `CONTAINS`
- `sym:` stub normalization through existing `RESOLVES_TO` edges
- cross-module dependency boosting
- optional private-symbol penalty
- node-level and module-level rankings
- optional persistence to `centrality_scores`

## Example

```bash
codekg centrality --db .codekg/graph.sqlite --top 25
codekg centrality --db .codekg/graph.sqlite --group-by module
codekg centrality --db .codekg/graph.sqlite --write-db
```

## Notes

The public repo currently uses a Click-based CLI under `src/code_kg/cli/` and keeps SQLite schema creation inline in `store.py`, so this PR follows that architecture rather than introducing a new migration framework. citeturn820418view3turn591393view1
