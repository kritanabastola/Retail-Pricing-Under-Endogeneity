"""Synthetic checks for the identification audit. No Kilts rows."""

import numpy as np
import pytest

from pricing_research.estimation.identify import _adjacent
from pricing_research.estimation.instruments import CANDIDATES, approved_candidates
from pricing_research.estimation.iv_demo import (
    assumed_movement_change,
    assumed_revenue_change,
    just_identified_slope,
    synthetic_iv_examples,
)
from pricing_research.estimation.ols import EstimationError, remaining_sum_of_squares_share


def test_no_instrument_is_approved() -> None:
    assert approved_candidates() == ()
    assert {item.verdict for item in CANDIDATES} == {"REJECTED"}
    assert len(CANDIDATES) >= 8


def test_valid_synthetic_iv_recovers_the_price_coefficient() -> None:
    valid, invalid = synthetic_iv_examples()
    assert valid.empirical is False
    assert valid.recovers_the_price_coefficient
    assert valid.estimated_price_coefficient == pytest.approx(-1.4, abs=0.05)
    assert invalid.empirical is False
    assert invalid.recovers_the_price_coefficient is False
    assert abs(invalid.first_stage_coefficient) > 0.5
    assert abs(invalid.estimated_price_coefficient - invalid.true_price_coefficient) > 0.4


def test_a_week_level_series_is_absorbed_by_week_effects() -> None:
    week = np.repeat(np.arange(12), 30)
    national = week.astype(np.float64) * 0.25 + 3.0
    assert remaining_sum_of_squares_share(national, [week]) == pytest.approx(0.0)


def test_constant_margin_cost_is_an_identity_in_price() -> None:
    price = np.array([1.5, 2.0, 2.5, 3.0])
    margin = np.full(price.shape, 0.25)
    log_cost = np.log(price * (1.0 - margin))
    correlation = np.corrcoef(np.log(price), log_cost)[0, 1]
    assert correlation == pytest.approx(1.0)


def test_unit_elasticity_assumption_does_not_change_revenue() -> None:
    assert assumed_revenue_change(-1.0, 1.10) == pytest.approx(0.0)
    assert assumed_movement_change(-1.0, 1.10) == pytest.approx(1.0 / 1.10 - 1.0)
    with pytest.raises(EstimationError):
        assumed_revenue_change(-1.0, 0.0)


def test_zero_instrument_is_rejected() -> None:
    outcome = np.array([1.0, 2.0, 3.0, 4.0])
    price = np.array([1.0, 1.5, 2.0, 2.5])
    with pytest.raises(EstimationError):
        just_identified_slope(outcome, price, np.ones(4))


def test_price_lead_requires_an_adjacent_calendar_week() -> None:
    pair = np.array([1, 1, 1, 2])
    week = np.array([1, 2, 4, 1])
    values = np.array([10.0, 20.0, 30.0, 40.0])
    lead = _adjacent(values, pair, week, lead=True)
    lag = _adjacent(values, pair, week, lead=False)
    assert lead[0] == pytest.approx(20.0)
    assert np.isnan(lead[1])
    assert np.isnan(lead[2])
    assert lag[1] == pytest.approx(10.0)
    assert np.isnan(lag[2])
