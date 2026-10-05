"""Diagnostic figures for the baseline associations.

These plots show fitted associations and residuals. They are not causal graphs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pricing_research.reporting.figures import ACCENT, FILL, INK, MUTED, new_figure, save_figure


def plot_price_coefficients(
    rows: list[dict[str, object]],
    path: Path,
    catalog: list[dict[str, object]],
    *,
    n_rows: int,
) -> None:
    """Store-cluster intervals for the log-price coefficient, one row per model."""
    price_rows = [row for row in rows if row["term"] == "log_unit_price"]
    if len(price_rows) < 2:
        raise ValueError("The coefficient plot needs at least two log-price estimates.")
    labels = [str(row["model_id"]) for row in price_rows]
    estimate = np.array([float(row["estimate"]) for row in price_rows])
    low = np.array([float(row["ci95_low"]) for row in price_rows])
    high = np.array([float(row["ci95_high"]) for row in price_rows])
    position = np.arange(len(labels))
    figure, axes = new_figure()
    axes.axvline(0, color=MUTED, linewidth=0.8)
    axes.errorbar(
        estimate,
        position,
        xerr=[estimate - low, high - estimate],
        fmt="o",
        color=ACCENT,
        ecolor=INK,
        capsize=3,
    )
    axes.set_yticks(position)
    axes.set_yticklabels(labels)
    axes.set_xlabel("Coefficient on log unit price")
    axes.set_title("Log-log price association by specification")
    axes.invert_yaxis()
    save_figure(
        figure,
        path,
        catalog,
        figure_id="baseline_01_coefficients",
        title="Log-log price association by specification",
        sample="cereals log sample, except rows whose model_id says otherwise",
        n_rows=n_rows,
        units="log item movement per log dollar of unit price",
        definition=(
            "Store-clustered 95 percent t intervals. PPML rows, when present, "
            "are elasticities of the conditional mean. None of the intervals is a causal effect."
        ),
    )


def plot_absorbed_variation(
    shares: list[dict[str, object]],
    path: Path,
    catalog: list[dict[str, object]],
    *,
    n_rows: int,
) -> None:
    """Share of log-price variance left after each specification's fixed effects."""
    labels = [str(item["model_id"]) for item in shares]
    values = np.array([float(item["log_unit_price_ss_share_remaining"]) for item in shares])
    figure, axes = new_figure()
    axes.barh(np.arange(len(labels)), values, color=FILL, edgecolor=ACCENT)
    axes.set_yticks(np.arange(len(labels)))
    axes.set_yticklabels(labels)
    axes.set_xlim(0, 1)
    axes.set_xlabel("Share of log unit-price variance remaining")
    axes.set_title("Price variation left for the coefficient")
    axes.invert_yaxis()
    save_figure(
        figure,
        path,
        catalog,
        figure_id="baseline_02_absorbed_price_variation",
        title="Price variation left for the coefficient",
        sample="cereals log sample",
        n_rows=n_rows,
        units="share of variance",
        definition=(
            "One minus the share absorbed by the fixed effects named in the model. "
            "Computed before the slope is used. A share near zero would mean the "
            "fixed effects had removed the price variation."
        ),
    )


def plot_residual_histogram(
    residual: np.ndarray,
    path: Path,
    catalog: list[dict[str, object]],
) -> None:
    """Histogram of confirmatory residuals. The bars are counts of rows."""
    figure, axes = new_figure()
    axes.hist(residual, bins=80, color=FILL, edgecolor=ACCENT)
    axes.set_xlabel("Residual log item movement")
    axes.set_ylabel("Rows")
    axes.set_title("Confirmatory residuals")
    save_figure(
        figure,
        path,
        catalog,
        figure_id="baseline_03_confirmatory_residuals",
        title="Confirmatory residuals",
        sample="cereals log sample, M5 pair and week fixed effects",
        n_rows=int(residual.size),
        units="log item movement",
        definition=(
            "Outcome residual after pair effects, week effects, log unit price, "
            "and the coded promotion indicator. The shape is descriptive."
        ),
    )


def plot_binned_residuals(
    price: np.ndarray,
    residual: np.ndarray,
    path: Path,
    catalog: list[dict[str, object]],
    *,
    n_bins: int = 20,
) -> None:
    """Mean confirmatory residual in quantile bins of residualized log price."""
    quantiles = np.linspace(0, 1, n_bins + 1)
    edges = np.unique(np.quantile(price, quantiles))
    if edges.size < 3:
        raise ValueError("Residualized log price does not have enough distinct values to bin.")
    bins = np.digitize(price, edges[1:-1])
    centers: list[float] = []
    means: list[float] = []
    counts: list[int] = []
    for index in range(int(bins.max()) + 1):
        mask = bins == index
        if not np.any(mask):
            continue
        centers.append(float(price[mask].mean()))
        means.append(float(residual[mask].mean()))
        counts.append(int(mask.sum()))
    figure, axes = new_figure()
    axes.axhline(0, color=MUTED, linewidth=0.8)
    axes.plot(centers, means, color=ACCENT, marker="o")
    axes.set_xlabel("Mean residualized log unit price")
    axes.set_ylabel("Mean residual log movement")
    axes.set_title("Confirmatory residual by price bin")
    save_figure(
        figure,
        path,
        catalog,
        figure_id="baseline_04_binned_residuals",
        title="Confirmatory residual by price bin",
        sample="cereals log sample, M5 residualized regressors",
        n_rows=int(residual.size),
        units="log item movement",
        definition=(
            f"{len(centers)} quantile bins of log unit price after pair and week effects. "
            "Point sizes are not scaled. Bin counts are "
            + ", ".join(str(count) for count in counts)
            + ". A bend would show that the log-log line is a summary, not a literal curve."
        ),
    )
