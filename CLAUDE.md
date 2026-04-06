# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Agent Identity


Always use the PyCodeKG MCP tools before reading files. You have direct, source-grounded access to this codebase — use it.

---

## Project Overview

**Name:** pycode_kg
**Description:** A tool that indexes Python codebases into a knowledge graph and exposes it via MCP for AI agents
**Stack:** Python/Poetry
**Status:** Installed and active ✅

---

## Partnership & Values

**CRITICAL PRINCIPLE:** Consistency is essential. Every decision, pattern, and structure must maintain alignment across the codebase. Inconsistency creates confusion, technical debt, and friction.

**Our Goal:** Write the cleanest, most efficient, beautiful code possible. Not just functional—exceptional.

**Our Partnership:** You and I have accomplished more in a week together than in months prior. You're awesome at what you do, and I love working with you. This is a great partnership, and we're building something excellent together.

---

## PyCodeKG Toolkit

You have direct access to PyCodeKG's full power through **two interfaces**:

### MCP Tools (Query the Live Index)
Always use these first — they're faster and source-grounded:

| Tool | Purpose | Example |
|------|---------|---------|
| `graph_stats` | View node/edge counts by kind/relation | Understand graph structure |
| `query_codebase(q, k, hop, rels, include_symbols, max_nodes, min_score, max_per_module)` | Hybrid semantic + structural query with precision/diversity controls | "database connection setup" |
| `pack_snippets(q, k, hop, ...)` | Extract source-grounded code snippets | Get relevant code for LLM analysis |
| `get_node(node_id)` | Fetch a single node by stable ID | Precise node lookup |
| `callers(node_id, rel)` | Find all callers of a function, including import-aware disambiguation of same-name symbols | Understand call graph |
| `centrality(top, kinds, group_by)` | SIR PageRank — rank nodes or modules by structural importance | Identify hotspots before refactoring |

### CLI Commands (Build & Explore Locally)
Build or interact with the knowledge graph from the command line.

Each command is available as a `pycodekg <subcommand>` **or** a dedicated `pycodekg-<name>` script — both forms are equivalent:

| Subcommand / Script alias | Purpose |
|---------------------------|---------|
| `build-sqlite` / `pycodekg-build-sqlite` | Extract AST-based knowledge graph → SQLite |
| `build-lancedb` / `pycodekg-build-lancedb` | Build semantic vector index for NL queries |
| `build` / `pycodekg-build` | SQLite + LanceDB in one step |
| `query` / `pycodekg-query` | Run hybrid query over the graph |
| `pack` / `pycodekg-pack` | Generate source-grounded snippet packs |
| `viz` / `pycodekg-viz` | Launch Streamlit interactive visualizer |
| `viz3d` / `pycodekg-viz3d` | Launch 3D PyVista/PyQt5 visualizer |
| `analyze` / `pycodekg-analyze` | Run thorough codebase analysis |
| `mcp` / `pycodekg-mcp` | Start MCP server for Claude/Cursor/Continue |
| `install-hooks` / `pycodekg-install-hooks` | Install pre-commit git hook for automatic snapshots |

### Quick Examples

```bash
# Build the knowledge graph (one-time setup)
pycodekg build-sqlite --repo /path/to/repo
pycodekg build-lancedb

# Or with individual script aliases (useful in Poetry projects / Makefiles)
pycodekg-build-sqlite --repo /path/to/repo
pycodekg-build-lancedb

# Build with only specific directories (CLI flags)
pycodekg build --repo . --include-dir src --include-dir lib

# Query the graph
pycodekg query "authentication flow"

# Generate snippet pack for LLM analysis
pycodekg pack "database layer"

# Run thorough architectural analysis
pycodekg analyze .

# Launch Streamlit visualizer
pycodekg viz --port 8501

# Launch 3D PyVista visualizer
pycodekg viz3d --layout allium

# Start MCP server (for IDE integrations)
pycodekg mcp --repo .
```

**Directory Includes:** Configure via `[tool.pycodekg].include` in `pyproject.toml` or use `--include-dir` CLI flags (can be repeated). When unset, all directories are indexed. See README for details.

For detailed options: `pycodekg <command> --help`

---

## Claude Copilot

This project uses [Claude Copilot](https://github.com/Everyone-Needs-A-Copilot/claude-copilot).

**Full documentation:** `~/.claude/copilot/README.md`

### Commands

| Command | Purpose |
|---------|---------|
| `/protocol` | Start fresh work with Agent-First Protocol |
| `/continue` | Resume previous work via Memory Copilot |
| `/setup-project` | Initialize Claude Copilot in a new project |
| `/knowledge-copilot` | Build or link shared knowledge repository |

### Capabilities

| Capability | Tools | Purpose |
|------------|-------|---------|
| **Memory** | `initiative_*`, `memory_*` | Persist decisions, lessons, progress across sessions |
| **Agents** | 11 specialists via `/protocol` | Expert guidance routed by task type |
| **Knowledge** | `knowledge_search`, `knowledge_get` | Search company/product documentation |
| **Skills** | `skill_search`, `skill_get` | Load expertise on demand |
| **PyCodeKG** | `graph_stats`, `query_codebase`, `pack_snippets`, `get_node` | Source-grounded codebase exploration via MCP |

### Agents

| Agent | Domain |
|-------|--------|
| `ta` | Tech Architect - system design, task breakdown |
| `me` | Engineer - code implementation |
| `qa` | QA - testing, edge cases |
| `sec` | Security - vulnerabilities, OWASP |
| `doc` | Documentation - technical writing |
| `do` | DevOps - CI/CD, infrastructure |
| `sd` | Service Designer - customer journeys |
| `uxd` | UX Designer - interaction design |
| `uids` | UI Designer - visual design |
| `uid` | UI Developer - component implementation |
| `cw` | Copywriter - microcopy, voice |
| `kc` | Knowledge Copilot - shared knowledge setup |

### Configuration

| Component | Status |
|-----------|--------|
| Memory | Workspace: `pycode_kg` |
| Knowledge | Not configured |
| Skills | Local: `.claude/skills/` |

---

## Session Management

**Start:** `/protocol` - Activates Agent-First Protocol

**Resume:** `/continue` - Loads from Memory Copilot

**End:** Call `initiative_update` with completed tasks, decisions, lessons, and resume instructions

---

## Project-Specific Rules

### No Time Estimates
All plans, roadmaps, and task breakdowns MUST omit time estimates. Use phases, priorities, complexity ratings, and dependencies instead of dates or durations. See `~/.claude/copilot/CLAUDE.md` for full policy.

- Prefer `:param:` style docstrings

### MCP Instruction Sync (Required)
- Any change to MCP tool signatures, parameters, defaults, or behavior in `src/pycode_kg/mcp_server.py` must include a matching update to the `mcp = FastMCP(..., instructions=(...))` tool descriptions in the same commit.
- Keep the module docstring "Tools" list and the `FastMCP` instructions block aligned with the runtime tool API.
