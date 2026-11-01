# Release Notes -- v0.29.2

> Released: 2026-11-01

A security release. The lock file is refreshed to clear all 56 open
Dependabot alerts, 6 of them critical. No code changes.

## What changed

**Pillow 13.** Most alerts were against Pillow 12.3.0. Streamlit 1.63 capped
Pillow below 13, so the lock carried 12.3.0 for the `viz` extra; Streamlit
1.66.1 lifts the cap and the lock now holds a single Pillow 13.0.0.

**Other transitive updates.** certifi, filelock, setuptools and virtualenv
move to their patched releases.

## Upgrading

`pyproject.toml` ranges are unchanged, so a fresh install already resolves
patched versions. Reinstall from the lock (`poetry install`) to pick them up
in a development checkout. Graphs and indexes need no rebuild.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
