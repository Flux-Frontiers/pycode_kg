# Installation & Configuration

Full installation options, manual MCP setup, and CLI reference for PyCodeKG.

---

## One-Line Installer (recommended for new repos)

Run from within the repo you want to index:

```bash
curl -fsSL https://raw.githubusercontent.com/Flux-Frontiers/pycode_kg/main/scripts/install-skill.sh | bash
```

This sets up everything end-to-end:

1. Installs SKILL.md reference files for Claude Code, Kilo Code, and other agents
2. Installs Claude Code slash commands (`/pycodekg`, `/setup-mcp`)
3. Installs the `pycode-kg` package if not already present
4. Builds the SQLite knowledge graph and LanceDB semantic index
5. Writes MCP configuration for Claude Code, Kilo Code, GitHub Copilot, and Cline

```bash
# Preview without making changes
curl -fsSL https://raw.githubusercontent.com/Flux-Frontiers/pycode_kg/main/scripts/install-skill.sh | bash -s -- --dry-run

# Claude Code and GitHub Copilot only
curl -fsSL https://raw.githubusercontent.com/Flux-Frontiers/pycode_kg/main/scripts/install-skill.sh | bash -s -- --providers claude,copilot
```

After the script completes, restart your AI agent to activate the MCP server.

---

## Requirements

Python ≥ 3.12, < 3.14

---

## Install via pip

```bash
# Core install (SQLite + LanceDB + MCP server)
pip install pycode-kg

# With Streamlit web visualizer
pip install 'pycode-kg[viz]'

# With 3D visualizer extras (PyVista, PyQt5 — heavy dependencies)
pip install 'pycode-kg[viz3d]'

# Both visualizers
pip install 'pycode-kg[viz,viz3d]'
```

---

## Install via Poetry

```bash
# Core
poetry add pycode-kg

# With Streamlit visualizer
poetry add 'pycode-kg[viz]'

# With 3D visualizer
poetry add 'pycode-kg[viz3d]'
```

Or in `pyproject.toml`:

```toml
[tool.poetry.dependencies]
# Core
pycode-kg = ">=0.18.0"

# With Streamlit visualizer
pycode-kg = {version = ">=0.18.0", extras = ["viz"]}

# With 3D visualizer
pycode-kg = {version = ">=0.18.0", extras = ["viz3d"]}
```

> **PyCodeKG developers:** Use `poetry install --with dev` for the full dev environment. Add `-E viz` or `-E viz3d` for visualizer extras. The `extras` mechanism above is for *consumers* of the package.

---

## Development Setup

```bash
git clone https://github.com/Flux-Frontiers/pycode_kg.git
cd pycode_kg
poetry install --with dev          # core + dev
poetry install --with dev -E viz   # + Streamlit visualizer
poetry install --with dev -E viz3d # + 3D visualizer
poetry install --all-extras --with dev  # everything
```

Run the test suite:

```bash
poetry run pytest
```

---

## CLI Reference

All commands are available as `pycodekg <subcommand>` or a dedicated `pycodekg-<name>` script. Both forms are equivalent.

| Script alias | Equivalent subcommand |
|---|---|
| `pycodekg-init` | `pycodekg init` |
| `pycodekg-build-sqlite` | `pycodekg build-sqlite` |
| `pycodekg-build-lancedb` | `pycodekg build-lancedb` |
| `pycodekg-build` | `pycodekg build` |
| `pycodekg-query` | `pycodekg query` |
| `pycodekg-pack` | `pycodekg pack` |
| `pycodekg-analyze` | `pycodekg analyze` |
| `pycodekg-architecture` | `pycodekg architecture` |
| `pycodekg-viz` | `pycodekg viz` |
| `pycodekg-viz3d` | `pycodekg viz3d` |
| `pycodekg-viz-timeline` | `pycodekg viz-timeline` |
| `pycodekg-mcp` | `pycodekg mcp` |
| `pycodekg-download-model` | `pycodekg download-model` |
| `pycodekg-install-hooks` | `pycodekg install-hooks` |

```bash
pycodekg --help
```

---

## Build Step-by-Step

### Recommended: Build both databases at once

```bash
pycodekg build --repo /path/to/repo [--wipe]
```

### Or step by step

```bash
# 1. SQLite knowledge graph
pycodekg build-sqlite --repo /path/to/repo [--wipe]

# 2. LanceDB semantic index
pycodekg build-lancedb [--model BAAI/bge-small-en-v1.5] [--wipe]

# 3. Pre-download the embedding model (offline / CI)
pycodekg-download-model --repo .
```

---

## Restricting Which Directories Are Indexed

By default, PyCodeKG indexes all Python files in your repository.

**Option 1: `pyproject.toml`** (persistent, recommended)

```toml
[tool.pycodekg]
include = ["src", "lib"]
```

