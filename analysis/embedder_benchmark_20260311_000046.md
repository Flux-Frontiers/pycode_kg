# Embedder Benchmark Report

- Started (UTC): 2026-03-11T00:00:46.589614+00:00
- Completed (UTC): 2026-03-11T00:01:10.366402+00:00
- Repo: `/Users/egs/repos/code_kg`
- SQLite: `/Users/egs/repos/code_kg/.codekg/graph.sqlite`
- LanceDB root: `/Users/egs/repos/code_kg/.codekg/lancedb-benchmark`
- Hybrid weights: semantic=0.7, lexical=0.3

## Model: `all-MiniLM-L6-v2`
- Build: 3.61s, indexed_rows=349, dim=384

### Query: `snapshot freshness comparison`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.318 | 8 | 64 | 10 | 0.543 | 0.519 | 0.600 |
| `semantic` | 0.010 | 8 | 64 | 10 | 0.534 | 0.534 | 0.333 |
| `legacy` | 0.010 | 8 | 64 | 10 | 0.521 | 0.521 | 0.400 |

#### Top nodes (hybrid)
- 1. `SnapshotManager` (score=0.574, sem=0.534, lex=0.667, hop=1)
- 2. `mcp_server` (score=0.560, sem=0.515, lex=0.667, hop=1)
- 3. `SnapshotManager.get_baseline` (score=0.558, sem=0.511, lex=0.667, hop=0)
- 4. `_snapshot_freshness` (score=0.550, sem=0.501, lex=0.667, hop=0)
- 5. `SnapshotManager.diff_snapshots` (score=0.474, sem=0.534, lex=0.333, hop=0)

#### Top nodes (semantic)
- 1. `SnapshotManager.diff_snapshots` (score=0.534, sem=0.534, lex=0.333, hop=0)
- 2. `Snapshot.key` (score=0.534, sem=0.534, lex=0.333, hop=1)
- 3. `SnapshotManager._compute_delta` (score=0.534, sem=0.534, lex=0.000, hop=1)
- 4. `SnapshotManager.load_snapshot` (score=0.534, sem=0.534, lex=0.333, hop=1)
- 5. `SnapshotManager` (score=0.534, sem=0.534, lex=0.667, hop=1)

#### Top nodes (legacy)
- 1. `SnapshotManager.diff_snapshots` (score=0.534, sem=0.534, lex=0.333, hop=0)
- 2. `snapshot_diff` (score=0.534, sem=0.534, lex=0.333, hop=0)
- 3. `snapshot_list` (score=0.515, sem=0.515, lex=0.333, hop=0)
- 4. `SnapshotManager.save_snapshot` (score=0.512, sem=0.512, lex=0.333, hop=0)
- 5. `SnapshotManager.get_baseline` (score=0.511, sem=0.511, lex=0.667, hop=0)

### Query: `missing_lineno_policy cap_or_skip fallback`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.257 | 6 | 6 | 6 | 0.277 | 0.396 | 0.000 |
| `semantic` | 0.009 | 6 | 6 | 6 | 0.396 | 0.396 | 0.000 |
| `legacy` | 0.009 | 6 | 6 | 6 | 0.396 | 0.396 | 0.000 |

#### Top nodes (hybrid)
- 1. `_read_lines` (score=0.282, sem=0.403, lex=0.000, hop=0)
- 2. `_compute_span` (score=0.279, sem=0.399, lex=0.000, hop=0)
- 3. `LayoutNode.line_count` (score=0.278, sem=0.396, lex=0.000, hop=0)
- 4. `LayoutNode` (score=0.275, sem=0.393, lex=0.000, hop=0)
- 5. `CodeKGVisitor._set_node_source_meta` (score=0.273, sem=0.390, lex=0.000, hop=0)

