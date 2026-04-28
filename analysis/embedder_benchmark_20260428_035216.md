# Embedder Benchmark Report

> Query cases marked **[pepys]** use real Samuel Pepys diary text (1660–1668) and are intended for evaluation against a DiaryKG index.  All other cases target a PyCodeKG index.

- Started (UTC): 2026-04-28T03:52:16.305458+00:00
- Completed (UTC): 2026-04-28T03:52:51.231636+00:00
- Repo: `/Users/egs/repos/pycode_kg`
- SQLite: `/Users/egs/repos/pycode_kg/.pycodekg/graph.sqlite`
- LanceDB root: `/Users/egs/repos/pycode_kg/.pycodekg/lancedb-benchmark`
- Hybrid weights: semantic=0.7, lexical=0.3

## Model: `BAAI/bge-small-en-v1.5`
- Build: 3.63s, indexed_rows=480, dim=384

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.042 | 8 | 106 | 10 | 0.955 | 0.665 | 0.567 |
| `semantic` | 0.011 | 8 | 106 | 10 | 1.000 | 0.690 | 0.150 |
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
| `hybrid` | 0.025 | 8 | 91 | 8 | 0.944 | 0.646 | 0.582 |
| `semantic` | 0.010 | 8 | 91 | 8 | 0.998 | 0.660 | 0.218 |
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
| `hybrid` | 0.011 | 8 | 135 | 8 | 0.961 | 0.596 | 0.564 |
| `semantic` | 0.010 | 8 | 135 | 8 | 1.000 | 0.598 | 0.436 |
| `legacy` | 0.010 | 8 | 135 | 8 | 0.987 | 0.591 | 0.455 |

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
| `hybrid` | 0.023 | 6 | 6 | 6 | 0.976 | 0.625 | 0.320 |
| `semantic` | 0.009 | 6 | 6 | 6 | 0.974 | 0.626 | 0.240 |
| `legacy` | 0.009 | 6 | 6 | 6 | 0.974 | 0.626 | 0.240 |

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
| `semantic` | 0.009 | 8 | 36 | 8 | 0.994 | 0.514 | 0.065 |
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
| `hybrid` | 0.020 | 8 | 59 | 8 | 0.965 | 0.464 | 0.159 |
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
| `hybrid` | 0.022 | 8 | 40 | 8 | 0.932 | 0.488 | 0.213 |
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
| `hybrid` | 0.019 | 8 | 28 | 8 | 0.976 | 0.485 | 0.121 |
| `semantic` | 0.008 | 8 | 28 | 8 | 0.997 | 0.491 | 0.026 |
| `legacy` | 0.008 | 8 | 28 | 8 | 0.993 | 0.489 | 0.016 |

#### Top nodes (hybrid)
- 1. `KGModule` (score=1.000, sem=0.482, lex=0.158, hop=1)
- 2. `SnapshotManager` (score=0.983, sem=0.484, lex=0.132, hop=1)
- 3. `KGModule.build_graph` (score=0.979, sem=0.482, lex=0.132, hop=1)
- 4. `KGModule.query` (score=0.973, sem=0.490, lex=0.105, hop=1)
- 5. `cmd_build_full` (score=0.944, sem=0.486, lex=0.079, hop=1)

#### Top nodes (semantic)
- 1. `KGModule.__exit__` (score=1.000, sem=0.492, lex=0.053, hop=0)
- 2. `KGModule.close` (score=0.999, sem=0.492, lex=0.026, hop=0)
- 3. `KGModule.store` (score=0.995, sem=0.490, lex=0.000, hop=0)
- 4. `src/pycode_kg/module/base.py.KGModule.query._rank_key` (score=0.995, sem=0.490, lex=0.000, hop=1)
- 5. `KGModule.callers` (score=0.995, sem=0.490, lex=0.053, hop=1)

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
| `hybrid` | 0.020 | 8 | 37 | 8 | 0.974 | 0.511 | 0.141 |
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

## Model: `BAAI/bge-large-en-v1.5`
- Build: 5.94s, indexed_rows=480, dim=1024

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.042 | 8 | 142 | 10 | 0.955 | 0.626 | 0.567 |
| `semantic` | 0.015 | 8 | 142 | 10 | 0.983 | 0.628 | 0.367 |
| `legacy` | 0.015 | 8 | 142 | 10 | 0.982 | 0.628 | 0.450 |

#### Top nodes (hybrid)
- 1. `query_codebase` (score=1.000, sem=0.624, lex=0.667, hop=0)
- 2. `mcp_server` (score=1.000, sem=0.624, lex=0.667, hop=1)
- 3. `pycodekg` (score=0.961, sem=0.624, lex=0.583, hop=0)
- 4. `__init__` (score=0.938, sem=0.639, lex=0.500, hop=0)
- 5. `StructuralImportanceRanker.compute` (score=0.875, sem=0.617, lex=0.417, hop=1)

#### Top nodes (semantic)
- 1. `__init__` (score=1.000, sem=0.639, lex=0.500, hop=0)
- 2. `compute_bridge_centrality` (score=0.980, sem=0.626, lex=0.333, hop=0)
- 3. `bridge` (score=0.980, sem=0.626, lex=0.250, hop=1)
- 4. `__init__` (score=0.977, sem=0.624, lex=0.167, hop=0)
- 5. `pycodekg` (score=0.977, sem=0.624, lex=0.583, hop=0)

#### Top nodes (legacy)
- 1. `__init__` (score=1.000, sem=0.639, lex=0.500, hop=0)
- 2. `compute_bridge_centrality` (score=0.980, sem=0.626, lex=0.333, hop=0)
- 3. `__init__` (score=0.977, sem=0.624, lex=0.167, hop=0)
- 4. `pycodekg` (score=0.977, sem=0.624, lex=0.583, hop=0)
- 5. `query_codebase` (score=0.977, sem=0.624, lex=0.667, hop=0)

### Query: `snapshot metrics over time`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.028 | 8 | 57 | 8 | 0.942 | 0.629 | 0.491 |
| `semantic` | 0.014 | 8 | 57 | 8 | 0.990 | 0.648 | 0.236 |
| `legacy` | 0.015 | 8 | 57 | 8 | 0.972 | 0.636 | 0.364 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.618, lex=0.636, hop=1)
- 2. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.978, sem=0.638, lex=0.545, hop=0)
- 3. `GraphStore.stats` (score=0.953, sem=0.654, lex=0.455, hop=0)
- 4. `SnapshotManager.capture` (score=0.893, sem=0.601, lex=0.455, hop=1)
- 5. `PyCodeKGAnalyzer._analyze_baseline` (score=0.886, sem=0.633, lex=0.364, hop=0)

#### Top nodes (semantic)
- 1. `GraphStore.stats` (score=1.000, sem=0.654, lex=0.455, hop=0)
- 2. `GraphStore.con` (score=1.000, sem=0.654, lex=0.000, hop=1)
- 3. `GraphStore` (score=1.000, sem=0.654, lex=0.182, hop=1)
- 4. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.975, sem=0.638, lex=0.545, hop=0)
- 5. `PyCodeKGAnalyzer` (score=0.975, sem=0.638, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `GraphStore.stats` (score=1.000, sem=0.654, lex=0.455, hop=0)
- 2. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.975, sem=0.638, lex=0.545, hop=0)
- 3. `PyCodeKGAnalyzer._analyze_baseline` (score=0.968, sem=0.633, lex=0.364, hop=0)
- 4. `KGExtractor.coverage_metric` (score=0.966, sem=0.632, lex=0.273, hop=0)
- 5. `BuildStats` (score=0.949, sem=0.621, lex=0.182, hop=0)

### Query: `MCP tool exposure`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.015 | 8 | 141 | 8 | 0.952 | 0.599 | 0.564 |
| `semantic` | 0.015 | 8 | 141 | 8 | 1.000 | 0.610 | 0.436 |
| `legacy` | 0.014 | 8 | 141 | 8 | 0.952 | 0.580 | 0.400 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.610, lex=0.636, hop=0)
- 2. `analyze_repo` (score=1.000, sem=0.610, lex=0.636, hop=1)
- 3. `KGExtractor` (score=0.938, sem=0.555, lex=0.636, hop=0)
- 4. `_parse_args` (score=0.912, sem=0.610, lex=0.455, hop=1)
- 5. `main` (score=0.912, sem=0.610, lex=0.455, hop=1)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.610, lex=0.636, hop=0)
- 2. `_get_snapshot_mgr` (score=1.000, sem=0.610, lex=0.273, hop=1)
- 3. `_parse_args` (score=1.000, sem=0.610, lex=0.455, hop=1)
- 4. `_snapshot_freshness` (score=1.000, sem=0.610, lex=0.182, hop=1)
- 5. `analyze_repo` (score=1.000, sem=0.610, lex=0.636, hop=1)

#### Top nodes (legacy)
- 1. `mcp_server` (score=1.000, sem=0.610, lex=0.636, hop=0)
- 2. `explain` (score=0.955, sem=0.582, lex=0.273, hop=0)
- 3. `explain_rank` (score=0.937, sem=0.571, lex=0.364, hop=0)
- 4. `query_codebase` (score=0.934, sem=0.569, lex=0.364, hop=0)
- 5. `graph_stats` (score=0.933, sem=0.569, lex=0.364, hop=0)

### Query: `node missing line number`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.026 | 6 | 6 | 6 | 0.922 | 0.583 | 0.240 |
| `semantic` | 0.013 | 6 | 6 | 6 | 0.952 | 0.583 | 0.180 |
| `legacy` | 0.013 | 6 | 6 | 6 | 0.952 | 0.583 | 0.180 |

#### Top nodes (hybrid)
- 1. `NodeSpec` (score=1.000, sem=0.573, lex=0.400, hop=0)
- 2. `PyCodeKGVisitor._set_node_source_meta` (score=0.996, sem=0.613, lex=0.300, hop=0)
- 3. `get_node` (score=0.937, sem=0.569, lex=0.300, hop=0)
- 4. `LayoutNode.line_count` (score=0.854, sem=0.592, lex=0.100, hop=0)
- 5. `KGModule.node` (score=0.822, sem=0.569, lex=0.100, hop=0)

#### Top nodes (semantic)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.613, lex=0.300, hop=0)
- 2. `LayoutNode.line_count` (score=0.967, sem=0.592, lex=0.100, hop=0)
- 3. `NodeSpec` (score=0.935, sem=0.573, lex=0.400, hop=0)
- 4. `_NodeInfo` (score=0.929, sem=0.569, lex=0.000, hop=0)
- 5. `KGModule.node` (score=0.928, sem=0.569, lex=0.100, hop=0)

#### Top nodes (legacy)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.613, lex=0.300, hop=0)
- 2. `LayoutNode.line_count` (score=0.967, sem=0.592, lex=0.100, hop=0)
- 3. `NodeSpec` (score=0.935, sem=0.573, lex=0.400, hop=0)
- 4. `_NodeInfo` (score=0.929, sem=0.569, lex=0.000, hop=0)
- 5. `KGModule.node` (score=0.928, sem=0.569, lex=0.100, hop=0)

### Query: `pepys naval fleet and king` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.025 | 8 | 54 | 8 | 0.969 | 0.462 | 0.123 |
| `semantic` | 0.014 | 8 | 54 | 8 | 0.999 | 0.463 | 0.052 |
| `legacy` | 0.014 | 8 | 54 | 8 | 0.998 | 0.462 | 0.077 |

#### Top nodes (hybrid)
- 1. `download_model` (score=1.000, sem=0.462, lex=0.161, hop=0)
- 2. `_render_legend` (score=0.974, sem=0.462, lex=0.129, hop=0)
- 3. `_tab_snippets` (score=0.974, sem=0.462, lex=0.129, hop=1)
- 4. `cmd_build_full` (score=0.951, sem=0.463, lex=0.097, hop=1)
- 5. `_tab_graph` (score=0.948, sem=0.462, lex=0.097, hop=1)

#### Top nodes (semantic)
- 1. `_common_options` (score=1.000, sem=0.463, lex=0.065, hop=0)
- 2. `cmd_build_full` (score=1.000, sem=0.463, lex=0.097, hop=1)
- 3. `main` (score=0.999, sem=0.463, lex=0.000, hop=0)
- 4. `cmd_bridges` (score=0.999, sem=0.463, lex=0.065, hop=1)
- 5. `__main__` (score=0.998, sem=0.462, lex=0.032, hop=0)

