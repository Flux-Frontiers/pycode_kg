"""The CLI build commands record each source file's hash (fleet sweep item 97).

``pycodekg build``, ``update`` and ``build-sqlite`` write the graph store
directly instead of going through ``KGModule.build_graph``, so they must call
``GraphStore.record_sources`` themselves. Without it the store is unrecorded and
``pack()`` cannot tell when a source file changed since the build.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from pycode_kg.cli.main import cli
from pycode_kg.kg import PyCodeKG
from pycode_kg.store import GraphStore

_FILES = {
    "pkg/__init__.py": "",
    "pkg/core.py": "def core():\n    return 1\n",
    "pkg/main.py": "from pkg.core import core\n\ndef main():\n    return core()\n",
}


def _make_repo(root: Path) -> Path:
    for rel, src in _FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(src))
    return root


def _recorded(repo: Path) -> dict[str, str] | None:
    with GraphStore(repo / ".pycodekg" / "graph.sqlite") as store:
        return store.source_hashes()


@pytest.mark.parametrize("command", ["build-sqlite", "build", "update"])
def test_cli_build_records_every_source_file(tmp_path: Path, command: str) -> None:
    repo = _make_repo(tmp_path / "repo")
    result = CliRunner().invoke(cli, [command, "--repo", str(repo)])
    assert result.exit_code == 0, result.output
    recorded = _recorded(repo)
    assert recorded is not None
    assert set(recorded) == set(_FILES)


def test_an_edit_after_a_cli_build_is_reported_stale(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path / "repo")
    result = CliRunner().invoke(cli, ["build", "--repo", str(repo)])
    assert result.exit_code == 0, result.output
    kg = PyCodeKG(repo)
    assert kg.stale_sources() == {}
    (repo / "pkg" / "core.py").write_text("# new first line\ndef core():\n    return 1\n")
    assert kg.stale_sources() == {"pkg/core.py": "changed"}
    pack = kg.pack("core function", k=4, max_nodes=None)
    assert not any(n.get("snippet") for n in pack.nodes if n.get("module_path") == "pkg/core.py")
    assert any("`pkg/core.py` changed since the graph was built" in w for w in pack.warnings)
    kg.close()
