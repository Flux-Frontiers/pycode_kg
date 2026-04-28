# Embedder Benchmark Report

> Query cases marked **[pepys]** use real Samuel Pepys diary text (1660–1668) and are intended for evaluation against a DiaryKG index.  All other cases target a PyCodeKG index.

- Started (UTC): 2026-04-28T03:51:45.694640+00:00
- Completed (UTC): 2026-04-28T03:52:04.287300+00:00
- Repo: `/Users/egs/repos/pycode_kg`
- SQLite: `/Users/egs/repos/pycode_kg/.pycodekg/graph.sqlite`
- LanceDB root: `/Users/egs/repos/pycode_kg/.pycodekg/lancedb-benchmark`
- Hybrid weights: semantic=0.7, lexical=0.3

## Model: `BAAI/bge-small-en-v1.5`
- Build: 3.45s, indexed_rows=480, dim=384

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.036 | 8 | 106 | 10 | 0.955 | 0.665 | 0.567 |
| `semantic` | 0.010 | 8 | 106 | 10 | 1.000 | 0.690 | 0.150 |
| `legacy` | 0.011 | 8 | 106 | 10 | 0.975 | 0.674 | 0.400 |

#### Top nodes (hybrid)
- 1. `query_codebase` (score=1.000, sem=0.665, lex=0.667, hop=0)
- 2. `mcp_server` (score=1.000, sem=0.665, lex=0.667, hop=1)
- 3. `extractor` (score=0.929, sem=0.669, lex=0.500, hop=1)
- 4. `__init__` (score=0.929, sem=0.669, lex=0.500, hop=0)
- 5. `query` (score=0.917, sem=0.657, lex=0.500, hop=0)

#### Top nodes (semantic)
- 1. `GraphStore` (score=1.000, sem=0.690, lex=0.417, hop=0)
- 2. `GraphStore.__enter__` (score=1.000, sem=0.690, lex=0.083, hop=1)
- 3. `GraphStore.__exit__` (score=1.000, sem=0.690, lex=0.083, hop=1)
- 4. `GraphStore.__init__` (score=1.000, sem=0.690, lex=0.083, hop=1)
- 5. `GraphStore.__repr__` (score=1.000, sem=0.690, lex=0.083, hop=1)

#### Top nodes (legacy)
- 1. `GraphStore` (score=1.000, sem=0.690, lex=0.417, hop=0)
- 2. `GraphStore.edges_from` (score=0.976, sem=0.674, lex=0.167, hop=0)
- 3. `EdgeSpec` (score=0.969, sem=0.669, lex=0.250, hop=0)
- 4. `__init__` (score=0.969, sem=0.669, lex=0.500, hop=0)
- 5. `query_codebase` (score=0.963, sem=0.665, lex=0.667, hop=0)

### Query: `snapshot metrics over time`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.021 | 8 | 91 | 8 | 0.944 | 0.646 | 0.582 |
| `semantic` | 0.009 | 8 | 91 | 8 | 0.998 | 0.660 | 0.218 |
| `legacy` | 0.009 | 8 | 91 | 8 | 0.987 | 0.653 | 0.418 |

#### Top nodes (hybrid)
- 1. `snapshot_list` (score=1.000, sem=0.636, lex=0.727, hop=0)
- 2. `mcp_server` (score=0.959, sem=0.636, lex=0.636, hop=1)
- 3. `viz3d_timeline` (score=0.933, sem=0.650, lex=0.545, hop=0)
- 4. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.928, sem=0.646, lex=0.545, hop=0)
- 5. `GraphStore.stats` (score=0.900, sem=0.658, lex=0.455, hop=0)

#### Top nodes (semantic)
- 1. `KGExtractor.coverage_metric` (score=1.000, sem=0.662, lex=0.273, hop=0)
- 2. `PyCodeKGExtractor.meaningful_node_kinds` (score=1.000, sem=0.662, lex=0.273, hop=1)
- 3. `KGExtractor` (score=1.000, sem=0.662, lex=0.091, hop=1)
- 4. `GraphStore.stats` (score=0.995, sem=0.658, lex=0.455, hop=0)
- 5. `GraphStore.con` (score=0.995, sem=0.658, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `KGExtractor.coverage_metric` (score=1.000, sem=0.662, lex=0.273, hop=0)
- 2. `GraphStore.stats` (score=0.995, sem=0.658, lex=0.455, hop=0)
- 3. `viz3d_timeline` (score=0.983, sem=0.650, lex=0.545, hop=0)
- 4. `viz_timeline` (score=0.978, sem=0.647, lex=0.273, hop=0)
- 5. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.977, sem=0.646, lex=0.545, hop=0)

### Query: `MCP tool exposure`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.010 | 8 | 135 | 8 | 0.961 | 0.596 | 0.564 |
| `semantic` | 0.010 | 8 | 135 | 8 | 1.000 | 0.598 | 0.436 |
| `legacy` | 0.009 | 8 | 135 | 8 | 0.987 | 0.591 | 0.455 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.598, lex=0.636, hop=0)
- 2. `analyze_repo` (score=1.000, sem=0.598, lex=0.636, hop=1)
- 3. `KGExtractor` (score=0.986, sem=0.586, lex=0.636, hop=0)
- 4. `_parse_args` (score=0.911, sem=0.598, lex=0.455, hop=1)
- 5. `main` (score=0.911, sem=0.598, lex=0.455, hop=1)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.598, lex=0.636, hop=0)
- 2. `_get_snapshot_mgr` (score=1.000, sem=0.598, lex=0.273, hop=1)
- 3. `_parse_args` (score=1.000, sem=0.598, lex=0.455, hop=1)
- 4. `_snapshot_freshness` (score=1.000, sem=0.598, lex=0.182, hop=1)
- 5. `analyze_repo` (score=1.000, sem=0.598, lex=0.636, hop=1)

#### Top nodes (legacy)
- 1. `mcp_server` (score=1.000, sem=0.598, lex=0.636, hop=0)
- 2. `query_codebase` (score=0.998, sem=0.597, lex=0.364, hop=0)
- 3. `base` (score=0.981, sem=0.587, lex=0.364, hop=0)
- 4. `KGModule.query` (score=0.979, sem=0.586, lex=0.273, hop=0)
- 5. `KGExtractor` (score=0.979, sem=0.586, lex=0.636, hop=0)

### Query: `node missing line number`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.025 | 6 | 6 | 6 | 0.976 | 0.625 | 0.320 |
| `semantic` | 0.009 | 6 | 6 | 6 | 0.974 | 0.626 | 0.240 |
| `legacy` | 0.008 | 6 | 6 | 6 | 0.974 | 0.626 | 0.240 |

