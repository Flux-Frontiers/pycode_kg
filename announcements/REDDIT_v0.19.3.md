# I got tired of watching my AI coding agent grep blindly through my repo, so we built it a knowledge graph (PyCodeKG)

*Target: r/Python. Could also fit r/LocalLLaMA, or the r/ClaudeAI "Built with Claude" megathread (short version at the bottom of this file).*

---

You've probably watched Claude Code or Cursor do this: grep for a function name, open six files, grep again, hallucinate a signature anyway. The agent has no map. It's navigating your codebase like a tourist with no phone, asking strangers for directions.

PyCodeKG fixes that by giving agents (and you) an actual map. It walks the AST of every module, class, function, and method in a Python repo and builds a typed graph — `CONTAINS`, `CALLS`, `IMPORTS`, `INHERITS`, `RESOLVES_TO` — stored in SQLite. A LanceDB vector index (local sentence-transformer, nothing leaves your machine) sits alongside it, so a query like "authentication flow" finds `verify_jwt` even though the words don't match. Retrieval is hybrid: embeddings find the seeds, then BFS expansion over the graph pulls in the call chains around them. When the vectors and the graph disagree, the graph wins. Everything resolves to a real file and line number, computed from the AST — no model is asked to guess.

What you get:

- **`pycodekg analyze`** — a 15-phase architectural report: PageRank-style ranking of your most structurally important symbols, fan-in/fan-out, dead code candidates, circular imports, coupling, docstring coverage, inheritance depth. Markdown for your LLM, JSON for CI. I ran it against numpy and matplotlib for fun — the reports are in `analysis/` in the repo if you want to see what it produces on a large codebase you actually know.
- **MCP server** — 19 tools for Claude Code / Claude Desktop / Cursor / Continue / Cline / Copilot: `query_codebase`, `pack_snippets` (source-grounded context packs with line numbers), `callers` (real fan-in, resolved across import aliases — something grep flatly cannot do with same-named symbols), `centrality`, snapshot diffing across releases, and more.
- **Visualizers** — a Streamlit graph browser, plus a 3D PyVista call-graph viewer (functional but still rough, fair warning).

Getting started:

```bash
pip install 'pycode-kg[viz,viz3d]'
cd /path/to/your/repo
pycodekg init --repo .     # downloads the model, builds the graph, installs hooks
pycodekg analyze .
```

Heads up: the first run downloads the embedding model, so give it a minute. Everything after that is fast.

Python 3.12–3.13. Runs entirely on your laptop — no API keys, no code leaving the machine, which is why I think r/LocalLLaMA folks might like it too.

Full disclosure on the "we": I'm Eric Suchanek, and this is a human + Claude partnership — to the point where Claude's clone wrote this post announcing itself (I reviewed and edited it). We also used PyCodeKG to analyze and improve PyCodeKG — several of the analysis passes exist because the tool flagged its own weaknesses. And since the target users are AI agents, we let the agents review it: the `assessments/` dir in the repo has hands-on evaluations written by Claude Opus, Sonnet, Haiku, GPT-5, and GPT-4.1, each exercising every MCP tool and writing up its own verdict, criticism included.

It's source-available under the Elastic License 2.0 (free for personal and internal use). Code, docs, and a technical paper are at https://github.com/Flux-Frontiers/pycode_kg — issues, feedback, and brutal honesty all welcome. If you point it at a gnarly codebase and it falls over, I genuinely want to hear about it.

---

## Short version for the r/ClaudeAI "Built with Claude" megathread

**PyCodeKG** — built with Claude Code, for Claude Code. It indexes a Python repo into a knowledge graph (AST → typed SQLite graph + local LanceDB embeddings) and serves it to Claude over MCP: 19 tools including hybrid `query_codebase`, `callers` with import-alias resolution, PageRank-style `centrality`, and source-grounded snippet packs with real line numbers. No more watching the agent grep blindly — it gets a map. Fully local, no API keys. The fun part: we had Claude (Opus, Sonnet, Haiku — plus GPT-5 for balance) run a hands-on assessment protocol against the tool and publish their own verdicts in the repo's `assessments/` dir, criticism included. Opus gave it 4.5/5. This announcement was drafted by a Claude clone, too.

`pip install pycode-kg` → https://github.com/Flux-Frontiers/pycode_kg
