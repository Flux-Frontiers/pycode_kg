# MCP Consolidation Plan

Cross-repo plan for the KG module family. Written in `pycode_kg/docs/` because that
is where the work started; the Phase B implementation lands in `KG_utils`, and this
document should move there once Phase B begins.

**Status:** Phase A complete **and shipped** — every repo in the family is bounded,
carries an MCP regression test, and has been released. Four packages are published
to PyPI with the ceiling in their live metadata. Phase B not started.

| Repo | Released | PyPI | Carries |
|---|---|---|---|
| pycode_kg | 0.21.1 | ✅ published | already bounded |
| doc_kg | 0.19.1 | ✅ published | `mcp<2` + tests |
| memory_kg | 0.6.2 | ✅ published | `mcp<2` + tests, `kgmodule-utils>=0.9.0` |
| agent_kg | 0.8.2 | ✅ published | `mcp<2` + tests, `kgmodule-utils>=0.9.0` |
| diary_kg | 0.93.4 | ✅ published | `mcp<2` + tests |
| tscode_kg | 0.2.0 | ✅ published (first release) | `mcp<2` + tests, `kg` extra dissolved |
| Metabo_kg | 0.9.1 | ⛔ standalone, never published | `mcp<2` + `create_server()` tests |
| gutenberg_kg | 1.12.0 | ⛔ standalone, never published | `fastmcp>=3.0,<4` + tests |
| kgrag | 0.11.0 | ✅ published | already bounded, 2.x-ready |

Verified against the published index rather than local wheels: `memory-kg`,
`agent-kg`, `diary-kg` and `tscode-kg` all advertise `Requires-Dist: mcp<2,>=1.0.0`.
A clean `pip install` can no longer resolve mcp 2.x and break the server at import.

---

## 1. Ground truth

`mcp` 2.0.0 is published on PyPI. Local environments are on 1.28.1, so a pinned
lock file hides the break from every developer while a clean `pip install` from
PyPI fails at import time.

What 2.0 actually changed, verified against the real 2.0.0 wheel rather than
inferred from release notes:

- `mcp.server.fastmcp` was **removed**. The ergonomic server class was rebuilt as
  `mcp.server.mcpserver.MCPServer`, re-exported as `mcp.server.MCPServer`.
- The lowlevel `mcp.server.Server` **survived** — `mcp/server/__init__.py` in 2.0
  still does `from .lowlevel import NotificationOptions, Server`.
- `MCPServer.__init__` accepts `name` and `instructions`; `.tool()` is still a
  decorator factory; `.run()` still takes `transport="stdio"|"sse"|"streamable-http"`.
  The port is a rename, not a rewrite.

### Per-repo state

Spec lines are as they stood before Phase A; each is now bounded. "Built at" is
where the server object is constructed, which decides what a regression test has
to do — see the Phase A regression guard.

| Repo | MCP module | LOC | Tools | API family | Built at | Spec before Phase A (line) |
|---|---|---|---|---|---|---|
| pycode_kg | `src/pycode_kg/mcp_server.py` | 1809 | 19 | `mcp.server.fastmcp` | import | `mcp>=1.0.0,<2` (99) — already safe |
| tscode_kg | `src/tscode_kg/mcp_server.py` | 1412 | 19 | `mcp.server.fastmcp` | import | `mcp>=1.0.0` (65, `kg` extra) — **was broken**; extra since dissolved into core |
| kgrag | `src/kg_rag/mcp_server.py` | 994 | — | lowlevel `Server` | `_make_server()` | `mcp>=1.0.0,<2` (115) — already safe, 2.x-ready |
| Metabo_kg | `src/metabokg/mcp_tools.py` | 654 | 13 | `mcp.server.fastmcp` | `create_server()` | `mcp>=1.0.0` (78) — **was broken** |
| agent_kg | `src/agent_kg/mcp/server.py` | 349 | — | lowlevel `Server` | — | `mcp>=1.0.0,<2` (75) — already safe, 2.x-ready |
| doc_kg | `src/doc_kg/mcp_server.py` | 188 | 4 | `mcp.server.fastmcp` | import | `mcp>=1.0.0,<2` (79) — fixed in 0.19.1 |
| memory_kg | `src/memory_kg/mcp_server.py` | 170 | 4 | `mcp.server.fastmcp` | import | `mcp>=1.0.0,<2` (82) — fixed in 0.6.1 |
| diary_kg | `src/diary_kg/mcp_server.py` | 162 | 3 | `mcp.server.fastmcp` | import | `mcp>=1.0.0` (83) — **was broken** |
| gutenberg_kg | `src/gutenberg_kg/mcp_server.py` | 161 | 2 | standalone `fastmcp` | import | `fastmcp>=2.0` (124, 161) — unbounded across a major |

