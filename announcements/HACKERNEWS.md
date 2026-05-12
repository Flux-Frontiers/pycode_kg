# PyCodeKG: Deterministic Knowledge Graph for Python Codebases

**Tagline:** A deterministic, auditable knowledge graph for Python codebases with semantic indexing and source-grounded snippet packing. Built with static analysis; used by Claude Code for precise code navigation and reasoning.

---

## The Problem

Most code search tools rely solely on embeddings or probabilistic inference. This creates three problems:

1. **No ground truth.** Embeddings rank relevance but can't verify what they're ranking — they can hallucinate structure.
2. **No auditability.** When an LLM gets the wrong code snippet, you can't trace why. The vector distance was close? That tells you nothing.
3. **Expensive and imprecise.** Dense embedding indexes are memory-heavy and struggle with exact structural queries (e.g., "find all callers of this function across modules").

---

## The Solution

PyCodeKG inverts the priority: **structure is authoritative; semantics accelerate retrieval.**

### What We Built

- **Deterministic knowledge graph** from Python AST — modules, classes, functions, methods, call graphs, imports, inheritance, data-flow. No heuristics. Identical input → identical output.
- **Symbol resolution** — Post-build pass bridges cross-module call sites via import aliases (e.g., `from utils import helper; helper()` resolves through `sym:` stubs).
- **Hybrid query model** — Semantic search seeds retrieval (LanceDB embeddings), structural graph expansion bounds and ranks results. Embeddings are an acceleration layer, never a decision layer.
- **Source-grounded snippet packing** — Extract definition and call-site code with exact line numbers. No synthetic context; every snippet maps to a file and line range.
- **MCP server** — Five tools (`query_codebase`, `pack_snippets`, `callers`, `get_node`, `graph_stats`) integrate PyCodeKG into Claude Code, GitHub Copilot, Cursor, Continue, and custom agents.

### The Payoff

**For AI agents:** Precise, auditable code context. No hallucination. Every snippet is traceable.

**For developers:** Interactive exploration. Streamlit web app for browsing. 3D graph visualizer (`viz3d`) — actively in development, functional but rough around the edges. CLI for scripting.

**For enterprises:** A canonical, SQLite-backed store of code structure that supports deterministic reasoning, compliance auditing, and downstream tool integration.

---

## Tech Details

**Three-pass AST pipeline:**
1. Structural extraction (modules, classes, functions, imports, inheritance)
2. Call graph (call expressions resolved to targets)
3. Data-flow (variable reads/writes, attribute access)

**Output:** SQLite (canonical) + LanceDB (derived semantic index).

**Query execution:**
1. Semantic seeding (natural-language query → vector search → entry points)
2. Structural expansion (graph traversal from seeds using selected edge types: `CONTAINS`, `CALLS`, `IMPORTS`, `INHERITS`)
3. Ranking (hop distance, embedding distance, node kind priority)
4. Snippet extraction (definition spans + call-site spans with context)

**Caller lookup:** Two-phase reverse traversal resolving `sym:` stubs via `RESOLVES_TO` edges. Finds every caller of a function, even across module boundaries.

---

## The Fast Win: `pycodekg analyze`

Honest admission: this single command is the actual reason this project exists. I got tired of watching my LLM grep through `src/` every time I asked for a codebase analysis. So I built a proper 15-phase structural pipeline that runs in seconds and hands the LLM something it can actually reason about. I ran it against **numpy** and **matplotlib** for fun — the reports are in `analysis/` in the repo.

One command, 15 analysis passes, seconds to run, Markdown output you can paste straight into Claude or ChatGPT for actionable improvement suggestions.

```bash
pip install 'pycode-kg[viz,viz3d]'
pycodekg init --repo .    # download model, build graph, install hooks, snapshot
pycodekg analyze .        # the full report
```

> **Note:** First run downloads the embedder model — be patient. Subsequent runs are fast.

The pipeline runs these phases in order:

| # | Phase | What it surfaces |
|---|-------|-----------------|
| 1 | Baseline metrics | Node/edge counts, graph shape |
| 2 | CodeRank (global PageRank) | Structurally most important symbols |
| 3 | Fan-in analysis | Heavily depended-on functions (breaking-change risk) |
| 4 | Fan-out analysis | Orchestrators and complexity hotspots |
| 5 | Dependency analysis | Orphaned / dead code candidates |
| 6 | Pattern detection | Anti-patterns and structural red flags |
| 7 | Module coupling | Tightly coupled pairs, import graph density |
| 8 | Critical paths | Longest call chains, bottlenecks |
| 9 | Public API identification | Exposed vs. internal surface |
| 10 | Docstring coverage | By module, class, function, method |
| 11 | Inheritance hierarchy | Depth, multiple inheritance, diamond patterns |
| 12 | Insight synthesis | Issues + strengths callouts |
| 13 | Snapshot history | Metric trends across releases |
| 14 | Structural centrality (SIR) | Bridge nodes, graph removal impact |
| 15 | Concern-based ranking | Nodes grouped by architectural concern |

Every finding maps to a file and line number. The JSON output is CI-gate-ready; the Markdown output is LLM-ready.

---

## Quick Start

```bash
pip install 'pycode-kg[viz,viz3d]'   # base + Streamlit + 3D viewer

cd /path/to/your/repo
pycodekg init --repo .               # download model, build graph, install hooks, snapshot
pycodekg analyze .                   # architectural report
```

**Query:**

```bash
pycodekg query "database connection setup"
```

**Pack source-grounded snippets for LLMs:**

```bash
pycodekg pack "authentication flow" --out context.md
```

**Analyze codebase architecture:**

```bash
pycodekg analyze .
```

**Visualize:**

```bash
pycodekg viz          # Streamlit web app
pycodekg viz3d        # 3D graph (PyVista) — actively in development, rough around the edges
```

**Integrate with agents:**

```bash
pycodekg mcp          # MCP server (Claude Code, Copilot, Cline, Continue)
```

---

## Philosophy

1. **Structure is authoritative** — AST-derived graph is source of truth.
2. **Semantics accelerate, never decide** — Embeddings are entry points, not arbiters.
3. **Everything is traceable** — Every node and edge maps to file + line number.
4. **Determinism over heuristics** — Same input, same output, always.
5. **Composable artifacts** — SQLite for structure, LanceDB for vectors, Markdown/JSON for consumption.

---

## Repository

[github.com/Flux-Frontiers/pycode_kg](https://github.com/Flux-Frontiers/pycode_kg)

**License:** Elastic License 2.0 (free to use, modify, and distribute; no hosted service reselling).

**Author:** Eric G. Suchanek, PhD (Flux-Frontiers, Liberty TWP, OH)

---

## Related Work

- **Microsoft GraphRAG** — Probabilistic inference; PyCodeKG prioritizes determinism and auditability.
- **Amplify** — Embedding-only search; PyCodeKG augments with structural graph traversal.
- **LanceDB** — Vector database used for semantic indexing in PyCodeKG.
