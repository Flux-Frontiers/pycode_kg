"""
viz3d.py — PyVista/PyQt5 3-D knowledge-graph visualiser for PyCodeKG.

Adapted from *repo_vis/pkg_visualizer/pkg_visualizer.py*
(Eric G. Suchanek, PhD — https://github.com/suchanek/repo_vis).

Window layout mirrors repo_vis exactly:
  Left  — control panel (DB path, layout selector, module filter, render options)
  Right — PyVista QtInteractor + button row (Reset View, Reset Settings, status)

Pick any node to open a modeless docstring popup; the picked node is
highlighted in pink and the camera zooms in, exactly as in repo_vis.

Author: Eric G. Suchanek, PhD
"""

# pylint: disable=C0301,C0116,C0115,W0613,E0611,C0415

from __future__ import annotations

import atexit
import gc
import logging
import re
import sys
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import param
import pyvista as pv
from markdown import markdown  # type: ignore[import-untyped]
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSlider,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor
from rich.logging import RichHandler

from pycode_kg import __version__

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.WARNING, handlers=[RichHandler()])
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

__author__ = "Eric G. Suchanek, PhD"

DEFAULT_DB = ".pycodekg/graph.sqlite"
DEFAULT_SAVE = "pycodekg_3d"

CONTROL_PANEL_WIDTH: int = 240
BUTTON_WIDTH: int = 120
ZOOM_FACTOR: float = 10.0

# Node colours (aligned with app.py pyvis visualiser)
KIND_COLOR: dict[str, str] = {
    "module": "#4A90D9",
    "class": "#27AE60",
    "function": "#E74C3C",
    "private_function": "#F1C40F",
    "method": "#3498DB",
    "symbol": "#95A5A6",
}

# Node sizes (radius)
KIND_SIZE: dict[str, float] = {
    "module": 1.2,
    "class": 0.9,
    "function": 0.7,
    "private_function": 0.7,
    "method": 0.5,
    "symbol": 0.4,
}

# Edge colours
REL_COLOR: dict[str, str] = {
    "CONTAINS": "#555555",
    "CALLS": "#E74C3C",
    "IMPORTS": "#3498DB",
    "INHERITS": "#F39C12",
}

# LOD thresholds (total visible nodes)
LOD_HIGH: int = 800  # icospheres / cylinders
LOD_LOW: int = 1500  # simplified geometry; above → small spheres

# Edge rendering limits
MAX_EDGES_ARC: int = 2000  # above this, draw straight lines instead of arcs
MAX_EDGES_TOTAL: int = 8000  # hard cap — skip lowest-priority edges beyond this

# Priority order when capping edges: CONTAINS (structural skeleton) always first
_EDGE_PRIORITY: dict[str, int] = {"CONTAINS": 0, "INHERITS": 1, "IMPORTS": 2, "CALLS": 3}

# ---------------------------------------------------------------------------
# Internal geometry helpers
# ---------------------------------------------------------------------------


def _make_node_mesh(kind: str, center: np.ndarray, size: float, lod: str):
    """
    Return a PyVista mesh for a single node, adapting geometry to the LOD tier.

    :param kind: Node kind string (``module``, ``class``, etc.).
    :param center: 3-D centre position.
    :param size: Node radius.
    :param lod: LOD tier — ``"high"``, ``"low"``, or ``"points"``.
    :return: PyVista PolyData mesh.
    """
    if lod == "high":
        if kind == "module":
            h = size * 0.9
            return pv.Box(
                bounds=(
                    center[0] - h,
                    center[0] + h,
                    center[1] - h,
                    center[1] + h,
                    center[2] - h,
                    center[2] + h,
                )
            )
        elif kind in ("function", "private_function"):
            return pv.Cylinder(
                center=center,
                direction=(0, 0, 1),
                radius=size * 0.6,
                height=size * 1.4,
                resolution=12,
            )
        else:
            return pv.Icosahedron(radius=size, center=center)
    elif lod == "low":
        if kind == "module":
            h = size * 0.9
            return pv.Box(
                bounds=(
                    center[0] - h,
                    center[0] + h,
                    center[1] - h,
                    center[1] + h,
                    center[2] - h,
                    center[2] + h,
                )
            )
        elif kind in ("function", "private_function"):
            return pv.Cylinder(
                center=center,
                direction=(0, 0, 1),
                radius=size * 0.6,
                height=size * 1.4,
                resolution=6,
            )
        elif kind == "class":
            return pv.Octahedron(radius=size, center=center)
        else:
            return pv.Sphere(radius=size * 0.5, center=center, theta_resolution=4, phi_resolution=4)
    else:
        return pv.Sphere(radius=size * 0.5, center=center, theta_resolution=4, phi_resolution=4)


def _arc_points(p1: np.ndarray, p2: np.ndarray, n_pts: int = 24, lift: float = 0.35) -> np.ndarray:
    """
    Quadratic Bézier arc from *p1* to *p2*, apex lifted ``lift × chord`` in Z.

    :param p1: Start point.
    :param p2: End point.
    :param n_pts: Number of sample points.
    :param lift: Fraction of chord length used as Z lift.
    :return: ``(n_pts, 3)`` array.
    """
    p1, p2 = np.asarray(p1, float), np.asarray(p2, float)
    mid = (p1 + p2) / 2.0
    mid[2] += lift * np.linalg.norm(p2 - p1)
    t = np.linspace(0.0, 1.0, n_pts)[:, None]
    return (1 - t) ** 2 * p1 + 2 * t * (1 - t) * mid + t**2 * p2


def _docstring_to_markdown(docstring: str | None) -> str:
    """
    Convert a ``:param:``-style docstring to Markdown.
    Adapted from ``utility.format_docstring_to_markdown`` in *repo_vis*.

    :param docstring: Raw Python docstring, or ``None``.
    :return: Markdown-formatted string.
    """
    if not docstring:
        return "No docstring available."
    lines = docstring.strip().split("\n")
    md: list[str] = [f"# {lines[0]}"]
    for line in lines[1:]:
        line = line.strip()
        if line.startswith(":type") or line.startswith(":rtype"):
            continue
        m = re.match(r":param (\w+): (.+)", line)
        if m:
            md.append(f"- **{m.group(1)}**: {m.group(2)}")
        elif line.startswith(":return:"):
            md.append(line.replace(":return:", "**Returns:**"))
        else:
            md.append(line)
    return "\n".join(md)