Five repos failed on a clean install when this was written; doc_kg and memory_kg
were fixed and released before Phase A began. gutenberg_kg never failed, but had
an unbounded floor against a package that has since gone 3.x on its own schedule.

### Three observations that shape the plan

**The immediate cause is unbounded version specs, not code duplication.** A shared
MCP layer would not have prevented this break; a `<2` ceiling would have.
Consolidation's real payoff is making that decision once instead of nine times.

**The shared surface is the bootstrap, not the tools.** Diffing `doc_kg` against
`memory_kg` with names normalised gives 52 differing lines out of ~180, and nearly
all of them are incidental (a `traced` parameter, a `--vectors-path` flag). The
argparse block, the `_kg` singleton and `_get_kg()`, the missing-database warning,
the stderr startup banner, and the `mcp.run(transport=...)` call are near-verbatim
identical across doc_kg, memory_kg, and diary_kg. Tool bodies are domain-specific
and must stay in their own repos.

**The vehicle already exists and is already universal.** `KG_utils` publishes as
`kgmodule-utils` 0.9.0 and every one of the nine repos already depends on it. It
contains no MCP code and declares `dependencies = []`, so anything MCP-related has
to sit behind an optional extra to preserve the zero-dependency core.

---

## 2. Phase A — restore clean installs

**Priority:** urgent. **Complexity:** trivial. **Dependencies:** none.
**Status:** ✅ complete.

Add a ceiling to every unbounded spec. Copy the rationale comment already written
at `pycode_kg/pyproject.toml:93-99` so the next reader knows why the bound exists
and what lifting it requires.

| Repo | File:line | From | To | Status |
|---|---|---|---|---|
| tscode_kg | `pyproject.toml:65` | `"mcp>=1.0.0",` | `"mcp>=1.0.0,<2",` | ✅ |
| Metabo_kg | `pyproject.toml:78` | `"mcp>=1.0.0",` | `"mcp>=1.0.0,<2",` | ✅ |
| doc_kg | `pyproject.toml:73` | `"mcp>=1.0.0",` | `"mcp>=1.0.0,<2",` | ✅ shipped in 0.19.1 |
| memory_kg | `pyproject.toml:76` | `"mcp>=1.0.0",` | `"mcp>=1.0.0,<2",` | ✅ shipped in 0.6.1 |
| diary_kg | `pyproject.toml:83` | `"mcp>=1.0.0",` | `"mcp>=1.0.0,<2",` | ✅ |
| gutenberg_kg | `pyproject.toml:124, 161` | `"fastmcp>=2.0",` | `"fastmcp>=3.0,<4",` | ✅ |

gutenberg_kg was the one judgement call, and the premise this plan started from
was wrong. It is the only repo on the standalone package, and the assumption here
was that its lock resolved to some 2.x, making `>=2.0,<3` the conservative freeze.
It does not: the lock already resolves to **fastmcp 3.4.4**, and the server imports
and registers both tools cleanly against it. Freezing to `<3` would have been a
downgrade away from the known-good state rather than a preservation of it, so the
ceiling landed at `>=3.0,<4` — the plan's other option, and the one that matches
what actually runs.

The lesson generalises: read the resolved lock, not the spec, before deciding
which side of a major to freeze on.

### Regression guard

The pin alone is not the deliverable. Propagate the import-level test already
proven in `pycode_kg/tests/test_mcp_server.py` (itself ported from `agent_kg`)
to every repo that lacks one. It catches exactly the failure mode at issue: a
module-level `FastMCP(...)` construction plus decorator registration means an
incompatible `mcp` breaks at import, invisibly to anyone with a lock file.

Minimum per repo:

- module imports cleanly
- the specific import path the server depends on exists, asserted directly so the
  failure names the incompatibility rather than surfacing as an opaque `ImportError`
- the console-script target resolves and is callable
- registered tool count matches the number documented in the README and MCP docs

Three wrinkles surfaced while propagating it, all worth carrying into Phase B:

**An import-level test is the wrong shape where the server is built in a factory.**
`Metabo_kg` constructs `FastMCP` inside `create_server()` behind a function-level
import, so importing `metabokg.mcp_tools` succeeds against any `mcp` and the test
passes while `metabokg mcp` is dead on arrival. Its test calls `create_server()`
for real. This is the same trap kgrag hit with `_make_server()`, and the rule is:
**test at the layer where the server object is actually constructed** — see the
"Built at" column above.

