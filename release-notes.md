# Release Notes -- v0.28.2

> Released: 2026-10-15

`pycodekg analyze` no longer reports web route handlers as dead code. On a
FastAPI repo this was enough to drop the analysis by a full grade.

## What changed

**Route handlers count as entry points.** A function decorated with
`@app.get`, `@router.post`, `@app.middleware`, `@app.route` or another
route-registration decorator of FastAPI, Starlette or Flask is called by the
framework's router, so the graph never holds a call to it, and the orphan scan
listed it as dead code. The scan now recognizes these decorators, including
ones split across several lines and handlers defined inside an app factory.
On `satprint`, a FastAPI app, dead-code candidates fall from 13 to 9, all four
removed ones false, and the grade rises from C (74.6) to B (77.0). Two related
blind spots remain: Pydantic models used only as type annotations, and
classes instantiated at module scope, still show as unused.

**Dependencies.** The floors rise to kgmodule-utils 0.27.0 and quiltwright
0.16.0, and the lock moves with them.

## Upgrading

Nothing to do. Re-run `pycodekg analyze` on a web application to get the
corrected dead-code list and grade.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