#### Top nodes (hybrid)
- 1. `NodeSpec` (score=1.000, sem=0.609, lex=0.400, hop=0)
- 2. `EdgeSpec` (score=0.987, sem=0.642, lex=0.300, hop=0)
- 3. `PyCodeKGVisitor._set_node_source_meta` (score=0.981, sem=0.638, lex=0.300, hop=0)
- 4. `get_node` (score=0.963, sem=0.624, lex=0.300, hop=0)
- 5. `main` (score=0.947, sem=0.611, lex=0.300, hop=0)

#### Top nodes (semantic)
- 1. `EdgeSpec` (score=1.000, sem=0.642, lex=0.300, hop=0)
- 2. `PyCodeKGVisitor._set_node_source_meta` (score=0.993, sem=0.638, lex=0.300, hop=0)
- 3. `get_node` (score=0.971, sem=0.624, lex=0.300, hop=0)
- 4. `_NodeInfo` (score=0.956, sem=0.614, lex=0.000, hop=0)
- 5. `main` (score=0.951, sem=0.611, lex=0.300, hop=0)

#### Top nodes (legacy)
- 1. `EdgeSpec` (score=1.000, sem=0.642, lex=0.300, hop=0)
- 2. `PyCodeKGVisitor._set_node_source_meta` (score=0.993, sem=0.638, lex=0.300, hop=0)
- 3. `get_node` (score=0.971, sem=0.624, lex=0.300, hop=0)
- 4. `_NodeInfo` (score=0.956, sem=0.614, lex=0.000, hop=0)
- 5. `main` (score=0.951, sem=0.611, lex=0.300, hop=0)

### Query: `pepys naval fleet and king` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.020 | 8 | 36 | 8 | 0.970 | 0.507 | 0.213 |
| `semantic` | 0.008 | 8 | 36 | 8 | 0.994 | 0.514 | 0.065 |
| `legacy` | 0.008 | 8 | 36 | 8 | 0.988 | 0.511 | 0.026 |

#### Top nodes (hybrid)
- 1. `PyCodeKGVisitor._add_var_edge` (score=1.000, sem=0.506, lex=0.258, hop=1)
- 2. `PyCodeKGVisitor` (score=0.978, sem=0.506, lex=0.226, hop=1)
- 3. `pack` (score=0.958, sem=0.508, lex=0.194, hop=1)
- 4. `query` (score=0.958, sem=0.508, lex=0.194, hop=1)
- 5. `PyCodeKGVisitor.visit_Call` (score=0.955, sem=0.506, lex=0.194, hop=0)

#### Top nodes (semantic)
- 1. `_done` (score=1.000, sem=0.517, lex=0.000, hop=0)
- 2. `_run_pipeline` (score=1.000, sem=0.517, lex=0.065, hop=1)
- 3. `cmd_build_full` (score=1.000, sem=0.517, lex=0.097, hop=1)
- 4. `MainWindow.show_selected_docstring` (score=0.986, sem=0.510, lex=0.097, hop=0)
- 5. `_docstring_to_markdown` (score=0.986, sem=0.510, lex=0.065, hop=1)

#### Top nodes (legacy)
- 1. `_done` (score=1.000, sem=0.517, lex=0.000, hop=0)
- 2. `MainWindow.show_selected_docstring` (score=0.986, sem=0.510, lex=0.097, hop=0)
- 3. `why_bridge` (score=0.986, sem=0.510, lex=0.000, hop=0)
- 4. `pycodekg_snippet_packer` (score=0.985, sem=0.510, lex=0.000, hop=0)
- 5. `_banner` (score=0.984, sem=0.509, lex=0.032, hop=0)

### Query: `pepys music and viol` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.019 | 8 | 59 | 8 | 0.965 | 0.464 | 0.159 |
| `semantic` | 0.008 | 8 | 59 | 8 | 0.995 | 0.465 | 0.069 |
| `legacy` | 0.008 | 8 | 59 | 8 | 0.992 | 0.464 | 0.062 |

#### Top nodes (hybrid)
- 1. `PyCodeKGVisitor` (score=1.000, sem=0.463, lex=0.207, hop=1)
- 2. `PyCodeKGVisitor._get_node_id` (score=0.973, sem=0.463, lex=0.172, hop=1)
- 3. `centrality` (score=0.956, sem=0.468, lex=0.138, hop=1)
- 4. `SemanticIndex.build` (score=0.947, sem=0.463, lex=0.138, hop=1)
- 5. `PyCodeKGVisitor._add_edge` (score=0.946, sem=0.463, lex=0.138, hop=1)

#### Top nodes (semantic)
- 1. `aggregate_module_scores` (score=1.000, sem=0.468, lex=0.069, hop=0)
- 2. `centrality` (score=1.000, sem=0.468, lex=0.138, hop=1)
- 3. `src/pycode_kg/analysis/hybrid_rank.py.get_sir_scores.norm` (score=0.993, sem=0.464, lex=0.000, hop=0)
- 4. `get_sir_scores` (score=0.993, sem=0.464, lex=0.034, hop=1)
- 5. `suppress_ingestion_logging` (score=0.990, sem=0.463, lex=0.103, hop=0)

#### Top nodes (legacy)
- 1. `aggregate_module_scores` (score=1.000, sem=0.468, lex=0.069, hop=0)
- 2. `src/pycode_kg/analysis/hybrid_rank.py.get_sir_scores.norm` (score=0.993, sem=0.464, lex=0.000, hop=0)
- 3. `suppress_ingestion_logging` (score=0.990, sem=0.463, lex=0.103, hop=0)
- 4. `PyCodeKGVisitor.visit_ClassDef` (score=0.989, sem=0.463, lex=0.103, hop=0)
- 5. `MainWindow.reset_actor_appearances` (score=0.989, sem=0.462, lex=0.034, hop=0)

### Query: `pepys plague and naval failure` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.021 | 8 | 40 | 8 | 0.932 | 0.488 | 0.213 |
| `semantic` | 0.009 | 8 | 40 | 8 | 0.997 | 0.494 | 0.115 |
| `legacy` | 0.009 | 8 | 40 | 8 | 0.989 | 0.490 | 0.055 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.484, lex=0.319, hop=1)
- 2. `callers` (score=0.941, sem=0.484, lex=0.234, hop=0)
- 3. `PyCodeKGAnalyzer.__init__` (score=0.912, sem=0.484, lex=0.191, hop=0)
- 4. `StructuralImportanceRanker.compute` (score=0.907, sem=0.490, lex=0.170, hop=1)
- 5. `PyCodeKGAnalyzer._analyze_inheritance` (score=0.901, sem=0.496, lex=0.149, hop=1)

