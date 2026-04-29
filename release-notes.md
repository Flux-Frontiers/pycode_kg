# Release Notes — v0.18.1

> Released: 2026-04-29

## Highlights

**MCP configuration template**
A new `.mcp.json.template` replaces the previously tracked `.mcp.json`. Users copy the template and fill in their own absolute paths — the live config is now gitignored, eliminating accidental commits of machine-specific paths. The `docs/claude_chat_global_mcp.json` reference doc was similarly sanitised with placeholder paths.

**Logo refresh — transparent backgrounds**
All PyCodeKG logo assets (`assets/logos/logo_16` through `logo_512`, `pycodeKG.PNG`, `src/logo.png`) now have transparent backgrounds, so they render cleanly on any background color in READMEs, docs, and UI surfaces.

**README overhaul**
The README is streamlined: the centered logo header is added at the top, verbose Python API, schema, storage layout, and contribution checklist sections are replaced with links to dedicated docs, and the Zenodo DOI is updated to the real archived DOI (`10.5281/zenodo.19834777`).

**Housekeeping**
Stale per-version analysis snapshots (`docs/analysis_v0.9.0` through `v0.17.2`) removed from the docs tree. Old Claude Copilot command files (superseded by the skills system) and `pycodekg_assessment_final.md` removed from the repo.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