#### Top nodes (legacy)
- 1. `_common_options` (score=1.000, sem=0.463, lex=0.065, hop=0)
- 2. `main` (score=0.999, sem=0.463, lex=0.000, hop=0)
- 3. `__main__` (score=0.998, sem=0.462, lex=0.032, hop=0)
- 4. `_render_legend` (score=0.997, sem=0.462, lex=0.129, hop=0)
- 5. `download_model` (score=0.997, sem=0.462, lex=0.161, hop=0)

### Query: `pepys music and viol` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.024 | 8 | 66 | 8 | 0.976 | 0.452 | 0.138 |
| `semantic` | 0.014 | 8 | 66 | 8 | 0.999 | 0.457 | 0.048 |
| `legacy` | 0.014 | 8 | 66 | 8 | 0.987 | 0.452 | 0.048 |

#### Top nodes (hybrid)
- 1. `GraphStore.callers_of` (score=1.000, sem=0.450, lex=0.172, hop=1)
- 2. `Snapshot` (score=0.996, sem=0.448, lex=0.172, hop=1)
- 3. `coderank` (score=0.982, sem=0.455, lex=0.138, hop=1)
- 4. `MainWindow.on_pick` (score=0.958, sem=0.458, lex=0.103, hop=1)
- 5. `GraphStore._is_compatible_stub_caller` (score=0.944, sem=0.450, lex=0.103, hop=0)

#### Top nodes (semantic)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.458, lex=0.034, hop=0)
- 2. `_remove_highlight_actors` (score=1.000, sem=0.458, lex=0.034, hop=1)
- 3. `MainWindow.highlight_actor` (score=1.000, sem=0.458, lex=0.034, hop=1)
- 4. `MainWindow.on_pick` (score=1.000, sem=0.458, lex=0.103, hop=1)
- 5. `_safe_norm_sum` (score=0.995, sem=0.455, lex=0.034, hop=0)

#### Top nodes (legacy)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.458, lex=0.034, hop=0)
- 2. `_safe_norm_sum` (score=0.995, sem=0.455, lex=0.034, hop=0)
- 3. `GraphStore._is_compatible_stub_caller` (score=0.983, sem=0.450, lex=0.103, hop=0)
- 4. `Snapshot.vs_previous` (score=0.979, sem=0.448, lex=0.000, hop=0)
- 5. `StructuralImportanceRanker.write_scores` (score=0.979, sem=0.448, lex=0.069, hop=0)

### Query: `pepys plague and naval failure` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.026 | 8 | 102 | 8 | 0.932 | 0.450 | 0.226 |
| `semantic` | 0.014 | 8 | 102 | 8 | 0.999 | 0.453 | 0.111 |
| `legacy` | 0.015 | 8 | 102 | 8 | 0.995 | 0.451 | 0.140 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.450, lex=0.319, hop=1)
- 2. `main` (score=0.973, sem=0.453, lex=0.277, hop=0)
- 3. `explain` (score=0.907, sem=0.450, lex=0.191, hop=0)
- 4. `find_definition_at` (score=0.907, sem=0.450, lex=0.191, hop=1)
- 5. `PyCodeKGAnalyzer._analyze_inheritance` (score=0.872, sem=0.448, lex=0.149, hop=1)

#### Top nodes (semantic)
- 1. `main` (score=1.000, sem=0.453, lex=0.277, hop=0)
- 2. `_default_report_name` (score=1.000, sem=0.453, lex=0.000, hop=1)
- 3. `PyCodeKGAnalyzer` (score=1.000, sem=0.453, lex=0.085, hop=1)
- 4. `pycodekg_thorough_analysis` (score=1.000, sem=0.453, lex=0.128, hop=1)
- 5. `cmd_build_full` (score=0.996, sem=0.451, lex=0.064, hop=0)

#### Top nodes (legacy)
- 1. `main` (score=1.000, sem=0.453, lex=0.277, hop=0)
- 2. `cmd_build_full` (score=0.996, sem=0.451, lex=0.064, hop=0)
- 3. `explain` (score=0.994, sem=0.450, lex=0.191, hop=0)
- 4. `GraphStore.edges_from` (score=0.992, sem=0.450, lex=0.128, hop=0)
- 5. `build` (score=0.990, sem=0.448, lex=0.043, hop=0)

### Query: `pepys treasury and accounts` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.025 | 8 | 38 | 8 | 0.948 | 0.441 | 0.168 |
| `semantic` | 0.015 | 8 | 38 | 8 | 0.999 | 0.443 | 0.047 |
| `legacy` | 0.015 | 8 | 38 | 8 | 0.996 | 0.442 | 0.032 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.439, lex=0.237, hop=1)
- 2. `snapshot_list` (score=0.979, sem=0.439, lex=0.211, hop=1)
- 3. `SnapshotManager` (score=0.925, sem=0.444, lex=0.132, hop=1)
- 4. `Snapshot` (score=0.920, sem=0.441, lex=0.132, hop=1)
- 5. `snapshot_diff` (score=0.917, sem=0.439, lex=0.132, hop=1)

#### Top nodes (semantic)
- 1. `SnapshotManager.get_baseline` (score=1.000, sem=0.444, lex=0.000, hop=0)
- 2. `_rewrap` (score=1.000, sem=0.444, lex=0.000, hop=1)
- 3. `SnapshotManager` (score=1.000, sem=0.444, lex=0.132, hop=1)
- 4. `MainWindow.on_status_change` (score=0.998, sem=0.443, lex=0.053, hop=0)
- 5. `SnapshotManager._compute_delta` (score=0.997, sem=0.442, lex=0.053, hop=0)

#### Top nodes (legacy)
- 1. `SnapshotManager.get_baseline` (score=1.000, sem=0.444, lex=0.000, hop=0)
- 2. `MainWindow.on_status_change` (score=0.998, sem=0.443, lex=0.053, hop=0)
- 3. `SnapshotManager._compute_delta` (score=0.997, sem=0.442, lex=0.053, hop=0)
- 4. `Snapshot.vs_previous` (score=0.995, sem=0.441, lex=0.000, hop=0)
- 5. `_get_snapshot_mgr` (score=0.990, sem=0.439, lex=0.053, hop=0)

### Query: `pepys year-end reflection` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.025 | 8 | 76 | 8 | 0.960 | 0.473 | 0.132 |
| `semantic` | 0.015 | 8 | 76 | 8 | 1.000 | 0.474 | 0.055 |
| `legacy` | 0.015 | 8 | 76 | 8 | 0.999 | 0.473 | 0.041 |

#### Top nodes (hybrid)
- 1. `main` (score=1.000, sem=0.473, lex=0.182, hop=0)
- 2. `Snapshot` (score=0.963, sem=0.473, lex=0.136, hop=1)
- 3. `PyCodeKGAnalyzer._analyze_inheritance` (score=0.960, sem=0.471, lex=0.136, hop=0)
- 4. `GraphStore` (score=0.947, sem=0.473, lex=0.114, hop=1)
- 5. `SnapshotManager` (score=0.930, sem=0.474, lex=0.091, hop=1)

#### Top nodes (semantic)
- 1. `SnapshotManager.get_previous` (score=1.000, sem=0.474, lex=0.000, hop=0)
- 2. `_rewrap` (score=1.000, sem=0.474, lex=0.000, hop=1)
- 3. `SnapshotManager` (score=1.000, sem=0.474, lex=0.091, hop=1)
- 4. `main` (score=0.999, sem=0.473, lex=0.182, hop=0)
- 5. `_default_report_name` (score=0.999, sem=0.473, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `SnapshotManager.get_previous` (score=1.000, sem=0.474, lex=0.000, hop=0)
- 2. `main` (score=0.999, sem=0.473, lex=0.182, hop=0)
- 3. `GraphStore.__exit__` (score=0.999, sem=0.473, lex=0.023, hop=0)
- 4. `_done` (score=0.999, sem=0.473, lex=0.000, hop=0)
- 5. `Snapshot.vs_previous` (score=0.998, sem=0.473, lex=0.000, hop=0)

## Model: `sentence-transformers/all-MiniLM-L6-v2`
- Build: 0.48s, indexed_rows=480, dim=384

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.013 | 8 | 118 | 10 | 0.965 | 0.550 | 0.483 |
| `semantic` | 0.007 | 8 | 118 | 10 | 0.983 | 0.561 | 0.317 |
| `legacy` | 0.008 | 8 | 118 | 10 | 0.967 | 0.552 | 0.367 |

#### Top nodes (hybrid)
- 1. `__init__` (score=1.000, sem=0.571, lex=0.500, hop=0)
- 2. `query` (score=0.997, sem=0.568, lex=0.500, hop=0)
- 3. `pycodekg` (score=0.982, sem=0.521, lex=0.583, hop=0)
- 4. `GraphStore` (score=0.923, sem=0.546, lex=0.417, hop=0)
- 5. `GraphStore.resolve_symbols` (score=0.923, sem=0.546, lex=0.417, hop=1)

#### Top nodes (semantic)
- 1. `__init__` (score=1.000, sem=0.571, lex=0.500, hop=0)
- 2. `query` (score=0.996, sem=0.568, lex=0.500, hop=0)
- 3. `cmd_query` (score=0.996, sem=0.568, lex=0.250, hop=1)
- 4. `QueryResult` (score=0.961, sem=0.549, lex=0.250, hop=0)
- 5. `QueryResult.print_summary` (score=0.961, sem=0.549, lex=0.083, hop=1)

#### Top nodes (legacy)
- 1. `__init__` (score=1.000, sem=0.571, lex=0.500, hop=0)
- 2. `query` (score=0.996, sem=0.568, lex=0.500, hop=0)
- 3. `QueryResult` (score=0.961, sem=0.549, lex=0.250, hop=0)
- 4. `GraphStore` (score=0.956, sem=0.546, lex=0.417, hop=0)
- 5. `GraphStore.edges_from` (score=0.924, sem=0.528, lex=0.167, hop=0)

### Query: `snapshot metrics over time`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 8 | 94 | 8 | 0.922 | 0.493 | 0.564 |
| `semantic` | 0.007 | 8 | 94 | 8 | 0.983 | 0.515 | 0.236 |
| `legacy` | 0.007 | 8 | 94 | 8 | 0.973 | 0.510 | 0.382 |

#### Top nodes (hybrid)
- 1. `snapshot_list` (score=1.000, sem=0.484, lex=0.727, hop=0)
- 2. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.952, sem=0.524, lex=0.545, hop=0)
- 3. `mcp_server` (score=0.951, sem=0.484, lex=0.636, hop=1)
- 4. `GraphStore.stats` (score=0.860, sem=0.490, lex=0.455, hop=0)
- 5. `SnapshotManager.capture` (score=0.848, sem=0.480, lex=0.455, hop=0)

#### Top nodes (semantic)
- 1. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=1.000, sem=0.524, lex=0.545, hop=0)
- 2. `graph_stats` (score=0.983, sem=0.515, lex=0.364, hop=0)
- 3. `_get_kg` (score=0.983, sem=0.515, lex=0.000, hop=1)
- 4. `PyCodeKGAnalyzer._get_report_metadata` (score=0.975, sem=0.511, lex=0.182, hop=0)
- 5. `PyCodeKGAnalyzer._write_report` (score=0.975, sem=0.511, lex=0.091, hop=1)

#### Top nodes (legacy)
- 1. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=1.000, sem=0.524, lex=0.545, hop=0)
- 2. `graph_stats` (score=0.983, sem=0.515, lex=0.364, hop=0)
- 3. `PyCodeKGAnalyzer._get_report_metadata` (score=0.975, sem=0.511, lex=0.182, hop=0)
- 4. `save_snapshot` (score=0.974, sem=0.511, lex=0.364, hop=0)
- 5. `GraphStore.stats` (score=0.934, sem=0.490, lex=0.455, hop=0)

### Query: `MCP tool exposure`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.008 | 8 | 122 | 8 | 0.927 | 0.478 | 0.509 |
| `semantic` | 0.008 | 8 | 122 | 8 | 1.000 | 0.478 | 0.436 |
| `legacy` | 0.008 | 8 | 122 | 8 | 0.954 | 0.456 | 0.400 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.478, lex=0.636, hop=0)
- 2. `analyze_repo` (score=1.000, sem=0.478, lex=0.636, hop=1)
- 3. `_parse_args` (score=0.896, sem=0.478, lex=0.455, hop=1)
- 4. `main` (score=0.896, sem=0.478, lex=0.455, hop=1)
- 5. `get_node` (score=0.844, sem=0.478, lex=0.364, hop=1)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.478, lex=0.636, hop=0)
- 2. `_get_snapshot_mgr` (score=1.000, sem=0.478, lex=0.273, hop=1)
- 3. `_parse_args` (score=1.000, sem=0.478, lex=0.455, hop=1)
- 4. `_snapshot_freshness` (score=1.000, sem=0.478, lex=0.182, hop=1)
- 5. `analyze_repo` (score=1.000, sem=0.478, lex=0.636, hop=1)

