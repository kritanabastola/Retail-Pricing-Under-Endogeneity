"""Independent checks. These arrays are not Kilts rows.

The within-transformation check is written with NumPy's least squares, not
with ``fit_ols``. The statsmodels check is skipped when that package is absent.
Neither result is a Dominick's elasticity.
"""

from __future__ import annotations

import numpy as np
import pytest

from pricing_research.economics.scenarios import revenue_factor
from pricing_research.estimation.ols import fit_ols


def test_hand_written_within_least_squares_matches_fit_ols() -> None:
    group = np.repeat(np.arange(12), 8)
    alpha = np.linspace(-2.0, 2.0, 12)
    price = alpha[group] + np.tile(np.linspace(-0.4, 0.4, 8), 12)
    beta = -1.25
    outcome = alpha[group] + beta * price
    counts = np.bincount(group).astype(np.float64)
    price_within = price - (np.bincount(group, weights=price) / counts)[group]
    outcome_within = outcome - (np.bincount(group, weights=outcome) / counts)[group]
    hand, *_rest = np.linalg.lstsq(price_within[:, None], outcome_within, rcond=None)
    project = fit_ols(
        outcome,
        price,
        ["log_unit_price"],
        group,
        absorb=[group],
        fe_rank=12,
    )
    assert hand[0] == pytest.approx(beta)
    assert project.beta[0] == pytest.approx(hand[0])


def test_revenue_factor_matches_the_constant_elasticity_identity() -> None:
    ratio = 1.10
    elasticity = -2.0
    by_hand = ratio * (ratio**elasticity)
    assert revenue_factor(ratio, elasticity) == pytest.approx(by_hand)
    assert by_hand == pytest.approx(1.10 ** (1.0 + elasticity))


def test_statsmodels_dummy_regression_matches_the_within_slope() -> None:
    statsmodels = pytest.importorskip("statsmodels.formula.api")
    group = np.repeat(np.arange(12), 8)
    alpha = np.linspace(-2.0, 2.0, 12)
    price = alpha[group] + np.tile(np.linspace(-0.4, 0.4, 8), 12)
    beta = -1.25
    outcome = alpha[group] + beta * price
    frame = {
        "outcome": outcome,
        "price": price,
        "group": group.astype(str),
    }
    published = statsmodels.ols("outcome ~ price + C(group)", data=frame).fit()
    project = fit_ols(
        outcome,
        price,
        ["log_unit_price"],
        group,
        absorb=[group],
        fe_rank=12,
    )
    assert float(published.params["price"]) == pytest.approx(beta)
    assert project.beta[0] == pytest.approx(float(published.params["price"]))
