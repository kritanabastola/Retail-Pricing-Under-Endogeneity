"""Shared figure style for the cereals exploratory plots.

Every saved figure records the sample, the row count, and the units in a
metadata catalog. The catalog is the denominator list for the memo.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

from pricing_research.paths import portable_path

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

INK = "#1f2933"
MUTED = "#52606d"
ACCENT = "#1d4e89"
FILL = "#d9e2ec"
GRID = "#e4e7eb"


def apply_style() -> None:
    """Set one matplotlib style for the exploratory figures."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "axes.axisbelow": True,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "regular",
            "figure.dpi": 140,
        }
    )


def new_figure(ncols: int = 1):
    """Open a wide figure. ``ncols`` greater than 1 returns a row of axes."""
    width = 7.4 if ncols == 1 else 10.2
    return plt.subplots(1, ncols, figsize=(width, 4.6))


def save_figure(
    figure: plt.Figure,
    path: Path,
    catalog: list[dict[str, object]],
    *,
    figure_id: str,
    title: str,
    sample: str,
    n_rows: int,
    units: str,
    definition: str,
) -> None:
    """Write a PNG and append its denominator record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)
    catalog.append(
        {
            "figure_id": figure_id,
            "path": portable_path(path),
            "title": title,
            "sample": sample,
            "n_rows": n_rows,
            "units": units,
            "definition": definition,
            "causal_claim": False,
        }
    )


def write_catalog(path: Path, catalog: list[dict[str, object]]) -> None:
    """Write figure metadata as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
