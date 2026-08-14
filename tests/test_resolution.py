"""Tests for post-resolution hygiene (pycode_kg.resolution).

The SDK's name-fallback resolution wires ``visited.update(...)``-style
builtin method calls onto any repo function sharing the method's name.  The
post-build prune deletes those RESOLVES_TO edges; these tests pin what is
deleted and, just as importantly, what is kept.
"""

import sqlite3

import pytest

from pycode_kg.resolution import BUILTIN_METHOD_NAMES, prune_builtin_method_resolutions


@pytest.fixture
def con() -> sqlite3.Connection:
    """In-memory edges table seeded with good and bogus resolutions."""
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE edges (src TEXT, rel TEXT, dst TEXT)")
    con.executemany(
        "INSERT INTO edges VALUES (?, ?, ?)",
        [
            # Bogus: set/dict mutations resolved onto a Click command
            ("sym:visited.update", "RESOLVES_TO", "fn:src/p/cli.py:update"),
            ("sym:snap.__dict__.update", "RESOLVES_TO", "fn:src/p/cli.py:update"),
            ("sym:chunks.append", "RESOLVES_TO", "fn:src/p/x.py:append"),
            # Legitimate: dotted attr call onto a real repo method
            ("sym:self.kg.callers", "RESOLVES_TO", "m:src/p/kg.py:KG.callers"),
            # Legitimate: bare-name direct call, even to a builtin-sounding name
            ("sym:update", "RESOLVES_TO", "fn:src/p/cli.py:update"),
            # Untouched: non-RESOLVES_TO edges never pruned
            ("fn:src/p/a.py:f", "CALLS", "sym:visited.update"),
        ],
    )
    con.commit()
    return con


def test_prunes_builtin_method_lookalikes(con) -> None:
    """Dotted stubs ending in builtin method names lose their resolutions."""
    deleted = prune_builtin_method_resolutions(con)
    assert deleted == 3
    remaining = {row[0] for row in con.execute("SELECT src FROM edges WHERE rel='RESOLVES_TO'")}
    assert remaining == {"sym:self.kg.callers", "sym:update"}


def test_calls_edges_are_never_touched(con) -> None:
    """Pruning removes resolutions only; the CALLS record of the stub stays."""
    prune_builtin_method_resolutions(con)
    calls = con.execute("SELECT COUNT(*) FROM edges WHERE rel='CALLS'").fetchone()[0]
    assert calls == 1


def test_prune_is_idempotent(con) -> None:
    """A second pass finds nothing to delete."""
    prune_builtin_method_resolutions(con)
    assert prune_builtin_method_resolutions(con) == 0


def test_builtin_names_cover_the_observed_polluters() -> None:
    """The names seen polluting this repo's graph are all covered."""
    assert {"update", "append", "get", "items", "add", "extend"} <= BUILTIN_METHOD_NAMES
