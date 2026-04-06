# CodeKG Thorough Analysis

**Comprehensive Codebase Health & Complexity Assessment**

Analyze your Python codebase for complexity hotspots, code quality metrics, architectural issues, and health signals. Produces detailed reports suitable for decision-making and team communication.

---

## Overview

The `codekg analyze` command performs deep structural and semantic analysis of your codebase:

**Markdown Report** — Human-readable summary for team communication
- Complexity hotspots (high fan-in/fan-out functions)
- Docstring coverage and documentation status
- Circular dependencies and coupling issues
- Orphaned (dead code) functions
- Known architectural issues
- Identified strengths

**JSON Snapshot** — Structured data for tool integration and tracking over time
- All metrics in machine-readable format
- Complexity metrics with risk levels
- Full function/class inventories
- Coverage percentages
- Suitable for CI/CD gates and metrics tracking
- Timestamped for temporal analysis

---

## Quick Start

### 1. Build the Knowledge Graph
```bash
codekg build
```

### 2. Run Thorough Analysis
```bash
codekg analyze --json ~/.claude/codekg_analysis_latest.json
```

### 3. View the Results
```bash
cat code_kg_analysis_*.md
```

---

## Command Reference

```bash
codekg analyze [OPTIONS] [REPO_ROOT]
```

### Options

| Option | Description |
|--------|-------------|
| `--db PATH` | SQLite knowledge graph path (default: `<repo>/.codekg/graph.sqlite`) |
| `--lancedb PATH` | LanceDB vector index path (default: `<repo>/.codekg/lancedb`) |
| `--output FILE` | Markdown report output path (default: `<repo>_analysis_<YYYYMMDD>.md`) |
| `--json FILE` | JSON snapshot output path (default: `~/.claude/codekg_analysis_latest.json`) |
| `--quiet` | Suppress the Rich console summary table |
| `--exclude-dir DIR` | Exclude directory from analysis (can be repeated) |

---

## What Gets Analyzed

### Complexity Hotspots

**High Fan-In Functions** (heavily called)
- Core functions that many other functions depend on
- Changes have broad impact
- Critical for stability
- Risk: Breaking changes affect many dependents

**High Fan-Out Functions** (many calls)
- Orchestration functions that call many others
- Complex coordination logic
- Testing burden
- Risk: Hard to understand and maintain

Example output:
```json
{
  "high_fanout_functions": [
    {
      "name": "process_pipeline",
      "fan_in": 3,
      "fan_out": 18,
      "risk_level": "high"
    }
  ]
}
```

### Docstring Coverage

Measures documentation completeness:
```json
{
  "docstring_coverage": {
    "total": 0.975,
    "by_kind": {
      "function": 0.92,
      "class": 0.98,
      "method": 0.97,
      "module": 1.0
    }
  }
}
```

- **Excellent:** >90%
- **Good:** 70-90%
- **Fair:** 50-70%
- **Poor:** <50%

### Circular Dependencies

Identifies import cycles that can cause issues:
```json
{
  "circular_dependencies": [
    {
      "modules": ["store.py", "graph.py", "index.py"],
      "cycle": "store → graph → index → store"
    }
  ]
}
```

**Impact:** Can cause:
- Import-time side effects
- Hard-to-debug failures
- Module ordering dependencies
- Refactoring difficulty

### Orphaned Functions

Functions with no callers (dead code):
```json
{
  "orphaned_functions": [
    {
      "name": "legacy_format_handler",
      "module": "src/utils.py",
      "lines": 42,
      "risk_level": "medium"
    }
  ]
}
```

**Note:** Some false positives are normal:
- Entry points (`cli`, `main`)
- Protocol methods (`__enter__`, `__repr__`)
- Indirect callers (via string names, reflection)

### Module Coupling

Analyzes interdependencies:
```json
{
  "module_coupling": {
    "dependencies": {
      "store": ["graph", "codekg"],
      "graph": ["codekg"],
      "visitor": []
    },
    "import_edges": 47,
    "highly_coupled": [
      {"from": "store", "to": "graph", "strength": 0.89}
    ]
  }
}
```

### Issues & Strengths

High-level assessment:
```json
{
  "issues": [
    "High fan-out in pipeline orchestrator (18 calls)",
    "2 circular import cycles detected",
    "Docstring coverage below 80% in utils module"
  ],
  "strengths": [
    "Well-structured layering (CLI → Store → Graph)",
    "No god objects (max fan-in: 12)",
    "Good separation of concerns"
  ]
}
```

---

## Output Example

### Markdown Report Section

