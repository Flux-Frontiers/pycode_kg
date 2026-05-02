# Release Notes — v0.18.2

> Released: 2026-05-01

A docs and hygiene release. No API or behaviour changes.

The MCP and Installation guides had drifted into each other — both tried to teach setup, neither did it completely. They're now split cleanly: **`docs/INSTALLATION.md`** owns install, build, and per-agent configuration; **`docs/MCP.md`** is purely the MCP tool reference. While we were in there, the MCP reference also caught up with reality — it had been documenting eleven tools for a while; the server actually exposes nineteen. All nineteen are now documented and grouped by purpose (Discovery, Relationships, Centrality & Ranking, Snapshots).

A round of `:param:`-style docstrings on the SIR centrality pipeline, the snapshot manager, and the CLI entry points pushed non-test docstring coverage from **91.5% to 96%**. Two long-orphaned placeholder modules (`mcp/bridge_tools.py`, `mcp/framework_tools.py`) were removed — they were never imported, and the live MCP server uses `analysis/bridge.py` and `analysis/framework_detector.py` directly.

## What you should know

- **`.mcp.json.template` is gone.** Use the one-line installer or `/setup-mcp` instead — both write `.mcp.json` with absolute paths resolved at install time.
  ```bash
  curl -fsSL https://raw.githubusercontent.com/Flux-Frontiers/pycode_kg/main/scripts/install-skill.sh | bash
  ```
- **The KGModule SDK guide moved.** It now lives at [`kgrag/docs/KGMODULE.md`](https://github.com/Flux-Frontiers/kgrag/blob/main/docs/KGMODULE.md), co-located with the federation layer that consumes it.
- **No rebuild required.** Existing `.pycodekg/graph.sqlite` and `.pycodekg/lancedb/` remain valid.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