#### Top nodes (semantic)
- 1. `src/pycode_kg/pycodekg_thorough_analysis.py.PyCodeKGAnalyzer._analyze_inheritance._all_internal_ancestors` (score=1.000, sem=0.496, lex=0.064, hop=0)
- 2. `PyCodeKGAnalyzer._analyze_inheritance` (score=1.000, sem=0.496, lex=0.149, hop=1)
- 3. `SnapshotManager._collect_module_node_counts` (score=0.995, sem=0.493, lex=0.085, hop=0)
- 4. `SnapshotManager.capture` (score=0.995, sem=0.493, lex=0.149, hop=1)
- 5. `SnapshotManager` (score=0.995, sem=0.493, lex=0.128, hop=1)

#### Top nodes (legacy)
- 1. `src/pycode_kg/pycodekg_thorough_analysis.py.PyCodeKGAnalyzer._analyze_inheritance._all_internal_ancestors` (score=1.000, sem=0.496, lex=0.064, hop=0)
- 2. `SnapshotManager._collect_module_node_counts` (score=0.995, sem=0.493, lex=0.085, hop=0)
- 3. `StructuralImportanceRanker._load_nodes` (score=0.989, sem=0.490, lex=0.000, hop=0)
- 4. `aggregate_module_scores` (score=0.981, sem=0.486, lex=0.106, hop=0)
- 5. `__main__` (score=0.979, sem=0.485, lex=0.021, hop=0)

### Query: `pepys treasury and accounts` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.019 | 8 | 28 | 8 | 0.963 | 0.487 | 0.121 |
| `semantic` | 0.008 | 8 | 28 | 8 | 0.997 | 0.491 | 0.047 |
| `legacy` | 0.008 | 8 | 28 | 8 | 0.993 | 0.489 | 0.016 |

#### Top nodes (hybrid)
- 1. `KGModule` (score=1.000, sem=0.492, lex=0.158, hop=1)
- 2. `SnapshotManager` (score=0.966, sem=0.484, lex=0.132, hop=1)
- 3. `KGModule.build_graph` (score=0.963, sem=0.482, lex=0.132, hop=1)
- 4. `KGModule.query` (score=0.956, sem=0.490, lex=0.105, hop=1)
- 5. `cmd_build_full` (score=0.928, sem=0.486, lex=0.079, hop=1)

#### Top nodes (semantic)
- 1. `KGModule.__exit__` (score=1.000, sem=0.492, lex=0.053, hop=0)
- 2. `KGModule.close` (score=0.999, sem=0.492, lex=0.026, hop=0)
- 3. `KGModule` (score=0.999, sem=0.492, lex=0.158, hop=1)
- 4. `KGModule.store` (score=0.995, sem=0.490, lex=0.000, hop=0)
- 5. `src/pycode_kg/module/base.py.KGModule.query._rank_key` (score=0.995, sem=0.490, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `KGModule.__exit__` (score=1.000, sem=0.492, lex=0.053, hop=0)
- 2. `KGModule.close` (score=0.999, sem=0.492, lex=0.026, hop=0)
- 3. `KGModule.store` (score=0.995, sem=0.490, lex=0.000, hop=0)
- 4. `_done` (score=0.986, sem=0.486, lex=0.000, hop=0)
- 5. `pycodekg_query` (score=0.984, sem=0.485, lex=0.000, hop=0)

### Query: `pepys year-end reflection` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.019 | 8 | 37 | 8 | 0.974 | 0.511 | 0.141 |
| `semantic` | 0.008 | 8 | 37 | 8 | 0.999 | 0.518 | 0.041 |
| `legacy` | 0.008 | 8 | 37 | 8 | 0.987 | 0.512 | 0.009 |

#### Top nodes (hybrid)
- 1. `SnapshotManager.capture` (score=1.000, sem=0.508, lex=0.182, hop=1)
- 2. `snapshots` (score=1.000, sem=0.508, lex=0.182, hop=1)
- 3. `Snapshot` (score=0.984, sem=0.519, lex=0.136, hop=1)
- 4. `GraphStore` (score=0.946, sem=0.506, lex=0.114, hop=1)
- 5. `SnapshotManager` (score=0.939, sem=0.511, lex=0.091, hop=1)

#### Top nodes (semantic)
- 1. `Snapshot.vs_previous` (score=1.000, sem=0.519, lex=0.000, hop=0)
- 2. `delta_from_dict` (score=1.000, sem=0.519, lex=0.023, hop=1)
- 3. `delta_to_dict` (score=1.000, sem=0.519, lex=0.023, hop=1)
- 4. `Snapshot` (score=1.000, sem=0.519, lex=0.136, hop=1)
- 5. `MainWindow.closeEvent` (score=0.994, sem=0.515, lex=0.023, hop=0)

#### Top nodes (legacy)
- 1. `Snapshot.vs_previous` (score=1.000, sem=0.519, lex=0.000, hop=0)
- 2. `MainWindow.closeEvent` (score=0.994, sem=0.515, lex=0.023, hop=0)
- 3. `SnapshotManager.get_previous` (score=0.986, sem=0.511, lex=0.000, hop=0)
- 4. `_rewrap` (score=0.981, sem=0.508, lex=0.000, hop=0)
- 5. `GraphStore.__exit__` (score=0.975, sem=0.506, lex=0.023, hop=0)

## Model: `nomic-ai/nomic-embed-text-v1`
- Build: 7.32s, indexed_rows=480, dim=768

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.139 | 8 | 52 | 10 | 0.931 | 0.559 | 0.533 |
| `semantic` | 0.013 | 8 | 52 | 10 | 0.999 | 0.570 | 0.150 |
| `legacy` | 0.009 | 8 | 52 | 10 | 0.990 | 0.564 | 0.300 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.560, lex=0.667, hop=1)
- 2. `pycodekg` (score=0.954, sem=0.557, lex=0.583, hop=1)
- 3. `extractor` (score=0.918, sem=0.562, lex=0.500, hop=1)
- 4. `graph_stats` (score=0.916, sem=0.560, lex=0.500, hop=0)
- 5. `GraphStore` (score=0.866, sem=0.554, lex=0.417, hop=0)

