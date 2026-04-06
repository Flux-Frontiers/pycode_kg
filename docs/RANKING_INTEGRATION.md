# Integration Notes for PyCodeKG

## Goal

Integrate CodeRank without disrupting the current PyCodeKG build and query flow.

Current flow, conceptually:

```text
repo -> AST passes -> SQLite graph -> semantic index -> query -> graph expansion -> ranking -> snippets
```

Target flow:

```text
repo -> AST passes -> SQLite graph
                         |-> global CodeRank persisted in node_metrics
                         |-> semantic index
query -> semantic seeds -> local subgraph -> hybrid rank / PPR -> explanations -> snippets
```

## Minimal integration plan

### Step 1. Add the ranking module

Place:

- `src/pycodekg/ranking/coderank.py`
- `src/pycodekg/ranking/cli_rank.py`

and register a CLI command that points to `pycodekg.ranking.cli_rank:main`.

### Step 2. Compute global rank after graph build

After the SQLite graph is complete:

1. build a directed weighted graph from the `nodes` and `edges` tables
2. compute global CodeRank on selected relations:
   - `CALLS`
   - `IMPORTS`
   - `INHERITS`
   - optionally `RESOLVES_TO`
3. persist to `node_metrics` as `coderank_global`

This should be a post-build step, not part of every query.

### Step 3. Read global rank during query

At query time:

1. get semantic seed nodes from the vector layer
2. induce a local graph within 1-2 hops of the seeds
3. load `coderank_global` for nodes in that local graph
4. compute:
   - hybrid rank, or
   - personalized PageRank over the local graph
5. sort by adjusted score
6. pass the highest-ranked nodes into snippet packing / explanation tools

### Step 4. Expose rank explanations

Add fields like:

```json
{
  "node_id": "...",
  "score": 0.842,
  "semantic_score": 0.79,
  "centrality_score": 0.61,
  "proximity_score": 1.0,
  "kind": "function",
  "qualname": "project.db.connect",
  "why": [
    "called by 12 upstream node(s)",
    "strong semantic match to the query",
    "one hop from a semantic seed"
  ]
}
```

## Suggested API-level additions

### CLI

```bash
pycodekg rank --sqlite .pycodekg/graph.sqlite --top 25
pycodekg rank --sqlite .pycodekg/graph.sqlite --persist-metric coderank_global
```

### Query path

Your existing search/query command can add a `--rank` option:

```bash
pycodekg query "database connection" --rank hybrid
pycodekg query "database connection" --rank ppr
```

### MCP tools

Useful additions later:

- `rank_nodes`
- `critical_nodes`
- `query_ranked`
- `explain_rank`

## Score combination defaults

### Simple hybrid

\[
0.60S + 0.25C + 0.15P
\]

where:

- \(S\) = semantic score
- \(C\) = global CodeRank
- \(P\) = inverse-distance proximity to seed set

### Personalized PageRank mode

\[
0.70\,\mathrm{PPR} + 0.30\,S
\]

Personalized PageRank generally yields cleaner rankings when the local graph is reasonably small.

## Performance expectations

For the graph size you mentioned earlier, roughly **20k edges**, this implementation should be comfortably feasible with NetworkX for:

- global CodeRank after build
- query-local personalized PageRank
- occasional diagnostics

If graphs become much larger or ranking becomes a latency bottleneck, the same math can later be moved to sparse matrices or GraphBLAS-backed routines.

## Recommended follow-on metrics

Once CodeRank is working well:

1. **Fan-in / fan-out**
   - easy to compute
   - highly interpretable

2. **Betweenness**
   - identifies bridge nodes and chokepoints
   - remember to convert strength weights into distances

3. **SCC-aware reporting**
   - detect strongly connected utility clusters
   - optionally collapse them for cleaner architecture summaries

4. **Architectural importance**
   - a composite metric such as:
   \[
   \mathrm{AI}(v)=\mathrm{CodeRank}(v)\cdot \log(1+\mathrm{FanIn}(v))
   \]

## Licensing note

Your repository currently advertises **Elastic License 2.0** in the README badge, so these additions are intended to be incorporated under the repository's existing license unless you decide otherwise. If you later split ranking into a standalone package, revisit that decision explicitly.
