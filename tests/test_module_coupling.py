"""
test_module_coupling.py

Regression tests for ``PyCodeKGAnalyzer._analyze_module_coupling`` and
specifically the cohesion calculation.  The formula is documented as:

    cohesion = incoming / (incoming + outgoing + 1)

so a leaf entry-point module (incoming=0, outgoing>0) must score near zero
and a widely-imported module (incoming>>outgoing) must score near 1.0.

A previous bug used ``outgoing`` in the numerator, giving entry-point
modules an inflated cohesion score (mcp_server.py read 0.75 with incoming=0,
outgoing=3).  These tests lock the corrected formula in place.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pycode_kg.kg import PyCodeKG
from pycode_kg.pycodekg_thorough_analysis import PyCodeKGAnalyzer


def _make_kg(tmp_path: Path, files: dict[str, str]) -> PyCodeKG:
    repo = tmp_path / "repo"
    for rel, src in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))
    kg = PyCodeKG(
        repo_root=repo,
        db_path=tmp_path / "pycodekg.sqlite",
        vectors_path=tmp_path / "vectors.sqlite",
    )
    kg.build_graph(wipe=True)
    return kg


def _cohesion_for(metrics: dict, suffix: str) -> float:
    """Find the metrics entry whose key ends with ``suffix`` and return its score."""
    matches = [m for path, m in metrics.items() if path.endswith(suffix)]
    assert matches, f"module ending {suffix!r} missing; have {list(metrics)}"
    return matches[0].cohesion_score


def test_leaf_entry_point_module_scores_zero(tmp_path):
    """A module that imports others but is imported by nobody scores ~0."""
    kg = _make_kg(
        tmp_path,
        {
            "core.py": "def core():\n    return 1\n",
            "util.py": "def util():\n    return 2\n",
            "main.py": (
                "from core import core\n"
                "from util import util\n"
                "def main():\n    return core() + util()\n"
            ),
        },
    )
    analyzer = PyCodeKGAnalyzer(kg)
    analyzer._analyze_module_coupling()

    # main.py: incoming=0, outgoing=2, cohesion = 0 / (0+2+1) = 0.0
    assert _cohesion_for(analyzer.module_metrics, "main.py") == pytest.approx(0.0)
    kg.close()


def test_central_imported_module_scores_high(tmp_path):
    """A module imported by many but importing nobody scores high."""
    kg = _make_kg(
        tmp_path,
        {
            "core.py": "def core():\n    return 1\n",
            "consumer_a.py": "from core import core\n",
            "consumer_b.py": "from core import core\n",
            "consumer_c.py": "from core import core\n",
        },
    )
    analyzer = PyCodeKGAnalyzer(kg)
    analyzer._analyze_module_coupling()

    # core.py: incoming=3, outgoing=0, cohesion = 3 / (3+0+1) = 0.75
    assert _cohesion_for(analyzer.module_metrics, "core.py") == pytest.approx(0.75)
    kg.close()


def test_cohesion_formula_matches_documentation(tmp_path):
    """Two-module repo: verify both directions of the import edge."""
    kg = _make_kg(
        tmp_path,
        {
            "core.py": "def core():\n    return 1\n",
            "leaf.py": "from core import core\n",
        },
    )
    analyzer = PyCodeKGAnalyzer(kg)
    analyzer._analyze_module_coupling()

    # core.py: incoming=1, outgoing=0 → 1/(1+0+1) = 0.5
    # leaf.py: incoming=0, outgoing=1 → 0/(0+1+1) = 0.0
    assert _cohesion_for(analyzer.module_metrics, "core.py") == pytest.approx(0.5)
    assert _cohesion_for(analyzer.module_metrics, "leaf.py") == pytest.approx(0.0)
    kg.close()
