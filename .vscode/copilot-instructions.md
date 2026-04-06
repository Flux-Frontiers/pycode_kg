# GitHub Copilot Instructions for CodeKG

## Available VS Code Tasks

The following CodeKG workflow tasks are available via the VS Code command palette (**Cmd+Shift+P** → search task name):

### Knowledge Graph Tasks
- **CodeKG: Rebuild** — Full rebuild with `--wipe` (both SQLite + LanceDB). Use after significant code changes or renames.
- **CodeKG: Build SQLite Graph** — Build/update the SQLite knowledge graph (incremental).
- **CodeKG: Build LanceDB Index** — Build/update the semantic vector index (incremental).

### Query & Analysis Tasks
- **CodeKG: Query (Interactive)** — Run an interactive semantic query over the graph.
- **CodeKG: Generate Architecture** — Generate Markdown architecture description (saves to `architecture.md`).
- **CodeKG: Run Thorough Analysis** — Run full codebase analysis (complexity, hotspots, dependencies).

### Snapshot Tasks
- **CodeKG: List Snapshots** — Show all captured temporal snapshots in reverse chronological order.
- **CodeKG: Save Snapshot** — Capture current metrics and save as a timestamped snapshot.

## Invoking Tasks in Copilot Chat

In Copilot chat, you can reference or ask to run these tasks:
- "Run the **CodeKG: Rebuild** task"
- "Execute **CodeKG: Query (Interactive)** and search for database layer"
- "Generate architecture with the **CodeKG: Generate Architecture** task"

## MCP Integration

The repo is also configured with CodeKG MCP server in `.vscode/mcp.json`. You have access to:
- `graph_stats()` — Get codebase metrics (node/edge counts by type)
- `query_codebase(q, k=8, hop=1, max_nodes=25, min_score=0.0, max_per_module=0)` — Semantic + structural query with precision/diversity controls
- `pack_snippets(q, k=8, hop=1, max_nodes=15, min_score=0.0, max_per_module=0)` — Source-grounded code snippets with context and precision controls
- `get_node(node_id, include_edges)` — Fetch node details by stable ID; `include_edges=True` also returns outgoing edges and incoming callers in one call
- `callers(node_id)` — Find all callers of a function (impact analysis), with import-aware filtering for ambiguous same-name symbols
- `explain(node_id)` — Natural-language explanation of a node (callers, callees, role)
- `analyze_repo()` — Full architectural analysis (complexity, coupling, hotspots)
- `snapshot_list(limit)` — List saved metric snapshots newest-first
- `snapshot_show(key)` — Full metrics for a snapshot key (tree hash) or `"latest"`; legacy snapshots backfill missing deltas on load
- `snapshot_diff(key_a, key_b)` — Compare two snapshots by key; returns delta for nodes, edges, coverage

**Prefer MCP tools for interactive queries — they're faster and source-grounded.**

## When to Use What

| Task | Use when |
|---|---|
| **Rebuild** | You've renamed/moved/deleted code; after major refactors |
| **Build SQLite/LanceDB** | Minor additions; incremental updates (after small commits) |
| **Query** | You need to explore the codebase via natural language |
| **Architecture** | You need a high-level overview of module relationships |
| **Thorough Analysis** | You need detailed metrics (complexity, coupling, docstring coverage) |
| **Snapshots** | You're tracking metrics over time (e.g., for releases) |

Use **MCP tools** directly instead of tasks for quick, interactive codebase exploration.
