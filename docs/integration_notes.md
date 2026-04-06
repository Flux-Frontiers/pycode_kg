# Wiring SIR into the current PyCodeKG repo

These files are designed for the current public PyCodeKG layout, which places source code under `src/pycode_kg/`, uses a Click-based CLI, and stores the authoritative graph in SQLite with `nodes` and `edges` tables plus a `resolve_symbols()` pass in `GraphStore`. citeturn820418view3turn591393view1

## 1. Add the new files

Copy these into the repo:

- `docs/structural_importance.md`
- `src/pycode_kg/analysis/__init__.py`
- `src/pycode_kg/analysis/centrality.py`
- `src/pycode_kg/cli/cmd_centrality.py`
- `sql/004_add_centrality_table.sql`
- `tests/test_centrality.py`

## 2. Register the CLI command

Edit `src/pycode_kg/cli/main.py` and import/register the new Click command.

Suggested patch:

```python
import importlib.metadata
import click

from pycode_kg.cli.cmd_centrality import cmd_centrality

@click.group()
@click.version_option(version=importlib.metadata.version("pycode-kg"))
def cli():
    """PyCodeKG — knowledge graph tools for Python codebases."""
    pass

cli.add_command(cmd_centrality)
```

The public repo currently shows `main.py` as the root Click group, with command modules under `src/pycode_kg/cli/`. citeturn820418view3turn591393view0

## 3. Decide how you want persistence handled

There are two viable models:

### Minimal-change model

Keep the current `GraphStore` schema untouched and let `centrality.py` create `centrality_scores` lazily when `--write-db` is used.

### Full-schema model

Move the `CREATE TABLE centrality_scores ...` SQL into the main `_SCHEMA_SQL` string in `store.py`.

Given the current repo, the minimal-change model is the safest first PR because `store.py` owns the schema inline rather than via an external migration framework. citeturn591393view1

## 4. Recommended usage

```bash
a) build the graph
   pycodekg build --repo .

b) ensure symbols are resolved
   # wherever your build pipeline already invokes GraphStore.resolve_symbols()

c) run centrality
   pycodekg centrality --db .pycodekg/graph.sqlite --top 25

# persist results
pycodekg centrality --db .pycodekg/graph.sqlite --write-db

# module-level view
pycodekg centrality --db .pycodekg/graph.sqlite --group-by module
```

## 5. Recommended PR sequence

1. Docs + algorithm core  
2. CLI registration  
3. Optional persistence/MCP exposure
