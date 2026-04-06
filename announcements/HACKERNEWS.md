# CodeKG: Deterministic Knowledge Graph for Python Codebases

**Tagline:** A deterministic, auditable knowledge graph for Python codebases with semantic indexing and source-grounded snippet packing. Built with static analysis; used by Claude Code for precise code navigation and reasoning.

---

## The Problem

Most code search tools rely solely on embeddings or probabilistic inference. This creates three problems:

1. **No ground truth.** Embeddings rank relevance but can't verify what they're ranking — they can hallucinate structure.
2. **No auditability.** When an LLM gets the wrong code snippet, you can't trace why. The vector distance was close? That tells you nothing.
3. **Expensive and imprecise.** Dense embedding indexes are memory-heavy and struggle with exact structural queries (e.g., "find all callers of this function across modules").

---

## The Solution

CodeKG inverts the priority: **structure is authoritative; semantics accelerate retrieval.**

### What We Built

- **Deterministic knowledge graph** from Python AST — modules, classes, functions, methods, call graphs, imports, inheritance, data-flow. No heuristics. Identical input → identical output.
- **Symbol resolution** — Post-build pass bridges cross-module call sites via import aliases (e.g., `from utils import helper; helper()` resolves through `sym:` stubs).
- **Hybrid query model** — Semantic search seeds retrieval (LanceDB embeddings), structural graph expansion bounds and ranks results. Embeddings are an acceleration layer, never a decision layer.
- **Source-grounded snippet packing** — Extract definition and call-site code with exact line numbers. No synthetic context; every snippet maps to a file and line range.
- **MCP server** — Five tools (`query_codebase`, `pack_snippets`, `callers`, `get_node`, `graph_stats`) integrate CodeKG into Claude Code, GitHub Copilot, Cursor, Continue, and custom agents.

### The Payoff

**For AI agents:** Precise, auditable code context. No hallucination. Every snippet is traceable.

**For developers:** Interactive exploration. Streamlit web app for browsing. 3D graph visualizer. CLI for scripting.

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

## Quick Start

**One-line installer** (runs inside your repo):

```bash
curl -fsSL https://raw.githubusercontent.com/Flux-Frontiers/code_kg/main/scripts/install-skill.sh | bash
```

This sets up:
- SQLite knowledge graph (`.codekg/graph.sqlite`)
- LanceDB semantic index
- MCP config for Claude Code, GitHub Copilot, Cline, or Claude Desktop
- Skill files for integration

**Build manually:**

```bash
pip install 'code-kg @ git+https://github.com/Flux-Frontiers/code_kg.git'

# Full pipeline in one step
codekg build --repo /path/to/repo

# Or step by step
codekg build-sqlite --repo /path/to/repo
codekg build-lancedb --repo /path/to/repo
```

**Query:**

```bash
codekg query "database connection setup"
```

**Pack source-grounded snippets for LLMs:**

```bash
codekg pack "authentication flow" --out context.md
```

**Analyze codebase architecture:**

```bash
codekg analyze .
```

**Visualize:**

```bash
codekg viz          # Streamlit web app
codekg viz3d        # 3D graph (PyVista)
```

**Integrate with agents:**

```bash
codekg mcp          # MCP server (Claude Code, Copilot, Cline, Continue)
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

[github.com/Flux-Frontiers/code_kg](https://github.com/Flux-Frontiers/code_kg)

**License:** Elastic License 2.0 (free to use, modify, and distribute; no hosted service reselling).

**Author:** Eric G. Suchanek, PhD (Flux-Frontiers, Liberty TWP, OH)

---

## Related Work

- **Microsoft GraphRAG** — Probabilistic inference; CodeKG prioritizes determinism and auditability.
- **Amplify** — Embedding-only search; CodeKG augments with structural graph traversal.
- **LanceDB** — Vector database used for semantic indexing in CodeKG.
