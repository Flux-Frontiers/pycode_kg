"""
test_architecture.py

Tests for architecture analysis and coherent descriptions:
  ArchitectureAnalyzer, ArchitectureGraph, ModuleLayer, ComponentNode
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pycode_kg.architecture import (
    ArchitectureAnalyzer,
    ArchitectureGraph,
    ComponentNode,
    ModuleLayer,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_store() -> MagicMock:
    """Create a mock GraphStore."""
    store = MagicMock()

    # Mock query_nodes for classes
    def mock_query_nodes(kinds=None):
        if kinds and "class" in kinds:
            return [
                {
                    "id": "cls:src/pycode_kg/store:GraphStore",
                    "name": "GraphStore",
                    "module_path": "src/pycode_kg/store.py",
                    "kind": "class",
                    "lineno": 42,
                    "docstring": "Main graph storage class",
                }
            ]
        return [
            {
                "id": "mod:src/pycode_kg/cli:cli",
                "module_path": "src/pycode_kg/cli",
                "kind": "module",
            },
            {
                "id": "mod:src/pycode_kg/store:store",
                "module_path": "src/pycode_kg/store",
                "kind": "module",
            },
            {
                "id": "mod:src/pycode_kg/index:index",
                "module_path": "src/pycode_kg/index",
                "kind": "module",
            },
        ]

    store.query_nodes = MagicMock(side_effect=mock_query_nodes)
    store.con = MagicMock()
    store.con.execute.return_value.fetchall.return_value = [
        ("src/pycode_kg/store", "src/pycode_kg/index"),
        ("src/pycode_kg/cli", "src/pycode_kg/store"),
    ]
    return store


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Create a temporary repository root."""
    repo = tmp_path / "repo"
    repo.mkdir()
    readme = repo / "README.md"
    readme.write_text("# Test Repository\n\nTest codebase.\n")
    return repo


@pytest.fixture
def architecture_analyzer(mock_store: MagicMock, repo_root: Path) -> ArchitectureAnalyzer:
    """Create an ArchitectureAnalyzer with mocked store."""
    return ArchitectureAnalyzer(
        store=mock_store,
        repo_root=repo_root,
        version="0.5.1",
        commit="abc123",  # pragma: allowlist secret
    )


# ---------------------------------------------------------------------------
# ModuleLayer Tests
# ---------------------------------------------------------------------------


def test_module_layer_creation() -> None:
    """Test ModuleLayer creation."""
    layer = ModuleLayer(
        name="CLI Layer",
        description="Command-line interface",
        modules=["src/pycode_kg/cli/__init__.py", "src/pycode_kg/cli/main.py"],
        responsibilities=["Handle CLI commands", "Route subcommands"],
    )
    assert layer.name == "CLI Layer"
    assert layer.description == "Command-line interface"
    assert len(layer.modules) == 2
    assert len(layer.responsibilities) == 2


# ---------------------------------------------------------------------------
# ComponentNode Tests
# ---------------------------------------------------------------------------


def test_component_node_creation() -> None:
    """Test ComponentNode creation."""
    comp = ComponentNode(
        node_id="cls:src/pycode_kg/store:GraphStore",
        name="GraphStore",
        kind="class",
        description="Central graph storage and querying",
        file="src/pycode_kg/store.py",
        lineno=42,
    )
    assert comp.name == "GraphStore"
    assert comp.kind == "class"
    assert comp.file == "src/pycode_kg/store.py"
    assert comp.lineno == 42


# ---------------------------------------------------------------------------
# ArchitectureGraph Tests
# ---------------------------------------------------------------------------


def test_architecture_graph_creation() -> None:
    """Test ArchitectureGraph creation."""
    graph = ArchitectureGraph(
        title="PyCodeKG Architecture",
        description="Knowledge graph for Python codebases",
        layers=[],
        key_components=[],
        critical_paths=[],
        coupling_summary={},
    )
    assert graph.title == "PyCodeKG Architecture"
    assert graph.description == "Knowledge graph for Python codebases"
    assert graph.generated_at is not None


def test_architecture_graph_with_metadata() -> None:
    """Test ArchitectureGraph with provenance metadata."""
    graph = ArchitectureGraph(
        title="Test Architecture",
        description="Test description",
        layers=[],
        key_components=[],
        critical_paths=[],
        coupling_summary={},
        version="0.5.1",
        commit="abc123",  # pragma: allowlist secret
    )
    assert graph.version == "0.5.1"
    assert graph.commit == "abc123"  # pragma: allowlist secret


