"""Synthetic checks for the baseline estimator. These arrays are not Kilts rows."""

from pathlib import Path

import numpy as np
import pytest
from scipy.stats import t as student_t

from pricing_research.estimation.ols import (
    EstimationError,
    cooks_distance,
    fit_ols,
    loglog_associated_change,
    remaining_sum_of_squares_share,
)
from pricing_research.estimation.ppml import fit_ppml
from pricing_research.estimation.registry import COMPARISON_MODELS, SELECTION_MODELS
from pricing_research.estimation.tables import write_regression_table

ROOT = Path(__file__).resolve().parents[2]


def test_loglog_slope_recovers_a_known_elasticity() -> None:
    price = np.array([1.0, 1.2, 0.8, 1.5, 0.9, 1.1])
    beta = -1.5
    movement = np.exp(0.4 + beta * np.log(price))
    fit = fit_ols(
        np.log(movement),
        np.log(price),
        ["log_unit_price"],
        np.array([1, 1, 2, 2, 3, 3]),
        add_intercept=True,
    )
    assert fit.beta[1] == pytest.approx(beta)
    low, high, critical = fit.interval()
    se = fit.store_se()
    assert critical == pytest.approx(student_t.ppf(0.975, fit.n_store_clusters - 1))
    assert low[1] == pytest.approx(fit.beta[1] - critical * se[1])
    assert high[1] == pytest.approx(fit.beta[1] + critical * se[1])
    assert loglog_associated_change(beta, 1.10) == pytest.approx(1.10**beta - 1)


def test_within_estimator_recovers_the_slope_when_group_means_are_confounded() -> None:
    group = np.repeat(np.arange(12), 8)
    alpha = np.linspace(-2.0, 2.0, 12)
    price = alpha[group] + np.tile(np.linspace(-0.4, 0.4, 8), 12)
    beta = -1.25
    outcome = alpha[group] + beta * price
    within = fit_ols(outcome, price, ["log_unit_price"], group, absorb=[group], fe_rank=12)
    pooled = fit_ols(outcome, price, ["log_unit_price"], group, add_intercept=True)
    assert within.beta[0] == pytest.approx(beta)
    assert abs(float(pooled.beta[1]) - beta) > 0.5


def test_two_way_effects_recover_the_slope() -> None:
    entity = np.repeat(np.arange(8), 10)
    time = np.tile(np.arange(10), 8)
    alpha = np.linspace(-0.5, 0.5, 8)
    tau = np.linspace(-0.3, 0.3, 10)
    idiosyncratic = np.sin(np.arange(entity.size) * 0.7)
    price = 0.4 * alpha[entity] + 0.4 * tau[time] + idiosyncratic
    beta = -0.8
    outcome = alpha[entity] + tau[time] + beta * price
    fit = fit_ols(
        outcome,
        price,
        ["log_unit_price"],
        entity,
        absorb=[entity, time],
        week_clusters=time,
        fe_rank=8 + 10 - 1,
    )
    assert fit.beta[0] == pytest.approx(beta, abs=1e-6)
    assert fit.projection["converged"] is True
    assert fit.twoway_positive_semidefinite is not None


def test_no_within_variation_is_rejected() -> None:
    group = np.repeat(np.arange(3), 4)
    price = np.repeat([1.0, 2.0, 3.0], 4)
    outcome = group.astype(float) + np.linspace(0, 1, group.size)
    with pytest.raises(EstimationError, match="no usable variation"):
        fit_ols(outcome, price, ["log_unit_price"], group, absorb=[group], fe_rank=3)
    assert remaining_sum_of_squares_share(price, [group]) == pytest.approx(0)


def test_invalid_inputs_are_rejected() -> None:
    outcome = np.array([1.0, 2.0, 3.0, 4.0])
    price = np.array([1.0, 2.0, 1.5, 2.5])
    with pytest.raises(EstimationError):
        fit_ols(
            np.array([1.0, np.nan, 3.0, 4.0]),
            price,
            ["x"],
            np.array([1, 1, 2, 2]),
            add_intercept=True,
        )
    with pytest.raises(EstimationError):
        fit_ols(outcome, price, ["x"], np.ones(4, dtype=int), add_intercept=True)
    with pytest.raises(EstimationError):
        loglog_associated_change(-1.0, 0.0)
    identical = np.column_stack([price, price])
    with pytest.raises(EstimationError, match="collinear"):
        fit_ols(outcome, identical, ["x", "x_copy"], np.array([1, 1, 2, 2]), add_intercept=True)


