"""
cmd_quilt.py

Click subcommand for holographic output:

  quilt — grow the repository as a tree and render it as a Looking Glass
          light-field quilt (or a turntable quilt video).

The quilt geometry — the off-axis frustum per view, the tiling convention and
the filename suffix Looking Glass software parses — all lives in
:mod:`quiltwright`.  What this command owns is the part quiltwright cannot
know: which graph to grow, how to frame it, and what the depth budget of the
result is.

Author: Eric G. Suchanek, PhD
Last Revision: 2026-08-14

License: Elastic 2.0
"""

from __future__ import annotations

import math
from pathlib import Path

import click

from pycode_kg.cli.main import cli

_VIZ3D_EXTRA = 'pip install "pycode-kg[viz3d]"'


def _depth_report(plotter, spec) -> str:
    """Disparity report for the framed subject, printed before every render.

    Projects the scene's bounding box onto the view axis to get near and far
    depths, then hands them to quiltwright's budget formatter.  Numbers above
    roughly 5 px read soft; past ~8 px expect visible ghosting.

    :param plotter: The framed plotter.
    :param spec: Quilt specification.
    :return: Multi-line report.
    """
    import numpy as np  # noqa: PLC0415
    from quiltwright.povray import PovCamera, format_depth_budget  # noqa: PLC0415

    camera = plotter.camera
    pos = np.asarray(camera.position, dtype=float)
    focal = np.asarray(camera.focal_point, dtype=float)
    forward = focal - pos
    distance = float(np.linalg.norm(forward))
    forward = forward / max(distance, 1e-9)

    xmin, xmax, ymin, ymax, zmin, zmax = plotter.bounds
    corners = np.array(
        [[x, y, z] for x in (xmin, xmax) for y in (ymin, ymax) for z in (zmin, zmax)],
        dtype=float,
    )
    along = (corners - pos) @ forward

    pov_cam = PovCamera(
        location=tuple(pos),
        look_at=tuple(focal),
        sky=(0.0, 0.0, 1.0),
        fov=camera.view_angle,
    )
    return format_depth_budget(
        spec,
        pov_cam,
        {
            "nearest foliage": float(along.min()),
            "focal plane (display surface)": distance,
            "farthest foliage": float(along.max()),
            "sky": math.inf,
        },
    )


