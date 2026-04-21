# Embedder Benchmark Report

- Started (UTC): 2026-04-21T12:23:59.536927+00:00
- Completed (UTC): 2026-04-21T12:24:08.140288+00:00
- Repo: `/Users/egs/repos/pycode_kg`
- SQLite: `/Users/egs/repos/pycode_kg/.pycodekg/graph.sqlite`
- LanceDB root: `/Users/egs/repos/pycode_kg/.pycodekg/lancedb-benchmark`
- Hybrid weights: semantic=0.7, lexical=0.3

## Model: `nomic-ai/nomic-embed-text-v1.5`
- Build: 8.53s, indexed_rows=476, dim=768

### Query: `snapshot freshness comparison`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.024 | 8 | 49 | 10 | 0.922 | 0.619 | 0.533 |
| `semantic` | 0.010 | 8 | 49 | 10 | 1.000 | 0.634 | 0.333 |

#### Top nodes (hybrid)
- 1. `_snapshot_freshness` (score=1.000, sem=0.634, lex=0.667, hop=0)
- 2. `mcp_server` (score=1.000, sem=0.634, lex=0.667, hop=1)
- 3. `PyCodeKGAnalyzer._analyze_snapshots` (score=0.919, sem=0.559, lex=0.667, hop=0)
- 4. `snapshot_diff` (score=0.845, sem=0.634, lex=0.333, hop=1)
- 5. `snapshot_list` (score=0.845, sem=0.634, lex=0.333, hop=1)

#### Top nodes (semantic)
- 1. `_snapshot_freshness` (score=1.000, sem=0.634, lex=0.667, hop=0)
- 2. `_get_kg` (score=1.000, sem=0.634, lex=0.000, hop=1)
- 3. `snapshot_diff` (score=1.000, sem=0.634, lex=0.333, hop=1)
- 4. `snapshot_list` (score=1.000, sem=0.634, lex=0.333, hop=1)
- 5. `snapshot_show` (score=1.000, sem=0.634, lex=0.333, hop=1)

### Query: `missing_lineno_policy cap_or_skip fallback`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.018 | 6 | 6 | 6 | 0.989 | 0.493 | 0.000 |
| `semantic` | 0.009 | 6 | 6 | 6 | 0.989 | 0.493 | 0.000 |

#### Top nodes (hybrid)
- 1. `MainWindow.reset_picking_state` (score=1.000, sem=0.499, lex=0.000, hop=0)
- 2. `MainWindow._build_render_options` (score=0.989, sem=0.493, lex=0.000, hop=0)
- 3. `load_exclude_dirs` (score=0.989, sem=0.493, lex=0.000, hop=0)
- 4. `MainWindow.reset_actor_appearances` (score=0.986, sem=0.491, lex=0.000, hop=0)
- 5. `_default_report_name` (score=0.982, sem=0.490, lex=0.000, hop=0)

#### Top nodes (semantic)
- 1. `MainWindow.reset_picking_state` (score=1.000, sem=0.499, lex=0.000, hop=0)
- 2. `MainWindow._build_render_options` (score=0.989, sem=0.493, lex=0.000, hop=0)
- 3. `load_exclude_dirs` (score=0.989, sem=0.493, lex=0.000, hop=0)
- 4. `MainWindow.reset_actor_appearances` (score=0.986, sem=0.491, lex=0.000, hop=0)
- 5. `_default_report_name` (score=0.982, sem=0.490, lex=0.000, hop=0)

### Query: `how does the graph get built from source code`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.008 | 8 | 63 | 8 | 0.964 | 0.599 | 0.378 |
| `semantic` | 0.008 | 8 | 63 | 8 | 1.000 | 0.601 | 0.156 |

#### Top nodes (hybrid)
- 1. `PyCodeKG` (score=1.000, sem=0.599, lex=0.444, hop=1)
- 2. `build_code_graph` (score=0.995, sem=0.595, lex=0.444, hop=0)
- 3. `KGModule.make_extractor` (score=0.942, sem=0.601, lex=0.333, hop=1)
- 4. `KGModule` (score=0.942, sem=0.601, lex=0.333, hop=1)
- 5. `PyCodeKG.graph` (score=0.940, sem=0.599, lex=0.333, hop=0)

#### Top nodes (semantic)
- 1. `KGModule.build_graph` (score=1.000, sem=0.601, lex=0.222, hop=0)
- 2. `_edgespec_to_edge` (score=1.000, sem=0.601, lex=0.222, hop=1)
- 3. `_nodespec_to_node` (score=1.000, sem=0.601, lex=0.222, hop=1)
- 4. `KGModule._post_build_hook` (score=1.000, sem=0.601, lex=0.111, hop=1)
- 5. `KGModule.build` (score=1.000, sem=0.601, lex=0.000, hop=1)
