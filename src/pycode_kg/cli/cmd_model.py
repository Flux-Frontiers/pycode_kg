"""
cmd_model.py

CLI command for managing the PyCodeKG embedding model cache.

  download-model   — download and cache the sentence-transformer model for offline use
"""

from __future__ import annotations

import click

from pycode_kg.cli.main import cli
from pycode_kg.index import _local_model_path
from pycode_kg.pycodekg import DEFAULT_MODEL


@cli.command("download-model")
@click.option(
    "--model",
    default=DEFAULT_MODEL,
    show_default=True,
    help="SentenceTransformer model name to download.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Re-download even if a local copy already exists.",
)
def download_model(model: str, force: bool) -> None:
    """Download and cache the embedding model for offline use.

    The model is saved to ``.pycodekg/models/<model>/`` in the current working
    directory (or the path set by the ``PYCODEKG_MODEL_DIR`` environment
    variable).  Once cached, ``pycodekg build-lancedb`` and ``pycodekg query``
    will use this local copy without any network access.
    """
    from sentence_transformers import (  # pylint: disable=import-outside-toplevel
        SentenceTransformer,
    )

    local_path = _local_model_path(model)

    if local_path.exists() and not force:
        click.echo(f"Model already cached at {local_path}")
        click.echo("Use --force to re-download.")
        return

    click.echo(f"Downloading model '{model}'...")
    st_model = SentenceTransformer(model)
    local_path.mkdir(parents=True, exist_ok=True)
    st_model.save(str(local_path))
    click.echo(f"OK: model saved to {local_path}")