def test_architecture_graph_with_analysis_results() -> None:
    """Test ArchitectureGraph with thorough analysis integration."""
    graph = ArchitectureGraph(
        title="Test Architecture",
        description="Test description",
        layers=[],
        key_components=[],
        critical_paths=[],
        coupling_summary={},
        complexity_hotspots=[
            {"name": "process_data", "fan_in": 10, "fan_out": 5, "risk_level": "high"}
        ],
        health_signals={"Docstring Coverage": 0.95, "Circular Dependencies": 0},
        issues=["High fan-out in process_data"],
        strengths=["Well-documented codebase"],
    )
    assert len(graph.complexity_hotspots) == 1
    assert len(graph.issues) == 1
    assert len(graph.strengths) == 1


# ---------------------------------------------------------------------------
# ArchitectureAnalyzer Tests
# ---------------------------------------------------------------------------


def test_architecture_analyzer_creation(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test ArchitectureAnalyzer initialization."""
    assert architecture_analyzer.version == "0.5.1"
    assert architecture_analyzer.commit == "abc123"  # pragma: allowlist secret
    assert architecture_analyzer.thorough_analysis == {}


def test_architecture_analyzer_incorporate_analysis(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test incorporating thorough analysis results."""
    analysis_results = {
        "issues": ["Issue 1", "Issue 2"],
        "strengths": ["Strength 1", "Strength 2"],
        "high_fan_in_functions": [
            {"name": "func_a", "fan_in": 10, "fan_out": 3, "risk_level": "high"}
        ],
        "high_fan_out_functions": [
            {"name": "func_b", "fan_in": 2, "fan_out": 15, "risk_level": "high"}
        ],
        "docstring_coverage": {"total": 0.95},
        "circular_dependencies": [],
        "orphaned_functions": [],
    }
    architecture_analyzer.incorporate_thorough_analysis(analysis_results)
    assert architecture_analyzer.thorough_analysis == analysis_results


def test_architecture_analyzer_detect_layers(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test layer detection from module structure."""
    layers = architecture_analyzer._detect_layers()
    assert len(layers) > 0
    assert all(hasattr(layer, "name") for layer in layers)
    assert all(hasattr(layer, "modules") for layer in layers)


def test_architecture_analyzer_identify_key_components(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test key component identification."""
    architecture_analyzer.store.query_nodes.return_value = [
        {
            "id": "cls:src/pycode_kg/store:GraphStore",
            "name": "GraphStore",
            "kind": "class",
            "module_path": "src/pycode_kg/store.py",
            "lineno": 42,
            "docstring": "Main graph storage class",
        }
    ]
    components = architecture_analyzer._identify_key_components()
    assert len(components) > 0
    assert components[0].name == "GraphStore"


def test_architecture_analyzer_trace_critical_paths(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test critical path tracing."""
    paths = architecture_analyzer._trace_critical_paths()
    assert len(paths) > 0
    assert all("name" in path for path in paths)
    assert all("description" in path for path in paths)


def test_architecture_analyzer_analyze_coupling(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test module coupling analysis."""
    coupling = architecture_analyzer._analyze_coupling()
    assert "dependencies" in coupling
    assert "total_import_edges" in coupling
    assert "summary" in coupling


def test_architecture_analyzer_extract_complexity_hotspots(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test complexity hotspot extraction."""
    architecture_analyzer.thorough_analysis = {
        "high_fan_in_functions": [
            {"name": "func_a", "fan_in": 10, "fan_out": 3, "risk_level": "high"}
        ],
        "high_fan_out_functions": [
            {"name": "func_b", "fan_in": 2, "fan_out": 15, "risk_level": "high"}
        ],
    }
    hotspots = architecture_analyzer._extract_complexity_hotspots()
    assert len(hotspots) > 0


def test_architecture_analyzer_extract_health_signals(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test health signal extraction."""
    architecture_analyzer.thorough_analysis = {
        "docstring_coverage": {"total": 0.95},
        "circular_dependencies": [],
        "orphaned_functions": ["orphaned_func"],
    }
    signals = architecture_analyzer._extract_health_signals()
    assert "Docstring Coverage" in signals
    assert "Circular Dependencies" in signals
    assert "Orphaned Functions" in signals


def test_architecture_analyzer_infer_project_title(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test project title inference from README."""
    title = architecture_analyzer._infer_project_title()
    assert title == "Test Repository"


def test_architecture_analyzer_generate_summary(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test architecture summary generation."""
    layers = [
        ModuleLayer("CLI Layer", "CLI", ["src/pycode_kg/cli"], []),
        ModuleLayer("Store Layer", "Storage", ["src/pycode_kg/store"], []),
    ]
    summary = architecture_analyzer._generate_architecture_summary(layers)
    assert "CLI Layer" in summary or "Store Layer" in summary
    assert "semantic code search" in summary


def test_architecture_analyzer_analyze_to_markdown(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test Markdown output generation."""
    architecture_analyzer.thorough_analysis = {
        "issues": [],
        "strengths": [],
        "high_fan_in_functions": [],
        "high_fan_out_functions": [],
        "docstring_coverage": {"total": 0.95},
        "circular_dependencies": [],
        "orphaned_functions": [],
    }

    markdown = architecture_analyzer.analyze_to_markdown()
    assert isinstance(markdown, str)
    assert len(markdown) > 0
    assert "# " in markdown  # Has headings
    assert "Architectural Layers" in markdown
    assert "Generated:" in markdown or "generated_at" in markdown.lower()


def test_architecture_analyzer_analyze_to_json(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test JSON output generation."""
    architecture_analyzer.thorough_analysis = {
        "issues": [],
        "strengths": [],
        "high_fan_in_functions": [],
        "high_fan_out_functions": [],
        "docstring_coverage": {"total": 0.95},
        "circular_dependencies": [],
        "orphaned_functions": [],
    }

    json_output = architecture_analyzer.analyze_to_json()
    assert isinstance(json_output, str)

    # Verify it's valid JSON
    data = json.loads(json_output)
    assert "metadata" in data
    assert "description" in data
    assert "layers" in data
    assert "key_components" in data


def test_architecture_analyzer_json_includes_provenance(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test that JSON output includes provenance metadata."""
    architecture_analyzer.thorough_analysis = {
        "issues": [],
        "strengths": [],
        "high_fan_in_functions": [],
        "high_fan_out_functions": [],
        "docstring_coverage": {"total": 0.95},
        "circular_dependencies": [],
        "orphaned_functions": [],
    }

    json_output = architecture_analyzer.analyze_to_json()
    data = json.loads(json_output)

    assert data["metadata"]["version"] == "0.5.1"
    assert data["metadata"]["commit"] == "abc123"  # pragma: allowlist secret
    assert "generated_at" in data["metadata"]


def test_architecture_analyzer_markdown_includes_hotspots(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test that Markdown includes complexity hotspots."""
    architecture_analyzer.thorough_analysis = {
        "issues": [],
        "strengths": [],
        "high_fan_in_functions": [
            {"name": "critical_func", "fan_in": 15, "fan_out": 5, "risk_level": "high"}
        ],
        "high_fan_out_functions": [],
        "docstring_coverage": {"total": 0.95},
        "circular_dependencies": [],
        "orphaned_functions": [],
    }

    markdown = architecture_analyzer.analyze_to_markdown()
    assert "Complexity Hotspots" in markdown
    assert "critical_func" in markdown


def test_architecture_analyzer_markdown_includes_health_signals(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test that Markdown includes health signals."""
    architecture_analyzer.thorough_analysis = {
        "issues": [],
        "strengths": [],
        "high_fan_in_functions": [],
        "high_fan_out_functions": [],
        "docstring_coverage": {"total": 0.95},
        "circular_dependencies": [],
        "orphaned_functions": [],
    }

    markdown = architecture_analyzer.analyze_to_markdown()
    assert "Health" in markdown or "Quality" in markdown or "Coverage" in markdown


def test_architecture_analyzer_markdown_includes_issues_and_strengths(
    architecture_analyzer: ArchitectureAnalyzer,
) -> None:
    """Test that Markdown includes issues and strengths."""
    architecture_analyzer.thorough_analysis = {
        "issues": ["Issue 1", "Issue 2"],
        "strengths": ["Strength 1", "Strength 2"],
        "high_fan_in_functions": [],
        "high_fan_out_functions": [],
        "docstring_coverage": {"total": 0.95},
        "circular_dependencies": [],
        "orphaned_functions": [],
    }

    markdown = architecture_analyzer.analyze_to_markdown()
    assert "Issue 1" in markdown or "Issues" in markdown
    assert "Strength 1" in markdown or "Strengths" in markdown