#### Top nodes (semantic)
- 1. `GraphStore.edges_within` (score=1.000, sem=0.570, lex=0.333, hop=0)
- 2. `GraphStore.con` (score=1.000, sem=0.570, lex=0.000, hop=1)
- 3. `QueryResult` (score=0.999, sem=0.569, lex=0.250, hop=0)
- 4. `QueryResult.print_summary` (score=0.999, sem=0.569, lex=0.083, hop=1)
- 5. `QueryResult.to_dict` (score=0.999, sem=0.569, lex=0.083, hop=1)

#### Top nodes (legacy)
- 1. `GraphStore.edges_within` (score=1.000, sem=0.570, lex=0.333, hop=0)
- 2. `QueryResult` (score=0.999, sem=0.569, lex=0.250, hop=0)
- 3. `EdgeSpec` (score=0.986, sem=0.562, lex=0.250, hop=0)
- 4. `graph_stats` (score=0.983, sem=0.560, lex=0.500, hop=0)
- 5. `CodeGraph.edges` (score=0.981, sem=0.559, lex=0.167, hop=0)

### Query: `snapshot metrics over time`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.022 | 8 | 104 | 8 | 0.951 | 0.571 | 0.600 |
| `semantic` | 0.011 | 8 | 104 | 8 | 0.988 | 0.590 | 0.309 |
| `legacy` | 0.009 | 8 | 104 | 8 | 0.981 | 0.586 | 0.364 |

#### Top nodes (hybrid)
- 1. `snapshot_list` (score=1.000, sem=0.559, lex=0.727, hop=1)
- 2. `mcp_server` (score=0.955, sem=0.559, lex=0.636, hop=0)
- 3. `snapshot_diff` (score=0.955, sem=0.559, lex=0.636, hop=1)
- 4. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.948, sem=0.592, lex=0.545, hop=0)
- 5. `GraphStore.stats` (score=0.898, sem=0.587, lex=0.455, hop=0)

#### Top nodes (semantic)
- 1. `graph_stats` (score=1.000, sem=0.597, lex=0.364, hop=0)
- 2. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.991, sem=0.592, lex=0.545, hop=0)
- 3. `GraphStore.stats` (score=0.983, sem=0.587, lex=0.455, hop=0)
- 4. `GraphStore.con` (score=0.983, sem=0.587, lex=0.000, hop=1)
- 5. `GraphStore` (score=0.983, sem=0.587, lex=0.182, hop=1)

#### Top nodes (legacy)
- 1. `graph_stats` (score=1.000, sem=0.597, lex=0.364, hop=0)
- 2. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.991, sem=0.592, lex=0.545, hop=0)
- 3. `GraphStore.stats` (score=0.983, sem=0.587, lex=0.455, hop=0)
- 4. `KGExtractor.coverage_metric` (score=0.969, sem=0.578, lex=0.273, hop=0)
- 5. `rank_nodes` (score=0.962, sem=0.574, lex=0.182, hop=0)

### Query: `MCP tool exposure`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.009 | 8 | 102 | 8 | 0.881 | 0.522 | 0.509 |
| `semantic` | 0.009 | 8 | 102 | 8 | 1.000 | 0.568 | 0.309 |
| `legacy` | 0.009 | 8 | 102 | 8 | 0.925 | 0.525 | 0.345 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.568, lex=0.636, hop=0)
- 2. `analyze_repo` (score=0.931, sem=0.509, lex=0.636, hop=1)
- 3. `main` (score=0.829, sem=0.501, lex=0.455, hop=0)
- 4. `_parse_args` (score=0.829, sem=0.501, lex=0.455, hop=1)
- 5. `graph_stats` (score=0.815, sem=0.529, lex=0.364, hop=0)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.568, lex=0.636, hop=0)
- 2. `_get_snapshot_mgr` (score=1.000, sem=0.568, lex=0.273, hop=1)
- 3. `snapshot_diff` (score=1.000, sem=0.568, lex=0.091, hop=1)
- 4. `snapshot_list` (score=1.000, sem=0.568, lex=0.273, hop=1)
- 5. `snapshot_show` (score=1.000, sem=0.568, lex=0.273, hop=1)

#### Top nodes (legacy)
- 1. `mcp_server` (score=1.000, sem=0.568, lex=0.636, hop=0)
- 2. `graph_stats` (score=0.933, sem=0.529, lex=0.364, hop=0)
- 3. `explain_rank` (score=0.908, sem=0.515, lex=0.364, hop=0)
- 4. `_get_kg` (score=0.898, sem=0.509, lex=0.273, hop=0)
- 5. `detect_framework_nodes` (score=0.885, sem=0.502, lex=0.091, hop=0)

### Query: `node missing line number`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.041 | 6 | 6 | 6 | 0.929 | 0.553 | 0.260 |
| `semantic` | 0.011 | 6 | 6 | 6 | 0.979 | 0.558 | 0.240 |
| `legacy` | 0.012 | 6 | 6 | 6 | 0.979 | 0.558 | 0.240 |

#### Top nodes (hybrid)
- 1. `NodeSpec` (score=1.000, sem=0.544, lex=0.400, hop=0)
- 2. `PyCodeKGVisitor._set_node_source_meta` (score=0.975, sem=0.570, lex=0.300, hop=0)
- 3. `get_node` (score=0.941, sem=0.545, lex=0.300, hop=0)
- 4. `_snapshot_freshness` (score=0.874, sem=0.540, lex=0.200, hop=0)
- 5. `KGModule.node` (score=0.853, sem=0.568, lex=0.100, hop=0)

#### Top nodes (semantic)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.570, lex=0.300, hop=0)
- 2. `KGModule.node` (score=0.997, sem=0.568, lex=0.100, hop=0)
- 3. `GraphStore.node` (score=0.986, sem=0.562, lex=0.100, hop=0)
- 4. `get_node` (score=0.957, sem=0.545, lex=0.300, hop=0)
- 5. `NodeSpec` (score=0.956, sem=0.544, lex=0.400, hop=0)

#### Top nodes (legacy)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.570, lex=0.300, hop=0)
- 2. `KGModule.node` (score=0.997, sem=0.568, lex=0.100, hop=0)
- 3. `GraphStore.node` (score=0.986, sem=0.562, lex=0.100, hop=0)
- 4. `get_node` (score=0.957, sem=0.545, lex=0.300, hop=0)
- 5. `NodeSpec` (score=0.956, sem=0.544, lex=0.400, hop=0)

### Query: `pepys naval fleet and king` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.074 | 8 | 59 | 8 | 0.978 | 0.462 | 0.206 |
| `semantic` | 0.010 | 8 | 59 | 8 | 1.000 | 0.466 | 0.168 |
| `legacy` | 0.009 | 8 | 59 | 8 | 0.993 | 0.463 | 0.052 |

