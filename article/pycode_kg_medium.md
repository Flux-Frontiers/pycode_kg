# Your Codebase Has a Shape. Most Tools Can't See It.

*How PyCodeKG builds a knowledge graph from Python source and makes it queryable by AI agents — without hallucination.*

---

There's a question every developer eventually asks about a codebase they didn't write: *where does this actually happen?*

Not "where is this function defined" — your IDE handles that. The harder question: where is the configuration loaded, and which functions downstream depend on it? Where is this API called, and what state has to be set up first? How does this class relate to the three others that seem to do similar things?

These are structural questions. They're about the shape of the system, not just the location of individual symbols. And most tools — text search, symbol lookup, even a capable LLM — give you a partial answer at best.

Text search finds strings. Symbol lookup finds definitions. LLMs give you plausible-sounding answers that may or may not reflect what the code actually does. None of them give you a reliable map.

PyCodeKG is an attempt to build that map.

---

## The Core Idea

Python's `ast` module can parse any `.py` file into a syntax tree. From that tree, you can extract every module, class, function, and method — along with the relationships between them: what contains what, what calls what, what imports what, what inherits from what.

Do that across an entire repository and you have a graph. Not a fuzzy, probabilistic graph — a deterministic one. Every node has a stable ID derived from its kind, file path, and qualified name. Every edge has a type. Call edges carry evidence: the exact line number and expression text of the call site.

That graph goes into SQLite. SQLite is the authoritative record. It doesn't drift, it doesn't hallucinate, and it doesn't require a GPU.

Then — and only then — PyCodeKG builds a semantic layer on top. Each node gets embedded using a sentence-transformer model (`all-MiniLM-L6-v2` by default, 384 dimensions). Those vectors go into LanceDB. The vector index is derived from SQLite and is fully disposable: delete it, rebuild it, swap the embedding model. The structural record doesn't change.

This separation is the whole point. Structure is ground truth. Semantics are an acceleration layer.

---

## What a Query Actually Does

When you ask PyCodeKG something like *"database connection setup"*, two things happen in sequence.

**Semantic seeding.** The query is embedded and compared against the vector index. The top-K most similar nodes come back as seed hits — these are the places in the codebase where the vocabulary most closely matches your question.

**Structural expansion.** From those seed nodes, PyCodeKG walks the graph. It follows edges — CONTAINS, CALLS, IMPORTS, INHERITS — up to a configurable number of hops. Every reachable node gets annotated with how far it is from the nearest seed and which seed it came from.

The result is ranked deterministically: closer nodes first, then by embedding distance, then by kind (functions before classes before modules). Identical inputs always produce identical outputs.

This is different from asking an LLM to describe the codebase. The LLM might give you a confident, well-written answer that describes code that doesn't exist, or conflates two different functions with similar names, or misses the actual entry point entirely. PyCodeKG gives you a list of real nodes with real file paths and real line numbers, ranked by structural and semantic relevance.

---

## Snippet Packing

The query result is useful for navigation. But often what you actually need is the source code itself — not just "here's a relevant function" but "here's what it does."

`pack()` does this. It takes the ranked, deduplicated node list and extracts source-grounded snippets: the actual lines from the file, with a configurable context window around each definition, with line numbers included. Overlapping spans in the same file are merged so you don't get the same code twice. Large definitions are capped so one enormous function doesn't swamp everything else.

The output is a Markdown document — a "context pack" — that looks like this:

```
### function — `GraphStore.expand`
- id: `fn:src/pycode_kg/store.py:GraphStore.expand`
- module: `src/pycode_kg/store.py`
- line: 187

    187: def expand(
    188:     self,
    189:     seed_ids: Set[str],
    ...
```

This is what you hand to an LLM when you want it to reason about implementation details. It's grounded. It has line numbers. It came from the actual source, not from the model's training data.

---

## The MCP Server

PyCodeKG ships a built-in Model Context Protocol server. Four tools:

- `graph_stats()` — how many nodes and edges, broken down by kind
- `query_codebase(q)` — the hybrid query, returns JSON
- `pack_snippets(q)` — the hybrid query plus snippets, returns Markdown
- `get_node(node_id)` — fetch a single node by its stable ID

Configure it in `.mcp.json` (Claude Code, Kilo Code), `.vscode/mcp.json` (GitHub Copilot), or `claude_desktop_config.json` (Claude Desktop), and any MCP-compatible agent gets direct, grounded access to the codebase graph.

