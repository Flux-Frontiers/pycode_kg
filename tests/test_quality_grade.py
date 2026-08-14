"""Tests for the continuous quality-grade curve.

The 2026-08-12 → 2026-08-13 runs swung a full letter (B/82 → C/67) from one
component crossing a step threshold.  The curve is now continuous: these
tests pin the component formulas, the smoothness property (one extra finding
never moves the score by a cliff), and the dead-code *rate* normalization.
"""

from types import SimpleNamespace

import pytest

from pycode_kg.pycodekg_thorough_analysis import FunctionMetrics, PyCodeKGAnalyzer


def _fm(name: str = "x") -> FunctionMetrics:
    """Minimal FunctionMetrics for list-length-driven grade inputs."""
    return FunctionMetrics(
        node_id="", name=name, module="", kind="function", fan_in=0, fan_out=0, lines=0
    )


@pytest.fixture
def analyzer() -> PyCodeKGAnalyzer:
    """Analyzer stub with a clean slate: full marks everywhere."""
    a = PyCodeKGAnalyzer(kg=SimpleNamespace(repo_root=""))
    a.docstring_coverage = {"coverage_pct": 95.0}
    a._orphan_scan_total = 400
    return a


def test_clean_repo_scores_100(analyzer) -> None:
    """No findings and ≥90% docstrings is a perfect score."""
    score, grade, label = analyzer._compute_quality_grade()
    assert score == 100.0
    assert (grade, label) == ("A", "Excellent")


def test_components_sum_to_score_and_are_stored(analyzer) -> None:
    """The breakdown table's rows always sum to the reported score."""
    analyzer.orphaned_functions = [_fm()] * 4
    analyzer.high_fanout_functions = [_fm()]
    score, _, _ = analyzer._compute_quality_grade()
    components = analyzer.grade_components
    assert len(components) == 4
    assert sum(c["points"] for c in components) == pytest.approx(score)
    assert all(c["points"] <= c["max"] for c in components)


def test_docstring_curve_is_linear_below_90(analyzer) -> None:
    """45% coverage earns exactly half of the docstring points."""
    analyzer.docstring_coverage = {"coverage_pct": 45.0}
    score, _, _ = analyzer._compute_quality_grade()
    assert score == pytest.approx(20.0 + 25.0 + 20.0 + 15.0)


def test_dead_code_is_rate_normalized(analyzer) -> None:
    """The same 4 dead candidates cost less in a bigger codebase."""
    analyzer.orphaned_functions = [_fm()] * 4
    analyzer._orphan_scan_total = 400
    small_repo_score, _, _ = analyzer._compute_quality_grade()
    analyzer._orphan_scan_total = 4000
    big_repo_score, _, _ = analyzer._compute_quality_grade()
    assert big_repo_score > small_repo_score


def test_dead_code_rate_of_five_percent_zeroes_the_component(analyzer) -> None:
    """At ≥5% dead definitions the dead-code component bottoms out at 0."""
    analyzer.orphaned_functions = [_fm()] * 20
    analyzer._orphan_scan_total = 400
    score, _, _ = analyzer._compute_quality_grade()
    assert score == pytest.approx(40.0 + 0.0 + 20.0 + 15.0)


def test_test_covered_orphans_do_not_count(analyzer) -> None:
    """Only dead candidates lower the score; test-covered orphans are free."""
    analyzer.test_covered_orphans = [_fm()] * 30
    score, _, _ = analyzer._compute_quality_grade()
    assert score == 100.0


def test_one_extra_finding_never_moves_a_letter(analyzer) -> None:
    """Smoothness: +1 dead candidate in a 400-definition repo shifts <2 pts."""
    analyzer.orphaned_functions = [_fm()] * 3
    before, _, _ = analyzer._compute_quality_grade()
    analyzer.orphaned_functions = [_fm()] * 4
    after, _, _ = analyzer._compute_quality_grade()
    assert 0 < before - after < 2.0


def test_fanout_and_circular_penalties_are_linear(analyzer) -> None:
    """Each orchestrator costs 4 pts, each cycle 5, floored at zero."""
    analyzer.high_fanout_functions = [_fm()] * 2
    analyzer.circular_deps = [("a", "b")]
    score, _, _ = analyzer._compute_quality_grade()
    assert score == pytest.approx(40.0 + 25.0 + 12.0 + 10.0)
    analyzer.high_fanout_functions = [_fm()] * 10
    analyzer.circular_deps = [("a", "b")] * 10
    score, _, _ = analyzer._compute_quality_grade()
    assert score == pytest.approx(40.0 + 25.0)
