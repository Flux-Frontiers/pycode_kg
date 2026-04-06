"""
test_exclusions.py

Unit tests for directory include filtering in PyCodeKG.
Tests cover:
- Config loading from pyproject.toml
- iter_python_files() with include parameter
- extract_repo() with include parameter
- CodeGraph with include parameter
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pycode_kg.config import load_include_dirs
from pycode_kg.graph import CodeGraph
from pycode_kg.pycodekg import extract_repo, iter_python_files

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def repo_with_dirs(tmp_path: Path) -> Path:
    """Create a test repo with multiple top-level directories."""
    # Main source
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main(): pass\n")

    # Old code
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "legacy.py").write_text("def legacy(): pass\n")

    # Vendor
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "external.py").write_text("def external(): pass\n")

    # Tests
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass\n")

    return tmp_path


@pytest.fixture
def repo_with_pyproject(tmp_path: Path) -> Path:
    """Create a test repo with pyproject.toml containing [tool.pycodekg].include."""
    # Write pyproject.toml
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""
            [build-system]
            requires = ["poetry-core"]

            [tool.poetry]
            name = "test-pkg"
            version = "0.1.0"

            [tool.pycodekg]
            include = ["src", "lib"]
        """)
    )

    # Create source files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main(): pass\n")

    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "legacy.py").write_text("def legacy(): pass\n")

    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "lib.py").write_text("def lib(): pass\n")

    return tmp_path


# ============================================================================
# Tests: config.load_include_dirs()
# ============================================================================


def test_load_include_dirs_no_pyproject(tmp_path: Path) -> None:
    """Should return empty set if pyproject.toml doesn't exist."""
    result = load_include_dirs(tmp_path)
    assert result == set()


def test_load_include_dirs_no_tool_pycodekg(tmp_path: Path) -> None:
    """Should return empty set if [tool.pycodekg] section doesn't exist."""
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'test'\n")
    result = load_include_dirs(tmp_path)
    assert result == set()


def test_load_include_dirs_no_include_key(tmp_path: Path) -> None:
    """Should return empty set if include key doesn't exist."""
    (tmp_path / "pyproject.toml").write_text("[tool.pycodekg]\nfoo = 'bar'\n")
    result = load_include_dirs(tmp_path)
    assert result == set()


def test_load_include_dirs_single_include(tmp_path: Path) -> None:
    """Should load single include directory."""
    (tmp_path / "pyproject.toml").write_text("[tool.pycodekg]\ninclude = ['src']\n")
    result = load_include_dirs(tmp_path)
    assert result == {"src"}


def test_load_include_dirs_multiple_includes(repo_with_pyproject: Path) -> None:
    """Should load multiple include directories from [tool.pycodekg].include."""
    result = load_include_dirs(repo_with_pyproject)
    assert result == {"src", "lib"}


def test_load_include_dirs_strips_trailing_slashes(tmp_path: Path) -> None:
    """Should strip trailing slashes from directory names."""
    (tmp_path / "pyproject.toml").write_text("[tool.pycodekg]\ninclude = ['src/', 'lib/', 'app']\n")
    result = load_include_dirs(tmp_path)
    assert result == {"src", "lib", "app"}


def test_load_include_dirs_invalid_toml(tmp_path: Path) -> None:
    """Should return empty set if pyproject.toml is invalid TOML."""
    (tmp_path / "pyproject.toml").write_text("this is not valid toml ][")
    result = load_include_dirs(tmp_path)
    assert result == set()


def test_load_include_dirs_non_list_include(tmp_path: Path) -> None:
    """Should return empty set if include is not a list."""
    (tmp_path / "pyproject.toml").write_text("[tool.pycodekg]\ninclude = 'src'\n")
    result = load_include_dirs(tmp_path)
    assert result == set()


# ============================================================================
# Tests: iter_python_files()
# ============================================================================


def test_iter_python_files_no_include(repo_with_dirs: Path) -> None:
    """Without include, should find all .py files in all directories."""
    files = set(iter_python_files(repo_with_dirs))
    names = {f.name for f in files}

    assert "main.py" in names
    assert "legacy.py" in names
    assert "external.py" in names
    assert "test_main.py" in names


def test_iter_python_files_with_include_one_dir(repo_with_dirs: Path) -> None:
    """With include={"src"}, should only return files under src/."""
    files = set(iter_python_files(repo_with_dirs, include={"src"}))
    names = {f.name for f in files}

    assert "main.py" in names
    assert "legacy.py" not in names
    assert "external.py" not in names
    assert "test_main.py" not in names


def test_iter_python_files_with_include_two_dirs(repo_with_dirs: Path) -> None:
    """With include={"src", "old"}, should return files from both directories."""
    files = set(iter_python_files(repo_with_dirs, include={"src", "old"}))
    names = {f.name for f in files}

    assert "main.py" in names
    assert "legacy.py" in names
    assert "external.py" not in names
    assert "test_main.py" not in names


def test_iter_python_files_include_empty_set(repo_with_dirs: Path) -> None:
    """With empty include set, should behave same as no include (all dirs)."""
    files_no_include = set(iter_python_files(repo_with_dirs))
    files_empty_include = set(iter_python_files(repo_with_dirs, include=set()))

    assert files_no_include == files_empty_include