#### Top nodes (semantic)
- 1. `_read_lines` (score=0.403, sem=0.403, lex=0.000, hop=0)
- 2. `_compute_span` (score=0.399, sem=0.399, lex=0.000, hop=0)
- 3. `LayoutNode.line_count` (score=0.396, sem=0.396, lex=0.000, hop=0)
- 4. `LayoutNode` (score=0.393, sem=0.393, lex=0.000, hop=0)
- 5. `CodeKGVisitor._set_node_source_meta` (score=0.390, sem=0.390, lex=0.000, hop=0)

#### Top nodes (legacy)
- 1. `_read_lines` (score=0.403, sem=0.403, lex=0.000, hop=0)
- 2. `_compute_span` (score=0.399, sem=0.399, lex=0.000, hop=0)
- 3. `LayoutNode.line_count` (score=0.396, sem=0.396, lex=0.000, hop=0)
- 4. `LayoutNode` (score=0.393, sem=0.393, lex=0.000, hop=0)
- 5. `CodeKGVisitor._set_node_source_meta` (score=0.390, sem=0.390, lex=0.000, hop=0)

### Query: `how does the graph get built from source code`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.025 | 8 | 36 | 8 | 0.469 | 0.546 | 0.289 |
| `semantic` | 0.010 | 8 | 36 | 8 | 0.562 | 0.562 | 0.156 |
| `legacy` | 0.010 | 8 | 36 | 8 | 0.561 | 0.561 | 0.156 |

#### Top nodes (hybrid)
- 1. `CodeGraph` (score=0.494, sem=0.563, lex=0.333, hop=0)
- 2. `CodeKG` (score=0.490, sem=0.557, lex=0.333, hop=1)
- 3. `ArchitectureAnalyzer._build_architecture_graph` (score=0.469, sem=0.527, lex=0.333, hop=0)
- 4. `CodeGraph.result` (score=0.454, sem=0.554, lex=0.222, hop=1)
- 5. `CodeGraph.__init__` (score=0.436, sem=0.528, lex=0.222, hop=0)

#### Top nodes (semantic)
- 1. `graph` (score=0.569, sem=0.569, lex=0.111, hop=0)
- 2. `CodeGraph` (score=0.563, sem=0.563, lex=0.333, hop=0)
- 3. `CodeGraph.__repr__` (score=0.561, sem=0.561, lex=0.111, hop=0)
- 4. `CodeKG.graph` (score=0.557, sem=0.557, lex=0.111, hop=0)
- 5. `CodeKG.build_graph` (score=0.557, sem=0.557, lex=0.111, hop=1)

#### Top nodes (legacy)
- 1. `graph` (score=0.569, sem=0.569, lex=0.111, hop=0)
- 2. `CodeGraph` (score=0.563, sem=0.563, lex=0.333, hop=0)
- 3. `CodeGraph.__repr__` (score=0.561, sem=0.561, lex=0.111, hop=0)
- 4. `CodeKG.graph` (score=0.557, sem=0.557, lex=0.111, hop=0)
- 5. `CodeGraph.nodes` (score=0.554, sem=0.554, lex=0.111, hop=0)

## Model: `all-MiniLM-L12-v2`
- Build: 9.59s, indexed_rows=349, dim=384

### Query: `snapshot freshness comparison`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.013 | 8 | 59 | 10 | 0.549 | 0.527 | 0.600 |
| `semantic` | 0.013 | 8 | 59 | 10 | 0.533 | 0.533 | 0.200 |
| `legacy` | 0.011 | 8 | 59 | 10 | 0.529 | 0.529 | 0.400 |

#### Top nodes (hybrid)
- 1. `mcp_server` (score=0.569, sem=0.527, lex=0.667, hop=1)
- 2. `SnapshotManager` (score=0.568, sem=0.526, lex=0.667, hop=1)
- 3. `_snapshot_freshness` (score=0.566, sem=0.524, lex=0.667, hop=0)
- 4. `SnapshotManager.get_baseline` (score=0.564, sem=0.520, lex=0.667, hop=0)
- 5. `SnapshotManager.save_snapshot` (score=0.478, sem=0.539, lex=0.333, hop=0)

