# PyCodeKG Exercises

Hands-on practice across all nineteen tools. Each exercise has a concrete call,
what to look for in the output, and a follow-up that builds on the result.

Work against any Python repo. The examples below use `pycode_kg` itself — run
`pycodekg build --repo .` first so the graph is current. Results from other
repos will differ in specifics but follow the same patterns.

---

## Setup

```bash
cd your-repo
pycodekg build --repo .
```

Verify the graph is live before starting:

```python
graph_stats()
```

You should see node and edge counts broken down by kind. If `total_nodes` is 0
something went wrong with the build. Check `pyproject.toml` for `exclude` settings
that might be too broad.

---

## Part 1 — Orientation

### Exercise 1.1 — Get your bearings

```python
graph_stats()
```

**What to notice:**
- Ratio of `function` + `method` to `module` nodes — tells you how many
  functions per file on average
- `CALLS` count vs `CONTAINS` count — a much higher CALLS-to-CONTAINS ratio
  means a rich call graph (good for tracing execution flow)
- Presence of `symbol` nodes — these indicate data-flow tracking is active
  (`ATTR_ACCESS`, `RESOLVES_TO` edges will be non-zero)

**Follow-up:** If `symbol` count is zero, the `PyCodeKGVisitor` may not be
active. Check your build flags.

---

### Exercise 1.2 — Find the architectural spine

```python
centrality(top=15, group_by="module")
```

**What to notice:**
- The top module is almost always an orchestrator (high outgoing edges) or a
  heavily-called utility (high incoming edges)
- Modules with low rank but high function counts are probably leaf workers
- Any `cli/` or `cmd_*` module that ranks near the top suggests the CLI layer
  is doing too much logic (it should rank lower than library modules)

**Follow-up:**
```python
centrality(top=15, group_by="node")
```
Compare: do the same modules dominate at the node level, or do surprises emerge?

---

### Exercise 1.3 — Identify bridges and hubs

```python
bridge_centrality(top=10)
```

Then:

```python
framework_nodes(top=10)
```

**What to notice:**
- `bridge_centrality` finds modules that sit between clusters — touching many
  others without necessarily being called heavily. These are the modules whose
  deletion would most fragment the graph.
- `framework_nodes` combines structural importance (SIR) with connectivity —
  the result is the modules you cannot afford to break.
- Any module that appears in **both** lists is your true architectural load-bearer.

---

## Part 2 — Exploration

### Exercise 2.1 — Semantic search, broad then narrow

```python
query_codebase("storage persistence database")
```

Note the top node IDs returned. Then narrow:

```python
query_codebase("storage persistence database", rels="CALLS")
```

**What to notice:**
- The second call restricts graph expansion to call edges only — the returned
  subgraph now shows *execution flow* toward the storage layer, not the full
  structural neighborhood
- Nodes that appear in both results are entry points to the storage layer from
  the rest of the codebase

**Follow-up:** Take one of the node IDs from the result and run:
```python
explain("fn:src/your_module.py:function_name")
```

---

### Exercise 2.2 — Find all implementations of a concept

```python
query_codebase("error handling retry backoff", hop=2)
```

**What to notice:**
- `hop=2` follows edges two levels out — you'll find not just the retry
  function itself but everything that calls it and everything it calls
- A large result at `hop=2` means the concept is widely distributed; a tight
  result means it's well-encapsulated

**Follow-up:** Try the same query with `hop=1` and compare the result sizes.

---

### Exercise 2.3 — Module structure in one call

```python
query_codebase("module_name_here", rels="CONTAINS", hop=2)
```

Replace `module_name_here` with one of the modules from Exercise 1.2.

**What to notice:**
- `CONTAINS` edges with `hop=2` give you the full module tree: module →
  class → method, module → function
- This is the fastest way to see what lives in a file without reading it

---

### Exercise 2.4 — Follow the import graph

```python
query_codebase("imports dependencies external", rels="IMPORTS")
```

**What to notice:**
- Modules that appear as destinations many times are your most-imported
  utilities — they should have the highest docstring coverage
- Any external package name in the results is a third-party dependency

---

## Part 3 — Source Reading

### Exercise 3.1 — Get source for a concept

```python
pack_snippets("query pipeline semantic search ranking")
```

**What to notice:**
- Unlike `query_codebase`, this returns actual source lines with line numbers
- The `context=5` default means you see 5 lines above and below each definition
- Results are deduplicated — the same function won't appear twice

**Follow-up:** Widen the context for a dense function:
```python
pack_snippets("query pipeline semantic search ranking", context=15)
```

---

### Exercise 3.2 — Cross-module source comparison

```python
pack_snippets("slugify normalize string identifier", max_per_module=1)
```

**What to notice:**
- `max_per_module=1` forces diversity — you'll see the top implementation from
  each module rather than five snippets from the same file
- If `slugify` appears in multiple modules with near-identical bodies, that's
  a deduplication opportunity

---