#### Top nodes (hybrid)
- 1. `snapshot_list` (score=1.000, sem=0.466, lex=0.226, hop=1)
- 2. `mcp_server` (score=1.000, sem=0.466, lex=0.226, hop=1)
- 3. `snapshot_diff` (score=0.975, sem=0.466, lex=0.194, hop=1)
- 4. `Snapshot` (score=0.958, sem=0.456, lex=0.194, hop=0)
- 5. `snapshots` (score=0.958, sem=0.456, lex=0.194, hop=1)

#### Top nodes (semantic)
- 1. `_get_snapshot_mgr` (score=1.000, sem=0.466, lex=0.032, hop=0)
- 2. `snapshot_diff` (score=1.000, sem=0.466, lex=0.194, hop=1)
- 3. `snapshot_list` (score=1.000, sem=0.466, lex=0.226, hop=1)
- 4. `snapshot_show` (score=1.000, sem=0.466, lex=0.161, hop=1)
- 5. `mcp_server` (score=1.000, sem=0.466, lex=0.226, hop=1)

#### Top nodes (legacy)
- 1. `_get_snapshot_mgr` (score=1.000, sem=0.466, lex=0.032, hop=0)
- 2. `get_sir_scores` (score=0.999, sem=0.466, lex=0.065, hop=0)
- 3. `MainWindow.reset_actor_appearances` (score=0.995, sem=0.464, lex=0.032, hop=0)
- 4. `_render_legend` (score=0.988, sem=0.461, lex=0.129, hop=0)
- 5. `src/pycode_kg/module/base.py.KGModule.query._rank_key` (score=0.983, sem=0.458, lex=0.000, hop=0)

### Query: `pepys music and viol` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.020 | 8 | 89 | 8 | 0.976 | 0.434 | 0.179 |
| `semantic` | 0.012 | 8 | 89 | 8 | 0.983 | 0.445 | 0.034 |
| `legacy` | 0.009 | 8 | 89 | 8 | 0.975 | 0.441 | 0.062 |

#### Top nodes (hybrid)
- 1. `snapshots` (score=1.000, sem=0.435, lex=0.207, hop=1)
- 2. `viz3d` (score=0.973, sem=0.436, lex=0.172, hop=1)
- 3. `Snapshot` (score=0.972, sem=0.435, lex=0.172, hop=0)
- 4. `GraphStore.callers_of` (score=0.970, sem=0.434, lex=0.172, hop=1)
- 5. `SemanticIndex` (score=0.965, sem=0.432, lex=0.172, hop=1)

#### Top nodes (semantic)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.453, lex=0.034, hop=0)
- 2. `_remove_highlight_actors` (score=1.000, sem=0.453, lex=0.034, hop=1)
- 3. `MainWindow._setup_mesh_picking` (score=0.985, sem=0.446, lex=0.034, hop=0)
- 4. `MainWindow.highlight_actor` (score=0.967, sem=0.438, lex=0.034, hop=0)
- 5. `MainWindow` (score=0.963, sem=0.436, lex=0.034, hop=0)

#### Top nodes (legacy)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.453, lex=0.034, hop=0)
- 2. `MainWindow._setup_mesh_picking` (score=0.985, sem=0.446, lex=0.034, hop=0)
- 3. `MainWindow.highlight_actor` (score=0.967, sem=0.438, lex=0.034, hop=0)
- 4. `MainWindow` (score=0.963, sem=0.436, lex=0.034, hop=0)
- 5. `Snapshot` (score=0.961, sem=0.435, lex=0.172, hop=0)

### Query: `pepys plague and naval failure` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.135 | 8 | 88 | 8 | 0.957 | 0.458 | 0.264 |
| `semantic` | 0.014 | 8 | 88 | 8 | 1.000 | 0.460 | 0.115 |
| `legacy` | 0.010 | 8 | 88 | 8 | 0.995 | 0.458 | 0.200 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.460, lex=0.319, hop=0)
- 2. `query_codebase` (score=0.985, sem=0.460, lex=0.298, hop=1)
- 3. `pack_snippets` (score=0.939, sem=0.460, lex=0.234, hop=1)
- 4. `callers` (score=0.935, sem=0.458, lex=0.234, hop=0)
- 5. `bridge_centrality` (score=0.927, sem=0.453, lex=0.234, hop=0)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.460, lex=0.319, hop=0)
- 2. `_enrich_edges_with_provenance` (score=1.000, sem=0.460, lex=0.085, hop=1)
- 3. `_get_snapshot_mgr` (score=1.000, sem=0.460, lex=0.064, hop=1)
- 4. `_parse_args` (score=1.000, sem=0.460, lex=0.064, hop=1)
- 5. `_snapshot_freshness` (score=1.000, sem=0.460, lex=0.043, hop=1)

#### Top nodes (legacy)
- 1. `mcp_server` (score=1.000, sem=0.460, lex=0.319, hop=0)
- 2. `get_node` (score=0.995, sem=0.458, lex=0.191, hop=0)
- 3. `centrality` (score=0.995, sem=0.458, lex=0.191, hop=0)
- 4. `callers` (score=0.995, sem=0.458, lex=0.234, hop=0)
- 5. `list_nodes` (score=0.989, sem=0.455, lex=0.064, hop=0)

### Query: `pepys treasury and accounts` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.045 | 8 | 47 | 8 | 0.961 | 0.435 | 0.132 |
| `semantic` | 0.011 | 8 | 47 | 8 | 0.988 | 0.439 | 0.068 |
| `legacy` | 0.011 | 8 | 47 | 8 | 0.983 | 0.436 | 0.037 |

#### Top nodes (hybrid)
- 1. `viz3d` (score=1.000, sem=0.444, lex=0.158, hop=1)
- 2. `KGModule` (score=0.978, sem=0.433, lex=0.158, hop=1)
- 3. `GraphStore.callers_of` (score=0.958, sem=0.434, lex=0.132, hop=1)
- 4. `KGVisualizer` (score=0.935, sem=0.433, lex=0.105, hop=1)
- 5. `rerank_hybrid` (score=0.935, sem=0.433, lex=0.105, hop=1)

#### Top nodes (semantic)
- 1. `_remove_highlight_actors` (score=1.000, sem=0.444, lex=0.026, hop=0)
- 2. `viz3d` (score=1.000, sem=0.444, lex=0.158, hop=1)
- 3. `MainWindow.reset_actor_appearances` (score=0.982, sem=0.436, lex=0.026, hop=0)
- 4. `MainWindow.highlight_actor` (score=0.980, sem=0.435, lex=0.053, hop=0)
- 5. `MainWindow.on_pick` (score=0.980, sem=0.435, lex=0.079, hop=1)