def test_cluster_standard_error_matches_a_direct_sandwich() -> None:
    outcome = np.array([1.0, 2.0, 2.0, 5.0, 1.5, 4.0])
    price = np.array([1.0, 2.0, 1.0, 3.0, 2.0, 4.0])
    store = np.array([10, 10, 20, 20, 30, 30])
    fit = fit_ols(outcome, price, ["x"], store, add_intercept=True)
    design = np.column_stack([np.ones(outcome.size), price])
    beta = np.linalg.solve(design.T @ design, design.T @ outcome)
    residual = outcome - design @ beta
    scores = []
    for label in (10, 20, 30):
        mask = store == label
        scores.append(design[mask].T @ residual[mask])
    score_matrix = np.vstack(scores)
    bread = np.linalg.inv(design.T @ design)
    scale = (3 / 2) * ((outcome.size - 1) / (outcome.size - beta.size))
    variance = scale * (bread @ (score_matrix.T @ score_matrix) @ bread)
    assert fit.beta == pytest.approx(beta)
    assert np.diag(fit.vcov_store) == pytest.approx(np.diag(variance))


def test_ppml_recovers_a_known_conditional_mean_slope() -> None:
    rng = np.random.default_rng(20261005)
    group = np.repeat(np.arange(40), 50)
    alpha = np.linspace(-0.4, 0.4, 40)
    price = alpha[group] + rng.normal(scale=0.8, size=group.size)
    beta = -0.7
    expected = np.exp(alpha[group] + beta * price)
    count = rng.poisson(expected)
    fit = fit_ppml(count.astype(float), price, ["log_unit_price"], group, groups=group)
    assert fit.converged is True
    assert fit.beta[0] == pytest.approx(beta, abs=0.12)
    assert fit.names == ["log_unit_price"]


def test_ppml_rejects_negative_counts() -> None:
    with pytest.raises(EstimationError, match="negative"):
        fit_ppml(
            np.array([1.0, -1.0, 2.0, 0.0]),
            np.array([1.0, 2.0, 1.5, 2.5]),
            ["x"],
            np.array([1, 1, 2, 2]),
            add_intercept=True,
        )


def test_cooks_distance_is_finite_on_a_known_sample() -> None:
    group = np.repeat(np.arange(6), 5)
    price = np.tile(np.linspace(-1, 1, 5), 6) + group
    noise = np.random.default_rng(4).normal(scale=0.05, size=price.size)
    outcome = -0.5 * price + group + noise
    fit = fit_ols(outcome, price, ["x"], group, absorb=[group], fe_rank=6, keep_arrays=True)
    distance = cooks_distance(fit)
    assert distance.shape == price.shape
    assert np.isfinite(distance).all()


def test_table_writer_rejects_an_empty_or_ragged_table(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_regression_table([], tmp_path / "empty.csv")
    with pytest.raises(ValueError):
        write_regression_table(
            [{"model_id": "M0"}, {"estimate": 1}],
            tmp_path / "ragged.csv",
        )
    destination = tmp_path / "rows.csv"
    write_regression_table(
        [{"model_id": "M0", "estimate": -1.2, "causal_claim": False}],
        destination,
    )
    text = destination.read_text()
    assert "model_id,estimate,causal_claim" in text
    assert "M0,-1.2,False" in text


def test_registry_matches_the_specification_file_and_omits_log1p() -> None:
    text = (ROOT / "configs" / "baseline_models.yaml").read_text()
    confirmatory = [spec for spec in COMPARISON_MODELS if spec.confirmatory]
    assert [spec.model_id for spec in confirmatory] == ["M5_confirmatory"]
    for spec in COMPARISON_MODELS + SELECTION_MODELS:
        assert f"id: {spec.model_id}" in text
        assert "log1p" not in spec.regressors
        assert "log_one_plus_move" not in spec.regressors
        assert "upc_week" not in spec.absorb
        assert "store_week" not in spec.absorb
    assert "log_one_plus_move" in text
