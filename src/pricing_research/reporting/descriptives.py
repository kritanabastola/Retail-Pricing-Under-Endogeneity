"""Sample statistics for the exploratory memo.

These functions describe rows that are already in memory. They do not decide
which Kilts rows belong in the log sample, and they do not estimate a demand
equation.
"""

from __future__ import annotations

import math

import numpy as np

PRICE_CHANGE_TOLERANCE = 0.001


def pearson_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Pearson correlation. Both arrays must be finite and the same length."""
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Correlation requires at least two aligned finite rows.")
    if not (np.isfinite(x).all() and np.isfinite(y).all()):
        raise ValueError("Correlation inputs must be finite.")
    x_centered = x - x.mean()
    y_centered = y - y.mean()
    denom = math.sqrt(float(np.dot(x_centered, x_centered) * np.dot(y_centered, y_centered)))
    if denom == 0:
        raise ValueError("Correlation is undefined when either series has zero variance.")
    return float(np.dot(x_centered, y_centered) / denom)


def within_sum_of_squares_share(values: np.ndarray, group_means: np.ndarray) -> float:
    """Share of variance that remains after subtracting group means.

    ``group_means`` is aligned to ``values``. The share is one when every
    group mean equals the grand mean, and zero when every row equals its
    group mean.
    """
    if len(values) != len(group_means) or len(values) < 2:
        raise ValueError("Within-share requires aligned rows and at least two of them.")
    centered = values - values.mean()
    total = float(np.dot(centered, centered))
    if total == 0:
        raise ValueError("Within-share is undefined when the series has zero variance.")
    residual = values - group_means
    return float(np.dot(residual, residual) / total)


def herfindahl(amounts: np.ndarray) -> float:
    """Herfindahl index of nonnegative amounts. A single product returns 1."""
    if len(amounts) == 0 or np.any(amounts < 0) or not np.isfinite(amounts).all():
        raise ValueError("Herfindahl amounts must be nonnegative and finite.")
    total = float(amounts.sum())
    if total <= 0:
        raise ValueError("Herfindahl is undefined when the total is not positive.")
    shares = amounts / total
    return float(np.dot(shares, shares))


def largest_share(amounts: np.ndarray, n_units: int) -> float:
    """Share of the total held by the ``n_units`` largest amounts."""
    if n_units < 1 or n_units > len(amounts):
        raise ValueError("The unit count must fall between 1 and the number of amounts.")
    total = float(amounts.sum())
    if total <= 0:
        raise ValueError("A share requires a positive total.")
    ordered = np.sort(amounts)[::-1]
    return float(ordered[:n_units].sum() / total)


def coverage_ratio(
    weeks_observed: int,
    first_week: int,
    last_week: int,
    missing_weeks: set[int],
) -> float:
    """Observed weeks divided by category weeks inside the product's own span.

    Weeks in ``missing_weeks`` are absent for the whole category. They are not
    part of the denominator. A week outside the span is not part of it either.
    """
    if weeks_observed < 1 or last_week < first_week:
        raise ValueError("Coverage requires a nonempty week span.")
    eligible = [
        week
        for week in range(first_week, last_week + 1)
        if week not in missing_weeks
    ]
    if not eligible or weeks_observed > len(eligible):
        raise ValueError("Observed weeks cannot exceed the category weeks inside the span.")
    return weeks_observed / len(eligible)


def price_changed(price: float, previous: float, tolerance: float = PRICE_CHANGE_TOLERANCE) -> bool:
    """True when two observed unit prices differ by more than ``tolerance`` dollars."""
    return abs(price - previous) > tolerance


def quantile_bin_means(x: np.ndarray, y: np.ndarray, n_bins: int = 20) -> list[dict[str, float]]:
    """Mean of ``y`` inside quantile bins of ``x``. Empty edge bins are dropped."""
    if len(x) != len(y) or n_bins < 2:
        raise ValueError("Bin means require aligned arrays and at least two bins.")
    edges = np.quantile(x, np.linspace(0, 1, n_bins + 1))
    edges = np.unique(edges)
    if len(edges) < 3:
        raise ValueError("Quantile bins need more than one distinct x value.")
    bins = np.digitize(x, edges[1:-1], right=False)
    rows: list[dict[str, float]] = []
    for bin_id in range(len(edges) - 1):
        mask = bins == bin_id
        count = int(mask.sum())
        if count == 0:
            continue
        rows.append(
            {
                "bin": float(bin_id + 1),
                "n": float(count),
                "x_mean": float(x[mask].mean()),
                "y_mean": float(y[mask].mean()),
            }
        )
    return rows
