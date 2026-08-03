# Session handoff — 2026-07-29

State of the KGRAG fleet after a long session. **Workstream 1 (`mcp<2`) is done,
released, and published.** Workstream 2 (LanceDB → sqlite-vec) is the next job and
has not been touched today.

**Companion docs (in `pycode_kg/`):**
- [`docs/MCP-CONSOLIDATION-PLAN.md`](docs/MCP-CONSOLIDATION-PLAN.md) — Phase A shipped; Phase B.1 now unblocked
- [`MIGRATION-sqlite-vec.md`](MIGRATION-sqlite-vec.md) — the LanceDB → sqlite-vec playbook, 11 hard-won learnings
- [`handoff_skills.md`](handoff_skills.md) — sweeping docs/config drift after a migration

---

## ➡️ Next step: Workstream 2 — LanceDB → sqlite-vec

Nothing else is blocking. Four KGs plus the kgrag registry remain.

| Repo | Scope (from prior session — **re-verify**) | Notes |
|---|---|---|
| `diary_kg` | ~30 src refs | adapter *mirrors* KGModule, doesn't subclass → hand-port |
| `Metabo_kg` | ~151 refs, 251-line `index.py` | |
| `memory_kg` | ~114 refs, 738-line `index.py` fork | |
| `doc_kg` | ~213 refs, **1615-line** fork | **user said do this LAST** |
| `kgrag` | registry only | **final step**, once every KG reports `vectors_path` |

