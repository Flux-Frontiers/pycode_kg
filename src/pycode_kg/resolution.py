"""resolution.py — Post-resolution hygiene for the symbol graph.

``kg_utils.store.resolve_symbols()`` matches ``sym:`` stubs to first-party
definitions by name, falling back to the bare last segment with no receiver
awareness.  A repo function named ``update`` therefore captures every
``visited.update(...)`` dict/set mutation in the codebase as a RESOLVES_TO
edge, polluting everything derived from resolved CALLS edges: ``callers()``
fan-in, CodeRank, and call-chain tracing.  (Observed here: the ``update()``
Click command collected RESOLVES_TO edges from nine unrelated container
mutations, fabricating the analysis report's only "deep call chain".)

:data:`BUILTIN_METHOD_NAMES` lists builtin container/str method names; a
dotted ``sym:`` stub ending in one of them is a builtin method call, and
:func:`prune_builtin_method_resolutions` deletes its RESOLVES_TO edges after
the resolution pass.

:func:`prune_thirdparty_attribute_resolutions` covers the larger population:
any dotted stub whose root is an imported stdlib/third-party name (e.g.
``subprocess.run``), found by joining ``CALLS`` back to the calling module's
``IMPORTS`` edges — no receiver typing required.

:func:`prune_self_attribute_resolutions` covers a third population: a stub
like ``self.plotter.render`` names an instance attribute of unknown type as
its receiver, so last-segment matching is a coin flip regardless of import
visibility.  All three prunes run from :func:`resolve_symbols_pruned`,
called from every build site.  The durable fix is receiver-aware resolution
upstream in kg_utils; until then these prunes run in
:meth:`PyCodeKG._post_build_hook`.

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

import sqlite3
from collections import defaultdict

BUILTIN_METHOD_NAMES = frozenset(
    {
        "add",
        "append",
        "clear",
        "copy",
        "count",
        "discard",
        "extend",
        "format",
        "get",
        "index",
        "insert",
        "items",
        "join",
        "keys",
        "pop",
        "popitem",
        "remove",
        "replace",
        "setdefault",
        "sort",
        "split",
        "strip",
        "update",
        "values",
        "write",
    }
)


def prune_builtin_method_resolutions(con: sqlite3.Connection) -> int:
    """Delete RESOLVES_TO edges sourced from builtin-method lookalike stubs.

    A stub qualifies when its name is dotted (it was an attribute call, so the
    receiver is some object, not a module import) and its last segment is a
    builtin container/str method name.  Bare-name stubs (``sym:update`` from a
    direct ``update(...)`` call) are never touched.

    :param con: Open SQLite connection with an ``edges`` table.
    :return: Number of RESOLVES_TO edges deleted.
    """
    rows = con.execute(
        "SELECT DISTINCT src FROM edges WHERE rel = 'RESOLVES_TO' AND src LIKE 'sym:%.%'"
    ).fetchall()
    doomed = [
        (src,)
        for (src,) in rows
        if src.removeprefix("sym:").rsplit(".", 1)[-1] in BUILTIN_METHOD_NAMES
    ]
    if not doomed:
        return 0
    cur = con.executemany("DELETE FROM edges WHERE rel = 'RESOLVES_TO' AND src = ?", doomed)
    con.commit()
    return cur.rowcount


def prune_thirdparty_attribute_resolutions(con: sqlite3.Connection) -> int:
    """Delete RESOLVES_TO edges into first-party lookalikes of external attribute calls.

    A dotted stub ``sym:<root>.<rest>`` from an attribute call (e.g.
    ``subprocess.run(...)``) still resolves by last-segment name fallback in
    ``kg_utils.store.resolve_symbols()``, so a first-party function
    coincidentally named ``run`` captures the call.  ``<root>`` is
    import-visible: a module that calls the stub and also imports ``<root>``
    (a ``mod:`` -[IMPORTS]-> ``sym:<root>`` edge) tells us what ``<root>``
    actually is.  When at least one calling module imports ``<root>`` and
    ``sym:<root>`` never resolves to a first-party module anywhere in the
    graph, ``<root>`` is a stdlib/third-party name and the stub's
    RESOLVES_TO edges are bogus.

    Conservative by construction, in both directions:

    - If ``sym:<root>`` resolves to a first-party module *anywhere* in the
      graph, the stub is left alone entirely — even for a calling module
      where ``<root>`` is actually external.  The join cannot tell which
      call site produced which resolution, so a stub reached from both a
      first-party and a third-party binding stays.
    - A stub whose root is never imported by any of its callers (e.g.
      ``self.<attr>.<method>``, a local variable) is left untouched — that
      population belongs to a receiver-type-aware prune, not this one.

    :param con: Open SQLite connection with ``nodes`` and ``edges`` tables.
    :return: Number of RESOLVES_TO edges deleted.
    """
    stub_rows = con.execute(
        "SELECT DISTINCT src FROM edges WHERE rel = 'RESOLVES_TO' AND src LIKE 'sym:%.%'"
    ).fetchall()
    if not stub_rows:
        return 0

    imports_by_module: dict[str, set[str]] = defaultdict(set)
    for src, dst in con.execute(
        "SELECT src, dst FROM edges WHERE rel = 'IMPORTS' AND src LIKE 'mod:%' AND dst LIKE 'sym:%'"
    ).fetchall():
        imports_by_module[src.removeprefix("mod:")].add(dst.removeprefix("sym:"))

    first_party_roots = {
        src.removeprefix("sym:")
        for (src,) in con.execute(
            "SELECT DISTINCT e.src FROM edges e JOIN nodes n ON n.id = e.dst"
            " WHERE e.rel = 'RESOLVES_TO' AND e.src LIKE 'sym:%' AND n.kind = 'module'"
        ).fetchall()
    }

    doomed: list[tuple[str]] = []
    for (stub_id,) in stub_rows:
        root = stub_id.removeprefix("sym:").split(".", 1)[0]
        if root in first_party_roots:
            continue

        caller_modules = {
            src.split(":", 2)[1]
            for (src,) in con.execute(
                "SELECT DISTINCT src FROM edges WHERE rel = 'CALLS' AND dst = ?", (stub_id,)
            ).fetchall()
            if src.count(":") >= 2
        }
        if not any(root in imports_by_module.get(m, ()) for m in caller_modules):
            continue

        doomed.append((stub_id,))

    if not doomed:
        return 0
    cur = con.executemany("DELETE FROM edges WHERE rel = 'RESOLVES_TO' AND src = ?", doomed)
    con.commit()
    return cur.rowcount


def prune_self_attribute_resolutions(con: sqlite3.Connection) -> int:
    """Delete RESOLVES_TO edges from ``self.``/``cls.`` attribute-of-attribute stubs.

    A stub with three or more dotted segments rooted at ``self`` or ``cls``
    (e.g. ``self.plotter.render``) names an instance/class attribute of
    unknown type as its receiver.  ``kg_utils.store.resolve_symbols()``
    still matches it by last-segment name fallback, so any first-party
    method sharing the final segment's name captures the call — a coin
    flip, not a resolution.  A two-segment ``self.<method>`` stub is a
    same-class method reference and is left alone; only the deeper,
    attribute-of-attribute form is unresolvable without receiver-type
    inference.

    :param con: Open SQLite connection with an ``edges`` table.
    :return: Number of RESOLVES_TO edges deleted.
    """
    rows = con.execute(
        "SELECT DISTINCT src FROM edges WHERE rel = 'RESOLVES_TO'"
        " AND (src LIKE 'sym:self.%.%' OR src LIKE 'sym:cls.%.%')"
    ).fetchall()
    doomed = [(src,) for (src,) in rows]
    if not doomed:
        return 0
    cur = con.executemany("DELETE FROM edges WHERE rel = 'RESOLVES_TO' AND src = ?", doomed)
    con.commit()
    return cur.rowcount


def resolve_symbols_pruned(store) -> int:
    """Resolve symbol stubs, then prune bogus attribute-call resolutions.

    Drop-in replacement for ``store.resolve_symbols()`` at every build site
    (CLI pipelines and the KGModule post-build hook), so resolution and
    hygiene cannot drift apart.

    :param store: :class:`~pycode_kg.store.GraphStore` whose graph was just
        written.
    :return: Net number of RESOLVES_TO edges added (resolved minus pruned).
    """
    resolved = store.resolve_symbols()
    pruned = prune_builtin_method_resolutions(store.con)
    pruned += prune_thirdparty_attribute_resolutions(store.con)
    pruned += prune_self_attribute_resolutions(store.con)
    return max(0, resolved - pruned)
