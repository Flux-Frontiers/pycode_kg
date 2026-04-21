# PyCodeKG Agent Assessment Protocol

**Author:** Eric G. Suchanek, PhD <suchanek@mac.com>
**Repository:** https://github.com/Flux-Frontiers/pycode_kg.git
**Testing Platform: 2024 M3 Max, Macbook Pro, 36GB RAM, 1TB SSD**

---

## Background

PyCodeKG is a tool that indexes Python codebases into a hybrid semantic + structural knowledge graph and exposes it to AI agents via MCP (Model Context Protocol). It evolved from [repo_viz](https://github.com/suchanek/repo_viz.git), an AST-based repository visualization system using PyVista into a semantically-accessible knowledge graph with precise, structurally-grounded data.

You have access to PyCodeKG's MCP tools in this session. Your task is to **evaluate the tool itself** — not the repository it happens to be indexing.

---

## Your Assignment

Perform a thorough, hands-on assessment of PyCodeKG's functional utility for understanding Python codebases **from your perspective as an AI agent**. Exercise every available tool, document what you find, and deliver a structured written assessment. Assess overall speed if possible.

---

## Phase 1: Orientation

1. Call `graph_stats()` to understand the shape and scale of the indexed codebase.
2. Call `analyze_repo()` to get the full architectural analysis.
3. Review the output: Are the metrics meaningful? Is the breakdown useful for orienting yourself?

## Phase 2: Semantic Search

Test the hybrid search capabilities with varied queries:

1. **Precise query** — Search for a specific known concept (e.g., "graph database storage", "MCP server endpoint").
2. **Broad query** — Search for a high-level architectural concern (e.g., "error handling strategy", "data flow").
3. **Exploratory query** — Search for something you'd want to know in a new codebase (e.g., "entry points", "configuration").

For each query, use both `query_codebase()` and `pack_snippets()`. Compare the results:
- Are the returned nodes relevant to your query?
- Does `pack_snippets` provide sufficient context to understand the code?
- How does semantic search compare to your default approach (grep/file reading)?

## Phase 3: Structural Navigation

1. Pick 2-3 interesting nodes from Phase 2 results.
2. Use `get_node(node_id, include_edges=True)` to inspect each one.
3. Use `explain(node_id)` on at least 2 nodes.
4. Use `callers(node_id)` on at least 1 function to trace its usage.
5. Assess: Does the graph structure (CALLS, IMPORTS, CONTAINS, INHERITS edges) accurately represent the codebase relationships?

## Phase 4: Temporal Analysis (if snapshots exist)

1. Call `snapshot_list()` to check for available snapshots.
2. If snapshots exist, use `snapshot_show()` and `snapshot_diff()` to examine codebase evolution.
3. Assess: Is the temporal dimension useful? What insights does it provide?

---

## Evaluation Criteria

Score each dimension from 1 (poor) to 5 (excellent) with brief justification:

| Dimension | What to Assess |
|-----------|----------------|
| **Accuracy** | Do nodes, edges, and relationships correctly reflect the actual code? |
| **Relevance** | Does semantic search return results that match your intent? |
| **Completeness** | Is the graph comprehensive? Are important elements missing? |
| **Efficiency** | Is this faster/better than your default workflow (grep, file reading, AST parsing)? |
| **Insight Generation** | Did you learn something about the codebase you wouldn't have found otherwise? |
| **Usability** | Are the tool interfaces intuitive? Is the output well-structured? |
| **Architectural Value** | Does `analyze_repo` surface genuinely useful architectural insights? |
| **Uniqueness** | How does this compare to other codebase analysis approaches you've encountered? |

---

## Output Requirements

Write your assessment as a markdown file saved to:

```
./assessments/PyCodeKG_assessment_<model_name>_<datestamp>.md
```

Where `<model_name>` is your model identifier (e.g., `claude_opus_4`, `gpt_4o`, `gemini_2_pro`) and `<datestamp>` is `YYYY-MM-DD` format.

### Required Sections

1. **Executive Summary** — 2-3 paragraph overall assessment
2. **Tool-by-Tool Evaluation** — Rate and discuss each MCP tool you exercised
3. **Scorecard** — The evaluation criteria table with your scores and justifications
4. **Comparison to Default Workflow** — How does PyCodeKG change your approach vs. raw file access?
5. **Strengths** — What PyCodeKG does well
6. **Weaknesses & Suggestions** — What could be improved, with specific recommendations
7. **Overall Verdict** — Would you recommend PyCodeKG? For what use cases? Final rating out of 5.

---

## Important Notes

- **Assess the tool, not the repo.** Your target codebase may be PyCodeKG itself or another Python project. Either way, focus on how well the *tools* help you understand the code.
- **Be honest and specific.** Vague praise is not useful. Cite concrete examples of where a tool helped or fell short.
- **Compare to your baseline.** Without PyCodeKG, you would use file reading, grep, and manual navigation. Explicitly compare the two approaches.
- **Exercise every tool.** Don't skip tools — even if you think they overlap, each has different strengths worth evaluating.