Already done: `pycode_kg`, `gutenberg_kg`, `ftree_kg`, `agent_kg`, and **`tscode_kg`**
(tscode_kg's migration shipped in 0.2.0 this session).

Re-verify the counts before planning — several repos changed today:
```bash
for r in diary_kg Metabo_kg memory_kg doc_kg; do
  echo -n "$r: "; grep -rn 'lancedb\|LanceDB' ~/repos/$r/src --include=*.py | wc -l
done
```

**Start with `diary_kg`** (fewest refs), but check the shape first:
`grep -rn 'class .*(KGModule)' src/` — only `ftree_kg` had a real subclass, so expect
`agent_kg`-shaped work (port read/write paths), not `ftree_kg`-shaped (flag flip).

`.dockg` is the largest remaining disk footprint and won't shrink until `doc_kg` migrates.

---

## ✅ Workstream 1: `mcp<2` — COMPLETE, released, published

Every MCP server in the fleet is version-bounded and carries a regression test shaped
to how its server is actually constructed. Verified against the **published index**,
not local wheels: `memory-kg`, `agent-kg`, `diary-kg`, `tscode-kg` all advertise
`Requires-Dist: mcp<2,>=1.0.0`.

### Releases cut today

| Package | Version | Tag+GH Release | PyPI |
|---|---|---|---|
| `pycode-kg` | **0.21.2** | ✅ | ❌ **not published** — PyPI still on 0.21.1 |
| `memory-kg` | **0.6.2** | ✅ | ✅ |
| `agent-kg` | **0.8.2** | ✅ | ✅ |
| `diary-kg` | **0.93.4** | ✅ | ✅ |
| `tscode-kg` | **0.2.0** | ✅ | ✅ **first ever publish** |
| `Metabo_kg` | 0.9.1 | tag only (no release workflow) | ⛔ standalone, never publish |
| `gutenberg_kg` | 1.12.0 | ✅ | ⛔ standalone, never publish |

`doc-kg` 0.19.1 and `kg-rag` 0.11.0 were already done. `doc-kg 0.19.0` is now **yanked**.

**`pycode-kg` 0.21.2 is released and on pypi
### Notable per-repo outcomes

- **tscode_kg** — the `kg` extra was **dissolved into core deps** (breaking:
  `tscode-kg[kg]` is no longer a valid install target). It also **stopped declaring
  `pycode-kg` entirely**; see "sibling pins" below.
- **Metabo_kg** — needed a different test shape. It builds `FastMCP` inside
  `create_server()` behind a function-level import, so an import-only test passes while
  `metabokg mcp` is dead. Its test calls `create_server()` for real.
- **gutenberg_kg** — `fastmcp` floor moved **up** to `>=3.0,<4`, not frozen at `<3`.
  The lock already resolved 3.4.4 and worked; freezing low would have been a downgrade.

---

## 🔑 The most important thing learned today

**A version ceiling on a sibling package can hide a CVE.**

Lifting tscode_kg's `kgmodule-utils` floor to `>=0.9.0` made poetry refuse to solve:
kgmodule-utils 0.9.0 needs `transformers>=5.5.0,<6`, while `pycode-kg` 0.20.0 caps
`transformers<4.57`. tscode_kg pinned `pycode-kg>=0.20.0,<0.21` — so that ceiling had
been quietly holding the repo on the **pre-CVE transformers line**, weeks after the rest
of the fleet moved off it. Nothing surfaced it until an unrelated floor bump forced the
resolver to complain.

The fix was not to raise the sibling pin but to **stop declaring it**. tscode_kg never
imports `pycode_kg` — PyCodeKG indexes it from the outside via the `pycodekg` CLI in a
git hook, which needs the binary on disk, not a dependency edge. `agent_kg` had already
reached this conclusion independently.

**Rule for this family: a cross-KG sibling that is only ever invoked as a CLI does not
belong in `dependencies`.** Install it by hand: `poetry run pip install pycode-kg`.

⚠️ **tscode_kg's venv now needs a hand-installed `pycode-kg`** for its pre-commit hook to
work. A bare `poetry install` will not provide it.

---

## Other work completed today

### `.gitignore` normalized across all 11 repos

One canonical block everywhere. Invariant, now stated in the block itself: **databases,
vector indexes and model caches are ignored; `snapshots/` never is.**

This fixed a **real, silent data-loss bug in three repos**, caused by bare `**/.<ns>/`
patterns that swallowed snapshot directories:

| Repo | Was |
|---|---|
| `doc_kg` | 66 snapshots tracked, **101 on disk** — 35 silently discarded |
| `memory_kg` | own KG snapshots — **none ever tracked** |
| `gutenberg_kg` | DocKG snapshots — **none ever tracked** |

Artifact patterns are `**/`-prefixed (covering nested stores) while `snapshots/` stays
addressable at every depth — necessary because gutenberg_kg keeps ~250 per-book stores
under `corpus/` that must stay hidden, while Metabo_kg **tracks** snapshots in a nested
store at `data/hsa_pathways/.metabokg/snapshots/`. `.agentkg/` is the one deliberate
exception, ignored wholesale.

⚠️ **The recovered snapshots are still untracked** in doc_kg (36 items) and memory_kg.
Deliberate — committing them is a separate decision.

### Pre-commit hook ordering fixed in 4 generators

Hooks rebuilt the KG index and staged snapshots **before** running `pre-commit run`.
Since `pre-commit run` stashes and restores unstaged changes, the build's rewritten
`snapshots/manifest.json` landed *inside that stash window*. This caused two real
failures today: a restore failing with `patch does not apply` (aborting a commit whose
hooks had all reported success), and **a staged deletion of a tracked snapshot silently
entering a commit**.

All now run **checks → write-tree → build → snapshot → stage**:

| Generator | Template | Fixed | Released |
|---|---|---|---|
| `pycodekg install-hooks` | pycode_kg `cli/cmd_hooks.py` | ✅ | ✅ 0.21.2 |
| `dockg install-hooks` | doc_kg `cli/cmd_hooks.py` | ✅ | ❌ **unreleased** |
| `agentkg install-hooks` | agent_kg `cli/main.py` | ✅ | ❌ **unreleased** |
| `memorykg install-hooks` | memory_kg `cli/cmd_hooks.py` | ✅ | ❌ **unreleased** |
| hand-written | ftree_kg | already correct | n/a |

Local `.git/hooks/pre-commit` was reinstalled in pycode_kg, tscode_kg, doc_kg, agent_kg,
memory_kg — **all five verified checks-first.** Backups in the session scratchpad.

⚠️ **`memory_kg`'s skip variable was renamed** `DOCKG_SKIP_SNAPSHOT` →
`MEMORYKG_SKIP_SNAPSHOT` (it was a copy-paste artifact). The old name no longer skips.

Repos on the **pre-commit framework** hook (kgrag, diary_kg, Metabo_kg, gutenberg_kg,
KG_utils) are unaffected — their ordering lives in `.pre-commit-config.yaml`, and
Metabo_kg already sequences `kg-index` after ty/pytest.

### Tooling

- **`~/repos/publish-fleet.sh`** — new. Clears `dist/`, builds, optionally publishes.
  Dry-run by default; `--publish` requires typing `publish`. Refuses to re-upload an
  existing version, wraps every poetry call in `env -u VIRTUAL_ENV`, and reads the
  version back out of the built wheel's METADATA. **`Metabo_kg` and `gutenberg_kg` are
  hard-blocked** as standalone apps even if named explicitly.
- **`~/.claude/commands/release.md`** — Step 3 rewritten (see mistake 6 below).
- **tscode_kg's local `skills/release/` and `skills/changelog-commit/` deleted** —
  duplicates of the global commands. Policy: generic workflows live in `~/.claude/`,
  per-project specifics in the project.

---

## Deferred — decided, not forgotten

**Hook-generator consolidation.** Four near-identical templates in four codebases; one
ordering fix needed four edits and four releases. They differ only in binary name,
artifact dir, and skip variable — data, not logic. The duplication already leaked a bug
(memory_kg's `DOCKG_SKIP_SNAPSHOT`). A `kg_utils.hooks` module with one parameterized
template is the obvious fix, and it is Phase-B-shaped work.
**User called it: "tired of it, leave it for now."** Do not start this unprompted.

---

## Mistakes — do not repeat

Carried forward and still true:

1. **Commits can silently drop staged files.** Pre-commit stash/restore can rewrite the
   tree between `git add` and commit. → **After every commit, verify contents:**
   `git show HEAD --stat` and grep the actual change, not the exit status. This caught
   three bad commits today.
2. **`VIRTUAL_ENV` leaks across repos.** `poetry run` honours an inherited `VIRTUAL_ENV`.
   → `env -u VIRTUAL_ENV` for any poetry/pytest call outside the repo you're in.
3. **`pip index versions` serves a stale cache.** → Use the JSON API with a cache-buster:
   `curl -s "https://pypi.org/pypi/<pkg>/json?$(date +%s)"`. **And allow ~20s propagation**
   — I reported "only diary-kg published" when in fact all four had gone out.
4. **A persisted `cd` gives false comparisons.** → Absolute paths for cross-tree work.
   **This bit me again today**: I diffed pycode_kg's hook against itself and reported
   "identical", concluding tscode_kg had a hook it never had.
5. **`git checkout -- <file>` wipes uncommitted work.** → Stash when the file holds
   unrelated edits.

New today:

6. **The release command's version sync rewrites things that are not versions.** A
   blanket replace of the old version string corrupted, in three separate releases:
   11 historical **snapshot JSON** files; **doctests, sample CLI output and test
   fixtures**; and **status docs** where the number was a factual claim about what is
   published. It even corrupted the release skill's own worked example into
   ``0.2.0 → 0.2.0 for minor``. → `~/.claude/commands/release.md` Step 3 now separates
   *declarations* from *statements about a version* and leads with `git diff` review.
   **Read every changed line before committing a release.**
7. **`git commit` commits the index, not the working tree.** pycode_kg shipped a stale
   `.gitignore` in the normalization batch because the file had been `git add`ed earlier,
   before two later corrections. → Re-`git add` immediately before committing.
8. **Pre-commit hooks sweep artifacts into metadata-only commits.** Several release
   commits picked up 35+ snapshot files. → For version/dependency-only commits, run the
   suite explicitly, then commit with `--no-verify`, then verify with `git show HEAD --stat`.
9. **A too-narrow grep gives a confidently wrong fleet picture.** I twice concluded only
   one repo used a given hook, because I grepped for a header string each template words
   differently. Found the 4th generator on the 3rd scan. → Grep for the *behaviour*
   (`bin/pycodekg`, `pre-commit run`), not for a comment.

---

## Cross-repo breakage to watch

`ftree_kg` 0.9.0's rename (`lancedb_path` → `vectors_path`) broke **kgrag's own
FileTreeKG adapter** — a `TypeError` on every FileTree query, invisible until the floor
was raised. **Each migration will do this again.** After migrating repo X:
```bash
grep -rn "lancedb_path\|lancedb_dir" ~/repos/kgrag/src/kg_rag/adapters/
```

`kgrag/src/kg_rag/cli/cmd_health.py:92` still probes code KGs with
`codekg query --sqlite {sqlite} --lancedb {lancedb}` — `codekg` is the **retired**
predecessor of pycode_kg and is not on PATH, so every code-KG liveness probe silently
fails. **Still unfixed.** The `doc`/`memory` entries below it need `--lancedb` →
`--vectors` once those repos migrate.

---

## Environment notes

- Always `env -u VIRTUAL_ENV` outside the repo you are working in.
- `pycodekg build` has **no `--wipe` flag** — full build always wipes. `build-sqlite`
  and `build-index` take it; `ftreekg build` uses `--no-wipe` to opt out.
- Pre-commit hooks run full KG builds — 60–90s per commit. Skip with the repo's own
  variable (`PYCODEKG_SKIP_SNAPSHOT`, `MEMORYKG_SKIP_SNAPSHOT`, …). Note **Metabo_kg's
  `kg-index` hook honours no skip variable at all.**
- Releases: tag → GitHub Release only. **PyPI publish is always manual.**
- `grep` on this machine is **ugrep** — `-m1` and some GNU flags behave differently.
  Prefer `python3` for anything structured.

## Working-tree state at handoff

- `pycode_kg` — clean, on `main`
- `diary_kg` — `HANDOFF_TWO_PHASE_EMBED.md` untracked (yours)
- `tscode_kg` — `AGENTS.md` untracked (yours)
- `doc_kg` — 36 recovered snapshots untracked (deliberate)
- `memory_kg` — recovered `.memorykg/` snapshots untracked (deliberate)
- `Metabo_kg`, `gutenberg_kg`, `kgrag`, `ftree_kg`, `KG_utils`, `agent_kg` — clean