def test_iter_python_files_include_nonexistent_dir(repo_with_dirs: Path) -> None:
    """Including a nonexistent directory should not raise — just skip it."""
    files = set(iter_python_files(repo_with_dirs, include={"src", "doesnotexist"}))
    names = {f.name for f in files}

    assert "main.py" in names
    assert len(files) == 1


# ============================================================================
# Tests: extract_repo()
# ============================================================================


def test_extract_repo_no_include(repo_with_dirs: Path) -> None:
    """Without include, should extract all modules."""
    nodes, _ = extract_repo(repo_with_dirs)
    module_paths = {n.module_path for n in nodes if n.kind == "module"}

    assert any("main.py" in m for m in module_paths)
    assert any("legacy.py" in m for m in module_paths)
    assert any("external.py" in m for m in module_paths)


def test_extract_repo_with_include(repo_with_dirs: Path) -> None:
    """With include={"src"}, should only extract modules under src/."""
    nodes, _ = extract_repo(repo_with_dirs, include={"src"})
    module_paths = {n.module_path for n in nodes if n.kind == "module"}

    assert any("main.py" in m for m in module_paths)
    assert not any("legacy.py" in m for m in module_paths)
    assert not any("external.py" in m for m in module_paths)


def test_extract_repo_include_reduces_node_count(repo_with_dirs: Path) -> None:
    """Including a subset of directories should reduce node count."""
    nodes_full, _ = extract_repo(repo_with_dirs)
    nodes_included, _ = extract_repo(repo_with_dirs, include={"src"})

    assert len(nodes_included) < len(nodes_full)


# ============================================================================
# Tests: CodeGraph
# ============================================================================


def test_codegraph_no_include(repo_with_dirs: Path) -> None:
    """CodeGraph without include should extract all nodes."""
    graph = CodeGraph(repo_with_dirs)
    nodes = graph.nodes

    module_count = sum(1 for n in nodes if n.kind == "module")
    assert module_count == 4  # main.py, legacy.py, external.py, test_main.py


def test_codegraph_with_include(repo_with_dirs: Path) -> None:
    """CodeGraph with include={"src"} should only index src/."""
    graph = CodeGraph(repo_with_dirs, include={"src"})
    nodes = graph.nodes

    module_count = sum(1 for n in nodes if n.kind == "module")
    assert module_count == 1  # main.py only

    module_paths = {n.module_path for n in nodes if n.kind == "module"}
    assert not any("legacy" in m for m in module_paths if m)
    assert not any("external" in m for m in module_paths if m)


def test_codegraph_stores_include(repo_with_dirs: Path) -> None:
    """CodeGraph should store include set for later use."""
    include = {"src", "old"}
    graph = CodeGraph(repo_with_dirs, include=include)

    assert graph.include == include


def test_codegraph_result_respects_include(repo_with_dirs: Path) -> None:
    """CodeGraph.result() should respect include parameter."""
    graph = CodeGraph(repo_with_dirs, include={"src", "old"})
    nodes, _ = graph.result()

    module_paths = {n.module_path for n in nodes if n.kind == "module"}
    assert len(module_paths) == 2


# ============================================================================
# Integration Tests
# ============================================================================


def test_integration_pyproject_config(repo_with_pyproject: Path) -> None:
    """Integration: load include from pyproject.toml and use in CodeGraph."""
    include = load_include_dirs(repo_with_pyproject)
    # pyproject has include = ["src", "lib"]; only src/ exists in the fixture
    graph = CodeGraph(repo_with_pyproject, include=include if include else None)

    nodes = graph.nodes
    module_paths = {n.module_path for n in nodes if n.kind == "module"}

    # Should only have src/main.py (old/ and vendor/ not in include list)
    assert any("main.py" in m for m in module_paths if m)
    assert not any("legacy" in m for m in module_paths if m)
    assert not any("lib.py" in m for m in module_paths if m)


def test_integration_cli_augments_config(repo_with_pyproject: Path) -> None:
    """Integration: CLI include dirs should merge with config include dirs."""
    config_include = load_include_dirs(repo_with_pyproject)  # {"src", "lib"}
    cli_include = {"old"}  # Additional directory from CLI

    # Merge: CLI flags augment config
    final_include = config_include | cli_include

    graph = CodeGraph(repo_with_pyproject, include=final_include if final_include else None)
    nodes = graph.nodes

    module_paths = {n.module_path for n in nodes if n.kind == "module"}

    # Should have src/main.py and old/legacy.py; vendor/ excluded
    assert any("main.py" in m for m in module_paths if m)
    assert any("legacy" in m for m in module_paths if m)
    assert not any("lib.py" in m for m in module_paths if m)


def test_codegraph_force_reextract_respects_include(repo_with_dirs: Path) -> None:
    """CodeGraph.extract(force=True) should still respect include."""
    graph = CodeGraph(repo_with_dirs, include={"src"})

    # First extract
    nodes1 = graph.nodes
    count1 = sum(1 for n in nodes1 if n.kind == "module")

    # Force re-extract
    graph.extract(force=True)
    nodes2 = graph.nodes
    count2 = sum(1 for n in nodes2 if n.kind == "module")

    assert count1 == count2 == 1
