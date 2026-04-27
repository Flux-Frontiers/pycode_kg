#!/usr/bin/env python3
"""
Code Knowledge Graph (PyCodeKG) Extractor

Extracts a deterministic, side-effect-free knowledge graph from Python repositories
via AST analysis. Produces nodes (modules, classes, functions, methods, symbols) and
edges (CONTAINS, IMPORTS, INHERITS, CALLS, READS, WRITES, ATTR_ACCESS, DEPENDS_ON).

**Core Principles:**
- Pure: No side effects, deterministic output given the same input
- Honest: Only extracts what's explicitly visible in the AST—no guessing,
  no embeddings, no LLM inference
- Modular: Three-pass approach (structure, call graph, data-flow)
- Extensible: Designed to feed downstream analysis (visualization, querying,
  semantic indexing)

**Design:**
- PASS 1: Structural extraction (modules, classes, functions, methods, imports, inheritance)
- PASS 2: Call graph via AST-based function call analysis
- PASS 3: Data-flow edges (reads, writes, attribute access) via PyCodeKGVisitor

No persistence, no embeddings, no LLMs—just pure AST extraction. Integration with
vector databases and semantic search happens downstream.

Author: Eric G. Suchanek, PhD
Last Revision: 2026-03-01 20:33:41
"""

from __future__ import annotations

import ast
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================
from pycode_kg.index import DEFAULT_MODEL as DEFAULT_MODEL  # noqa: F401 — re-exported
from pycode_kg.utils import node_id, rel_module_path
from pycode_kg.visitor import PyCodeKGVisitor

# ============================================================================
# Graph primitives (LOCKED v0 CONTRACT)
# ============================================================================


@dataclass(frozen=True)
class Node:
    """
    Graph node.

    :param id: Stable node id (e.g. fn:pkg/util.py:parse_file)
    :param kind: module | class | function | method | symbol
    :param name: Short name
    :param qualname: Qualified name within module
    :param module_path: Repo-relative module path
    :param lineno: Starting line number
    :param end_lineno: Ending line number (if available)
    :param docstring: Extracted docstring (may be None)
    """

    id: str
    kind: str
    name: str
    qualname: str | None
    module_path: str | None
    lineno: int | None
    end_lineno: int | None
    docstring: str | None


@dataclass(frozen=True)
class Edge:
    """
    Graph edge.

    :param src: Source node id
    :param rel: Relationship type
    :param dst: Destination node id
    :param evidence: Optional evidence dict (lineno, expr, etc.)
    """

    src: str
    rel: str
    dst: str
    evidence: dict | None = None


# ============================================================================
# Constants
# ============================================================================

NODE_KINDS = {"module", "class", "function", "method", "symbol"}
EDGE_KINDS = {
    "CONTAINS",
    "IMPORTS",
    "INHERITS",
    "CALLS",
    "READS",
    "WRITES",
    "ATTR_ACCESS",
    "DEPENDS_ON",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".pycodekg",
}


# ============================================================================
# Utility helpers
# ============================================================================


def iter_python_files(
    repo_root: Path,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
) -> Iterable[Path]:
    """
    Yield Python files under repo_root.

    :param repo_root: Repository root
    :param include: Set of directory names to include (e.g., {"src", "lib"}).
                   When non-empty, only these top-level directories are walked.
                   When empty/None, all directories are walked (except SKIP_DIRS).
    :param exclude: Set of directory names to prune at every depth of the walk
                   (e.g., {"tests", "benchmarks"}).  Combined with SKIP_DIRS.
    """
    skip = SKIP_DIRS | (exclude or set())
    walk_roots = (
        [repo_root / d for d in include if (repo_root / d).is_dir()] if include else [repo_root]
    )
    for walk_root in walk_roots:
        for root, dirs, files in os.walk(walk_root):
            dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
            for f in files:
                if f.endswith(".py") and not f.startswith("."):
                    yield Path(root) / f