#### Top nodes (legacy)
- 1. `mcp_server` (score=1.000, sem=0.478, lex=0.636, hop=0)
- 2. `__init__` (score=0.950, sem=0.454, lex=0.364, hop=0)
- 3. `query_codebase` (score=0.948, sem=0.453, lex=0.364, hop=0)
- 4. `framework_nodes` (score=0.943, sem=0.451, lex=0.273, hop=0)
- 5. `explain_rank` (score=0.927, sem=0.443, lex=0.364, hop=0)

### Query: `node missing line number`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.010 | 6 | 6 | 6 | 0.876 | 0.434 | 0.300 |
| `semantic` | 0.006 | 6 | 6 | 6 | 0.971 | 0.434 | 0.300 |
| `legacy` | 0.006 | 6 | 6 | 6 | 0.971 | 0.434 | 0.300 |

#### Top nodes (hybrid)
- 1. `find_definition_at` (score=1.000, sem=0.428, lex=0.500, hop=0)
- 2. `NodeSpec` (score=0.956, sem=0.443, lex=0.400, hop=0)
- 3. `PyCodeKGVisitor._set_node_source_meta` (score=0.896, sem=0.447, lex=0.300, hop=0)
- 4. `_parse_call_site_lineno` (score=0.800, sem=0.428, lex=0.200, hop=0)
- 5. `CodeGraph` (score=0.726, sem=0.424, lex=0.100, hop=0)

#### Top nodes (semantic)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.447, lex=0.300, hop=0)
- 2. `NodeSpec` (score=0.990, sem=0.443, lex=0.400, hop=0)
- 3. `_parse_call_site_lineno` (score=0.958, sem=0.428, lex=0.200, hop=0)
- 4. `find_definition_at` (score=0.958, sem=0.428, lex=0.500, hop=0)
- 5. `CodeGraph` (score=0.948, sem=0.424, lex=0.100, hop=0)

#### Top nodes (legacy)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.447, lex=0.300, hop=0)
- 2. `NodeSpec` (score=0.990, sem=0.443, lex=0.400, hop=0)
- 3. `_parse_call_site_lineno` (score=0.958, sem=0.428, lex=0.200, hop=0)
- 4. `find_definition_at` (score=0.958, sem=0.428, lex=0.500, hop=0)
- 5. `CodeGraph` (score=0.948, sem=0.424, lex=0.100, hop=0)

### Query: `pepys naval fleet and king` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.012 | 8 | 42 | 8 | 0.978 | 0.361 | 0.110 |
| `semantic` | 0.007 | 8 | 42 | 8 | 0.994 | 0.364 | 0.071 |
| `legacy` | 0.006 | 8 | 42 | 8 | 0.990 | 0.362 | 0.045 |

#### Top nodes (hybrid)
- 1. `MainWindow.on_pick` (score=1.000, sem=0.362, lex=0.129, hop=1)
- 2. `MainWindow` (score=1.000, sem=0.362, lex=0.129, hop=1)
- 3. `MainWindow.highlight_actor` (score=0.967, sem=0.362, lex=0.097, hop=0)
- 4. `main` (score=0.962, sem=0.360, lex=0.097, hop=1)
- 5. `app` (score=0.962, sem=0.360, lex=0.097, hop=1)

#### Top nodes (semantic)
- 1. `viz` (score=1.000, sem=0.366, lex=0.032, hop=0)
- 2. `cmd_viz` (score=1.000, sem=0.366, lex=0.065, hop=1)
- 3. `MainWindow.highlight_actor` (score=0.990, sem=0.362, lex=0.097, hop=0)
- 4. `MainWindow.on_pick` (score=0.990, sem=0.362, lex=0.129, hop=1)
- 5. `MainWindow.reset_camera` (score=0.990, sem=0.362, lex=0.032, hop=1)

#### Top nodes (legacy)
- 1. `viz` (score=1.000, sem=0.366, lex=0.032, hop=0)
- 2. `MainWindow.highlight_actor` (score=0.990, sem=0.362, lex=0.097, hop=0)
- 3. `MainWindow.reset_actor_appearances` (score=0.988, sem=0.362, lex=0.032, hop=0)
- 4. `pycodekg_viz3d` (score=0.987, sem=0.361, lex=0.000, hop=0)
- 5. `cmd_mcp` (score=0.987, sem=0.361, lex=0.065, hop=0)

### Query: `pepys music and viol` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 8 | 36 | 8 | 0.958 | 0.362 | 0.117 |
| `semantic` | 0.007 | 8 | 36 | 8 | 0.963 | 0.363 | 0.076 |
| `legacy` | 0.007 | 8 | 36 | 8 | 0.958 | 0.361 | 0.062 |

#### Top nodes (hybrid)
- 1. `layout3d` (score=1.000, sem=0.356, lex=0.172, hop=1)
- 2. `build_pycodekg_lancedb` (score=0.979, sem=0.377, lex=0.103, hop=0)
- 3. `main` (score=0.942, sem=0.361, lex=0.103, hop=1)
- 4. `app` (score=0.942, sem=0.361, lex=0.103, hop=1)
- 5. `build_pycodekg_sqlite` (score=0.929, sem=0.355, lex=0.103, hop=0)

#### Top nodes (semantic)
- 1. `build_pycodekg_lancedb` (score=1.000, sem=0.377, lex=0.103, hop=0)
- 2. `_inject_css` (score=0.957, sem=0.361, lex=0.000, hop=0)
- 3. `main` (score=0.957, sem=0.361, lex=0.103, hop=1)
- 4. `app` (score=0.957, sem=0.361, lex=0.103, hop=1)
- 5. `_golden_spiral_2d` (score=0.945, sem=0.356, lex=0.069, hop=0)

#### Top nodes (legacy)
- 1. `build_pycodekg_lancedb` (score=1.000, sem=0.377, lex=0.103, hop=0)
- 2. `_inject_css` (score=0.957, sem=0.361, lex=0.000, hop=0)
- 3. `_golden_spiral_2d` (score=0.945, sem=0.356, lex=0.069, hop=0)
- 4. `_init_state` (score=0.945, sem=0.356, lex=0.034, hop=0)
- 5. `build_pycodekg_sqlite` (score=0.943, sem=0.355, lex=0.103, hop=0)

### Query: `pepys plague and naval failure` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.010 | 8 | 51 | 8 | 0.973 | 0.339 | 0.179 |
| `semantic` | 0.007 | 8 | 51 | 8 | 0.978 | 0.341 | 0.106 |
| `legacy` | 0.007 | 8 | 51 | 8 | 0.974 | 0.340 | 0.089 |

#### Top nodes (hybrid)
- 1. `_build_index_text` (score=1.000, sem=0.335, lex=0.213, hop=1)
- 2. `layout3d` (score=0.985, sem=0.338, lex=0.191, hop=1)
- 3. `SemanticIndex` (score=0.977, sem=0.335, lex=0.191, hop=1)
- 4. `SemanticIndex.build` (score=0.957, sem=0.335, lex=0.170, hop=0)
- 5. `fibonacci_sphere` (score=0.946, sem=0.349, lex=0.128, hop=0)

#### Top nodes (semantic)
- 1. `fibonacci_sphere` (score=1.000, sem=0.349, lex=0.128, hop=0)
- 2. `_golden_spiral_2d` (score=0.976, sem=0.341, lex=0.085, hop=0)
- 3. `FunnelLayout.compute` (score=0.976, sem=0.341, lex=0.106, hop=1)
- 4. `fibonacci_annulus` (score=0.969, sem=0.338, lex=0.106, hop=0)
- 5. `AlliumLayout.compute` (score=0.969, sem=0.338, lex=0.106, hop=1)

#### Top nodes (legacy)
- 1. `fibonacci_sphere` (score=1.000, sem=0.349, lex=0.128, hop=0)
- 2. `_golden_spiral_2d` (score=0.976, sem=0.341, lex=0.085, hop=0)
- 3. `fibonacci_annulus` (score=0.969, sem=0.338, lex=0.106, hop=0)
- 4. `MainWindow._h2` (score=0.962, sem=0.336, lex=0.021, hop=0)
- 5. `SemanticIndex._read_nodes` (score=0.962, sem=0.336, lex=0.106, hop=0)

### Query: `pepys treasury and accounts` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 8 | 48 | 8 | 0.942 | 0.353 | 0.100 |
| `semantic` | 0.007 | 8 | 48 | 8 | 0.989 | 0.356 | 0.011 |
| `legacy` | 0.007 | 8 | 48 | 8 | 0.984 | 0.354 | 0.037 |

#### Top nodes (hybrid)
- 1. `KGModule` (score=1.000, sem=0.353, lex=0.158, hop=1)
- 2. `KGModule.build_graph` (score=0.973, sem=0.353, lex=0.132, hop=1)
- 3. `KGModule.__init__` (score=0.946, sem=0.353, lex=0.105, hop=0)
- 4. `MainWindow` (score=0.905, sem=0.347, lex=0.079, hop=1)
- 5. `KGModule.build_index` (score=0.883, sem=0.360, lex=0.026, hop=0)

#### Top nodes (semantic)
- 1. `KGModule.build_index` (score=1.000, sem=0.360, lex=0.026, hop=0)
- 2. `KGModule.store` (score=1.000, sem=0.360, lex=0.000, hop=1)
- 3. `KGModule.embedder` (score=0.982, sem=0.354, lex=0.026, hop=0)
- 4. `KGModule.index` (score=0.982, sem=0.354, lex=0.000, hop=1)
- 5. `KGModule.build` (score=0.981, sem=0.353, lex=0.000, hop=0)

#### Top nodes (legacy)
- 1. `KGModule.build_index` (score=1.000, sem=0.360, lex=0.026, hop=0)
- 2. `KGModule.embedder` (score=0.982, sem=0.354, lex=0.026, hop=0)
- 3. `KGModule.build` (score=0.981, sem=0.353, lex=0.000, hop=0)
- 4. `KGModule.__init__` (score=0.980, sem=0.353, lex=0.105, hop=0)
- 5. `KGModule.close` (score=0.975, sem=0.351, lex=0.026, hop=0)

### Query: `pepys year-end reflection` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 8 | 65 | 8 | 0.942 | 0.357 | 0.145 |
| `semantic` | 0.007 | 8 | 65 | 8 | 0.991 | 0.366 | 0.023 |
| `legacy` | 0.007 | 8 | 65 | 8 | 0.982 | 0.363 | 0.032 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.358, lex=0.205, hop=1)
- 2. `prune_snapshots` (score=0.937, sem=0.359, lex=0.136, hop=0)
- 3. `Snapshot` (score=0.935, sem=0.358, lex=0.136, hop=1)
- 4. `save_snapshot` (score=0.925, sem=0.354, lex=0.136, hop=1)
- 5. `snapshot_list` (score=0.913, sem=0.358, lex=0.114, hop=0)

#### Top nodes (semantic)
- 1. `list_snapshots` (score=1.000, sem=0.370, lex=0.023, hop=0)
- 2. `SnapshotManager.get_previous` (score=0.991, sem=0.366, lex=0.000, hop=0)
- 3. `_rewrap` (score=0.991, sem=0.366, lex=0.000, hop=1)
- 4. `SnapshotManager` (score=0.991, sem=0.366, lex=0.091, hop=1)
- 5. `viz_timeline` (score=0.982, sem=0.363, lex=0.000, hop=0)

#### Top nodes (legacy)
- 1. `list_snapshots` (score=1.000, sem=0.370, lex=0.023, hop=0)
- 2. `SnapshotManager.get_previous` (score=0.991, sem=0.366, lex=0.000, hop=0)
- 3. `viz_timeline` (score=0.982, sem=0.363, lex=0.000, hop=0)
- 4. `prune_snapshots` (score=0.971, sem=0.359, lex=0.136, hop=0)
- 5. `Snapshot.vs_previous` (score=0.968, sem=0.358, lex=0.000, hop=0)

