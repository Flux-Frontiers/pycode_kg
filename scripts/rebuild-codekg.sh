#!/usr/bin/env bash
# Rebuild CodeKG SQLite knowledge graph and LanceDB semantic index.
# Invoked by pre-commit after pytest succeeds.
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "--- CodeKG rebuild: SQLite ---"
poetry run codekg-build-sqlite --repo "$REPO_ROOT" --wipe

echo "--- CodeKG rebuild: LanceDB ---"
poetry run codekg-build-lancedb --repo "$REPO_ROOT" --wipe

echo "--- CodeKG rebuild: complete ---"