#### Top nodes (legacy)
- 1. `_remove_highlight_actors` (score=1.000, sem=0.444, lex=0.026, hop=0)
- 2. `MainWindow.reset_actor_appearances` (score=0.982, sem=0.436, lex=0.026, hop=0)
- 3. `MainWindow.highlight_actor` (score=0.980, sem=0.435, lex=0.053, hop=0)
- 4. `_parse_call_site_lineno` (score=0.977, sem=0.434, lex=0.053, hop=0)
- 5. `KGVisualizer._kind_visible` (score=0.976, sem=0.433, lex=0.026, hop=0)

### Query: `pepys year-end reflection` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.018 | 8 | 88 | 8 | 0.984 | 0.453 | 0.123 |
| `semantic` | 0.011 | 8 | 88 | 8 | 0.999 | 0.456 | 0.064 |
| `legacy` | 0.010 | 8 | 88 | 8 | 0.995 | 0.454 | 0.100 |

#### Top nodes (hybrid)
- 1. `SnapshotManager.diff_snapshots` (score=1.000, sem=0.456, lex=0.136, hop=0)
- 2. `prune_snapshots` (score=0.997, sem=0.454, lex=0.136, hop=0)
- 3. `PyCodeKGAnalyzer._analyze_inheritance` (score=0.988, sem=0.450, lex=0.136, hop=0)
- 4. `aggregate_module_scores` (score=0.971, sem=0.451, lex=0.114, hop=0)
- 5. `SnapshotManager` (score=0.962, sem=0.456, lex=0.091, hop=1)

#### Top nodes (semantic)
- 1. `SnapshotManager.diff_snapshots` (score=1.000, sem=0.456, lex=0.136, hop=0)
- 2. `Snapshot.metrics` (score=1.000, sem=0.456, lex=0.000, hop=1)
- 3. `SnapshotManager._compute_delta_from_metrics` (score=1.000, sem=0.456, lex=0.000, hop=1)
- 4. `SnapshotManager` (score=1.000, sem=0.456, lex=0.091, hop=1)
- 5. `diff_snapshots` (score=0.997, sem=0.454, lex=0.091, hop=0)

#### Top nodes (legacy)
- 1. `SnapshotManager.diff_snapshots` (score=1.000, sem=0.456, lex=0.136, hop=0)
- 2. `diff_snapshots` (score=0.997, sem=0.454, lex=0.091, hop=0)
- 3. `prune_snapshots` (score=0.996, sem=0.454, lex=0.136, hop=0)
- 4. `PyCodeKGAnalyzer._analyze_snapshots` (score=0.993, sem=0.453, lex=0.068, hop=0)
- 5. `PyCodeKGAnalyzer._analyze_centrality` (score=0.990, sem=0.451, lex=0.068, hop=0)

## Model: `nomic-ai/nomic-embed-text-v1.5`
- Build: 6.51s, indexed_rows=480, dim=768

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.012 | 8 | 72 | 10 | 0.956 | 0.586 | 0.567 |
| `semantic` | 0.010 | 8 | 72 | 10 | 0.984 | 0.599 | 0.217 |
| `legacy` | 0.009 | 8 | 72 | 10 | 0.966 | 0.588 | 0.283 |

#### Top nodes (hybrid)
- 1. `query_codebase` (score=1.000, sem=0.581, lex=0.667, hop=1)
- 2. `mcp_server` (score=0.999, sem=0.580, lex=0.667, hop=1)
- 3. `pycodekg` (score=0.956, sem=0.579, lex=0.583, hop=0)
- 4. `graph_stats` (score=0.916, sem=0.580, lex=0.500, hop=0)
- 5. `GraphStore` (score=0.908, sem=0.608, lex=0.417, hop=1)

#### Top nodes (semantic)
- 1. `GraphStore.edges_within` (score=1.000, sem=0.608, lex=0.333, hop=0)
- 2. `GraphStore.con` (score=1.000, sem=0.608, lex=0.000, hop=1)
- 3. `GraphStore` (score=1.000, sem=0.608, lex=0.417, hop=1)
- 4. `GraphStore.edges_from` (score=0.963, sem=0.586, lex=0.167, hop=0)
- 5. `CodeGraph.edges` (score=0.959, sem=0.583, lex=0.167, hop=0)

#### Top nodes (legacy)
- 1. `GraphStore.edges_within` (score=1.000, sem=0.608, lex=0.333, hop=0)
- 2. `GraphStore.edges_from` (score=0.963, sem=0.586, lex=0.167, hop=0)
- 3. `CodeGraph.edges` (score=0.959, sem=0.583, lex=0.167, hop=0)
- 4. `_enrich_edges_with_provenance` (score=0.955, sem=0.581, lex=0.250, hop=0)
- 5. `graph_stats` (score=0.954, sem=0.580, lex=0.500, hop=0)

### Query: `snapshot metrics over time`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.012 | 8 | 69 | 8 | 0.931 | 0.619 | 0.473 |
| `semantic` | 0.009 | 8 | 69 | 8 | 0.989 | 0.626 | 0.309 |
| `legacy` | 0.009 | 8 | 69 | 8 | 0.983 | 0.622 | 0.364 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.610, lex=0.636, hop=1)
- 2. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.982, sem=0.633, lex=0.545, hop=0)
- 3. `GraphStore.stats` (score=0.927, sem=0.624, lex=0.455, hop=0)
- 4. `graph_stats` (score=0.887, sem=0.627, lex=0.364, hop=0)
- 5. `PyCodeKGAnalyzer._analyze_baseline` (score=0.857, sem=0.600, lex=0.364, hop=0)

#### Top nodes (semantic)
- 1. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=1.000, sem=0.633, lex=0.545, hop=0)
- 2. `graph_stats` (score=0.990, sem=0.627, lex=0.364, hop=0)
- 3. `GraphStore.stats` (score=0.986, sem=0.624, lex=0.455, hop=0)
- 4. `GraphStore.con` (score=0.986, sem=0.624, lex=0.000, hop=1)
- 5. `GraphStore` (score=0.986, sem=0.624, lex=0.182, hop=1)

#### Top nodes (legacy)
- 1. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=1.000, sem=0.633, lex=0.545, hop=0)
- 2. `graph_stats` (score=0.990, sem=0.627, lex=0.364, hop=0)
- 3. `GraphStore.stats` (score=0.986, sem=0.624, lex=0.455, hop=0)
- 4. `KGExtractor.coverage_metric` (score=0.974, sem=0.616, lex=0.273, hop=0)
- 5. `rank_nodes` (score=0.964, sem=0.610, lex=0.182, hop=0)