```markdown
## Complexity & Architecture Health

### High Fan-Out Functions (Orchestrators)
These functions coordinate many other functions. Candidates for refactoring.

1. **build_graph** (Fan-in: 2, Fan-out: 14)
   - Complex coordination logic
   - Calls: extract_nodes, build_edges, index_semantics, ...
   - Risk: HIGH

### Docstring Coverage: 97.5%
✅ Well documented. Excellent for onboarding.

- Modules: 100% (15/15)
- Classes: 98% (32/33)
- Functions: 96% (152/159)
- Methods: 97% (203/209)

### Issues Identified
- ⚠️ 2 circular import cycles in graph building
- ⚠️ 1 orphaned function (legacy_handler)

### Strengths
- ✓ No god objects detected
- ✓ Clear layering across modules
- ✓ Consistent error handling patterns
```

---

## Workflows

### Generate & Use Analysis

```bash
# Run analysis
codekg analyze --quiet --json ~/.claude/codekg_analysis_latest.json

# View report
cat code_kg_analysis_*.md

# Use JSON for tooling
jq '.docstring_coverage.total' ~/.claude/codekg_analysis_latest.json
```

### CI/CD Integration

```bash
# Fail if coverage drops below threshold
COVERAGE=$(jq '.docstring_coverage.total' analysis.json)
if (( $(echo "$COVERAGE < 0.85" | bc -l) )); then
  echo "Documentation coverage below 85%"
  exit 1
fi

# Alert on new high-risk hotspots
jq '.high_fanout_functions[] | select(.risk_level == "high")' analysis.json
```

### Combine with Architecture

For the richest insights:

```bash
# 1. Run thorough analysis
codekg analyze --quiet --json ~/.claude/codekg_analysis_latest.json

# 2. Generate architecture WITH analysis insights
codekg architecture --load-latest \
  --markdown docs/architecture.md \
  --json assets/arch.json
```

The architecture description will include:
- Complexity hotspots in architectural context
- Health signals (docstring coverage, cycles, orphaned code)
- Issues and strengths identified by analysis

---

## Best Practices

1. **Run regularly** — After major refactoring, at releases, during design reviews
2. **Track over time** — Use snapshots to monitor trends in complexity and coverage
3. **Share reports** — Team communication: "We're above 95% documentation"
4. **Set thresholds** — Define minimum acceptable coverage (80-90% is common)
5. **Act on hotspots** — Use for refactoring prioritization
6. **Verify fixes** — Re-run after major changes to confirm improvements

---

## Interpreting Results

### Docstring Coverage

| Coverage | Interpretation | Action |
|----------|----------------|--------|
| >95% | Excellent | Maintain standards |
| 85-95% | Good | Review gaps, target improvements |
| 70-85% | Fair | Schedule documentation sprints |
| <70% | Poor | High onboarding friction, priority work |

### Fan-Out Risk

| Fan-Out | Risk | Recommendation |
|---------|------|-----------------|
| <5 | Low | Normal, no action |
| 5-12 | Medium | Monitor, consider refactoring |
| 12-20 | High | Plan refactoring |
| >20 | Critical | Immediate refactoring needed |

### Circular Dependencies

| Count | Action |
|-------|--------|
| 0 | Perfect |
| 1-2 | Low risk, document carefully |
| >2 | Plan refactoring cycles |

---

## API Usage

### Python Integration

```python
from code_kg.codekg_thorough_analysis import CodeKGAnalyzer
from code_kg.store import GraphStore
from pathlib import Path
import json

store = GraphStore(Path(".codekg/graph.sqlite"))
analyzer = CodeKGAnalyzer(store, repo_root=Path("."))

# Run analysis
results = analyzer.run_analysis()

# Access metrics
coverage = results['docstring_coverage']['total']
hotspots = results['high_fanout_functions']
issues = results['issues']

# Save for later use
with open("analysis.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

## FAQ

**Q: How often should I analyze?**
A: After major refactoring, at release milestones, and monthly during normal development.

**Q: What's a good docstring coverage target?**
A: 85% is a good baseline; 90%+ is excellent. Use snapshots to track trends.

**Q: Are orphaned functions always dead code?**
A: No, there are false positives: entry points, protocol methods, indirect calls. Review before deleting.

**Q: How do I fix high fan-out functions?**
A: Break into smaller helpers, extract decision logic, use composition. Reduce coordination burden.

**Q: What about circular dependencies?**
A: Usually fixable by moving shared code to a new module or restructuring imports. Plan refactoring.

---

## See Also

- [Architecture_usage.md](Architecture_usage.md) — Generate coherent architecture descriptions
- [SNAPSHOTS.md](SNAPSHOTS.md) — Track metrics over time
- [README.md](../README.md) — Project overview
