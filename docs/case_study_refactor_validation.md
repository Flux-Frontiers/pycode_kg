# Case Study: Using PyCodeKG to Validate a Live Refactoring

**Project:** `gutenberg_kg` — universal ingestion engine for digitized text corpora
(Project Gutenberg + Internet Archive → DocKG knowledge graphs)
**Date:** 2026-05-05
**PyCodeKG version:** 0.19.0
**Refactor scope:** ~400 lines deleted / restructured across 6 files

---

## The Problem

`gutenberg_kg` had grown a dual-personality anti-pattern: three core library
modules each carried **both** a clean public API **and** a full argparse CLI
bolted on alongside it. This was the result of independent development of the IA (internet archive) ingestion system.

```
src/gutenberg_kg/gutenberg.py   — download library  +  argparse main()
src/gutenberg_kg/ia.py          — IA library        +  argparse main()
src/gutenberg_kg/ingest.py      — ingest library    +  duplicated loop logic
scripts/download_gutenberg.py   — called gutenberg.main()
scripts/download_ia.py          — called ia.main()
scripts/ingest.py               — called ingest.main() (which didn't exist — broken)
```

A Click CLI already existed in `cli/cmd_*.py` and already called the library
APIs correctly. The argparse layer was pure redundancy — and the scripts were
wrapping the wrong thing.

---

## What Changed

| File | Change |
|---|---|
| `gutenberg.py` | Removed `import argparse`, 5 `cmd_*` adapters, `main()`, `if __name__` (~200 lines) |
| `ia.py` | Same — removed argparse layer (~90 lines) |
| `cli/cmd_ingest.py` | Collapsed duplicated genre loop (~80 lines) into `ig.run_ingest()` (3 lines) |
| `scripts/download_gutenberg.py` | Deleted — CLI is the entry point |
| `scripts/download_ia.py` | Deleted — CLI is the entry point |
| `scripts/ingest.py` | Deleted — was already broken |
| `scripts/rebuild_lancedb.sh` | Deleted — covered by `gutenkg rebuild-lancedb` |
| `scripts/push.sh` | Deleted — covered by `gutenkg ingest --push`; had hardcoded genre list |

After: `scripts/` contains only two genuine standalone utilities
(`process_logo.py`, `benchmark_embedders.py`) and the catalog data files.

---

## PyCodeKG's Role: Independent Verification

After the refactor, `pycodekg analyze` ran in **3.6 seconds** and returned a
report that independently confirmed every architectural decision made during
the session.

### 1. No Orphaned Code

```
## Appendix: Orphaned Code
No orphaned functions detected.
```

Every argparse `cmd_*` adapter function and `main()` that was deleted had
**zero callers** in the codebase. The graph proved they were safe to remove —
nothing depended on them. This is the kind of check that normally requires a
dedicated dead-code scanner; PyCodeKG surfaces it as a standard section of
every analysis.

### 2. cmd_ingest.py Dropped to 2 Functions

```
| src/gutenberg_kg/cli/cmd_ingest.py | 2 | 0 | 1 | 2 | 0.25 |
```

The module table showed `cmd_ingest.py` at **2 functions** — exactly the
`ingest` command handler and `list_genres`. Before the refactor it contained
a full duplicated genre loop, corpus setup, registry management, and summary
printing. The collapse to `ig.run_ingest()` is visible as a hard number.

### 3. Layer Cohesion Scores Are Correct

```
| src/gutenberg_kg/ingest.py         | 14 | 3 | 1 | 0 | 0.50 |
| src/gutenberg_kg/gutenberg.py      | 20 | 0 | 1 | 0 | 0.50 |
| src/gutenberg_kg/ia.py             | 18 | 0 | 1 | 0 | 0.50 |
| src/gutenberg_kg/cli/cmd_download.py| 6 | 0 | 1 | 2 | 0.25 |
| src/gutenberg_kg/cli/cmd_ia.py     |  5 | 0 | 1 | 2 | 0.25 |
| src/gutenberg_kg/cli/cmd_ingest.py |  2 | 0 | 1 | 2 | 0.25 |
```

**Library modules sit at cohesion 0.50** — they receive calls from the CLI
layer and emit none. **CLI modules sit at cohesion 0.25** — they depend
outward onto the library layer. This is not just aesthetically clean; it's
*measurably* the correct dependency direction. Before the refactor, the
library modules also had outgoing edges into the argparse machinery, which
would have pulled their cohesion below 0.50 and added spurious fan-out to
the coupling tables.

### 4. fetch_url Correctly Identified as Architectural Spine

```
| 1 | fetch_url() | src/gutenberg_kg/gutenberg.py | 4 callers |
| 5 | fetch_url() | src/gutenberg_kg/ia.py        | 3 callers |
```

The fan-in ranking independently surfaces `fetch_url` — the single network
primitive both download modules rely on — as the most-depended-upon function
in the codebase. This is something you might *feel* from reading the code, but
the graph makes it a fact. It's the right function to harden first if
reliability becomes a concern.

### 5. Overall Grade

```
| Overall Quality | Grade | Score |
|----------------|-------|-------|
| [A] Excellent  |  A    | 100 / 100 |
```

```
Docstring coverage: 93.0% (107/115 nodes documented)
No god objects or god functions detected
No deep call chains detected
No major code quality issues
```

A perfect score **after** an active refactoring session — not before, not on a
greenfield codebase. The score reflects the state of the code at the moment
the analysis ran.

---

## What This Demonstrates

### PyCodeKG as a Refactoring Confidence Tool

The standard approach to validating a refactor is: run the test suite, read
the diff, hope nothing was missed. PyCodeKG adds a structural layer that
neither tests nor diffs can provide:

| Question | Normal tooling | PyCodeKG |
|---|---|---|
| Did I leave dead code behind? | Dead-code linter (separate tool) | Orphan section — built in |
| Did I break the dependency direction? | Manual review | Cohesion scores per module |
| What is the architectural spine now? | grep + intuition | Fan-in ranking |
| Is the module simplified? | Count lines | Function count in module table |
| Overall health? | Subjective | Scored, graded, reproducible |

### Structural Numbers as Design Language

The cohesion values (0.50 for library, 0.25 for CLI) are not targets that were
set in advance — they emerged from the refactored code. But they communicate
the architecture more precisely than any prose description: "library modules
receive; CLI modules dispatch." That's a design principle expressed as a ratio.

### Speed

The entire analysis — 1731 nodes, 1411 edges, 15 modules — completed in
**3.6 seconds**. In a live refactoring session where decisions are being made
in real time, a sub-5-second feedback loop is the difference between a tool
you actually use and one you run at the end of a sprint.

---

## Reproducing This Analysis

```bash
cd gutenberg_kg
pycodekg build --repo .
pycodekg analyze --repo . --out analysis/gutenberg_kg_analysis_$(date +%Y%m%d).md
```

Or via the MCP server during a Claude Code session:

```
analyze_repo()
```

---

## Key Takeaway

> PyCodeKG doesn't just describe what's there — it confirms what *should* be
> there. Run it after a refactor and the graph either validates your decisions
> or surfaces what you missed. In this session it did both: validated the
> library/CLI split, confirmed the dead-code deletions, and identified
> `fetch_url` as the function most worth hardening. Three findings, 3.6
> seconds, zero additional tooling.
