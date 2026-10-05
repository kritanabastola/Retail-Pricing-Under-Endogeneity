"""Synthetic checks for price scenarios. No Kilts rows and no causal claim."""

import numpy as np
import pytest

from pricing_research.economics.counterfactual import _decision, _jsonable
from pricing_research.economics.scenarios import (
    ScenarioError,
    accounting_totals,
    less_favorable_unit_cost,
    prices_inside_support,
    quantities_after_price_change,
    revenue_factor,
    support_for_ratios,
    unit_cost_from_profit_percent,
)


def test_unit_elasticity_leaves_revenue_unchanged() -> None:
    quantity = np.array([10.0, 4.0])
    price = np.array([2.0, 5.0])
    cost = np.array([1.0, 2.5])
    totals = accounting_totals(quantity, price, cost, 1.10, -1.0)
    assert totals["revenue_change"] == pytest.approx(0.0)
    assert totals["quantity_change"] == pytest.approx(1.0 / 1.10 - 1.0)
    assert revenue_factor(1.10, -1.0) == pytest.approx(1.0)


def test_constant_unit_cost_does_not_scale_gross_profit_with_revenue() -> None:
    quantity = np.array([10.0])
    price = np.array([2.0])
    cost = unit_cost_from_profit_percent(price, np.array([25.0]))
    assert cost[0] == pytest.approx(1.5)
    totals = accounting_totals(quantity, price, cost, 1.10, -1.0)
    assert totals["revenue_1"] == pytest.approx(totals["revenue_0"])
    assert totals["gross_profit_1"] > totals["gross_profit_0"]


def test_recorded_margin_matches_the_manual_identity_at_the_baseline() -> None:
    price = np.array([3.0])
    quantity = np.array([8.0])
    cost = unit_cost_from_profit_percent(price, np.array([25.3]))
    totals = accounting_totals(quantity, price, cost, 1.0, -2.0)
    sales = 3.0 * 8.0
    assert totals["gross_profit_0"] == pytest.approx(sales * 0.253)


def test_less_favorable_margin_raises_unit_cost() -> None:
    price = np.array([4.0, 4.0])
    profit = np.array([20.0, -95.0])
    recorded = unit_cost_from_profit_percent(price, profit)
    adverse, capped = less_favorable_unit_cost(price, profit, margin_points=10.0)
    assert adverse[0] == pytest.approx(price[0] * 0.90)
    assert adverse[0] > recorded[0]
    assert capped == 1
    assert adverse[1] == pytest.approx(price[1] * 2.0)


def test_a_price_outside_the_pair_range_is_marked_as_extrapolation() -> None:
    price = np.array([3.0, 3.0])
    low = np.array([2.5, 2.95])
    high = np.array([3.4, 3.05])
    inside = prices_inside_support(price, low, high, 1.10)
    assert inside.tolist() == [True, False]
    menu = support_for_ratios(price, low, high, (0.90, 1.00, 1.10))
    assert menu.tolist() == [True, False]


def test_negative_quantity_and_nonpositive_price_ratio_are_rejected() -> None:
    with pytest.raises(ScenarioError):
        quantities_after_price_change(np.array([1.0, -0.1]), 1.02, -1.5)
    with pytest.raises(ScenarioError):
        accounting_totals(np.array([1.0]), np.array([2.0]), np.array([1.0]), 0.0, -1.0)


def test_uniform_ratio_revenue_change_does_not_depend_on_the_subset() -> None:
    quantity = np.array([5.0, 9.0, 2.0])
    price = np.array([2.0, 3.0, 4.0])
    cost = np.array([1.0, 1.2, 2.0])
    everyone = accounting_totals(quantity, price, cost, 0.95, -2.1)
    subset = accounting_totals(
        quantity,
        price,
        cost,
        0.95,
        -2.1,
        np.array([True, False, True]),
    )
    assert everyone["revenue_change"] == pytest.approx(subset["revenue_change"])
    assert everyone["revenue_change"] == pytest.approx(0.95 ** (1.0 - 2.1) - 1.0)


def test_decision_block_never_supports_deployment() -> None:
    body = {
        "grids": {
            "full_menu_historical_support": [
                {
                    "elasticity_case": "central_confirmatory_association",
                    "elasticity": -2.0,
                    "price_ratio": 0.9,
                    "price_change": -0.1,
                    "cost_case": "recorded_average_acquisition_cost",
                    "quantity_change": 0.2,
                    "revenue_change": 0.05,
                    "gross_profit_change": 0.01,
                }
            ]
        }
    }
    decision = _decision(body)
    assert decision["deployment_supported"] is False
    dust = {
        "grids": {
            "full_menu_historical_support": [
                {
                    "elasticity_case": "assumed_unit",
                    "elasticity": -1.0,
                    "price_ratio": 1.1,
                    "price_change": 0.1,
                    "cost_case": "recorded_average_acquisition_cost",
                    "quantity_change": -0.09,
                    "revenue_change": 1e-15,
                    "gross_profit_change": 0.2,
                }
            ]
        }
    }
    assert _decision(dust)["accounting_improvements_only_under_the_stated_elasticity"] == []
    assert decision["accounting_improvements_only_under_the_stated_elasticity"][0][
        "deployment_supported"
    ] is False


def test_false_stays_false_in_the_result_file() -> None:
    assert _jsonable({"causal_claim": False, "pairs": 3}) == {
        "causal_claim": False,
        "pairs": 3,
    }