**Option 2: CLI flags** (per-command override)

```bash
pycodekg build --repo . --include-dir src
pycodekg build --repo . --include-dir src --include-dir lib
```

When no `include` is configured, all directories are indexed (excluding `.git`, `.venv`, `__pycache__`, `.pycodekg`, etc.).

---

## `pack` Options

| Option | Default | Description |
|---|---|---|
| `--k` | `8` | Top-K semantic hits |
| `--hop` | `1` | Graph expansion hops |
| `--rels` | `CONTAINS,CALLS,IMPORTS,INHERITS` | Edge types to expand |
| `--context` | `5` | Extra context lines around each span |
| `--max-lines` | `160` | Max lines per snippet block |
| `--max-nodes` | `50` | Max nodes returned in pack |
| `--format` | `md` | Output format: `md` or `json` |
| `--include-symbols` | off | Include symbol nodes in output |

---

## MCP Server Setup

### Automated setup

The Quick Start installer (`curl ... | bash`) writes all MCP config files automatically. Alternatively, from inside Claude Code run:

```
/setup-mcp [/path/to/repo]
```

### Claude Code / Kilo Code — `.mcp.json`

```json
{
  "mcpServers": {
    "pycodekg": {
      "command": "pycodekg",
      "args": ["mcp", "--repo", "/absolute/path/to/repo"]
    }
  }
}
```

> Use per-repo `.mcp.json` only — do NOT add `pycodekg` to any global settings file.

### GitHub Copilot — `.vscode/mcp.json`

```json
{
  "servers": {
    "pycodekg": {
      "type": "stdio",
      "command": "/absolute/path/to/.venv/bin/pycodekg-mcp",
      "args": [
        "--repo", "/absolute/path/to/repo",
        "--db", "/absolute/path/to/repo/.pycodekg/graph.sqlite",
        "--lancedb", "/absolute/path/to/repo/.pycodekg/lancedb"
      ]
    }
  }
}
```

### Cline (global settings)

Cline does not support per-repo MCP config. The installer writes a uniquely-keyed entry to Cline's global settings file:

**macOS:** `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

```json
{
  "mcpServers": {
    "pycodekg-my-repo": {
      "command": "/absolute/path/to/venv/bin/pycodekg-mcp",
      "args": ["--repo", "/absolute/path/to/repo"]
    }
  }
}
```

> Do **not** add a `pycodekg` entry without a repo-specific suffix — global settings are shared across all VS Code windows.

### Claude Desktop — `claude_desktop_config.json`

macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pycodekg": {
      "command": "/absolute/path/to/venv/bin/pycodekg-mcp",
      "args": ["--repo", "/absolute/path/to/repo"]
    }
  }
}
```

Use **absolute paths** — Claude Desktop does not inherit your shell's working directory.

### Restarting agents after MCP setup

| Agent | How to restart |
|---|---|
| **Claude Code** | `Cmd+Shift+P` → `Developer: Reload Window` |
| **Cline** | `Cmd+Shift+P` → `Developer: Reload Window` |
| **Kilo Code** | `Cmd+Shift+P` → `Developer: Reload Window` |
| **GitHub Copilot** | `Cmd+Shift+P` → `Developer: Reload Window` |
| **Claude Desktop** | Quit and relaunch |

See [MCP.md](MCP.md) for the full MCP reference including tool schemas, query strategy guide, and troubleshooting.

---

## For Downstream Projects

If your project depends on PyCodeKG (e.g., `meta_kg`), **do not** redefine the CLI entrypoints in your own `pyproject.toml`.

**Correct: use PyCodeKG's commands directly**

```bash
poetry run pycodekg build-sqlite --repo /path/to/repo
poetry run pycodekg build-lancedb --repo /path/to/repo
poetry run pycodekg query "search term"
```

**Also correct: forward to PyCodeKG's modules via CLI**

```toml
[tool.poetry.scripts]
my-build-sqlite  = "pycode_kg.cli.cmd_build:build_sqlite"   # ✅
my-build-lancedb = "pycode_kg.cli.cmd_build:build_lancedb"  # ✅
my-mcp           = "pycode_kg.mcp_server:main"               # ✅
```

**Avoid legacy module names**

```toml
[tool.poetry.scripts]
my-build-sqlite = "pycode_kg.build_pycodekg_sqlite:main"  # ❌ legacy
```

The legacy modules (`build_pycodekg_sqlite`, `build_pycodekg_lancedb`) exist only as backward-compatibility stubs. Always import from `pycode_kg.cli.cmd_build`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `.pycodekg/graph.sqlite` | Canonical knowledge graph (nodes + edges) |
| `.pycodekg/lancedb/` | Derived semantic vector index |
| Markdown | Human-readable context packs with line numbers |
| JSON | Structured payload for agent/LLM ingestion |
