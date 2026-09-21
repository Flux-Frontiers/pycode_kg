"""The pre-commit hook `pycodekg install-hooks` writes resolves `pycodekg` from PATH.

Under the fleet's "tools are global" rule (kgrag_priv sweep item 50) a repo
never depends on `pycodekg`; it is installed once with `uv tool`. The template
therefore looks on PATH first and falls back to a `.venv` copy only if one
exists. Before this, it hard-wired `$REPO_ROOT/.venv/bin/pycodekg` with
`|| exit 1`, the same shape that left `_waverider`'s hooks failing silently
for weeks. There was no test of the template at all.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from click.testing import CliRunner

from pycode_kg.cli.cmd_hooks import _PRE_COMMIT_HOOK, install_hooks


class TestTemplate:
    def test_resolves_pycodekg_from_path_first(self) -> None:
        assert 'PYCODEKG="$(command -v pycodekg 2>/dev/null || true)"' in _PRE_COMMIT_HOOK

    def test_falls_back_to_a_venv_copy_only_if_present(self) -> None:
        assert '[ -n "$PYCODEKG" ] || PYCODEKG="$REPO_ROOT/.venv/bin/pycodekg"' in _PRE_COMMIT_HOOK
        assert '[ -x "$PYCODEKG" ] ||' in _PRE_COMMIT_HOOK

    def test_never_hard_wires_the_venv_path(self) -> None:
        """The defect this guards against: a hook that dies when .venv has no pycodekg."""
        assert '"$REPO_ROOT/.venv/bin/pycodekg" build' not in _PRE_COMMIT_HOOK
        assert '"$REPO_ROOT/.venv/bin/pycodekg" snapshot' not in _PRE_COMMIT_HOOK

    def test_both_invocations_use_the_resolved_binary(self) -> None:
        assert '"$PYCODEKG" build --repo "$REPO_ROOT" || exit 1' in _PRE_COMMIT_HOOK
        assert '"$PYCODEKG" snapshot save' in _PRE_COMMIT_HOOK

    def test_missing_tool_names_the_fix(self) -> None:
        assert "uv tool install pycode-kg" in _PRE_COMMIT_HOOK


class TestInstall:
    def test_writes_an_executable_hook_carrying_the_resolver(self, tmp_path: Path) -> None:
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
        result = CliRunner().invoke(install_hooks, ["--repo", str(tmp_path), "--force"])
        assert result.exit_code == 0, result.output
        hook = tmp_path / ".git" / "hooks" / "pre-commit"
        assert hook.is_file()
        assert os.access(hook, os.X_OK)
        assert "command -v pycodekg" in hook.read_text()

    def test_refuses_a_non_repo(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(install_hooks, ["--repo", str(tmp_path)])
        assert result.exit_code == 1
        assert "not a git repository" in result.output
