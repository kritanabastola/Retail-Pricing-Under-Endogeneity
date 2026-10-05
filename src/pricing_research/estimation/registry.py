"""Executable copy of configs/baseline_models.yaml.

The YAML file is the specification record. These objects are what the fitter
runs. A unit test checks that the ids match.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    """One baseline regression. ``confirmatory`` is true for at most one model."""

    model_id: str
    role: str
    confirmatory: bool
    outcome: str
    regressors: tuple[str, ...]
    absorb: tuple[str, ...]
    estimator: str = "within_ols"
    sample: str = "log"
    loglog_association: bool = True


COMPARISON_MODELS: tuple[ModelSpec, ...] = (
    ModelSpec(
        "M0_pooled_ols",
        "descriptive pooled OLS",
        False,
        "log_move",
        ("log_unit_price",),
        (),
    ),
    ModelSpec(
        "M1_pooled_promotion",
        "pooled OLS with the incomplete promotion indicator",
        False,
        "log_move",
        ("log_unit_price", "promo_coded"),
        (),
    ),
    ModelSpec(
        "M2_upc",
        "product fixed effects",
        False,
        "log_move",
        ("log_unit_price",),
        ("upc",),
    ),
    ModelSpec(
        "M2_upc_and_store",
        "additive product and store fixed effects",
        False,
        "log_move",
        ("log_unit_price",),
        ("upc", "store"),
    ),
    ModelSpec(
        "M3_pair",
        "store-product pair fixed effects",
        False,
        "log_move",
        ("log_unit_price",),
        ("pair",),
    ),
    ModelSpec(
        "M3_pair_week",
        "pair and week fixed effects, promotion not partialled",
        False,
        "log_move",
        ("log_unit_price",),
        ("pair", "week"),
    ),
    ModelSpec(
        "M4_pair_month",
        "pair effects with calendar-month seasonality",
        False,
        "log_move",
        ("log_unit_price",),
        ("pair", "month"),
    ),
    ModelSpec(
        "M4_pair_year_month",
        "pair effects with year-month time effects",
        False,
        "log_move",
        ("log_unit_price",),
        ("pair", "year_month"),
    ),
    ModelSpec(
        "M5_confirmatory",
        "pre-specified confirmatory association",
        True,
        "log_move",
        ("log_unit_price", "promo_coded"),
        ("pair", "week"),
    ),
)

SELECTION_MODELS: tuple[ModelSpec, ...] = (
    ModelSpec(
        "L_level_pair_week",
        "level movement on unit price, pair and week effects",
        False,
        "move",
        ("unit_price",),
        ("pair", "week"),
        loglog_association=False,
    ),
    ModelSpec(
        "P_ppml_pooled",
        "pooled PPML of movement on log unit price",
        False,
        "move",
        ("log_unit_price",),
        (),
        estimator="ppml",
        loglog_association=False,
    ),
    ModelSpec(
        "P_ppml_pair",
        "pair-effect PPML of movement on log unit price",
        False,
        "move",
        ("log_unit_price",),
        ("pair",),
        estimator="ppml",
        loglog_association=False,
    ),
    ModelSpec(
        "S_restore_ok0",
        "confirmatory association with OK=0 positive-sale rows restored",
        False,
        "log_move",
        ("log_unit_price", "promo_coded"),
        ("pair", "week"),
        sample="log_plus_ok0_positive",
    ),
)

WITHIN_PAIR_PRICE_SHARE_FLOOR = 0.20
PRICE_CHANGE_TOLERANCE = 0.001
