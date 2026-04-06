import ast

from code_kg.utils import node_id

# Relation types (add to your constants or use strings directly)
REL_CALLS = "CALLS"
REL_CONTAINS = "CONTAINS"
REL_READS = "READS"
REL_WRITES = "WRITES"
REL_ATTR_ACCESS = "ATTR_ACCESS"
REL_DEPENDS_ON = "DEPENDS_ON"  # placeholder for future control-flow


class CodeKGVisitor(ast.NodeVisitor):
    """AST visitor that walks a single Python source file and emits graph nodes and edges.

    Tracks scope (module → class → function/method), records ``CONTAINS``,
    ``CALLS``, ``READS``, ``WRITES``, and ``ATTR_ACCESS`` relationships, and
    builds a per-file node/edge registry consumed by :func:`~code_kg.graph.CodeGraph`.

    Property accesses (``obj.attr`` where ``attr`` is decorated with
    ``@property``) are resolved to ``CALLS`` edges via a pre-scan of the
    module tree performed in :meth:`visit_Module`.

    :param module_id: Dot-separated module identifier for the file being visited
        (e.g. ``code_kg.visitor``).
    :param file_path: Absolute path to the source file, stored as evidence on
        every edge emitted by this visitor.
    """

    def __init__(self, module_id: str, file_path: str):
        """Initialise the visitor for a single Python source file.

        :param module_id: Dot-separated module identifier for the file being
            visited (e.g. ``code_kg.visitor``).
        :param file_path: Absolute path to the source file, stored as evidence
            on every edge emitted by this visitor.
        """
        self.module_id = module_id
        self.file_path = file_path
        self.current_scope: list[str] = []  # qualnames stack
        self.current_func: str | None = None
        self.vars_in_scope: dict[str, set[str]] = {}  # scope → local vars set
        self._scope_kinds: dict[str, str] = {}  # qualname → kind
        self.edges: list[tuple[str, str, str, dict | None]] = []  # (src_id, tgt_id, rel, evidence)
        self.nodes: dict[str, dict] = {}  # id → node props (your existing)
        self._property_node_ids: dict[str, list[str]] = {}  # attr_name → property node IDs

    def _qualname(self, name: str) -> str:
        """Build the qualified name for *name* relative to the current scope.

        :param name: Short symbol name to qualify.
        :return: Dot-joined qualified name, e.g. ``MyClass.my_method``.
        """
        if self.current_scope:
            return f"{self.current_scope[-1]}.{name}"
        return name

    def _get_node_id(self, qualname: str) -> str:
        """Build a stable node id using the project's ``kind:module:qualname`` convention.

        Looks up the kind for *qualname* in the internal scope-kinds registry,
        defaulting to ``"symbol"`` when unknown. The resulting node is
        registered in ``self.nodes`` if not already present.

        :param qualname: Fully-qualified name of the symbol
            (e.g. ``mymodule.MyClass.my_method``).
        :return: Stable node identifier string suitable for use as a graph key.
        """
        kind = self._scope_kinds.get(qualname, "symbol")
        prefix = self.module_id + "."
        if kind == "module" or qualname == self.module_id:
            nid = node_id("module", self.module_id, None)
        else:
            rel_qn = qualname[len(prefix) :] if qualname.startswith(prefix) else qualname
            nid = node_id(kind, self.module_id, rel_qn)
        if nid not in self.nodes:
            self.nodes[nid] = {
                "qualname": qualname,
                "kind": kind,
                "file": self.file_path,
                "lineno": None,
                "end_lineno": None,
                "docstring": None,
            }
        return nid

    def _set_node_source_meta(self, node_id_value: str, ast_node: ast.AST) -> None:
        """Attach source span/docstring metadata to an existing visitor node.

        :param node_id_value: Stable node ID already present in ``self.nodes``.
        :param ast_node: AST node that carries ``lineno`` / ``end_lineno`` and
            optionally a docstring.
        """
        rec = self.nodes.get(node_id_value)
        if rec is None:
            return
        rec["lineno"] = getattr(ast_node, "lineno", None)
        rec["end_lineno"] = getattr(ast_node, "end_lineno", None)
        if isinstance(ast_node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            rec["docstring"] = ast.get_docstring(ast_node)

    def _add_edge(self, src_id: str, tgt_id: str, rel: str, evidence: ast.AST | None = None):
        """Record a directed edge between two graph nodes.

        :param src_id: Node identifier for the source of the edge.
        :param tgt_id: Node identifier for the target of the edge.
        :param rel: Relation type label (e.g. ``CALLS``, ``CONTAINS``).
        :param evidence: Optional AST node from which the line number is
            extracted and stored alongside the edge.
        """
        ev = {"lineno": getattr(evidence, "lineno", None), "file": self.file_path}
        self.edges.append((src_id, tgt_id, rel, ev))

    def _extract_reads(self, expr: ast.AST) -> set[str]:
        """Collect variable names that are loaded (READS).

        Walks *expr* and returns the identifier of every ``ast.Name`` node
        whose context is ``Load`` or ``Del`` (deletion can be read-like).

        :param expr: Root AST node to walk.
        :return: Set of variable name strings that are read within *expr*.
        """
        reads = set()
        for sub in ast.walk(expr):
            if isinstance(sub, ast.Name) and isinstance(
                sub.ctx, ast.Load | ast.Del
            ):  # Del can be read-like
                reads.add(sub.id)
        return reads

    def _add_var_edge(
        self,
        var_name: str,
        rel: str,
        target: str | None = None,
        evidence: ast.AST | None = None,
    ):
        """Emit an edge involving a variable node in the current scope.

        Creates a per-scope variable node for *var_name* and, when *target* is
        provided, emits a directed edge from that variable node to a node for
        *target* within the same scope.

        :param var_name: Name of the variable that is the source of the edge.
        :param rel: Relation type label (e.g. ``READS``, ``WRITES``,
            ``ATTR_ACCESS``).
        :param target: Name of the symbol that is the target of the edge.
            When ``None`` no edge is emitted (variable node is still created).
        :param evidence: Optional AST node used to record the source line
            number on the edge.
        """
        scope = self.current_scope[-1] if self.current_scope else None
        if not scope:
            return
        src_id = self._get_node_id(f"{scope}.{var_name}")  # per-scope var node
        if target:
            tgt_id = self._get_node_id(f"{scope}.{target}")
            self._add_edge(src_id, tgt_id, rel, evidence)
        # Optionally annotate var node itself

    # ────────────────────────────────────────────────
    # Enhanced visitors
    # ────────────────────────────────────────────────

    def _prescan_properties(self, tree: ast.AST) -> None:
        """Pre-scan the AST to register all ``@property`` methods before the main visit.

        Walks the full module tree and collects every method decorated with
        ``@property``, mapping its short name to its stable node ID.  This
        allows :meth:`visit_Attribute` to emit ``CALLS`` edges for property
        accesses even when the property definition appears after the access site.

        :param tree: Root ``ast.Module`` node for the file.
        """

        def _walk(node: ast.AST, class_parts: list[str]) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef):
                    _walk(child, class_parts + [child.name])
                elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    if class_parts:  # only methods, not module-level functions
                        is_property = any(
                            (isinstance(d, ast.Name) and d.id == "property")
                            or (isinstance(d, ast.Attribute) and d.attr == "property")
                            for d in child.decorator_list
                        )
                        if is_property:
                            rel_qn = ".".join(class_parts + [child.name])
                            nid = node_id("method", self.module_id, rel_qn)
                            self._property_node_ids.setdefault(child.name, []).append(nid)

        _walk(tree, [])

    def visit_Module(self, node: ast.Module):
        """Visit the top-level module node and initialise module scope state.

        Pushes the module's identifier onto the scope stack, registers its
        kind as ``"module"``, initialises its variable-in-scope set, then
        recurses into all child nodes before popping the scope.

        :param node: The ``ast.Module`` node for the file being visited.
        """
        self._prescan_properties(node)
        self.current_scope = [self.module_id]
        self._scope_kinds[self.module_id] = "module"
        self.vars_in_scope[self.module_id] = set()
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit a class definition and emit a CONTAINS edge from its parent.

        Registers the class as kind ``"class"``, pushes its qualified name onto
        the scope stack, records a ``CONTAINS`` relationship from the enclosing
        scope, then recurses into the class body before restoring the scope.

        :param node: The ``ast.ClassDef`` node being visited.
        """
        qualname = self._qualname(node.name)
        self._scope_kinds[qualname] = "class"
        self.current_scope.append(qualname)
        parent_id = self._get_node_id(self.current_scope[-2])
        class_id = self._get_node_id(qualname)
        self._set_node_source_meta(class_id, node)
        self._add_edge(parent_id, class_id, REL_CONTAINS)
        self.generic_visit(node)
        self.current_scope.pop()

    def _seed_params(self, qualname: str, args: ast.arguments) -> None:
        """Seed all parameter names into the function's local variable scope.

        :param qualname: Qualified name of the function being entered.
        :param args: The ``ast.arguments`` node from the function definition.
        """
        all_params = (
            args.posonlyargs
            + args.args
            + args.kwonlyargs
            + ([args.vararg] if args.vararg else [])
            + ([args.kwarg] if args.kwarg else [])
        )
        for param in all_params:
            self.vars_in_scope[qualname].add(param.arg)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit a synchronous function or method definition.

        Determines whether the callable is a ``"function"`` or ``"method"``
        based on the enclosing scope kind, processes default argument
        expressions in the enclosing scope, then pushes a new scope for the
        function body. Emits a ``CONTAINS`` edge from the parent scope and
        seeds parameter names into the local variable set before recursing.

        :param node: The ``ast.FunctionDef`` node being visited.
        """
        qualname = self._qualname(node.name)
        parent_kind = self._scope_kinds.get(
            self.current_scope[-1] if self.current_scope else "", "module"
        )
        func_kind = "method" if parent_kind == "class" else "function"
        self._scope_kinds[qualname] = func_kind

        # Default expressions are evaluated in the enclosing scope, not the
        # function scope — process them before pushing the new scope.
        # kw_defaults may contain None for keyword-only args without a default.
        defaults = node.args.defaults + [d for d in node.args.kw_defaults if d is not None]
        for expr in defaults:
            for r in self._extract_reads(expr):
                self._add_var_edge(r, REL_READS, evidence=expr)

        self.current_scope.append(qualname)
        self.current_func = qualname
        self.vars_in_scope[qualname] = set()
        self._seed_params(qualname, node.args)

        parent_id = self._get_node_id(self.current_scope[-2])
        func_id = self._get_node_id(qualname)
        self._set_node_source_meta(func_id, node)
        self._add_edge(parent_id, func_id, REL_CONTAINS)

        for stmt in node.body:
            self.visit(stmt)

        self.current_scope.pop()
        self.current_func = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit an asynchronous function or method definition.

        Behaves identically to :meth:`visit_FunctionDef` but handles
        ``async def`` nodes. Determines kind (``"function"`` or
        ``"method"``), processes default argument expressions in the
        enclosing scope, pushes the function scope, emits a ``CONTAINS``
        edge, seeds parameters, and recurses into the body.

        :param node: The ``ast.AsyncFunctionDef`` node being visited.
        """
        qualname = self._qualname(node.name)
        parent_kind = self._scope_kinds.get(
            self.current_scope[-1] if self.current_scope else "", "module"
        )
        func_kind = "method" if parent_kind == "class" else "function"
        self._scope_kinds[qualname] = func_kind

        # Default expressions are evaluated in the enclosing scope, not the
        # function scope — process them before pushing the new scope.
        # kw_defaults may contain None for keyword-only args without a default.
        defaults = node.args.defaults + [d for d in node.args.kw_defaults if d is not None]
        for expr in defaults:
            for r in self._extract_reads(expr):
                self._add_var_edge(r, REL_READS, evidence=expr)

        self.current_scope.append(qualname)
        self.current_func = qualname
        self.vars_in_scope[qualname] = set()
        self._seed_params(qualname, node.args)

        parent_id = self._get_node_id(self.current_scope[-2])
        func_id = self._get_node_id(qualname)
        self._set_node_source_meta(func_id, node)
        self._add_edge(parent_id, func_id, REL_CONTAINS)

        for stmt in node.body:
            self.visit(stmt)

        self.current_scope.pop()
        self.current_func = None

    def visit_Assign(self, node: ast.Assign):
        """Visit a simple assignment statement and record READS/WRITES edges.

        For each ``ast.Name`` target, registers the variable in the current
        scope's variable set, emits ``READS`` edges for every variable name
        loaded from the right-hand side, and emits a ``WRITES`` edge for the
        target variable.

        :param node: The ``ast.Assign`` node being visited.
        """
        for target in node.targets:
            if isinstance(target, ast.Name):
                var = target.id
                scope = self.current_scope[-1] if self.current_scope else None
                if scope:
                    self.vars_in_scope.setdefault(scope, set()).add(var)

                # READS from value
                reads = self._extract_reads(node.value)
                for r in reads:
                    self._add_var_edge(r, REL_READS, evidence=node)

                # WRITES to target
                self._add_var_edge(var, REL_WRITES, evidence=node)

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Visit an attribute access and emit an ATTR_ACCESS edge.

        When the object being accessed is a simple name (``ast.Name``), emits
        an ``ATTR_ACCESS`` edge from the object's variable node to a node
        representing the accessed attribute within the current scope.

        Additionally, if the accessed attribute matches a ``@property`` method
        discovered during the pre-scan, emits a ``CALLS`` edge from the
        enclosing function to that property method node so that property
        accesses appear in the call graph.

        :param node: The ``ast.Attribute`` node being visited.
        """
        if isinstance(node.value, ast.Name):
            obj = node.value.id
            attr = node.attr
            self._add_var_edge(obj, REL_ATTR_ACCESS, target=attr, evidence=node)
            if self.current_func and attr in self._property_node_ids:
                caller_id = self._get_node_id(self.current_func)
                for prop_nid in self._property_node_ids[attr]:
                    self._add_edge(caller_id, prop_nid, REL_CALLS, evidence=node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Visit a call expression and emit READS edges for all arguments.

        Records ``READS`` edges for every variable loaded from positional
        arguments and keyword argument values so that data-flow through call
        sites is captured in the graph.

        :param node: The ``ast.Call`` node being visited.
        """
        # Assume you already have CALLS logic; add READS from args/kwargs
        for arg in node.args:
            reads = self._extract_reads(arg)
            for r in reads:
                self._add_var_edge(r, REL_READS, evidence=node)

        for kw in node.keywords:
            if kw.value:
                reads = self._extract_reads(kw.value)
                for r in reads:
                    self._add_var_edge(r, REL_READS, evidence=node)

        self.generic_visit(node)

    # Add more visitors as needed (e.g. visit_If for DEPENDS_ON stubs)

    def finalize(self):
        """Return collected nodes and edges for database insertion.

        :return: A two-tuple ``(nodes, edges)`` where *nodes* is a dict
            mapping node id strings to their property dicts and *edges* is a
            list of ``(src_id, tgt_id, rel, evidence)`` tuples.
        """
        return self.nodes, self.edges
