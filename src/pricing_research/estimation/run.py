"""Fit the baseline cereals associations and write the result files.

The command reads the log sample built in Phase 2. It does not change the
confirmatory equation, and it does not treat a coefficient as causal.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from pricing_research.data.acquire import sha256_file
from pricing_research.estimation.ols import (
    EstimationError,
    LinearFit,
    cooks_distance,
    fit_ols,
    loglog_associated_change,
    price_gap_test,
    remaining_sum_of_squares_share,
    successive_residual_correlation,
)
from pricing_research.estimation.plots import (
    plot_absorbed_variation,
    plot_binned_residuals,
    plot_price_coefficients,
    plot_residual_histogram,
)
from pricing_research.estimation.ppml import fit_ppml
from pricing_research.estimation.registry import (
    COMPARISON_MODELS,
    PRICE_CHANGE_TOLERANCE,
    SELECTION_MODELS,
    WITHIN_PAIR_PRICE_SHARE_FLOOR,
    ModelSpec,
)
from pricing_research.estimation.tables import write_regression_table
from pricing_research.reporting.figures import write_catalog

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
LOG_COLUMNS = [
    "store",
    "upc",
    "week",
    "move",
    "qty",
    "ok",
    "unit_price",
    "log_move",
    "log_unit_price",
    "promo_coded",
    "month",
    "year",
    "in_log_sample",
]
AUDIT_COLUMNS = [
    "store",
    "upc",
    "week",
    "move",
    "qty",
    "ok",
    "price",
    "unit_price",
    "promo_coded",
    "month",
    "year",
    "in_log_sample",
]


def _jsonable(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, np.floating):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _panel_from_frame(frame: pd.DataFrame) -> dict[str, object]:
    store = frame["store"].to_numpy(dtype=np.int64)
    upc = frame["upc"].to_numpy(dtype=np.int64)
    if int(store.max()) >= 10_000:
        raise EstimationError("A store id is too large to pack into the pair key.")
    month = frame["month"].to_numpy(dtype=np.int64)
    year = frame["year"].to_numpy(dtype=np.int64)
    return {
        "log_move": frame["log_move"].to_numpy(dtype=np.float64),
        "log_unit_price": frame["log_unit_price"].to_numpy(dtype=np.float64),
        "move": frame["move"].to_numpy(dtype=np.float64),
        "unit_price": frame["unit_price"].to_numpy(dtype=np.float64),
        "promo_coded": frame["promo_coded"].to_numpy(dtype=bool).astype(np.float64),
        "store": store,
        "upc": upc,
        "week": frame["week"].to_numpy(dtype=np.int64),
        "codes": {
            "upc": upc,
            "store": store,
            "week": frame["week"].to_numpy(dtype=np.int64),
            "pair": upc * 10_000 + store,
            "month": month,
            "year_month": year * 12 + month,
        },
    }


def _subset(panel: dict[str, object], mask: np.ndarray) -> dict[str, object]:
    codes = panel["codes"]
    assert isinstance(codes, dict)
    return {
        key: (
            {name: values[mask] for name, values in codes.items()}
            if key == "codes"
            else values[mask]
        )
        for key, values in panel.items()
    }


def _fe_rank(panel: dict[str, object], absorb: tuple[str, ...]) -> int:
    if not absorb:
        return 0
    codes = panel["codes"]
    assert isinstance(codes, dict)
    counts = [int(np.unique(codes[name]).size) for name in absorb]
    if len(counts) == 1:
        return counts[0]
    if len(counts) == 2:
        return counts[0] + counts[1] - 1
    raise EstimationError("The registry absorbs at most two factors.")


def _formula(spec: ModelSpec) -> str:
    right = " + ".join(spec.regressors)
    if spec.absorb:
        right = f"{right} | {' + '.join(spec.absorb)}"
    return f"{spec.outcome} ~ {right}"


def _fit_linear(panel: dict[str, object], spec: ModelSpec, *, keep_arrays: bool) -> LinearFit:
    codes = panel["codes"]
    assert isinstance(codes, dict)
    regressors = np.column_stack([panel[name] for name in spec.regressors])
    return fit_ols(
        panel[spec.outcome],
        regressors,
        list(spec.regressors),
        panel["store"],
        absorb=[codes[name] for name in spec.absorb],
        week_clusters=panel["week"],
        fe_rank=_fe_rank(panel, spec.absorb),
        add_intercept=not spec.absorb,
        keep_arrays=keep_arrays,
    )


def _coefficient_record(fit: LinearFit, spec: ModelSpec) -> list[dict[str, object]]:
    low, high, critical = fit.interval()
    standard_errors = fit.store_se()
    p_values = fit.two_sided_p()
    rows: list[dict[str, object]] = []
    for index, name in enumerate(fit.names):
        estimate = float(fit.beta[index])
        week_se = None
        if fit.vcov_week is not None:
            week_variance = float(fit.vcov_week[index, index])
            week_se = float(np.sqrt(week_variance)) if week_variance > 0 else None
        twoway_se = None
        if fit.vcov_twoway is not None:
            twoway_variance = float(fit.vcov_twoway[index, index])
            twoway_se = float(np.sqrt(twoway_variance)) if twoway_variance > 0 else None
        associated = None
        if name == "log_unit_price" and (spec.loglog_association or spec.estimator == "ppml"):
            associated = loglog_associated_change(estimate, 1.10)
        rows.append(
            {
                "model_id": spec.model_id,
                "role": spec.role,
                "confirmatory": spec.confirmatory,
                "term": name,
                "estimate": estimate,
                "se_cluster_store": float(standard_errors[index]),
                "ci95_low": float(low[index]),
                "ci95_high": float(high[index]),
                "t_critical_store": critical,
                "t_store": estimate / float(standard_errors[index]),
                "p_two_sided_store": float(p_values[index]),
                "se_cluster_week": week_se,
                "se_cluster_store_and_week": twoway_se,
                "twoway_variance_usable": fit.twoway_positive_semidefinite,
                "n": fit.n,
                "store_clusters": fit.n_store_clusters,
                "week_clusters": fit.n_week_clusters,
                "k_total_for_cluster_adjustment": fit.k_total,
                "r_squared": fit.r_squared,
                "within_r_squared": fit.within_r_squared,
                "outcome": spec.outcome,
                "sample": spec.sample,
                "estimator": spec.estimator,
                "associated_movement_change_for_10_percent_price": associated,
                "loglog_association": bool(
                    spec.loglog_association and name == "log_unit_price"
                ),
                "conditional_mean_elasticity": bool(
                    spec.estimator == "ppml" and name == "log_unit_price"
                ),
                "causal_claim": False,
            }
        )
    return rows


def _ppml_rows(panel: dict[str, object], spec: ModelSpec) -> tuple[list[dict[str, object]], dict]:
    codes = panel["codes"]
    assert isinstance(codes, dict)
    regressors = np.column_stack([panel[name] for name in spec.regressors])
    started = time.perf_counter()
    if len(spec.absorb) > 1:
        raise EstimationError("Two-way PPML is not part of this baseline.")
    fit = fit_ppml(
        panel[spec.outcome],
        regressors,
        list(spec.regressors),
        panel["store"],
        groups=None if not spec.absorb else codes[spec.absorb[0]],
        add_intercept=not spec.absorb,
    )
    elapsed = time.perf_counter() - started
    standard_errors = np.sqrt(np.clip(np.diag(fit.vcov_store), 0, None))
    degrees = fit.n_store_clusters - 1
    critical = float(student_t.ppf(0.975, degrees))
    rows: list[dict[str, object]] = []
    for index, name in enumerate(fit.names):
        estimate = float(fit.beta[index])
        se = float(standard_errors[index])
        statistic = estimate / se
        associated = loglog_associated_change(estimate, 1.10) if name == "log_unit_price" else None
        rows.append(
            {
                "model_id": spec.model_id,
                "role": spec.role,
                "confirmatory": False,
                "term": name,
                "estimate": estimate,
                "se_cluster_store": se,
                "ci95_low": estimate - critical * se,
                "ci95_high": estimate + critical * se,
                "t_critical_store": critical,
                "t_store": statistic,
                "p_two_sided_store": float(2 * student_t.sf(abs(statistic), degrees)),
                "se_cluster_week": None,
                "se_cluster_store_and_week": None,
                "twoway_variance_usable": None,
                "n": fit.n,
                "store_clusters": fit.n_store_clusters,
                "week_clusters": None,
                "k_total_for_cluster_adjustment": fit.k_total,
                "r_squared": None,
                "within_r_squared": None,
                "outcome": spec.outcome,
                "sample": spec.sample,
                "estimator": "ppml",
                "associated_movement_change_for_10_percent_price": associated,
                "loglog_association": False,
                "conditional_mean_elasticity": name == "log_unit_price",
                "causal_claim": False,
            }
        )
    summary = {
        "model_id": spec.model_id,
        "formula": _formula(spec),
        "iterations": fit.iterations,
        "converged": fit.converged,
        "seconds": elapsed,
        "includes_fixed_effects": fit.includes_fixed_effects,
        "n": fit.n,
        "note": (
            "Elasticity of the conditional mean on the rows passed in. "
            "Not an elasticity of log(1 + movement), and not causal."
        ),
    }
    return rows, summary


def _selection_counts(frame: pd.DataFrame) -> dict[str, int]:
    ok = frame["ok"].to_numpy()
    move = frame["move"].to_numpy(dtype=np.float64)
    price = frame["price"].to_numpy(dtype=np.float64)
    qty = frame["qty"].to_numpy(dtype=np.float64)
    unit_price = frame["unit_price"].to_numpy(dtype=np.float64)
    in_log = frame["in_log_sample"].to_numpy(dtype=bool)
    positive_price = np.isfinite(unit_price) & (unit_price > 0) & (qty > 0)
    return {
        "audited_rows": int(len(frame)),
        "in_log_sample_rows": int(in_log.sum()),
        "move_not_positive": int(np.sum(~(move > 0))),
        "move_not_positive_and_price_not_positive": int(np.sum(~(move > 0) & ~(price > 0))),
        "ok1_positive_price_zero_move": int(np.sum((ok == 1) & positive_price & ~(move > 0))),
        "positive_move_nonpositive_price": int(np.sum((move > 0) & ~(price > 0))),
        "ok_not_one_positive_price_and_move": int(
            np.sum((ok != 1) & positive_price & (move > 0))
        ),
    }


def _pair_price_screen(panel: dict[str, object]) -> dict[str, float | int | bool]:
    codes = panel["codes"]
    assert isinstance(codes, dict)
    frame = pd.DataFrame(
        {"pair": codes["pair"], "unit_price": panel["unit_price"]}
    )
    span = frame.groupby("pair", sort=False)["unit_price"].agg(["min", "max", "size"])
    changed = (span["max"] - span["min"]) > PRICE_CHANGE_TOLERANCE
    n_pairs = int(len(span))
    n_changed = int(changed.sum())
    share = n_changed / n_pairs
    return {
        "pairs": n_pairs,
        "pairs_with_unit_price_change": n_changed,
        "share_with_unit_price_change": share,
        "tolerance_dollars": PRICE_CHANGE_TOLERANCE,
        "within_pair_reading_allowed": share >= WITHIN_PAIR_PRICE_SHARE_FLOOR,
        "floor": WITHIN_PAIR_PRICE_SHARE_FLOOR,
    }


def _absorbed(panel: dict[str, object], models: tuple[ModelSpec, ...]) -> list[dict[str, object]]:
    codes = panel["codes"]
    assert isinstance(codes, dict)
    rows = []
    for spec in models:
        if spec.estimator != "within_ols":
            continue
        factors = [codes[name] for name in spec.absorb]
        started = time.perf_counter()
        shares = {
            name: remaining_sum_of_squares_share(panel[name], factors) for name in spec.regressors
        }
        rows.append(
            {
                "model_id": spec.model_id,
                "absorb": list(spec.absorb),
                "seconds": time.perf_counter() - started,
                "log_unit_price_ss_share_remaining": shares.get("log_unit_price"),
                "regressor_ss_share_remaining": shares,
                "fitted_after_this_check": True,
            }
        )
    return rows


def _price_after_promotion(panel: dict[str, object]) -> dict[str, float]:
    """Share of log-price variance left after pair, week, and the promotion indicator."""
    from pricing_research.estimation.ols import residualize

    codes = panel["codes"]
    assert isinstance(codes, dict)
    residual, info = residualize(
        np.column_stack([panel["log_unit_price"], panel["promo_coded"]]),
        [codes["pair"], codes["week"]],
    )
    price = residual[:, 0]
    promo = residual[:, 1]
    promo_ss = float(np.dot(promo, promo))
    if promo_ss <= 0:
        raise EstimationError("The promotion indicator has no within variation.")
    partial = price - promo * (float(np.dot(promo, price)) / promo_ss)
    centered = panel["log_unit_price"] - panel["log_unit_price"].mean()
    total = float(np.dot(centered, centered))
    return {
        "share_remaining_after_pair_week_and_promo": float(np.dot(partial, partial) / total),
        "projection_iterations": float(info["iterations"]),
    }


def _diagnostics(panel: dict[str, object], fit: LinearFit) -> dict[str, object]:
    codes = panel["codes"]
    assert isinstance(codes, dict)
    cook = cooks_distance(fit)
    cutoff = float(np.quantile(cook, 0.999))
    keep = cook <= cutoff
    leverage = np.sum((fit.x_resid @ fit.bread) * fit.x_resid, axis=1)
    mse = float(np.dot(fit.residual, fit.residual) / fit.residual_degrees)
    student = fit.residual / np.sqrt(mse * np.clip(1.0 - leverage, 1e-12, None))
    residual = fit.residual
    centered = residual - residual.mean()
    scale = float(np.sqrt(np.dot(centered, centered) / residual.size))
    skew = float(np.mean((centered / scale) ** 3))
    refit = _fit_linear(_subset(panel, keep), _confirmatory(), keep_arrays=False)
    price_index = fit.names.index("log_unit_price")
    refit_index = refit.names.index("log_unit_price")
    quantiles = [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
    return {
        "successive_within_pair_residual_correlation": successive_residual_correlation(
            fit.residual, codes["pair"], panel["week"]
        ),
        "residual_sd": scale,
        "residual_skewness": skew,
        "residual_quantiles": {
            str(point): float(np.quantile(residual, point)) for point in quantiles
        },
        "cook_p99": float(np.quantile(cook, 0.99)),
        "cook_p999": cutoff,
        "cook_max": float(cook.max()),
        "rows_with_abs_studentized_residual_above_4": int(np.sum(np.abs(student) > 4)),
        "influence_refit": {
            "rule": "drop rows above the 99.9 percentile of Cook's distance; diagnostic only",
            "rows_dropped": int((~keep).sum()),
            "rows_kept": int(keep.sum()),
            "log_unit_price": float(refit.beta[refit_index]),
            "full_sample_log_unit_price": float(fit.beta[price_index]),
            "replaces_confirmatory": False,
        },
    }


def _confirmatory() -> ModelSpec:
    matches = [spec for spec in COMPARISON_MODELS if spec.confirmatory]
    if len(matches) != 1:
        raise EstimationError("The registry must contain one confirmatory model.")
    return matches[0]


def _model_summary(spec: ModelSpec, fit: LinearFit, seconds: float) -> dict[str, object]:
    return {
        "model_id": spec.model_id,
        "role": spec.role,
        "confirmatory": spec.confirmatory,
        "formula": _formula(spec),
        "estimator": spec.estimator,
        "sample": spec.sample,
        "n": fit.n,
        "store_clusters": fit.n_store_clusters,
        "week_clusters": fit.n_week_clusters,
        "fe_rank_assumed": fit.k_total - fit.k_slopes,
        "fe_rank_note": (
            "No fixed effects."
            if not spec.absorb
            else (
                "One-way rank equals the number of groups."
                if len(spec.absorb) == 1
                else (
                    "Two-way rank is n1 + n2 - 1 and assumes those two factors "
                    "form a connected graph."
                )
            )
        ),
        "seconds": seconds,
        "projection": fit.projection,
        "r_squared": fit.r_squared,
        "within_r_squared": fit.within_r_squared,
        "twoway_variance_usable": fit.twoway_positive_semidefinite,
        "causal_claim": False,
        "chosen_by_r_squared": False,
    }


def fit_baseline(root: Path) -> dict[str, object]:
    """Estimate every registry model and return the JSON document."""
    quality_path = root / "reports" / "results" / "data_quality.json"
    quality = json.loads(quality_path.read_text())
    if not quality["full_sample"]:
        raise EstimationError("The quality report is not the full cereals sample.")
    log_path = root / "data" / "processed" / "cereals_log_sample.parquet"
    audit_path = root / "data" / "interim" / "cereals_movement_audited.parquet"
    log_hash = sha256_file(log_path)
    expected_hash = next(
        item["sha256"]
        for item in quality["outputs"]
        if item["path"].endswith("cereals_log_sample.parquet")
    )
    if log_hash != expected_hash:
        raise EstimationError("The log-sample file hash does not match data_quality.json.")
    expected_rows = int(quality["row_reconciliation"]["log_sample_rows"])
    frame = pd.read_parquet(log_path, columns=LOG_COLUMNS)
    if len(frame) != expected_rows:
        raise EstimationError(
            f"The log sample has {len(frame)} rows; data_quality.json says {expected_rows}."
        )
    if frame[LOG_COLUMNS].isna().any().any():
        raise EstimationError("The log sample has a null in a regression column.")
    if not bool((frame["in_log_sample"] == True).all()):  # noqa: E712
        raise EstimationError("The log-sample file contains a row outside the log sample.")
    if not bool((frame["ok"] == 1).all() and (frame["move"] > 0).all()):
        raise EstimationError("The log sample failed the movement or OK check.")
    if not bool((frame["unit_price"] > 0).all() and (frame["qty"] > 0).all()):
        raise EstimationError("The log sample failed the price or bundle-size check.")

    panel = _panel_from_frame(frame)
    logger.info("Measuring absorbed price variation before the slopes.")
    absorbed = _absorbed(panel, COMPARISON_MODELS)
    partial_price = _price_after_promotion(panel)
    screen = _pair_price_screen(panel)

    fits: dict[str, LinearFit] = {}
    summaries = []
    table_rows: list[dict[str, object]] = []
    for spec in COMPARISON_MODELS:
        logger.info("Fitting %s.", spec.model_id)
        started = time.perf_counter()
        fit = _fit_linear(panel, spec, keep_arrays=spec.confirmatory)
        elapsed = time.perf_counter() - started
        fits[spec.model_id] = fit
        summaries.append(_model_summary(spec, fit, elapsed))
        table_rows.extend(_coefficient_record(fit, spec))

    confirmatory = fits["M5_confirmatory"]
    diagnostics = _diagnostics(panel, confirmatory)
    gap = price_gap_test(fits["M0_pooled_ols"], confirmatory, "log_unit_price")
    price_row = next(
        row
        for row in table_rows
        if row["model_id"] == "M5_confirmatory" and row["term"] == "log_unit_price"
    )
    hypotheses = {
        "h1_negative_confirmatory_slope": {
            "statement": "confirmatory cereals beta on log unit price is negative",
            "estimate": price_row["estimate"],
            "sign_is_negative": price_row["estimate"] < 0,
            "one_sided_p_against_zero": float(
            student_t.cdf(float(price_row["t_store"]), confirmatory.n_store_clusters - 1)
        ),
            "causal_claim": False,
        },
        "h2_pooled_differs_from_confirmatory": {
            "statement": "pooled OLS beta differs from confirmatory beta on the same rows",
            "sidedness": "two-sided",
            "test": gap,
            "not_a_hausman_exogeneity_test": True,
        },
        "h3_oatmeal_same_sign": {
            "status": "not_estimated",
            "reason": "Oatmeal is the robustness category and is outside this cereals baseline.",
        },
    }

    audit = pd.read_parquet(audit_path, columns=AUDIT_COLUMNS)
    selection = _selection_counts(audit)
    if selection["in_log_sample_rows"] != expected_rows:
        raise EstimationError("The audited log-sample flag does not match the log-sample file.")
    level_spec = next(spec for spec in SELECTION_MODELS if spec.model_id == "L_level_pair_week")
    logger.info("Fitting the level specification.")
    started = time.perf_counter()
    level_fit = _fit_linear(panel, level_spec, keep_arrays=False)
    level_rows = _coefficient_record(level_fit, level_spec)
    level_summary = _model_summary(level_spec, level_fit, time.perf_counter() - started)
    median_price = float(np.median(panel["unit_price"]))
    median_move = float(np.median(panel["move"]))
    level_beta = float(level_fit.beta[level_fit.names.index("unit_price")])
    level_summary["translation_at_median"] = {
        "median_unit_price_dollars": median_price,
        "median_move_items": median_move,
        "implied_elasticity": level_beta * median_price / median_move,
        "meaning": (
            "Linear items-per-dollar coefficient times median price over median movement. "
            "This is not the log-log estimand and not a causal elasticity."
        ),
    }
    table_rows.extend(level_rows)

    ppml_summaries = []
    for spec in SELECTION_MODELS:
        if spec.estimator != "ppml":
            continue
        logger.info("Fitting %s.", spec.model_id)
        try:
            rows, summary = _ppml_rows(panel, spec)
        except EstimationError as exc:
            ppml_summaries.append(
                {"model_id": spec.model_id, "status": "not_estimated", "reason": str(exc)}
            )
            continue
        table_rows.extend(rows)
        ppml_summaries.append(summary)

    ok0_mask = (
        (audit["ok"] != 1)
        & (audit["move"] > 0)
        & (audit["qty"] > 0)
        & audit["unit_price"].gt(0)
    )
    ok0 = audit.loc[ok0_mask].copy()
    ok0["log_move"] = np.log(ok0["move"].to_numpy(dtype=np.float64))
    ok0["log_unit_price"] = np.log(ok0["unit_price"].to_numpy(dtype=np.float64))
    ok0["in_log_sample"] = False
    restore_summary: dict[str, object]
    if len(ok0) == 0:
        restore_summary = {
            "model_id": "S_restore_ok0",
            "status": "not_estimated",
            "reason": "No OK=0 row has positive price, quantity, and movement.",
        }
    else:
        restored = pd.concat(
            [frame, ok0[LOG_COLUMNS]],
            ignore_index=True,
        )
        restore_panel = _panel_from_frame(restored)
        restore_spec = next(spec for spec in SELECTION_MODELS if spec.model_id == "S_restore_ok0")
        logger.info("Fitting the OK=0 sign check on %s extra rows.", len(ok0))
        try:
            started = time.perf_counter()
            restore_fit = _fit_linear(restore_panel, restore_spec, keep_arrays=False)
            restore_rows = _coefficient_record(restore_fit, restore_spec)
            table_rows.extend(restore_rows)
            restore_beta = float(
                restore_fit.beta[restore_fit.names.index("log_unit_price")]
            )
            restore_summary = _model_summary(
                restore_spec, restore_fit, time.perf_counter() - started
            )
            restore_summary["extra_rows"] = int(len(ok0))
            restore_summary["sign_matches_confirmatory"] = (restore_beta < 0) == (
                price_row["estimate"] < 0
            )
            restore_summary["replaces_confirmatory"] = False
        except EstimationError as exc:
            restore_summary = {
                "model_id": "S_restore_ok0",
                "status": "not_estimated",
                "reason": str(exc),
            }

    document: dict[str, object] = {
        "generated_by": "python -m pricing_research.estimation.run",
        "category": "cereals",
        "causal_claim": False,
        "dataset": {
            "log_sample": str(log_path.relative_to(root)),
            "sha256": log_hash,
            "rows": expected_rows,
            "stores": int(frame["store"].nunique()),
            "upcs": int(frame["upc"].nunique()),
            "weeks": int(frame["week"].nunique()),
            "audited_rows": selection["audited_rows"],
        },
        "estimand": {
            "outcome": "natural log of MOVE, item movement",
            "price": "natural log of PRICE / QTY, dollars per item",
            "beta": (
                "conditional log-log association. A 10 percent price difference maps "
                "through exp(beta * log(1.10)) - 1. Not a causal elasticity."
            ),
            "promotion": "1{SALE in {B, C, S}}. Blank, G, and L stay in the reference group.",
            "cluster_primary": "store",
            "cluster_sensitivity": ["week", "store and week"],
            "interval": "Student t with store clusters minus 1 degree of freedom",
            "not_included": ["upc by week", "store by week", "log(1 + MOVE)", "instruments"],
        },
        "pair_price_screen": screen,
        "absorbed_variation_before_slopes": absorbed,
        "price_variation_after_promotion_control": partial_price,
        "models": summaries,
        "selection": {
            "counts": selection,
            "zero_sales_and_log_price": (
                "A zero-movement row can enter a log-price regression only when its "
                "unit price is positive. ok1_positive_price_zero_move is that count."
            ),
            "log_one_plus_move": (
                "not estimated; those coefficients would not be exact elasticities"
            ),
            "level": level_summary,
            "ppml": ppml_summaries,
            "restore_ok0": restore_summary,
        },
        "hypotheses": hypotheses,
        "diagnostics": diagnostics,
        "inference_limits": {
            "store_clusters": int(confirmatory.n_store_clusters),
            "week_clusters": int(confirmatory.n_week_clusters),
            "store_cluster_covers": "arbitrary dependence among products and weeks inside a store",
            "store_cluster_misses": (
                "correlation across stores, including a UPC-specific shock that hits many stores "
                "in the same week"
            ),
            "week_cluster_covers": "arbitrary dependence across products and stores inside a week",
            "week_cluster_misses": "dependence across weeks inside a store",
            "two_way": (
                "Cameron-Gelbach-Miller store plus week minus the intersection. "
                "The matrix is discarded when it is not positive semidefinite. "
                "It is a sensitivity, not a proof of exogeneity."
            ),
        },
    }
    figure_dir = root / "reports" / "figures"
    catalog: list[dict[str, object]] = []
    plot_price_coefficients(
        [row for row in table_rows if row["sample"] == "log"],
        figure_dir / "baseline_01_coefficients.png",
        catalog,
        n_rows=expected_rows,
    )
    plot_absorbed_variation(
        absorbed,
        figure_dir / "baseline_02_absorbed_price_variation.png",
        catalog,
        n_rows=expected_rows,
    )
    plot_residual_histogram(
        confirmatory.residual,
        figure_dir / "baseline_03_confirmatory_residuals.png",
        catalog,
    )
    plot_binned_residuals(
        confirmatory.x_resid[:, confirmatory.names.index("log_unit_price")],
        confirmatory.residual,
        figure_dir / "baseline_04_binned_residuals.png",
        catalog,
    )
    write_catalog(figure_dir / "baseline_figure_metadata.json", catalog)
    results_path = root / "reports" / "results" / "baseline_models.json"
    results_path.write_text(json.dumps(_jsonable(document), indent=2) + "\n")
    write_regression_table(table_rows, root / "reports" / "tables" / "baseline_regression.csv")
    logger.info("Wrote %s.", results_path)
    return document


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Fit the cereals baseline associations.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    fit_baseline(args.root)


if __name__ == "__main__":
    main()
