# Session handoff — 2026-07-29

Two parallel workstreams across the KGRAG fleet. Read this before resuming.

**Companion docs (both in `pycode_kg/`):**
- [`MIGRATION-sqlite-vec.md`](MIGRATION-sqlite-vec.md) — the LanceDB → sqlite-vec playbook, with 11 hard-won learnings
- [`handoff_skills.md`](handoff_skills.md) — how to sweep docs/config drift after a migration

---

## ⚠️ Immediate: unfinished business

1. **`kgrag` tag `v0.11.0` is NOT pushed.** The release commit (`2549338`) and the
   recovery commit (`ab0c516`) are both on `main` and pushed. Tag when ready:
   ```bash
   cd ~/repos/kgrag && git tag -a v0.11.0 -m "v0.11.0" && git push origin v0.11.0
   ```
   That triggers `release.yml` → builds wheel+sdist → creates a GitHub Release from
   `release-notes.md`. **It does not publish to PyPI** (manual `poetry publish`).

   ⚠️ **`release-notes.md` and the `[0.11.0]` changelog were written BEFORE the
   recovery commit.** They describe the mcp pin as shipped, which is now true again —
   but neither mentions the `ftree_adapter` fix in `ab0c516`. Consider amending the
   changelog before tagging.

2. **`memory_kg` PR #9 is open and green** — not merged. After merging, it needs a
   `0.6.1` release (user asked for this explicitly).
   https://github.com/Flux-Frontiers/memory_kg/pull/9

3. **`doc-kg 0.19.0` needs yanking** on PyPI (0.19.1 is published and live).
   PyPI has no yank API — web UI only:
   pypi.org/manage/project/doc-kg/releases/ → 0.19.0 → Options → Yank.

---

## Workstream 1: `mcp<2` pin — essentially complete

mcp 2.0 broke **every** MCP server in the fleet, in two different ways:

| API | Under mcp 2.0 | Fails at | Repos |
|---|---|---|---|
| `mcp.server.fastmcp.FastMCP` | module unbundled into standalone `fastmcp` pkg | **import** | pycode_kg, doc_kg, memory_kg, Metabo_kg, diary_kg |
| `mcp.server.Server` decorators | class survives, `@server.list_tools()` removed | **call** | kgrag |

**The pin is not copy-pasteable** — the test shape differs. FastMCP repos get an
import-level test; kgrag needs one that actually calls `_make_server()`, because it
builds its server inside a function and an import-only test passes while the server
is broken.

### Status

| Package | PyPI | Pin | Notes |
|---|---|---|---|
| `pycode-kg` | **0.21.1** | ✅ | 0.21.0 yanked |
| `agent-kg` | **0.8.1** | ✅ | 0.8.0 deleted (never published) |
| `doc-kg` | **0.19.1** | ✅ | **0.19.0 still needs yanking** |
| `kg-rag` | 0.10.0 | ✅ on main | 0.11.0 pending tag+publish |
| `memory-kg` | 0.6.0 | ✅ PR #9 | needs merge + 0.6.1 |
| `Metabo_kg`, `diary_kg` | unpublished | ❌ | **pin before next publish** |

---

## Workstream 2: LanceDB → sqlite-vec — 4 of 8

| Repo | Status |
|---|---|
| `pycode_kg` · `gutenberg_kg` · `ftree_kg` (v0.9.0) · `agent_kg` (0.8.1) | ✅ done |
| `diary_kg` | 30 src refs — adapter *mirrors* KGModule, doesn't subclass → hand-port |
| `Metabo_kg` | 151 refs, 251-line `index.py` |
| `memory_kg` | 114 refs, **738-line** `index.py` fork |
| `doc_kg` | 213 refs, **1615-line** fork — **user said do this LAST** |
| `kgrag` | registry only — **final step**, once every KG reports `vectors_path` |

**User's instruction: "do the easy ones first" — `doc_kg` is explicitly deferred.**