## Model: `sentence-transformers/all-MiniLM-L12-v2`
- Build: 0.69s, indexed_rows=480, dim=384

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.012 | 8 | 94 | 10 | 0.929 | 0.533 | 0.517 |
| `semantic` | 0.010 | 8 | 94 | 10 | 0.984 | 0.543 | 0.233 |
| `legacy` | 0.009 | 8 | 94 | 10 | 0.965 | 0.532 | 0.467 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.526, lex=0.667, hop=1)
- 2. `__init__` (score=0.943, sem=0.551, lex=0.500, hop=0)
- 3. `graph_stats` (score=0.912, sem=0.526, lex=0.500, hop=0)
- 4. `query` (score=0.907, sem=0.522, lex=0.500, hop=0)
- 5. `GraphStore` (score=0.885, sem=0.540, lex=0.417, hop=0)

#### Top nodes (semantic)
- 1. `__init__` (score=1.000, sem=0.551, lex=0.500, hop=0)
- 2. `GraphStore` (score=0.980, sem=0.540, lex=0.417, hop=0)
- 3. `GraphStore.__enter__` (score=0.980, sem=0.540, lex=0.083, hop=1)
- 4. `GraphStore.__exit__` (score=0.980, sem=0.540, lex=0.083, hop=1)
- 5. `GraphStore.__init__` (score=0.980, sem=0.540, lex=0.083, hop=1)

#### Top nodes (legacy)
- 1. `__init__` (score=1.000, sem=0.551, lex=0.500, hop=0)
- 2. `GraphStore` (score=0.980, sem=0.540, lex=0.417, hop=0)
- 3. `graph_stats` (score=0.954, sem=0.526, lex=0.500, hop=0)
- 4. `query` (score=0.946, sem=0.522, lex=0.500, hop=0)
- 5. `SemanticIndex` (score=0.943, sem=0.520, lex=0.417, hop=0)

### Query: `snapshot metrics over time`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.012 | 8 | 78 | 8 | 0.928 | 0.500 | 0.527 |
| `semantic` | 0.009 | 8 | 78 | 8 | 0.990 | 0.513 | 0.291 |
| `legacy` | 0.009 | 8 | 78 | 8 | 0.950 | 0.492 | 0.455 |

#### Top nodes (hybrid)
- 1. `snapshot_diff` (score=1.000, sem=0.510, lex=0.636, hop=0)
- 2. `mcp_server` (score=1.000, sem=0.510, lex=0.636, hop=1)
- 3. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.961, sem=0.518, lex=0.545, hop=0)
- 4. `GraphStore.stats` (score=0.870, sem=0.486, lex=0.455, hop=0)
- 5. `save_snapshot` (score=0.807, sem=0.475, lex=0.364, hop=0)

#### Top nodes (semantic)
- 1. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=1.000, sem=0.518, lex=0.545, hop=0)
- 2. `PyCodeKGAnalyzer` (score=1.000, sem=0.518, lex=0.000, hop=1)
- 3. `snapshot_diff` (score=0.984, sem=0.510, lex=0.636, hop=0)
- 4. `_get_snapshot_mgr` (score=0.984, sem=0.510, lex=0.000, hop=1)
- 5. `_snapshot_freshness` (score=0.984, sem=0.510, lex=0.273, hop=1)

#### Top nodes (legacy)
- 1. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=1.000, sem=0.518, lex=0.545, hop=0)
- 2. `snapshot_diff` (score=0.984, sem=0.510, lex=0.636, hop=0)
- 3. `GraphStore.stats` (score=0.939, sem=0.486, lex=0.455, hop=0)
- 4. `save_snapshot` (score=0.918, sem=0.475, lex=0.364, hop=0)
- 5. `analyze` (score=0.909, sem=0.471, lex=0.273, hop=0)

### Query: `MCP tool exposure`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.010 | 8 | 123 | 8 | 0.930 | 0.502 | 0.509 |
| `semantic` | 0.010 | 8 | 123 | 8 | 1.000 | 0.502 | 0.436 |
| `legacy` | 0.010 | 8 | 123 | 8 | 0.945 | 0.474 | 0.382 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.502, lex=0.636, hop=0)
- 2. `analyze_repo` (score=1.000, sem=0.502, lex=0.636, hop=1)
- 3. `_parse_args` (score=0.899, sem=0.502, lex=0.455, hop=1)
- 4. `main` (score=0.899, sem=0.502, lex=0.455, hop=1)
- 5. `get_node` (score=0.849, sem=0.502, lex=0.364, hop=1)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.502, lex=0.636, hop=0)
- 2. `_get_snapshot_mgr` (score=1.000, sem=0.502, lex=0.273, hop=1)
- 3. `_parse_args` (score=1.000, sem=0.502, lex=0.455, hop=1)
- 4. `_snapshot_freshness` (score=1.000, sem=0.502, lex=0.182, hop=1)
- 5. `analyze_repo` (score=1.000, sem=0.502, lex=0.636, hop=1)

#### Top nodes (legacy)
- 1. `mcp_server` (score=1.000, sem=0.502, lex=0.636, hop=0)
- 2. `graph_stats` (score=0.976, sem=0.490, lex=0.364, hop=0)
- 3. `_enrich_edges_with_provenance` (score=0.933, sem=0.468, lex=0.182, hop=0)
- 4. `query_codebase` (score=0.924, sem=0.464, lex=0.364, hop=0)
- 5. `explain_rank` (score=0.890, sem=0.447, lex=0.364, hop=0)

### Query: `node missing line number`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.013 | 6 | 6 | 6 | 0.933 | 0.432 | 0.320 |
| `semantic` | 0.009 | 6 | 6 | 6 | 0.899 | 0.432 | 0.260 |
| `legacy` | 0.008 | 6 | 6 | 6 | 0.899 | 0.432 | 0.260 |

#### Top nodes (hybrid)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.481, lex=0.300, hop=0)
- 2. `NodeSpec` (score=0.963, sem=0.416, lex=0.400, hop=0)
- 3. `compute_span` (score=0.960, sem=0.414, lex=0.400, hop=0)
- 4. `get_node` (score=0.891, sem=0.415, lex=0.300, hop=0)
- 5. `_parse_call_site_lineno` (score=0.852, sem=0.434, lex=0.200, hop=0)

#### Top nodes (semantic)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.481, lex=0.300, hop=0)
- 2. `_parse_call_site_lineno` (score=0.901, sem=0.434, lex=0.200, hop=0)
- 3. `LayoutNode.line_count` (score=0.866, sem=0.417, lex=0.100, hop=0)
- 4. `NodeSpec` (score=0.864, sem=0.416, lex=0.400, hop=0)
- 5. `get_node` (score=0.861, sem=0.415, lex=0.300, hop=0)

#### Top nodes (legacy)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.481, lex=0.300, hop=0)
- 2. `_parse_call_site_lineno` (score=0.901, sem=0.434, lex=0.200, hop=0)
- 3. `LayoutNode.line_count` (score=0.866, sem=0.417, lex=0.100, hop=0)
- 4. `NodeSpec` (score=0.864, sem=0.416, lex=0.400, hop=0)
- 5. `get_node` (score=0.861, sem=0.415, lex=0.300, hop=0)

### Query: `pepys naval fleet and king` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.010 | 8 | 59 | 8 | 0.947 | 0.368 | 0.168 |
| `semantic` | 0.009 | 8 | 59 | 8 | 0.987 | 0.373 | 0.026 |
| `legacy` | 0.009 | 8 | 59 | 8 | 0.979 | 0.370 | 0.084 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.368, lex=0.226, hop=1)
- 2. `pack_snippets` (score=0.971, sem=0.368, lex=0.194, hop=0)
- 3. `viz3d` (score=0.942, sem=0.368, lex=0.161, hop=1)
- 4. `MainWindow.on_pick` (score=0.911, sem=0.368, lex=0.129, hop=1)
- 5. `MainWindow` (score=0.911, sem=0.368, lex=0.129, hop=1)

#### Top nodes (semantic)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.378, lex=0.032, hop=0)
- 2. `MainWindow.reset_picking_state` (score=1.000, sem=0.378, lex=0.000, hop=1)
- 3. `load_snapshots_timeline` (score=0.978, sem=0.370, lex=0.032, hop=0)
- 4. `create_timeline_figure` (score=0.978, sem=0.370, lex=0.032, hop=1)
- 5. `display_timeline_summary` (score=0.978, sem=0.370, lex=0.032, hop=1)

#### Top nodes (legacy)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.378, lex=0.032, hop=0)
- 2. `load_snapshots_timeline` (score=0.978, sem=0.370, lex=0.032, hop=0)
- 3. `_remove_highlight_actors` (score=0.973, sem=0.368, lex=0.065, hop=0)
- 4. `MainWindow.highlight_actor` (score=0.973, sem=0.368, lex=0.097, hop=0)
- 5. `pack_snippets` (score=0.972, sem=0.368, lex=0.194, hop=0)

### Query: `pepys music and viol` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.015 | 8 | 80 | 8 | 0.973 | 0.371 | 0.145 |
| `semantic` | 0.008 | 8 | 80 | 8 | 0.991 | 0.374 | 0.069 |
| `legacy` | 0.008 | 8 | 80 | 8 | 0.989 | 0.373 | 0.083 |

#### Top nodes (hybrid)
- 1. `_scaffold_pycodekg_config` (score=1.000, sem=0.371, lex=0.172, hop=1)
- 2. `PyCodeKG` (score=0.972, sem=0.374, lex=0.138, hop=1)
- 3. `init` (score=0.967, sem=0.371, lex=0.138, hop=0)
- 4. `SentenceTransformerEmbedder.embed_query` (score=0.964, sem=0.370, lex=0.138, hop=1)
- 5. `SentenceTransformerEmbedder.embed_texts` (score=0.964, sem=0.370, lex=0.138, hop=1)

#### Top nodes (semantic)
- 1. `SentenceTransformerEmbedder.__repr__` (score=1.000, sem=0.377, lex=0.069, hop=0)
- 2. `PyCodeKG.__init__` (score=0.990, sem=0.374, lex=0.103, hop=0)
- 3. `PyCodeKG` (score=0.990, sem=0.374, lex=0.138, hop=1)
- 4. `build_lancedb` (score=0.988, sem=0.373, lex=0.000, hop=0)
- 5. `cmd_build` (score=0.988, sem=0.373, lex=0.034, hop=1)

#### Top nodes (legacy)
- 1. `SentenceTransformerEmbedder.__repr__` (score=1.000, sem=0.377, lex=0.069, hop=0)
- 2. `PyCodeKG.__init__` (score=0.990, sem=0.374, lex=0.103, hop=0)
- 3. `build_lancedb` (score=0.988, sem=0.373, lex=0.000, hop=0)
- 4. `init` (score=0.984, sem=0.371, lex=0.138, hop=0)
- 5. `build_pycodekg_lancedb` (score=0.984, sem=0.371, lex=0.103, hop=0)

### Query: `pepys plague and naval failure` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 8 | 72 | 8 | 0.941 | 0.351 | 0.251 |
| `semantic` | 0.009 | 8 | 72 | 8 | 0.993 | 0.354 | 0.085 |
| `legacy` | 0.009 | 8 | 72 | 8 | 0.991 | 0.353 | 0.111 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.350, lex=0.319, hop=1)
- 2. `main` (score=0.964, sem=0.351, lex=0.277, hop=1)
- 3. `PyCodeKGAnalyzer._identify_public_apis` (score=0.945, sem=0.351, lex=0.255, hop=1)
- 4. `PyCodeKGAnalyzer._analyze_concerns` (score=0.908, sem=0.351, lex=0.213, hop=1)
- 5. `PyCodeKGAnalyzer.__init__` (score=0.889, sem=0.351, lex=0.191, hop=1)

