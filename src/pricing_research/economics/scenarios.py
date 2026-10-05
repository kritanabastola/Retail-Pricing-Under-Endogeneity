"""Constant-elasticity accounting scenarios.

A coefficient enters only as a stated elasticity. Nothing here estimates
demand, signs a causal effect, or solves a pricing equilibrium.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# The full menu. The widest moves are what limit comparable historical support.
PRICE_RATIOS: tuple[float, ...] = (0.90, 0.95, 0.98, 0.99, 1.00, 1.01, 1.02, 1.05, 1.10)
# A smaller menu a store could post without a 10 percent move.
NARROW_RATIOS: tuple[float, ...] = (0.98, 0.99, 1.00, 1.01, 1.02)
# Stated worsening of the recorded margin, in percentage points. Not estimated.
LESS_FAVORABLE_MARGIN_POINTS = 10.0
PRICE_TOLERANCE = 1e-8


class ScenarioError(ValueError):
    """Raised when a scenario input breaks a feasibility guardrail."""


@dataclass(frozen=True)
class ElasticityCase:
    """One stated own-price elasticity and the label that keeps it honest."""

    case_id: str
    elasticity: float
    origin: str
    role: str


def require_positive_price_ratio(price_ratio: float) -> float:
    """Reject a nonpositive price ratio before any power is taken."""
    ratio = float(price_ratio)
    if not np.isfinite(ratio) or ratio <= 0.0:
        raise ScenarioError("A scenario price ratio must be finite and positive.")
    return ratio


def require_elasticity(elasticity: float) -> float:
    """Reject a nonfinite elasticity. A positive value is allowed and labeled later."""
    value = float(elasticity)
    if not np.isfinite(value):
        raise ScenarioError("An elasticity must be finite.")
    return value


def quantity_factor(price_ratio: float, elasticity: float) -> float:
    """Return ``(P1 / P0) ** ε`` for one price ratio."""
    ratio = require_positive_price_ratio(price_ratio)
    slope = require_elasticity(elasticity)
    return float(ratio**slope)


def revenue_factor(price_ratio: float, elasticity: float) -> float:
    """Return ``(P1 / P0) ** (1 + ε)``. At ε = −1 this factor is 1."""
    ratio = require_positive_price_ratio(price_ratio)
    slope = require_elasticity(elasticity)
    return float(ratio ** (1.0 + slope))


def quantities_after_price_change(
    quantity: np.ndarray,
    price_ratio: float,
    elasticity: float,
) -> np.ndarray:
    """Scale each baseline quantity by the same constant-elasticity factor.

    Units stay in items. The factor does not add a promotion shock, a
    cross-price term, or a store-traffic term.
    """
    baseline = np.asarray(quantity, dtype=np.float64)
    if baseline.ndim != 1 or baseline.size == 0:
        raise ScenarioError("Quantity must be a non-empty vector.")
    if not np.isfinite(baseline).all() or np.any(baseline < 0.0):
        raise ScenarioError("Baseline quantity must be finite and nonnegative.")
    return baseline * quantity_factor(price_ratio, elasticity)


def unit_cost_from_profit_percent(unit_price: np.ndarray, profit_percent: np.ndarray) -> np.ndarray:
    """Return unit average acquisition cost ``P * (1 - PROFIT/100)``.

    ``PROFIT`` is the manual's cents of gross margin per dollar of sales.
    The result is a historical cost proxy for the baseline week. It is not
    marginal cost and not replacement cost.
    """
    price = np.asarray(unit_price, dtype=np.float64)
    profit = np.asarray(profit_percent, dtype=np.float64)
    if price.shape != profit.shape or price.ndim != 1:
        raise ScenarioError("Price and PROFIT must be aligned vectors.")
    if not np.isfinite(price).all() or np.any(price <= 0.0):
        raise ScenarioError("Unit price must be finite and positive.")
    if not np.isfinite(profit).all() or np.any(profit < -100.0) or np.any(profit > 100.0):
        raise ScenarioError("PROFIT percent must lie between -100 and 100.")
    return price * (1.0 - profit / 100.0)


def less_favorable_unit_cost(
    unit_price: np.ndarray,
    profit_percent: np.ndarray,
    margin_points: float = LESS_FAVORABLE_MARGIN_POINTS,
) -> tuple[np.ndarray, int]:
    """Raise unit cost by a stated margin worsening, holding the baseline price.

    Ten points means a recorded 25.3 percent margin is treated as 15.3 percent.
    The worsening is an assumption. A shifted margin below −100 is capped at
    −100, and the cap count is returned. Cost may still exceed price.
    """
    points = float(margin_points)
    if not np.isfinite(points) or points < 0.0:
        raise ScenarioError("The margin worsening must be finite and nonnegative.")
    shifted = np.asarray(profit_percent, dtype=np.float64) - points
    capped = int(np.sum(shifted < -100.0))
    shifted = np.maximum(shifted, -100.0)
    return unit_cost_from_profit_percent(unit_price, shifted), capped


def prices_inside_support(
    baseline_price: np.ndarray,
    price_min: np.ndarray,
    price_max: np.ndarray,
    price_ratio: float,
    tolerance: float = PRICE_TOLERANCE,
) -> np.ndarray:
    """Mark candidate prices that sit inside the pair's historical unit-price range."""
    ratio = require_positive_price_ratio(price_ratio)
    price = np.asarray(baseline_price, dtype=np.float64)
    low = np.asarray(price_min, dtype=np.float64)
    high = np.asarray(price_max, dtype=np.float64)
    if price.shape != low.shape or price.shape != high.shape:
        raise ScenarioError("Support bounds must align with the baseline price.")
    candidate = price * ratio
    return (candidate >= low - tolerance) & (candidate <= high + tolerance)


