"""Tests for the index-freshness warning in :meth:`PyCodeKGAnalyzer._get_report_metadata`.

The graph indexes on-disk file contents at build time, not git state, so it
cannot record "built at commit X" directly. A dirty working tree at report
time is the cheap, always-available signal that the index may have drifted
from current file contents (round 2's own audit was thrown off by exactly
this: orphan-table line numbers were off by roughly 100 lines because the
tree had moved on since the last build).
"""

from types import SimpleNamespace
from unittest.mock import patch

from pycode_kg.pycodekg_thorough_analysis import PyCodeKGAnalyzer


def _analyzer(tmp_path) -> PyCodeKGAnalyzer:
    return PyCodeKGAnalyzer(kg=SimpleNamespace(repo_root=str(tmp_path)))


def _run_result(returncode: int, stdout: str) -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=stdout)


def test_clean_working_tree_reports_ok(tmp_path) -> None:
    """An empty `git status --porcelain` renders the clean-tree line."""
    analyzer = _analyzer(tmp_path)
    with patch(
        "pycode_kg.pycodekg_thorough_analysis.subprocess.run",
        return_value=_run_result(0, ""),
    ):
        metadata = analyzer._get_report_metadata()
    assert "**Index freshness:** [OK] working tree clean" in metadata


def test_dirty_working_tree_warns_with_count(tmp_path) -> None:
    """Uncommitted changes render a [WARN] line naming the count."""
    analyzer = _analyzer(tmp_path)
    dirty_status = " M src/pkg/a.py\n?? src/pkg/b.py\n"
    with patch(
        "pycode_kg.pycodekg_thorough_analysis.subprocess.run",
        return_value=_run_result(0, dirty_status),
    ):
        metadata = analyzer._get_report_metadata()
    assert "**Index freshness:** [WARN] 2 uncommitted change(s)" in metadata


def test_non_git_repo_reports_unknown(tmp_path) -> None:
    """A failing git invocation (not a repo, git missing) degrades to 'unknown'."""
    analyzer = _analyzer(tmp_path)
    with patch(
        "pycode_kg.pycodekg_thorough_analysis.subprocess.run",
        side_effect=FileNotFoundError,
    ):
        metadata = analyzer._get_report_metadata()
    assert "**Index freshness:** unknown" in metadata
