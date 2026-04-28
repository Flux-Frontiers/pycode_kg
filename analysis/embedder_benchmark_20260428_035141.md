# Embedder Benchmark Report

> Query cases marked **[pepys]** use real Samuel Pepys diary text (1660–1668) and are intended for evaluation against a DiaryKG index.  All other cases target a PyCodeKG index.

- Started (UTC): 2026-04-28T03:51:41.424573+00:00
- Completed (UTC): 2026-04-28T03:51:45.311357+00:00
- Repo: `/Users/egs/repos/pycode_kg`
- SQLite: `/Users/egs/repos/pycode_kg/.pycodekg/graph.sqlite`
- LanceDB root: `/Users/egs/repos/pycode_kg/.pycodekg/lancedb-benchmark`
- Hybrid weights: semantic=0.7, lexical=0.3

## Model: `BAAI/bge-small-en-v1.5`
- Build: 3.53s, indexed_rows=480, dim=384

### Query: `edge storage and query`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.039 | 8 | 106 | 10 | 0.955 | 0.665 | 0.567 |
| `semantic` | 0.010 | 8 | 106 | 10 | 1.000 | 0.690 | 0.150 |
| `legacy` | 0.010 | 8 | 106 | 10 | 0.975 | 0.674 | 0.400 |

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
| `hybrid` | 0.020 | 8 | 91 | 8 | 0.944 | 0.646 | 0.582 |
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
| `semantic` | 0.009 | 8 | 135 | 8 | 1.000 | 0.598 | 0.364 |
| `legacy` | 0.010 | 8 | 135 | 8 | 0.987 | 0.591 | 0.455 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=1.000, sem=0.598, lex=0.636, hop=0)
- 2. `analyze_repo` (score=1.000, sem=0.598, lex=0.636, hop=1)
- 3. `KGExtractor` (score=0.986, sem=0.586, lex=0.636, hop=0)
- 4. `_parse_args` (score=0.911, sem=0.598, lex=0.455, hop=1)
- 5. `main` (score=0.911, sem=0.598, lex=0.455, hop=1)

#### Top nodes (semantic)
- 1. `mcp_server` (score=1.000, sem=0.598, lex=0.636, hop=0)
- 2. `_enrich_edges_with_provenance` (score=1.000, sem=0.598, lex=0.182, hop=1)
- 3. `_get_kg` (score=1.000, sem=0.598, lex=0.273, hop=1)
- 4. `_get_snapshot_mgr` (score=1.000, sem=0.598, lex=0.273, hop=1)
- 5. `_parse_args` (score=1.000, sem=0.598, lex=0.455, hop=1)

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
| `semantic` | 0.010 | 8 | 36 | 8 | 0.994 | 0.514 | 0.065 |
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
| `legacy` | 0.009 | 8 | 59 | 8 | 0.992 | 0.464 | 0.062 |

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
| `semantic` | 0.008 | 8 | 40 | 8 | 0.997 | 0.494 | 0.115 |
| `legacy` | 0.008 | 8 | 40 | 8 | 0.989 | 0.490 | 0.055 |

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
| `hybrid` | 0.020 | 8 | 28 | 8 | 0.968 | 0.488 | 0.121 |
| `semantic` | 0.008 | 8 | 28 | 8 | 0.997 | 0.491 | 0.042 |
| `legacy` | 0.008 | 8 | 28 | 8 | 0.993 | 0.489 | 0.016 |

#### Top nodes (hybrid)
- 1. `KGModule` (score=1.000, sem=0.490, lex=0.158, hop=1)
- 2. `KGModule.build_graph` (score=0.980, sem=0.490, lex=0.132, hop=1)
- 3. `SnapshotManager` (score=0.969, sem=0.484, lex=0.132, hop=1)
- 4. `KGModule.query` (score=0.960, sem=0.490, lex=0.105, hop=1)
- 5. `cmd_build_full` (score=0.931, sem=0.486, lex=0.079, hop=1)

#### Top nodes (semantic)
- 1. `KGModule.__exit__` (score=1.000, sem=0.492, lex=0.053, hop=0)
- 2. `KGModule.close` (score=0.999, sem=0.492, lex=0.026, hop=0)
- 3. `KGModule.store` (score=0.995, sem=0.490, lex=0.000, hop=0)
- 4. `src/pycode_kg/module/base.py.KGModule.query._rank_key` (score=0.995, sem=0.490, lex=0.000, hop=1)
- 5. `KGModule.build_graph` (score=0.995, sem=0.490, lex=0.132, hop=1)

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
