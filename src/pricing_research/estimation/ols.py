"""Within-transformed OLS and cluster-robust variance.

The algebra is ordinary least squares after residualizing on grouping factors.
A slope on log unit price in a log movement equation is a log-log association.
Nothing in this module establishes that the association is causal.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import t as student_t

PROJECTION_TOLERANCE = 1e-8
PROJECTION_MAX_ITER = 200
MIN_COLUMN_SS = 1e-10
MAX_CONDITION = 1e12


class EstimationError(ValueError):
    """The regression inputs do not identify a coefficient."""


def finite_vector(values: np.ndarray, name: str) -> np.ndarray:
    """Return a one-dimensional finite float array."""
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size < 2:
        raise EstimationError(f"{name} must be a vector with at least two rows.")
    if not np.isfinite(array).all():
        raise EstimationError(f"{name} contains a non-finite value.")
    return array


def dense_codes(codes: np.ndarray, name: str, n_rows: int) -> np.ndarray:
    """Map group labels onto 0 .. G-1. Labels may be any integer."""
    array = np.asarray(codes)
    if array.shape != (n_rows,):
        raise EstimationError(f"{name} must have one code per row.")
    if array.dtype.kind not in "iu":
        raise EstimationError(f"{name} codes must be integers.")
    _labels, inverse = np.unique(array, return_inverse=True)
    return inverse.astype(np.int64, copy=False)


def group_counts(codes: np.ndarray) -> int:
    """Number of distinct groups in a dense code array."""
    if codes.size == 0:
        return 0
    return int(codes.max()) + 1


def _demean_columns(matrix: np.ndarray, codes: np.ndarray) -> np.ndarray:
    counts = np.bincount(codes).astype(np.float64)
    if np.any(counts == 0):
        raise EstimationError("A group code has no rows.")
    sums = np.empty((counts.size, matrix.shape[1]), dtype=np.float64)
    for column in range(matrix.shape[1]):
        sums[:, column] = np.bincount(codes, weights=matrix[:, column])
    return matrix - (sums / counts[:, None])[codes]


def residualize(
    matrix: np.ndarray,
    absorb: list[np.ndarray],
    *,
    tolerance: float = PROJECTION_TOLERANCE,
    max_iter: int = PROJECTION_MAX_ITER,
) -> tuple[np.ndarray, dict[str, float | int | bool]]:
    """Residualize columns on one or more sets of group dummies.

    One grouping is an exact within transformation. Two or more groupings use
    alternating projections. The loop stops when the largest absolute change
    is below ``tolerance``.
    """
    out = np.array(matrix, dtype=np.float64, copy=True)
    if out.ndim != 2 or out.shape[0] < 2:
        raise EstimationError("Residualizing requires a matrix with at least two rows.")
    if not np.isfinite(out).all():
        raise EstimationError("A residualized column contains a non-finite value.")
    if not absorb:
        return out, {"iterations": 0, "converged": True, "max_abs_change": 0.0}
    dense: list[np.ndarray] = []
    for index, codes in enumerate(absorb):
        if codes.shape != (out.shape[0],):
            raise EstimationError("Grouping codes do not match the matrix rows.")
        dense.append(dense_codes(codes, f"group_{index}", out.shape[0]))
    absorb = dense
    if len(absorb) == 1:
        return _demean_columns(out, absorb[0]), {
            "iterations": 1,
            "converged": True,
            "max_abs_change": 0.0,
        }
    change = np.inf
    for iteration in range(1, max_iter + 1):
        before = out.copy()
        for codes in absorb:
            out = _demean_columns(out, codes)
        change = float(np.max(np.abs(out - before)))
        if change < tolerance:
            return out, {
                "iterations": iteration,
                "converged": True,
                "max_abs_change": change,
            }
    raise EstimationError(
        f"Fixed-effect projection did not converge after {max_iter} iterations "
        f"(largest change {change:.3e})."
    )


def remaining_sum_of_squares_share(values: np.ndarray, absorb: list[np.ndarray]) -> float:
    """Share of variance left after the grouping projection.

    The share is the identifying variation for a coefficient on this column.
    It is zero when the column is constant inside every group combination.
    """
    vector = finite_vector(values, "values")
    centered = vector - vector.mean()
    total = float(np.dot(centered, centered))
    if total <= 0:
        raise EstimationError("A regressor with zero variance cannot identify a coefficient.")
    if not absorb:
        return 1.0
    residual, _info = residualize(vector[:, None], absorb)
    return float(np.dot(residual[:, 0], residual[:, 0]) / total)


def _cluster_scores(x_matrix: np.ndarray, residual: np.ndarray, clusters: np.ndarray) -> np.ndarray:
    weighted = x_matrix * residual[:, None]
    scores = np.column_stack(
        [
            np.bincount(clusters, weights=weighted[:, column])
            for column in range(x_matrix.shape[1])
        ]
    )
    occupied = np.bincount(clusters) > 0
    return scores[occupied]


def _sandwich(
    bread: np.ndarray,
    scores: np.ndarray,
    n_rows: int,
    k_total: int,
) -> np.ndarray:
    n_clusters = scores.shape[0]
    if n_clusters < 2:
        raise EstimationError("Cluster-robust variance needs at least two clusters.")
    if n_rows - k_total <= 0:
        raise EstimationError("Degrees of freedom are not positive after the fixed effects.")
    scale = (n_clusters / (n_clusters - 1.0)) * ((n_rows - 1.0) / (n_rows - k_total))
    meat = scores.T @ scores
    return scale * (bread @ meat @ bread)


def _psd(matrix: np.ndarray) -> bool:
    eigenvalues = np.linalg.eigvalsh(matrix)
    scale = max(1.0, float(np.max(np.abs(eigenvalues))))
    return bool(eigenvalues.min() >= -1e-8 * scale)


@dataclass
class LinearFit:
    """One fitted linear specification. Slopes are associations."""

    names: list[str]
    beta: np.ndarray
    residual: np.ndarray
    x_resid: np.ndarray
    bread: np.ndarray
    store_scores: np.ndarray
    vcov_store: np.ndarray
    vcov_week: np.ndarray | None
    vcov_twoway: np.ndarray | None
    twoway_positive_semidefinite: bool | None
    n: int
    k_slopes: int
    k_total: int
    n_store_clusters: int
    n_week_clusters: int
    r_squared: float
    within_r_squared: float
    residual_degrees: int
    projection: dict[str, float | int | bool]

    def store_se(self) -> np.ndarray:
        return np.sqrt(np.clip(np.diag(self.vcov_store), 0, None))

    def interval(self, level: float = 0.95) -> tuple[np.ndarray, np.ndarray, float]:
        """Store-cluster confidence interval using a t reference with G-1 degrees."""
        if not 0 < level < 1:
            raise EstimationError("The confidence level must lie between 0 and 1.")
        degrees = self.n_store_clusters - 1
        critical = float(student_t.ppf(0.5 + level / 2, degrees))
        se = self.store_se()
        return self.beta - critical * se, self.beta + critical * se, critical

    def two_sided_p(self) -> np.ndarray:
        degrees = self.n_store_clusters - 1
        se = self.store_se()
        if np.any(se <= 0):
            raise EstimationError("A store-cluster standard error is not positive.")
        statistic = self.beta / se
        return 2 * student_t.sf(np.abs(statistic), degrees)


def fit_ols(
    outcome: np.ndarray,
    regressors: np.ndarray,
    names: list[str],
    store_clusters: np.ndarray,
    *,
    absorb: list[np.ndarray] | None = None,
    week_clusters: np.ndarray | None = None,
    fe_rank: int = 0,
    add_intercept: bool = False,
    keep_arrays: bool = False,
) -> LinearFit:
    """Fit OLS, optionally after residualizing on grouping factors.

    ``fe_rank`` is the rank of the absorbed dummies. It enters only the
    finite-sample factor in the cluster variance. The point estimate does not
    depend on it.
    """
    y_raw = finite_vector(outcome, "outcome")
    x_raw = np.asarray(regressors, dtype=np.float64)
    if x_raw.ndim == 1:
        x_raw = x_raw[:, None]
    if x_raw.shape != (y_raw.size, len(names)):
        raise EstimationError("Regressor columns do not match the outcome or the names.")
    if not np.isfinite(x_raw).all():
        raise EstimationError("A regressor contains a non-finite value.")
    factors = list(absorb or [])
    store = dense_codes(store_clusters, "store", y_raw.size)
    week = None if week_clusters is None else dense_codes(week_clusters, "week", y_raw.size)

    if add_intercept and factors:
        raise EstimationError("An intercept is redundant once fixed effects are absorbed.")
    if add_intercept:
        x_raw = np.column_stack([np.ones(y_raw.size), x_raw])
        names = ["intercept", *names]
    if not factors and not add_intercept:
        raise EstimationError("A pooled regression needs an intercept or an explicit demeaning.")

    stacked = np.column_stack([y_raw, x_raw])
    residualized, projection = residualize(stacked, factors)
    y = residualized[:, 0]
    x_matrix = residualized[:, 1:]
    for index, name in enumerate(names):
        column_ss = float(np.dot(x_matrix[:, index], x_matrix[:, index]))
        if column_ss < MIN_COLUMN_SS:
            raise EstimationError(
                f"{name} has no usable variation after the fixed effects "
                f"(sum of squares {column_ss:.3e})."
            )
    xtx = x_matrix.T @ x_matrix
    condition = float(np.linalg.cond(xtx))
    if not np.isfinite(condition) or condition > MAX_CONDITION:
        raise EstimationError(
            f"The residualized regressors are collinear (condition number {condition:.3e})."
        )
    beta = np.linalg.solve(xtx, x_matrix.T @ y)
    residual = y - x_matrix @ beta
    bread = np.linalg.inv(xtx)
    k_slopes = int(beta.size)
    k_total = k_slopes + int(fe_rank)
    if add_intercept:
        # The intercept is already inside k_slopes. fe_rank stays 0.
        k_total = k_slopes
    store_scores = _cluster_scores(x_matrix, residual, store)
    vcov_store = _sandwich(bread, store_scores, y_raw.size, k_total)
    vcov_week = None
    vcov_twoway = None
    twoway_ok = None
    n_week = 0
    if week is not None:
        week_scores = _cluster_scores(x_matrix, residual, week)
        n_week = int(week_scores.shape[0])
        vcov_week = _sandwich(bread, week_scores, y_raw.size, k_total)
        intersection = store * (int(week.max()) + 1) + week
        both_scores = _cluster_scores(x_matrix, residual, intersection)
        vcov_both = _sandwich(bread, both_scores, y_raw.size, k_total)
        combined = vcov_store + vcov_week - vcov_both
        twoway_ok = _psd(combined)
        vcov_twoway = combined if twoway_ok else None

    y_centered = y_raw - y_raw.mean()
    total_ss = float(np.dot(y_centered, y_centered))
    resid_ss = float(np.dot(residual, residual))
    within_ss = total_ss if not factors else float(np.dot(y, y))
    if total_ss <= 0 or within_ss <= 0:
        raise EstimationError("The outcome has no variation in this sample.")
    degrees = y_raw.size - k_total
    if not keep_arrays:
        residual = np.empty(0, dtype=np.float64)
        x_matrix = np.empty((0, k_slopes), dtype=np.float64)
    return LinearFit(
        names=list(names),
        beta=beta,
        residual=residual,
        x_resid=x_matrix,
        bread=bread,
        store_scores=store_scores,
        vcov_store=vcov_store,
        vcov_week=vcov_week,
        vcov_twoway=vcov_twoway,
        twoway_positive_semidefinite=twoway_ok,
        n=int(y_raw.size),
        k_slopes=k_slopes,
        k_total=k_total,
        n_store_clusters=int(store_scores.shape[0]),
        n_week_clusters=n_week,
        r_squared=1.0 - resid_ss / total_ss,
        within_r_squared=1.0 - resid_ss / within_ss,
        residual_degrees=int(degrees),
        projection=projection,
    )


def price_gap_test(
    left: LinearFit,
    right: LinearFit,
    term: str,
) -> dict[str, float | bool]:
    """Two-sided test that two store-clustered slopes on ``term`` are equal.

    The covariance uses a common finite-sample factor so the variance of the
    difference is a coherent sandwich. This is not a Hausman exogeneity test.
    """
    if left.n != right.n or left.n_store_clusters != right.n_store_clusters:
        raise EstimationError("The gap test requires the same rows and the same store clusters.")
    if left.store_scores.shape[0] != right.store_scores.shape[0]:
        raise EstimationError("Store score rows are not aligned.")
    left_index = left.names.index(term)
    right_index = right.names.index(term)
    g_clusters = left.n_store_clusters
    k_for_scale = max(left.k_total, right.k_total)
    scale = (g_clusters / (g_clusters - 1.0)) * ((left.n - 1.0) / (left.n - k_for_scale))
    cross = left.store_scores.T @ right.store_scores
    covariance = scale * float(
        left.bread[left_index] @ cross @ right.bread[right_index]
    )
    var_left = scale * float(
        left.bread[left_index] @ (left.store_scores.T @ left.store_scores) @ left.bread[left_index]
    )
    var_right = scale * float(
        right.bread[right_index]
        @ (right.store_scores.T @ right.store_scores)
        @ right.bread[right_index]
    )
    variance = var_left + var_right - 2 * covariance
    gap = float(left.beta[left_index] - right.beta[right_index])
    if variance <= 0:
        raise EstimationError("The variance of the coefficient gap is not positive.")
    standard_error = float(np.sqrt(variance))
    degrees = g_clusters - 1
    statistic = gap / standard_error
    p_value = float(2 * student_t.sf(abs(statistic), degrees))
    return {
        "gap": gap,
        "standard_error": standard_error,
        "t": float(statistic),
        "p_two_sided": p_value,
        "degrees_of_freedom": float(degrees),
        "hausman_exogeneity_test": False,
    }


def loglog_associated_change(beta: float, price_ratio: float) -> float:
    """Proportional movement difference associated with a price ratio.

    For a log-log coefficient, a price multiplied by ``price_ratio`` is
    associated with a movement factor of ``exp(beta * log(price_ratio))``.
    The return value is that factor minus one. It is not a causal effect.
    """
    if price_ratio <= 0:
        raise EstimationError("A price ratio must be positive.")
    return float(np.exp(beta * np.log(price_ratio)) - 1.0)


def cooks_distance(fit: LinearFit) -> np.ndarray:
    """Cook's distance on the residualized regressors.

    The measure ranks rows inside this specification. It is not a reason to
    drop a row from the confirmatory sample.
    """
    fitted = fit.x_resid @ fit.bread
    leverage = np.clip(np.sum(fitted * fit.x_resid, axis=1), 0.0, 1.0 - 1e-8)
    mse = float(np.dot(fit.residual, fit.residual) / fit.residual_degrees)
    if mse <= 0:
        raise EstimationError("Cook's distance is undefined when the residual variance is zero.")
    return (fit.residual**2 / (fit.k_slopes * mse)) * (leverage / (1.0 - leverage) ** 2)


def successive_residual_correlation(
    residual: np.ndarray,
    pair: np.ndarray,
    week: np.ndarray,
) -> float:
    """Correlation of residuals in successive observed weeks inside a pair.

    The lag is the previous observed row for that pair, not a filled calendar lag.
    """
    if residual.shape != pair.shape or residual.shape != week.shape:
        raise EstimationError("Residual, pair, and week arrays must be aligned.")
    order = np.lexsort((week, pair))
    ordered_residual = residual[order]
    ordered_pair = pair[order]
    same_pair = ordered_pair[1:] == ordered_pair[:-1]
    if int(same_pair.sum()) < 2:
        raise EstimationError("Not enough successive pairs to measure residual correlation.")
    current = ordered_residual[1:][same_pair]
    lagged = ordered_residual[:-1][same_pair]
    current = current - current.mean()
    lagged = lagged - lagged.mean()
    denom = float(np.sqrt(np.dot(current, current) * np.dot(lagged, lagged)))
    if denom == 0:
        raise EstimationError("Successive residuals have zero variance.")
    return float(np.dot(current, lagged) / denom)
