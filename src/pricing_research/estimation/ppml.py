"""Poisson pseudo-maximum likelihood for a positive or zero count.

The coefficient on log price is an elasticity of the conditional mean when
the mean is log-linear in log price. It is not an elasticity of log(1 + Q),
and it is not causal. One-way fixed effects are concentrated group by group.
Two-way Poisson fixed effects are not estimated here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pricing_research.estimation.ols import (
    EstimationError,
    _cluster_scores,
    _psd,
    _sandwich,
    dense_codes,
    finite_vector,
)

PPML_TOLERANCE = 1e-8
PPML_MAX_ITER = 100
ETA_CLIP = 40.0


@dataclass
class PpmlFit:
    """A fitted Poisson pseudo-likelihood. ``beta`` refers to the conditional mean."""

    names: list[str]
    beta: np.ndarray
    mu: np.ndarray
    vcov_store: np.ndarray
    n: int
    k_total: int
    n_store_clusters: int
    iterations: int
    converged: bool
    includes_fixed_effects: bool


def _weighted_within_beta(
    working: np.ndarray,
    regressors: np.ndarray,
    weights: np.ndarray,
    groups: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """WLS slopes after weighted within-group demeaning. Returns beta, x residual, bread."""
    weight_sums = np.bincount(groups, weights=weights)
    if np.any(weight_sums <= 0):
        raise EstimationError("A Poisson group has no positive weight.")

    def demean(column: np.ndarray) -> np.ndarray:
        weighted_sum = np.bincount(groups, weights=column * weights)
        means = weighted_sum / weight_sums
        return column - means[groups]

    y_resid = demean(working)
    x_resid = np.column_stack(
        [demean(regressors[:, column]) for column in range(regressors.shape[1])]
    )
    weighted_x = x_resid * weights[:, None]
    xtwx = x_resid.T @ weighted_x
    condition = float(np.linalg.cond(xtwx))
    if not np.isfinite(condition) or condition > 1e12:
        raise EstimationError("PPML regressors are collinear inside the groups.")
    beta = np.linalg.solve(xtwx, x_resid.T @ (weights * y_resid))
    return beta, x_resid, np.linalg.inv(xtwx)


def fit_ppml(
    outcome: np.ndarray,
    regressors: np.ndarray,
    names: list[str],
    store_clusters: np.ndarray,
    *,
    groups: np.ndarray | None = None,
    add_intercept: bool = False,
) -> PpmlFit:
    """Fit PPML by iteratively reweighted least squares.

    ``groups`` supplies one-way fixed effects. Without groups, pass
    ``add_intercept=True``. Zeros are allowed. Negative counts are not.
    """
    y = finite_vector(outcome, "count")
    if np.any(y < 0):
        raise EstimationError("PPML counts cannot be negative.")
    if float(y.sum()) <= 0:
        raise EstimationError("PPML is undefined when every count is zero.")
    x_matrix = np.asarray(regressors, dtype=np.float64)
    if x_matrix.ndim == 1:
        x_matrix = x_matrix[:, None]
    if x_matrix.shape != (y.size, len(names)):
        raise EstimationError("PPML regressors do not match the outcome or the names.")
    if not np.isfinite(x_matrix).all():
        raise EstimationError("A PPML regressor contains a non-finite value.")
    if (groups is None) == (not add_intercept):
        raise EstimationError("PPML needs an intercept or one grouping factor, and not both.")
    if add_intercept:
        x_matrix = np.column_stack([np.ones(y.size), x_matrix])
        names = ["intercept", *names]
        return _fit_pooled(y, x_matrix, names, store_clusters)
    assert groups is not None
    groups_dense = dense_codes(groups, "groups", y.size)
    occupied = np.bincount(groups_dense)
    group_total = np.bincount(groups_dense, weights=y)
    if np.any(group_total[occupied > 0] <= 0):
        raise EstimationError(
            "A fixed-effect group has no positive count, so its Poisson effect is undefined."
        )
    fe_rank = group_counts(groups_dense)
    beta = np.zeros(x_matrix.shape[1], dtype=np.float64)
    mu = np.full(y.size, float(y.mean()))
    x_resid = x_matrix
    bread = np.eye(beta.size)
    converged = False
    iterations = 0
    for iterations in range(1, PPML_MAX_ITER + 1):
        eta = np.clip(x_matrix @ beta, -ETA_CLIP, ETA_CLIP)
        exp_eta = np.exp(eta)
        sum_exp = np.bincount(groups_dense, weights=exp_eta)
        log_shift = np.log(group_total[groups_dense]) - np.log(sum_exp[groups_dense])
        mu = np.exp(np.clip(log_shift + eta, -ETA_CLIP, ETA_CLIP))
        working = eta + (y - mu) / mu
        beta_new, x_resid, bread = _weighted_within_beta(working, x_matrix, mu, groups_dense)
        if float(np.max(np.abs(beta_new - beta))) < PPML_TOLERANCE:
            beta = beta_new
            converged = True
            break
        beta = beta_new
    if not converged:
        raise EstimationError(f"PPML did not converge after {PPML_MAX_ITER} iterations.")
    eta = np.clip(x_matrix @ beta, -ETA_CLIP, ETA_CLIP)
    exp_eta = np.exp(eta)
    sum_exp = np.bincount(groups_dense, weights=exp_eta)
    log_shift = np.log(group_total[groups_dense]) - np.log(sum_exp[groups_dense])
    mu = np.exp(np.clip(log_shift + eta, -ETA_CLIP, ETA_CLIP))
    _working, x_resid, bread = _weighted_within_beta(
        eta + (y - mu) / mu,
        x_matrix,
        mu,
        groups_dense,
    )
    store = dense_codes(store_clusters, "store", y.size)
    scores = _cluster_scores(x_resid, y - mu, store)
    k_total = beta.size + fe_rank
    vcov = _sandwich(bread, scores, y.size, k_total)
    if not _psd(vcov):
        raise EstimationError("The PPML cluster variance is not positive semidefinite.")
    return PpmlFit(
        names=list(names),
        beta=beta,
        mu=mu,
        vcov_store=vcov,
        n=int(y.size),
        k_total=int(k_total),
        n_store_clusters=int(scores.shape[0]),
        iterations=iterations,
        converged=True,
        includes_fixed_effects=True,
    )


def group_counts(codes: np.ndarray) -> int:
    return int(codes.max()) + 1


def _fit_pooled(
    y: np.ndarray,
    x_matrix: np.ndarray,
    names: list[str],
    store_clusters: np.ndarray,
) -> PpmlFit:
    beta = np.zeros(x_matrix.shape[1], dtype=np.float64)
    beta[0] = float(np.log(y.mean()))
    mu = np.full(y.size, float(y.mean()))
    converged = False
    iterations = 0
    for iterations in range(1, PPML_MAX_ITER + 1):
        eta = np.clip(x_matrix @ beta, -ETA_CLIP, ETA_CLIP)
        mu = np.exp(eta)
        working = eta + (y - mu) / mu
        weighted_x = x_matrix * mu[:, None]
        xtwx = x_matrix.T @ weighted_x
        beta_new = np.linalg.solve(xtwx, x_matrix.T @ (mu * working))
        if float(np.max(np.abs(beta_new - beta))) < PPML_TOLERANCE:
            beta = beta_new
            converged = True
            break
        beta = beta_new
    if not converged:
        raise EstimationError(f"Pooled PPML did not converge after {PPML_MAX_ITER} iterations.")
    eta = np.clip(x_matrix @ beta, -ETA_CLIP, ETA_CLIP)
    mu = np.exp(eta)
    xtwx = x_matrix.T @ (x_matrix * mu[:, None])
    bread = np.linalg.inv(xtwx)
    store = dense_codes(store_clusters, "store", y.size)
    scores = _cluster_scores(x_matrix, y - mu, store)
    vcov = _sandwich(bread, scores, y.size, beta.size)
    return PpmlFit(
        names=list(names),
        beta=beta,
        mu=mu,
        vcov_store=vcov,
        n=int(y.size),
        k_total=int(beta.size),
        n_store_clusters=int(scores.shape[0]),
        iterations=iterations,
        converged=True,
        includes_fixed_effects=False,
    )
