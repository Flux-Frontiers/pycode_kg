# Release Notes — v0.18.0

> Released: 2026-04-28

## Highlights

**3-D Visualizer — FunnelLayout and docs**
The `LayerCakeLayout` has been replaced by `FunnelLayout`, which derives per-layer radii algorithmically (`node_spacing × node_size × √n`) so layouts scale correctly across repos of any size. Orphan nodes are lifted out of the module plane to avoid overlap. The CLI flag is renamed `--layout funnel`. A new [`docs/VIZ3D.md`](docs/VIZ3D.md) user guide covers all layout options, controls, keyboard shortcuts, and install notes for PyVista/PyQt5.

**Embedder benchmarking infrastructure**
`scripts/benchmark_embedders.py` is fully redesigned: a `CANDIDATE_MODELS` registry catalogs all evaluated models, a `--preset` flag (`current`, `diary`, `bge`, `full`) replaces hand-typed model lists, and the query suite is expanded with five Samuel Pepys diary passages for cross-corpus evaluation against DiaryKG. Four benchmark runs from 2026-04-28 are included in `analysis/`.

**Timeline fixes and test coverage**
`viz3d_timeline.py` guards against empty-snapshot dicts, fixes invalid f-string compound format specs, and corrects stale manifest field names. A new 20-test suite (`tests/test_viz3d_timeline.py`) covers the full timeline contract.

**DocKG skill refresh**
`.claude/skills/dockg/SKILL.md` updated to reflect DocKG's new CLI defaults (`--update` replaces `--wipe`), the new `semantic-analyze` command, and the multipass analysis pipeline (`dockg pipeline run/embed/manifold`).

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