def _remove_highlight_actors(plotter: pv.Plotter) -> None:
    """Remove any leftover pink highlight or outline actors from the plotter."""
    for name in list(plotter.actors.keys()):
        if "highlight" in name.lower() or "bounds" in name.lower() or "outline" in name.lower():
            plotter.remove_actor(name, reset_camera=False)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# DocstringPopup — copied from repo_vis (with attribution)
# ---------------------------------------------------------------------------


class DocstringPopup(QDialog):
    """
    Modeless popup dialog that renders a docstring as HTML Markdown.
    Adapted from *repo_vis/pkg_visualizer/pkg_visualizer.py*
    (Eric G. Suchanek, PhD).
    """

    def __init__(self, title: str, docstring: str, parent=None, on_close_callback=None):
        """
        Initialise the popup window.

        :param title: Window title.
        :param docstring: Raw docstring text (will be rendered as Markdown/HTML).
        :param parent: Parent widget.
        :param on_close_callback: Called when the window is closed.
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)
        self.on_close_callback = on_close_callback
        self.setWindowModality(Qt.NonModal)  # type: ignore[attr-defined]

        if parent:
            geo = parent.screen().geometry()
            self.move(geo.x() + 50, geo.y() + 50)

        layout = QVBoxLayout(self)
        html = markdown(docstring or "No docstring available.")
        browser = QTextBrowser(self)
        browser.setHtml(html)
        layout.addWidget(browser)

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.close)  # type: ignore[arg-type]
        layout.addWidget(close_btn)

    def closeEvent(self, event):
        """Trigger the close callback if set."""
        if self.on_close_callback:
            self.on_close_callback()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# create_kg_visualization — adapted from create_allium_visualization()
# ---------------------------------------------------------------------------


def create_kg_visualization(
    viz: KGVisualizer,
    nodes,
    edges,
    plotter: pv.Plotter,
) -> tuple[pv.Plotter, str, dict[str, dict]]:
    """
    Render the knowledge graph into *plotter* using the current layout.

    Mirrors the structure of ``create_allium_visualization`` in *repo_vis*:
    clears the plotter, sets up lights, computes the layout, builds
    per-kind ``pv.MultiBlock`` node meshes, builds per-relation edge
    meshes, and returns the ``actor_to_node`` lookup used by picking.

    :param viz: :class:`KGVisualizer` instance (source of settings and state).
    :param nodes: List of :class:`~pycode_kg.layout3d.LayoutNode` objects to render.
    :param edges: Full edge list (used for layout computation and edge rendering).
    :param plotter: The ``QtInteractor`` to render into.
    :return: ``(plotter, title_text, actor_to_node)``
    """
    from pycode_kg.layout3d import AlliumLayout, FunnelLayout

    viz.status = "Setting up visualization..."
    QApplication.processEvents()

    plotter.clear_actors()
    plotter.enable_anti_aliasing("msaa")
    plotter.enable_terrain_style()  # type: ignore[call-arg]
    plotter.set_background("white", top="lightblue")  # type: ignore[arg-type]
    plotter.add_axes(  # type: ignore[call-arg]
        interactive=False,
        viewport=(0.75, 0.75, 1.0, 1.0),
    )

    # -- Layout
    layout = (
        AlliumLayout()
        if viz.layout_name == "allium"
        else FunnelLayout(layer_gap=20.0, node_spacing=viz.node_spacing)
    )
    # Always compute on ALL nodes for stable positions; filtering happens in display

    all_nodes_for_layout = viz.nodes  # full set for stable layout
    all_edges_for_layout = viz.edges
    positions = layout.compute(all_nodes_for_layout, all_edges_for_layout)

    # Clamp all nodes to Z >= 0 so nothing clips below the ground plane
    for nid, pos in positions.items():
        if pos[2] < 0:
            positions[nid] = np.array([pos[0], pos[1], 0.0])

    # -- LOD tier
    n_visible = len(nodes)
    lod = "high" if n_visible <= LOD_HIGH else "low" if n_visible <= LOD_LOW else "points"

    # -- Build per-kind MultiBlocks
    kind_blocks: dict[str, pv.MultiBlock] = {k: pv.MultiBlock() for k in KIND_SIZE}
    actor_to_node: dict[str, dict] = {}
    kind_counters: dict[str, int] = {k: 0 for k in KIND_SIZE}

    node_id_set = {n.id for n in nodes}

    for node in nodes:
        pos = positions.get(node.id)  # type: ignore[assignment]
        if pos is None:
            continue
        kind = node.kind
        if kind == "function" and node.name.startswith("_"):
            kind = "private_function"
        elif kind not in KIND_SIZE:
            kind = "symbol"

        mesh = _make_node_mesh(kind, pos, KIND_SIZE[kind], lod)
        kind_blocks[kind].append(mesh)

        mesh_id = f"{kind}_{kind_counters[kind]}"
        kind_counters[kind] += 1
        actor_to_node[mesh_id] = {
            "kind": kind,
            "id": node.id,
            "name": node.name,
            "module_path": node.module_path,
            "lineno": node.lineno,
            "end_lineno": node.end_lineno,
            "docstring": node.docstring,
            "position": pos,
            "mesh": mesh,
        }

        # Progress update
        total_nodes = len(nodes)
        update_every = max(1, total_nodes // 10)
        rendered = sum(kind_counters.values())
        if rendered % update_every == 0 or rendered == total_nodes:
            pct = int(rendered / total_nodes * 100)
            bar = "█" * (pct // 10) + "░" * ((100 - pct) // 10)
            viz.status = f"Rendering nodes | {bar} {pct}% ({rendered}/{total_nodes})"
            QApplication.processEvents()

    # -- Add node MultiBlocks
    for kind, block in kind_blocks.items():
        if block.n_blocks > 0:
            # Only apply smooth shading to cylinders (function nodes)
            plotter.add_mesh(
                block,
                color=KIND_COLOR[kind],
                show_edges=False,
                smooth_shading=(kind == "function"),
                name=f"{kind}_nodes",
            )

    # -- Edge rendering
    rel_to_show = set()
    if viz.show_calls:
        rel_to_show.add("CALLS")
    if viz.show_imports:
        rel_to_show.add("IMPORTS")
    if viz.show_inherits:
        rel_to_show.add("INHERITS")
    if viz.show_contains:
        rel_to_show.add("CONTAINS")

    # Count renderable edges to decide rendering strategy
    renderable = [
        e for e in edges if e.rel in rel_to_show and e.src in node_id_set and e.dst in node_id_set
    ]
    use_arcs = len(renderable) <= MAX_EDGES_ARC
    if len(renderable) > MAX_EDGES_TOTAL:
        renderable.sort(key=lambda e: _EDGE_PRIORITY.get(e.rel, 9))
        renderable = renderable[:MAX_EDGES_TOTAL]

    viz.status = f"Rendering {len(renderable)} edges {'(arcs)' if use_arcs else '(lines)'}..."
    QApplication.processEvents()

    # Accumulate raw point/connectivity arrays per relation — one PolyData per rel
    rel_pts: dict[str, list[np.ndarray]] = {r: [] for r in rel_to_show}
    rel_cells: dict[str, list[int]] = {r: [] for r in rel_to_show}
    rel_idx: dict[str, int] = {r: 0 for r in rel_to_show}

    for edge in renderable:
        p1, p2 = positions.get(edge.src), positions.get(edge.dst)
        if p1 is None or p2 is None:
            continue
        rel = edge.rel
        if use_arcs and rel != "CONTAINS":
            seg = _arc_points(p1, p2)
        else:
            seg = np.array([p1, p2])
        n = len(seg)
        rel_pts[rel].extend(seg)
        rel_cells[rel].extend([n] + list(range(rel_idx[rel], rel_idx[rel] + n)))
        rel_idx[rel] += n

    QApplication.processEvents()

    for rel in rel_to_show:
        pts = rel_pts[rel]
        cells = rel_cells[rel]
        if not pts:
            continue
        pd = pv.PolyData()
        pd.points = np.array(pts)
        pd.lines = np.array(cells)
        is_contains = rel == "CONTAINS"
        plotter.add_mesh(
            pd,
            color=REL_COLOR[rel],
            line_width=4.0 if is_contains else 2.5,
            opacity=0.5 if is_contains else 1.0,
            name=f"{rel.lower()}_edges",
        )

    # -- Ground plane: auto-sized to scene bounds, added after all meshes
    plotter.add_floor(  # type: ignore[call-arg]
        face="-z",
        color="lightgray",
        opacity=0.85,
        show_edges=True,
        i_resolution=20,
        j_resolution=20,
        pad=0.1,
    )

    # -- Stats
    total_faces = 0
    for block in kind_blocks.values():
        for i in range(block.n_blocks):
            mesh = block[i]
            if hasattr(mesh, "n_faces_strict"):
                total_faces += mesh.n_faces_strict  # type: ignore[union-attr]
    viz.num_faces = total_faces

    _db = Path(viz.db_path)
    _repo_name = _db.parent.parent.name if _db.parent.name == ".pycodekg" else _db.stem
    title = (
        f"PyCodeKG 3D v{__version__} | {_repo_name} | "
        f"Modules: {viz.num_modules}  Classes: {viz.num_classes}  "
        f"Methods: {viz.num_methods}  Functions: {viz.num_functions}  "
        f"Faces: {total_faces}"
    )

    plotter.reset_camera()  # type: ignore[call-arg]
    # Front-elevated perspective: mostly looking along +Y, tilted ~25° down,
    # with a slight rightward rotation so the scene reads with depth.
    plotter.view_vector((0.0, 1.0, 0.35), viewup=(0, 0, 1))  # type: ignore[call-arg, arg-type]
    plotter.camera.zoom(1.6)
    plotter.render()

    viz.status = "Scene generation complete."
    QApplication.processEvents()

    return plotter, title, actor_to_node


# ---------------------------------------------------------------------------
# KGVisualizer — adapted from PackageVisualizer
# ---------------------------------------------------------------------------


class KGVisualizer(param.Parameterized):
    """
    Data and state model for the PyCodeKG 3-D visualiser.
    Adapted from ``PackageVisualizer`` in *repo_vis*.

    Reactive attributes (via ``param``) drive the Qt control panel;
    watched parameters trigger graph reload or UI updates automatically.
    """

    db_path: str = param.String(default=DEFAULT_DB, doc="SQLite database path")
    layout_name: str = param.Selector(
        objects=["allium", "funnel"], default="allium", doc="3-D layout strategy"
    )
    save_path: str = param.String(default=DEFAULT_SAVE, doc="Save path stem")
    save_format: str = param.Selector(
        objects=["html", "png", "jpg"], default="html", doc="Export format"
    )

    # Node kind visibility
    show_methods: bool = param.Boolean(default=True, doc="Render method nodes")
    show_symbols: bool = param.Boolean(default=False, doc="Render symbol stub nodes")
    # Edge visibility
    show_calls: bool = param.Boolean(default=True, doc="Render CALLS edges")
    show_imports: bool = param.Boolean(default=True, doc="Render IMPORTS edges")
    show_inherits: bool = param.Boolean(default=True, doc="Render INHERITS edges")
    show_contains: bool = param.Boolean(default=True, doc="Render CONTAINS edges")
    # Layout spacing (funnel only)
    node_spacing: float = param.Number(default=2.0, bounds=(0.5, 10.0), doc="Funnel node spacing")

    # Status / title
    status: str = param.String(default="Ready", doc="Status bar text")
    window_title: str = param.String(default=f"PyCodeKG 3D v{__version__}", doc="Window title")

    # Stats
    num_modules: int = param.Integer(default=0)
    num_classes: int = param.Integer(default=0)
    num_functions: int = param.Integer(default=0)
    num_methods: int = param.Integer(default=0)
    num_faces: int = param.Integer(default=0)

    # Module selector data
    available_modules: list[str] = param.List(default=[], doc="Available module names")
    selected_modules: list[str] = param.ListSelector(
        default=[], objects=[], doc="Selected module names"
    )

    def __init__(self, plotter: pv.Plotter | None = None, **params) -> None:
        """
        Initialise the visualiser data model.

        :param plotter: The ``QtInteractor`` to render into.
        :param params: Additional ``param`` keyword arguments.
        """
        super().__init__(**params)
        self.plotter: pv.Plotter | None = plotter
        self.nodes: list = []
        self.edges: list = []
        self.actor_to_node: dict[str, dict] = {}
        self._load_graph()

    @param.depends("db_path", watch=True)
    def _load_graph(self) -> None:
        """Reload nodes and edges from the SQLite database."""
        from pycode_kg.layout3d import LayoutEdge, LayoutNode
        from pycode_kg.store import GraphStore

        db = Path(self.db_path)
        if not db.exists():
            self.status = f"Error: database not found: {db}"
            return

        self.status = "Loading graph..."
        QApplication.processEvents()

        with GraphStore(db) as store:
            raw_nodes = store.query_nodes()
            node_ids = {n["id"] for n in raw_nodes}
            raw_edges = store.edges_within(node_ids)

        self.nodes = [LayoutNode.from_dict(n) for n in raw_nodes]
        self.edges = [LayoutEdge.from_dict(e) for e in raw_edges]

        counts = Counter(n.kind for n in self.nodes)
        self.num_modules = counts.get("module", 0)
        self.num_classes = counts.get("class", 0)
        self.num_functions = counts.get("function", 0)
        self.num_methods = counts.get("method", 0)

        mod_names = sorted(n.name for n in self.nodes if n.kind == "module")
        self.available_modules = mod_names
        self.param.selected_modules.objects = mod_names
        self.selected_modules = []

        repo_name = db.parent.parent.name if db.parent.name == ".pycodekg" else db.stem
        self.window_title = (
            f"PyCodeKG 3D v{__version__} | {repo_name} | "
            f"Modules: {self.num_modules}  Classes: {self.num_classes}  "
            f"Methods: {self.num_methods}  Functions: {self.num_functions}"
        )
        self.status = f"Loaded: {len(self.nodes)} nodes, {len(self.edges)} edges"

        if self.plotter and hasattr(self.plotter, "clear_actors"):
            self.plotter.clear_actors()

    def visualize(self) -> None:
        """
        Build and render the 3-D scene using the current settings.

        Applies the selected module filter, then delegates to
        :func:`create_kg_visualization`.
        """
        if not self.plotter:
            return
        if not self.nodes:
            self.status = "No data — check DB path."
            return

        # Apply module filter
        if self.selected_modules:
            contains_children: dict[str, list[str]] = {}
            for e in self.edges:
                if e.rel == "CONTAINS":
                    contains_children.setdefault(e.src, []).append(e.dst)

            def subtree(root_id: str) -> set:
                """Collect all node IDs in the CONTAINS subtree rooted at *root_id*.

                :param root_id: ID of the root node.
                :return: Set of node IDs reachable via CONTAINS edges.
                """
                s = {root_id}
                for c in contains_children.get(root_id, []):
                    s |= subtree(c)
                return s

            in_scope: set = set()
            for mod_name in self.selected_modules:
                mod_node = next(
                    (n for n in self.nodes if n.kind == "module" and n.name == mod_name),
                    None,
                )
                if mod_node:
                    in_scope |= subtree(mod_node.id)

            # Respect show_methods / show_symbols
            visible_nodes = [
                n for n in self.nodes if n.id in in_scope and self._kind_visible(n.kind)
            ]
        else:
            visible_nodes = [n for n in self.nodes if self._kind_visible(n.kind)]

        try:
            _, title, actor_to_node = create_kg_visualization(
                self, visible_nodes, self.edges, self.plotter
            )
            self.actor_to_node = actor_to_node
            self.window_title = title
        except (ValueError, RuntimeError) as exc:
            self.status = f"Error: {exc}"

    def _kind_visible(self, kind: str) -> bool:
        """Return ``True`` if nodes of this kind should be rendered."""
        if kind == "method" and not self.show_methods:
            return False
        if kind == "symbol" and not self.show_symbols:
            return False
        return True


# ---------------------------------------------------------------------------
# MainWindow — adapted from repo_vis MainWindow
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    """
    Full Qt main window for the PyCodeKG 3-D visualiser.

    Layout mirrors *repo_vis/pkg_visualizer/pkg_visualizer.py*:
    - **Left** — control panel (DB path, layout, module filter, render options)
    - **Right** — PyVista ``QtInteractor`` + button row

    Adapted from ``MainWindow`` in *repo_vis* (Eric G. Suchanek, PhD).
    """

    status_changed: pyqtSignal = pyqtSignal(str)

    def __init__(
        self,
        db_path: str = DEFAULT_DB,
        save_path: str = DEFAULT_SAVE,
        width: int = 1400,
        height: int = 900,
    ) -> None:
        """
        Initialise the main window.

        :param db_path: Path to the ``.pycodekg/graph.sqlite`` file.
        :param save_path: Default output file stem for exports.
        :param width: Initial window width in pixels.
        :param height: Initial window height in pixels.
        """
        super().__init__()

        self.timer = None
        self.current_frame = 0
        self._current_picked_actor = None
        self._current_popup: DocstringPopup | None = None
        self._original_camera_state = None

        self.setGeometry(100, 100, width, height)

        self.vtk_plotter: QtInteractor = QtInteractor(self)
        self.visualizer: KGVisualizer = KGVisualizer(
            plotter=self.vtk_plotter,
            db_path=db_path,
            save_path=save_path,
        )
        self.plotter = self.vtk_plotter  # convenience alias

        self.setWindowTitle(self.visualizer.window_title)

        # ── Central widget ──────────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        self.setStyleSheet(
            """
            QPushButton { background-color: #4CAF50; color: white; border: none;
                          border-radius: 3px; padding: 6px; margin: 2px; }
            QPushButton#reset-view  { background-color: #FFEB3B; color: black; }
            QPushButton#reset-all   { background-color: #E53935; color: white; }
            QPushButton { font-size: 12px; }
        """
        )

        ctrl_widget = self._build_control_panel()
        vis_widget = self._build_viewport_panel()

        main_layout.addWidget(ctrl_widget)
        main_layout.addWidget(vis_widget, stretch=1)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        central.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ctrl_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        self._setup_mesh_picking()
        self._connect_signals()

        font = QFont("Arial", 12)
        self.setFont(font)
        self.resize(width, height)

        # Perform initial render on launch
        QApplication.processEvents()
        self.on_visualize_clicked()

    # ── UI builder helpers ───────────────────────────────────────────────────

    @staticmethod
    def _h2(text: str) -> QLabel:
        """Create a bold section-header QLabel.

        :param text: Header text (rendered at 13 px bold).
        :return: Styled :class:`QLabel` instance.
        """
        lbl = QLabel(f"<b style='font-size:13px;'>{text}</b>")
        lbl.setStyleSheet("background:transparent; border:none;")
        return lbl

    @staticmethod
    def _lbl(text: str) -> QLabel:
        """Create a plain-text QLabel with transparent background.

        :param text: Label text (may contain basic HTML).
        :return: Styled :class:`QLabel` instance.
        """
        lbl = QLabel(text)
        lbl.setStyleSheet("background:transparent; border:none;")
        return lbl

    def _build_input_params(self, ctrl: QVBoxLayout) -> None:
        """Populate *ctrl* with the Input Parameters section.

        Adds widgets for DB path, layout selector, save path, and save format.

        :param ctrl: The control-panel layout to populate.
        """
        ctrl.addWidget(self._h2("Input Parameters"))

        ctrl.addWidget(self._lbl("<b>Database Path</b>"))
        self.db_path_input = QLineEdit(self.visualizer.db_path)
        self.db_path_input.setPlaceholderText(".pycodekg/graph.sqlite")
        ctrl.addWidget(self.db_path_input)

        ctrl.addWidget(self._lbl("<b>Layout</b>"))
        self.layout_select = QComboBox()
        self.layout_select.addItems(["allium", "funnel"])
        self.layout_select.setCurrentText(self.visualizer.layout_name)
        ctrl.addWidget(self.layout_select)

        ctrl.addWidget(self._lbl("<b>Save Path</b>"))
        self.save_path_input = QLineEdit(self.visualizer.save_path)
        ctrl.addWidget(self.save_path_input)

        ctrl.addWidget(self._lbl("<b>Save Format</b>"))
        self.save_format_select = QComboBox()
        self.save_format_select.addItems(["html", "png", "jpg"])
        self.save_format_select.setCurrentText(self.visualizer.save_format)
        ctrl.addWidget(self.save_format_select)

    def _build_module_filter(self, ctrl: QVBoxLayout) -> None:
        """Populate *ctrl* with the Module Filter section.

        Adds a single-selection list pre-filled with available modules.

        :param ctrl: The control-panel layout to populate.
        """
        ctrl.addWidget(self._h2("Module Filter"))
        ctrl.addWidget(self._lbl("Select module (empty = all):"))
        self.module_selector = QListWidget()
        self.module_selector.setSelectionMode(QListWidget.SingleSelection)
        self.module_selector.setMaximumHeight(90)
        for name in self.visualizer.available_modules:
            self.module_selector.addItem(name)
        ctrl.addWidget(self.module_selector)

    def _build_render_options(self, ctrl: QVBoxLayout) -> None:
        """Populate *ctrl* with the Render Options and Graph Statistics sections.

        Adds node-kind checkboxes, edge-type checkboxes, and a live stats label.

        :param ctrl: The control-panel layout to populate.
        """
        ctrl.addWidget(self._h2("Render Options"))

        cb_row1 = QHBoxLayout()
        self.cb_methods = QCheckBox("Methods")
        self.cb_methods.setChecked(self.visualizer.show_methods)
        self.cb_symbols = QCheckBox("Symbols")
        self.cb_symbols.setChecked(self.visualizer.show_symbols)
        self.cb_contains = QCheckBox("CONTAINS")
        self.cb_contains.setChecked(self.visualizer.show_contains)
        for w in (self.cb_methods, self.cb_symbols, self.cb_contains):
            cb_row1.addWidget(w)
        ctrl.addLayout(cb_row1)

        ctrl.addWidget(self._lbl("<b>Edge Types</b>"))
        cb_row2 = QHBoxLayout()
        self.cb_calls = QCheckBox("CALLS")
        self.cb_calls.setChecked(self.visualizer.show_calls)
        self.cb_imports = QCheckBox("IMPORTS")
        self.cb_imports.setChecked(self.visualizer.show_imports)
        self.cb_inherits = QCheckBox("INHERITS")
        self.cb_inherits.setChecked(self.visualizer.show_inherits)
        for w in (self.cb_calls, self.cb_imports, self.cb_inherits):
            cb_row2.addWidget(w)
        ctrl.addLayout(cb_row2)

        ctrl.addWidget(self._lbl("<b>Funnel Spacing</b>"))
        spacing_row = QHBoxLayout()
        self.spacing_slider = QSlider(Qt.Orientation.Horizontal)
        self.spacing_slider.setMinimum(5)
        self.spacing_slider.setMaximum(100)
        self.spacing_slider.setValue(int(self.visualizer.node_spacing * 10))
        self.spacing_slider.setTickInterval(5)
        self.spacing_val_label = QLabel(f"{self.visualizer.node_spacing:.1f}")
        self.spacing_val_label.setFixedWidth(30)
        self.spacing_slider.valueChanged.connect(self._on_spacing_changed)
        spacing_row.addWidget(self.spacing_slider)
        spacing_row.addWidget(self.spacing_val_label)
        ctrl.addLayout(spacing_row)

        ctrl.addWidget(self._lbl("<b>Graph Statistics</b>"))
        self.stats_label = QLabel(self._stats_text())
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet(
            "background-color:white; color:black; padding:5px; border-radius:3px;"
        )
        ctrl.addWidget(self.stats_label)

    def _build_action_buttons(self, ctrl: QVBoxLayout) -> None:
        """Populate *ctrl* with the action-button row at the bottom of the panel.

        Adds a prominent Render Graph button and a secondary row with
        Show Docstring and Save View.

        :param ctrl: The control-panel layout to populate.
        """
        ctrl.addStretch()

        self.visualize_button = QPushButton("Render Graph")
        self.visualize_button.setMinimumHeight(40)
        self.visualize_button.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; }")
        ctrl.addWidget(self.visualize_button)

        btn_row = QHBoxLayout()
        self.show_docstring_button = QPushButton("Show Docstring")
        self.save_button = QPushButton("Save View")
        btn_row.addWidget(self.show_docstring_button)
        btn_row.addWidget(self.save_button)
        ctrl.addLayout(btn_row)

    def _build_control_panel(self) -> QWidget:
        """Build and return the left-side control-panel widget.

        Assembles Input Parameters, Module Filter, Render Options, and
        action buttons into a fixed-width :class:`QWidget`.

        :return: A :class:`QWidget` containing the complete control panel.
        """
        ctrl = QVBoxLayout()
        ctrl.setSpacing(12)
        ctrl.setContentsMargins(6, 6, 6, 6)

        self._build_input_params(ctrl)
        self._build_module_filter(ctrl)
        self._build_render_options(ctrl)
        self._build_action_buttons(ctrl)

        widget = QWidget()
        widget.setLayout(ctrl)
        widget.setFixedWidth(CONTROL_PANEL_WIDTH)
        return widget

    def _build_viewport_panel(self) -> QWidget:
        """Build and return the right-side viewport widget.

        Wraps the PyVista :class:`QtInteractor` and a bottom button row
        (Reset View, Reset Settings, status display) in a :class:`QWidget`.

        :return: A :class:`QWidget` containing the 3-D viewport and controls.
        """
        vis = QVBoxLayout()
        vis.setSpacing(10)
        vis.setContentsMargins(10, 10, 10, 10)
        vis.addWidget(self.vtk_plotter, stretch=1)
        vis.addStretch()

        btn_row = QHBoxLayout()

        self.reset_view_button = QPushButton("Reset View")
        self.reset_view_button.setObjectName("reset-view")
        self.reset_view_button.setFixedWidth(BUTTON_WIDTH)
        btn_row.addWidget(self.reset_view_button)

        self.reset_settings_button = QPushButton("Reset Settings")
        self.reset_settings_button.setObjectName("reset-all")
        self.reset_settings_button.setFixedWidth(BUTTON_WIDTH)
        btn_row.addWidget(self.reset_settings_button)

        self.status_display = QLabel("Ready")
        self.status_display.setTextInteractionFlags(Qt.TextBrowserInteraction)  # type: ignore[attr-defined]
        self.status_display.setStyleSheet(
            "font-weight:bold; font-size:13px; background-color:white; color:black;"
        )
        btn_row.addWidget(self.status_display, stretch=1)

        vis.addLayout(btn_row)

        widget = QWidget()
        widget.setLayout(vis)
        return widget

    def _setup_mesh_picking(self) -> None:
        """Configure PyVista mesh picking on the VTK plotter.

        Enables actor-based mesh picking with a tight tolerance, mirroring
        the *repo_vis* picking setup.
        """
        self.vtk_plotter.enable_mesh_picking(
            callback=self.on_pick,
            show=False,
            show_actors=False,
            show_message=False,
            font_size=14,
            left_clicking=False,
            use_actor=True,
            through=True,
        )
        if hasattr(self.vtk_plotter, "picker"):
            self.vtk_plotter.picker.SetTolerance(0.005)
            self.vtk_plotter.picker.SetPickFromList(0)

    def _connect_signals(self) -> None:
        """Wire all Qt signal/slot connections for the main window.

        Connects control-panel inputs to visualizer properties, action
        buttons to their handlers, and param watchers for live updates.
        """
        self.db_path_input.editingFinished.connect(self.update_db_path)
        self.layout_select.currentTextChanged.connect(self.update_layout)
        self.save_path_input.textChanged.connect(lambda t: setattr(self.visualizer, "save_path", t))
        self.save_format_select.currentTextChanged.connect(
            lambda t: setattr(self.visualizer, "save_format", t)
        )
        self.module_selector.itemSelectionChanged.connect(self.update_selected_modules)

        self.cb_methods.stateChanged.connect(
            lambda s: setattr(self.visualizer, "show_methods", s == Qt.Checked)  # type: ignore[attr-defined]
        )
        self.cb_symbols.stateChanged.connect(
            lambda s: setattr(self.visualizer, "show_symbols", s == Qt.Checked)  # type: ignore[attr-defined]
        )
        self.cb_contains.stateChanged.connect(
            lambda s: setattr(self.visualizer, "show_contains", s == Qt.Checked)  # type: ignore[attr-defined]
        )
        self.cb_calls.stateChanged.connect(
            lambda s: setattr(self.visualizer, "show_calls", s == Qt.Checked)  # type: ignore[attr-defined]
        )
        self.cb_imports.stateChanged.connect(
            lambda s: setattr(self.visualizer, "show_imports", s == Qt.Checked)  # type: ignore[attr-defined]
        )
        self.cb_inherits.stateChanged.connect(
            lambda s: setattr(self.visualizer, "show_inherits", s == Qt.Checked)  # type: ignore[attr-defined]
        )

        self.visualize_button.clicked.connect(self.on_visualize_clicked)
        self.show_docstring_button.clicked.connect(self.show_selected_docstring)
        self.save_button.clicked.connect(self.save_current_view)
        self.reset_view_button.clicked.connect(self.reset_camera)
        self.reset_settings_button.clicked.connect(self.reset_settings)

        self.status_changed.connect(self.update_status_display)
        self.visualizer.param.watch(self.on_status_change, "status")
        self.visualizer.param.watch(self.update_module_selector, "available_modules")
        self.visualizer.param.watch(self.update_window_title, "window_title")
        self.visualizer.param.watch(
            lambda _: self.stats_label.setText(self._stats_text()), "num_faces"
        )

    # ── Spacing slider ───────────────────────────────────────────────────────

    def _on_spacing_changed(self, value: int) -> None:
        spacing = value / 10.0
        self.visualizer.node_spacing = spacing
        self.spacing_val_label.setText(f"{spacing:.1f}")

    # ── Stats helper ────────────────────────────────────────────────────────

    def _stats_text(self) -> str:
        """Build a formatted stats string from the current visualizer state.

        :return: Multi-line string summarising module, class, method,
                 function, and face counts.
        """
        v = self.visualizer
        return (
            f"Modules: {v.num_modules}   Classes: {v.num_classes}\n"
            f"Methods: {v.num_methods}   Functions: {v.num_functions}\n"
            f"Faces: {v.num_faces}"
        )

    # ── Control panel updates ───────────────────────────────────────────────

    def update_db_path(self) -> None:
        """Handle DB path text field edit-finished."""
        text = self.db_path_input.text().strip()
        self.visualizer.db_path = text
        self.module_selector.clear()
        for name in self.visualizer.available_modules:
            self.module_selector.addItem(name)

    def update_layout(self, name: str) -> None:
        """Handle layout combo-box change."""
        self.visualizer.layout_name = name

    def update_selected_modules(self) -> None:
        """Sync QListWidget selection to visualizer.selected_modules."""
        self.visualizer.selected_modules = [
            item.text() for item in self.module_selector.selectedItems()
        ]

    def update_module_selector(self, event: param.Event) -> None:
        """Refresh module list when available_modules changes."""
        self.module_selector.clear()
        for name in event.new:
            self.module_selector.addItem(name)

    def update_window_title(self, event: param.Event) -> None:
        """Update the window title bar."""
        self.setWindowTitle(event.new)

    # ── Visualize ───────────────────────────────────────────────────────────

    def on_visualize_clicked(self) -> None:
        """Trigger a full scene rebuild."""
        self.visualizer.visualize()

    # ── Picking (mirrors repo_vis on_pick exactly) ──────────────────────────

    def on_pick(self, actor) -> None:
        """
        Callback fired when the user right-clicks a node mesh.
        Finds the nearest node, highlights it, and shows the docstring popup.
        Adapted from ``MainWindow.on_pick`` in *repo_vis*.
        """
        if not self.visualizer.plotter:
            return
        self.reset_actor_appearances()

        if self._current_popup and self._current_popup.isVisible():
            self._current_popup.close()
            self._current_popup = None

        if actor is None:
            self.update_status_display("No object picked.")
            return

        if not hasattr(self.vtk_plotter, "picked_point") or self.vtk_plotter.picked_point is None:
            self.update_status_display("No object picked.")
            return

        picked_point = np.asarray(self.vtk_plotter.picked_point, float)

        # Identify actor by name
        picked_name = None
        for name, act in self.plotter.actors.items():
            if act == actor:
                picked_name = name
                break

        if picked_name is None:
            self.update_status_display("Could not identify picked object.")
            return

        # Extract kind from actor name: "{kind}_nodes"
        picked_kind = None
        for kind in KIND_SIZE:
            if picked_name == f"{kind}_nodes":
                picked_kind = kind
                break

        if picked_kind is None:
            self.update_status_display(f"Unknown actor: {picked_name}")
            return

        # Find closest node of that kind
        best_id, best_dist = None, float("inf")
        for mesh_id, elem in self.visualizer.actor_to_node.items():
            if elem["kind"] != picked_kind:
                continue
            pos = np.asarray(elem["position"], float)
            d = float(np.linalg.norm(pos - picked_point))
            if d < best_dist:
                best_dist = d
                best_id = mesh_id

        if best_id is None:
            self.update_status_display(f"No {picked_kind} near pick point.")
            return

        elem = self.visualizer.actor_to_node[best_id]
        self.highlight_actor(elem["mesh"])
        title = f"{elem['kind'].capitalize()}: {elem['name']}"
        self._current_popup = DocstringPopup(
            title,
            _docstring_to_markdown(elem.get("docstring")),
            self,
            on_close_callback=self.reset_picking_state,
        )
        self._current_popup.show()

    def highlight_actor(self, mesh) -> None:
        """
        Highlight *mesh* in pink, focus camera, and zoom.
        Adapted from ``MainWindow.highlight_actor`` in *repo_vis*.
        """
        if not self.plotter:
            return
        self.reset_actor_appearances()
        self.reset_camera()

        self.plotter.add_mesh(
            mesh,
            color="pink",
            show_edges=True,
            edge_color="white",
            line_width=3,
            pickable=False,
            show_scalar_bar=False,
            reset_camera=False,
            name="_kg_highlight",
        )
        self._current_picked_actor = self.plotter.actors.get("_kg_highlight")

        self._original_camera_state = {  # type: ignore[assignment]
            "position": self.plotter.camera.position,
            "focal_point": self.plotter.camera.focal_point,
            "view_up": self.plotter.camera.up,
        }

        self.plotter.camera.focal_point = np.array(mesh.center)
        self.plotter.camera.Zoom(ZOOM_FACTOR)
        self.plotter.render()

    def reset_actor_appearances(self) -> None:
        """Reset pick highlights and restore actor colours."""
        if self._current_picked_actor:
            self.plotter.remove_actor(self._current_picked_actor, reset_camera=False)
            self._current_picked_actor = None

        for kind in KIND_SIZE:
            actor = self.plotter.actors.get(f"{kind}_nodes")
            if actor:
                actor.prop.color = KIND_COLOR[kind]
                actor.prop.show_edges = False
                actor.prop.line_width = 1

        _remove_highlight_actors(self.plotter)

    def reset_picking_state(self) -> None:
        """Clear pick state after popup is closed."""
        self.reset_actor_appearances()
        self.module_selector.clearSelection()
        self.update_status_display("Ready")
        self.plotter.render()

    # ── Docstring button ────────────────────────────────────────────────────

    def show_selected_docstring(self) -> None:
        """Show docstring for the selected module in the list (if any)."""
        items = self.module_selector.selectedItems()
        if not items:
            self.update_status_display("Select a module first.")
            return
        mod_name = items[0].text()
        mod_node = next(
            (n for n in self.visualizer.nodes if n.kind == "module" and n.name == mod_name),
            None,
        )
        if mod_node is None:
            return
        self._current_popup = DocstringPopup(
            f"Module: {mod_name}",
            _docstring_to_markdown(mod_node.docstring),
            self,
            on_close_callback=self.reset_picking_state,
        )
        self._current_popup.show()

    # ── Camera controls (spin_camera copied verbatim from repo_vis) ─────────

    def reset_camera(self) -> None:
        """Reset the camera to the default front-elevated view."""
        if not self.plotter:
            return
        self.plotter.reset_camera()
        self.plotter.view_vector((0.0, 1.0, 0.35), viewup=(0, 0, 1))
        self.plotter.render()
        self.visualizer.status = "View reset."

    # ── Save ────────────────────────────────────────────────────────────────

    def save_current_view(self) -> None:
        """
        Save the current visualization to a file.
        Adapted from ``MainWindow.save_current_view`` in *repo_vis*.
        """
        save_path = Path(self.visualizer.save_path)
        fmt = self.visualizer.save_format
        if save_path.suffix.lstrip(".") != fmt:
            save_path = save_path.with_suffix(f".{fmt}")

        self.visualizer.status = f"Saving to {save_path}…"
        QApplication.processEvents()

        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            if fmt == "html":
                self.plotter.export_html(str(save_path))
            else:
                self.plotter.screenshot(str(save_path))
            self.visualizer.status = f"Saved → {save_path}"
        except ImportError as exc:
            self.visualizer.status = f"HTML export unavailable: {exc}"
        except (OSError, RuntimeError, ValueError) as exc:
            self.visualizer.status = f"Error saving: {exc}"

    # ── Status display (mirrors repo_vis update_status_display) ────────────

    def on_status_change(self, event: param.Event) -> None:
        """Forward param status change to the Qt signal."""
        self.status_changed.emit(event.new)
        QApplication.processEvents()

    def update_status_display(self, status: str) -> None:
        """Render status text with colour coding (mirrors repo_vis)."""
        if status.startswith("Error"):
            html = f"<span style='color:#E53935;font-size:13px;'><b>Error:</b> {status[6:]}</span>"
        elif "Rendering" in status or "Loading" in status or "Saving" in status:
            html = f"<span style='color:#42A5F5;font-size:13px;'><b>⏳ {status}</b></span>"
        elif "Loaded" in status or "Saved" in status or "complete" in status.lower():
            html = f"<span style='color:#66BB6A;font-size:13px;'><b>✓ {status}</b></span>"
        elif "Ready" in status or "reset" in status.lower():
            html = "<span style='color:#66BB6A;font-size:13px;'><b>⚡ Ready</b></span>"
        else:
            html = f"<span style='font-size:13px;'>{status}</span>"
        self.status_display.setText(html)

    # ── Reset settings ──────────────────────────────────────────────────────

    def reset_settings(self) -> None:
        """Reset all controls to defaults and clear the scene."""
        self.module_selector.clearSelection()
        self.cb_methods.setChecked(True)
        self.cb_symbols.setChecked(False)
        self.cb_contains.setChecked(False)
        self.cb_calls.setChecked(True)
        self.cb_imports.setChecked(True)
        self.cb_inherits.setChecked(True)
        self.reset_camera()
        self.visualizer.status = "Ready"

    # ── Cleanup / close (copied from repo_vis) ──────────────────────────────

    def cleanup_pyvista_objects(self) -> None:
        """Thorough PyVista cleanup to prevent errors on exit."""
        if self._current_popup and hasattr(self._current_popup, "isVisible"):
            try:
                self._current_popup.close()
            except (AttributeError, RuntimeError):
                pass
            self._current_popup = None

        if hasattr(self, "plotter") and self.plotter:
            try:
                if hasattr(self.plotter, "clear_actors"):
                    self.plotter.clear_actors()
                if hasattr(self.plotter, "clear"):
                    self.plotter.clear()
                if hasattr(self.plotter, "close"):
                    self.plotter.close()
                self.visualizer.plotter = None
                self.plotter = None
                self.vtk_plotter = None
            except (AttributeError, RuntimeError):
                pass
        gc.collect()

    def closeEvent(self, event) -> None:
        """Handle window close with cleanup."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                self.cleanup_pyvista_objects()
            except (AttributeError, RuntimeError):
                pass
        event.accept()

    def run(self) -> None:
        """Start the Qt event loop and show the window."""
        app = QApplication.instance() or QApplication(sys.argv)
        self.show()
        try:
            app.exec()
        except (RuntimeError, AttributeError) as exc:
            logger.error("Application error: %s", exc)
        finally:
            sys.exit()


# ---------------------------------------------------------------------------
# Atexit cleanup
# ---------------------------------------------------------------------------

atexit.register(gc.collect)


# ---------------------------------------------------------------------------
# launch() — convenience entry point used by pycodekg_viz3d.py CLI
# ---------------------------------------------------------------------------


def launch(
    db_path: str = DEFAULT_DB,
    layout_name: str = "allium",
    width: int = 1400,
    height: int = 900,
    **_kwargs,
) -> None:
    """
    Create a :class:`QApplication`, open :class:`MainWindow`, and run the event loop.

    :param db_path: Path to the SQLite database.
    :param layout_name: ``"allium"`` or ``"funnel"``.
    :param width: Initial window width.
    :param height: Initial window height.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("pycodekg-viz3d")

    win = MainWindow(
        db_path=db_path,
        save_path=Path(db_path).stem,
        width=width,
        height=height,
    )
    win.visualizer.layout_name = layout_name
    win.layout_select.setCurrentText(layout_name)
    win.show()
    sys.exit(app.exec())