`MetaKG.__init__` only resolves paths, so building a throwaway server in a test
opens no database and costs nothing. Check that holds before copying the pattern.

**Where the MCP dep lives in an extra, `importorskip` is correct, not a cop-out.**
`gutenberg_kg` (`mcp` extra) guards with `pytest.importorskip`, matching that
repo's existing idiom for extra-gated tests. This does not weaken the guard: it
skips only when the package is absent *entirely*, and still fails when it is
present at an incompatible major, because the vanished import path is asserted
separately. That is precisely the case the pin exists to catch.

**But an extra-gated MCP dep is often the real bug.** `tscode_kg` started this way
and the guard was inert where it mattered: CI installs `--extras dev`, which never
included `kg`, so the test skipped in the only place it ran unattended. The
underlying problem was worse than the test — `[project.scripts]` advertised
`tscodekg-mcp` unconditionally while `mcp` sat behind an extra, so a base install
shipped a command that could not run. Promoting `mcp` alone would not have fixed
it either, since `mcp_server.py` also imports `kg_utils.semantic` and
`tscode_kg.kg` at module level.

The `kg` extra was therefore dissolved into core dependencies, bringing tscode_kg
in line with the seven other repos that already carry `mcp` in core. Before
reaching for `importorskip`, check whether the extra is load-bearing or just
drift: if the repo declares an MCP console script, the dependency belongs in core.
gutenberg_kg keeps its extra legitimately — it declares `gutenkg-mcp` too, so it
is arguably the same bug, but its `fastmcp` stack is genuinely optional to the
corpus tooling. Left as a follow-up rather than folded in here.

**A version ceiling on a sibling can hide a CVE.** Lifting tscode_kg's
`kgmodule-utils` floor to `>=0.9.0` made poetry refuse to solve at all:
kgmodule-utils 0.9.0 requires `transformers>=5.5.0,<6`, while `pycode-kg` 0.20.0
caps `transformers<4.57`. tscode_kg pinned `pycode-kg>=0.20.0,<0.21`, so that
ceiling had been quietly holding the repo on the pre-CVE `transformers` line —
the same one unpinned across the rest of the fleet weeks earlier. Nothing
surfaced it until an unrelated floor bump forced the resolver to speak up.

The fix was not to raise the sibling pin but to stop declaring it. tscode_kg
never imports `pycode_kg`: PyCodeKG indexes its Python source from the outside,
through the `pycodekg` CLI in the pre-commit hook, which needs the binary on disk
rather than a resolved dependency edge. Declaring it forced poetry's universal
resolution to reconcile every published sibling's `transformers` pin against this
project's own. `agent_kg` had already reached the same conclusion and documents
it in its own `pyproject.toml`. Install such tools by hand:
`poetry run pip install pycode-kg`.

The general rule for this family: **a cross-KG sibling that is only ever invoked
as a CLI does not belong in `dependencies`.** Declaring it buys nothing and
couples your resolvable version range to theirs.

### Verification

Per repo, in a throwaway environment rather than the dev environment:

1. `poetry lock && poetry install`
2. `poetry run pytest tests/test_mcp_server.py`
3. `poetry run <prog>-mcp --help`
4. Build the wheel and read back `Requires-Dist` to confirm the ceiling reaches
   published metadata — the check that caught this in pycode_kg.

Ship as patch releases.

### Explicitly not in Phase A

kgrag and agent_kg need no change. Both are already bounded and both use the
lowlevel `Server` API that 2.0 left intact.

---

## 3. Phase B — shared MCP layer in kgmodule-utils

**Priority:** high, but strictly after Phase A. **Complexity:** moderate.
**Dependencies:** Phase A complete and released — **now satisfied**, so B.1 is
unblocked and is the next thing to start.

The goal is not to reduce line count. It is to make the *next* `mcp` major a
single-file change instead of a nine-repo scramble.

### Design: a toolkit, not a framework

Add `kg_utils/mcp/` behind a new `mcp` extra in `KG_utils/pyproject.toml`, keeping
the core dependency-free.

**`kg_utils/mcp/_compat.py` — the piece that actually earns its place.**

```python
try:
    from mcp.server import MCPServer as _ServerClass      # mcp >= 2.0
except ImportError:                                        # pragma: no cover
    from mcp.server.fastmcp import FastMCP as _ServerClass  # mcp 1.x
```

In 1.x, `mcp.server.__init__` exports `Server` and `NotificationOptions` but not
`MCPServer`, so the fallback triggers cleanly. Both classes take `name` and
`instructions`, both expose `.tool()` as a decorator factory, and both expose
`.run(transport=...)` — so one `make_server(name, *, instructions)` function
spans both eras, and the ceiling can be widened to `<3` once verified.

