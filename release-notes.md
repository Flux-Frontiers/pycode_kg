# Release Notes — v0.21.0

> Released: 2026-07-28

PyCodeKG now runs on `transformers` 5. The previous `<4.57` ceiling pinned the stack to 4.56.2, a release carrying two open high-severity advisories, and this version lifts it to `>=5.5.0,<6`. The upgrade is invisible to your data: embeddings come out bitwise identical and an index rebuilt on the new stack is byte-for-byte the same file. Nothing needs rebuilding.

## What changed

**The transformers ceiling is gone.** Lifting it clears a remote-code-execution advisory and an arbitrary-code-execution advisory in the model-loading path. Because the old and new ranges do not overlap, this is a breaking dependency change — an environment pinned to transformers 4.x cannot install this release. `huggingface-hub` moves to 1.x along with it, and `typer` arrives as a new transitive dependency.

**Embeddings were verified unchanged, not assumed unchanged.** Three models were checked across awkward inputs — empty strings, whitespace, three-thousand-character blocks, unicode and emoji, CRLF line endings — and every vector matched bit for bit, including the `trust_remote_code` model path. A full index rebuild reproduced an identical vector store, and queries run against an index built under the old stack returned identical results under the new one.

**A silent embedder bug went with it.** `transformers` 5 removed the `transformers.logging` submodule alias. The shared embedder imported it by name, and the resulting `ModuleNotFoundError` was swallowed by a broad `except`, so log and progress-bar suppression quietly stopped working while appearing fine — a stray "Loading weights" bar leaked into every build and query. The fix ships in `kgmodule-utils` 0.9.0, which this release now requires.

**The `kgdeps` extra has been removed.** PyCodeKG and DocKG each listed the other as an optional dependency, which meant neither could resolve a relaxed pin until the other had already been published — a deadlock with no first move. Since neither package actually imports the other, the dependency was removed rather than sequenced around.

**Plus the tail of the 0.20.0 migration.** Scripts, IDE config, docs, and agent skills that still referenced the retired LanceDB backend have been swept — three of them outright broken rather than merely stale. See the changelog for the full accounting.

## Upgrading

Existing indexes need no attention. There is no migration, no re-index, and no change to the vector store format — the same repository produces the same file before and after.

The one thing to check is your environment. If you hold `transformers` at 4.x for another package, that pin now conflicts and must be resolved before upgrading. And if you installed via `pip install 'pycode-kg[kgdeps]'`, that extra no longer exists; install the sibling directly with `pip install doc-kg` instead.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
