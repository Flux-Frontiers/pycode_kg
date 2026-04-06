# Embedder Benchmark Summary

## Provenance

| Field | Value |
|---|---|
| **PyCodeKG version** | 0.8.0 |
| **Branch** | `develop` |
| **HEAD commit** | `9b6218c` — fix: pass snapshot_mgr to PyCodeKGAnalyzer in analyze_repo() |
| **Run 1** | 2026-03-11T00:00:46 UTC — `embedder_benchmark_20260311_000046.md/.json` |
| **Run 2** | 2026-03-11T00:50:14 UTC — `embedder_benchmark_20260311_005014.md/.json` |
| **Repo indexed** | `/Users/egs/repos/pycode_kg` |
| **SQLite DB** | `.pycodekg/graph.sqlite` |
| **Indexed rows** | 349–350 nodes |
| **Hybrid weights** | semantic=0.7, lexical=0.3 |
| **Benchmark script** | `scripts/benchmark_embedders.py` |

---

## Models Tested

| Model | Dim | Approx build (s) |
|---|---:|---:|
| `all-MiniLM-L6-v2` | 384 | ~3.5 |
| `all-MiniLM-L12-v2` | 384 | ~0.8 |
| `BAAI/bge-small-en-v1.5` | 384 | ~1.2 |
| `all-mpnet-base-v2` | 768 | ~2.4 |
| `microsoft/codebert-base` | 768 | ~3.2 |

---

## Queries Used

| # | Query | Params | Character |
|---|---|---|---|
| Q1 | `snapshot freshness comparison` | k=8, hop=1, max_nodes=10 | Natural language, domain-specific terms |
| Q2 | `missing_lineno_policy cap_or_skip fallback` | k=6, hop=0, max_nodes=6 | Raw code identifiers |
| Q3 | `how does the graph get built from source code` | k=8, hop=1, max_nodes=8 | Natural language, general |

---

## Hybrid Score Comparison (Mean, across runs)

| Model | Q1 | Q2 | Q3 |
|---|---:|---:|---:|
| `all-MiniLM-L6-v2` | ~0.540 | ~0.310 | ~0.470 |
| `all-MiniLM-L12-v2` | ~0.551 | ~0.379 | ~0.456 |
| **`BAAI/bge-small-en-v1.5`** | **~0.648** | **~0.444** | **~0.564** |
| `all-mpnet-base-v2` | ~0.538 | ~0.317 | ~0.481 |
| `microsoft/codebert-base` | ~0.709* | ~0.659* | ~0.771* |

\* Inflated and meaningless — see CodeBERT section below.

---

## Findings

### 1. `BAAI/bge-small-en-v1.5` wins on every meaningful metric

BGE-small produces the highest **discriminative** hybrid scores across all three query types — and critically, the top-ranked nodes are actually relevant:

- **Q1** — `_snapshot_freshness` (0.690), `mcp_server` (0.690), `SnapshotManager.get_baseline` (0.637): all on-target
- **Q2** — `PyCodeKG.pack` (0.568), `_compute_span` (0.478): correct (span/lineno logic)
- **Q3** — `CodeGraph` (0.579), `ArchitectureAnalyzer._build_architecture_graph` (0.578): directly relevant

It also has a compact 384-dim space (fast indexing and query) with sub-1.5s build times — faster than `all-mpnet-base-v2` (768-dim, 2.4s) at higher quality, and faster than `all-MiniLM-L6-v2` (3.5s) at significantly higher quality.

---

### 2. `microsoft/codebert-base` is degenerate for this retrieval use case

CodeBERT reported the highest scores of any model (~0.90 semantic across the board), but those scores are **meaningless**. The embedding space is nearly uniform — all nodes receive near-identical cosine similarity values, making discrimination impossible.

Examples of catastrophic failures:

- Q2 ("missing_lineno_policy cap_or_skip fallback") → top semantic results: `PyCodeKG.__exit__`, `_docstring_signal`, `QueryResult.print_summary` at 0.907. **Completely unrelated.**
- Q3 ("how does the graph get built from source code") → top semantic results: `MainWindow.on_pick`, `MainWindow.highlight_actor`, `MainWindow.reset_actor_appearances` at 0.913. **3D visualizer methods, not graph construction.**
- Q1 ("snapshot freshness comparison") in legacy mode → `MainWindow.on_pick` and `PyCodeKG.__exit__` surface at the top.

#### Why CodeBERT fails here (and where it would work)

CodeBERT was pre-trained on raw source code tokens — Python syntax, identifiers, operators, AST-level structure. It is a **code understanding** model, not a semantic retrieval model. Its cosine similarity space is calibrated to code token proximity, not conceptual meaning.

It *would* be appropriate if PyCodeKG embedded the actual source code text (the raw function bodies as strings). In that case, CodeBERT's token-level representations would give it a structural advantage for identifier matching. But PyCodeKG embeds **node metadata** — qualified names, docstrings, signatures, and structural context. That's closer to natural language than Python syntax, and CodeBERT has no meaningful discrimination there.

**Bottom line:** CodeBERT produces a degenerate retrieval embedding space for PyCodeKG's metadata-based indexing. Do not use it.

---

### 3. `all-mpnet-base-v2` underperforms its size

768-dim, 2.4s build, yet hybrid scores trail BGE-small on every query. Q3 results in hybrid mode are particularly poor: `_tab_snippets` and `PyCodeKGVisitor._add_edge` surface at the top for "how does the graph get built from source code" — a UI tab widget and an edge-insertion helper. Higher cost, lower quality than BGE-small.

---

### 4. Hybrid mode: helpful for natural language queries, noisy for identifier queries

| Query type | Hybrid vs. Semantic |
|---|---|
| Natural language with domain terms (Q1) | Hybrid **wins** — lexical boost correctly elevates `_snapshot_freshness`, `SnapshotManager` |
| Raw code identifiers (Q2) | Hybrid **hurts** — lexical tokenization of compound identifiers is noisy; pure semantic is better |
| Natural language, general (Q3) | Hybrid is roughly equivalent to semantic |

For identifier-style queries, consider using `rerank_semantic_weight=1.0` or `hop=0` to let pure semantic scoring carry it without lexical interference.

---

## Conclusion

**`BAAI/bge-small-en-v1.5` is the canonical embedding model for PyCodeKG.**

This is not a default with alternatives — it is the right model for the job. The benchmark tested every credible alternative across natural-language, identifier, and mixed query types. BGE-small won every category that involves meaningful discrimination. No other model comes close when relevance correctness (not raw inflated scores) is the criterion.

The `DEFAULT_MODEL` constant in `src/pycode_kg/pycodekg.py` is set correctly. No change needed. This benchmark result locks it in.

| Setting | Value |
|---|---|
| **Canonical model** | `BAAI/bge-small-en-v1.5` |
| **Dimension** | 384 |
| **Build time** | ~1.2s |
| **Do not use** | `microsoft/codebert-base` for metadata retrieval |
| **Do not use** | `all-mpnet-base-v2` — higher cost, lower quality |
| **Identifier queries** | Prefer `rerank_semantic_weight=1.0` or `hop=0` |