### Query: `MCP tool exposure`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.009 | 8 | 108 | 8 | 0.916 | 0.566 | 0.509 |
| `semantic` | 0.009 | 8 | 108 | 8 | 1.000 | 0.583 | 0.382 |
| `legacy` | 0.009 | 8 | 108 | 8 | 0.930 | 0.542 | 0.364 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.583, lex=0.636, hop=0)
- 2. `analyze_repo` (score=0.936, sem=0.527, lex=0.636, hop=1)
- 3. `_parse_args` (score=0.909, sem=0.583, lex=0.455, hop=1)
- 4. `main` (score=0.909, sem=0.583, lex=0.455, hop=1)
- 5. `graph_stats` (score=0.829, sem=0.553, lex=0.364, hop=0)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.583, lex=0.636, hop=0)
- 2. `_get_snapshot_mgr` (score=1.000, sem=0.583, lex=0.273, hop=1)
- 3. `_parse_args` (score=1.000, sem=0.583, lex=0.455, hop=1)
- 4. `main` (score=1.000, sem=0.583, lex=0.455, hop=1)
- 5. `snapshot_diff` (score=1.000, sem=0.583, lex=0.091, hop=1)

#### Top nodes (legacy)
- 1. `mcp_server` (score=1.000, sem=0.583, lex=0.636, hop=0)
- 2. `graph_stats` (score=0.949, sem=0.553, lex=0.364, hop=0)
- 3. `_get_kg` (score=0.905, sem=0.527, lex=0.273, hop=0)
- 4. `explain_rank` (score=0.903, sem=0.526, lex=0.364, hop=0)
- 5. `_enrich_edges_with_provenance` (score=0.893, sem=0.520, lex=0.182, hop=0)

### Query: `node missing line number`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.012 | 6 | 6 | 6 | 0.933 | 0.568 | 0.260 |
| `semantic` | 0.008 | 6 | 6 | 6 | 0.976 | 0.573 | 0.240 |
| `legacy` | 0.008 | 6 | 6 | 6 | 0.976 | 0.573 | 0.240 |

#### Top nodes (hybrid)
- 1. `NodeSpec` (score=1.000, sem=0.557, lex=0.400, hop=0)
- 2. `PyCodeKGVisitor._set_node_source_meta` (score=0.983, sem=0.587, lex=0.300, hop=0)
- 3. `get_node` (score=0.949, sem=0.562, lex=0.300, hop=0)
- 4. `_snapshot_freshness` (score=0.879, sem=0.554, lex=0.200, hop=0)
- 5. `KGModule.node` (score=0.856, sem=0.581, lex=0.100, hop=0)

#### Top nodes (semantic)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.587, lex=0.300, hop=0)
- 2. `KGModule.node` (score=0.989, sem=0.581, lex=0.100, hop=0)
- 3. `GraphStore.node` (score=0.988, sem=0.580, lex=0.100, hop=0)
- 4. `get_node` (score=0.957, sem=0.562, lex=0.300, hop=0)
- 5. `NodeSpec` (score=0.948, sem=0.557, lex=0.400, hop=0)

#### Top nodes (legacy)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.587, lex=0.300, hop=0)
- 2. `KGModule.node` (score=0.989, sem=0.581, lex=0.100, hop=0)
- 3. `GraphStore.node` (score=0.988, sem=0.580, lex=0.100, hop=0)
- 4. `get_node` (score=0.957, sem=0.562, lex=0.300, hop=0)
- 5. `NodeSpec` (score=0.948, sem=0.557, lex=0.400, hop=0)

### Query: `pepys naval fleet and king` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 8 | 65 | 8 | 0.971 | 0.478 | 0.187 |
| `semantic` | 0.009 | 8 | 65 | 8 | 0.987 | 0.484 | 0.039 |
| `legacy` | 0.009 | 8 | 65 | 8 | 0.981 | 0.481 | 0.045 |

#### Top nodes (hybrid)
- 1. `snapshot_list` (score=1.000, sem=0.478, lex=0.226, hop=1)
- 2. `mcp_server` (score=1.000, sem=0.478, lex=0.226, hop=1)
- 3. `snapshot_diff` (score=0.976, sem=0.478, lex=0.194, hop=1)
- 4. `snapshot_show` (score=0.952, sem=0.478, lex=0.161, hop=1)
- 5. `MainWindow.on_pick` (score=0.928, sem=0.478, lex=0.129, hop=1)

#### Top nodes (semantic)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.490, lex=0.032, hop=0)
- 2. `_remove_highlight_actors` (score=1.000, sem=0.490, lex=0.065, hop=1)
- 3. `MainWindow.update_status_display` (score=0.979, sem=0.480, lex=0.000, hop=0)
- 4. `MainWindow.reset_picking_state` (score=0.979, sem=0.480, lex=0.000, hop=1)
- 5. `MainWindow.show_selected_docstring` (score=0.979, sem=0.480, lex=0.097, hop=1)

#### Top nodes (legacy)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.490, lex=0.032, hop=0)
- 2. `MainWindow.update_status_display` (score=0.979, sem=0.480, lex=0.000, hop=0)
- 3. `MainWindow.highlight_actor` (score=0.976, sem=0.478, lex=0.097, hop=0)
- 4. `_get_snapshot_mgr` (score=0.976, sem=0.478, lex=0.032, hop=0)
- 5. `get_sir_scores` (score=0.975, sem=0.478, lex=0.065, hop=0)

### Query: `pepys music and viol` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 8 | 107 | 8 | 0.967 | 0.441 | 0.193 |
| `semantic` | 0.009 | 8 | 107 | 8 | 0.985 | 0.460 | 0.048 |
| `legacy` | 0.010 | 8 | 107 | 8 | 0.961 | 0.449 | 0.076 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.438, lex=0.241, hop=1)
- 2. `snapshots` (score=0.981, sem=0.442, lex=0.207, hop=1)
- 3. `Snapshot` (score=0.953, sem=0.442, lex=0.172, hop=0)
- 4. `GraphStore.callers_of` (score=0.952, sem=0.441, lex=0.172, hop=1)
- 5. `_load_kg` (score=0.951, sem=0.441, lex=0.172, hop=1)

#### Top nodes (semantic)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.467, lex=0.034, hop=0)
- 2. `_remove_highlight_actors` (score=1.000, sem=0.467, lex=0.034, hop=1)
- 3. `MainWindow.reset_picking_state` (score=1.000, sem=0.467, lex=0.034, hop=1)
- 4. `MainWindow.highlight_actor` (score=0.963, sem=0.450, lex=0.034, hop=0)
- 5. `MainWindow.on_pick` (score=0.963, sem=0.450, lex=0.103, hop=1)

