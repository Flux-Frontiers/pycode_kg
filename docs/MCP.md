# PyCodeKG MCP Installation Guide

**Integrating PyCodeKG with Claude Code and Claude Desktop**

*Author: Eric G. Suchanek, PhD*

---

## Overview

PyCodeKG ships a built-in MCP server (`pycodekg mcp`) that exposes the full hybrid query and snippet-pack pipeline as structured tools consumable by any MCP-compatible AI agent — Claude Code, Claude Desktop, Cursor, Continue, or any custom agent that speaks the Model Context Protocol.

Once configured, the agent gains ten tools:

| Tool | Purpose |
|---|---|
| `graph_stats()` | Codebase size and shape — good first call |
| `query_codebase(q)` | Semantic + structural graph exploration |
| `pack_snippets(q)` | Source-grounded code snippets for implementation detail |
| `get_node(node_id, include_edges)` | Single node metadata lookup; optionally returns immediate neighborhood |
| `list_nodes(module_path, kind)` | List nodes filtered by module path prefix and/or kind |
| `callers(node_id, rel)` | Precise fan-in lookup — find all callers of a node, resolving through sym: stubs |
| `explain(node_id)` | Natural-language explanation: role, docstring, callers, callees |
| `analyze_repo()` | Full architectural analysis: complexity, coupling, coverage, orphans |
| `snapshot_list(limit, branch)` | List saved codebase snapshots in reverse chronological order |
| `snapshot_show(key)` | Full metrics for a specific snapshot (or `"latest"`) |
| `snapshot_diff(key_a, key_b)` | Compare two snapshots side-by-side with computed deltas |

---

## Quick Start (TL;DR)

```bash
# 1. Install pycode-kg (MCP server is included in the standard install)
poetry add 'pycode-kg @ git+https://github.com/Flux-Frontiers/pycode_kg.git'

# 2. Build the knowledge graph
pycodekg build-sqlite  --repo . --db .pycodekg/graph.sqlite
pycodekg build-lancedb --sqlite .pycodekg/graph.sqlite

# 3. Add per-repo config for your agent (see Section 4–6)
#    • Claude Code + Kilo Code  → .mcp.json
#    • GitHub Copilot           → .vscode/mcp.json
#    • Claude Desktop           → claude_desktop_config.json (global)

# 4. Restart your agent — the pycodekg tools are now active
```

Or use the automated setup command inside Claude Code / Kilo Code:

```
/setup-mcp
```

---

## Bootstrap: New Machine Setup

On a **brand-new machine** the Claude skill doesn't exist yet, so Claude won't know how to help you set up PyCodeKG. Install the skill first with a single command — no clone required:

```bash
curl -fsSL https://raw.githubusercontent.com/Flux-Frontiers/pycode_kg/main/scripts/install-skill.sh | bash
```

Or, if you already have the repo cloned:

```bash
bash scripts/install-skill.sh
```

This installs `~/.claude/skills/pycodekg/` so that any Claude Code session (with `skills-copilot` running) will automatically have expert PyCodeKG knowledge available. Then proceed with the normal installation steps below.

---

## Table of Contents