def expr_to_name(expr: ast.AST) -> str | None:
    """
    Convert AST expression to dotted name (best effort).

    :param expr: AST node
    """
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        left = expr_to_name(expr.value)
        return f"{left}.{expr.attr}" if left else expr.attr
    if isinstance(expr, ast.Call):
        return expr_to_name(expr.func)
    if isinstance(expr, ast.Subscript):
        return expr_to_name(expr.value)
    return None


# ============================================================================
# AST helpers (module-level to avoid closure-in-loop)
# ============================================================================


def _enclosing_def(
    n: ast.AST,
    parent: dict[ast.AST, ast.AST],
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Find the nearest enclosing function or async function definition.

    :param n: AST node whose enclosing function definition is sought.
    :param parent: Mapping from child node to its parent node.
    :return: Nearest enclosing ``FunctionDef`` or ``AsyncFunctionDef``,
             or ``None`` if not inside any function.
    """
    cur = parent.get(n)
    while cur:
        if isinstance(cur, ast.FunctionDef | ast.AsyncFunctionDef):
            return cur
        cur = parent.get(cur)
    return None


def _owner_id(
    fn: ast.FunctionDef | ast.AsyncFunctionDef,
    parent: dict[ast.AST, ast.AST],
    module: str,
    module_locals: dict[str, dict[str, str]],
) -> str | None:
    """Compute the graph node ID for the owner of a function definition.

    :param fn: Function or async function definition node.
    :param parent: Mapping from child node to its parent node.
    :param module: Repo-relative module path for the current file.
    :param module_locals: Per-module mapping of qualname to node ID.
    :return: Graph node ID string if the function is tracked, otherwise ``None``.
    """
    p = parent.get(fn)
    if isinstance(p, ast.ClassDef):
        return module_locals[module].get(f"{p.name}.{fn.name}")
    return module_locals[module].get(fn.name)


# ============================================================================
# Core extraction logic
# ============================================================================


def extract_repo(
    repo_root: Path,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
) -> tuple[list[Node], list[Edge]]:
    """
    Extract a code knowledge graph from a repository.

    This function is:
    - pure
    - deterministic
    - side-effect free

    :param repo_root: Path to repository root
    :param include: Set of directory names to include (e.g., {"src", "lib"}).
                   When non-empty, only these top-level directories are indexed.
                   When empty/None, all directories are indexed.
    :param exclude: Set of directory names to prune at every walk depth
                   (e.g., {"tests", "benchmarks"}).
    :return: (nodes, edges)
    """
    nodes: dict[str, Node] = {}
    edges: dict[tuple[str, str, str], Edge] = {}

    # ------------------------------------------------------------------
    # PASS 1: modules, classes, functions, methods
    # ------------------------------------------------------------------

    module_locals: dict[str, dict[str, str]] = {}
    module_class_methods: dict[str, dict[str, str]] = {}
    module_import_aliases: dict[str, dict[str, str]] = {}

    for pyfile in iter_python_files(repo_root, include=include, exclude=exclude):
        module = rel_module_path(pyfile, repo_root)

        try:
            src = pyfile.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=module)
        except (SyntaxError, UnicodeDecodeError):
            continue

        # module node
        mod_id = node_id("module", module, None)
        nodes[mod_id] = Node(
            id=mod_id,
            kind="module",
            name=Path(module).stem,
            qualname=None,
            module_path=module,
            lineno=1,
            end_lineno=src.count("\n") + 1,
            docstring=ast.get_docstring(tree),
        )

        module_locals[module] = {}
        module_class_methods[module] = {}
        module_import_aliases[module] = {}

        # traverse module body only (NOT ast.walk)
        for stmt in tree.body:
            # --------------------
            # class definitions
            # --------------------
            if isinstance(stmt, ast.ClassDef):
                cls_qn = stmt.name
                cls_id = node_id("class", module, cls_qn)

                nodes[cls_id] = Node(
                    id=cls_id,
                    kind="class",
                    name=stmt.name,
                    qualname=cls_qn,
                    module_path=module,
                    lineno=getattr(stmt, "lineno", None),
                    end_lineno=getattr(stmt, "end_lineno", None),
                    docstring=ast.get_docstring(stmt),
                )

                edges[(mod_id, "CONTAINS", cls_id)] = Edge(
                    src=mod_id,
                    rel="CONTAINS",
                    dst=cls_id,
                )

                module_locals[module][stmt.name] = cls_id

                # inheritance
                for base in stmt.bases:
                    bname = expr_to_name(base)
                    if not bname:
                        continue
                    sym_id = f"sym:{bname}"
                    nodes.setdefault(
                        sym_id,
                        Node(
                            sym_id,
                            "symbol",
                            bname.split(".")[-1],
                            bname,
                            None,
                            None,
                            None,
                            None,
                        ),
                    )
                    edges[(cls_id, "INHERITS", sym_id)] = Edge(
                        src=cls_id,
                        rel="INHERITS",
                        dst=sym_id,
                        evidence={"lineno": getattr(stmt, "lineno", None)},
                    )

                # methods
                for cstmt in stmt.body:
                    if isinstance(cstmt, ast.FunctionDef | ast.AsyncFunctionDef):
                        m_qn = f"{stmt.name}.{cstmt.name}"
                        m_id = node_id("method", module, m_qn)

                        nodes[m_id] = Node(
                            id=m_id,
                            kind="method",
                            name=cstmt.name,
                            qualname=m_qn,
                            module_path=module,
                            lineno=getattr(cstmt, "lineno", None),
                            end_lineno=getattr(cstmt, "end_lineno", None),
                            docstring=ast.get_docstring(cstmt),
                        )

                        edges[(cls_id, "CONTAINS", m_id)] = Edge(
                            src=cls_id,
                            rel="CONTAINS",
                            dst=m_id,
                        )

                        module_class_methods[module][cstmt.name] = m_id
                        module_locals[module][m_qn] = m_id

            # --------------------
            # top-level functions
            # --------------------
            elif isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
                fn_qn = stmt.name
                fn_id = node_id("function", module, fn_qn)

                nodes[fn_id] = Node(
                    id=fn_id,
                    kind="function",
                    name=stmt.name,
                    qualname=fn_qn,
                    module_path=module,
                    lineno=getattr(stmt, "lineno", None),
                    end_lineno=getattr(stmt, "end_lineno", None),
                    docstring=ast.get_docstring(stmt),
                )

                edges[(mod_id, "CONTAINS", fn_id)] = Edge(
                    src=mod_id,
                    rel="CONTAINS",
                    dst=fn_id,
                )

                module_locals[module][stmt.name] = fn_id

            # --------------------
            # imports
            # --------------------
            elif isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    sym = alias.name
                    alias_name = alias.asname or alias.name.split(".")[0]
                    module_import_aliases[module][alias_name] = sym
                    sym_id = f"sym:{sym}"
                    nodes.setdefault(
                        sym_id,
                        Node(
                            sym_id,
                            "symbol",
                            sym.split(".")[-1],
                            sym,
                            None,
                            None,
                            None,
                            None,
                        ),
                    )
                    edges[(mod_id, "IMPORTS", sym_id)] = Edge(
                        src=mod_id,
                        rel="IMPORTS",
                        dst=sym_id,
                        evidence={"lineno": getattr(stmt, "lineno", None)},
                    )

            elif isinstance(stmt, ast.ImportFrom):
                mod = stmt.module or ""
                for alias in stmt.names:
                    full = f"{mod}.{alias.name}" if mod else alias.name
                    alias_name = alias.asname or alias.name
                    module_import_aliases[module][alias_name] = full
                    sym_id = f"sym:{full}"
                    nodes.setdefault(
                        sym_id,
                        Node(sym_id, "symbol", alias.name, full, None, None, None, None),
                    )
                    edges[(mod_id, "IMPORTS", sym_id)] = Edge(
                        src=mod_id,
                        rel="IMPORTS",
                        dst=sym_id,
                        evidence={"lineno": getattr(stmt, "lineno", None)},
                    )

        # Capture function-local imports too so call resolution can disambiguate
        # symbols imported inside function bodies (e.g., ``from pkg.mod import x``).
        for imp in ast.walk(tree):
            if isinstance(imp, ast.Import):
                for alias in imp.names:
                    alias_name = alias.asname or alias.name.split(".")[0]
                    module_import_aliases[module][alias_name] = alias.name
            elif isinstance(imp, ast.ImportFrom):
                mod = imp.module or ""
                for alias in imp.names:
                    full = f"{mod}.{alias.name}" if mod else alias.name
                    alias_name = alias.asname or alias.name
                    module_import_aliases[module][alias_name] = full

        # ------------------------------------------------------------------
        # PASS 2: call graph (best-effort, honest)
        # ------------------------------------------------------------------

        parent: dict[ast.AST, ast.AST] = {}
        for p in ast.walk(tree):
            for c in ast.iter_child_nodes(p):
                parent[c] = p

        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue

            fn = _enclosing_def(n, parent)
            if fn is None:
                continue

            src_id = _owner_id(fn, parent, module, module_locals)
            if not src_id:
                continue

            callee = expr_to_name(n.func)
            if not callee:
                continue

            # resolution rules (LOCKED)
            if callee in module_locals[module]:
                dst_id = module_locals[module][callee]
            elif callee in module_import_aliases[module]:
                dst_id = f"sym:{module_import_aliases[module][callee]}"
            elif "." in callee and callee.split(".", 1)[0] in module_import_aliases[module]:
                head, tail = callee.split(".", 1)
                resolved = module_import_aliases[module][head]
                dst_id = f"sym:{resolved}.{tail}"
            elif callee.startswith("self."):
                meth = callee.split(".", 1)[1]
                dst_id = module_class_methods[module].get(meth) or f"sym:{callee}"
            else:
                dst_id = f"sym:{callee}"

            if dst_id.startswith("sym:"):
                nodes.setdefault(
                    dst_id,
                    Node(
                        dst_id,
                        "symbol",
                        dst_id.split(":")[-1].split(".")[-1],
                        dst_id[4:],
                        None,
                        None,
                        None,
                        None,
                    ),
                )

            edges[(src_id, "CALLS", dst_id)] = Edge(
                src=src_id,
                rel="CALLS",
                dst=dst_id,
                evidence={
                    "lineno": getattr(n, "lineno", None),
                    "expr": callee,
                },
            )

        # ------------------------------------------------------------------
        # PASS 3: data-flow edges via PyCodeKGVisitor (READS, WRITES, ATTR_ACCESS)
        # ------------------------------------------------------------------

        vis = PyCodeKGVisitor(module_id=module, file_path=str(pyfile))
        vis.visit(tree)
        vis_nodes, vis_edges = vis.finalize()

        # Merge new symbol/var nodes that Pass 1 didn't create.
        for nid, props in vis_nodes.items():
            nodes.setdefault(
                nid,
                Node(
                    id=nid,
                    kind=props["kind"],
                    name=props["qualname"].split(".")[-1],
                    qualname=props["qualname"],
                    module_path=module,
                    lineno=props.get("lineno"),
                    end_lineno=props.get("end_lineno"),
                    docstring=props.get("docstring"),
                ),
            )

        # Merge data-flow edges; setdefault keeps Pass 1/2 edges authoritative
        # for any CONTAINS/CALLS duplicates.
        for src_id, tgt_id, rel, ev in vis_edges:
            edges.setdefault(
                (src_id, rel, tgt_id),
                Edge(src=src_id, rel=rel, dst=tgt_id, evidence=ev),
            )

    return list(nodes.values()), list(edges.values())
