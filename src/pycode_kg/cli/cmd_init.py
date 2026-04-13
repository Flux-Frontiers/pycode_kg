"""
cmd_init.py

CLI command for initializing PyCodeKG in a repository:

  init — download model, build graph, install hooks, capture snapshot

  Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import stat
import subprocess
import time
import tomllib
from pathlib import Path

import click

from pycode_kg.cli.main import cli
from pycode_kg.cli.options import (
    exclude_option,
    include_option,
    model_option,
    repo_option,
)
from pycode_kg.index import _local_model_path


def _has_pycodekg_config(repo_root: Path) -> bool:
    """Check whether pyproject.toml already has a [tool.pycodekg] section."""
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return False
    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return "pycodekg" in data.get("tool", {})
    except (OSError, ValueError):
        return False


def _scaffold_pycodekg_config(repo_root: Path) -> bool:
    """Append a minimal [tool.pycodekg] section to pyproject.toml if missing.

    Detects the most likely source directory (``src``, ``lib``, or the
    project name) and sets it as the include list.

    :param repo_root: Repository root directory.
    :return: True if the section was added, False if skipped.
    """
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return False

    # Guess the best include directory
    candidates = ["src", "lib"]
    include_dirs: list[str] = [d for d in candidates if (repo_root / d).is_dir()]

    if not include_dirs:
        # Fall back to the repo name itself if it's a directory
        repo_name = repo_root.name.replace("-", "_")
        if (repo_root / repo_name).is_dir():
            include_dirs = [repo_name]

    lines = [
        "",
        "[tool.pycodekg]",
        "# Directories to include in the knowledge graph build and analysis.",
        "# When unset, all directories are indexed.",
    ]
    if include_dirs:
        include_str = ", ".join(f'"{d}"' for d in include_dirs)
        lines.append(f"include = [{include_str}]")
    else:
        lines.append("# include = []")

    pyproject.open("a").write("\n".join(lines) + "\n")
    return True


@cli.command("init")
@repo_option
@model_option
@include_option
@exclude_option
@click.option("--skip-hooks", is_flag=True, help="Don't install the pre-commit git hook.")
@click.option("--skip-snapshot", is_flag=True, help="Don't capture an initial snapshot.")
@click.option("--force", is_flag=True, help="Overwrite existing graph data and hook.")
@click.option("-v", "--verbose", is_flag=True, help="Show progress details.")
def init(
    repo: str,
    model: str,
    include_dir: tuple[str, ...],
    exclude_dir: tuple[str, ...],
    skip_hooks: bool,
    skip_snapshot: bool,
    force: bool,
    verbose: bool,
) -> None:
    """Initialize PyCodeKG in a repository.

    Downloads the embedding model, builds the knowledge graph (SQLite +
    LanceDB), optionally installs the pre-commit hook, and captures an
    initial snapshot.  Designed to be idempotent — safe to run more than once.

    Example::

        pycodekg init --repo .
    """
    from pycode_kg.cli.cmd_build_full import (
        _run_pipeline,  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
    )
    from pycode_kg.cli.cmd_hooks import (
        _PRE_COMMIT_HOOK,  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
    )

    repo_root = Path(repo).resolve()
    t_total = time.monotonic()

    click.echo()
    click.echo("  PyCodeKG  Init")
    click.echo(f"  repo  {repo_root}")
    click.echo()

    # ------------------------------------------------------------------
    # Step 0: Scaffold [tool.pycodekg] in pyproject.toml if missing
    # ------------------------------------------------------------------
    if not _has_pycodekg_config(repo_root):
        if _scaffold_pycodekg_config(repo_root):
            click.echo("  [0/4]  Added [tool.pycodekg] section to pyproject.toml")
        else:
            click.echo("  [0/4]  No pyproject.toml found — skipping config scaffold")
    else:
        click.echo("  [0/4]  [tool.pycodekg] config already present")

    # ------------------------------------------------------------------
    # Step 1: Download the embedding model
    # ------------------------------------------------------------------
    click.echo()
    local_path = _local_model_path(model)

    if local_path.exists() and not force:
        click.echo(f"  [1/4]  Model already cached at {local_path}")
    else:
        click.echo(f"  [1/4]  Downloading embedding model '{model}'...")
        from sentence_transformers import (  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
            SentenceTransformer,
        )

        st_model = SentenceTransformer(model)
        local_path.mkdir(parents=True, exist_ok=True)
        st_model.save(str(local_path))
        click.echo(f"         OK: model saved to {local_path}")

    # ------------------------------------------------------------------
    # Step 2: Build the knowledge graph (full wipe)
    # ------------------------------------------------------------------
    click.echo()
    click.echo("  [2/4]  Building knowledge graph...")
    _run_pipeline(
        repo=repo,
        db=None,
        lancedb=None,
        table="pycodekg_nodes",
        model=model,
        verbose=verbose,
        kinds="module,class,function,method",
        batch=256,
        include_dir=include_dir,
        exclude_dir=exclude_dir,
        wipe=True,
        label="Init Build",
    )

    # ------------------------------------------------------------------
    # Step 3: Install pre-commit hook
    # ------------------------------------------------------------------
    click.echo()
    if skip_hooks:
        click.echo("  [3/4]  Skipping hook installation (--skip-hooks)")
    else:
        git_dir = repo_root / ".git"
        if not git_dir.is_dir():
            click.echo("  [3/4]  Not a git repository — skipping hook installation")
        else:
            hooks_dir = git_dir / "hooks"
            hooks_dir.mkdir(exist_ok=True)
            hook_path = hooks_dir / "pre-commit"

            if hook_path.exists() and not force:
                click.echo(f"  [3/4]  Hook already exists: {hook_path}")
                click.echo("         Use --force to overwrite.")
            else:
                hook_path.write_text(_PRE_COMMIT_HOOK)
                mode = hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                hook_path.chmod(mode)
                click.echo(f"  [3/4]  OK: installed pre-commit hook at {hook_path}")

    # ------------------------------------------------------------------
    # Step 4: Capture initial snapshot
    # ------------------------------------------------------------------
    click.echo()
    if skip_snapshot:
        click.echo("  [4/4]  Skipping initial snapshot (--skip-snapshot)")
    else:
        try:
            tree_hash = (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    cwd=str(repo_root),
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
            branch = (
                subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=str(repo_root),
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            tree_hash = ""
            branch = "unknown"

        try:
            import importlib.metadata  # noqa: PLC0415  # pylint: disable=import-outside-toplevel

            from pycode_kg.kg import (
                PyCodeKG,  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
            )
            from pycode_kg.pycodekg_thorough_analysis import (
                PyCodeKGAnalyzer,  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
            )
            from pycode_kg.snapshots import (
                SnapshotManager,  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
            )
            from pycode_kg.store import (
                GraphStore,  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
            )

            db_path = repo_root / ".pycodekg" / "graph.sqlite"
            snapshots_path = repo_root / ".pycodekg" / "snapshots"
            lancedb_dir = repo_root / ".pycodekg" / "lancedb"

            store = GraphStore(db_path)
            try:
                stats = store.stats()
            finally:
                store.close()

            kg = PyCodeKG(
                repo_root=repo_root,
                db_path=db_path,
                lancedb_dir=lancedb_dir,
                model=model,
            )
            snap_mgr = SnapshotManager(snapshots_path, db_path=db_path)
            try:
                analyzer = PyCodeKGAnalyzer(kg, snapshot_mgr=snap_mgr)
                analysis = analyzer.run_analysis()

                docstring_cov = analysis.get("docstring_coverage", {})
                coverage = docstring_cov.get("coverage_pct", 0.0) / 100.0 if docstring_cov else 0.0
                critical_issues = len(analysis.get("issues", []))

                fn_metrics = analysis.get("function_metrics", {})
                hotspots = [
                    {
                        "name": name,
                        "callers": m.get("fan_in", 0),
                        "callees": m.get("fan_out", 0),
                        "risk_level": m.get("risk_level", "low"),
                    }
                    for name, m in list(fn_metrics.items())[:10]
                ]
                fan_ins = [m.get("fan_in", 0) for m in fn_metrics.values()]
                complexity_median = sorted(fan_ins)[len(fan_ins) // 2] if fan_ins else 0.0
            finally:
                kg.close()

            version = importlib.metadata.version("pycode-kg")
            snapshot_obj = snap_mgr.capture(
                version=version,
                branch=branch,
                graph_stats_dict=stats,
                coverage=coverage,
                critical_issues=critical_issues,
                complexity_median=complexity_median,
                hotspots=hotspots,
                issues=analysis.get("issues", []),
                tree_hash=tree_hash,
            )
            snap_mgr.save_snapshot(snapshot_obj)
            click.echo(f"  [4/4]  OK: snapshot saved (key={snapshot_obj.key[:12]})")
        except Exception as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            click.echo(f"  [4/4]  Snapshot skipped: {exc}", err=True)

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    elapsed = time.monotonic() - t_total
    click.echo()
    click.echo(f"  Done ({elapsed:.1f}s)")
    click.echo()
    click.echo("  Run 'pycodekg query \"your question\"' to search the codebase.")
    click.echo()