1. [Installation](#1-installation)
2. [Building the Knowledge Graph](#2-building-the-knowledge-graph)
3. [Smoke-Testing the Pipeline](#3-smoke-testing-the-pipeline)
4. [Configuring Claude Code / Kilo Code](#4-configuring-claude-code--kilo-code)
5. [Configuring GitHub Copilot](#5-configuring-github-copilot)
6. [Configuring Claude Desktop](#6-configuring-claude-desktop)
7. [Configuring Cline](#7-configuring-cline)
8. [Installing the PyCodeKG Skill](#8-installing-the-pycodekg-skill)
9. [Automated Setup with `/setup-mcp`](#9-automated-setup-with-setup-mcp)
10. [Claude Copilot Integration](#10-claude-copilot-integration)
11. [Available Tools Reference](#11-available-tools-reference)
12. [Query Strategy Guide](#12-query-strategy-guide)
13. [Rebuilding After Code Changes](#13-rebuilding-after-code-changes)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Installation

### 1a. Install from GitHub (recommended until PyPI release)

In the target project's directory:

```bash
# Standard install (MCP server included — no extra needed)
poetry add 'pycode-kg @ git+https://github.com/Flux-Frontiers/pycode_kg.git'

# With 3D visualizer (optional)
poetry add 'pycode-kg[viz3d] @ git+https://github.com/Flux-Frontiers/pycode_kg.git'
```

This adds the following to your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
# Standard
pycode-kg = {git = "https://github.com/Flux-Frontiers/pycode_kg.git"}

# With 3D visualizer
pycode-kg = {git = "https://github.com/Flux-Frontiers/pycode_kg.git", extras = ["viz3d"]}
```

Then run:

```bash
poetry lock && poetry install
```

### 1b. Pin to a specific commit

```toml
pycode-kg = { git = "https://github.com/Flux-Frontiers/pycode_kg.git", rev = "66d565f" }
```

### 1c. Verify the install

```bash
# Confirm the entry point is available
poetry run which pycodekg

# Confirm the mcp package is importable
poetry run python -c "import mcp; print('mcp OK')"
```

---

## 2. Building the Knowledge Graph

The MCP server is **read-only**. Two artifacts must be built before starting the server:

| Artifact | Built by | Contains |
|---|---|---|
| `.pycodekg/graph.sqlite` | `pycodekg build-sqlite` | AST-extracted nodes and edges |
| `.pycodekg/lancedb/` | `pycodekg build-lancedb` | Sentence-transformer vector embeddings |

### Step 1 — Static analysis: repo → SQLite

```bash
pycodekg build-sqlite \
  --repo /absolute/path/to/repo \
  --db   /absolute/path/to/repo/.pycodekg/graph.sqlite
```

Add `--wipe` to rebuild from scratch (safe to re-run):

```bash
pycodekg build-sqlite --repo . --db .pycodekg/graph.sqlite --wipe
```

**Output:** `OK: nodes=<N> edges=<M> db=.pycodekg/graph.sqlite`

### Step 2 — Semantic indexing: SQLite → LanceDB

> **Note:** The flag is `--sqlite`, not `--db`.

```bash
pycodekg build-lancedb \
  --sqlite /absolute/path/to/repo/.pycodekg/graph.sqlite
```

Add `--wipe` to rebuild the vector index:

```bash
pycodekg build-lancedb --sqlite .pycodekg/graph.sqlite --wipe
```

**Output:** `OK: indexed_rows=<V> dim=768 table=pycodekg_nodes lancedb_dir=.pycodekg/lancedb kinds=module,class,function,method`

Both steps are idempotent. Re-run them whenever the codebase changes significantly.

### CLI flags reference

**`pycodekg build-sqlite`**

| Flag | Required | Default | Description |
|---|---|---|---|
| `--repo` | ✓ | — | Repository root path |
| `--db` | ✓ | — | SQLite output path |
| `--wipe` | | false | Delete existing graph first |

**`pycodekg build-lancedb`**

| Flag | Required | Default | Description |
|---|---|---|---|
| `--sqlite` | ✓ | — | Path to the SQLite graph |
| `--lancedb` | | `.pycodekg/lancedb` | LanceDB output directory |
| `--table` | | `pycodekg_nodes` | LanceDB table name |
| `--model` | | `BAAI/bge-small-en-v1.5` | Sentence-transformer model |
| `--wipe` | | false | Delete existing vectors first |
| `--kinds` | | `module,class,function,method` | Node kinds to embed |
| `--batch` | | `256` | Embedding batch size |

---

## 3. Smoke-Testing the Pipeline

Before configuring any agent, verify the full pipeline works end-to-end:

```bash
# Check graph stats
poetry run python -c "
from pycode_kg import PyCodeKG
import json
kg = PyCodeKG(repo_root='.', db_path='.pycodekg/graph.sqlite', lancedb_dir='.pycodekg/lancedb')
print(json.dumps(kg.stats(), indent=2))
"

# Run a sample query
pycodekg query "module structure"
```

Expected output from `kg.stats()`:

```json
{
  "total_nodes": 412,
  "total_edges": 1087,
  "node_counts": { "module": 18, "class": 34, "function": 201, "method": 143 },
  "edge_counts": { "CONTAINS": 378, "CALLS": 512, "IMPORTS": 147, "INHERITS": 50 },
  "db_path": ".pycodekg/graph.sqlite"
}
```

If this succeeds, the MCP server will work correctly.

---

## 4. Configuring Claude Code / Kilo Code

Both **Claude Code** and **Kilo Code** read MCP servers from **`.mcp.json`** in the project root — this is the canonical per-project MCP config for `pycodekg`.

> **CRITICAL: Absolute Paths Required**
>
> The `.mcp.json` configuration must use absolute paths for all commands and arguments. Relative paths will not work because MCP clients do not inherit your shell's working directory. This applies to:
> - `command` — The path to the `pycodekg-mcp` binary
> - `--repo` — Full path to the repository root
> - `--db`, `--lancedb` — Full paths to graph and index locations
>
> Once `.mcp.json` is created, it should be frozen and not hand-edited. Use `/setup-mcp` to update it.

> **Per-repo only.** Do NOT add `pycodekg` to any global settings file (Kilo Code's `mcp_settings.json` or Claude Code's `~/.claude/settings.json`). Global files are shared across all windows — hardcoded paths will point every window to the same repo.

> **Note:** If your project uses Claude Copilot, the copilot servers (`copilot-memory`, `skills-copilot`, `task-copilot`) live in `.claude/claude_code_config.json` — separate from `pycodekg`. See [Section 10](#10-claude-copilot-integration) for the full layout.

### 4a. Create or update `.mcp.json`

```json
{
  "mcpServers": {
    "pycodekg": {
      "command": "pycodekg-mcp",
      "args": ["--repo", "/absolute/path/to/repo"]
    }
  }
}
```

> **Always use absolute paths.** MCP clients do not inherit your shell's working directory.
>
> `--db` and `--lancedb` are optional — they default to `.pycodekg/graph.sqlite` and `.pycodekg/lancedb` relative to `--repo`.

### 4b. Merging with an existing `.mcp.json`

If you already have other MCP servers in `.mcp.json`, add `pycodekg` to the existing `mcpServers` object — do not overwrite other entries:

```json
{
  "mcpServers": {
    "other-server": { "...": "existing entry" },
    "pycodekg": {
      "command": "pycodekg-mcp",
      "args": ["--repo", "/absolute/path/to/repo"]
    }
  }
}
```

### 4c. Activate

Restart Claude Code / reload the Kilo Code MCP panel. The `pycodekg` server will appear in the MCP tools list.

---

## 5. Configuring GitHub Copilot

GitHub Copilot in VS Code reads MCP servers from `.vscode/mcp.json` in the **workspace root**. Note the key differences from `.mcp.json`:

- Uses `"servers"` (not `"mcpServers"`)
- Requires `"type": "stdio"` for local process servers
- Can be committed to source control to share the config with your team

> **Absolute paths required.** All paths in `.vscode/mcp.json` must be fully qualified (e.g., `/Users/you/repos/my-project`), not relative paths.

### 5a. Create or update `.vscode/mcp.json`

```json
{
  "servers": {
    "pycodekg": {
      "type": "stdio",
      "command": "pycodekg",
      "args": [
        "mcp",
        "--repo", "/absolute/path/to/repo",
        "--db",   "/absolute/path/to/repo/.pycodekg/graph.sqlite"
      ],
      "env": {
        "POETRY_VIRTUALENVS_IN_PROJECT": "false"
      }
    }
  }
}
```

### 5b. Activate

After saving, VS Code will display a prompt to **Trust** the MCP server — click Trust to activate it. The `pycodekg` tools will then be available in GitHub Copilot Chat.

---

## 6. Configuring Claude Desktop

Claude Desktop does not have Poetry on its PATH, so you must use the **absolute path to the venv binary**.

> **All paths must be absolute.** The venv binary path, `--repo`, `--db`, and `--lancedb` arguments must all be fully qualified. Claude Desktop cannot resolve relative paths.

### 6a. Find the venv binary path

```bash
# In the project directory
poetry env info --path
# → /Users/you/Library/Caches/pypoetry/virtualenvs/my-project-abc123-py3.11
```

The `pycodekg` binary is at `<venv_path>/bin/pycodekg`.

### 6b. Edit `claude_desktop_config.json`

| OS | Config path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

Add the `pycodekg` entry:

```json
{
  "mcpServers": {
    "pycodekg": {
      "command": "/Users/you/Library/Caches/pypoetry/virtualenvs/my-project-abc123-py3.11/bin/pycodekg",
      "args": [
        "mcp",
        "--repo", "/absolute/path/to/repo",
        "--db",   "/absolute/path/to/repo/.pycodekg/graph.sqlite"
      ]
    }
  }
}
```

### 6c. Activate

Restart Claude Desktop. The `pycodekg` server will appear in the tool panel.

---

## 7. Configuring Cline

> ⚠️ **Cline does NOT support per-repo MCP config.** Its settings file is global and shared across all VS Code windows.

### Options

**Option A — Use Kilo Code instead** (recommended): Kilo Code is a drop-in replacement for Cline that supports per-repo `.mcp.json`. Switch to Kilo Code and follow Section 4.

**Option B — Named entry per repo**: Add a uniquely-named entry to Cline's global settings file and toggle it via the Cline MCP panel when switching repos.

Config path (macOS):
```
~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

Add a repo-specific named entry:

```json
{
  "mcpServers": {
    "pycodekg-myproject": {
      "command": "/path/to/venv/bin/pycodekg",
      "args": [
        "mcp",
        "--repo", "/absolute/path/to/myproject",
        "--db",   "/absolute/path/to/myproject/.pycodekg/graph.sqlite"
      ]
    }
  }
}
```

Use the absolute venv binary path (from `poetry env info --path`) — Cline does not have Poetry on its PATH.

---

## 8. Installing the PyCodeKG Skill

The PyCodeKG skill gives AI agents expert knowledge about PyCodeKG installation and usage. It must be installed to the correct directory for each agent type.

| Agent | Skill directory |
|---|---|
| **Claude Code** | `~/.claude/skills/pycodekg/` (served by `skills-copilot` MCP server) |
| **Kilo Code** | `~/.kilocode/skills/pycodekg/` |
| **Other agents** | `~/.agents/skills/pycodekg/` |

### Install to all locations at once (recommended)

```bash
# From the pycode_kg repo root
bash scripts/install-skill.sh

# Or without cloning (one-liner)
curl -fsSL https://raw.githubusercontent.com/Flux-Frontiers/pycode_kg/main/scripts/install-skill.sh | bash
```

The script installs `SKILL.md` and `references/installation.md` to all three skill directories and generates the appropriate MCP config files in the current project directory:
- `.mcp.json` (Claude Code + Kilo Code — contains the `pycodekg` entry)
- `.vscode/mcp.json` (GitHub Copilot)

### Manual install

```bash
# Claude Code
mkdir -p ~/.claude/skills/pycodekg/references
cp .claude/skills/pycodekg/SKILL.md ~/.claude/skills/pycodekg/SKILL.md
cp .claude/skills/pycodekg/references/installation.md ~/.claude/skills/pycodekg/references/installation.md

# Kilo Code
mkdir -p ~/.kilocode/skills/pycodekg/references
cp .claude/skills/pycodekg/SKILL.md ~/.kilocode/skills/pycodekg/SKILL.md
cp .claude/skills/pycodekg/references/installation.md ~/.kilocode/skills/pycodekg/references/installation.md
```

After installing for Kilo Code, reload VS Code (`Cmd+Shift+P` → **Developer: Reload Window**) to pick up the new skill.

---

## 9. Automated Setup with `/setup-mcp`


If your project uses **Claude Copilot**, the `/setup-mcp` command automates the entire installation and configuration process.

### Usage

```
/setup-mcp                        # Interactive — prompts for repo path
/setup-mcp /path/to/repo          # Non-interactive — uses provided path
```

### What it does

The command runs six steps automatically:

| Step | Action |
|---|---|
| 0 | Resolves the target repository path and verifies Python files exist |
| 1 | Verifies `pycodekg mcp` is installed; installs `pycode-kg` if missing |
| 2 | Builds the SQLite knowledge graph (asks before wiping existing data) |
| 3 | Builds the LanceDB vector index (asks before wiping existing data) |
| 4 | Smoke-tests the full query pipeline |
| 5 | Writes/updates MCP configs: `.mcp.json` (Claude Code + Kilo Code), `.vscode/mcp.json` (GitHub Copilot), `claude_desktop_config.json` (Claude Desktop) |
| 6 | Prints a final summary with node/edge/vector counts and next steps |

### Example output

```
✓ Repository indexed:    /path/to/repo
✓ SQLite graph:          /path/to/repo/.pycodekg/graph.sqlite  (412 nodes, 1087 edges)
✓ LanceDB index:         /path/to/repo/.pycodekg/lancedb  (378 vectors)
✓ Smoke test:            passed
✓ Claude Code config:    /path/to/repo/.mcp.json
✓ Claude Desktop config: ~/Library/Application Support/Claude/claude_desktop_config.json

Restart Claude Code / Claude Desktop to activate the pycodekg MCP server.

Available tools once active:
  • graph_stats()                      — codebase size and shape
  • query_codebase(q)                  — semantic + structural exploration
  • pack_snippets(q)                   — source-grounded code snippets
  • get_node(node_id, include_edges)   — single node metadata lookup + optional neighborhood
  • list_nodes(module_path, kind)      — list nodes in a module
  • callers(node_id)                   — fan-in lookup resolving cross-module stubs
  • explain(node_id)                   — natural-language explanation of a code node
  • analyze_repo()                     — full architectural analysis
  • snapshot_list()                  — list temporal metric snapshots
  • snapshot_show(key)               — full snapshot details
  • snapshot_diff(key_a, key_b)      — compare two snapshots

Suggested first query after restart:
  graph_stats()
```

---

## 10. Claude Copilot Integration

If your project uses [Claude Copilot](https://github.com/Everyone-Needs-A-Copilot/claude-copilot), PyCodeKG integrates naturally with the agent framework.

### Setting up Claude Copilot in a new project

Claude Copilot provides the agent infrastructure (Memory Copilot, Task Copilot, Skills, Agents). To set it up alongside PyCodeKG:

```
/setup-project          # Initialize Claude Copilot
/setup-mcp              # Then set up PyCodeKG MCP
```

### Project structure with both installed

```
your-project/
├── .mcp.json                    ← MCP server config (pycodekg — read by Claude Code + Kilo Code)
├── .claude/
│   ├── claude_code_config.json  ← Claude Code MCP config (copilot servers only)
│   ├── settings.local.json      ← Claude Code settings
│   ├── agents/                  ← Agent definitions (ta, me, qa, doc, etc.)
│   ├── commands/
│   │   ├── protocol.md          ← /protocol command
│   │   ├── continue.md          ← /continue command
│   │   └── setup-mcp.md         ← /setup-mcp command
│   └── skills/                  ← Local skills (empty until populated)
├── .pycodekg/                     ← Knowledge graph + index (gitignored)
│   ├── graph.sqlite
│   └── lancedb/
```

### Recommended `.mcp.json`

Contains `pycodekg` — read by both Claude Code and Kilo Code:

```json
{
  "mcpServers": {
    "pycodekg": {
      "command": "pycodekg-mcp",
      "args": ["--repo", "/absolute/path/to/your-project"]
    }
  }
}
```

### Recommended `.claude/claude_code_config.json` with Copilot stack

Contains the Claude Copilot servers (Claude Code-specific — Kilo Code does not read this file):

```json
{
  "mcpServers": {
    "copilot-memory": {
      "command": "node",
      "args": ["/Users/you/.claude/copilot/mcp-servers/copilot-memory/dist/index.js"],
      "env": {
        "MEMORY_PATH": "/Users/you/.claude/memory",
        "WORKSPACE_ID": "your-project"
      }
    },
    "skills-copilot": {
      "command": "node",
      "args": ["/Users/you/.claude/copilot/mcp-servers/skills-copilot/dist/index.js"],
      "env": {
        "LOCAL_SKILLS_PATH": "./.claude/skills"
      }
    },
    "task-copilot": {
      "command": "node",
      "args": ["/Users/you/.claude/copilot/mcp-servers/task-copilot/dist/index.js"],
      "env": {
        "TASK_DB_PATH": "/Users/you/.claude/tasks",
        "WORKSPACE_ID": "your-project"
      }
    }
  }
}
```

### Using PyCodeKG tools within the Agent-First Protocol

When working under `/protocol`, agents can call PyCodeKG tools directly. The recommended workflow:

```
1. Start session:
   /protocol

2. Agent orientation (agent calls automatically):
   graph_stats()                          → understand codebase shape

3. Investigation (agent calls):
   query_codebase("authentication flow")  → find relevant nodes
   pack_snippets("JWT validation logic")  → read implementation

4. Implementation:
   @agent-me implements changes with full source context from pack_snippets
```

The `@agent-doc` agent is particularly well-suited to use `pack_snippets` when generating documentation — it gets accurate source-grounded snippets rather than hallucinating implementations.

---

## 11. Available Tools Reference

### `graph_stats()`

Return node and edge counts broken down by kind and relation.

**When to use:** First call in any session — understand the codebase size and shape before querying.

**Parameters:** None.

**Returns:**

```json
{
  "total_nodes": 412,
  "total_edges": 1087,
  "node_counts": {
    "module": 18, "class": 34, "function": 201, "method": 143, "symbol": 16
  },
  "edge_counts": {
    "CONTAINS": 378, "CALLS": 512, "IMPORTS": 147, "INHERITS": 50
  },
  "db_path": ".pycodekg/graph.sqlite"
}
```

---

### `query_codebase(q, k, hop, rels, include_symbols, max_nodes, min_score, max_per_module)`

Hybrid semantic + structural query. Returns ranked nodes and edges as JSON.

**When to use:** Exploring the graph — finding what classes, functions, and modules are relevant to a topic, understanding call relationships, tracing imports.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | `str` | — | Natural-language query |
| `k` | `int` | `8` | Semantic seed count (top-K from vector search) |
| `hop` | `int` | `1` | Graph expansion hops from each seed |
| `rels` | `str` | `"CONTAINS,CALLS,IMPORTS,INHERITS"` | Comma-separated edge types to follow |
| `include_symbols` | `bool` | `false` | Include low-level `sym:` nodes |
| `max_nodes` | `int` | `25` | Maximum nodes to return |
| `min_score` | `float` | `0.0` | Minimum seed score (`score = 1 - distance`, clamped to `[0,1]`) |
| `max_per_module` | `int` | `0` | Maximum returned nodes per module (`0` disables the cap) |

**Returns:** JSON with keys: `query`, `seeds`, `expanded_nodes`, `returned_nodes`, `hop`, `rels`, `nodes`, `edges`.

---

### `pack_snippets(q, k, hop, rels, include_symbols, context, max_lines, max_nodes, min_score, max_per_module)`

Hybrid query + source-grounded snippet extraction. Returns a Markdown context pack.

**When to use:** Any time you need to read actual source code — understanding an implementation, debugging, writing tests, reviewing logic. **Prefer this over `query_codebase` when implementation details matter.**

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | `str` | — | Natural-language query |
| `k` | `int` | `8` | Semantic seed count |
| `hop` | `int` | `1` | Graph expansion hops |
| `rels` | `str` | `"CONTAINS,CALLS,IMPORTS,INHERITS"` | Edge types to follow |
| `include_symbols` | `bool` | `false` | Include symbol nodes |
| `context` | `int` | `5` | Extra context lines around each definition |
| `max_lines` | `int` | `160` | Maximum lines per snippet block |
| `max_nodes` | `int` | `50` | Maximum nodes in the pack |
| `min_score` | `float` | `0.0` | Minimum seed score (`score = 1 - distance`, clamped to `[0,1]`) |
| `max_per_module` | `int` | `0` | Maximum returned nodes per module (`0` disables the cap) |

**Returns:** Markdown string with ranked, deduplicated code snippets and line numbers.

---

### `get_node(node_id, include_edges)`

Fetch a single node by its stable ID, optionally including its immediate neighborhood.

**When to use:** You have a node ID from a previous query result and want its full metadata. Pass `include_edges=True` to get outgoing edges and incoming callers in one call, avoiding a separate `callers()` round-trip.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `node_id` | `str` | — | Stable node ID, e.g. `fn:src/auth/jwt.py:JWTValidator.validate` |
| `include_edges` | `bool` | `false` | If `true`, attach `outgoing_edges` (by relation type) and `incoming_calls` to the response |

**Node ID format:** `<kind>:<module_path>:<qualname>`

| Prefix | Kind |
|---|---|
| `mod:` | module |
| `cls:` | class |
| `fn:` | function / method |
| `sym:` | unresolved external symbol |

**Returns:** JSON object with all node fields, or `{"error": "Node not found: '...'"}`.\
When `include_edges=True`: also includes `outgoing_edges` (dict keyed by relation type) and `incoming_calls` (list of caller node dicts).

---

### `list_nodes(module_path, kind)`

List nodes filtered by module path prefix and/or kind.

**When to use:** Enumerating the contents (classes, functions) of a specific module before inspecting individual nodes with `get_node`.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `module_path` | `str` | `""` | Module path prefix filter |
| `kind` | `str` | `""` | Node kind filter (e.g., `class`, `function`) |

**Returns:** JSON array of matching node dicts.

---

### `callers(node_id, rel)`

Find all callers of a specific node by inverting a relation — fan-in analysis.

**When to use:** Finding all callers of a specific function/method/class — fan-in analysis. More precise than `query_codebase` for this use case because it resolves cross-module callers through `sym:` import stubs.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `node_id` | `str` | — | Stable node ID, e.g. `fn:src/auth/jwt.py:JWTValidator.validate` |
| `rel` | `str` | `"CALLS"` | Relation type to invert |

**Returns:** JSON with `node_id`, `rel`, `caller_count`, `callers` (list of node dicts).

**Example return shape:**

```json
{
  "node_id": "fn:src/pycode_kg/store.py:GraphStore.expand",
  "rel": "CALLS",
  "caller_count": 7,
  "callers": [
    { "id": "m:src/pycode_kg/kg.py:PyCodeKG.query", "kind": "method", ... },
    ...
  ]
}
```

> **Note:** `sym:` nodes are resolved automatically — callers from other modules that import the target function are included even when they reference it via an alias.

---

### `explain(node_id)`

Return a natural-language Markdown explanation of a single code node.

**When to use:** You want to understand what a specific function, method, or class does — its role, who calls it, what it calls — without reading the raw source. Use as the first step when a user asks about a specific node before reaching for `pack_snippets`.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `node_id` | `str` | Stable node ID, e.g. `fn:src/pycode_kg/store.py:GraphStore.expand` |

**Returns:** Markdown report with: kind and qualified name, module path and line range, full docstring, list of callers (top 10), list of callees, and a role assessment (high-value / utility / orphaned) based on call count.

---

### `analyze_repo()`

Run a full nine-phase architectural analysis of the entire codebase.

**When to use:** When you want a comprehensive health check or architectural overview — complexity hotspots, high fan-out functions, module coupling, circular dependencies, critical call paths, public API surface, docstring coverage, code quality issues, and orphaned code.

**Parameters:** None.

**Returns:** Structured Markdown with sections for: baseline metrics, complexity hotspots, high fan-out functions, module architecture, critical paths, public API surface, docstring coverage, issues and strengths.

---

### `snapshot_list(limit, branch)`

List saved temporal snapshots of codebase metrics in reverse chronological order.

**When to use:** Tracking how the codebase has grown over time — node/edge counts, docstring coverage changes, critical issue trends. Returns the `key` values needed for `snapshot_show` and `snapshot_diff`.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | `int` | `10` | Maximum snapshots to return; pass `0` for all |
| `branch` | `str` | `""` | Filter to snapshots from a specific branch; omit or pass `""` for all branches |

**Returns:** JSON array of snapshot metadata (key, branch, timestamp, version, key metrics, deltas vs. previous).

---

### `snapshot_show(key)`

Show full details of a specific codebase metrics snapshot.

**When to use:** Inspecting the state of the codebase at a specific snapshot — full node/edge counts, docstring coverage, complexity hotspots, and deltas vs. both the previous and baseline snapshots.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `key` | `str` | `"latest"` | Snapshot key — tree hash or `"latest"` for the most recent |

**Returns:** JSON object with full `SnapshotMetrics`, top complexity hotspots, and deltas vs. previous and baseline.

Legacy note: if an older snapshot file does not contain persisted deltas, PyCodeKG backfills `vs_previous` and `vs_baseline` from manifest chronology at load time.

---

### `snapshot_diff(key_a, key_b)`

Compare two codebase metric snapshots side-by-side.

**When to use:** Quantifying the impact of a refactor, release, or sprint — how many nodes were added, did coverage improve, did critical issues increase?

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `key_a` | `str` | First (older) snapshot key (tree hash) |
| `key_b` | `str` | Second (newer) snapshot key (tree hash) |

**Returns:** JSON with keys `a` (metrics for key_a), `b` (metrics for key_b), and `delta` (b − a) for nodes, edges, coverage, and critical issues.

**Typical workflow:**
```
1. snapshot_list()                         → discover available snapshot keys
2. snapshot_diff("abc1234", "def5678")     → compare two points in time
```

---

## 12. Query Strategy Guide

### Choosing `k` and `hop`

| Goal | Recommended settings |
|---|---|
| Narrow, precise lookup | `k=4, hop=0` — seeds only, no expansion |
| Standard exploration | `k=8, hop=1` — default; good for most queries |
| Broad context sweep | `k=12, hop=2` — pulls in more of the call graph |
| Deep dependency trace | `k=8, hop=2, rels="CALLS,IMPORTS"` — follow execution paths |

Higher `hop` values expand the result set geometrically. Use `max_nodes` in `pack_snippets` to keep output manageable.

### Choosing `rels`

| Relation | Meaning | When to include |
|---|---|---|
| `CONTAINS` | Module/class contains a definition | Almost always — provides structural context |
| `CALLS` | Function A calls function B | Tracing execution flow, finding callers/callees |
| `IMPORTS` | Module A imports from module B | Dependency analysis |
| `INHERITS` | Class A inherits from class B | OOP hierarchy exploration |

### Typical agent workflow

```
1. graph_stats()
   → understand codebase size and shape

2. query_codebase("authentication flow", k=8, hop=1)
   → identify relevant classes and functions, note their IDs

3. explain("cls:src/auth/jwt.py:JWTValidator")
   → natural-language orientation before reading source

4. pack_snippets("JWT token validation", k=6, hop=1)
   → read the actual implementation

5. get_node("fn:src/auth/jwt.py:JWTValidator.validate", include_edges=True)
   → fetch node metadata + outgoing edges + incoming callers in one call

6. pack_snippets("JWT token validation error handling", k=4, hop=2, rels="CALLS")
   → follow the call graph deeper into error paths

7. snapshot_list()
   → review how the codebase has evolved over time
   snapshot_diff("abc1234", "def5678")
   → compare metrics between two commits
```

---

## 13. Rebuilding After Code Changes

When the codebase changes, rebuild both artifacts (safe to re-run, idempotent):

```bash
pycodekg build-sqlite  --repo . --db .pycodekg/graph.sqlite --wipe
pycodekg build-lancedb --sqlite .pycodekg/graph.sqlite --wipe
```

The `.mcp.json` entry does not need to change after rebuilds — it points to the same file paths.

### Gitignore recommendations

Add this to `.gitignore` to avoid committing large binary artifacts:

```gitignore
.pycodekg/
```

This ignores the SQLite graph and LanceDB vector index — both are transient artifacts. Snapshots in `.pycodekg/snapshots/` are tracked in git and committed atomically by the pre-commit hook.

---

## 14. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ERROR: 'mcp' package not found` | Package not installed correctly | `poetry add 'pycode-kg @ git+https://github.com/Flux-Frontiers/pycode_kg.git'` |
| `WARNING: SQLite database not found` | Graph not built yet | Run `pycodekg build-sqlite` then `pycodekg build-lancedb` |
| `pycodekg build-lancedb: error: the following arguments are required: --sqlite` | Wrong flag name | Use `--sqlite`, not `--db`, for the lancedb builder |
| Empty results from `query_codebase` | LanceDB index missing or stale | Run `pycodekg build-lancedb --wipe` |
| Node IDs in results don't resolve with `get_node` | Graph rebuilt since last query | Rebuild both SQLite and LanceDB |
| `RuntimeError: PyCodeKG not initialised` | Server called without `main()` | Always start via `pycodekg mcp` CLI |
| Snippets show wrong line numbers | Source files changed since build | Rebuild with `pycodekg build-sqlite --wipe` |
| MCP server not appearing in Claude Code | `.mcp.json` not in project root, or paths are relative | Verify `.mcp.json` uses absolute paths: `command`, `--repo`, `--db`, `--lancedb` must all be fully qualified. Restart Claude Code. |
| MCP server not appearing in Claude Desktop | Wrong binary path or paths are relative | Use `poetry env info --path` to find venv; all paths in config must be absolute (venv binary, `--repo`, `--db`, `--lancedb`). |
| `pycodekg` command not found | Package not installed or venv not active | `poetry install` or use absolute venv path from `poetry env info --path` |
| MCP config not being applied | `.mcp.json` or `.vscode/mcp.json` edited by hand | Use `/setup-mcp` to regenerate configs automatically with correct absolute paths. Manual edits may introduce typos or relative paths. |

---

## Summary

| Concern | Answer |
|---|---|
| What does the MCP server expose? | 11 tools: `graph_stats`, `query_codebase`, `pack_snippets`, `get_node`, `list_nodes`, `callers`, `explain`, `analyze_repo`, `snapshot_list`, `snapshot_show`, `snapshot_diff` |
| What must exist before starting? | `.pycodekg/graph.sqlite` + `.pycodekg/lancedb/` directory |
| How do I build those? | `pycodekg build-sqlite` then `pycodekg build-lancedb --sqlite ...` |
| Is the server stateful? | Yes — one `PyCodeKG` instance per server process |
| Can it modify the graph? | No — strictly read-only |
| What transport should I use? | `stdio` for Claude Code / Claude Desktop; `sse` for HTTP clients |
| Which tool should I call first? | `graph_stats()` for orientation |
| How do I automate setup? | `/setup-mcp` command (requires Claude Copilot) |