The server is read-only. It can't modify the graph. It just answers questions about it.

The practical effect: an agent working on a codebase can call `graph_stats()` to orient itself, `query_codebase("authentication flow")` to find relevant nodes, and `pack_snippets("JWT validation")` to read the actual implementation — all without the agent having to guess, hallucinate, or rely on stale training data.

---

## Why Not Just Use an LLM?

You can. And for many tasks, you should. LLMs are excellent at reasoning about code once they have the right context. The problem is getting them that context reliably.

An LLM asked to describe a codebase it hasn't seen will do its best with what it knows — which is its training data, not your code. An LLM given a context window full of relevant, line-numbered source snippets will do much better. PyCodeKG is a way to fill that context window with the right material.

The other issue is auditability. When an LLM tells you "the authentication flow goes through `JWTValidator.validate`," you want to be able to verify that. With PyCodeKG, you can: the node ID is `fn:src/auth/jwt.py:JWTValidator.validate`, the line is 47, and you can look it up. When the LLM is working from a PyCodeKG snippet pack, its claims are checkable.

---

## The Architecture in Brief

Four layers, each with a single job:

**`CodeGraph`** — pure AST extraction. No I/O, no persistence. Just walks the repository and returns nodes and edges.

**`GraphStore`** — SQLite persistence and graph traversal. Stores the nodes and edges, provides BFS expansion, tracks provenance (which seed a node came from, how many hops away).

**`SemanticIndex`** — LanceDB vector index. Reads from `GraphStore`, embeds nodes, stores vectors. Fully derived and disposable.

**`PyCodeKG`** — the orchestrator. Owns all three layers with lazy initialization, coordinates the build pipeline and query pipeline, exposes the public API.

Everything is independently testable. The graph layer doesn't know about embeddings. The index layer doesn't know about the query logic. The orchestrator doesn't know about AST parsing.

---

## Getting Started

```bash
# Install with MCP server support
poetry add 'pycode-kg @ git+https://github.com/Flux-Frontiers/pycode_kg.git'

# Build the knowledge graph
poetry run pycodekg-build-sqlite  --repo .
poetry run pycodekg-build-lancedb

# Run a query
poetry run pycodekg-query --q "database connection setup"
```

Or use the Streamlit app (`pycodekg-viz`) for an interactive graph browser with point-and-click queries and snippet extraction.

For AI agent integration, the `/setup-mcp` command (available in Claude Code and Kilo Code) automates the full workflow: install, build, smoke-test, and write the config files for every agent you use.

---

## What It's Good For

**Onboarding.** New to a codebase? `graph_stats()` tells you the shape. `pack_snippets("entry points")` shows you where things start. `query_codebase("configuration loading")` traces how settings flow through the system.

**Code review.** Before reviewing a PR, query the affected modules to understand their call graph and dependencies. The context pack gives you the relevant source without having to navigate the file tree manually.

**Agent-assisted development.** Give your AI agent a PyCodeKG MCP server and it can orient itself in the codebase, find relevant implementations, and read actual source code — rather than guessing from training data.

**Documentation.** The `@doc` agent pattern: ask an agent to document a module, give it a `pack_snippets` result for that module, and it writes documentation grounded in the actual implementation rather than what it thinks the implementation probably looks like.

---

## The Honest Limitations

PyCodeKG is a static analysis tool. It sees what the AST sees. Dynamic dispatch, runtime-generated code, and heavily metaprogrammed systems will have gaps in the graph. Call edges are extracted from explicit call expressions; if you call a function through a dictionary or a decorator, that edge may not appear.

The semantic layer is only as good as the embedding model and the quality of docstrings. A codebase with no docstrings and cryptic function names will produce less useful semantic seeds than one with clear naming and documentation.

And it's Python-only. The AST approach is language-specific; extending to other languages would require new extraction passes.

---

## The Bigger Picture

The interesting thing about PyCodeKG isn't any individual component — SQLite, LanceDB, and sentence-transformers are all well-understood tools. The interesting thing is the combination: a structural record that is deterministic and auditable, augmented by a semantic layer that makes it navigable with natural language, exposed through a protocol that AI agents can use directly.

The goal isn't to replace LLMs in the development workflow. It's to give them something solid to stand on. A codebase has a shape. PyCodeKG makes that shape explicit, queryable, and grounded in the actual source.

---

*PyCodeKG is open source. Source, documentation, and installation instructions at [github.com/suchanek/pycode_kg](https://github.com/suchanek/pycode_kg).*
