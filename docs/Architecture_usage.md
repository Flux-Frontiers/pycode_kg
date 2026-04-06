# PyCodeKG Architecture Analysis

**Coherent Descriptions of Your Codebase Structure**

Generate comprehensive, machine-readable architectural documentation from your code graph. Understand layers, components, dependencies, complexity hotspots, and health signals — enriched with insights from thorough codebase analysis.

---

## Overview

The `pycodekg architecture` command produces two complementary outputs:

**Markdown** — Human-readable documentation for wikis, READMEs, and presentations
- Architectural layers with responsibilities
- Key components and their roles
- Critical execution paths
- Module dependencies and coupling analysis
- Complexity hotspots with risk context and refactoring guidance
- Health metrics with status indicators (✅/⚠️/📋)
- Known issues and architectural strengths

**JSON** — Structured data for tooling and infographic generation
- Full metadata (timestamp, version, commit hash)
- Layered architecture graph
- Component inventory with line numbers and docstring status
- Risk assessment summary (high-risk count, integration hubs, coordinators)
- Hotspot analysis with descriptions and impact ratings
- Health signals and issue tracking
- Ready for parsing by visualization tools and infographic generators

---

## Quick Start

### 1. Build the Knowledge Graph
```bash
pycodekg build
```

### 2. Generate Thorough Analysis (Optional but Recommended)
```bash
pycodekg analyze --json ~/.claude/pycodekg_analysis_latest.json
```

This produces complexity metrics, docstring coverage, and identifies architectural issues.

### 3. Generate Architecture Description

**With thorough analysis insights** (richest output):
```bash
pycodekg architecture --load-latest --markdown docs/architecture.md --json arch.json
```

**Without analysis** (still includes layers and components):
```bash
pycodekg architecture --markdown docs/architecture.md --json arch.json
```

**Explicit analysis path**:
```bash
pycodekg architecture --analysis ~/my-analysis.json --markdown docs/architecture.md
```

**Print to console**:
```bash
pycodekg architecture --load-latest
```

---

## Command Reference

```bash
pycodekg architecture [OPTIONS] [REPO_ROOT]
```

### Options

| Option | Description |
|--------|-------------|
| `--db PATH` | SQLite knowledge graph path (default: `<repo>/.pycodekg/graph.sqlite`) |
| `--markdown PATH` | Save Markdown description |
| `--json PATH` | Save JSON description (infographic-ready) |
| `--analysis PATH` | Incorporate thorough analysis from file |
| `--load-latest` | Auto-load latest analysis from `~/.claude/pycodekg_analysis_latest.json` |

---

## Workflow: Thorough Analysis + Architecture

For the richest architectural insights, combine `pycodekg analyze` with `pycodekg architecture`:

```bash
# Step 1: Run thorough analysis (creates complexity metrics, hotspots, coverage)
pycodekg analyze --quiet --json ~/.claude/pycodekg_analysis_latest.json

# Step 2: Generate enriched architecture
pycodekg architecture --load-latest \
  --markdown docs/architecture.md \
  --json assets/pycodekg_architecture.json

# Step 3: Use outputs
# - Markdown for documentation
# - JSON for infographic tools
# - Reference in README or wiki
```

---

## What Gets Analyzed

### Architectural Layers

Layers are detected automatically from your module structure:

```
src/pycode_kg/
├── cli/           → Command-line Interface layer
├── store/         → Data Persistence layer
├── index/         → Semantic Search layer
├── graph/         → Graph Construction layer
└── visitor/       → AST Analysis layer
```

For each layer:
- **Name** — Human-readable description
- **Modules** — Files in this layer
- **Responsibilities** — What it does
- **Dependencies** — Imports and internal coupling

### Key Components

Identifies important classes and their roles:
- Type and location with line numbers
- Docstring status
- Architectural significance

### Critical Paths

Documents important workflows:
- Query pipeline (semantic search → expansion → snippet extraction)
- Build pipeline (AST extraction → storage → indexing)
- Data flow through the system

### Module Coupling

Analyzes dependencies between modules:
- What each module imports
- Coupling strength
- Identifies circular dependencies
- Shows import chains

### Complexity Hotspots (When Analysis Included)

When you use `--load-latest` or `--analysis`, shows architecturally significant functions:

