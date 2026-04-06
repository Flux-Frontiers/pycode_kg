# CodeRank for CodeKG

## Overview

This bundle adds a structurally grounded ranking layer to CodeKG:

- **Global CodeRank**: weighted PageRank over the repository graph
- **Hybrid query ranking**: semantic relevance + global centrality + seed proximity
- **Personalized CodeRank**: personalized PageRank over a query-induced subgraph
- **Explainability hooks**: per-node score components and simple `why` strings

The design matches CodeKG's existing architecture: structure remains authoritative, and semantic signals accelerate retrieval rather than override it.

## Recommended defaults

### Global architectural rank

Use a weighted directed graph with these default relation strengths:

| Relation | Weight | Rationale |
|---|---:|---|
| `CALLS` | 1.00 | Direct execution influence |
| `IMPORTS` | 0.90 | Strong module-level dependence |
| `INHERITS` | 0.75 | Architectural type dependence |
| `RESOLVES_TO` | 0.30 | Repairs indirection but is not itself authority |
| `CONTAINS` | 0.15 | Weak containment signal only |
| `ATTR_ACCESS` | 0.10 | Secondary structural signal |
| `READS` / `WRITES` | 0.05 | Very light data-flow enrichment |

Default target-kind priors:

| Kind | Prior |
|---|---:|
| `function`, `method` | 1.00 |
| `class` | 0.92 |
| `module` | 0.80 |
| `symbol`, `attribute` | 0.50 |

Exclude tests by default from global centrality.

### Hybrid query ranking

Use:

\[
\mathrm{FinalScore}(v \mid q)
= 0.60\,S(v,q) + 0.25\,C(v) + 0.15\,P(v,q)
\]

where:

- \(S(v,q)\): normalized semantic score
- \(C(v)\): normalized global CodeRank
- \(P(v,q)\): inverse shortest-path proximity to the seed set

This works well when semantic relevance should dominate but structural importance should break ties.

### Personalized PageRank query mode

Use a query-induced subgraph around the semantic seeds and compute personalized PageRank with teleport mass proportional to the seed scores. Recommended final combination:

\[
\mathrm{FinalScore}_{\mathrm{PPR}}(v \mid q)
= 0.70\,\mathrm{PPR}(v \mid q) + 0.30\,S(v,q)
\]

This often outperforms the simple hybrid baseline for interactive search.

## Why PageRank here is appropriate

CodeKG already captures relations such as `CALLS`, `IMPORTS`, and `INHERITS` in a directed graph. Those edges naturally encode dependency and authority flow:

- caller \(\rightarrow\) callee
- importer \(\rightarrow\) imported module
- subclass \(\rightarrow\) base class

A node that receives edges from many important upstream nodes should rank highly. Weighted PageRank captures exactly that.

## What this bundle contains

- `src/codekg/ranking/coderank.py`
  - graph builder from SQLite
  - global CodeRank
  - personalized CodeRank
  - query subgraph induction
  - proximity scoring
  - hybrid score combination
  - SQLite persistence helper
- `src/codekg/ranking/cli_rank.py`
  - minimal CLI for top-ranked nodes
- `tests/test_coderank.py`
  - small integration-style smoke test

## Suggested usage pattern

1. Build the CodeKG SQLite graph as usual.
2. Compute global CodeRank once after graph build.
3. Persist `coderank_global` into `node_metrics`.
4. At query time:
   - get top semantic seeds from the vector index
   - induce a local graph around the seeds
   - rank using either hybrid mode or personalized PageRank
   - return score components and a short explanation

## Suggested SQLite persistence schema

```sql
CREATE TABLE IF NOT EXISTS node_metrics (
    node_id TEXT NOT NULL,
    metric TEXT NOT NULL,
    score REAL NOT NULL,
    computed_at TEXT NOT NULL,
    PRIMARY KEY (node_id, metric)
);
```

Persist at least:

- `coderank_global`
- `fan_in`
- `fan_out`
- later: `betweenness`

## Important implementation notes

### 1. Avoid `CONTAINS` dominating global rank

Containment is useful context but a poor primary authority signal. Keep it weak or omit it from global runs.

### 2. Exclude tests by default

Test helpers and fixtures can dominate fan-in and distort architecture.

### 3. Be careful with betweenness later

The weights in this module are **strengths**, but weighted shortest-path algorithms interpret weights as **distances**. If you later compute weighted betweenness, convert strengths into distances, for example:

\[
\ell(e)=\frac{1}{w(e)+\varepsilon}
\]

### 4. Strongly connected components

Large utility clusters can inflate each other. If this becomes visible in practice, consider collapsing SCCs before global rank.

## Recommended CLI surface

```bash
codekg rank --sqlite .codekg/graph.sqlite --top 50 --metric coderank
codekg rank --sqlite .codekg/graph.sqlite --persist-metric coderank_global
codekg search "database connection" --rank hybrid
codekg search "database connection" --rank ppr
```

## Explainability output

For each result, expose:

- `semantic_score`
- `centrality_score`
- `proximity_score`
- `adjusted_score`
- `kind`
- `qualname`
- `module_path`
- `why`

Example `why` strings:

- called by 12 upstream node(s)
- imported by 4 upstream node(s)
- strong semantic match to the query
- high centrality within the ranked subgraph
- one hop from a semantic seed

That preserves CodeKG's deterministic and auditable character.
