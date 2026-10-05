"""Regression table rows. The table records estimates; it does not rank models."""

from __future__ import annotations

import csv
from pathlib import Path


def write_regression_table(rows: list[dict[str, object]], path: Path) -> None:
    """Write one row per coefficient. An empty table is an error."""
    if not rows:
        raise ValueError("The regression table has no rows.")
    fieldnames = list(rows[0])
    for row in rows:
        if list(row) != fieldnames:
            raise ValueError("Regression table rows do not share one column order.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