#### Top nodes (legacy)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.467, lex=0.034, hop=0)
- 2. `MainWindow.highlight_actor` (score=0.963, sem=0.450, lex=0.034, hop=0)
- 3. `MainWindow._setup_mesh_picking` (score=0.950, sem=0.444, lex=0.034, hop=0)
- 4. `Snapshot` (score=0.946, sem=0.442, lex=0.172, hop=0)
- 5. `GraphStore._is_compatible_stub_caller` (score=0.945, sem=0.441, lex=0.103, hop=0)

### Query: `pepys plague and naval failure` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.013 | 8 | 88 | 8 | 0.958 | 0.464 | 0.264 |
| `semantic` | 0.010 | 8 | 88 | 8 | 1.000 | 0.465 | 0.115 |
| `legacy` | 0.010 | 8 | 88 | 8 | 0.996 | 0.464 | 0.149 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.465, lex=0.319, hop=0)
- 2. `query_codebase` (score=0.985, sem=0.465, lex=0.298, hop=1)
- 3. `pack_snippets` (score=0.939, sem=0.465, lex=0.234, hop=1)
- 4. `bridge_centrality` (score=0.933, sem=0.461, lex=0.234, hop=0)
- 5. `callers` (score=0.932, sem=0.461, lex=0.234, hop=0)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.465, lex=0.319, hop=0)
- 2. `_enrich_edges_with_provenance` (score=1.000, sem=0.465, lex=0.085, hop=1)
- 3. `_get_snapshot_mgr` (score=1.000, sem=0.465, lex=0.064, hop=1)
- 4. `_parse_args` (score=1.000, sem=0.465, lex=0.064, hop=1)
- 5. `_snapshot_freshness` (score=1.000, sem=0.465, lex=0.043, hop=1)

#### Top nodes (legacy)
- 1. `mcp_server` (score=1.000, sem=0.465, lex=0.319, hop=0)
- 2. `SemanticIndex._open_table` (score=0.996, sem=0.463, lex=0.064, hop=0)
- 3. `graph_stats` (score=0.995, sem=0.463, lex=0.128, hop=0)
- 4. `load_include_dirs` (score=0.995, sem=0.463, lex=0.170, hop=0)
- 5. `KGModule.build_index` (score=0.995, sem=0.463, lex=0.064, hop=0)

### Query: `pepys treasury and accounts` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 8 | 46 | 8 | 0.950 | 0.452 | 0.111 |
| `semantic` | 0.009 | 8 | 46 | 8 | 0.996 | 0.456 | 0.047 |
| `legacy` | 0.009 | 8 | 46 | 8 | 0.992 | 0.454 | 0.032 |

#### Top nodes (hybrid)
- 1. `viz3d` (score=1.000, sem=0.458, lex=0.158, hop=1)
- 2. `GraphStore.callers_of` (score=0.963, sem=0.449, lex=0.132, hop=1)
- 3. `rerank_hybrid` (score=0.935, sem=0.446, lex=0.105, hop=1)
- 4. `MainWindow.show_selected_docstring` (score=0.927, sem=0.453, lex=0.079, hop=1)
- 5. `MainWindow.on_pick` (score=0.925, sem=0.452, lex=0.079, hop=1)

#### Top nodes (semantic)
- 1. `_remove_highlight_actors` (score=1.000, sem=0.458, lex=0.026, hop=0)
- 2. `viz3d` (score=1.000, sem=0.458, lex=0.158, hop=1)
- 3. `MainWindow.reset_actor_appearances` (score=0.999, sem=0.457, lex=0.026, hop=0)
- 4. `MainWindow.update_status_display` (score=0.990, sem=0.453, lex=0.000, hop=0)
- 5. `MainWindow.reset_picking_state` (score=0.990, sem=0.453, lex=0.026, hop=1)

#### Top nodes (legacy)
- 1. `_remove_highlight_actors` (score=1.000, sem=0.458, lex=0.026, hop=0)
- 2. `MainWindow.reset_actor_appearances` (score=0.999, sem=0.457, lex=0.026, hop=0)
- 3. `MainWindow.update_status_display` (score=0.990, sem=0.453, lex=0.000, hop=0)
- 4. `MainWindow.highlight_actor` (score=0.988, sem=0.452, lex=0.053, hop=0)
- 5. `_parse_call_site_lineno` (score=0.982, sem=0.449, lex=0.053, hop=0)

### Query: `pepys year-end reflection` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 8 | 69 | 8 | 0.988 | 0.467 | 0.127 |
| `semantic` | 0.009 | 8 | 69 | 8 | 0.997 | 0.469 | 0.086 |
| `legacy` | 0.010 | 8 | 69 | 8 | 0.995 | 0.468 | 0.082 |

#### Top nodes (hybrid)
- 1. `prune_snapshots` (score=1.000, sem=0.470, lex=0.136, hop=0)
- 2. `save_snapshot` (score=0.998, sem=0.469, lex=0.136, hop=0)
- 3. `SnapshotManager.diff_snapshots` (score=0.990, sem=0.465, lex=0.136, hop=0)
- 4. `GraphStore` (score=0.975, sem=0.467, lex=0.114, hop=1)
- 5. `index` (score=0.974, sem=0.466, lex=0.114, hop=1)

#### Top nodes (semantic)
- 1. `prune_snapshots` (score=1.000, sem=0.470, lex=0.136, hop=0)
- 2. `save_snapshot` (score=0.998, sem=0.469, lex=0.136, hop=0)
- 3. `cmd_snapshot` (score=0.998, sem=0.469, lex=0.091, hop=1)
- 4. `MainWindow.reset_actor_appearances` (score=0.994, sem=0.467, lex=0.023, hop=0)
- 5. `_remove_highlight_actors` (score=0.994, sem=0.467, lex=0.045, hop=1)

#### Top nodes (legacy)
- 1. `prune_snapshots` (score=1.000, sem=0.470, lex=0.136, hop=0)
- 2. `save_snapshot` (score=0.998, sem=0.469, lex=0.136, hop=0)
- 3. `MainWindow.reset_actor_appearances` (score=0.994, sem=0.467, lex=0.023, hop=0)
- 4. `GraphStore.__exit__` (score=0.993, sem=0.467, lex=0.023, hop=0)
- 5. `_extract_distance` (score=0.992, sem=0.466, lex=0.091, hop=0)
