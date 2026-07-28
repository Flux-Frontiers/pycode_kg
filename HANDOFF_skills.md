# Handoff: auditing doc/config drift after a breaking migration

**From:** `pycode_kg` (v0.20.0 LanceDB → sqlite-vec migration cleanup, PRs #14 / #15)
**To:** agents working in `doc_kg`, `ftree_kg`, `memory_kg`, `Metabo_kg`, `agent_kg`, `diary_kg`, `gutenberg_kg`, `ia_kg`, `kgrag`, `KG_utils`, `tscode_kg`
**Date:** 2026-07-28

---

## ⚠️ Read this first: do NOT find-replace `lancedb`

`pycode_kg` migrated off LanceDB to sqlite-vec, so its LanceDB references were stale. **Most sibling repos have not migrated.** A blind sweep would break them.

Measured state at time of writing (`pyproject.toml`, core dependencies):

| Repo | Vector backend declared | LanceDB references are… |
|---|---|---|
| `pycode_kg` | `kgmodule-utils[semantic,sqlite-vec,viz]`, no lancedb | **stale** — swept in #14 |
| `gutenberg_kg` | `kgmodule-utils[synthesis,sqlite-vec]`, no lancedb | **probably stale** — audit |
| `doc_kg` | `lancedb>=0.29.0` **and** an `sqlite-vec` extra | **mixed** — audit carefully |
| `ftree_kg` | `lancedb>=0.29.0` core | **probably correct — leave alone** |
| `memory_kg` | `lancedb>=0.29.0` core | **probably correct — leave alone** |
| `Metabo_kg` | `lancedb>=0.29.0` core | **probably correct — leave alone** |
| `agent_kg`, `diary_kg` | `lancedb>=0.29.0` core | **probably correct — leave alone** |
| `ia_kg`, `kgrag` | neither declared directly | inherits — audit |
| `tscode_kg` | — | 0 references found |

**Verify your own repo before changing anything.** The transferable asset here is the *method*, not the rename.

---

## The problem class

A breaking change lands in `src/`. Tests pass, CI is green, the library is correct. But the change also invalidates things nothing validates:

- Markdown documentation
- Agent skill files (`.claude/skills/**`) and slash commands (`.claude/commands/**`)
- IDE config (`.vscode/mcp.json`, `.vscode/tasks.json`, `.vscode/copilot-instructions.md`)
- MCP config (`.mcp.json`, `claude_desktop_config.json`)
- Generated API docs (pdoc output)
- Helper scripts not covered by tests
- The **global** `~/.claude/` copies of skills and commands

No type checker reads Markdown. No test imports a JSON config. So these rot silently, and — because agents read them — they actively teach the wrong API. In `pycode_kg` this had already happened **three separate times** before being caught properly (`TODO.md` records the earliest).

---

## Step 0 — Establish ground truth

Do not trust documentation, including this file. Ask the code.

```bash
# What does the package actually depend on?
sed -n '/^dependencies = \[/,/^\]/p' pyproject.toml

# What subcommands actually exist?
poetry run <yourcli> --help

# What flags does each subcommand actually take?
poetry run <yourcli> <subcmd> --help

# What does the constructor actually accept?
poetry run python -c "
from your_pkg.kg import YourKG; import inspect
print(inspect.signature(YourKG.__init__))"

# What console scripts are declared?
grep -A30 '\[project.scripts\]' pyproject.toml
```

Write these down. Every later edit gets checked against them, not against memory.

---

## Step 1 — Find candidate drift

```bash
TERM='lancedb'   # or whatever your migration retired

# Live config and instructions (the stuff that breaks agents)
grep -rn -i "$TERM" .claude/ .vscode/ .mcp.json scripts/ src/ 2>/dev/null

# Documentation
grep -rn -i "$TERM" docs/ README.md assets/ 2>/dev/null

# Retired command names anywhere
grep -rn 'build-lancedb\|--lancedb\|LANCEDB_DIR\|lancedb_dir' . \
  --exclude-dir={.venv,.git,node_modules,.mypy_cache} 2>/dev/null
```

**Also run your type checker.** It catches the subset that is real code:

```bash
poetry run ty check     # or mypy/pyright
```

In `pycode_kg` this found exactly one genuine bug — `scripts/exercise_runner.py` passing a removed keyword — that greps for the *old name* would have found, but that a grep for the *new name* would not.

---

## Step 2 — Triage into four buckets

Not every hit is a defect. Sort before editing.

### A. Broken — will fail at runtime

Highest priority. In `pycode_kg`:

| Site | Symptom |
|---|---|
| `scripts/exercise_runner.py` | `TypeError` — passed removed `lancedb_dir=` kwarg |
| `.vscode/mcp.json` | `exit 2` — `unrecognized arguments: --lancedb` |
| `.vscode/tasks.json`, `.claude/commands/release.md` | `No such command 'build-lancedb'` |

**Prove each one is broken before fixing, and prove it fixed after.** Run the script. Run the binary with the exact args from the config.

### B. Stale instructions — will mislead agents

Won't crash, but teaches a non-existent API. `.claude/skills/**`, `.claude/commands/**`, `copilot-instructions.md`. Worth as much as bucket A because agents act on them.

### C. Prose — descriptive only

Architecture docs, installation guides. Fix, but they're not urgent and they're where you're most likely to introduce errors by pattern-matching.

### D. Correct as-is — **do not touch**

This bucket is larger than you expect:

- **`CHANGELOG.md`, release notes, `TODO.md`** — historical record. "We used to use X" is *true*.
- **Other projects' references.** `pycode_kg`'s `docs/case_study_refactor_validation.md` mentions `rebuild_lancedb.sh` — that's GutenbergKG's script, not ours.
- **Deliberate compatibility guards.** `tests/test_index.py` has `pytest.importorskip("lancedb")` for a backend-parity test. Intentional.
- **Published/archived artifacts.** `pycode_kg`'s `article/` holds a `.tex` plus a compiled PDF that predate the migration and were accurate when written. They're Zenodo-archived. Rewriting them retcons a citable document *and* desyncs the source from the committed PDF. **Left untouched.**
- **Upstream symbols that genuinely still exist.** See the next section.

---

## Step 3 — Watch for legacy names that are still real

The single biggest trap.

`kgmodule-utils` still ships **both** backends. So even in fully-migrated `pycode_kg`:

```python
SemanticIndex.__init__(self, lancedb_dir, *, embedder=None, table='kg_nodes', backend=None)
#                            ^^^^^^^^^^^ still literally named this
```

`lancedb_dir` is a **real parameter**, `LanceDBBackend` is a **real class**, and `tests/test_index.py:500` asserts on `idx.lancedb_dir`. "Correcting" these in docs would have documented an API that does not exist.

We **documented the inconsistency** instead of hiding it:

> The first positional parameter is still named `lancedb_dir` in `SemanticIndex.__init__` — a leftover from the pre-0.20.0 backend. It takes the *directory* holding the store (`vectors_path.parent`); the vector file itself is passed to `SqliteVecBackend`.

**Rule: before renaming a term in docs, confirm the term isn't still a real identifier.**

```bash
poetry run python -c "
from your_pkg.index import SemanticIndex; import inspect
print(inspect.signature(SemanticIndex.__init__))"
```

---

## Step 4 — Check facts, not just names

Three `pycode_kg` fixes required looking at source, and a find-replace would have gotten all three wrong:

1. **Dependency lists.** Both architecture docs listed `lancedb 0.29.0+`, plus `streamlit`/`pyvis` as core. Reality: `kgmodule-utils[semantic,sqlite-vec,viz] 0.8.0+` and friends. Read `pyproject.toml`; don't paraphrase.

2. **Half-true claims.** `INSTALLATION.md` said `build_pycodekg_sqlite` *and* `build_pycodekg_lancedb` both exist as stubs. Only the first imports; the second raises `ModuleNotFoundError`. Check each:
   ```bash
   poetry run python -c "import importlib; importlib.import_module('your_pkg.legacy_mod')"
   ```

3. **Incomplete examples.** The docs showed `SemanticIndex("./lancedb", embedder=...)`. The real build path passes `vectors_path.parent` **plus** an explicit `SqliteVecBackend(...)`, without which nothing is sqlite-vec backed. Find how your own code constructs the thing:
   ```bash
   grep -rn 'SemanticIndex(' src/
   ```

---

## Step 5 — Cross-file consistency

Config that names things declared elsewhere drifts silently. We renamed two VS Code tasks in `tasks.json` and broke `copilot-instructions.md`, which invokes them **by exact label** — reintroducing the exact bug class we were fixing (PR #15).

Validate programmatically, not by eye:

```python
import json, re
labels = {t['label'] for t in json.load(open('.vscode/tasks.json'))['tasks']}
doc    = open('.vscode/copilot-instructions.md').read()
refs   = set(re.findall(r'\*\*([A-Za-z]+KG: [^*]+)\*\*', doc))
print("broken refs :", refs - labels)
print("undocumented:", labels - refs)
```

Apply the same idea to any name crossing a file boundary: MCP tool names in skills vs. the server, CLI names in READMEs vs. `[project.scripts]`.

---

## Step 6 — Sync the GLOBAL `~/.claude/`

**Easy to miss, and it affects every project.** Repo skills are copied to `~/.claude/skills/<name>/` by `scripts/install-skill.sh`. The global copies do **not** update when you fix the repo.

`pycode_kg`'s global copies were 1–3 months stale with 9 broken references:

```bash
diff ~/.claude/skills/<name>/SKILL.md ./.claude/skills/<name>/SKILL.md
```

Repo is source of truth; copy repo → global:

```bash
R=./.claude/skills/<name>; G=~/.claude/skills/<name>
cp $R/SKILL.md $R/clinerules.md $G/
cp $R/references/*.md $G/references/
cp ./.claude/commands/setup-<name>-mcp.md ~/.claude/commands/
```

Also audit `~/.claude/settings.json` for permission entries and `additionalDirectories` pointing at repos that no longer exist. We removed **64** dead entries there.

> ⚠️ Use a negative-lookbehind when filtering, or you will delete the wrong things. `codekg` matches inside `pycodekg`; `code_kg` matches inside `pycode_kg`. Pattern used: `(?<!py)codekg|code[-_]kg`, then re-check hits containing `pycode`.
>
> ⚠️ **Back up `settings.json` first** and validate it parses afterwards — a malformed file breaks Claude Code.

---

## Step 7 — Regenerate API docs, and fix what that exposes

If you ship pdoc/sphinx output, regenerate it. It's a **detector**, not just an artifact — generated docs re-emit stale source docstrings, so a diff that still contains the old term points at `src/`.

```bash
poetry run poe docs   # check your own task name
```

This is how we found three stale strings in `pycode_kg`'s source, including a **public docstring** claiming a method *"Requires the LanceDB vector index to be available."* User-visible, wrong, and invisible to every test.

Expect residual hits from upstream symbols that legitimately exist (see Step 3) — 38 of ours were correct.

### Trap: pre-commit fights generated files

`trailing-whitespace` and `end-of-file-fixer` reformat pdoc output (412 lines in our case), and the commit fails with:

```
[WARNING] Stashed changes conflicted with hook auto-fixes... Rolling back fixes...
```

Workaround: `git add -A` again so index matches worktree, then re-commit. Real fix: exclude generated docs from those hooks, or normalize in the docs task.

---

## Verification protocol

**Execute; don't inspect.** Every claim below was earned by running something.

| Claim | How to earn it |
|---|---|
| script works | run it end-to-end, check exit code |
| CLI flag valid | `poetry run <cli> <cmd> --help`, grep the flag |
| subcommand exists | invoke it; confirm no `No such command` |
| config args accepted | run the binary with the config's exact args |
| code example works | paste it into `python -c` and run |
| dependency list right | read `pyproject.toml` |
| module exists | `importlib.import_module` it |
| labels resolve | parse both files, compare sets |
| no regression | full test suite + linter + type checker, before **and** after |

### Traps that cost us time

- **`--dry-run` proves nothing about availability.** `poetry install --dry-run` cheerfully reported `Updating torch (2.12.1 → 2.13.0+cpu)` for a wheel that does not exist on macOS. Only a real install or `pip download` catches it.
- **CI green ≠ correct.** Our Linux CI passed while macOS was broken, because the bug was platform-specific and CI only ran the working platform.
- **Empty databases produce false negatives.** A probe pointed at a non-existent `graph.db` "reproduced" a bug that wasn't there. Confirm your fixture has data (`SELECT COUNT(*) FROM nodes`).
- **Working directory persists between shell calls.** A `cd` into a comparison worktree silently made two later "before vs after" diffs compare a tree against itself, reporting a false "IDENTICAL". Use absolute paths for cross-tree comparisons.
- **Don't trust a commit message's scope.** One claimed six broken call sites; only two reproduced on current `main`. The other four were latent — real to fix, but the stated impact was wrong. Re-verify against *current* code, especially for old branches.

---

## Suggested commit structure

Keep buckets separable so a revert is surgical:

1. `fix(config):` — things that were actually broken (bucket A + B)
2. `docs:` — prose sweep (bucket C)
3. `docs:` — regenerated API docs + the source docstrings they exposed

Three commits, one PR. Squash at merge if you prefer a single commit on `main`.

---

## Checklist

- [ ] Established ground truth from code, not docs (Step 0)
- [ ] Confirmed whether your repo actually migrated — **or should keep LanceDB**
- [ ] Grepped `.claude/`, `.vscode/`, `.mcp.json`, `scripts/`, `src/`, `docs/`
- [ ] Ran type checker; fixed real code hits
- [ ] Triaged into broken / misleading / prose / correct-as-is
- [ ] Verified legacy-looking names aren't still real identifiers
- [ ] Checked dependency lists against `pyproject.toml`
- [ ] Verified every code example by executing it
- [ ] Validated cross-file name references programmatically
- [ ] Synced global `~/.claude/` skills + commands; audited `settings.json`
- [ ] Regenerated API docs; fixed source docstrings it exposed
- [ ] Left historical records, other projects' refs, and published artifacts alone
- [ ] Full test suite + linter + type checker clean, before and after

---

## Reference

- `pycode_kg` PR #14 — the migration sweep (3 commits)
- `pycode_kg` PR #15 — the follow-up cross-file label fix
- `pycode_kg` PR #13 — a related silent-failure bug (`getattr(kg, "_store")` vs the lazy `kg.store` property) worth checking for in any repo built on `KGModule`