def support_for_ratios(
    baseline_price: np.ndarray,
    price_min: np.ndarray,
    price_max: np.ndarray,
    ratios: tuple[float, ...],
) -> np.ndarray:
    """Pairs whose baseline can reach every listed ratio without leaving history."""
    mask = np.ones(np.asarray(baseline_price).shape[0], dtype=bool)
    for ratio in ratios:
        mask &= prices_inside_support(baseline_price, price_min, price_max, ratio)
    return mask


def accounting_totals(
    quantity: np.ndarray,
    unit_price: np.ndarray,
    unit_cost: np.ndarray,
    price_ratio: float,
    elasticity: float,
    mask: np.ndarray | None = None,
) -> dict[str, float | int | None]:
    """Sum items, revenue, and accounting gross profit before and after the price ratio.

    Gross profit is ``(P - c) * Q`` with ``c`` held at the baseline unit cost.
    It is not operating profit. Percent changes are omitted when the baseline
    total is not positive.
    """
    ratio = require_positive_price_ratio(price_ratio)
    require_elasticity(elasticity)
    quantity = np.asarray(quantity, dtype=np.float64)
    price = np.asarray(unit_price, dtype=np.float64)
    cost = np.asarray(unit_cost, dtype=np.float64)
    if mask is None:
        mask = np.ones(quantity.shape[0], dtype=bool)
    else:
        mask = np.asarray(mask, dtype=bool)
    if not (quantity.shape == price.shape == cost.shape == mask.shape):
        raise ScenarioError("Scenario vectors must be aligned.")
    if np.any(cost[mask] < 0.0):
        raise ScenarioError("Unit cost must be nonnegative.")
    keep_q = quantity[mask]
    keep_p = price[mask]
    keep_c = cost[mask]
    new_q = keep_q * quantity_factor(ratio, elasticity)
    new_p = keep_p * ratio
    revenue_0 = float(np.sum(keep_p * keep_q))
    revenue_1 = float(np.sum(new_p * new_q))
    profit_0 = float(np.sum((keep_p - keep_c) * keep_q))
    profit_1 = float(np.sum((new_p - keep_c) * new_q))
    quantity_0 = float(np.sum(keep_q))
    quantity_1 = float(np.sum(new_q))
    return {
        "pairs": int(mask.sum()),
        "quantity_0": quantity_0,
        "quantity_1": quantity_1,
        "quantity_change": _percent(quantity_1, quantity_0),
        "revenue_0": revenue_0,
        "revenue_1": revenue_1,
        "revenue_change": _percent(revenue_1, revenue_0),
        "gross_profit_0": profit_0,
        "gross_profit_1": profit_1,
        "gross_profit_change": _percent(profit_1, profit_0),
        "gross_profit_dollar_change": profit_1 - profit_0,
        "closed_form_quantity_change": quantity_factor(ratio, elasticity) - 1.0,
        "closed_form_revenue_change": revenue_factor(ratio, elasticity) - 1.0,
    }


def _percent(new: float, old: float) -> float | None:
    if old > 0.0 and np.isfinite(new) and np.isfinite(old):
        return float(new / old - 1.0)
    return None
