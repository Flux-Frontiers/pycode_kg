# Release Notes -- v0.30.0

> Released: 2026-11-24

`pack()` no longer serves source text from a Python file that changed after
the graph was built. A snippet is cut from the live file by the line numbers
recorded at build, so an edited file used to return the wrong lines under a
function's name, with nothing to say so. With kgmodule-utils 0.32.0 the build
records a hash of every source file, and `pack()` leaves out the snippets of
any file that no longer matches, with a warning to rebuild.

## What changed

**Source hashes from the CLI.** `pycodekg build`, `update` and `build-sqlite`
write the graph store directly rather than through the shared pipeline, so
they now record the hashes themselves, after symbol resolution. `pack()`,
the MCP `pack` tool and kgrag's federated pack all leave out a changed file's
text, and `PyCodeKG.stale_sources()` names the files that changed or went
missing. The rest of a result is unaffected: other files' snippets, and the
nodes themselves, still come back.

**Dependencies.** The kgmodule-utils floor is 0.32.0. The lock was written with
Poetry 2.4.3, and a new test fails if a lock would install two versions of a
package on Linux, macOS or Windows, the Poetry 2.5 regression that crashed
torch in other fleet CI.

**A new logo.** The brain is gone. The Art Techno mark is a call tree: a
module holding two classes of two functions each, with one call edge between
them. The README's images now use absolute URLs, so they show on PyPI too.

## Upgrading

Run `pycodekg build` once after upgrading. A store built by an earlier version
has no hashes and packs exactly as before, so the check only starts after a
rebuild. From then on, editing a file and packing before the next build
returns that file's nodes without source text, plus a warning naming the file.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
