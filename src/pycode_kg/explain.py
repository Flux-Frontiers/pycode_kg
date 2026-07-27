"""
Markdown rendering of node explanations for PyCodeKG.

Single source of truth for the ``explain`` output used by both:

- the CLI ``pycodekg explain`` command, and
- the MCP ``explain`` tool.

Centralizing the rendering here ensures the two surfaces never drift in
their role-labeling, formatting, threshold semantics, or markdown
structure — which previously caused divergent output (different
thresholds, different "Utility function" vs kind-aware labels).
"""

from __future__ import annotations

from typing import Any


def render_explain(
    kg: Any,
    node_id: str,
    *,
    limit: int = 10,
    snippets_hint: str = "pack_snippets()",
) -> str:
    """
    Render a Markdown natural-language explanation of a code node.

    :param kg: A :class:`PyCodeKG`-like object exposing ``node()``,
               ``callers()``, ``stats()``, and ``_store.edges_from()``.
    :param node_id: Stable node identifier
                    (e.g. ``fn:src/pycode_kg/store.py:GraphStore.expand``).
    :param limit: Maximum callers and callees to list.  Pass 0 to list all.
    :param snippets_hint: Closing call-to-action shown to the consumer for
                          retrieving the full source — ``"pack_snippets()"``
                          for MCP, ``"pycodekg pack"`` for CLI.
    :return: Markdown string, or a "Node Not Found" header when the ID does
             not exist in the knowledge graph.
    """
    node = kg.node(node_id)
    if node is None:
        return f"# Node Not Found\n\nNode ID `{node_id}` does not exist in the knowledge graph."

    out: list[str] = []

    kind = node.get("kind", "unknown")
    name = node.get("qualname") or node.get("name", "unknown")
    out.append(f"# {kind.capitalize()}: `{name}`\n")

    out.append("## Metadata\n")
    if node.get("module_path"):
        out.append(f"- **Module**: `{node['module_path']}`")
    if node.get("lineno") is not None:
        out.append(
            f"- **Location**: line {node['lineno']}"
            + (f"–{node['end_lineno']}" if node.get("end_lineno") else "")
        )
    out.append(f"- **ID**: `{node_id}`")
    out.append("")

    docstring = (node.get("docstring") or "").strip()
    if docstring:
        out.append("## Documentation\n")
        out.append(docstring)
        out.append("")

    _append_callers(out, kg, node_id, kind, limit)
    _append_callees(out, kg, node_id, kind, limit)

    out.append("## Role in Codebase\n")
    out.append(_role_label(kg, node_id, node))

    out.append("")
    out.append("---\n")
    out.append(f"*Use `{snippets_hint}` to retrieve the full source code.*")

    return "\n".join(out)


def _append_callers(out: list[str], kg: Any, node_id: str, kind: str, limit: int) -> None:
    try:
        caller_list = kg.callers(node_id, rel="CALLS")
    except (AttributeError, ValueError, RuntimeError):
        return
    if not caller_list:
        return
    out.append("## Called By (Callers)\n")
    out.append(f"This {kind} is called by **{len(caller_list)}** other function(s):\n")
    shown = caller_list[:limit] if limit > 0 else caller_list
    for caller in shown:
        cn = caller.get("qualname") or caller.get("name", "unknown")
        cm = caller.get("module_path", "")
        out.append(f"- `{cn}` ({cm})")
    if limit > 0 and len(caller_list) > limit:
        out.append(f"- ... and {len(caller_list) - limit} more")
    out.append("")


def _append_callees(out: list[str], kg: Any, node_id: str, kind: str, limit: int) -> None:
    try:
        edges = kg.store.edges_from(node_id, rel="CALLS", limit=50)
    except (AttributeError, ValueError, RuntimeError):
        return
    if not edges:
        return
    callees: set[str] = set()
    for edge in edges:
        dst = edge.get("dst")
        if dst is None:
            continue
        dst_node = kg.node(dst)
        # Filter out symbol stubs and externals (no module_path → builtin/stdlib).
        if dst_node and dst_node.get("kind") != "symbol" and dst_node.get("module_path"):
            dn = dst_node.get("qualname") or dst_node.get("name", "unknown")
            callees.add(f"- `{dn}`")
    if not callees:
        return
    out.append("## Calls (Callees)\n")
    out.append(f"This {kind} calls **{len(callees)}** other function(s):\n")
    sorted_c = sorted(callees)
    shown = sorted_c[:limit] if limit > 0 else sorted_c
    for callee in shown:
        out.append(callee)
    if limit > 0 and len(callees) > limit:
        out.append(f"- ... and {len(callees) - limit} more")
    out.append("")


