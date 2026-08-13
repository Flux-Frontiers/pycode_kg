"""
render.py — Shared Markdown rendering primitives.

Every PyCodeKG surface that emits Markdown — the MCP tools, the Click
commands, and the thorough-analysis report — builds the same GitHub-flavored
tables by hand.  Hand-rolled separator rows drift (column counts stop matching
headers, alignment differs between the CLI and MCP rendering of the same data),
so the construction lives here once.

Usage::

    from pycode_kg.render import md_table

    lines = md_table(
        ["Rank", "Score", "Module"],
        [(1, f"{0.12:.6f}", "`src/pkg/a.py`")],
        aligns="rrl",
    )
"""

from collections.abc import Iterable, Sequence

__all__ = ["md_table"]

_SEPARATORS = {"l": ":---", "c": ":---:", "r": "---:"}


def md_table(
    headers: Sequence[str],
    rows: Iterable[Sequence[object]],
    aligns: str | None = None,
) -> list[str]:
    """Build a GitHub-flavored Markdown table as a list of lines.

    :param headers: Column headers, one per column.
    :param rows: Iterable of row sequences.  Each cell is rendered with
        ``str()``; pre-format numbers and backtick any code spans yourself.
        Rows shorter than *headers* are padded with empty cells; longer rows
        are truncated, so a ragged row can never break the table.
    :param aligns: Per-column alignment as a string of ``l``/``c``/``r``
        characters, e.g. ``"lrr"``.  Defaults to left-aligning every column.
        Shorter than *headers* means the remaining columns are left-aligned.
    :return: List of Markdown lines (header, separator, then one per row).
        Returns an empty list when *headers* is empty.
    :raises ValueError: If *aligns* contains a character other than l/c/r.
    """
    if not headers:
        return []

    width = len(headers)
    spec = (aligns or "").ljust(width, "l")[:width]
    bad = set(spec) - set(_SEPARATORS)
    if bad:
        raise ValueError(f"invalid alignment character(s) {sorted(bad)}; expected 'l', 'c', or 'r'")

    lines = [
        "| " + " | ".join(str(h) for h in headers) + " |",
        "| " + " | ".join(_SEPARATORS[c] for c in spec) + " |",
    ]
    for row in rows:
        cells = [str(c) for c in row][:width]
        cells += [""] * (width - len(cells))
        lines.append("| " + " | ".join(cells) + " |")
    return lines
