# CodeKG: Making Sense of Your Codebase (Without the Hallucination)

**We just released CodeKG.** It's a knowledge graph for Python codebases that lets you search, navigate, and extract code context with precision. No embeddings guessing. No probabilistic inference. Just structure + semantics working together.

---

## What's the Problem?

If you've ever tried to use semantic search on code, you've probably hit this: the embedding says your search result is close, but it's not actually related. Or you get snippets without line numbers. Or you can't trace back why a result even came up.

We built CodeKG to fix that.

---

## How It Works (Plain English)

**Step 1: Build the graph**
- CodeKG parses your Python repo with three passes:
  1. Extract structure (modules, classes, functions, calls, imports, inheritance)
  2. Build call graph (who calls who)
  3. Walk data-flow (variable reads/writes, attribute access)
- Everything goes into SQLite. This is your ground truth.

**Step 2: Add semantics**
- Embed the code (docstrings + names) into LanceDB for fast semantic search.
- This layer is *derived*—you can rebuild it anytime.

**Step 3: Query**
- You ask something like: *"database connection setup"*
- CodeKG finds semantically similar functions (the embedding layer)
- Then expands outward using the graph (all callers, all dependencies, etc.)
- Returns ranked, deduplicated results with exact line numbers.

**Step 4: Extract snippets**
- CodeKG pulls the actual source code from your files.
- You get definition snippets + call-site snippets.
- Every snippet has line numbers. Zero guessing.

---

## Why This Matters

**For solo developers:**
- Search your own codebase without thinking. No more grepping.
- Understand code flow interactively (Streamlit web app, 3D visualizer).

**For teams:**
- Onboard engineers faster. Give them precise, traceable context.
- Audit code changes. Know exactly which functions are affected.

**For AI agents (Claude, Copilot, etc.):**
- Feed LLMs precise context instead of hallucination-prone embeddings.
- When an agent uses the wrong code, you can see why (it's all traceable).

**For enterprises:**
- Store code structure in a canonical format. Build tools on top of it.
- Compliance: every answer is auditable.

---

## Technical Highlights

- **Deterministic** — same codebase, same graph, always.
- **Traceable** — every result maps to a file + line number.
- **Cross-module calls** — symbol resolution handles import aliases. `from utils import helper; helper()` → finds the actual `helper` definition.
- **Caller lookup** — find every place a function is called, even through imports.
- **Multiple outputs** — JSON, Markdown, interactive web, 3D graph, MCP server.

---

## Get Started

**Fastest way (one-liner):**

```bash
curl -fsSL https://raw.githubusercontent.com/Flux-Frontiers/code_kg/main/scripts/install-skill.sh | bash
```

This sets up everything: graph, index, MCP config, and integrates with your IDE.

**Manual:**

```bash
pip install 'code-kg @ git+https://github.com/Flux-Frontiers/code_kg.git'

# Build (full pipeline in one step)
codekg-build --repo .

# Or step by step
codekg-build-sqlite --repo .
codekg-build-lancedb --repo .

# Query
codekg-query "your search here"

# Pack source-grounded snippets for LLMs
codekg-pack "authentication flow" --out context.md

# Analyze codebase architecture
codekg-analyze .

# Visualize
codekg-viz          # Streamlit web app
codekg-viz3d        # 3D graph (PyVista)

# Start MCP server (Claude Code, Copilot, Cline, Continue)
codekg-mcp --repo .
```

---

## Repository & Docs

[**github.com/Flux-Frontiers/code_kg**](https://github.com/Flux-Frontiers/code_kg)

- Quick start guide in the README
- Full architecture & design philosophy in `/docs`
- MCP integration guide for Claude Code, GitHub Copilot, Cline, Continue
- Tests and examples in `/tests`

**License:** Elastic 2.0 (free to use, modify, distribute; no hosted service).

**Author:** Eric G. Suchanek, PhD

---

## Questions?

- How does it compare to GraphRAG? GraphRAG uses probabilistic inference. CodeKG uses deterministic AST parsing and structural graph traversal.
- Does it work with my IDE? Yes. MCP integration with Claude Code, GitHub Copilot, Cursor, Continue. Streamlit web app. 3D visualizer.
- Can I use this in production? Yes. It's read-only. Build the graph once, query infinite times.
- What's the license? Elastic 2.0. Free for internal use, no reselling.

Looking forward to feedback!
