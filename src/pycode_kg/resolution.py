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
the resolution pass.  The durable fix is receiver-aware resolution upstream
in kg_utils; until then this prune runs in :meth:`PyCodeKG._post_build_hook`.

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
"""

import sqlite3

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


def resolve_symbols_pruned(store) -> int:
    """Resolve symbol stubs, then prune builtin-method lookalikes.

    Drop-in replacement for ``store.resolve_symbols()`` at every build site
    (CLI pipelines and the KGModule post-build hook), so resolution and
    hygiene cannot drift apart.

    :param store: :class:`~pycode_kg.store.GraphStore` whose graph was just
        written.
    :return: Net number of RESOLVES_TO edges added (resolved minus pruned).
    """
    resolved = store.resolve_symbols()
    pruned = prune_builtin_method_resolutions(store.con)
    return max(0, resolved - pruned)
