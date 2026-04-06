#!/usr/bin/env bash
# Rebuild PyCodeKG SQLite knowledge graph and LanceDB semantic index.
# Invoked by pre-commit after pytest succeeds.
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "--- PyCodeKG rebuild: SQLite ---"
poetry run pycodekg-build-sqlite --repo "$REPO_ROOT" --wipe

echo "--- PyCodeKG rebuild: LanceDB ---"
poetry run pycodekg-build-lancedb --repo "$REPO_ROOT" --wipe

echo "--- PyCodeKG rebuild: complete ---"
