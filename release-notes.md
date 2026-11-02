# Release Notes -- v0.29.3

> Released: 2026-11-02

A security release for the 3-D extras. 0.29.2 refreshed the lock past
Pillow 12.3.0, but a pip install of `pycode-kg[viz3d]` or `pycode-kg[all]`
could still resolve an older quiltwright and, through it, the vulnerable
Pillow line. Both extras now floor quiltwright at 0.17.0, the first release
that floors Pillow at 13.0.0. Nothing else changes.

## What changed

**quiltwright 0.17.0 is the floor in `viz3d` and `all`.** The floor moves
from 0.16.0 to 0.17.0, which carries `pillow>=13.0.0` in its own metadata,
so every install of these extras gets the patched Pillow. The lock moves
quiltwright to 0.17.0.

## Upgrading

`pip install -U "pycode-kg[viz3d]"` (or `[all]`). No command, tool or index
changes, so existing graphs stay valid.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