**Integration Hubs** (high fan-in)
- Called by many other functions
- Changes propagate broadly
- High impact on stability
- Risk: Breaking changes affect many dependents

**Coordinators** (high fan-out)
- Call many other functions
- Complex orchestration logic
- Refactoring candidates
- Risk: Hard to test, hard to maintain

Each hotspot includes:
- Fan-in/fan-out counts
- Risk level (low/medium/high)
- Actionable description ("Requires careful testing", "Consider breaking into smaller steps")

### Health Signals (When Analysis Included)

Status indicators for code quality:

| Signal | Meaning |
|--------|---------|
| **Documentation Status** | ✅ Well Documented (>85%), 📋 Good Progress (60-85%), ⚠️ Below Target (<60%) |
| **Coupling Health** | ✅ Acyclic, ⚠️ Has cycles |
| **Dead Code Status** | ✅ Clean, 📦 Minor cleanup, ⚠️ Cleanup needed |

Plus metrics:
- Docstring coverage percentage
- Circular dependency count
- Orphaned function count

### Issues & Strengths (When Analysis Included)

From thorough analysis:
- **Issues** — Known risks, code smells, architectural concerns
- **Strengths** — Well-architected areas, best practices observed

---

## Output Examples

### Markdown Section: Complexity Hotspots

```markdown
## 🔥 Complexity Hotspots & Risk Areas

These functions have high complexity or connectivity. Changes require careful testing and impact assessment.

### Integration Hubs (High Fan-In)
Heavily called functions. Changes impact many dependents.

**1. query_and_expand**
   Risk: HIGH | Callers: 12 | Calls: 8
   Called by 12 other functions. Changes propagate broadly. Requires careful testing and backward compatibility.
```

### JSON Structure: Risk Assessment

```json
{
  "risk_assessment": {
    "total_hotspots": 3,
    "high_risk_count": 1,
    "integration_hubs": 2,
    "coordinators": 1
  },
  "complexity_hotspots": [
    {
      "name": "query_and_expand",
      "fan_in": 12,
      "fan_out": 8,
      "risk_level": "high",
      "type": "integration_hub",
      "description": "Called by 12 other functions...",
      "impact": "high"
    }
  ]
}
```

---

## Best Practices

1. **Generate at milestones** — After refactoring, at releases, during onboarding
2. **Use thorough analysis** — Always run `pycodekg analyze` first for rich insights
3. **Version with code** — Commit architecture description alongside changes
4. **Use for communication** — Share Markdown with team, include in docs
5. **Automate** — Add to CI pipeline, generate before releases
6. **Monitor trends** — Track hotspots and health signals over time using snapshots
7. **Integrate outputs** — Use JSON for infographic tools and visualization

---

## API Usage

### Python Integration

```python
from pycode_kg.architecture import ArchitectureAnalyzer
from pycode_kg.store import GraphStore
from pathlib import Path
import json

store = GraphStore(Path(".pycodekg/graph.sqlite"))
analyzer = ArchitectureAnalyzer(
    store,
    repo_root=Path("."),
    version="0.5.1",
    commit="c2e58fc"
)

# Optionally incorporate thorough analysis
with open("analysis.json") as f:
    analysis = json.load(f)
analyzer.incorporate_thorough_analysis(analysis)

# Generate outputs
md = analyzer.analyze_to_markdown()
json_str = analyzer.analyze_to_json()

# Save or use
with open("architecture.md", "w") as f:
    f.write(md)
```

---

## FAQ

**Q: Do I need thorough analysis to use architecture?**
A: No. `pycodekg architecture` works standalone. But with `--load-latest` or `--analysis`, you get richer insights: complexity hotspots, health signals, and issue tracking.

**Q: Where does the layer detection come from?**
A: Automatically detected from your module directory structure (e.g., `src/cli/` → CLI Layer).

**Q: Can I customize layer names?**
A: Currently auto-detected. Customization coming in future versions.

**Q: How often should I regenerate?**
A: After major refactoring, at release milestones, or when onboarding team members.

**Q: Can I use the JSON in infographics?**
A: Yes! It includes all necessary metadata, risk assessment, and structured data.

---

## See Also

- [SNAPSHOTS.md](SNAPSHOTS.md) — Track architectural metrics over time
- [Analyze.md](Analyze.md) — Thorough codebase analysis
- [README.md](../README.md) — Project overview