#### Top nodes (semantic)
- 1. `load_include_dirs` (score=1.000, sem=0.356, lex=0.170, hop=0)
- 2. `load_exclude_dirs` (score=0.996, sem=0.355, lex=0.170, hop=0)
- 3. `config` (score=0.996, sem=0.355, lex=0.043, hop=1)
- 4. `delta_from_dict` (score=0.987, sem=0.351, lex=0.043, hop=0)
- 5. `Snapshot.vs_baseline` (score=0.987, sem=0.351, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `load_include_dirs` (score=1.000, sem=0.356, lex=0.170, hop=0)
- 2. `load_exclude_dirs` (score=0.996, sem=0.355, lex=0.170, hop=0)
- 3. `delta_from_dict` (score=0.987, sem=0.351, lex=0.043, hop=0)
- 4. `CallChain` (score=0.986, sem=0.351, lex=0.085, hop=0)
- 5. `PyCodeKGAnalyzer` (score=0.985, sem=0.351, lex=0.085, hop=0)

### Query: `pepys treasury and accounts` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.010 | 8 | 51 | 8 | 0.983 | 0.360 | 0.168 |
| `semantic` | 0.009 | 8 | 51 | 8 | 1.000 | 0.360 | 0.142 |
| `legacy` | 0.009 | 8 | 51 | 8 | 0.996 | 0.359 | 0.100 |

#### Top nodes (hybrid)
- 1. `PyCodeKGVisitor._add_var_edge` (score=1.000, sem=0.360, lex=0.184, hop=1)
- 2. `PyCodeKGVisitor` (score=1.000, sem=0.360, lex=0.184, hop=1)
- 3. `PyCodeKGVisitor._get_node_id` (score=0.975, sem=0.360, lex=0.158, hop=1)
- 4. `PyCodeKGVisitor._extract_reads` (score=0.974, sem=0.360, lex=0.158, hop=1)
- 5. `_build_pyvis` (score=0.968, sem=0.357, lex=0.158, hop=1)

#### Top nodes (semantic)
- 1. `PyCodeKGVisitor.visit_Attribute` (score=1.000, sem=0.360, lex=0.132, hop=0)
- 2. `PyCodeKGVisitor._add_edge` (score=1.000, sem=0.360, lex=0.132, hop=1)
- 3. `PyCodeKGVisitor._get_node_id` (score=1.000, sem=0.360, lex=0.158, hop=1)
- 4. `PyCodeKGVisitor.visit_Assign` (score=0.999, sem=0.360, lex=0.105, hop=0)
- 5. `PyCodeKGVisitor._add_var_edge` (score=0.999, sem=0.360, lex=0.184, hop=1)

#### Top nodes (legacy)
- 1. `PyCodeKGVisitor.visit_Attribute` (score=1.000, sem=0.360, lex=0.132, hop=0)
- 2. `PyCodeKGVisitor.visit_Assign` (score=0.999, sem=0.360, lex=0.105, hop=0)
- 3. `PyCodeKGVisitor.visit_Module` (score=0.998, sem=0.360, lex=0.105, hop=0)
- 4. `_extract_distance` (score=0.992, sem=0.358, lex=0.079, hop=0)
- 5. `_build_node_tooltip` (score=0.991, sem=0.357, lex=0.079, hop=0)

### Query: `pepys year-end reflection` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.013 | 8 | 57 | 8 | 0.966 | 0.363 | 0.100 |
| `semantic` | 0.009 | 8 | 57 | 8 | 0.999 | 0.366 | 0.036 |
| `legacy` | 0.008 | 8 | 57 | 8 | 0.995 | 0.364 | 0.032 |

#### Top nodes (hybrid)
- 1. `Snapshot` (score=1.000, sem=0.362, lex=0.136, hop=1)
- 2. `viz3d_timeline` (score=0.963, sem=0.366, lex=0.091, hop=0)
- 3. `load_snapshots_timeline` (score=0.961, sem=0.365, lex=0.091, hop=1)
- 4. `cmd_snapshot` (score=0.956, sem=0.362, lex=0.091, hop=1)
- 5. `SnapshotManager` (score=0.949, sem=0.359, lex=0.091, hop=1)

#### Top nodes (semantic)
- 1. `viz_timeline` (score=1.000, sem=0.366, lex=0.000, hop=0)
- 2. `cmd_viz` (score=1.000, sem=0.366, lex=0.023, hop=1)
- 3. `viz3d_timeline` (score=1.000, sem=0.366, lex=0.091, hop=0)
- 4. `create_timeline_figure` (score=1.000, sem=0.366, lex=0.023, hop=1)
- 5. `display_timeline_summary` (score=0.997, sem=0.365, lex=0.045, hop=0)

#### Top nodes (legacy)
- 1. `viz_timeline` (score=1.000, sem=0.366, lex=0.000, hop=0)
- 2. `viz3d_timeline` (score=1.000, sem=0.366, lex=0.091, hop=0)
- 3. `display_timeline_summary` (score=0.997, sem=0.365, lex=0.045, hop=0)
- 4. `list_snapshots` (score=0.991, sem=0.362, lex=0.023, hop=0)
- 5. `Snapshot.vs_previous` (score=0.989, sem=0.362, lex=0.000, hop=0)

## Model: `sentence-transformers/all-mpnet-base-v2`
- Build: 4.08s, indexed_rows=480, dim=768

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.596 | 8 | 107 | 10 | 0.936 | 0.515 | 0.550 |
| `semantic` | 0.018 | 8 | 107 | 10 | 0.997 | 0.523 | 0.300 |
| `legacy` | 0.015 | 8 | 107 | 10 | 0.977 | 0.512 | 0.400 |

#### Top nodes (hybrid)
- 1. `query_codebase` (score=1.000, sem=0.517, lex=0.667, hop=0)
- 2. `mcp_server` (score=1.000, sem=0.517, lex=0.667, hop=1)
- 3. `__init__` (score=0.912, sem=0.517, lex=0.500, hop=0)
- 4. `graph_stats` (score=0.890, sem=0.500, lex=0.500, hop=0)
- 5. `base` (score=0.877, sem=0.525, lex=0.417, hop=0)

#### Top nodes (semantic)
- 1. `base` (score=1.000, sem=0.525, lex=0.417, hop=0)
- 2. `_edgespec_to_edge` (score=1.000, sem=0.525, lex=0.083, hop=1)
- 3. `_nodespec_to_node` (score=1.000, sem=0.525, lex=0.083, hop=1)
- 4. `KGModule` (score=1.000, sem=0.525, lex=0.417, hop=1)
- 5. `__init__` (score=0.986, sem=0.517, lex=0.500, hop=0)

#### Top nodes (legacy)
- 1. `base` (score=1.000, sem=0.525, lex=0.417, hop=0)
- 2. `__init__` (score=0.986, sem=0.517, lex=0.500, hop=0)
- 3. `query_codebase` (score=0.985, sem=0.517, lex=0.667, hop=0)
- 4. `QueryResult` (score=0.957, sem=0.502, lex=0.250, hop=0)
- 5. `GraphStore.edges_from` (score=0.956, sem=0.502, lex=0.167, hop=0)

### Query: `snapshot metrics over time`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.031 | 8 | 70 | 8 | 0.946 | 0.485 | 0.618 |
| `semantic` | 0.014 | 8 | 70 | 8 | 0.992 | 0.497 | 0.309 |
| `legacy` | 0.013 | 8 | 70 | 8 | 0.986 | 0.494 | 0.418 |

#### Top nodes (hybrid)
- 1. `snapshot_list` (score=1.000, sem=0.481, lex=0.727, hop=0)
- 2. `snapshot_diff` (score=0.956, sem=0.485, lex=0.636, hop=0)
- 3. `mcp_server` (score=0.951, sem=0.481, lex=0.636, hop=1)
- 4. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.916, sem=0.492, lex=0.545, hop=0)
- 5. `viz3d_timeline` (score=0.907, sem=0.485, lex=0.545, hop=0)

#### Top nodes (semantic)
- 1. `graph_stats` (score=1.000, sem=0.501, lex=0.364, hop=0)
- 2. `_get_kg` (score=1.000, sem=0.501, lex=0.000, hop=1)
- 3. `analyze_repo` (score=0.998, sem=0.500, lex=0.364, hop=0)
- 4. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.984, sem=0.492, lex=0.545, hop=0)
- 5. `BuildStats.__str__` (score=0.979, sem=0.490, lex=0.273, hop=0)

#### Top nodes (legacy)
- 1. `graph_stats` (score=1.000, sem=0.501, lex=0.364, hop=0)
- 2. `analyze_repo` (score=0.998, sem=0.500, lex=0.364, hop=0)
- 3. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.984, sem=0.492, lex=0.545, hop=0)
- 4. `BuildStats.__str__` (score=0.979, sem=0.490, lex=0.273, hop=0)
- 5. `viz3d_timeline` (score=0.970, sem=0.485, lex=0.545, hop=0)

### Query: `MCP tool exposure`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.012 | 8 | 120 | 8 | 0.949 | 0.485 | 0.564 |
| `semantic` | 0.011 | 8 | 120 | 8 | 1.000 | 0.493 | 0.345 |
| `legacy` | 0.011 | 8 | 120 | 8 | 0.959 | 0.473 | 0.382 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.493, lex=0.636, hop=0)
- 2. `analyze_repo` (score=1.000, sem=0.493, lex=0.636, hop=1)
- 3. `KGExtractor` (score=0.948, sem=0.453, lex=0.636, hop=1)
- 4. `_parse_args` (score=0.898, sem=0.493, lex=0.455, hop=1)
- 5. `main` (score=0.898, sem=0.493, lex=0.455, hop=1)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.493, lex=0.636, hop=0)
- 2. `_enrich_edges_with_provenance` (score=1.000, sem=0.493, lex=0.182, hop=1)
- 3. `_get_snapshot_mgr` (score=1.000, sem=0.493, lex=0.273, hop=1)
- 4. `_parse_args` (score=1.000, sem=0.493, lex=0.455, hop=1)
- 5. `_snapshot_freshness` (score=1.000, sem=0.493, lex=0.182, hop=1)

#### Top nodes (legacy)
- 1. `mcp_server` (score=1.000, sem=0.493, lex=0.636, hop=0)
- 2. `explain` (score=0.987, sem=0.487, lex=0.273, hop=0)
- 3. `base` (score=0.945, sem=0.466, lex=0.364, hop=0)
- 4. `graph_stats` (score=0.943, sem=0.465, lex=0.364, hop=0)
- 5. `find_node` (score=0.920, sem=0.454, lex=0.273, hop=0)

### Query: `node missing line number`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.059 | 6 | 6 | 6 | 0.945 | 0.432 | 0.340 |
| `semantic` | 0.016 | 6 | 6 | 6 | 0.979 | 0.432 | 0.320 |
| `legacy` | 0.009 | 6 | 6 | 6 | 0.979 | 0.432 | 0.320 |

#### Top nodes (hybrid)
- 1. `compute_span` (score=1.000, sem=0.439, lex=0.400, hop=0)
- 2. `PyCodeKGVisitor._add_edge` (score=0.975, sem=0.424, lex=0.400, hop=0)
- 3. `PyCodeKGVisitor._set_node_source_meta` (score=0.934, sem=0.442, lex=0.300, hop=0)
- 4. `get_node` (score=0.913, sem=0.429, lex=0.300, hop=0)
- 5. `GraphStore._is_compatible_stub_caller` (score=0.905, sem=0.424, lex=0.300, hop=0)

#### Top nodes (semantic)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.442, lex=0.300, hop=0)
- 2. `compute_span` (score=0.995, sem=0.439, lex=0.400, hop=0)
- 3. `get_node` (score=0.972, sem=0.429, lex=0.300, hop=0)
- 4. `_parse_call_site_lineno` (score=0.969, sem=0.428, lex=0.200, hop=0)
- 5. `PyCodeKGVisitor._add_edge` (score=0.960, sem=0.424, lex=0.400, hop=0)

#### Top nodes (legacy)
- 1. `PyCodeKGVisitor._set_node_source_meta` (score=1.000, sem=0.442, lex=0.300, hop=0)
- 2. `compute_span` (score=0.995, sem=0.439, lex=0.400, hop=0)
- 3. `get_node` (score=0.972, sem=0.429, lex=0.300, hop=0)
- 4. `_parse_call_site_lineno` (score=0.969, sem=0.428, lex=0.200, hop=0)
- 5. `PyCodeKGVisitor._add_edge` (score=0.960, sem=0.424, lex=0.400, hop=0)

### Query: `pepys naval fleet and king` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.359 | 8 | 34 | 8 | 0.969 | 0.371 | 0.161 |
| `semantic` | 0.012 | 8 | 34 | 8 | 0.998 | 0.375 | 0.052 |
| `legacy` | 0.010 | 8 | 34 | 8 | 0.993 | 0.373 | 0.052 |

#### Top nodes (hybrid)
- 1. `index` (score=1.000, sem=0.371, lex=0.194, hop=1)
- 2. `SemanticIndex` (score=0.999, sem=0.371, lex=0.194, hop=1)
- 3. `KGModule.build_graph` (score=0.967, sem=0.370, lex=0.161, hop=1)
- 4. `suppress_ingestion_logging` (score=0.939, sem=0.371, lex=0.129, hop=0)
- 5. `SemanticIndex.build` (score=0.939, sem=0.371, lex=0.129, hop=1)

