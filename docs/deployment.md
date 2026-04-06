# PyCodeKG Deployment Guide

*Author: Eric G. Suchanek, PhD*

---

## Overview

PyCodeKG has two distinct deployment surfaces:

| Surface | What it is | Best options |
|---|---|---|
| **Python library + CLI** | `pycode_kg` package + unified `pycodekg` CLI | PyPI, Conda, GitHub Releases |
| **Streamlit web app** | `pycodekg viz` interactive graph explorer | Streamlit Cloud, Fly.io |

These can be deployed independently or together. The sections below cover each option in detail.

---

## Option 1 — PyPI (Recommended for the library)

The project is already structured perfectly for PyPI: `pyproject.toml` with Poetry, proper `packages` declaration, classifiers, keywords, entry points, and a README.

### 1a. Prepare for release

```bash
# Bump version in pyproject.toml and src/pycode_kg/__init__.py
# e.g. 0.1.0 → 0.2.0

# Ensure the lock file is current
poetry lock

# Run tests
poetry run pytest

# Build sdist + wheel
poetry build
# → dist/pycode_kg-0.1.0.tar.gz
# → dist/pycode_kg-0.1.0-py3-none-any.whl
```

### 1b. Publish to TestPyPI first

```bash
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish --repository testpypi
```

Verify the install:

```bash
pip install --index-url https://test.pypi.org/simple/ pycode-kg
```

### 1c. Publish to PyPI

```bash
poetry publish
# prompts for PyPI credentials (or use POETRY_PYPI_TOKEN_PYPI env var)
```

After publishing, users install with:

```bash
pip install pycode-kg
```

The `pycodekg` CLI and all subcommands become available immediately:

```
pycodekg build-sqlite
pycodekg build-lancedb
pycodekg query
pycodekg pack
pycodekg viz
pycodekg viz3d
pycodekg analyze
pycodekg mcp
```

### 1d. Automate with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install poetry
      - run: poetry install --no-dev
      - run: poetry build
      - run: poetry publish
        env:
          POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
```

Tag a release to trigger:

```bash
git tag v0.1.0
git push origin v0.1.0
```

---

## Option 2 — Streamlit Community Cloud (Zero-infra for the app)

The fastest way to share the Streamlit app publicly — free tier available.

1. Push the repo to GitHub (already done: `github.com/Flux-Frontiers/pycode_kg`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select repo `Flux-Frontiers/pycode_kg`, branch `main`, main file `src/pycode_kg/app.py`
4. Add a `requirements.txt` (Streamlit Cloud doesn't use Poetry directly):

```bash
# Generate from poetry
poetry export -f requirements.txt --without-hashes -o requirements.txt
```

**Limitation:** Streamlit Cloud has no persistent filesystem — the SQLite/LanceDB
artifacts won't survive restarts. Best suited for demos with a pre-built DB
committed to the repo or stored in cloud storage (S3, GCS).

---

## Option 3 — Fly.io (Lightweight cloud VM for the app)

Fly.io runs containers globally with persistent volumes — a good middle
ground between Streamlit Cloud and a full Kubernetes cluster.

```bash
# Install flyctl
brew install flyctl
fly auth login

# From the repo root
fly launch --name pycodekg --region iad

# Add a persistent volume for SQLite + LanceDB
fly volumes create pycodekg_data --size 10 --region iad

# Deploy
fly deploy
```

Add to `fly.toml`:

```toml
[mounts]
  source = "pycodekg_data"
  destination = "/data"

[[services]]
  internal_port = 8500
  protocol = "tcp"

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
  [[services.ports]]
    port = 80
    handlers = ["http"]
```

---

## Option 4 — GitHub Releases (Binary artifacts)

For users who want pre-built wheels without PyPI:

```bash
# Build
poetry build

