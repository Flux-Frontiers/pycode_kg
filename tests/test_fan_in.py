"""Tests for :func:`pycode_kg.pycodekg_thorough_analysis._fan_in_count`.

Property bodies that read the attribute they back emit a CALLS self-loop
(see visitor.py's property-access rule); ``kg.callers()`` includes it, which
would otherwise inflate fan-in for a node with no real callers.
"""

from pycode_kg.pycodekg_thorough_analysis import _fan_in_count


class _FakeKG:
    """Stub exposing only the ``callers()`` surface ``_fan_in_count`` uses."""

    def __init__(self, caller_ids: list[str]) -> None:
        self._caller_ids = caller_ids

    def callers(self, node_id: str, rel: str = "CALLS") -> list[dict]:
        return [{"id": cid} for cid in self._caller_ids]


def test_self_loop_only_reports_zero_fan_in() -> None:
    """A node whose only caller is itself has no real callers."""
    node_id = "m:pkg/mod.py:Cls.prop"
    kg = _FakeKG([node_id])
    assert _fan_in_count(kg, node_id) == 0


def test_self_loop_plus_genuine_caller_reports_one() -> None:
    """A self-loop alongside a real caller still counts only the real one."""
    node_id = "m:pkg/mod.py:Cls.prop"
    kg = _FakeKG([node_id, "fn:pkg/other.py:caller"])
    assert _fan_in_count(kg, node_id) == 1


def test_no_self_loop_counts_all_callers() -> None:
    """Without a self-loop, every caller counts normally."""
    node_id = "m:pkg/mod.py:Cls.prop"
    kg = _FakeKG(["fn:pkg/a.py:a", "fn:pkg/b.py:b"])
    assert _fan_in_count(kg, node_id) == 2
