"""Tests for :func:`pycode_kg.pycodekg_thorough_analysis._package_root`.

"Public API Surface", "Structural Importance", and CodeRank seeding describe
the installable package, not every top-level directory a repo happens to
contain — a provisioning script under ``runpod/`` is real repo content but
not an API-surface candidate.  These tests pin what counts as the package
root and, just as importantly, when detection gives up rather than guesses.
"""

from types import SimpleNamespace

from pycode_kg.pycodekg_thorough_analysis import PyCodeKGAnalyzer, _package_root


def test_detects_src_layout_from_project_name(tmp_path) -> None:
    """[project].name resolves to a src/<name>/ directory when one exists."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-pkg"\n')
    (tmp_path / "src" / "my_pkg").mkdir(parents=True)
    assert _package_root(tmp_path) == "src/my_pkg/"


def test_detects_flat_layout_from_poetry_name(tmp_path) -> None:
    """[tool.poetry].name is read when [project].name is absent."""
    (tmp_path / "pyproject.toml").write_text('[tool.poetry]\nname = "my-pkg"\n')
    (tmp_path / "my_pkg").mkdir()
    assert _package_root(tmp_path) == "my_pkg/"


def test_normalizes_hyphens_to_underscores(tmp_path) -> None:
    """A hyphenated distribution name maps to its underscored import path."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "gutenberg-kg"\n')
    (tmp_path / "src" / "gutenberg_kg").mkdir(parents=True)
    assert _package_root(tmp_path) == "src/gutenberg_kg/"


def test_prefers_src_layout_when_both_exist(tmp_path) -> None:
    """A src/<name>/ directory wins over a flat <name>/ directory."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-pkg"\n')
    (tmp_path / "src" / "my_pkg").mkdir(parents=True)
    (tmp_path / "my_pkg").mkdir()
    assert _package_root(tmp_path) == "src/my_pkg/"


def test_empty_when_no_pyproject(tmp_path) -> None:
    """A repo without pyproject.toml disables the filter rather than guessing."""
    assert _package_root(tmp_path) == ""


def test_empty_when_name_has_no_matching_directory(tmp_path) -> None:
    """A declared name with neither layout present disables the filter."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-pkg"\n')
    assert _package_root(tmp_path) == ""


def test_empty_on_malformed_pyproject(tmp_path) -> None:
    """Invalid TOML disables the filter instead of raising."""
    (tmp_path / "pyproject.toml").write_text("not valid toml [[[")
    assert _package_root(tmp_path) == ""


def test_analyzer_caches_package_root(tmp_path) -> None:
    """_get_package_root computes once and reuses the cached value."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-pkg"\n')
    (tmp_path / "src" / "my_pkg").mkdir(parents=True)
    analyzer = PyCodeKGAnalyzer(kg=SimpleNamespace(repo_root=str(tmp_path)))
    assert analyzer._get_package_root() == "src/my_pkg/"
    # Delete the directory; a cached result must not re-read the filesystem.
    (tmp_path / "src" / "my_pkg").rmdir()
    assert analyzer._get_package_root() == "src/my_pkg/"
