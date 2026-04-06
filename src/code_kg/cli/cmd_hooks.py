"""
cmd_hooks.py

CLI command for installing CodeKG git hooks:

  install-hooks — install the pre-commit snapshot hook into .git/hooks/

  Author: Eric G. Suchanek, PhD
  Last Revision: 2026-03-08 21:30:55
"""

from __future__ import annotations

import stat
from pathlib import Path

import click

from code_kg.cli.main import cli

# ---------------------------------------------------------------------------
# Hook script content (embedded so this module is self-contained when
# installed as a package in any repo, not just code_kg itself)
# ---------------------------------------------------------------------------

_PRE_COMMIT_HOOK = """\
#!/usr/bin/env bash
# CodeKG + DocKG pre-commit hook — keeps local indices in sync and captures
# metrics snapshots BEFORE quality checks run.
# Installed by: codekg install-hooks
# Skip with: CODEKG_SKIP_SNAPSHOT=1 git commit ...
set -euo pipefail

[ "${CODEKG_SKIP_SNAPSHOT:-0}" = "1" ] && exit 0

REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
DOCKG_REPO="${WORKSPACE_ROOT}/doc_kg"

cd "$REPO_ROOT"

# Capture the tree hash of the staged index NOW — before any tool modifies files.
TREE_HASH=$(git write-tree)
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Rebuild both local indices to keep them in sync with staged content.
"$REPO_ROOT/.venv/bin/codekg" build --repo "$REPO_ROOT" || exit 1
if [ -d "$DOCKG_REPO" ]; then
    "$REPO_ROOT/.venv/bin/dockg" build --repo "$DOCKG_REPO" --wipe || true
fi

# Snapshot CodeKG (version auto-detected from installed package).
"$REPO_ROOT/.venv/bin/codekg" snapshot save \\
    --repo . \\
    --tree-hash "$TREE_HASH" \\
    --branch "$BRANCH" \\
  || { echo "[codekg] snapshot skipped (run 'codekg build' to initialize)" >&2; }

# Snapshot DocKG if available (version auto-detected from installed package).
if [ -d "$DOCKG_REPO/.dockg" ]; then
    (cd "$DOCKG_REPO" && "$REPO_ROOT/.venv/bin/dockg" snapshot save \\
        --repo . \\
        --tree-hash "$TREE_HASH" \\
        --branch "$BRANCH") || true
fi

# Stage both snapshot directories so they are included in the commit.
git add .codekg/snapshots/ 2>/dev/null || true
if [ -d "$DOCKG_REPO" ]; then
    (cd "$DOCKG_REPO" && git add .dockg/snapshots/ 2>/dev/null || true)
fi

# Run pre-commit framework checks (ruff, mypy, detect-secrets, etc.) AFTER
# snapshots are captured and staged. Delegates to .pre-commit-config.yaml so
# quality checks stay in one place.
PRECOMMIT="$REPO_ROOT/.venv/bin/pre-commit"
if [ -x "$PRECOMMIT" ]; then
    "$PRECOMMIT" run || exit 1
elif command -v pre-commit &>/dev/null; then
    pre-commit run || exit 1
fi

exit 0
"""


@cli.command("install-hooks")
@click.option(
    "--repo",
    default=".",
    type=click.Path(exists=True),
    show_default=True,
    help="Repository root.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite an existing pre-commit hook.",
)
def install_hooks(repo: str, force: bool) -> None:
    """Install the CodeKG pre-commit git hook.

    After installation, before each commit:
      1. Rebuilds local CodeKG index (full wipe)
      2. Rebuilds local DocKG index if available (full wipe)
      3. Captures metrics snapshots for both KGs, keyed by tree hash
      4. Stages both snapshot directories atomically

    This keeps CodeKG and DocKG indices in sync and ensures snapshots
    reflect the current state of both knowledge graphs at commit time.

    Example:
        codekg install-hooks --repo .
    """
    repo_root = Path(repo).resolve()
    git_dir = repo_root / ".git"

    if not git_dir.is_dir():
        click.echo(f"Error: {repo_root} is not a git repository.", err=True)
        raise SystemExit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    if hook_path.exists() and not force:
        click.echo(f"Hook already exists: {hook_path}")
        click.echo("Use --force to overwrite.")
        raise SystemExit(1)

    hook_path.write_text(_PRE_COMMIT_HOOK)
    mode = hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    hook_path.chmod(mode)

    click.echo(f"OK Installed pre-commit hook: {hook_path}")
    click.echo("  Snapshots will be captured automatically before each commit.")
    click.echo("  Run 'codekg build' first if you haven't built the graph yet.")