#### Top nodes (semantic)
- 1. `_done` (score=1.000, sem=0.376, lex=0.000, hop=0)
- 2. `_run_pipeline` (score=1.000, sem=0.376, lex=0.065, hop=1)
- 3. `cmd_build_full` (score=1.000, sem=0.376, lex=0.097, hop=1)
- 4. `_banner` (score=0.998, sem=0.375, lex=0.032, hop=0)
- 5. `QueryResult.print_summary` (score=0.994, sem=0.373, lex=0.065, hop=0)

#### Top nodes (legacy)
- 1. `_done` (score=1.000, sem=0.376, lex=0.000, hop=0)
- 2. `_banner` (score=0.998, sem=0.375, lex=0.032, hop=0)
- 3. `QueryResult.print_summary` (score=0.994, sem=0.373, lex=0.065, hop=0)
- 4. `_step_result` (score=0.988, sem=0.371, lex=0.032, hop=0)
- 5. `suppress_ingestion_logging` (score=0.987, sem=0.371, lex=0.129, hop=0)

### Query: `pepys music and viol` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.033 | 8 | 28 | 8 | 0.977 | 0.374 | 0.152 |
| `semantic` | 0.011 | 8 | 28 | 8 | 0.998 | 0.375 | 0.062 |
| `legacy` | 0.010 | 8 | 28 | 8 | 0.995 | 0.374 | 0.076 |

#### Top nodes (hybrid)
- 1. `SemanticIndex` (score=1.000, sem=0.375, lex=0.172, hop=1)
- 2. `_load_kg` (score=0.994, sem=0.373, lex=0.172, hop=0)
- 3. `SentenceTransformerEmbedder.embed_texts` (score=0.968, sem=0.375, lex=0.138, hop=0)
- 4. `_tab_query` (score=0.962, sem=0.373, lex=0.138, hop=1)
- 5. `_tab_snippets` (score=0.962, sem=0.373, lex=0.138, hop=1)

#### Top nodes (semantic)
- 1. `SentenceTransformerEmbedder.__repr__` (score=1.000, sem=0.376, lex=0.069, hop=0)
- 2. `SentenceTransformerEmbedder.embed_texts` (score=0.997, sem=0.375, lex=0.138, hop=0)
- 3. `Embedder.embed_query` (score=0.997, sem=0.375, lex=0.000, hop=1)
- 4. `SentenceTransformerEmbedder` (score=0.997, sem=0.375, lex=0.034, hop=1)
- 5. `SemanticIndex.__repr__` (score=0.996, sem=0.375, lex=0.069, hop=0)

#### Top nodes (legacy)
- 1. `SentenceTransformerEmbedder.__repr__` (score=1.000, sem=0.376, lex=0.069, hop=0)
- 2. `SentenceTransformerEmbedder.embed_texts` (score=0.997, sem=0.375, lex=0.138, hop=0)
- 3. `SemanticIndex.__repr__` (score=0.996, sem=0.375, lex=0.069, hop=0)
- 4. `_record_to_dict` (score=0.990, sem=0.373, lex=0.000, hop=0)
- 5. `KGModule.__init__` (score=0.990, sem=0.373, lex=0.103, hop=0)

### Query: `pepys plague and naval failure` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.090 | 8 | 80 | 8 | 0.928 | 0.378 | 0.226 |
| `semantic` | 0.012 | 8 | 80 | 8 | 0.999 | 0.379 | 0.077 |
| `legacy` | 0.011 | 8 | 80 | 8 | 0.997 | 0.378 | 0.111 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.375, lex=0.319, hop=1)
- 2. `main` (score=0.973, sem=0.379, lex=0.277, hop=0)
- 3. `_build_index_text` (score=0.919, sem=0.379, lex=0.213, hop=1)
- 4. `SemanticIndex` (score=0.901, sem=0.379, lex=0.191, hop=1)
- 5. `pycodekg_thorough_analysis` (score=0.848, sem=0.379, lex=0.128, hop=1)

#### Top nodes (semantic)
- 1. `why_bridge` (score=1.000, sem=0.379, lex=0.000, hop=0)
- 2. `bridge_tools` (score=1.000, sem=0.379, lex=0.021, hop=1)
- 3. `main` (score=0.998, sem=0.379, lex=0.277, hop=0)
- 4. `_default_report_name` (score=0.998, sem=0.379, lex=0.000, hop=1)
- 5. `PyCodeKGAnalyzer` (score=0.998, sem=0.379, lex=0.085, hop=1)

#### Top nodes (legacy)
- 1. `why_bridge` (score=1.000, sem=0.379, lex=0.000, hop=0)
- 2. `main` (score=0.998, sem=0.379, lex=0.277, hop=0)
- 3. `index` (score=0.998, sem=0.379, lex=0.106, hop=0)
- 4. `CallChain` (score=0.995, sem=0.377, lex=0.085, hop=0)
- 5. `KGModule.__init__` (score=0.992, sem=0.376, lex=0.085, hop=0)

### Query: `pepys treasury and accounts` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.057 | 8 | 58 | 8 | 0.940 | 0.350 | 0.174 |
| `semantic` | 0.012 | 8 | 58 | 8 | 0.999 | 0.352 | 0.095 |
| `legacy` | 0.011 | 8 | 58 | 8 | 0.996 | 0.351 | 0.095 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.350, lex=0.237, hop=1)
- 2. `KGModule` (score=0.927, sem=0.351, lex=0.158, hop=0)
- 3. `KGModule.analyze` (score=0.927, sem=0.351, lex=0.158, hop=1)
- 4. `main` (score=0.925, sem=0.350, lex=0.158, hop=1)
- 5. `viz3d` (score=0.922, sem=0.349, lex=0.158, hop=1)

#### Top nodes (semantic)
- 1. `_escape` (score=1.000, sem=0.352, lex=0.079, hop=0)
- 2. `SemanticIndex.build` (score=1.000, sem=0.352, lex=0.105, hop=1)
- 3. `index` (score=1.000, sem=0.352, lex=0.132, hop=1)
- 4. `KGModule.index` (score=0.998, sem=0.352, lex=0.000, hop=0)
- 5. `KGModule` (score=0.996, sem=0.351, lex=0.158, hop=0)

#### Top nodes (legacy)
- 1. `_escape` (score=1.000, sem=0.352, lex=0.079, hop=0)
- 2. `KGModule.index` (score=0.998, sem=0.352, lex=0.000, hop=0)
- 3. `KGModule` (score=0.996, sem=0.351, lex=0.158, hop=0)
- 4. `_parse_args` (score=0.994, sem=0.350, lex=0.105, hop=0)
- 5. `PyCodeKG` (score=0.991, sem=0.349, lex=0.132, hop=0)

### Query: `pepys year-end reflection` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.027 | 8 | 43 | 8 | 0.945 | 0.370 | 0.105 |
| `semantic` | 0.013 | 8 | 43 | 8 | 0.980 | 0.372 | 0.055 |
| `legacy` | 0.012 | 8 | 43 | 8 | 0.970 | 0.368 | 0.032 |

#### Top nodes (hybrid)
- 1. `snapshots` (score=1.000, sem=0.361, lex=0.182, hop=1)
- 2. `viz3d_timeline` (score=0.953, sem=0.380, lex=0.091, hop=1)
- 3. `KGModule` (score=0.938, sem=0.363, lex=0.114, hop=1)
- 4. `load_snapshots_timeline` (score=0.924, sem=0.367, lex=0.091, hop=0)
- 5. `display_timeline_summary` (score=0.909, sem=0.380, lex=0.045, hop=0)

#### Top nodes (semantic)
- 1. `display_timeline_summary` (score=1.000, sem=0.380, lex=0.045, hop=0)
- 2. `viz3d_timeline` (score=1.000, sem=0.380, lex=0.091, hop=1)
- 3. `load_snapshots_timeline` (score=0.966, sem=0.367, lex=0.091, hop=0)
- 4. `create_3d_timeline_figure` (score=0.966, sem=0.367, lex=0.023, hop=1)
- 5. `create_timeline_figure` (score=0.966, sem=0.367, lex=0.023, hop=1)

#### Top nodes (legacy)
- 1. `display_timeline_summary` (score=1.000, sem=0.380, lex=0.045, hop=0)
- 2. `load_snapshots_timeline` (score=0.966, sem=0.367, lex=0.091, hop=0)
- 3. `_done` (score=0.966, sem=0.367, lex=0.000, hop=0)
- 4. `MainWindow.closeEvent` (score=0.958, sem=0.364, lex=0.023, hop=0)
- 5. `viz_timeline` (score=0.958, sem=0.364, lex=0.000, hop=0)

## Model: `nomic-ai/nomic-embed-text-v1`
- Build: 6.54s, indexed_rows=480, dim=768

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.022 | 8 | 52 | 10 | 0.931 | 0.559 | 0.533 |
| `semantic` | 0.009 | 8 | 52 | 10 | 0.999 | 0.570 | 0.150 |
| `legacy` | 0.010 | 8 | 52 | 10 | 0.990 | 0.564 | 0.300 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.560, lex=0.667, hop=1)
- 2. `pycodekg` (score=0.954, sem=0.557, lex=0.583, hop=1)
- 3. `extractor` (score=0.918, sem=0.562, lex=0.500, hop=1)
- 4. `graph_stats` (score=0.916, sem=0.560, lex=0.500, hop=0)
- 5. `GraphStore` (score=0.866, sem=0.554, lex=0.417, hop=0)

#### Top nodes (semantic)
- 1. `GraphStore.edges_within` (score=1.000, sem=0.570, lex=0.333, hop=0)
- 2. `QueryResult` (score=0.999, sem=0.569, lex=0.250, hop=0)
- 3. `QueryResult.print_summary` (score=0.999, sem=0.569, lex=0.083, hop=1)
- 4. `QueryResult.to_dict` (score=0.999, sem=0.569, lex=0.083, hop=1)
- 5. `QueryResult.to_json` (score=0.999, sem=0.569, lex=0.000, hop=1)

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
| `hybrid` | 0.020 | 8 | 104 | 8 | 0.951 | 0.571 | 0.600 |
| `semantic` | 0.010 | 8 | 104 | 8 | 0.988 | 0.590 | 0.309 |
| `legacy` | 0.010 | 8 | 104 | 8 | 0.981 | 0.586 | 0.364 |

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
| `hybrid` | 0.010 | 8 | 102 | 8 | 0.896 | 0.535 | 0.509 |
| `semantic` | 0.011 | 8 | 102 | 8 | 1.000 | 0.568 | 0.345 |
| `legacy` | 0.009 | 8 | 102 | 8 | 0.925 | 0.525 | 0.345 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.568, lex=0.636, hop=0)
- 2. `analyze_repo` (score=0.931, sem=0.509, lex=0.636, hop=1)
- 3. `_parse_args` (score=0.907, sem=0.568, lex=0.455, hop=1)
- 4. `main` (score=0.829, sem=0.501, lex=0.455, hop=0)
- 5. `graph_stats` (score=0.815, sem=0.529, lex=0.364, hop=0)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.568, lex=0.636, hop=0)
- 2. `_get_snapshot_mgr` (score=1.000, sem=0.568, lex=0.273, hop=1)
- 3. `_parse_args` (score=1.000, sem=0.568, lex=0.455, hop=1)
- 4. `snapshot_diff` (score=1.000, sem=0.568, lex=0.091, hop=1)
- 5. `snapshot_list` (score=1.000, sem=0.568, lex=0.273, hop=1)

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
| `hybrid` | 0.022 | 6 | 6 | 6 | 0.929 | 0.553 | 0.260 |
| `semantic` | 0.008 | 6 | 6 | 6 | 0.979 | 0.558 | 0.240 |
| `legacy` | 0.008 | 6 | 6 | 6 | 0.979 | 0.558 | 0.240 |

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
| `hybrid` | 0.020 | 8 | 59 | 8 | 0.978 | 0.462 | 0.206 |
| `semantic` | 0.011 | 8 | 59 | 8 | 1.000 | 0.466 | 0.168 |
| `legacy` | 0.010 | 8 | 59 | 8 | 0.993 | 0.463 | 0.052 |

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
| `semantic` | 0.010 | 8 | 89 | 8 | 0.983 | 0.445 | 0.034 |
| `legacy` | 0.010 | 8 | 89 | 8 | 0.975 | 0.441 | 0.062 |

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
| `hybrid` | 0.020 | 8 | 88 | 8 | 0.957 | 0.458 | 0.264 |
| `semantic` | 0.010 | 8 | 88 | 8 | 1.000 | 0.460 | 0.115 |
| `legacy` | 0.011 | 8 | 88 | 8 | 0.995 | 0.458 | 0.200 |

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
| `hybrid` | 0.019 | 8 | 47 | 8 | 0.961 | 0.435 | 0.132 |
| `semantic` | 0.010 | 8 | 47 | 8 | 0.988 | 0.439 | 0.063 |
| `legacy` | 0.010 | 8 | 47 | 8 | 0.983 | 0.436 | 0.037 |

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
- 5. `MainWindow.reset_camera` (score=0.980, sem=0.435, lex=0.053, hop=1)

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
| `hybrid` | 0.019 | 8 | 88 | 8 | 0.984 | 0.453 | 0.123 |
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
- Build: 6.74s, indexed_rows=480, dim=768

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.012 | 8 | 72 | 10 | 0.956 | 0.586 | 0.567 |
| `semantic` | 0.009 | 8 | 72 | 10 | 0.984 | 0.599 | 0.217 |
| `legacy` | 0.009 | 8 | 72 | 10 | 0.966 | 0.588 | 0.283 |

