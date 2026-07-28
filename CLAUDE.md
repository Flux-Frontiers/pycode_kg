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
