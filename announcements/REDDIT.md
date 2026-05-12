# PyCodeKG: Making Sense of Your Codebase (Without the Hallucination)

**We just released PyCodeKG.** It's a knowledge graph for Python codebases that lets you search, navigate, and extract code context with precision. No embeddings guessing. No probabilistic inference. Just structure + semantics working together.

---

## What's the Problem?

If you've ever tried to use semantic search on code, you've probably hit this: the embedding says your search result is close, but it's not actually related. Or you get snippets without line numbers. Or you can't trace back why a result even came up.

We built PyCodeKG to fix that.

---

## How It Works (Plain English)

**Step 1: Build the graph**
- PyCodeKG parses your Python repo with three passes:
  1. Extract structure (modules, classes, functions, calls, imports, inheritance)
  2. Build call graph (who calls who)
  3. Walk data-flow (variable reads/writes, attribute access)
- Everything goes into SQLite. This is your ground truth.

**Step 2: Add semantics**
- Embed the code (docstrings + names) into LanceDB for fast semantic search.
- This layer is *derived*—you can rebuild it anytime.

**Step 3: Query**
- You ask something like: *"database connection setup"*
- PyCodeKG finds semantically similar functions (the embedding layer)
- Then expands outward using the graph (all callers, all dependencies, etc.)
- Returns ranked, deduplicated results with exact line numbers.

**Step 4: Extract snippets**
- PyCodeKG pulls the actual source code from your files.
- You get definition snippets + call-site snippets.
- Every snippet has line numbers. Zero guessing.

---

## Why This Matters

**For solo developers:**
- Search your own codebase without thinking. No more grepping.
- Understand code flow interactively (Streamlit web app; 3D visualizer `viz3d` is actively in development — functional but rough around the edges).

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

## The Killer Feature: `pycodekg analyze`

Honest confession: this single command is the actual reason I built PyCodeKG. I got tired of watching my LLM grep through `src/` every time I asked for a codebase analysis. So I built a proper 15-phase structural pipeline that runs in seconds and hands the LLM something it can actually reason about.

I ran it against **numpy** and **matplotlib** for fun. The reports are in `analysis/` if you want to see what the output looks like on a large, real-world codebase.

> **Note:** First-time run downloads the embedder model — be patient. Subsequent runs are fast.

```bash
pycodekg init                # downloads embedder (one-time)
pycodekg build --repo .      # build the graph
pycodekg analyze .           # the full report
```

The 15-step pipeline runs in sequence:

1. **Baseline metrics** — node/edge counts, graph shape
2. **CodeRank (global PageRank)** — structurally most important code
3. **Fan-in analysis** — what's heavily depended on (breaking-change risk)
4. **Fan-out analysis** — orchestrators and complexity hotspots
5. **Dependency analysis** — orphaned code, dead functions
6. **Pattern detection** — anti-patterns, structural red flags
7. **Module coupling** — tightly coupled pairs, import graph
8. **Critical paths** — longest call chains, bottlenecks
9. **Public API identification** — what's exposed vs. internal
10. **Docstring coverage** — by module, class, function, method
11. **Inheritance hierarchy** — depth, multiple inheritance, diamonds
12. **Generate insights** — issues + strengths synthesis
13. **Snapshot history** — metric trends across releases
14. **Structural centrality (SIR)** — bridge nodes, removal impact
15. **Concern-based ranking** — group nodes by architectural concern

Output: a Markdown report for humans + a timestamped JSON snapshot for CI gates and trend tracking. The Markdown drops straight into a Claude / ChatGPT conversation for targeted improvement suggestions. No copy-pasting grep results. No hallucinated function signatures. Every finding is traced back to a file and line number.

---

## Technical Highlights

- **Deterministic** — same codebase, same graph, always.
- **Traceable** — every result maps to a file + line number.
- **Cross-module calls** — symbol resolution handles import aliases. `from utils import helper; helper()` → finds the actual `helper` definition.
- **Caller lookup** — find every place a function is called, even through imports.
- **Multiple outputs** — JSON, Markdown, interactive web, 3D graph (actively in development), MCP server.

---

## Get Started

```bash
pip install 'pycode-kg[viz,viz3d]'   # base + Streamlit + 3D viewer

cd /path/to/your/repo
pycodekg init --repo .               # download model, build graph, install hooks, snapshot
pycodekg analyze .                   # the architectural report
```

Other useful commands:

```bash
pycodekg query "your search here"                    # hybrid semantic + structural search
pycodekg pack "authentication flow" --out ctx.md     # source-grounded snippets for LLMs
pycodekg viz                                         # Streamlit web app
pycodekg viz3d                                       # 3D graph (PyVista) — actively in development, rough around the edges
pycodekg mcp --repo .                                # MCP server for Claude / Copilot / Cline
```

---

## Repository & Docs

[**github.com/Flux-Frontiers/pycode_kg**](https://github.com/Flux-Frontiers/pycode_kg)

- Quick start guide in the README
- Full architecture & design philosophy in `/docs`
- MCP integration guide for Claude Code, GitHub Copilot, Cline, Continue
- Tests and examples in `/tests`

**License:** Elastic 2.0 (free to use, modify, distribute; no hosted service).

**Author:** Eric G. Suchanek, PhD

---

## Questions?

- How does it compare to GraphRAG? GraphRAG uses probabilistic inference. PyCodeKG uses deterministic AST parsing and structural graph traversal.
- Does it work with my IDE? Yes. MCP integration with Claude Code, GitHub Copilot, Cursor, Continue. Streamlit web app. 3D visualizer.
- Can I use this in production? Yes. It's read-only. Build the graph once, query infinite times.
- What's the license? Elastic 2.0. Free for internal use, no reselling.

Looking forward to feedback!
