# Overview

> **Generated:** 2026-03-07T21:41:54.194439+00:00 | **Version:** 0.5.2 | **Commit:** 6e945e0fb8

This codebase is organized into 2 architectural layers: Scripts Layer, Src Layer. The architecture supports semantic code search via knowledge graph indexing and querying.

## Architectural Layers

### Scripts Layer
Handles scripts concerns.

**Responsibilities:**
- Component responsibility

**Modules:**
- `scripts/generate_wiki.py`

### Src Layer
Handles src concerns.

**Responsibilities:**
- Component responsibility

**Modules:**
- `src/code_kg/__init__.py`
- `src/code_kg/__main__.py`
- `src/code_kg/app.py`
- `src/code_kg/architecture.py`
- `src/code_kg/build_codekg_lancedb.py`
- `src/code_kg/build_codekg_sqlite.py`
- `src/code_kg/cli/__init__.py`
- `src/code_kg/cli/cmd_analyze.py`
- `src/code_kg/cli/cmd_architecture.py`
- `src/code_kg/cli/cmd_build.py`
- `src/code_kg/cli/cmd_build_full.py`
- `src/code_kg/cli/cmd_mcp.py`
- `src/code_kg/cli/cmd_model.py`
- `src/code_kg/cli/cmd_query.py`
- `src/code_kg/cli/cmd_snapshot.py`
- `src/code_kg/cli/cmd_viz.py`
- `src/code_kg/cli/main.py`
- `src/code_kg/cli/options.py`
- `src/code_kg/codekg.py`
- `src/code_kg/codekg_query.py`
- `src/code_kg/codekg_snippet_packer.py`
- `src/code_kg/codekg_thorough_analysis.py`
- `src/code_kg/codekg_viz.py`
- `src/code_kg/codekg_viz3d.py`
- `src/code_kg/config.py`
- `src/code_kg/graph.py`
- `src/code_kg/index.py`
- `src/code_kg/kg.py`
- `src/code_kg/layout3d.py`
- `src/code_kg/mcp_server.py`
- `src/code_kg/snapshots.py`
- `src/code_kg/store.py`
- `src/code_kg/utils.py`
- `src/code_kg/visitor.py`
- `src/code_kg/viz3d.py`
- `src/code_kg/viz3d_timeline.py`

## Key Components

### ModuleLayer
**Type:** `class` | **File:** `src/code_kg/architecture.py:40`

Represents a logical layer or module group.

### ComponentNode
**Type:** `class` | **File:** `src/code_kg/architecture.py:50`

A significant architectural component.

### ArchitectureGraph
**Type:** `class` | **File:** `src/code_kg/architecture.py:62`

Structured representation of architecture with provenance.

### ArchitectureAnalyzer
**Type:** `class` | **File:** `src/code_kg/architecture.py:82`

Analyzes codebase architecture and produces coherent descriptions.

### Node
**Type:** `class` | **File:** `src/code_kg/codekg.py:54`

Graph node.

## Critical Paths

### Path 1: Graph Query Pipeline
Semantic search → graph expansion → snippet packing

- Semantic search finds seed nodes via LanceDB
- Graph expansion traverses CALLS, CONTAINS, IMPORTS edges
- Snippet pack materializes source code with context

### Path 2: AST Extraction & Graph Building
Repository scanning → code analysis → graph storage

- CodeGraph walks repo and extracts Python files
- CodeKGVisitor traverses AST, collects nodes and edges
- GraphStore persists in SQLite with symbol resolution

## Dependency & Coupling Analysis

### Module Dependencies
**scripts/generate_wiki.py**
- imports: argparse
- imports: os
- imports: re
- imports: shutil
- imports: subprocess
- imports: tempfile
- imports: pathlib.Path

**src/code_kg/store.py**
- imports: __future__.annotations
- imports: json
- imports: sqlite3
- imports: collections.abc.Iterable
- imports: collections.abc.Sequence
- imports: pathlib.Path
- imports: code_kg.codekg.Edge
- imports: code_kg.codekg.Node

**src/code_kg/snapshots.py**
- imports: __future__.annotations
- imports: json
- imports: subprocess
- imports: dataclasses.asdict
- imports: dataclasses.dataclass
- imports: dataclasses.field
- imports: datetime.UTC
- imports: datetime.datetime
- imports: pathlib.Path
- imports: typing.Any

**src/code_kg/codekg.py**
- imports: __future__.annotations
- imports: ast
- imports: os
- imports: collections.abc.Iterable
- imports: dataclasses.dataclass
- imports: pathlib.Path
- imports: code_kg.utils.node_id
- imports: code_kg.utils.rel_module_path
- imports: code_kg.visitor.CodeKGVisitor

**src/code_kg/config.py**
- imports: __future__.annotations
- imports: tomllib
- imports: pathlib.Path

**src/code_kg/index.py**
- imports: __future__.annotations
- imports: collections.abc.Sequence
- imports: dataclasses.dataclass
- imports: pathlib.Path
- imports: typing.TYPE_CHECKING
- imports: numpy
- imports: code_kg.codekg.DEFAULT_MODEL

**src/code_kg/graph.py**
- imports: __future__.annotations
- imports: collections.Counter
- imports: pathlib.Path
- imports: code_kg.codekg.Edge
- imports: code_kg.codekg.Node
- imports: code_kg.codekg.extract_repo

**src/code_kg/__init__.py**
- imports: code_kg.codekg.DEFAULT_MODEL
- imports: code_kg.codekg.Edge
- imports: code_kg.codekg.Node
- imports: code_kg.graph.CodeGraph
- imports: code_kg.index.Embedder
- imports: code_kg.index.SeedHit
- imports: code_kg.index.SemanticIndex
- imports: code_kg.index.SentenceTransformerEmbedder
- imports: code_kg.kg.BuildStats
- imports: code_kg.kg.CodeKG
- imports: code_kg.kg.QueryResult
- imports: code_kg.kg.Snippet
- imports: code_kg.kg.SnippetPack
- imports: code_kg.store.DEFAULT_RELS
- imports: code_kg.store.GraphStore
- imports: code_kg.store.ProvMeta

**src/code_kg/codekg_thorough_analysis.py**
- imports: datetime
- imports: json
- imports: logging
- imports: os
- imports: subprocess
- imports: collections.defaultdict
- imports: dataclasses.asdict
- imports: dataclasses.dataclass
- imports: pathlib.Path
- imports: rich.console.Console
- imports: rich.panel.Panel
- imports: rich.table.Table

**src/code_kg/build_codekg_lancedb.py**
- imports: code_kg.cli.cmd_build.build_lancedb

**src/code_kg/layout3d.py**
- imports: __future__.annotations
- imports: abc.ABC
- imports: abc.abstractmethod
- imports: dataclasses.dataclass
- imports: numpy

**src/code_kg/build_codekg_sqlite.py**
- imports: code_kg.cli.cmd_build.build_sqlite

**src/code_kg/visitor.py**
- imports: ast
- imports: code_kg.utils.node_id

**src/code_kg/utils.py**
- imports: __future__.annotations
- imports: pathlib.Path

**src/code_kg/viz3d_timeline.py**
- imports: __future__.annotations
- imports: pathlib.Path
- imports: typing.Any
- imports: plotly.graph_objects
- imports: plotly.subplots
- imports: code_kg.snapshots.SnapshotManager

**src/code_kg/architecture.py**
- imports: __future__.annotations
- imports: json
- imports: dataclasses.asdict
- imports: dataclasses.dataclass
- imports: dataclasses.field

## Health & Quality Signals

- **Circular Dependencies:** 0
- **Orphaned Functions:** 0