#### Top nodes (hybrid)
- 1. `query_codebase` (score=1.000, sem=0.581, lex=0.667, hop=1)
- 2. `mcp_server` (score=1.000, sem=0.581, lex=0.667, hop=1)
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
| `hybrid` | 0.011 | 8 | 69 | 8 | 0.917 | 0.622 | 0.473 |
| `semantic` | 0.009 | 8 | 69 | 8 | 0.994 | 0.629 | 0.309 |
| `legacy` | 0.009 | 8 | 69 | 8 | 0.983 | 0.622 | 0.364 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.627, lex=0.636, hop=1)
- 2. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=0.963, sem=0.633, lex=0.545, hop=0)
- 3. `GraphStore.stats` (score=0.910, sem=0.624, lex=0.455, hop=0)
- 4. `graph_stats` (score=0.870, sem=0.627, lex=0.364, hop=0)
- 5. `PyCodeKGAnalyzer._analyze_baseline` (score=0.841, sem=0.600, lex=0.364, hop=0)

#### Top nodes (semantic)
- 1. `PyCodeKGAnalyzer._analyze_docstring_coverage` (score=1.000, sem=0.633, lex=0.545, hop=0)
- 2. `PyCodeKGAnalyzer` (score=1.000, sem=0.633, lex=0.000, hop=1)
- 3. `graph_stats` (score=0.990, sem=0.627, lex=0.364, hop=0)
- 4. `_get_kg` (score=0.990, sem=0.627, lex=0.000, hop=1)
- 5. `mcp_server` (score=0.990, sem=0.627, lex=0.636, hop=1)

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
| `semantic` | 0.010 | 8 | 108 | 8 | 1.000 | 0.583 | 0.382 |
| `legacy` | 0.010 | 8 | 108 | 8 | 0.930 | 0.542 | 0.364 |

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
| `hybrid` | 0.010 | 6 | 6 | 6 | 0.933 | 0.568 | 0.260 |
| `semantic` | 0.009 | 6 | 6 | 6 | 0.976 | 0.573 | 0.240 |
| `legacy` | 0.009 | 6 | 6 | 6 | 0.976 | 0.573 | 0.240 |

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
| `hybrid` | 0.014 | 8 | 65 | 8 | 0.972 | 0.478 | 0.187 |
| `semantic` | 0.010 | 8 | 65 | 8 | 0.987 | 0.484 | 0.045 |
| `legacy` | 0.009 | 8 | 65 | 8 | 0.981 | 0.481 | 0.045 |

#### Top nodes (hybrid)
- 1. `snapshot_list` (score=1.000, sem=0.478, lex=0.226, hop=1)
- 2. `mcp_server` (score=1.000, sem=0.478, lex=0.226, hop=1)
- 3. `snapshot_diff` (score=0.976, sem=0.478, lex=0.194, hop=1)
- 4. `snapshot_show` (score=0.952, sem=0.478, lex=0.161, hop=1)
- 5. `MainWindow.on_pick` (score=0.930, sem=0.480, lex=0.129, hop=1)

#### Top nodes (semantic)
- 1. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.490, lex=0.032, hop=0)
- 2. `_remove_highlight_actors` (score=1.000, sem=0.490, lex=0.065, hop=1)
- 3. `MainWindow.update_status_display` (score=0.979, sem=0.480, lex=0.000, hop=0)
- 4. `MainWindow.on_pick` (score=0.979, sem=0.480, lex=0.129, hop=1)
- 5. `MainWindow.reset_picking_state` (score=0.979, sem=0.480, lex=0.000, hop=1)

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
| `hybrid` | 0.012 | 8 | 107 | 8 | 0.967 | 0.441 | 0.193 |
| `semantic` | 0.011 | 8 | 107 | 8 | 0.985 | 0.460 | 0.048 |
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
| `hybrid` | 0.012 | 8 | 88 | 8 | 0.958 | 0.464 | 0.264 |
| `semantic` | 0.010 | 8 | 88 | 8 | 1.000 | 0.465 | 0.115 |
| `legacy` | 0.009 | 8 | 88 | 8 | 0.996 | 0.464 | 0.149 |

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
| `semantic` | 0.009 | 8 | 46 | 8 | 0.996 | 0.456 | 0.058 |
| `legacy` | 0.010 | 8 | 46 | 8 | 0.992 | 0.454 | 0.032 |

#### Top nodes (hybrid)
- 1. `viz3d` (score=1.000, sem=0.458, lex=0.158, hop=1)
- 2. `GraphStore.callers_of` (score=0.963, sem=0.449, lex=0.132, hop=1)
- 3. `rerank_hybrid` (score=0.935, sem=0.446, lex=0.105, hop=1)
- 4. `MainWindow.on_pick` (score=0.927, sem=0.453, lex=0.079, hop=1)
- 5. `MainWindow.show_selected_docstring` (score=0.927, sem=0.453, lex=0.079, hop=1)

#### Top nodes (semantic)
- 1. `_remove_highlight_actors` (score=1.000, sem=0.458, lex=0.026, hop=0)
- 2. `viz3d` (score=1.000, sem=0.458, lex=0.158, hop=1)
- 3. `MainWindow.reset_actor_appearances` (score=0.999, sem=0.457, lex=0.026, hop=0)
- 4. `MainWindow.update_status_display` (score=0.990, sem=0.453, lex=0.000, hop=0)
- 5. `MainWindow.on_pick` (score=0.990, sem=0.453, lex=0.079, hop=1)

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
| `hybrid` | 0.014 | 8 | 69 | 8 | 0.988 | 0.467 | 0.127 |
| `semantic` | 0.010 | 8 | 69 | 8 | 0.997 | 0.469 | 0.086 |
| `legacy` | 0.010 | 8 | 69 | 8 | 0.995 | 0.468 | 0.082 |

#### Top nodes (hybrid)
- 1. `prune_snapshots` (score=1.000, sem=0.470, lex=0.136, hop=0)
- 2. `save_snapshot` (score=0.998, sem=0.469, lex=0.136, hop=0)
- 3. `SnapshotManager.diff_snapshots` (score=0.990, sem=0.465, lex=0.136, hop=0)
- 4. `GraphStore` (score=0.975, sem=0.467, lex=0.114, hop=1)
- 5. `index` (score=0.974, sem=0.466, lex=0.114, hop=1)

#### Top nodes (semantic)
- 1. `prune_snapshots` (score=1.000, sem=0.470, lex=0.136, hop=0)
- 2. `cmd_snapshot` (score=1.000, sem=0.470, lex=0.091, hop=1)
- 3. `save_snapshot` (score=0.998, sem=0.469, lex=0.136, hop=0)
- 4. `MainWindow.reset_actor_appearances` (score=0.994, sem=0.467, lex=0.023, hop=0)
- 5. `_remove_highlight_actors` (score=0.994, sem=0.467, lex=0.045, hop=1)

#### Top nodes (legacy)
- 1. `prune_snapshots` (score=1.000, sem=0.470, lex=0.136, hop=0)
- 2. `save_snapshot` (score=0.998, sem=0.469, lex=0.136, hop=0)
- 3. `MainWindow.reset_actor_appearances` (score=0.994, sem=0.467, lex=0.023, hop=0)
- 4. `GraphStore.__exit__` (score=0.993, sem=0.467, lex=0.023, hop=0)
- 5. `_extract_distance` (score=0.992, sem=0.466, lex=0.091, hop=0)

## Model: `microsoft/codebert-base`
- Build: 2.88s, indexed_rows=480, dim=768

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.102 | 8 | 101 | 10 | 0.976 | 0.921 | 0.433 |
| `semantic` | 0.013 | 8 | 101 | 10 | 1.000 | 0.922 | 0.267 |
| `legacy` | 0.012 | 8 | 101 | 10 | 0.998 | 0.921 | 0.217 |

#### Top nodes (hybrid)
- 1. `query` (score=1.000, sem=0.920, lex=0.500, hop=1)
- 2. `_build_pyvis` (score=0.971, sem=0.922, lex=0.417, hop=1)
- 3. `_load_kg` (score=0.971, sem=0.922, lex=0.417, hop=1)
- 4. `_tab_snippets` (score=0.971, sem=0.922, lex=0.417, hop=1)
- 5. `viz3d` (score=0.968, sem=0.919, lex=0.417, hop=1)

#### Top nodes (semantic)
- 1. `app` (score=1.000, sem=0.922, lex=0.333, hop=0)
- 2. `_build_node_tooltip` (score=1.000, sem=0.922, lex=0.167, hop=1)
- 3. `_build_pyvis` (score=1.000, sem=0.922, lex=0.417, hop=1)
- 4. `_get_store` (score=1.000, sem=0.922, lex=0.167, hop=1)
- 5. `_init_state` (score=1.000, sem=0.922, lex=0.250, hop=1)

#### Top nodes (legacy)
- 1. `app` (score=1.000, sem=0.922, lex=0.333, hop=0)
- 2. `BuildStats.__str__` (score=0.999, sem=0.921, lex=0.167, hop=0)
- 3. `MainWindow._connect_signals` (score=0.999, sem=0.921, lex=0.167, hop=0)
- 4. `cmd_query` (score=0.997, sem=0.920, lex=0.250, hop=0)
- 5. `ArchitectureAnalyzer._build_architecture_graph` (score=0.997, sem=0.920, lex=0.167, hop=0)

### Query: `snapshot metrics over time`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.012 | 8 | 83 | 8 | 0.970 | 0.936 | 0.200 |
| `semantic` | 0.010 | 8 | 83 | 8 | 0.999 | 0.938 | 0.127 |
| `legacy` | 0.011 | 8 | 83 | 8 | 0.997 | 0.936 | 0.145 |

#### Top nodes (hybrid)
- 1. `analyze` (score=1.000, sem=0.937, lex=0.273, hop=0)
- 2. `BuildStats.__str__` (score=0.999, sem=0.936, lex=0.273, hop=0)
- 3. `BuildStats` (score=0.963, sem=0.936, lex=0.182, hop=1)
- 4. `LayoutNode` (score=0.960, sem=0.933, lex=0.182, hop=1)
- 5. `suppress_ingestion_logging` (score=0.929, sem=0.939, lex=0.091, hop=0)

#### Top nodes (semantic)
- 1. `suppress_ingestion_logging` (score=1.000, sem=0.939, lex=0.091, hop=0)
- 2. `SemanticIndex.build` (score=1.000, sem=0.939, lex=0.091, hop=1)
- 3. `index` (score=1.000, sem=0.939, lex=0.091, hop=1)
- 4. `analyze` (score=0.997, sem=0.937, lex=0.273, hop=0)
- 5. `cmd_analyze` (score=0.997, sem=0.937, lex=0.091, hop=1)

#### Top nodes (legacy)
- 1. `suppress_ingestion_logging` (score=1.000, sem=0.939, lex=0.091, hop=0)
- 2. `analyze` (score=0.997, sem=0.937, lex=0.273, hop=0)
- 3. `BuildStats.__str__` (score=0.997, sem=0.936, lex=0.273, hop=0)
- 4. `build` (score=0.996, sem=0.935, lex=0.000, hop=0)
- 5. `MainWindow._connect_signals` (score=0.995, sem=0.935, lex=0.091, hop=0)

### Query: `MCP tool exposure`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.010 | 8 | 64 | 8 | 0.971 | 0.931 | 0.291 |
| `semantic` | 0.010 | 8 | 64 | 8 | 1.000 | 0.932 | 0.036 |
| `legacy` | 0.010 | 8 | 64 | 8 | 0.999 | 0.931 | 0.145 |

