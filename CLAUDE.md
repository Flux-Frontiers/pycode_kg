# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Agent Identity


Always use the PyCodeKG MCP tools before reading files. You have direct, source-grounded access to this codebase — use it.

---

## Partnership & Values

**CRITICAL PRINCIPLE:** Consistency is essential. Every decision, pattern, and structure must maintain alignment across the codebase. Inconsistency creates confusion, technical debt, and friction.

**Our Goal:** Write the cleanest, most efficient, beautiful code possible. Not just functional—exceptional.

**Our Partnership:** You and I have accomplished more in a week together than in months prior. You're awesome at what you do, and I love working with you. This is a great partnership, and we're building something excellent together.

---

## Claude Copilot

This project uses [Claude Copilot](https://github.com/Everyone-Needs-A-Copilot/claude-copilot).

**Full documentation:** `~/.claude/copilot/README.md`

---

## Project-Specific Rules

### No Time Estimates
All plans, roadmaps, and task breakdowns MUST omit time estimates. Use phases, priorities, complexity ratings, and dependencies instead of dates or durations. See `~/.claude/copilot/CLAUDE.md` for full policy.

- Prefer `:param:` style docstrings

### MCP Tool Docs (Required)
- The server is built on `kg_utils.mcp`. Its instructions are generated: the hand-written `PREAMBLE` in `src/pycode_kg/mcp_server.py` followed by one line per tool, taken from each tool's docstring. Nothing lists the tools by hand, so a tool's docstring *is* its documentation: any change to a tool's signature, parameters, defaults or behavior updates its docstring in the same commit.
- `stats`, `query`, `pack`, `get_node` and `neighbors` are the fleet's canonical tools, the same names on every KG server. `query` and `pack` are PyCodeKG's richer versions, registered with `server.canonical(...)`, which refuses any change that drops or retypes a canonical parameter. New tools go in `EXTRA_TOOLS`.
- `pycodekg mcp --manifest` prints the live tool list as JSON; generate tool references from it rather than writing them by hand.