# Create a GitHub release and attach artifacts
gh release create v0.1.0 dist/* \
  --title "PyCodeKG v0.1.0" \
  --notes "Initial release"
```

Users install directly from the release:

```bash
pip install https://github.com/Flux-Frontiers/pycode_kg/releases/download/v0.1.0/pycode_kg-0.1.0-py3-none-any.whl
```

---

## Option 5 — MCP Server (AI agent integration)

PyCodeKG ships a production-ready MCP server (`pycodekg mcp`) that exposes the full hybrid query and snippet-pack pipeline as structured tools for any MCP-compatible agent — Claude Code, Kilo Code, GitHub Copilot, Claude Desktop, Cursor, Continue, or any custom agent.

### Install

```bash
# MCP server is included in the standard install — no extra needed
poetry add 'pycode-kg @ git+https://github.com/Flux-Frontiers/pycode_kg.git'
# or
pip install 'pycode-kg @ git+https://github.com/Flux-Frontiers/pycode_kg.git'

# With 3D visualizer (optional)
poetry add 'pycode-kg[viz3d] @ git+https://github.com/Flux-Frontiers/pycode_kg.git'
```

### Build the knowledge graph first

```bash
pycodekg build-sqlite --repo /path/to/repo
pycodekg build-lancedb
```

### Start the server manually

```bash
pycodekg mcp \
  --repo /path/to/repo \
  --db   /path/to/repo/.pycodekg/graph.sqlite
```

### Exposed tools

| Tool | Description |
|---|---|
| `graph_stats()` | Node and edge counts by kind/relation |
| `query_codebase(q, ...)` | Hybrid semantic + structural query; returns JSON |
| `pack_snippets(q, ...)` | Hybrid query + source-grounded snippets; returns Markdown |
| `get_node(node_id)` | Fetch a single node by stable ID |

### Agent configuration quick reference

| Agent | Config file | Key |
|---|---|---|
| **Claude Code** | `.claude/claude_code_config.json` (project root) | `"mcpServers"` |
| **Kilo Code** | `.mcp.json` (project root) | `"mcpServers"` |
| **GitHub Copilot** | `.vscode/mcp.json` (workspace root) | `"servers"` + `"type": "stdio"` |
| **Claude Desktop** | `~/Library/Application Support/Claude/claude_desktop_config.json` | `"mcpServers"` |
| **Cline** | Global `cline_mcp_settings.json` only | `"mcpServers"` |

**Claude Code** (`.claude/claude_code_config.json`):
```json
{
  "mcpServers": {
    "pycodekg": {
      "command": "pycodekg",
      "args": ["mcp",
        "--repo", "/absolute/path/to/repo",
        "--db",   "/absolute/path/to/repo/.pycodekg/graph.sqlite"
      ]
    }
  }
}
```

**Kilo Code** (`.mcp.json` — Copilot servers without PyCodeKG):
```json
{
  "mcpServers": {
    "copilot-memory": { "...": "configured by Claude Copilot" },
    "skills-copilot": { "...": "configured by Claude Copilot" },
    "task-copilot": { "...": "configured by Claude Copilot" }
  }
}
```

**GitHub Copilot** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "pycodekg": {
      "type": "stdio",
      "command": "pycodekg",
      "args": ["mcp",
        "--repo", "/absolute/path/to/repo",
        "--db",   "/absolute/path/to/repo/.pycodekg/graph.sqlite"
      ],
      "env": { "POETRY_VIRTUALENVS_IN_PROJECT": "false" }
    }
  }
}
```

**Claude Desktop** — use the absolute venv binary path (Poetry not on PATH):
```bash
poetry env info --path   # → /path/to/venv; binary at /path/to/venv/bin/pycodekg
```
```json
{
  "mcpServers": {
    "pycodekg": {
      "command": "/path/to/venv/bin/pycodekg",
      "args": ["mcp", "--repo", "/abs/path", "--db", "/abs/path/.pycodekg/graph.sqlite"]
    }
  }
}
```

### Automated setup

The `/setup-mcp` command (available in Claude Code / Kilo Code) automates the full workflow — install, build, smoke-test, and write all config files:

```
/setup-mcp /path/to/repo
```

See [`docs/MCP.md`](MCP.md) for the complete reference.

---

## Recommended Deployment Strategy

| Goal | Recommended path |
|---|---|
| Share the library with the Python community | **PyPI** (Option 1) |
| Quick public demo, no infra | **Streamlit Community Cloud** (Option 2) |
| Persistent cloud deployment | **Fly.io** (Option 3) |
| Distribute pre-built wheels without PyPI | **GitHub Releases** (Option 4) |
| Integrate with AI agents / IDEs | **MCP Server** (Option 5) |

### Suggested release order

1. **PyPI first** — the `pyproject.toml` is already complete; `poetry build && poetry publish` is all it takes.
2. **MCP server** — add as a CLI entry point so agent users get it automatically with `pip install pycode-kg`.

---

## Pre-release Checklist

- [ ] Bump `version` in `pyproject.toml` and `src/pycode_kg/__init__.py`
- [ ] Update `CHANGELOG.md`
- [ ] Run `poetry run pytest` — all tests green
- [ ] Run `poetry run ruff check src/` — no lint errors
- [ ] Run `poetry build` — wheel and sdist build cleanly
- [ ] Test install in a fresh venv: `pip install dist/pycode_kg-*.whl`
- [ ] Smoke-test all `pycodekg` subcommands
- [ ] `git tag v0.1.0 && git push origin v0.1.0`
- [ ] `poetry publish` (or let GitHub Actions do it)