#### Top nodes (hybrid)
- 1. `viz3d` (score=1.000, sem=0.931, lex=0.364, hop=1)
- 2. `MainWindow.__init__` (score=0.964, sem=0.931, lex=0.273, hop=1)
- 3. `main` (score=0.964, sem=0.930, lex=0.273, hop=0)
- 4. `_tab_graph` (score=0.964, sem=0.930, lex=0.273, hop=1)
- 5. `_tab_snippets` (score=0.964, sem=0.930, lex=0.273, hop=1)

#### Top nodes (semantic)
- 1. `MainWindow.on_pick` (score=1.000, sem=0.932, lex=0.091, hop=0)
- 2. `_docstring_to_markdown` (score=1.000, sem=0.932, lex=0.091, hop=1)
- 3. `MainWindow.highlight_actor` (score=1.000, sem=0.932, lex=0.000, hop=1)
- 4. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.932, lex=0.000, hop=1)
- 5. `MainWindow.update_status_display` (score=1.000, sem=0.932, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `MainWindow.on_pick` (score=1.000, sem=0.932, lex=0.091, hop=0)
- 2. `KGVisualizer` (score=0.999, sem=0.931, lex=0.182, hop=0)
- 3. `main` (score=0.998, sem=0.930, lex=0.273, hop=0)
- 4. `BuildStats.__str__` (score=0.998, sem=0.930, lex=0.091, hop=0)
- 5. `SentenceTransformerEmbedder.__init__` (score=0.998, sem=0.930, lex=0.091, hop=0)

### Query: `node missing line number`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.024 | 6 | 6 | 6 | 0.965 | 0.920 | 0.120 |
| `semantic` | 0.009 | 6 | 6 | 6 | 0.999 | 0.920 | 0.100 |
| `legacy` | 0.009 | 6 | 6 | 6 | 0.999 | 0.920 | 0.100 |

#### Top nodes (hybrid)
- 1. `MainWindow.on_pick` (score=1.000, sem=0.921, lex=0.200, hop=0)
- 2. `BuildStats.__str__` (score=0.999, sem=0.920, lex=0.200, hop=0)
- 3. `CodeGraph.__repr__` (score=0.956, sem=0.920, lex=0.100, hop=0)
- 4. `LayoutNode.line_count` (score=0.956, sem=0.919, lex=0.100, hop=0)
- 5. `build` (score=0.915, sem=0.921, lex=0.000, hop=0)

#### Top nodes (semantic)
- 1. `MainWindow.on_pick` (score=1.000, sem=0.921, lex=0.200, hop=0)
- 2. `build` (score=1.000, sem=0.921, lex=0.000, hop=0)
- 3. `BuildStats.__str__` (score=0.999, sem=0.920, lex=0.200, hop=0)
- 4. `CodeGraph.__repr__` (score=0.999, sem=0.920, lex=0.100, hop=0)
- 5. `ModuleLayer` (score=0.998, sem=0.919, lex=0.000, hop=0)

#### Top nodes (legacy)
- 1. `MainWindow.on_pick` (score=1.000, sem=0.921, lex=0.200, hop=0)
- 2. `build` (score=1.000, sem=0.921, lex=0.000, hop=0)
- 3. `BuildStats.__str__` (score=0.999, sem=0.920, lex=0.200, hop=0)
- 4. `CodeGraph.__repr__` (score=0.999, sem=0.920, lex=0.100, hop=0)
- 5. `ModuleLayer` (score=0.998, sem=0.919, lex=0.000, hop=0)

### Query: `pepys naval fleet and king` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.031 | 8 | 102 | 8 | 0.963 | 0.931 | 0.200 |
| `semantic` | 0.010 | 8 | 102 | 8 | 1.000 | 0.936 | 0.065 |
| `legacy` | 0.010 | 8 | 102 | 8 | 0.997 | 0.933 | 0.090 |

#### Top nodes (hybrid)
- 1. `_build_index_text` (score=1.000, sem=0.931, lex=0.290, hop=1)
- 2. `index` (score=0.961, sem=0.931, lex=0.194, hop=0)
- 3. `SemanticIndex` (score=0.961, sem=0.931, lex=0.194, hop=1)
- 4. `viz3d` (score=0.948, sem=0.932, lex=0.161, hop=1)
- 5. `ProvMeta` (score=0.947, sem=0.930, lex=0.161, hop=1)

#### Top nodes (semantic)
- 1. `MainWindow.on_pick` (score=1.000, sem=0.936, lex=0.129, hop=0)
- 2. `_docstring_to_markdown` (score=1.000, sem=0.936, lex=0.065, hop=1)
- 3. `MainWindow.highlight_actor` (score=1.000, sem=0.936, lex=0.097, hop=1)
- 4. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.936, lex=0.032, hop=1)
- 5. `MainWindow.update_status_display` (score=1.000, sem=0.936, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `MainWindow.on_pick` (score=1.000, sem=0.936, lex=0.129, hop=0)
- 2. `bridge` (score=0.996, sem=0.932, lex=0.065, hop=0)
- 3. `DocstringPopup` (score=0.996, sem=0.932, lex=0.065, hop=0)
- 4. `main` (score=0.996, sem=0.932, lex=0.097, hop=0)
- 5. `analyze` (score=0.995, sem=0.931, lex=0.097, hop=0)

### Query: `pepys music and viol` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.031 | 8 | 119 | 8 | 0.994 | 0.917 | 0.159 |
| `semantic` | 0.010 | 8 | 119 | 8 | 1.000 | 0.920 | 0.041 |
| `legacy` | 0.010 | 8 | 119 | 8 | 0.998 | 0.919 | 0.076 |

#### Top nodes (hybrid)
- 1. `SemanticIndex` (score=1.000, sem=0.918, lex=0.172, hop=1)
- 2. `viz3d` (score=0.999, sem=0.917, lex=0.172, hop=1)
- 3. `_scaffold_pycodekg_config` (score=0.999, sem=0.917, lex=0.172, hop=1)
- 4. `_build_index_text` (score=0.985, sem=0.918, lex=0.138, hop=1)
- 5. `_extract_distance` (score=0.985, sem=0.918, lex=0.138, hop=1)

#### Top nodes (semantic)
- 1. `MainWindow.on_pick` (score=1.000, sem=0.920, lex=0.103, hop=0)
- 2. `_docstring_to_markdown` (score=1.000, sem=0.920, lex=0.034, hop=1)
- 3. `MainWindow.highlight_actor` (score=1.000, sem=0.920, lex=0.034, hop=1)
- 4. `MainWindow.reset_actor_appearances` (score=1.000, sem=0.920, lex=0.034, hop=1)
- 5. `MainWindow.update_status_display` (score=1.000, sem=0.920, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `MainWindow.on_pick` (score=1.000, sem=0.920, lex=0.103, hop=0)
- 2. `graph` (score=1.000, sem=0.920, lex=0.000, hop=0)
- 3. `analyze` (score=0.998, sem=0.919, lex=0.103, hop=0)
- 4. `index` (score=0.997, sem=0.918, lex=0.103, hop=0)
- 5. `bridge` (score=0.996, sem=0.917, lex=0.069, hop=0)

### Query: `pepys plague and naval failure` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.031 | 8 | 118 | 8 | 0.983 | 0.937 | 0.128 |
| `semantic` | 0.011 | 8 | 118 | 8 | 0.998 | 0.939 | 0.051 |
| `legacy` | 0.010 | 8 | 118 | 8 | 0.997 | 0.938 | 0.085 |

#### Top nodes (hybrid)
- 1. `SemanticIndex.build` (score=1.000, sem=0.936, lex=0.170, hop=1)
- 2. `_tab_snippets` (score=0.984, sem=0.938, lex=0.128, hop=1)
- 3. `viz3d` (score=0.980, sem=0.934, lex=0.128, hop=1)
- 4. `app` (score=0.975, sem=0.938, lex=0.106, hop=1)
- 5. `init` (score=0.974, sem=0.937, lex=0.106, hop=0)

#### Top nodes (semantic)
- 1. `analyze` (score=1.000, sem=0.941, lex=0.064, hop=0)
- 2. `cmd_analyze` (score=1.000, sem=0.941, lex=0.000, hop=1)
- 3. `main` (score=0.997, sem=0.938, lex=0.064, hop=0)
- 4. `_init_state` (score=0.997, sem=0.938, lex=0.085, hop=1)
- 5. `_inject_css` (score=0.997, sem=0.938, lex=0.043, hop=1)

#### Top nodes (legacy)
- 1. `analyze` (score=1.000, sem=0.941, lex=0.064, hop=0)
- 2. `main` (score=0.997, sem=0.938, lex=0.064, hop=0)
- 3. `init` (score=0.996, sem=0.937, lex=0.106, hop=0)
- 4. `suppress_ingestion_logging` (score=0.995, sem=0.936, lex=0.085, hop=0)
- 5. `architecture` (score=0.995, sem=0.936, lex=0.106, hop=0)

### Query: `pepys treasury and accounts` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.021 | 8 | 128 | 8 | 0.982 | 0.938 | 0.168 |
| `semantic` | 0.010 | 8 | 128 | 8 | 0.999 | 0.940 | 0.047 |
| `legacy` | 0.010 | 8 | 128 | 8 | 0.999 | 0.939 | 0.068 |

#### Top nodes (hybrid)
- 1. `SemanticIndex` (score=1.000, sem=0.939, lex=0.211, hop=1)
- 2. `_build_index_text` (score=0.989, sem=0.939, lex=0.184, hop=1)
- 3. `compute_bridge_centrality` (score=0.978, sem=0.938, lex=0.158, hop=1)
- 4. `architecture` (score=0.977, sem=0.938, lex=0.158, hop=0)
- 5. `index` (score=0.967, sem=0.939, lex=0.132, hop=0)

#### Top nodes (semantic)
- 1. `analyze` (score=1.000, sem=0.940, lex=0.079, hop=0)
- 2. `cmd_analyze` (score=1.000, sem=0.940, lex=0.026, hop=1)
- 3. `graph` (score=0.999, sem=0.939, lex=0.000, hop=0)
- 4. `CodeGraph` (score=0.999, sem=0.939, lex=0.053, hop=1)
- 5. `MainWindow.on_pick` (score=0.999, sem=0.939, lex=0.079, hop=0)

#### Top nodes (legacy)
- 1. `analyze` (score=1.000, sem=0.940, lex=0.079, hop=0)
- 2. `graph` (score=0.999, sem=0.939, lex=0.000, hop=0)
- 3. `MainWindow.on_pick` (score=0.999, sem=0.939, lex=0.079, hop=0)
- 4. `index` (score=0.998, sem=0.939, lex=0.132, hop=0)
- 5. `bridge` (score=0.998, sem=0.938, lex=0.053, hop=0)

### Query: `pepys year-end reflection` **[pepys]**
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.031 | 8 | 102 | 8 | 0.994 | 0.928 | 0.123 |
| `semantic` | 0.010 | 8 | 102 | 8 | 0.998 | 0.930 | 0.050 |
| `legacy` | 0.010 | 8 | 102 | 8 | 0.997 | 0.929 | 0.068 |

#### Top nodes (hybrid)
- 1. `SemanticIndex.build` (score=1.000, sem=0.928, lex=0.136, hop=1)
- 2. `compute_bridge_centrality` (score=0.999, sem=0.926, lex=0.136, hop=1)
- 3. `_tab_graph` (score=0.991, sem=0.928, lex=0.114, hop=1)
- 4. `_tab_query` (score=0.991, sem=0.928, lex=0.114, hop=1)
- 5. `_tab_snippets` (score=0.991, sem=0.928, lex=0.114, hop=1)

#### Top nodes (semantic)
- 1. `analyze` (score=1.000, sem=0.932, lex=0.068, hop=0)
- 2. `cmd_analyze` (score=1.000, sem=0.932, lex=0.000, hop=1)
- 3. `graph` (score=0.997, sem=0.929, lex=0.023, hop=0)
- 4. `CodeGraph` (score=0.997, sem=0.929, lex=0.091, hop=1)
- 5. `main` (score=0.996, sem=0.928, lex=0.068, hop=0)

#### Top nodes (legacy)
- 1. `analyze` (score=1.000, sem=0.932, lex=0.068, hop=0)
- 2. `graph` (score=0.997, sem=0.929, lex=0.023, hop=0)
- 3. `main` (score=0.996, sem=0.928, lex=0.068, hop=0)
- 4. `architecture` (score=0.996, sem=0.928, lex=0.114, hop=0)
- 5. `suppress_ingestion_logging` (score=0.996, sem=0.928, lex=0.068, hop=0)
