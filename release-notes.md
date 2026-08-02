# Release Notes — v0.21.3

> Released: 2026-08-02

A packaging-correctness release. A dependency change in 0.21.2's wake left `sqlite-vec`
out of the install tree entirely, which broke every build and query path for anyone
installing from PyPI — the vector index could neither be created nor read. This release
restores it and tightens what a default install actually pulls down. There are no code
changes; only the declared dependency surface moved.

## What changed

**`sqlite-vec` is a first-class dependency again.** PyCodeKG hard-codes `sqlite-vec` as
its vector backend, so the package is a hard runtime requirement of every build and
query — not an opt-in alternative to something else. It had been arriving second-hand
through an optional extra of `kgmodule-utils`, and when those extras were narrowed it
silently vanished from the tree; the first thing a fresh install did on `pycodekg build`
was raise `ImportError`. It is now declared directly, pinned to the exact version the
rest of the KG family uses, so the requirement is visible in this package's own metadata
rather than inherited from a sibling's optional feature set.

The test suite had no opinion on any of this. Its sqlite-vec coverage is guarded by
`importorskip`, so removing the dependency turned those tests into skips and the suite
stayed green.

**A default install is meaningfully smaller.** Two libraries were being pulled in for no
reason. `lancedb` arrived through an extra that also carried `sentence-transformers`,
`torch` and `transformers` — all three of which PyCodeKG already declares itself — and
nothing in the codebase has imported LanceDB since the sqlite-vec migration. `pyvis` was
being forced into every installation even though it is only reachable from the Streamlit
and 3-D visualizers, both of which live behind optional extras and import it lazily.
Neither is installed by default now.

**Documentation and release tooling caught up.** The committed architecture analysis was
three releases stale and has been regenerated against current source. Two errors in the
release workflow were corrected: it documented a CLI invocation that fails outright, and
it pointed at the wrong table for the version string while omitting three of the files
that carry it.

## Upgrading

Nothing to migrate and no rebuild required — existing `.pycodekg/` indices are
unaffected. `pip install --upgrade pycode-kg` restores `sqlite-vec` on its own.

One thing to check: if you were installing bare `pycode-kg` and relying on `lancedb` or
`pyvis` showing up as a side effect, they no longer will. For the visualizers, install
the extra that owns them — `pip install 'pycode-kg[viz]'` for the Streamlit graph view,
or `[viz3d]` for the PyVista viewer. If you genuinely need LanceDB, install it directly;
PyCodeKG itself no longer uses it.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