def _frame_tree(plotter) -> None:
    """Point the camera level at the tree, focal plane through mid-canopy.

    Putting the focal point at the bounding-box centre makes the crown
    *straddle* the display surface — half the depth budget in front of the
    glass, half behind — which is what a light-field panel fuses best.

    :param plotter: Plotter with the scene already composed.
    """
    xmin, xmax, ymin, ymax, zmin, zmax = plotter.bounds
    centre = ((xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2)
    plotter.camera.up = (0.0, 0.0, 1.0)
    plotter.camera.focal_point = centre
    plotter.camera.position = (centre[0], ymin - (zmax - zmin) * 1.5, centre[2])
    plotter.reset_camera()


@cli.command("quilt")
@click.option(
    "--db",
    default=".pycodekg/graph.sqlite",
    show_default=True,
    help="SQLite database path.",
)
@click.option(
    "--spec",
    default="16-landscape",
    show_default=True,
    help="Looking Glass quilt preset (see quiltwright's QUILT_PRESETS).",
)
@click.option(
    "--out",
    default="renders/quilts",
    show_default=True,
    type=click.Path(file_okay=False),
    help="Output directory.",
)
@click.option(
    "--name",
    default="",
    help="Output filename stem (default: the repository directory name).",
)
@click.option(
    "--leaf-size",
    type=float,
    default=0.55,
    show_default=True,
    help="Leaf radius before density scaling.",
)
@click.option(
    "--tip-radius",
    type=float,
    default=0.14,
    show_default=True,
    help="Radius of leaf-bearing twigs; sets how heavy the whole tree looks.",
)
@click.option(
    "--zoom",
    type=float,
    default=1.0,
    show_default=True,
    help="Camera dolly after framing. Above 1 fills more of each tile, which is what drives perceived depth.",
)
@click.option(
    "--fov",
    type=float,
    default=14.0,
    show_default=True,
    help="Vertical field of view per view, in degrees.",
)
@click.option(
    "--orbit",
    type=int,
    default=0,
    show_default=True,
    help="Frame count for a turntable quilt video. 0 renders a still.",
)
@click.option(
    "--fps",
    type=int,
    default=24,
    show_default=True,
    help="Frame rate for --orbit.",
)
@click.option(
    "--preview/--no-preview",
    default=True,
    show_default=True,
    help="Also write the centre view as a flat PNG for viewing on a normal screen.",
)
@click.option(
    "--cast",
    is_flag=True,
    help="Send the finished quilt to a Looking Glass display via Bridge.",
)
def quilt(  # noqa: PLR0913 - one option per knob, by design
    db: str,
    spec: str,
    out: str,
    name: str,
    leaf_size: float,
    tip_radius: float,
    zoom: float,
    fov: float,
    orbit: int,
    fps: int,
    preview: bool,
    cast: bool,
) -> None:
    """Grow the repository as a tree and render it as a Looking Glass quilt."""
    db_path = Path(db)
    if not db_path.exists():
        raise click.UsageError(
            f"Database not found: {db_path}\nRun 'pycodekg build' first to index your repository."
        )

    try:
        import pyvista as pv  # noqa: PLC0415
        from quiltwright import (  # noqa: PLC0415
            QUILT_PRESETS,
            render_quilt,
            render_quilt_video,
            save_quilt,
        )
    except ImportError as exc:  # pragma: no cover - depends on the install
        raise click.ClickException(
            f"The quilt command needs the viz3d extra.\nInstall with:  {_VIZ3D_EXTRA}"
        ) from exc

    if spec not in QUILT_PRESETS:
        valid = ", ".join(sorted(QUILT_PRESETS))
        raise click.ClickException(f"Unknown quilt spec {spec!r}. Valid presets: {valid}")
    quilt_spec = QUILT_PRESETS[spec]

    from pycode_kg.layout3d import LayoutEdge, LayoutNode  # noqa: PLC0415
    from pycode_kg.scene3d import build_code_tree_scene  # noqa: PLC0415
    from pycode_kg.store import GraphStore  # noqa: PLC0415

    with GraphStore(db_path) as store:
        raw_nodes = store.query_nodes()
        raw_edges = store.edges_within({n["id"] for n in raw_nodes})
    nodes = [LayoutNode.from_dict(n) for n in raw_nodes]
    edges = [LayoutEdge.from_dict(e) for e in raw_edges]

    # Resolve first: for a relative ".pycodekg/graph.sqlite" the grandparent is
    # ".", whose name is empty — which would silently seed the RNG with "" and
    # write a quilt called ".png".
    resolved = db_path.resolve()
    repo_name = (
        resolved.parent.parent.name if resolved.parent.name == ".pycodekg" else resolved.stem
    )
    stem = name or repo_name or "repository"

    click.echo(f"Growing {repo_name} ({len(nodes)} nodes)...")
    plotter = pv.Plotter(off_screen=True)
    try:
        scene = build_code_tree_scene(
            nodes,
            edges,
            plotter,
            key=repo_name,
            leaf_size=leaf_size,
            tip_radius=tip_radius,
        )
        click.echo(
            f"  {scene.n_modules} module limbs, {scene.n_leaves} leaves, "
            f"trunk {scene.trunk_height:.1f} units, "
            f"{scene.skeleton.n_nodes} skeleton nodes"
        )

        _frame_tree(plotter)
        click.echo(_depth_report(plotter, quilt_spec))

        out_dir = Path(out)
        out_dir.mkdir(parents=True, exist_ok=True)

        if orbit > 0:
            click.echo(f"Rendering {orbit}-frame turntable at {quilt_spec.n_views} views/frame...")
            written = render_quilt_video(
                plotter,
                quilt_spec,
                out_dir / stem,
                n_frames=orbit,
                fps=fps,
                fov=fov,
                zoom=zoom,
            )
        else:
            click.echo(f"Rendering {quilt_spec.n_views} views at {spec}...")
            image = render_quilt(plotter, quilt_spec, fov=fov, zoom=zoom)
            written = save_quilt(image, out_dir / stem, quilt_spec)

            if preview:
                _save_preview(image, quilt_spec, Path("renders/previews") / f"{stem}.png")

        click.echo(f"[OK] {written}")

        if cast:
            _cast(written, quilt_spec)
    finally:
        plotter.close()


def _save_preview(image, spec, path: Path) -> None:
    """Write the quilt's centre view as a flat PNG.

    A quilt opened in an ordinary viewer is a tiled contact sheet, which is
    useless for judging whether the tree looks right.  The centre view is the
    same framing without the parallax sweep.

    :param image: Quilt array from ``render_quilt``.
    :param spec: Quilt specification.
    :param path: Destination PNG path.
    """
    from PIL import Image  # noqa: PLC0415

    x, y = spec.tile_origin(spec.n_views // 2)
    tile = image[y : y + spec.tile_height, x : x + spec.tile_width]
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(tile).save(path)
    click.echo(f"[OK] {path}")


def _cast(path: Path, spec) -> None:
    """Hand a rendered quilt to Looking Glass Bridge, tolerating its absence.

    :param path: Quilt file to display.
    :param spec: Quilt specification.
    """
    from quiltwright import cast_quilt  # noqa: PLC0415

    try:
        cast_quilt(path.resolve(), spec)
        click.echo("[OK] cast to Looking Glass")
    except Exception as exc:  # noqa: BLE001 - Bridge absence must not fail the render
        click.echo(f"[WARN] could not cast: {exc}")