def _role_label(kg: Any, node_id: str, node: dict) -> str:
    """Build the kind-aware role label used in ``## Role in Codebase``.

    Uses caller-count thresholds relative to the codebase size (top 5% / top
    2%), an orchestrator branch for high-fan-out coordination hubs, and
    kind-aware nouns/verbs so a class is described as "Constructed" rather
    than as a "Utility function".
    """
    try:
        caller_count = len(kg.callers(node_id, rel="CALLS"))

        callee_count = _count_internal_callees(kg, node_id)

        try:
            meaningful_nodes = kg.stats().get("meaningful_nodes", 100)
        except (AttributeError, ValueError, RuntimeError):
            meaningful_nodes = 100

        thresh_high = max(15, int(meaningful_nodes * 0.05))
        thresh_imp = max(5, int(meaningful_nodes * 0.02))
        thresh_orch = 8

        node_kind = node.get("kind", "")
        if node_kind == "class":
            kind_noun, verb_past = "class", "Constructed"
        elif node_kind == "module":
            kind_noun, verb_past = "module", "Imported"
        else:
            kind_noun, verb_past = "function", "Called"

        if caller_count >= thresh_high:
            return (
                f"**High-value {kind_noun}**: {verb_past} {caller_count} times "
                f"(≥{thresh_high} = top 5% of this codebase). "
                "This is likely a core API or bottleneck. "
                "Changes here may have wide impact."
            )
        if caller_count >= thresh_imp:
            return (
                f"**Important {kind_noun}**: {verb_past} {caller_count} times "
                f"(≥{thresh_imp} = top 2% of this codebase). "
                "Part of the essential infrastructure."
            )
        if callee_count >= thresh_orch and caller_count > 0:
            return (
                f"**Core orchestrator**: Called {caller_count} time(s), "
                f"calls {callee_count} others. "
                "Low caller count likely reflects a top-level entry point — "
                "the high fan-out indicates a coordination hub, not a utility."
            )
        if caller_count > 0:
            mod_summary = _caller_module_summary(kg, node_id)
            utility_noun = "Supporting" if node_kind == "class" else "Utility"
            return (
                f"**{utility_noun} {kind_noun}**: {verb_past} {caller_count} time(s) "
                f"from {mod_summary}."
            )

        return _zero_caller_label(node)
    except (AttributeError, ValueError, RuntimeError):
        return "Unable to determine call graph role."


def _count_internal_callees(kg: Any, node_id: str) -> int:
    try:
        edges = kg.store.edges_from(node_id, rel="CALLS", limit=100)
    except (AttributeError, ValueError, RuntimeError):
        return 0
    count = 0
    for e in edges or []:
        dst = e.get("dst") or ""
        if dst.startswith("sym:"):
            continue
        dst_node = kg.node(dst)
        if dst_node and dst_node.get("module_path"):
            count += 1
    return count


def _caller_module_summary(kg: Any, node_id: str) -> str:
    try:
        callers_for_role = kg.callers(node_id, rel="CALLS")
    except (AttributeError, ValueError, RuntimeError):
        return "various callers"
    caller_mods = sorted(
        {
            c.get("module_path", "").split("/")[-1].replace(".py", "")
            for c in callers_for_role
            if c.get("module_path")
        }
    )
    if not caller_mods:
        return "various callers"
    summary = ", ".join(f"`{m}`" for m in caller_mods[:4])
    if len(caller_mods) > 4:
        summary += " and more"
    return summary


def _zero_caller_label(node: dict) -> str:
    module = node.get("module_path", "")
    name = node.get("name", "")
    if name.startswith("__") and name.endswith("__"):
        return (
            "**Protocol method**: Zero internal callers by design. "
            "Invoked by Python's runtime machinery "
            "(e.g., `__init__`, `__str__`, `__exit__`)."
        )
    if "mcp_server" in module or name.startswith("_get_"):
        return (
            "**MCP Tool / Framework entry point**: Zero internal callers by design. "
            "Invoked by the MCP protocol dispatcher, not by code."
        )
    if "/cli/" in module or module.endswith("cli.py"):
        return (
            "**CLI entry point**: Zero internal callers by design. "
            "Invoked by Click's CLI router when the user runs the command."
        )
    return (
        "**Orphaned**: Never called internally. "
        "May be dead code, a public API, or a framework entry point."
    )
