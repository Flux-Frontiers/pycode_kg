# Release Notes — v0.23.0

> Released: 2026-08-15

PyCodeKG can now grow your repository as a tree and put it on a holographic display. `pycodekg viz3d --layout organic` replaces the lattice with a skeleton grown toward the code by space colonization, and `pycodekg quilt` renders that tree as a Looking Glass light-field quilt. Everything else in this release is consolidation: the depth-budget helper moved upstream, the module headers were completed, and a pile of console-script aliases nobody used went away.

## What changed

**The repository as a tree.** The trunk is the repo, each limb a module, each leaf a class, function or method. Because the attractors are real definitions, the canopy's shape is the codebase's shape — and two readings fall out of the growth rather than being drawn on top of it. Limb *thickness* follows the pipe model, so a fat limb is a module carrying a lot of code; limb *length* is scaled by definition count, so the biggest module reaches furthest. Foliage is tinted by node kind, which makes a class-heavy module visibly different from a module of free functions. The growth engine is shared fleet-wide in `kgmodule-utils`; what lives here is only the mapping from code to wood.

**Holographic output.** `pycodekg quilt` writes a multi-view quilt a lenticular panel fuses into real depth, with `--orbit` for a turntable video and `--cast` to hand it straight to Looking Glass Bridge. Every render prints its disparity budget first — the per-view pixel shift that decides whether the display fuses the views or ghosts them. The viewer gained a matching **Cast to LG** button and a Render Mode group whose layout selector now re-renders immediately.

**The depth budget moved upstream, and got fixed on the way.** This package used to hand-roll the report, as did gutenberg_kg. It is now `quiltwright.depth_report`. Promoting it exposed a bug both copies shared: `render_quilt` narrows the FOV and dollies back before sweeping, so a budget measured from the camera as-framed describes a picture nobody is about to make. The numbers this release prints are the ones the render actually produces.

**Housekeeping worth knowing about.** Every module docstring now carries an `Author` and `License: Elastic 2.0` line — 54 of 54. Four tombstone modules that had been reduced to a one-line redirect are deleted, along with a permanently-skipped LanceDB test, so the suite runs with no skips at all. The sister-project list moved into `docs/SISTER_PROJECTS.md`, where it is complete and correct for the first time in a while.

## Upgrading

Nothing to migrate: no API changed, and existing graphs work as they are. Two things to be aware of.

The per-subcommand console scripts are gone — `pycodekg-analyze`, `pycodekg-build` and thirteen others. Use `pycodekg <subcommand>`, which every doc already showed. **`pycodekg-mcp` is deliberately kept**, because the documented Claude Desktop and Copilot setups put that path into config files; those keep working untouched.

For the new visuals, install the `viz3d` extra (`pip install 'pycode-kg[viz3d]'`). It now works on Python 3.13 as well as 3.12 — quiltwright 0.4.0 widened its own ceiling, which retired the version marker consumers previously needed.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