### Exercise 3.3 — Find a specific implementation

```python
pack_snippets("write reference markdown metadata sidecar", k=12)
```

**What to notice:**
- `k=12` increases the number of semantic seed nodes before graph expansion —
  useful when the first few results are adjacent to your target but not quite it
- Compare with `k=8` (the default) to see how many new nodes appear

---

## Part 4 — Pinpoint Lookups

### Exercise 4.1 — Resolve a node ID

Take any node ID from a previous query result (format:
`fn:src/module.py:function_name`) and fetch it directly:

```python
get_node("fn:src/your_module.py:your_function")
```

Then fetch with its neighborhood:

```python
get_node("fn:src/your_module.py:your_function", include_edges=True)
```

**What to notice:**
- The `include_edges=True` version returns `outgoing_edges` grouped by relation
  type and `incoming_calls` — everything `callers()` would give you, in one call
- `lineno` and `end_lineno` tell you the exact source span

---

### Exercise 4.2 — Search by name

```python
find_node("fetch", kind="function")
```

**What to notice:**
- Returns all functions whose name contains "fetch" — useful when you know the
  name but not the module
- Multiple hits with the same name in different modules signal potential naming
  inconsistency or legitimate parallel implementations

---

### Exercise 4.3 — Reverse-lookup from a line number

Open any source file, note a line number, then:

```python
find_definition_at("src/your_module.py", 42)
```

**What to notice:**
- Returns the node whose source span contains that line — works for any line
  inside a function body, not just the `def` line
- Same output shape as `explain()` — immediate context without needing to know
  the node ID first

---

## Part 5 — Fan-In and Explanations

### Exercise 5.1 — Who calls a function?

From Exercise 1.2, pick the top-ranked node by SIR. Get its callers:

```python
callers("fn:src/your_module.py:top_function")
```

**What to notice:**
- High fan-in functions are your most critical — changes break many callers
- Callers from many different modules indicate a true shared utility; callers
  all from one module suggest it belongs there, not at the top level

---

### Exercise 5.2 — Understand a function completely

```python
explain("fn:src/your_module.py:top_function")
```

**What to notice:**
- **Role** — kind, module, exact location
- **Called By** — top 10 callers with module paths
- **Calls** — what this function depends on
- The Calls list is your dependency footprint for this function — anything
  there that is also high fan-in is a double risk point

---

### Exercise 5.3 — Trace a class

```python
explain("cls:src/your_module.py:YourClass")
```

Then enumerate its methods:

```python
list_nodes("src/your_module.py", kind="method")
```

**What to notice:**
- The class `explain` gives you the class-level view; `list_nodes` fills in
  every method in one call
- Methods that appear in `callers()` results for other functions are the class's
  effective public API regardless of naming convention

---

## Part 6 — Structural Ranking (CodeRank)

### Exercise 6.1 — Global PageRank

```python
rank_nodes(top=25)
```

**What to notice:**
- This is pure structural importance — no semantic query involved
- The top nodes are the ones whose removal would most damage the call graph
- Compare with `centrality(top=25, group_by="node")` — they should broadly
  agree, with minor differences from edge weighting

---

### Exercise 6.2 — Structure-aware semantic search

```python
query_ranked("database connection storage", mode="hybrid")
```

Then:

```python
query_ranked("database connection storage", mode="ppr")
```

**What to notice:**
- `hybrid` blends 0.60×semantic + 0.25×centrality + 0.15×proximity —
  results are semantically relevant AND structurally important
- `ppr` weights 0.70×personalized PageRank + 0.30×semantic — useful when
  you want results that are *topologically close* to the query concepts
- The two modes return different orderings; neither is always better

---

### Exercise 6.3 — Explain a ranking

Take the top node from Exercise 6.1 and explain why it ranked there:

```python
explain_rank("fn:src/your_module.py:top_function")
```

Then explain in the context of a query:

```python
explain_rank("fn:src/your_module.py:top_function", q="database connection")
```

**What to notice:**
- The first call explains *structural* rank (inbound count, global PageRank score)
- The second adds the semantic similarity score for the query — you can see
  exactly how much each component contributed to the final rank

---

## Part 7 — Architecture Analysis

### Exercise 7.1 — Full health check

```python
analyze_repo()
```

This is the full nine-phase analysis. **What to look for:**

| Section | Red flag |
|---|---|
| Fan-In Ranking | Same function at top across multiple query types |
| High Fan-Out | Any function calling 10+ others |
| Module Cohesion | CLI modules with cohesion ≥ 0.5 (doing too much) |
| Orphaned Code | Any production function with zero callers |
| Docstring Coverage | Any module below 80% |
| Key Call Chains | Depth > 8 indicates brittle sequential coupling |
| Overall Grade | Anything below B warrants immediate attention |

---

### Exercise 7.2 — Validate the layer boundary

After running `analyze_repo()`, check the module cohesion table.

**Expected pattern for a well-layered codebase:**

