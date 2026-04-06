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
- `src/pycode_kg/__init__.py`
- `src/pycode_kg/__main__.py`
- `src/pycode_kg/app.py`
- `src/pycode_kg/architecture.py`
- `src/pycode_kg/build_pycodekg_lancedb.py`
- `src/pycode_kg/build_pycodekg_sqlite.py`
- `src/pycode_kg/cli/__init__.py`
- `src/pycode_kg/cli/cmd_analyze.py`
- `src/pycode_kg/cli/cmd_architecture.py`
- `src/pycode_kg/cli/cmd_build.py`
- `src/pycode_kg/cli/cmd_build_full.py`
- `src/pycode_kg/cli/cmd_mcp.py`
- `src/pycode_kg/cli/cmd_model.py`
- `src/pycode_kg/cli/cmd_query.py`
- `src/pycode_kg/cli/cmd_snapshot.py`
- `src/pycode_kg/cli/cmd_viz.py`
- `src/pycode_kg/cli/main.py`
- `src/pycode_kg/cli/options.py`
- `src/pycode_kg/pycodekg.py`
- `src/pycode_kg/pycodekg_query.py`
- `src/pycode_kg/pycodekg_snippet_packer.py`
- `src/pycode_kg/pycodekg_thorough_analysis.py`
- `src/pycode_kg/pycodekg_viz.py`
- `src/pycode_kg/pycodekg_viz3d.py`
- `src/pycode_kg/config.py`
- `src/pycode_kg/graph.py`
- `src/pycode_kg/index.py`
- `src/pycode_kg/kg.py`
- `src/pycode_kg/layout3d.py`
- `src/pycode_kg/mcp_server.py`
- `src/pycode_kg/snapshots.py`
- `src/pycode_kg/store.py`
- `src/pycode_kg/utils.py`
- `src/pycode_kg/visitor.py`
- `src/pycode_kg/viz3d.py`
- `src/pycode_kg/viz3d_timeline.py`

## Key Components

### ModuleLayer
**Type:** `class` | **File:** `src/pycode_kg/architecture.py:40`

Represents a logical layer or module group.

### ComponentNode
**Type:** `class` | **File:** `src/pycode_kg/architecture.py:50`

A significant architectural component.

### ArchitectureGraph
**Type:** `class` | **File:** `src/pycode_kg/architecture.py:62`

Structured representation of architecture with provenance.

### ArchitectureAnalyzer
**Type:** `class` | **File:** `src/pycode_kg/architecture.py:82`

Analyzes codebase architecture and produces coherent descriptions.

### Node
**Type:** `class` | **File:** `src/pycode_kg/pycodekg.py:54`

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
- PyCodeKGVisitor traverses AST, collects nodes and edges
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

**src/pycode_kg/store.py**
- imports: __future__.annotations
- imports: json
- imports: sqlite3
- imports: collections.abc.Iterable
- imports: collections.abc.Sequence
- imports: pathlib.Path
- imports: pycode_kg.pycodekg.Edge
- imports: pycode_kg.pycodekg.Node

**src/pycode_kg/snapshots.py**
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

**src/pycode_kg/pycodekg.py**
- imports: __future__.annotations
- imports: ast
- imports: os
- imports: collections.abc.Iterable
- imports: dataclasses.dataclass
- imports: pathlib.Path
- imports: pycode_kg.utils.node_id
- imports: pycode_kg.utils.rel_module_path
- imports: pycode_kg.visitor.PyCodeKGVisitor

**src/pycode_kg/config.py**
- imports: __future__.annotations
- imports: tomllib
- imports: pathlib.Path

**src/pycode_kg/index.py**
- imports: __future__.annotations
- imports: collections.abc.Sequence
- imports: dataclasses.dataclass
- imports: pathlib.Path
- imports: typing.TYPE_CHECKING
- imports: numpy
- imports: pycode_kg.pycodekg.DEFAULT_MODEL

**src/pycode_kg/graph.py**
- imports: __future__.annotations
- imports: collections.Counter
- imports: pathlib.Path
- imports: pycode_kg.pycodekg.Edge
- imports: pycode_kg.pycodekg.Node
- imports: pycode_kg.pycodekg.extract_repo

**src/pycode_kg/__init__.py**
- imports: pycode_kg.pycodekg.DEFAULT_MODEL
- imports: pycode_kg.pycodekg.Edge
- imports: pycode_kg.pycodekg.Node
- imports: pycode_kg.graph.CodeGraph
- imports: pycode_kg.index.Embedder
- imports: pycode_kg.index.SeedHit
- imports: pycode_kg.index.SemanticIndex
- imports: pycode_kg.index.SentenceTransformerEmbedder
- imports: pycode_kg.kg.BuildStats
- imports: pycode_kg.kg.PyCodeKG
- imports: pycode_kg.kg.QueryResult
- imports: pycode_kg.kg.Snippet
- imports: pycode_kg.kg.SnippetPack
- imports: pycode_kg.store.DEFAULT_RELS
- imports: pycode_kg.store.GraphStore
- imports: pycode_kg.store.ProvMeta

**src/pycode_kg/pycodekg_thorough_analysis.py**
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

**src/pycode_kg/build_pycodekg_lancedb.py**
- imports: pycode_kg.cli.cmd_build.build_lancedb

**src/pycode_kg/layout3d.py**
- imports: __future__.annotations
- imports: abc.ABC
- imports: abc.abstractmethod
- imports: dataclasses.dataclass
- imports: numpy

**src/pycode_kg/build_pycodekg_sqlite.py**
- imports: pycode_kg.cli.cmd_build.build_sqlite

**src/pycode_kg/visitor.py**
- imports: ast
- imports: pycode_kg.utils.node_id

**src/pycode_kg/utils.py**
- imports: __future__.annotations
- imports: pathlib.Path

**src/pycode_kg/viz3d_timeline.py**
- imports: __future__.annotations
- imports: pathlib.Path
- imports: typing.Any
- imports: plotly.graph_objects
- imports: plotly.subplots
- imports: pycode_kg.snapshots.SnapshotManager

**src/pycode_kg/architecture.py**
- imports: __future__.annotations
- imports: json
- imports: dataclasses.asdict
- imports: dataclasses.dataclass
- imports: dataclasses.field

## Health & Quality Signals

- **Circular Dependencies:** 0
- **Orphaned Functions:** 0