#### Top nodes (semantic)
- 1. `SnapshotManager.save_snapshot` (score=0.539, sem=0.539, lex=0.333, hop=0)
- 2. `SnapshotManager._save_manifest` (score=0.539, sem=0.539, lex=0.000, hop=1)
- 3. `SnapshotManager.list_snapshots` (score=0.532, sem=0.532, lex=0.333, hop=0)
- 4. `snapshot_diff` (score=0.527, sem=0.527, lex=0.333, hop=0)
- 5. `_get_snapshot_mgr` (score=0.527, sem=0.527, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `SnapshotManager.save_snapshot` (score=0.539, sem=0.539, lex=0.333, hop=0)
- 2. `SnapshotManager.list_snapshots` (score=0.532, sem=0.532, lex=0.333, hop=0)
- 3. `snapshot_diff` (score=0.527, sem=0.527, lex=0.333, hop=0)
- 4. `SnapshotManager.diff_snapshots` (score=0.526, sem=0.526, lex=0.333, hop=0)
- 5. `_snapshot_freshness` (score=0.524, sem=0.524, lex=0.667, hop=0)

### Query: `missing_lineno_policy cap_or_skip fallback`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 6 | 6 | 6 | 0.289 | 0.412 | 0.000 |
| `semantic` | 0.012 | 6 | 6 | 6 | 0.412 | 0.412 | 0.000 |
| `legacy` | 0.011 | 6 | 6 | 6 | 0.412 | 0.412 | 0.000 |

#### Top nodes (hybrid)
- 1. `LayoutNode.line_count` (score=0.298, sem=0.425, lex=0.000, hop=0)
- 2. `Edge` (score=0.292, sem=0.418, lex=0.000, hop=0)
- 3. `main` (score=0.291, sem=0.415, lex=0.000, hop=0)
- 4. `Node` (score=0.281, sem=0.401, lex=0.000, hop=0)
- 5. `_read_lines` (score=0.281, sem=0.401, lex=0.000, hop=0)

#### Top nodes (semantic)
- 1. `LayoutNode.line_count` (score=0.425, sem=0.425, lex=0.000, hop=0)
- 2. `Edge` (score=0.418, sem=0.418, lex=0.000, hop=0)
- 3. `main` (score=0.415, sem=0.415, lex=0.000, hop=0)
- 4. `Node` (score=0.401, sem=0.401, lex=0.000, hop=0)
- 5. `_read_lines` (score=0.401, sem=0.401, lex=0.000, hop=0)

#### Top nodes (legacy)
- 1. `LayoutNode.line_count` (score=0.425, sem=0.425, lex=0.000, hop=0)
- 2. `Edge` (score=0.418, sem=0.418, lex=0.000, hop=0)
- 3. `main` (score=0.415, sem=0.415, lex=0.000, hop=0)
- 4. `Node` (score=0.401, sem=0.401, lex=0.000, hop=0)
- 5. `_read_lines` (score=0.401, sem=0.401, lex=0.000, hop=0)

### Query: `how does the graph get built from source code`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.012 | 8 | 45 | 8 | 0.454 | 0.525 | 0.289 |
| `semantic` | 0.011 | 8 | 45 | 8 | 0.532 | 0.532 | 0.222 |
| `legacy` | 0.011 | 8 | 45 | 8 | 0.530 | 0.530 | 0.178 |

#### Top nodes (hybrid)
- 1. `CodeGraph` (score=0.468, sem=0.526, lex=0.333, hop=1)
- 2. `ArchitectureAnalyzer._build_architecture_graph` (score=0.466, sem=0.523, lex=0.333, hop=0)
- 3. `CodeKG` (score=0.459, sem=0.513, lex=0.333, hop=1)
- 4. `CodeGraph.__init__` (score=0.449, sem=0.546, lex=0.222, hop=0)
- 5. `BuildStats` (score=0.428, sem=0.516, lex=0.222, hop=1)

#### Top nodes (semantic)
- 1. `CodeGraph.__init__` (score=0.546, sem=0.546, lex=0.222, hop=0)
- 2. `CodeGraph.__repr__` (score=0.537, sem=0.537, lex=0.111, hop=0)
- 3. `graph` (score=0.526, sem=0.526, lex=0.111, hop=0)
- 4. `CodeGraph` (score=0.526, sem=0.526, lex=0.333, hop=1)
- 5. `ArchitectureAnalyzer._build_architecture_graph` (score=0.523, sem=0.523, lex=0.333, hop=0)

#### Top nodes (legacy)
- 1. `CodeGraph.__init__` (score=0.546, sem=0.546, lex=0.222, hop=0)
- 2. `CodeGraph.__repr__` (score=0.537, sem=0.537, lex=0.111, hop=0)
- 3. `graph` (score=0.526, sem=0.526, lex=0.111, hop=0)
- 4. `ArchitectureAnalyzer._build_architecture_graph` (score=0.523, sem=0.523, lex=0.333, hop=0)
- 5. `CodeKG.build_graph` (score=0.516, sem=0.516, lex=0.111, hop=0)

## Model: `BAAI/bge-small-en-v1.5`
- Build: 1.35s, indexed_rows=349, dim=384

### Query: `snapshot freshness comparison`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.015 | 8 | 75 | 10 | 0.638 | 0.654 | 0.600 |
| `semantic` | 0.013 | 8 | 75 | 10 | 0.671 | 0.671 | 0.333 |
| `legacy` | 0.012 | 8 | 75 | 10 | 0.640 | 0.640 | 0.467 |

#### Top nodes (hybrid)
- 1. `_snapshot_freshness` (score=0.690, sem=0.701, lex=0.667, hop=0)
- 2. `SnapshotManager.get_baseline` (score=0.637, sem=0.624, lex=0.667, hop=0)
- 3. `SnapshotManager` (score=0.637, sem=0.624, lex=0.667, hop=1)
- 4. `mcp_server` (score=0.635, sem=0.621, lex=0.667, hop=1)
- 5. `snapshot_show` (score=0.590, sem=0.701, lex=0.333, hop=1)

#### Top nodes (semantic)
- 1. `_snapshot_freshness` (score=0.701, sem=0.701, lex=0.667, hop=0)
- 2. `_get_kg` (score=0.701, sem=0.701, lex=0.000, hop=1)
- 3. `snapshot_show` (score=0.701, sem=0.701, lex=0.333, hop=1)
- 4. `snapshot_diff` (score=0.628, sem=0.628, lex=0.333, hop=0)
- 5. `Snapshot.key` (score=0.625, sem=0.625, lex=0.333, hop=0)

#### Top nodes (legacy)
- 1. `_snapshot_freshness` (score=0.701, sem=0.701, lex=0.667, hop=0)
- 2. `snapshot_diff` (score=0.628, sem=0.628, lex=0.333, hop=0)
- 3. `Snapshot.key` (score=0.625, sem=0.625, lex=0.333, hop=0)
- 4. `SnapshotManager.get_baseline` (score=0.624, sem=0.624, lex=0.667, hop=0)
- 5. `snapshot_list` (score=0.621, sem=0.621, lex=0.333, hop=0)

### Query: `missing_lineno_policy cap_or_skip fallback`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 6 | 6 | 6 | 0.399 | 0.571 | 0.000 |
| `semantic` | 0.011 | 6 | 6 | 6 | 0.571 | 0.571 | 0.000 |
| `legacy` | 0.010 | 6 | 6 | 6 | 0.571 | 0.571 | 0.000 |

#### Top nodes (hybrid)
- 1. `_step_header` (score=0.401, sem=0.573, lex=0.000, hop=0)
- 2. `GraphStore.__exit__` (score=0.400, sem=0.572, lex=0.000, hop=0)
- 3. `_summary` (score=0.400, sem=0.571, lex=0.000, hop=0)
- 4. `_banner` (score=0.399, sem=0.569, lex=0.000, hop=0)
- 5. `_step_ok` (score=0.397, sem=0.567, lex=0.000, hop=0)

#### Top nodes (semantic)
- 1. `_step_header` (score=0.573, sem=0.573, lex=0.000, hop=0)
- 2. `GraphStore.__exit__` (score=0.572, sem=0.572, lex=0.000, hop=0)
- 3. `_summary` (score=0.571, sem=0.571, lex=0.000, hop=0)
- 4. `_banner` (score=0.569, sem=0.569, lex=0.000, hop=0)
- 5. `_step_ok` (score=0.567, sem=0.567, lex=0.000, hop=0)

#### Top nodes (legacy)
- 1. `_step_header` (score=0.573, sem=0.573, lex=0.000, hop=0)
- 2. `GraphStore.__exit__` (score=0.572, sem=0.572, lex=0.000, hop=0)
- 3. `_summary` (score=0.571, sem=0.571, lex=0.000, hop=0)
- 4. `_banner` (score=0.569, sem=0.569, lex=0.000, hop=0)
- 5. `_step_ok` (score=0.567, sem=0.567, lex=0.000, hop=0)

### Query: `how does the graph get built from source code`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.011 | 8 | 42 | 8 | 0.564 | 0.681 | 0.289 |
| `semantic` | 0.011 | 8 | 42 | 8 | 0.686 | 0.686 | 0.222 |
| `legacy` | 0.011 | 8 | 42 | 8 | 0.684 | 0.684 | 0.222 |

#### Top nodes (hybrid)
- 1. `CodeGraph` (score=0.579, sem=0.684, lex=0.333, hop=0)
- 2. `ArchitectureAnalyzer._build_architecture_graph` (score=0.578, sem=0.684, lex=0.333, hop=0)
- 3. `CodeKG` (score=0.564, sem=0.663, lex=0.333, hop=1)
- 4. `CodeGraph.result` (score=0.552, sem=0.693, lex=0.222, hop=0)
- 5. `CodeGraph.__init__` (score=0.546, sem=0.684, lex=0.222, hop=1)

#### Top nodes (semantic)
- 1. `CodeGraph.result` (score=0.693, sem=0.693, lex=0.222, hop=0)
- 2. `CodeGraph` (score=0.684, sem=0.684, lex=0.333, hop=0)
- 3. `CodeGraph.__init__` (score=0.684, sem=0.684, lex=0.222, hop=1)
- 4. `ArchitectureAnalyzer._build_architecture_graph` (score=0.684, sem=0.684, lex=0.333, hop=0)
- 5. `ArchitectureAnalyzer._analyze_coupling` (score=0.684, sem=0.684, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `CodeGraph.result` (score=0.693, sem=0.693, lex=0.222, hop=0)
- 2. `CodeGraph` (score=0.684, sem=0.684, lex=0.333, hop=0)
- 3. `ArchitectureAnalyzer._build_architecture_graph` (score=0.684, sem=0.684, lex=0.333, hop=0)
- 4. `graph` (score=0.682, sem=0.682, lex=0.111, hop=0)
- 5. `CodeGraph.nodes` (score=0.675, sem=0.675, lex=0.111, hop=0)

## Model: `all-mpnet-base-v2`
- Build: 2.59s, indexed_rows=349, dim=768

### Query: `snapshot freshness comparison`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 1.108 | 8 | 57 | 10 | 0.537 | 0.511 | 0.600 |
| `semantic` | 0.019 | 8 | 57 | 10 | 0.521 | 0.521 | 0.400 |
| `legacy` | 0.013 | 8 | 57 | 10 | 0.505 | 0.505 | 0.467 |

#### Top nodes (hybrid)
- 1. `SnapshotManager` (score=0.569, sem=0.527, lex=0.667, hop=1)
- 2. `_snapshot_freshness` (score=0.559, sem=0.513, lex=0.667, hop=0)
- 3. `SnapshotManager.get_baseline` (score=0.549, sem=0.498, lex=0.667, hop=0)
- 4. `mcp_server` (score=0.542, sem=0.488, lex=0.667, hop=1)
- 5. `SnapshotManager.diff_snapshots` (score=0.469, sem=0.527, lex=0.333, hop=0)

#### Top nodes (semantic)
- 1. `SnapshotManager.diff_snapshots` (score=0.527, sem=0.527, lex=0.333, hop=0)
- 2. `Snapshot.key` (score=0.527, sem=0.527, lex=0.333, hop=1)
- 3. `SnapshotManager` (score=0.527, sem=0.527, lex=0.667, hop=1)
- 4. `_snapshot_freshness` (score=0.513, sem=0.513, lex=0.667, hop=0)
- 5. `_get_kg` (score=0.513, sem=0.513, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `SnapshotManager.diff_snapshots` (score=0.527, sem=0.527, lex=0.333, hop=0)
- 2. `_snapshot_freshness` (score=0.513, sem=0.513, lex=0.667, hop=0)
- 3. `SnapshotManager.list_snapshots` (score=0.501, sem=0.501, lex=0.333, hop=0)
- 4. `SnapshotManager.get_baseline` (score=0.498, sem=0.498, lex=0.667, hop=0)
- 5. `snapshot_diff` (score=0.488, sem=0.488, lex=0.333, hop=0)

### Query: `missing_lineno_policy cap_or_skip fallback`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.297 | 6 | 6 | 6 | 0.279 | 0.398 | 0.000 |
| `semantic` | 0.015 | 6 | 6 | 6 | 0.398 | 0.398 | 0.000 |
| `legacy` | 0.015 | 6 | 6 | 6 | 0.398 | 0.398 | 0.000 |

#### Top nodes (hybrid)
- 1. `CodeKGAnalyzer._is_special_entry_point` (score=0.283, sem=0.405, lex=0.000, hop=0)
- 2. `LayoutNode.line_count` (score=0.280, sem=0.400, lex=0.000, hop=0)
- 3. `CodeKG.__exit__` (score=0.278, sem=0.396, lex=0.000, hop=0)
- 4. `CodeKGAnalyzer._analyze_snapshots` (score=0.277, sem=0.396, lex=0.000, hop=0)
- 5. `CodeKGAnalyzer._analyze_docstring_coverage` (score=0.276, sem=0.394, lex=0.000, hop=0)

#### Top nodes (semantic)
- 1. `CodeKGAnalyzer._is_special_entry_point` (score=0.405, sem=0.405, lex=0.000, hop=0)
- 2. `LayoutNode.line_count` (score=0.400, sem=0.400, lex=0.000, hop=0)
- 3. `CodeKG.__exit__` (score=0.396, sem=0.396, lex=0.000, hop=0)
- 4. `CodeKGAnalyzer._analyze_snapshots` (score=0.396, sem=0.396, lex=0.000, hop=0)
- 5. `CodeKGAnalyzer._analyze_docstring_coverage` (score=0.394, sem=0.394, lex=0.000, hop=0)

#### Top nodes (legacy)
- 1. `CodeKGAnalyzer._is_special_entry_point` (score=0.405, sem=0.405, lex=0.000, hop=0)
- 2. `LayoutNode.line_count` (score=0.400, sem=0.400, lex=0.000, hop=0)
- 3. `CodeKG.__exit__` (score=0.396, sem=0.396, lex=0.000, hop=0)
- 4. `CodeKGAnalyzer._analyze_snapshots` (score=0.396, sem=0.396, lex=0.000, hop=0)
- 5. `CodeKGAnalyzer._analyze_docstring_coverage` (score=0.394, sem=0.394, lex=0.000, hop=0)

### Query: `how does the graph get built from source code`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.282 | 8 | 84 | 8 | 0.476 | 0.518 | 0.378 |
| `semantic` | 0.020 | 8 | 84 | 8 | 0.524 | 0.524 | 0.178 |
| `legacy` | 0.014 | 8 | 84 | 8 | 0.521 | 0.521 | 0.267 |

#### Top nodes (hybrid)
- 1. `_tab_snippets` (score=0.497, sem=0.520, lex=0.444, hop=1)
- 2. `CodeKGVisitor._add_edge` (score=0.495, sem=0.516, lex=0.444, hop=1)
- 3. `app` (score=0.464, sem=0.520, lex=0.333, hop=1)
- 4. `_build_pyvis` (score=0.463, sem=0.518, lex=0.333, hop=0)
- 5. `CodeKGVisitor` (score=0.461, sem=0.516, lex=0.333, hop=0)

#### Top nodes (semantic)
- 1. `CodeGraph.__repr__` (score=0.539, sem=0.539, lex=0.111, hop=0)
- 2. `main` (score=0.520, sem=0.520, lex=0.222, hop=0)
- 3. `_init_state` (score=0.520, sem=0.520, lex=0.111, hop=1)
- 4. `_render_sidebar` (score=0.520, sem=0.520, lex=0.222, hop=1)
- 5. `_tab_query` (score=0.520, sem=0.520, lex=0.222, hop=1)

#### Top nodes (legacy)
- 1. `CodeGraph.__repr__` (score=0.539, sem=0.539, lex=0.111, hop=0)
- 2. `main` (score=0.520, sem=0.520, lex=0.222, hop=0)
- 3. `_build_pyvis` (score=0.518, sem=0.518, lex=0.333, hop=0)
- 4. `CodeKGVisitor` (score=0.516, sem=0.516, lex=0.333, hop=0)
- 5. `CodeGraph` (score=0.510, sem=0.510, lex=0.333, hop=0)

## Model: `microsoft/codebert-base`
- Build: 3.69s, indexed_rows=349, dim=768

### Query: `snapshot freshness comparison`
- Params: k=8, hop=1, max_nodes=10

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.104 | 8 | 41 | 10 | 0.709 | 0.899 | 0.267 |
| `semantic` | 0.015 | 8 | 41 | 10 | 0.902 | 0.902 | 0.000 |
| `legacy` | 0.015 | 8 | 41 | 10 | 0.900 | 0.900 | 0.000 |

#### Top nodes (hybrid)
- 1. `SnapshotDelta` (score=0.729, sem=0.898, lex=0.333, hop=0)
- 2. `Snapshot.from_dict` (score=0.729, sem=0.898, lex=0.333, hop=1)
- 3. `SnapshotManager.load_snapshot` (score=0.729, sem=0.898, lex=0.333, hop=1)
- 4. `snapshots` (score=0.729, sem=0.898, lex=0.333, hop=1)
- 5. `SnapshotManifest` (score=0.632, sem=0.902, lex=0.000, hop=0)

#### Top nodes (semantic)
- 1. `SnapshotManifest` (score=0.902, sem=0.902, lex=0.000, hop=0)
- 2. `SnapshotManager.load_manifest` (score=0.902, sem=0.902, lex=0.000, hop=1)
- 3. `SnapshotManifest.from_dict` (score=0.902, sem=0.902, lex=0.000, hop=1)
- 4. `SnapshotManifest.to_dict` (score=0.902, sem=0.902, lex=0.000, hop=1)
- 5. `ModuleLayer` (score=0.901, sem=0.901, lex=0.000, hop=0)

#### Top nodes (legacy)
- 1. `SnapshotManifest` (score=0.902, sem=0.902, lex=0.000, hop=0)
- 2. `ModuleLayer` (score=0.901, sem=0.901, lex=0.000, hop=0)
- 3. `CodeKG.__exit__` (score=0.900, sem=0.900, lex=0.000, hop=0)
- 4. `BuildStats.__str__` (score=0.899, sem=0.899, lex=0.000, hop=0)
- 5. `MainWindow.on_pick` (score=0.899, sem=0.899, lex=0.000, hop=0)

### Query: `missing_lineno_policy cap_or_skip fallback`
- Params: k=6, hop=0, max_nodes=6

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.059 | 6 | 6 | 6 | 0.651 | 0.930 | 0.000 |
| `semantic` | 0.013 | 6 | 6 | 6 | 0.930 | 0.930 | 0.000 |
| `legacy` | 0.013 | 6 | 6 | 6 | 0.930 | 0.930 | 0.000 |

#### Top nodes (hybrid)
- 1. `LayoutNode.line_count` (score=0.653, sem=0.933, lex=0.000, hop=0)
- 2. `suppress_ingestion_logging` (score=0.651, sem=0.930, lex=0.000, hop=0)
- 3. `CodeKG.__exit__` (score=0.650, sem=0.929, lex=0.000, hop=0)
- 4. `_docstring_signal` (score=0.650, sem=0.928, lex=0.000, hop=0)
- 5. `CodeKGAnalyzer._analyze_baseline` (score=0.650, sem=0.928, lex=0.000, hop=0)

#### Top nodes (semantic)
- 1. `LayoutNode.line_count` (score=0.933, sem=0.933, lex=0.000, hop=0)
- 2. `suppress_ingestion_logging` (score=0.930, sem=0.930, lex=0.000, hop=0)
- 3. `CodeKG.__exit__` (score=0.929, sem=0.929, lex=0.000, hop=0)
- 4. `_docstring_signal` (score=0.928, sem=0.928, lex=0.000, hop=0)
- 5. `CodeKGAnalyzer._analyze_baseline` (score=0.928, sem=0.928, lex=0.000, hop=0)

#### Top nodes (legacy)
- 1. `LayoutNode.line_count` (score=0.933, sem=0.933, lex=0.000, hop=0)
- 2. `suppress_ingestion_logging` (score=0.930, sem=0.930, lex=0.000, hop=0)
- 3. `CodeKG.__exit__` (score=0.929, sem=0.929, lex=0.000, hop=0)
- 4. `_docstring_signal` (score=0.928, sem=0.928, lex=0.000, hop=0)
- 5. `CodeKGAnalyzer._analyze_baseline` (score=0.928, sem=0.928, lex=0.000, hop=0)

### Query: `how does the graph get built from source code`
- Params: k=8, hop=1, max_nodes=8

| Mode | Time (s) | Seeds | Expanded | Returned | Mean score | Mean semantic | Mean lexical |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hybrid` | 0.039 | 8 | 69 | 8 | 0.756 | 0.909 | 0.400 |
| `semantic` | 0.015 | 8 | 69 | 8 | 0.913 | 0.913 | 0.089 |
| `legacy` | 0.014 | 8 | 69 | 8 | 0.910 | 0.910 | 0.200 |

#### Top nodes (hybrid)
- 1. `index` (score=0.802, sem=0.907, lex=0.556, hop=1)
- 2. `cmd_query` (score=0.771, sem=0.911, lex=0.444, hop=0)
- 3. `CodeKG` (score=0.739, sem=0.912, lex=0.333, hop=1)
- 4. `kg` (score=0.735, sem=0.908, lex=0.333, hop=1)
- 5. `build_sqlite` (score=0.735, sem=0.907, lex=0.333, hop=0)

#### Top nodes (semantic)
- 1. `MainWindow.on_pick` (score=0.913, sem=0.913, lex=0.222, hop=0)
- 2. `_docstring_to_markdown` (score=0.913, sem=0.913, lex=0.111, hop=1)
- 3. `MainWindow.highlight_actor` (score=0.913, sem=0.913, lex=0.111, hop=1)
- 4. `MainWindow.reset_actor_appearances` (score=0.913, sem=0.913, lex=0.000, hop=1)
- 5. `MainWindow.update_status_display` (score=0.913, sem=0.913, lex=0.000, hop=1)

#### Top nodes (legacy)
- 1. `MainWindow.on_pick` (score=0.913, sem=0.913, lex=0.222, hop=0)
- 2. `CodeKG.__exit__` (score=0.912, sem=0.912, lex=0.222, hop=0)
- 3. `cmd_query` (score=0.911, sem=0.911, lex=0.444, hop=0)
- 4. `BuildStats.__str__` (score=0.909, sem=0.909, lex=0.111, hop=0)
- 5. `_escape` (score=0.908, sem=0.908, lex=0.000, hop=0)
