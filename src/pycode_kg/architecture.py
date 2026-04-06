"""
architecture.py — Coherent Architectural Analysis

Provides intelligent analysis of codebase architecture, producing humanreadable descriptions of:
  - Module layers and their purposes
  - Key architectural components (classes, functions)
  - Inter-module dependencies and coupling
  - Data flow patterns
  - Critical paths and integration points
  - Complexity hotspots and risk factors
  - Health signals (docstring coverage, circular dependencies, issues)

Outputs both Markdown (human-readable) and JSON (machine-ingestion) formats,
with timestamp/version provenance stamping.

Integrates thorough analysis results for richer architectural insights suitable
for infographic generation and decision-making.

Usage
-----
>>> from pycode_kg.architecture import ArchitectureAnalyzer
>>> analyzer = ArchitectureAnalyzer(store, repo_root, version="0.5.1")
>>> analyzer.incorporate_thorough_analysis(analysis_results)
>>> arch_md = analyzer.analyze_to_markdown()
>>> arch_json = analyzer.analyze_to_json()
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pycode_kg.store import GraphStore


@dataclass
class ModuleLayer:
    """Represents a logical layer or module group."""

    name: str
    description: str
    modules: list[str]  # module paths in this layer
    responsibilities: list[str]  # high-level responsibilities


@dataclass
class ComponentNode:
    """A significant architectural component."""

    node_id: str
    name: str
    kind: str  # class, function, module
    description: str
    file: str
    lineno: int


@dataclass
class ArchitectureGraph:
    """Structured representation of architecture with provenance."""

    title: str
    description: str
    layers: list[ModuleLayer]
    key_components: list[ComponentNode]
    critical_paths: list[dict]  # important call chains
    coupling_summary: dict[str, Any]  # module dependencies and strength
    # Metadata for provenance
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    version: str = "unknown"
    commit: str = "unknown"
    # Thorough analysis integration
    complexity_hotspots: list[dict] = field(default_factory=list)
    health_signals: dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)


class ArchitectureAnalyzer:
    """Analyzes codebase architecture and produces coherent descriptions."""

    def __init__(
        self, store: GraphStore, repo_root: Path, version: str = "unknown", commit: str = "unknown"
    ):
        """
        Initialize architecture analyzer.

        :param store: GraphStore instance for querying graph.
        :param repo_root: Root directory of repository.
        :param version: Version string for provenance stamping.
        :param commit: Commit hash for provenance stamping.
        """
        self.store = store
        self.repo_root = Path(repo_root)
        self.version = version
        self.commit = commit
        self.thorough_analysis: dict[str, Any] = {}

    def incorporate_thorough_analysis(self, analysis_results: dict[str, Any]) -> None:
        """
        Incorporate results from thorough analysis into architecture.

        Enriches the architecture description with complexity hotspots,
        issues, strengths, and health signals from the PyCodeKG analyzer.

        :param analysis_results: Output from PyCodeKGAnalyzer.run_analysis()
        """
        self.thorough_analysis = analysis_results

    def analyze_to_markdown(self) -> str:
        """
        Analyze architecture and produce Markdown description.

        Returns a comprehensive architectural overview in Markdown format,
        suitable for documentation, infographics, and human consumption.
        Includes provenance metadata and thorough analysis integration.

        :return: Markdown string describing the architecture.
        """
        arch = self._build_architecture_graph()

        lines = []
        # Header with provenance
        lines.append(f"# {arch.title}")
        lines.append("")
        lines.append(
            f"> **Generated:** {arch.generated_at} | **Version:** {arch.version} | **Commit:** {arch.commit}"
        )
        lines.append("")
        lines.append(arch.description)
        lines.append("")

        # Layers section
        lines.append("## Architectural Layers")
        lines.append("")
        for layer in arch.layers:
            lines.append(f"### {layer.name}")
            lines.append(layer.description)
            lines.append("")
            if layer.responsibilities:
                lines.append("**Responsibilities:**")
                for resp in layer.responsibilities:
                    lines.append(f"- {resp}")
                lines.append("")
            if layer.modules:
                lines.append("**Modules:**")
                for mod in layer.modules:
                    lines.append(f"- `{mod}`")
                lines.append("")

        # Key components
        if arch.key_components:
            lines.append("## Key Components")
            lines.append("")
            for comp in arch.key_components:
                lines.append(f"### {comp.name}")
                lines.append(f"**Type:** `{comp.kind}` | **File:** `{comp.file}:{comp.lineno}`")
                lines.append("")
                lines.append(comp.description)
                lines.append("")

        # Critical paths
        if arch.critical_paths:
            lines.append("## Critical Paths")
            lines.append("")
            for i, path in enumerate(arch.critical_paths, 1):
                lines.append(f"### Path {i}: {path.get('name', 'Key Workflow')}")
                lines.append(path.get("description", ""))
                lines.append("")
                if "steps" in path:
                    for step in path["steps"]:
                        lines.append(f"- {step}")
                lines.append("")

        # Coupling analysis
        if arch.coupling_summary:
            lines.append("## Dependency & Coupling Analysis")
            lines.append("")
            lines.append("### Module Dependencies")
            for mod, deps in arch.coupling_summary.get("dependencies", {}).items():
                if deps:
                    lines.append(f"**{mod}**")
                    for dep in deps:
                        lines.append(f"- imports: {dep}")
                    lines.append("")

        # Complexity hotspots with risk context
        if arch.complexity_hotspots:
            lines.append("## Complexity Hotspots & Risk Areas")
            lines.append("")
            lines.append(
                "These functions have high complexity or connectivity. "
                "Changes require careful testing and impact assessment."
            )
            lines.append("")

            # Group by type for clarity
            hubs = [h for h in arch.complexity_hotspots if h.get("type") == "integration_hub"]
            coordinators = [h for h in arch.complexity_hotspots if h.get("type") == "coordinator"]

            if hubs:
                lines.append("### Integration Hubs (High Fan-In)")
                lines.append("Heavily called functions. Changes impact many dependents.")
                lines.append("")
                for i, hotspot in enumerate(hubs[:5], 1):
                    name = hotspot.get("name", "unknown")
                    fan_in = hotspot.get("fan_in", 0)
                    fan_out = hotspot.get("fan_out", 0)
                    risk = hotspot.get("risk_level", "low")
                    desc = hotspot.get("description", "")
                    lines.append(f"**{i}. {name}**")
                    lines.append(f"   Risk: {risk.upper()} | Callers: {fan_in} | Calls: {fan_out}")
                    if desc:
                        lines.append(f"   {desc}")
                    lines.append("")

            if coordinators:
                lines.append("### Coordinators (High Fan-Out)")
                lines.append("Complex orchestration logic. Refactoring candidates.")
                lines.append("")
                for i, hotspot in enumerate(coordinators[:5], 1):
                    name = hotspot.get("name", "unknown")
                    fan_in = hotspot.get("fan_in", 0)
                    fan_out = hotspot.get("fan_out", 0)
                    risk = hotspot.get("risk_level", "low")
                    desc = hotspot.get("description", "")
                    lines.append(f"**{i}. {name}**")
                    lines.append(f"   Risk: {risk.upper()} | Callers: {fan_in} | Calls: {fan_out}")
                    if desc:
                        lines.append(f"   {desc}")
                    lines.append("")

        # Health signals
        if arch.health_signals:
            lines.append("## Health & Quality Signals")
            lines.append("")
            for signal, value in arch.health_signals.items():
                if isinstance(value, float):
                    lines.append(
                        f"- **{signal}:** {value:.1%}"
                        if signal.lower().endswith("coverage")
                        else f"- **{signal}:** {value}"
                    )
                else:
                    lines.append(f"- **{signal}:** {value}")
            lines.append("")

        # Issues and strengths
        if arch.issues or arch.strengths:
            if arch.issues:
                lines.append("## Issues & Risks")
                lines.append("")
                for issue in arch.issues[:10]:
                    lines.append(f"- {issue}")
                lines.append("")

            if arch.strengths:
                lines.append("## Strengths")
                lines.append("")
                for strength in arch.strengths[:10]:
                    lines.append(f"- {strength}")
                lines.append("")

        return "\n".join(lines)

    def analyze_to_json(self) -> str:
        """
        Analyze architecture and produce JSON description.

        Returns a structured JSON representation of the architecture suitable
        for machine ingestion, tool integration, infographic generation,
        and programmatic processing. Includes full provenance and metadata.

        :return: JSON string describing the architecture.
        """
        arch = self._build_architecture_graph()

        # Build risk assessment summary
        risk_summary = {
            "total_hotspots": len(arch.complexity_hotspots),
            "high_risk_count": sum(
                1 for h in arch.complexity_hotspots if h.get("risk_level") == "high"
            ),
            "integration_hubs": sum(
                1 for h in arch.complexity_hotspots if h.get("type") == "integration_hub"
            ),
            "coordinators": sum(
                1 for h in arch.complexity_hotspots if h.get("type") == "coordinator"
            ),
        }

        data = {
            "metadata": {
                "generated_at": arch.generated_at,
                "version": arch.version,
                "commit": arch.commit,
                "title": arch.title,
            },
            "description": arch.description,
            "layers": [asdict(layer) for layer in arch.layers],
            "key_components": [asdict(comp) for comp in arch.key_components],
            "critical_paths": arch.critical_paths,
            "risk_assessment": risk_summary,
            "complexity_hotspots": arch.complexity_hotspots,
            "coupling": arch.coupling_summary,
            "health_signals": arch.health_signals,
            "issues": arch.issues,
            "strengths": arch.strengths,
        }

        return json.dumps(data, indent=2, default=str)

    def _build_architecture_graph(self) -> ArchitectureGraph:
        """
        Build internal architecture representation by analyzing the graph.

        Combines code-level analysis with thorough analysis results for
        rich, infographic-ready descriptions.

        :return: ArchitectureGraph with layers, components, paths, coupling.
        """
        # Detect layers from module hierarchy
        layers = self._detect_layers()

        # Find key components (high fan-in, central classes, entry points)
        key_components = self._identify_key_components()

        # Trace critical paths (important call chains)
        critical_paths = self._trace_critical_paths()

        # Analyze module coupling
        coupling = self._analyze_coupling()

        # Extract data from thorough analysis if available
        complexity_hotspots = self._extract_complexity_hotspots()
        health_signals = self._extract_health_signals()
        issues = self.thorough_analysis.get("issues", [])
        strengths = self.thorough_analysis.get("strengths", [])

        return ArchitectureGraph(
            title=self._infer_project_title(),
            description=self._generate_architecture_summary(layers),
            version=self.version,
            commit=self.commit,
            layers=layers,
            key_components=key_components,
            critical_paths=critical_paths,
            coupling_summary=coupling,
            complexity_hotspots=complexity_hotspots,
            health_signals=health_signals,
            issues=issues,
            strengths=strengths,
        )

    def _detect_layers(self) -> list[ModuleLayer]:
        """
        Detect logical layers from module organization.

        Common patterns:
        - cli/ → Command-line layer
        - api/ → API layer
        - core/ → Core business logic
        - store/ → Data persistence
        - models/ → Data models

        :return: List of detected layers.
        """
        # Get all modules from graph
        all_nodes = self.store.query_nodes(kinds=["module"])
        modules = [n["module_path"] for n in all_nodes if n.get("module_path")]

        layers = []
        layer_map: dict[str, list[str]] = {}

        # Organize by prefix path
        for mod in sorted(modules):
            parts = mod.split("/")
            if len(parts) > 1:
                layer_name = parts[0]
                if layer_name not in layer_map:
                    layer_map[layer_name] = []
                layer_map[layer_name].append(mod)

        # Create layer definitions based on detected structure
        layer_descriptions = {
            "cli": (
                "Command-line Interface",
                ["Parse and handle CLI commands", "Route to subcommands"],
            ),
            "api": ("API Layer", ["Expose REST/RPC endpoints", "Handle request/response"]),
            "core": (
                "Core Business Logic",
                ["Implement core functionality", "Orchestrate workflows"],
            ),
            "store": ("Data Storage & Persistence", ["Manage graph data", "Query knowledge graph"]),
            "index": (
                "Semantic Search & Indexing",
                ["Embed and index vectors", "Semantic similarity search"],
            ),
            "models": ("Data Models", ["Define core entities", "Provide type definitions"]),
            "graph": ("Graph Construction", ["Extract code structure", "Build AST-based graph"]),
            "visitor": ("AST Visitor & Analysis", ["Traverse AST", "Track scopes and symbols"]),
        }

        for layer_name, modules_list in sorted(layer_map.items()):
            desc, resps = layer_descriptions.get(
                layer_name, (f"{layer_name.capitalize()} Layer", ["Component responsibility"])
            )
            layers.append(
                ModuleLayer(
                    name=desc,
                    description=f"Handles {layer_name} concerns.",
                    modules=modules_list,
                    responsibilities=resps,
                )
            )

        return layers

    def _identify_key_components(self) -> list[ComponentNode]:
        """
        Identify key architectural components (high fan-in, central classes).

        :return: List of important components.
        """
        components = []

        # Get classes from the graph
        classes = self.store.query_nodes(kinds=["class"])

        for cls_node in classes[:5]:  # Top 5 classes
            node_id = cls_node["id"]
            docstring = cls_node.get("docstring", "Core component")
            desc = docstring.split("\n")[0] if docstring else "Core component"

            components.append(
                ComponentNode(
                    node_id=node_id,
                    name=cls_node["name"],
                    kind="class",
                    description=desc,
                    file=cls_node.get("module_path", "unknown"),
                    lineno=cls_node.get("lineno", 0),
                )
            )

        return components

    def _trace_critical_paths(self) -> list[dict]:
        """
        Identify critical execution paths (important call chains).

        :return: List of critical paths with descriptions.
        """
        return [
            {
                "name": "Graph Query Pipeline",
                "description": "Semantic search → graph expansion → snippet packing",
                "steps": [
                    "Semantic search finds seed nodes via LanceDB",
                    "Graph expansion traverses CALLS, CONTAINS, IMPORTS edges",
                    "Snippet pack materializes source code with context",
                ],
            },
            {
                "name": "AST Extraction & Graph Building",
                "description": "Repository scanning → code analysis → graph storage",
                "steps": [
                    "CodeGraph walks repo and extracts Python files",
                    "PyCodeKGVisitor traverses AST, collects nodes and edges",
                    "GraphStore persists in SQLite with symbol resolution",
                ],
            },
        ]

    def _analyze_coupling(self) -> dict[str, Any]:
        """
        Analyze module dependencies and coupling strength.

        :return: Dict with dependency analysis.
        """
        # Query IMPORTS edges from the graph store directly
        # We'll use the internal SQLite connection
        rows = self.store.con.execute(
            "SELECT src, dst FROM edges WHERE rel = 'IMPORTS' LIMIT 100"
        ).fetchall()

        dependencies: dict[str, list[str]] = {}
        for src, dst in rows:
            if src and dst:
                src_mod = src.split(":")[1] if ":" in src else src
                dst_mod = dst.split(":")[1] if ":" in dst else dst
                if src_mod not in dependencies:
                    dependencies[src_mod] = []
                if dst_mod not in dependencies[src_mod]:
                    dependencies[src_mod].append(dst_mod)

        return {
            "dependencies": dependencies,
            "total_import_edges": len(rows),
            "summary": "Module dependencies tracked via IMPORTS edges in knowledge graph",
        }

    def _extract_complexity_hotspots(self) -> list[dict]:
        """Extract top complexity hotspots from thorough analysis with risk context."""
        hotspots = []

        # High fan-in functions (heavily called = change impact risk)
        high_fanin = self.thorough_analysis.get("high_fan_in_functions", [])
        for func in high_fanin[:10]:
            fan_in = func.get("fan_in", 0)
            fan_out = func.get("fan_out", 0)
            risk = func.get("risk_level", "low")
            hotspots.append(
                {
                    "name": func.get("name", "unknown"),
                    "fan_in": fan_in,
                    "fan_out": fan_out,
                    "risk_level": risk,
                    "type": "integration_hub",
                    "description": (
                        f"Called by {fan_in} other functions. Changes propagate broadly. "
                        f"Requires careful testing and backward compatibility."
                    ),
                    "impact": "high" if fan_in > 15 else "medium",
                }
            )

        # High fan-out functions (many calls = coordination burden)
        high_fanout = self.thorough_analysis.get("high_fan_out_functions", [])
        for func in high_fanout[:10]:
            fan_in = func.get("fan_in", 0)
            fan_out = func.get("fan_out", 0)
            risk = func.get("risk_level", "low")
            hotspots.append(
                {
                    "name": func.get("name", "unknown"),
                    "fan_in": fan_in,
                    "fan_out": fan_out,
                    "risk_level": risk,
                    "type": "coordinator",
                    "description": (
                        f"Calls {fan_out} other functions. Complex orchestration logic. "
                        f"Refactoring candidate: consider breaking into smaller steps."
                    ),
                    "impact": "high" if fan_out > 20 else "medium",
                }
            )

        # Sort by impact and risk, return top hotspots
        return sorted(
            hotspots, key=lambda h: (h.get("risk_level") == "high", h.get("impact") == "high")
        )[:15]

    def _extract_health_signals(self) -> dict[str, Any]:
        """Extract comprehensive health and quality signals from thorough analysis."""
        signals: dict[str, Any] = {}

        # Docstring coverage (primary quality metric)
        coverage = self.thorough_analysis.get("docstring_coverage", {})
        if coverage:
            total_cov = coverage.get("total", 0.0)
            signals["Docstring Coverage"] = total_cov
            # Add color/severity
            if total_cov < 0.6:
                signals["Documentation Status"] = "Below Target"
            elif total_cov < 0.85:
                signals["Documentation Status"] = "Good Progress"
            else:
                signals["Documentation Status"] = "Well Documented"

        # Circular dependencies (structural health)
        circular = self.thorough_analysis.get("circular_dependencies", [])
        circular_count = len(circular)
        signals["Circular Dependencies"] = circular_count
        if circular_count > 0:
            signals["Coupling Health"] = "Has cycles"
        else:
            signals["Coupling Health"] = "Acyclic"

        # Orphaned functions (dead code)
        orphaned = self.thorough_analysis.get("orphaned_functions", [])
        orphaned_count = len(orphaned)
        signals["Orphaned Functions"] = orphaned_count
        if orphaned_count > 5:
            signals["Dead Code Status"] = "Cleanup needed"
        elif orphaned_count > 0:
            signals["Dead Code Status"] = "Minor cleanup"
        else:
            signals["Dead Code Status"] = "Clean"

        # High-level counts if available
        stats = self.thorough_analysis.get("statistics", {})
        if stats:
            total_funcs = stats.get("total_functions", 0)
            if total_funcs > 0:
                signals["Function Count"] = total_funcs

        return signals

    def _infer_project_title(self) -> str:
        """Infer project title from repo structure."""
        readme = self.repo_root / "README.md"
        if readme.exists():
            try:
                with open(readme) as f:
                    for line in f:
                        if line.startswith("#"):
                            return line.lstrip("#").strip()
            except OSError:
                pass
        return "PyCodeKG Architecture"

    def _generate_architecture_summary(self, layers: list[ModuleLayer]) -> str:
        """Generate high-level architecture summary."""
        layer_names = [layer.name for layer in layers]
        return (
            f"This codebase is organized into {len(layers)} architectural layers: "
            f"{', '.join(layer_names)}. "
            f"The architecture supports semantic code search via knowledge graph indexing and querying."
        )
