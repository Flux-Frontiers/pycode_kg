"""
cmd_hooks.py

CLI command for installing PyCodeKG git hooks:

  install-hooks — install the pre-commit snapshot hook into .git/hooks/

  Author: Eric G. Suchanek, PhD
  Last Revision: 2026-08-11 19:32:52
"""

from __future__ import annotations

import stat
from pathlib import Path

import click

from pycode_kg.cli.main import cli

# ---------------------------------------------------------------------------
# Hook script content (embedded so this module is self-contained when
# installed as a package in any repo, not just pycode_kg itself)
# ---------------------------------------------------------------------------

_PRE_COMMIT_HOOK = """\
#!/usr/bin/env bash
# PyCodeKG pre-commit hook — runs quality checks first, then rebuilds the local
# index and captures a metrics snapshot.
# Installed by: pycodekg install-hooks
# Skip with: PYCODEKG_SKIP_SNAPSHOT=1 git commit ...
#
# Order matters, and it is deliberately checks-then-index:
#
#   * `pre-commit run` stashes unstaged changes and restores them afterwards.
#     Rebuilding the index before that ran meant the build's freshly-rewritten
#     snapshots/manifest.json landed inside the stash window, where the restore
#     could fail with "patch does not apply" and abort the commit outright — or,
#     worse, let a staged deletion of a tracked snapshot slip into the commit.
#     Building afterwards keeps KG artifacts entirely outside that window.
#   * A full index rebuild costs 60-90s. There is no reason to pay it for a
#     commit that ruff/ty/pytest is about to reject.
set -euo pipefail

[ "${PYCODEKG_SKIP_SNAPSHOT:-0}" = "1" ] && exit 0

REPO_ROOT="$(git rev-parse --show-toplevel)"

cd "$REPO_ROOT"

# Quality checks first (ruff, ty, pytest, detect-secrets, ...). Delegates to
# .pre-commit-config.yaml so quality checks stay in one place. A hook that
# rewrites files also exits non-zero here, so we never index a tree that is
# about to be reformatted.
PRECOMMIT="$REPO_ROOT/.venv/bin/pre-commit"
if [ -x "$PRECOMMIT" ]; then
    "$PRECOMMIT" run || exit 1
elif command -v pre-commit &>/dev/null; then
    pre-commit run || exit 1
fi

# Capture the tree hash now that the checks have passed and nothing further
# will modify the working tree — this keys the snapshot to the content that is
# actually about to be committed.
TREE_HASH=$(git write-tree)
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Rebuild the local index to keep it in sync with staged content.
"$REPO_ROOT/.venv/bin/pycodekg" build --repo "$REPO_ROOT" || exit 1

# Snapshot PyCodeKG (version auto-detected from installed package).
"$REPO_ROOT/.venv/bin/pycodekg" snapshot save \\
    --repo . \\
    --tree-hash "$TREE_HASH" \\
    --branch "$BRANCH" \\
  || { echo "[pycodekg] snapshot skipped (run 'pycodekg build' to initialize)" >&2; }

# Stage the snapshot directory so it is included in the commit. These files are
# added after `pre-commit run`, so they are not scanned by it — detect-secrets
# already excludes snapshots/ by config, which is why that is safe.
git add .pycodekg/snapshots/ 2>/dev/null || true

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
    """Install the PyCodeKG pre-commit git hook.

    After installation, before each commit:
      1. Rebuilds the local PyCodeKG index (full wipe)
      2. Captures a metrics snapshot, keyed by tree hash
      3. Stages the snapshot directory

    This keeps the index in sync and ensures snapshots reflect the state of
    the knowledge graph at commit time.  The hook only ever touches its own
    repository — sibling KG repos install their own hooks.

    Example:
        pycodekg install-hooks --repo .
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
    click.echo("  Run 'pycodekg build' first if you haven't built the graph yet.")
