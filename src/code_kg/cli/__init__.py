"""
code_kg.cli — Click-based CLI entry points.

Public API
----------
The root Click group is importable from either location::

    from code_kg.cli import cli
    from code_kg.cli.main import cli
"""

from code_kg.cli import (  # noqa: F401  — registers snapshot (save, list, show, diff)
    cmd_analyze,  # noqa: F401  — registers analyze
    cmd_architecture,  # noqa: F401  — registers architecture
    cmd_build,  # noqa: F401  — registers build-sqlite, build-lancedb
    cmd_build_full,  # noqa: F401  — registers build (full pipeline), update (incremental upsert)
    cmd_centrality,  # noqa: F401  — registers centrality
    cmd_explain,  # noqa: F401  — registers explain
    cmd_hooks,  # noqa: F401  — registers install-hooks
    cmd_mcp,  # noqa: F401  — registers mcp
    cmd_model,  # noqa: F401  — registers download-model
    cmd_query,  # noqa: F401  — registers query, pack
    cmd_snapshot,
    cmd_viz,  # noqa: F401  — registers viz, viz3d, viz-timeline
)
from code_kg.cli.main import cli

__all__ = ["cli"]
