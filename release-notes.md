# Release Notes — v0.24.1

> Released: 2026-08-25

A single unreadable file inside `.venv/` was silently gutting two phases of
the `pycodekg analyze` report. This release fixes that, teaches call
resolution to read receiver annotations, and cleans up two places where the
report presented numbers badly.

## What changed

**One undecodable file no longer costs you two report phases.** The orphan
scan's `_declared_export_names()` walked the *entire* repository root with a
raw `rglob("*.py")` — unfiltered by the `.venv`/`__pycache__` exclusions the
graph build itself honors — and three of the analyzer's read sites caught
`OSError` but not `UnicodeDecodeError`, which is a `ValueError` subclass and
slipped straight past them. Analyzing this very repo therefore reached a
vendored dependency's deliberately Big5-encoded test fixture under `.venv/`,
which aborted the declared-exports scan outright. The damage was invisible:
Public API identification reported 2 functions against a real 31, dead-code
detection reported nothing at all, and the only clue was a generic
"Dependency analysis incomplete" warning that named no file. The walk now
goes through the same `iter_python_files()` helper the build uses, and each
read site skips one unreadable file with a debug log naming it rather than
losing the whole phase. `architecture.py` carried the identical defect —
`_infer_project_title()` read `README.md` with the platform's locale encoding
and caught only `OSError`, and since it holds that module's sole exception
handler, an undecodable byte escaped uncaught out of `analyze_to_markdown()`.

**Call resolution can now read the receiver's type.** A dotted call whose
receiver is a plain local or parameter — not `self`/`cls`, not a module-level
import alias — records the class name from that receiver's annotation on its
`sym:` stub. Given `def use(plotter: pv.Plotter)`, the stub for
`plotter.render()` now carries `receiver_class="Plotter"`. It unwraps
`X | None` and `Optional[X]`, the shape a lazily-assigned local or a
loop-accumulated match object tends to carry, and it deliberately ignores
nested function and class scopes so an annotation inside a closure can't leak
into the enclosing function's lookup.

The consumer lives in the SDK, and it is version-sensitive in a way worth
stating plainly: `resolve_symbols()` only began reading this metadata in
`kgmodule-utils` 0.18.1, so that is now the floor. Against 0.18.0 the stubs
are tagged correctly and the tag is silently ignored -- the feature installs,
reports no error, and does nothing. Indexing this repo tags 139 call stubs
across 13 distinct receiver types; most of them (`dict`, `str`, `Plotter`,
`DiGraph`) name types defined outside the graph, which is precisely the
signal that stops a `d.get()` from resolving onto an unrelated first-party
function named `get`.

**Two reporting cleanups.** The console summary printed `node_counts` and
`edge_counts` through `str()`, dumping raw Python dict reprs that wrapped
across the value column; they now render as a side-by-side "Nodes by Kind" /
"Edges by Relation" breakdown, largest bucket first, with thousands
separators and coverage as a percentage. A stat key the label map doesn't
recognize still prints under its raw name, so a metric added later can't
vanish silently. Separately, the Markdown report's "Edge Distribution" table
omits `RESOLVES_TO` by design — it records the graph's own stub-to-definition
bookkeeping rather than a relationship between two pieces of code — but it
summed to 5,485 directly beneath a "Total Edges 6,443" row, leaving 958 edges
unexplained. The table keeps its shape; the renderer now states the excluded
count and the reason beneath it.

## Upgrading

`pip install --upgrade pycode-kg` pulls the raised `kgmodule-utils >=0.18.1`
floor with it; if you pin that package yourself, raise it, or receiver-aware
resolution will sit inert with nothing to tell you so.

The graph and vector index formats are unchanged and `receiver_class`
defaults to `None`, so an existing index keeps working. Rebuild
(`pycodekg build`) if you want the corrected report and the receiver types,
since an index built before this release carries neither — and your last
analysis run may have been missing its public-API and dead-code sections
without saying so.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