**`kg_utils/mcp/bootstrap.py` — the shared boilerplate, as discrete helpers:**

- `add_standard_args(parser)` — `--repo`, `--db`, `--lancedb`, `--vectors-path`,
  `--model`, `--transport`
- `resolve_paths(args)` — the repeated absolute-or-relative-to-repo resolution
- `warn_if_missing(db, build_cmd)` — the stderr warning
- `print_banner(title, fields)` — the aligned stderr startup block

Each repo's `main()` keeps calling these itself and stays readable. The deliberate
alternative — a `run_kg_server(server, config, factory)` that inverts control and
owns `main()` outright — would save roughly forty more lines per repo but couples
every server's startup path to a kg_utils release. Given the family's
simplicity-first rule, prefer the toolkit; revisit only if the duplication that
remains proves to actually churn.

### What moves and what does not

**Moves:** the `FastMCP`/`MCPServer` import and construction, argparse, path
resolution, the banner, the missing-database warning.

**Stays:** every `@mcp.tool()` function body, the `_kg` singleton and `_get_kg()`
(the KG type differs per repo), and all per-repo default relation strings.

Expected outcome: doc_kg, memory_kg, and diary_kg drop to roughly 60 lines each.
pycode_kg and tscode_kg shed maybe 80 lines apiece out of ~1800 and ~1400 — for
them the win is the shim, not the line count.

### Scope

**In:** pycode_kg, tscode_kg, Metabo_kg, doc_kg, memory_kg, diary_kg — the six on
the `mcp.server.fastmcp` family.

**Out:** kgrag and agent_kg. They use the lowlevel `Server` API, which 2.0 left
untouched, making them simultaneously the least broken and the most structurally
different. Converting them is a separate optional cleanup, not part of this.

**Out:** gutenberg_kg, until a decision is made about whether the family
standardises on the SDK's `MCPServer` or the standalone `fastmcp`. Folding it in
before that decision means writing the shim twice.

### Rollout order

Forced by the dependency direction:

1. `kgmodule-utils` 0.10.0 with `kg_utils.mcp` and the `mcp` extra, released to PyPI.
2. Per repo, one at a time: bump the floor to `kgmodule-utils[mcp]>=0.10.0`, port
   `mcp_server.py`, run the import-level tests from Phase A, release.
3. Start with doc_kg — smallest, four tools, and the diff against memory_kg is
   already understood. It validates the shape before pycode_kg and tscode_kg,
   which have nineteen tools each.
4. Once all six are ported and verified against a real mcp 2.0 install, widen the
   ceiling to `<3` in one coordinated wave.

### Risk

`kgmodule-utils` becomes release-critical for MCP: a bad 0.10.0 breaks nine
servers simultaneously rather than one. Two mitigations — keep `kg_utils.mcp`
importable without the extra installed failing at *call* time rather than import
time, and make the import-level tests from Phase A a required check in each repo
before its floor bump lands.

Version skew is the second cost. Repos currently pinned at `kgmodule-utils>=0.8.0`
will not pick up a fix until each bumps its floor. Consolidation reduces the depth
of each future change, not the number of repos touched.

---

## 4. Rejected: migrate to standalone `fastmcp`

Following gutenberg_kg's lead across the family was considered and set aside.

**For:** single upstream, actively developed, richer feature set — auth, proxying,
server composition.

**Against:** it swaps one moving target for another that just went 2.x to 3.x on
its own schedule; it still sits on top of `mcp`; and it does not remove the need
for a version ceiling. The official SDK's `MCPServer` is the same ergonomic layer
folded back into `mcp`, so tracking the SDK means tracking one package instead of
two. Revisit only if a specific `fastmcp` 3.x feature is needed.

---

## 5. Summary

| Phase | Deliverable | Priority | Depends on |
|---|---|---|---|
| A | ✅ **Shipped.** Ceilings on 6 repos + MCP regression tests everywhere; 6 releases, 4 published | Urgent | — |
| B.1 | `kgmodule-utils` 0.10.0 with `kg_utils.mcp` shim + bootstrap helpers | High | ✅ A satisfied |
| B.2 | Port 6 repos, doc_kg first | High | B.1 |
| B.3 | Coordinated widening to `mcp<3` | Medium | B.2 |
| — | Convert kgrag/agent_kg off lowlevel `Server` | Optional | B.2 |
| — | gutenberg_kg 2.x→3.x, or fold into the shim | Optional | B.3 |
