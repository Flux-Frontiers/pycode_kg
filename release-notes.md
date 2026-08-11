# Release Notes — v0.22.0

> Released: 2026-08-11

The 3-D layout engine moves out of PyCodeKG and into `kgmodule-utils`, where every KG
module can reach it, and CI gains a job that tests the artifact users actually install
rather than the source tree it was built from. Neither change touches the graph format,
the CLI surface, or the MCP tool API, and every name that lived in `pycode_kg.layout3d`
still imports from exactly where it did before.

## What changed

**`layout3d` is now a thin binding over the shared engine.** The module went from 476
lines to 84. `Layout3D`, `LayoutNode`, `LayoutEdge`, `AlliumLayout`, `FunnelLayout` and
the Fibonacci point distributions now live in `kgmodule-utils` 0.11.0. The move was
overdue: GutenbergKG had been importing them from here and paying for a full `pycode-kg`
dependency to get five symbols that have nothing to do with parsing Python. What stays
behind is the genuinely code-specific part — `FunnelLayout` is a subclass supplying
`zlevels`, `level_sizes` and `default_level` from `pycode_kg.theme`, because the shared
engine drops unknown kinds to level 0, which in a code graph would put them in the
*module* layer instead of the symbol layer.

**CI now verifies the built wheel.** `lint`, `type-check` and `test` all run against
`src/` via `pythonpath`, which makes them structurally incapable of noticing a broken
artifact: a module the CLI imports can be absent from the wheel, or a dependency can be
declared in a form PyPI strips from wheel metadata, and every one of those jobs still
passes. The new job builds the wheel, installs it into a clean virtualenv with no source
tree in sight, and loads every console-script entry point. This was added fleet-wide
after a sibling project shipped to PyPI with green CI and a console script that died on
import.

**Maintainer tooling moved into an optional Poetry group.** `.mcp.json` serves a `dockg`
MCP server from `.venv/bin/dockg`, so that CLI has to exist in this repo's environment —
but nothing under `src/` imports `doc_kg`, and a real dependency would follow the wheel
out to every consumer. As a `[tool.poetry.group.kg]` group it is locked and installable
yet never written into wheel metadata; the built wheel's 42 `Requires-Dist` entries
contain no `doc-kg`.

**Dependencies refreshed.** Fifty locked packages moved, all inside their declared
constraints, with `setuptools` 83 → 84 the only major. Five transitive packages —
`gitpython`, `cachetools`, `gitdb`, `smmap` and `decorator` — left the lock entirely
when Streamlit 1.61 and IPython 9.16 stopped requiring them. Nothing in
`[project.dependencies]` changed.

## Upgrading

Nothing to do, and nothing to rebuild. Existing `.pycodekg/` indices are unaffected, and
`from pycode_kg.layout3d import ...` keeps working unchanged — every name is re-exported.
The one new requirement is `kgmodule-utils[semantic,viz3d]>=0.11.0`, and the `viz3d`
extra it adds is numpy only, which `semantic` already pulls, so a bare install grows by
nothing.

Working from a clone, `poetry install --extras dev --extras viz` is worth preferring over
a bare `poetry install`. The visualisation tests guard themselves with
`pytest.importorskip("pyvis")`, so without the `viz` extra they skip silently rather than
fail, and an environment that has pyvis but a stale IPython will skip them too.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
