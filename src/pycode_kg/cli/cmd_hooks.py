"""
cmd_hooks.py

CLI command for installing PyCodeKG git hooks:

  install-hooks — install the pre-commit snapshot hook into .git/hooks/

  Author: Eric G. Suchanek, PhD
  Last Revision: 2026-08-14 22:51:58

Author: Eric G. Suchanek, PhD

License: Elastic 2.0
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
# PyCodeKG pre-commit hook — runs quality checks. The index rebuild and metrics
# snapshot are opt-in and OFF by default; see "Why snapshots are off" below.
# Installed by: pycodekg install-hooks
#
#   PYCODEKG_SNAPSHOT=1 git commit ...        opt in to a per-commit snapshot
#   PYCODEKG_SKIP_SNAPSHOT=1 git commit ...   force snapshots off (wins)
#
# Note that PYCODEKG_SKIP_SNAPSHOT no longer skips the quality checks. It used
# to short-circuit the whole hook, so a variable named "skip snapshot" also
# silently skipped ruff, ty and pytest. It now gates only what it names.
#
# Why snapshots are off by default (2026-08-18)
# ---------------------------------------------
# A per-commit snapshot records `git write-tree` and is then itself staged into
# that same commit. Staging changes the index, so the recorded hash can never
# equal the tree it claims to describe — and manifest.json carries a
# `last_update` timestamp, so the `git add` is never a no-op. The drift is
# guaranteed by construction, not caused by formatting, and reordering does not
# fix it: the `git add` lands after the hash either way.
#
# An audit of 605 snapshots across 29 fleet manifests found 63 (10.4%) keyed to
# a tree any commit actually has. `snapshot diff` between adjacent entries has
# therefore been comparing states that never existed.
#
# The fix is to snapshot at release, keyed on the tag rather than on an
# ephemeral pre-commit tree. See kgrag_priv/docs/SNAPSHOT_STRATEGY.md. Until
# that lands, this hook runs quality checks only.
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

# ---------------------------------------------------------------------------
# Opt-in index rebuild + snapshot. Everything below is skipped unless
# PYCODEKG_SNAPSHOT=1 is set, and is skipped regardless if
# PYCODEKG_SKIP_SNAPSHOT=1.
# ---------------------------------------------------------------------------
[ "${PYCODEKG_SNAPSHOT:-0}" = "1" ] || exit 0
[ "${PYCODEKG_SKIP_SNAPSHOT:-0}" = "1" ] && exit 0

# Captured after the checks so nothing further modifies the working tree. Note
# the caveat above: this still cannot match the committed tree, because the
# `git add` below changes the index after this point.
TREE_HASH=$(git write-tree)
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Snapshots are default-branch history. On any other branch, stop here —
# feature-branch commits (and the PRs/CI built from them) stay free of
# generated snapshot files, and skip the 60-90s rebuild along the way.
DEFAULT_BRANCH=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || true)
DEFAULT_BRANCH="${DEFAULT_BRANCH#origin/}"
[ "$BRANCH" != "${DEFAULT_BRANCH:-main}" ] && exit 0

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

    After installation, before each commit on the default branch:
      1. Rebuilds the local PyCodeKG index (full wipe)
      2. Captures a metrics snapshot, keyed by tree hash
      3. Stages the snapshot directory

    On any other branch the quality checks still run but the rebuild and
    snapshot are skipped, so feature-branch commits carry no generated files.

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
    click.echo("  Quality checks run on every commit.")
    click.echo("  Snapshots are OFF by default - see kgrag_priv/docs/SNAPSHOT_STRATEGY.md.")
    click.echo("  Opt in with:  PYCODEKG_SNAPSHOT=1 git commit ...")
    click.echo("  Force off:    PYCODEKG_SKIP_SNAPSHOT=1 git commit ...")
    click.echo("  Run 'pycodekg build' first if you haven't built the graph yet.")
