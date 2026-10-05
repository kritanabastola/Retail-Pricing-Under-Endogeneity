"""Synthetic two-stage least squares. These functions do not read Kilts rows.

A strong first stage is not an exclusion restriction. The invalid design below
is the demonstration of that point.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pricing_research.estimation.ols import EstimationError


@dataclass(frozen=True)
class SyntheticIV:
    """A labeled synthetic fit. ``empirical`` is always false."""

    design: str
    empirical: bool
    n: int
    true_price_coefficient: float
    estimated_price_coefficient: float
    first_stage_coefficient: float
    direct_instrument_effect_in_outcome: float
    recovers_the_price_coefficient: bool
    note: str


def just_identified_slope(
    outcome: np.ndarray,
    endogenous: np.ndarray,
    instrument: np.ndarray,
) -> tuple[float, float]:
    """Slope from just-identified 2SLS with an intercept and one instrument.

    The instrument is not assumed valid. Callers that pass a Kilts series are
    outside what this helper is for; it has no data-source check because it
    only sees arrays. The audit command does not pass Kilts columns here.
    """
    y = np.asarray(outcome, dtype=np.float64)
    x = np.asarray(endogenous, dtype=np.float64)
    z = np.asarray(instrument, dtype=np.float64)
    if y.shape != x.shape or y.shape != z.shape or y.ndim != 1 or y.size < 3:
        raise EstimationError("2SLS needs three aligned vectors of length at least 3.")
    if not (np.isfinite(y).all() and np.isfinite(x).all() and np.isfinite(z).all()):
        raise EstimationError("2SLS inputs must be finite.")
    y = y - y.mean()
    x = x - x.mean()
    z = z - z.mean()
    instrument_ss = float(np.dot(z, z))
    if instrument_ss <= 0:
        raise EstimationError("The instrument has no variation.")
    first_stage = float(np.dot(z, x) / instrument_ss)
    fitted = first_stage * z
    fitted_ss = float(np.dot(fitted, fitted))
    if fitted_ss <= 0:
        raise EstimationError("The first stage fitted value has no variation.")
    return float(np.dot(fitted, y) / fitted_ss), first_stage


def synthetic_iv_examples(seed: int = 20261005, n: int = 20_000) -> list[SyntheticIV]:
    """One valid design and one design in which the instrument shifts demand."""
    rng = np.random.default_rng(seed)
    valid_instrument = rng.normal(size=n)
    valid_price = 0.8 * valid_instrument + rng.normal(scale=0.5, size=n)
    valid_outcome = -1.4 * valid_price + rng.normal(scale=0.5, size=n)
    valid_beta, valid_first = just_identified_slope(valid_outcome, valid_price, valid_instrument)

    invalid_instrument = rng.normal(size=n)
    invalid_price = 1.2 * invalid_instrument + rng.normal(scale=0.3, size=n)
    invalid_outcome = (
        -1.4 * invalid_price + 0.9 * invalid_instrument + rng.normal(scale=0.3, size=n)
    )
    invalid_beta, invalid_first = just_identified_slope(
        invalid_outcome, invalid_price, invalid_instrument
    )
    return [
        SyntheticIV(
            design="valid_excluded_instrument",
            empirical=False,
            n=n,
            true_price_coefficient=-1.4,
            estimated_price_coefficient=valid_beta,
            first_stage_coefficient=valid_first,
            direct_instrument_effect_in_outcome=0.0,
            recovers_the_price_coefficient=abs(valid_beta - (-1.4)) < 0.05,
            note="Synthetic rows. The instrument shifts price and is excluded from the outcome.",
        ),
        SyntheticIV(
            design="instrument_shifts_demand_directly",
            empirical=False,
            n=n,
            true_price_coefficient=-1.4,
            estimated_price_coefficient=invalid_beta,
            first_stage_coefficient=invalid_first,
            direct_instrument_effect_in_outcome=0.9,
            recovers_the_price_coefficient=abs(invalid_beta - (-1.4)) < 0.05,
            note=(
                "Synthetic rows. The first stage is strong because the instrument "
                "shifts price, and the 2SLS slope is not the price coefficient "
                "because the instrument also shifts the outcome."
            ),
        ),
    ]


def assumed_movement_change(elasticity: float, price_ratio: float) -> float:
    """Proportional movement change under an assumed constant elasticity.

    This is arithmetic. It is not an estimated causal effect.
    """
    if price_ratio <= 0:
        raise EstimationError("A price ratio must be positive.")
    return float(np.exp(elasticity * np.log(price_ratio)) - 1.0)


def assumed_revenue_change(elasticity: float, price_ratio: float) -> float:
    """Proportional revenue change if quantity scales by the assumed elasticity.

    Revenue scales by ``price_ratio ** (1 + elasticity)``. At an assumed
    elasticity of −1 the revenue factor is 1. The function does not say the
    elasticity is known.
    """
    if price_ratio <= 0:
        raise EstimationError("A price ratio must be positive.")
    return float(price_ratio ** (1.0 + elasticity) - 1.0)