| Layer | Expected cohesion |
|---|---|
| Library / domain modules | ~0.50 (receive calls, emit none) |
| CLI / adapter modules | ~0.25 (emit calls to library, receive from entry point) |
| Entry points (`main`, `cli`) | ~0.10–0.20 (mostly outgoing) |

If a library module has cohesion < 0.40, it has too many outgoing edges —
it's doing orchestration it shouldn't own. If a CLI module has cohesion > 0.40,
it's implementing logic it should delegate.

---

## Part 8 — Temporal Tracking

### Exercise 8.1 — Survey the snapshot history

```python
snapshot_list()
```

**What to notice:**
- Each entry has a tree-hash `key` — use these in `snapshot_show` and
  `snapshot_diff`
- The `deltas` field shows node/edge change vs. the previous snapshot —
  a sudden spike in nodes often means a new module was added
- If the list is empty: run `pycodekg install-hooks` to enable automatic
  snapshot capture on commit

---

### Exercise 8.2 — Inspect a snapshot

```python
snapshot_show("latest")
```

**What to notice:**
- `hotspots` lists the functions that were most complex at that point in time
- `coverage` shows docstring coverage as a percentage — compare across
  snapshots to track documentation discipline

---

### Exercise 8.3 — Before/after comparison

```python
# Get two keys from snapshot_list()
snapshot_diff("older_key", "newer_key")
```

**What to notice:**
- `delta.total_nodes` and `delta.total_edges` show raw growth
- `delta.coverage` shows whether documentation improved or regressed
- `delta.critical_issues` moving from 0 to positive means something was
  introduced that the analyzer flags as a concern

---

## Part 9 — Data Flow (Advanced)

### Exercise 9.1 — Attribute access patterns

```python
query_codebase("self attribute property access", rels="ATTR_ACCESS", include_symbols=True)
```

**What to notice:**
- `ATTR_ACCESS` edges connect variable symbols to the attributes accessed on them
- `include_symbols=True` is required to surface `symbol`-kind nodes — without
  it, the results are filtered to functions and classes only

---

### Exercise 9.2 — Variable resolution

```python
query_codebase("variable assignment name binding resolved", rels="RESOLVES_TO", include_symbols=True)
```

**What to notice:**
- `RESOLVES_TO` edges map local variable symbols to the definition nodes they
  resolve to — this is how you trace a variable back to where it was defined
- A high `RESOLVES_TO` count in `graph_stats()` means import-aware name
  resolution is active and call-graph accuracy is high

---

## Part 10 — Refactor Validation (Capstone)

This is the full workflow used to validate the `gutenberg_kg` refactor described
in `case_study_refactor_validation.md`. Apply it to any codebase before and
after a structural change.

### Step 1 — Snapshot before

```bash
pycodekg snapshot save pre-refactor
```

### Step 2 — Check for existing dead code

```python
analyze_repo()
# Read the "Orphaned Code" section
```

Functions with zero callers that you *intend* to delete are confirmed safe.
Functions with zero callers you didn't know about are candidates for removal.

### Step 3 — Check current cohesion

```python
analyze_repo()
# Read the "Module Architecture" table — note cohesion per module
```

Write down the cohesion values for every module you plan to touch.

### Step 4 — Make your changes

### Step 5 — Rebuild

```bash
pycodekg build --repo .
```

### Step 6 — Re-run analysis

```python
analyze_repo()
```

**What to confirm:**
- "Orphaned Code" section: still empty (you didn't accidentally strand anything)
- Module cohesion: library modules stayed at ~0.50, CLI modules stayed at ~0.25
- Function counts per module: the simplified module shows fewer functions
- Overall grade: should be equal or better

### Step 7 — Snapshot after and diff

```bash
pycodekg snapshot save post-refactor
```

```python
snapshot_list()
# Copy the two keys
snapshot_diff("pre-refactor-key", "post-refactor-key")
```

**What to read:**
- `delta.total_nodes` negative → you removed code (expected for dead-code cleanup)
- `delta.coverage` positive → documentation improved (or at least didn't regress)
- `delta.critical_issues` zero or negative → no new problems introduced

---

## Quick Reference — Tool Selection

| I want to… | Use |
|---|---|
| Get oriented in an unfamiliar codebase | `graph_stats()` then `centrality(group_by="module")` |
| Find what a concept maps to in code | `query_codebase(q)` |
| Read the actual source | `pack_snippets(q)` |
| Look up a specific function | `get_node(node_id)` or `find_node(name)` |
| Find what depends on a function | `callers(node_id)` |
| Understand a function completely | `explain(node_id)` |
| Find the most critical module | `framework_nodes()` |
| Find an architectural bridge | `bridge_centrality()` |
| Run a structure-weighted search | `query_ranked(q, mode="hybrid")` |
| Explain why something ranked high | `explain_rank(node_id, q)` |
| Validate a refactor | `analyze_repo()` before + after |
| Track change over time | `snapshot_diff(key_a, key_b)` |