Next candidate is `diary_kg` (fewest refs) but **verify before committing to it**:
`grep -rn 'class .*(KGModule)' src/` — only `ftree_kg` had a real subclass. Everything
remaining is hand-rolled, so expect `agent_kg`-shaped work (port read/write paths), not
`ftree_kg`-shaped (flag flip).

All 12 `.agentkg` stores were converted and their `lancedb/` dirs removed (~440 MB).
`.dockg` is now the largest remaining footprint and won't convert until `doc_kg` does.

---

## Mistakes I made — do not repeat

1. **A commit silently dropped its staged files.** `b7d2a34` was titled "pin mcp<2"
   and contained *only the test file*. `pyproject.toml`, `CHANGELOG.md`, `poetry.lock`
   were staged and lost — most likely the pre-commit hook's stash/restore cycle
   rewriting the tree between `git add` and commit. **The commit succeeded and tests
   passed**, so nothing surfaced it. It only came to light when `poetry update`
   downgraded pycode-kg to 0.20.0 (the stale `transformers<4.57` made 0.21.1
   unsatisfiable). Recovered in `ab0c516`.
   → **After every commit in a repo with heavy pre-commit hooks, verify contents:**
   `git show HEAD --stat` and grep the actual change, not the exit status.

2. **`VIRTUAL_ENV` leaked across repos.** My shell inherited
   `VIRTUAL_ENV=/Users/egs/repos/pycode_kg/.venv`, and `poetry run` honours it — so
   every poetry call inside `kgrag` silently used pycode_kg's environment. I concluded
   kgrag's hooks were "misconfigured and reaching into sibling repos." **They were
   fine.** → Use `env -u VIRTUAL_ENV` for any poetry/pytest call outside `pycode_kg`.

3. **`pip index versions` serves a stale cache.** It told me pycode-kg was on 0.20.0
   when 0.21.0 was already published, and hid agent-kg 0.8.1. → Always use the JSON API:
   `curl -s "https://pypi.org/pypi/<pkg>/json?$(date +%s)"`. Also allow ~20s propagation
   before contradicting a "just published" claim.

4. **A persisted `cd`** made two "before vs after" diffs compare a tree against itself
   and report a false IDENTICAL. → Absolute paths for cross-tree comparisons.

5. **`git checkout -- <file>` wiped uncommitted work** while I was reverting a probe.
   → Stash instead when the file holds unrelated edits.

---

## Cross-repo breakage to watch

`ftree_kg` 0.9.0's rename (`lancedb_path` → `vectors_path`) broke **kgrag's own
FileTreeKG adapter** — `ftree_adapter.py:42` passed a parameter that no longer exists,
a `TypeError` on every FileTree query. Invisible until the `ftree-kg` floor was raised.
Fixed in `ab0c516`.

**Each migration will do this again.** After migrating repo X, grep kgrag's adapters
for X's constructor and check the signature:
```bash
grep -rn "lancedb_path\|lancedb_dir" ~/repos/kgrag/src/kg_rag/adapters/
```

Also note `kgrag/src/kg_rag/cli/cmd_health.py:92` still probes code KGs with
`codekg query --sqlite {sqlite} --lancedb {lancedb}` — `codekg` is the **retired**
predecessor of pycode_kg and is not on PATH, so every code-KG liveness probe silently
fails. Unfixed. The `doc`/`memory` entries below it will need `--lancedb` → `--vectors`
once those repos migrate.

---

## Environment notes

- Always `env -u VIRTUAL_ENV` outside `pycode_kg`.
- `pycodekg build` has **no `--wipe` flag** — full build always wipes. `build-sqlite`
  and `build-index` still take it; `ftreekg build` uses `--no-wipe` to opt out.
- Pre-commit hooks in these repos run full PyCodeKG + DocKG builds and can take
  60–90s per commit.
- Releases: tag → GitHub Release only. **PyPI publish is always manual** (`poetry publish`).
