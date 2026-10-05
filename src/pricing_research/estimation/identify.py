"""Identification audit for the cereals log sample.

This command does not estimate two-stage least squares on Kilts rows. Instrument
verdicts are read from ``instruments.py`` and are not updated from correlations.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from pricing_research.data.calendar import week_bounds
from pricing_research.estimation.instruments import CANDIDATES
from pricing_research.estimation.iv_demo import (
    assumed_movement_change,
    assumed_revenue_change,
    synthetic_iv_examples,
)
from pricing_research.estimation.ols import EstimationError, residualize
from pricing_research.estimation.registry import (
    PRICE_CHANGE_TOLERANCE,
    WITHIN_PAIR_PRICE_SHARE_FLOOR,
    ModelSpec,
)
from pricing_research.estimation.run import (
    ROOT,
    _coefficient_record,
    _fit_linear,
    _jsonable,
    _panel_from_frame,
)
from pricing_research.estimation.tables import write_regression_table
from pricing_research.reporting.descriptives import pearson_correlation
from pricing_research.reporting.figures import new_figure, save_figure, write_catalog

logger = logging.getLogger(__name__)

WEEK_SPLIT = 200
AUDIT_COLUMNS = [
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
    "profit",
    "sale_class",
    "descrip",
    "price_tier",
    "month",
    "year",
    "in_log_sample",
]


def _pair_screen(unit_price: np.ndarray, pair: np.ndarray) -> dict[str, float | int | bool]:
    span = (
        pd.DataFrame({"pair": pair, "price": unit_price})
        .groupby("pair", sort=False)["price"]
        .agg(["min", "max", "size"])
    )
    changed = (span["max"] - span["min"]) > PRICE_CHANGE_TOLERANCE
    n_pairs = int(len(span))
    n_changed = int(changed.sum())
    share = n_changed / n_pairs if n_pairs else float("nan")
    multi = span["size"] >= 2
    multi_range = np.log(span.loc[multi, "max"].to_numpy()) - np.log(
        span.loc[multi, "min"].to_numpy()
    )
    wide = int(np.sum(multi_range >= np.log(1.10))) if multi_range.size else 0
    return {
        "pairs": n_pairs,
        "pairs_with_unit_price_change": n_changed,
        "share_with_unit_price_change": share,
        "within_pair_reading_allowed": bool(share >= WITHIN_PAIR_PRICE_SHARE_FLOOR),
        "multiweek_pairs": int(multi.sum()),
        "multiweek_pairs_with_log_range_at_least_log_1_10": wide,
    }


def _finite_correlation(left: np.ndarray, right: np.ndarray) -> tuple[float | None, int]:
    mask = np.isfinite(left) & np.isfinite(right)
    used = int(mask.sum())
    if used < 3:
        return None, used
    return pearson_correlation(left[mask], right[mask]), used


def _within_correlation(
    left: np.ndarray,
    right: np.ndarray,
    groups: np.ndarray,
) -> tuple[float | None, int]:
    mask = np.isfinite(left) & np.isfinite(right)
    used = int(mask.sum())
    if used < 3:
        return None, used
    try:
        left_resid, _info = residualize(left[mask][:, None], [groups[mask]])
        right_resid, _info = residualize(right[mask][:, None], [groups[mask]])
        return pearson_correlation(left_resid[:, 0], right_resid[:, 0]), used
    except (EstimationError, ValueError):
        return None, used


def _ss_share(values: np.ndarray, pair: np.ndarray, week: np.ndarray) -> float | None:
    mask = np.isfinite(values)
    if int(mask.sum()) < 3:
        return None
    try:
        from pricing_research.estimation.ols import remaining_sum_of_squares_share

        return remaining_sum_of_squares_share(values[mask], [pair[mask], week[mask]])
    except (EstimationError, ValueError):
        return None


def _adjacent(values: np.ndarray, pair: np.ndarray, week: np.ndarray, lead: bool) -> np.ndarray:
    """Copy the adjacent calendar week's value. Gaps are left missing."""
    out = np.full(values.shape, np.nan)
    order = np.lexsort((week, pair))
    ordered_pair = pair[order]
    ordered_week = week[order]
    ordered_values = values[order]
    adjacent = (ordered_pair[1:] == ordered_pair[:-1]) & (
        ordered_week[1:] == ordered_week[:-1] + 1
    )
    if lead:
        out[order[:-1][adjacent]] = ordered_values[1:][adjacent]
    else:
        out[order[1:][adjacent]] = ordered_values[:-1][adjacent]
    return out


def _instrument_measurements(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    log_price = frame["log_unit_price"].to_numpy(dtype=np.float64)
    unit_price = frame["unit_price"].to_numpy(dtype=np.float64)
    profit = frame["profit"].to_numpy(dtype=np.float64)
    pair = frame["upc"].to_numpy(dtype=np.int64) * 10_000 + frame["store"].to_numpy(dtype=np.int64)
    week = frame["week"].to_numpy(dtype=np.int64)
    promo = frame["promo_coded"].to_numpy(dtype=bool).astype(np.float64)

    cost_share = 1.0 - profit / 100.0
    log_aac = np.full(log_price.shape, np.nan)
    positive_cost = np.isfinite(cost_share) & (cost_share > 0) & np.isfinite(unit_price)
    log_aac[positive_cost] = np.log(unit_price[positive_cost] * cost_share[positive_cost])
    aac_corr, aac_n = _finite_correlation(log_aac, log_price)
    aac_within, _aac_within_n = _within_correlation(log_aac, log_price, pair)

    lagged = _adjacent(log_price, pair, week, lead=False)
    lag_corr, lag_n = _finite_correlation(lagged, log_price)
    lag_within, _lag_within_n = _within_correlation(lagged, log_price, pair)

    grouped = frame.groupby(["upc", "week"], sort=False)["log_unit_price"]
    totals = grouped.transform("sum").to_numpy(dtype=np.float64)
    counts = grouped.transform("size").to_numpy(dtype=np.float64)
    other_store = np.full(log_price.shape, np.nan)
    multi = counts >= 2
    other_store[multi] = (totals[multi] - log_price[multi]) / (counts[multi] - 1.0)
    other_corr, other_n = _finite_correlation(other_store, log_price)
    other_within, _other_within_n = _within_correlation(other_store, log_price, pair)

    promo_corr, promo_n = _finite_correlation(promo, log_price)
    promo_within, _promo_within_n = _within_correlation(promo, log_price, pair)

    tier = frame["price_tier"].astype("string")
    tier_missing = float(tier.isna().mean())
    tier_nunique = frame.assign(_tier=tier.fillna("")).groupby("store")["_tier"].nunique()
    tier_constant = bool(tier_nunique.max() == 1)
    high_or_cub = tier.isin(["High", "CubFighter"]).to_numpy()
    high = tier.eq("High").to_numpy(dtype=float)
    tier_corr, tier_n = _finite_correlation(high[high_or_cub], log_price[high_or_cub])

    week_index = week.astype(np.float64)
    from pricing_research.estimation.ols import remaining_sum_of_squares_share

    week_share = remaining_sum_of_squares_share(week_index, [week])

    return {
        "log_average_acquisition_cost": {
            "rows_used_for_correlation": aac_n,
            "correlation_with_log_unit_price": aac_corr,
            "within_pair_correlation_with_log_unit_price": aac_within,
            "ss_share_remaining_after_pair_and_week": _ss_share(log_aac, pair, week),
            "missing_share": float(1.0 - positive_cost.mean()),
            "cross_section_note": "Same row as the shelf price.",
            "time_note": "Moves when the margin or the shelf price moves.",
        },
        "lagged_log_unit_price": {
            "rows_used_for_correlation": lag_n,
            "correlation_with_log_unit_price": lag_corr,
            "within_pair_correlation_with_log_unit_price": lag_within,
            "ss_share_remaining_after_pair_and_week": _ss_share(lagged, pair, week),
            "missing_share": float(1.0 - np.isfinite(lagged).mean()),
            "cross_section_note": "Within the UPC-store pair.",
            "time_note": "Previous calendar week only. A gap is not filled.",
        },
        "other_store_leave_one_out_log_unit_price": {
            "rows_used_for_correlation": other_n,
            "correlation_with_log_unit_price": other_corr,
            "within_pair_correlation_with_log_unit_price": other_within,
            "ss_share_remaining_after_pair_and_week": _ss_share(other_store, pair, week),
            "missing_share": float(1.0 - np.isfinite(other_store).mean()),
            "cross_section_note": "Other stores in the same UPC-week. At least two stores.",
            "time_note": (
                "Contemporaneous. Week effects do not remove a UPC-specific chainwide price."
            ),
        },
        "price_tier": {
            "rows_used_for_correlation": tier_n,
            "correlation_with_log_unit_price": tier_corr,
            "within_pair_correlation_with_log_unit_price": None,
            "ss_share_remaining_after_pair_and_week": 0.0 if tier_constant else None,
            "missing_share": tier_missing,
            "cross_section_note": (
                "Point-biserial correlation of a High-tier indicator with log price, "
                "on High and CubFighter rows only."
            ),
            "time_note": (
                "Tier is constant within every store."
                if tier_constant
                else "Tier is not constant within every store."
            ),
        },
        "promo_coded": {
            "rows_used_for_correlation": promo_n,
            "correlation_with_log_unit_price": promo_corr,
            "within_pair_correlation_with_log_unit_price": promo_within,
            "ss_share_remaining_after_pair_and_week": _ss_share(promo, pair, week),
            "missing_share": 0.0,
            "cross_section_note": "Coded B, C, or S versus blank and unclassified.",
            "time_note": (
                "Turns on and off inside pairs. The confirmatory equation uses it as a control."
            ),
        },
        "national_cost_index": {
            "rows_used_for_correlation": None,
            "correlation_with_log_unit_price": None,
            "within_pair_correlation_with_log_unit_price": None,
            "ss_share_remaining_after_pair_and_week": week_share,
            "missing_share": None,
            "cross_section_note": "No cost index was joined.",
            "time_note": (
                "Demonstration only: the week index is constant across rows in a week, "
                f"and its remaining sum-of-squares share after week effects is {week_share}."
            ),
        },
    }


def _fit_frame(
    frame: pd.DataFrame,
    model_id: str,
    role: str,
    regressors: tuple[str, ...],
    extra: dict[str, np.ndarray] | None = None,
) -> dict[str, object]:
    panel = _panel_from_frame(frame)
    if extra:
        for name, values in extra.items():
            panel[name] = values
    spec = ModelSpec(
        model_id,
        role,
        False,
        "log_move",
        regressors,
        ("pair", "week"),
        sample=model_id,
    )
    fit = _fit_linear(panel, spec, keep_arrays=False)
    coded = panel["codes"]
    assert isinstance(coded, dict)
    screen = _pair_screen(panel["unit_price"], coded["pair"])
    price = next(
        row for row in _coefficient_record(fit, spec) if row["term"] == "log_unit_price"
    )
    extras = [
        row for row in _coefficient_record(fit, spec) if row["term"] != "log_unit_price"
    ]
    stores = int(pd.Series(panel["store"]).nunique())
    return {
        "model_id": model_id,
        "role": role,
        "status": "estimated",
        "n": fit.n,
        "stores": stores,
        "few_store_clusters": stores < 30,
        "estimate": price["estimate"],
        "se_cluster_store": price["se_cluster_store"],
        "ci95_low": price["ci95_low"],
        "ci95_high": price["ci95_high"],
        "associated_movement_change_for_10_percent_price": price[
            "associated_movement_change_for_10_percent_price"
        ],
        "other_coefficients": [
            {
                "term": row["term"],
                "estimate": row["estimate"],
                "se_cluster_store": row["se_cluster_store"],
            }
            for row in extras
        ],
        "causal_claim": False,
        "replaces_confirmatory": False,
        **screen,
    }


def _try_fit(
    frame: pd.DataFrame,
    model_id: str,
    role: str,
    regressors: tuple[str, ...],
    extra: dict[str, np.ndarray] | None = None,
) -> dict[str, object]:
    logger.info("Robustness fit %s on %s rows.", model_id, len(frame))
    if frame["store"].nunique() < 2 or len(frame) < 10:
        return {
            "model_id": model_id,
            "role": role,
            "status": "not_estimated",
            "reason": "The subsample does not have two stores and ten rows.",
            "causal_claim": False,
            "replaces_confirmatory": False,
        }
    try:
        return _fit_frame(frame, model_id, role, regressors, extra)
    except EstimationError as exc:
        return {
            "model_id": model_id,
            "role": role,
            "status": "not_estimated",
            "reason": str(exc),
            "n": int(len(frame)),
            "causal_claim": False,
            "replaces_confirmatory": False,
        }


def audit(root: Path) -> dict[str, object]:
    """Write the identification audit from the cereals log sample."""
    quality_path = root / "reports" / "results" / "data_quality.json"
    baseline_path = root / "reports" / "results" / "baseline_models.json"
    quality = json.loads(quality_path.read_text())
    baseline = json.loads(baseline_path.read_text())
    if not quality["full_sample"] or baseline.get("causal_claim") is not False:
        raise EstimationError("The quality report or the baseline file is not the cereals fit.")
    expected_rows = int(quality["row_reconciliation"]["log_sample_rows"])
    log_path = root / "data" / "processed" / "cereals_log_sample.parquet"
    frame = pd.read_parquet(log_path, columns=AUDIT_COLUMNS)
    if len(frame) != expected_rows:
        raise EstimationError("The log sample row count does not match the quality report.")
    if frame[AUDIT_COLUMNS].isna().any().any():
        # descrip and price_tier may be missing; those are not regression requirements
        required = [column for column in AUDIT_COLUMNS if column not in {"descrip", "price_tier"}]
        if frame[required].isna().any().any():
            raise EstimationError("A required audit column contains a null.")

    logger.info("Measuring instrument correlations. Verdicts stay at their pre-set values.")
    measurements = _instrument_measurements(frame)
    evidence = []
    for candidate in CANDIDATES:
        measured = measurements.get(candidate.variable, {})
        evidence.append(
            {
                "variable": candidate.variable,
                "source": candidate.source,
                "construction": candidate.construction,
                "rationale": candidate.rationale,
                "exclusion": candidate.exclusion,
                "direct_demand_effects": candidate.direct_demand_effects,
                "common_shocks": candidate.common_shocks,
                "required_controls": candidate.required_controls,
                "verdict": candidate.verdict,
                "verdict_reason": candidate.verdict_reason,
                **measured,
            }
        )
    if any(row["verdict"] == "APPROVED" for row in evidence):
        raise EstimationError("An instrument verdict was APPROVED. This audit does not allow that.")

    confirmatory_regressors = ("log_unit_price", "promo_coded")
    blank = frame.loc[frame["sale_class"].eq("blank")]
    coded = frame.loc[frame["sale_class"].eq("coded")]
    discontinued = frame["descrip"].astype("string").fillna("").str.startswith("~")
    early = frame.loc[frame["week"] <= WEEK_SPLIT]
    late = frame.loc[frame["week"] >= WEEK_SPLIT + 1]
    high = frame.loc[frame["price_tier"].astype("string").eq("High")]
    cub = frame.loc[frame["price_tier"].astype("string").eq("CubFighter")]
    gl = frame.copy()
    gl["promo_coded"] = frame["sale_class"].isin(["coded", "unclassified"]).to_numpy()

    pair = frame["upc"].to_numpy(dtype=np.int64) * 10_000 + frame["store"].to_numpy(dtype=np.int64)
    week = frame["week"].to_numpy(dtype=np.int64)
    log_price = frame["log_unit_price"].to_numpy(dtype=np.float64)
    lead = _adjacent(log_price, pair, week, lead=True)
    lead_frame = frame.loc[np.isfinite(lead)].copy()
    lead_values = lead[np.isfinite(lead)]

    price_span = (
        pd.DataFrame({"pair": pair, "price": frame["unit_price"].to_numpy(dtype=np.float64)})
        .groupby("pair", sort=False)["price"]
        .agg(["min", "max"])
    )
    keepers = price_span.index[(price_span["max"] - price_span["min"]) > PRICE_CHANGE_TOLERANCE]
    varying = frame.loc[np.isin(pair, keepers.to_numpy())]

    price_only = ("log_unit_price",)
    robustness = [
        _try_fit(
            gl,
            "R_promo_includes_unclassified",
            "M5 with G and L moved into the promotion indicator.",
            confirmatory_regressors,
        ),
        _try_fit(
            blank,
            "R_blank_sale_only",
            "Pair and week effects on blank SALE rows. Blank is not a confirmed regular price.",
            price_only,
        ),
        _try_fit(
            coded,
            "R_coded_sale_only",
            "Pair and week effects on coded B/C/S rows only.",
            price_only,
        ),
        _try_fit(
            frame.loc[discontinued],
            "R_discontinued_upc",
            "M5 on UPCs whose description begins with the discontinued mark.",
            confirmatory_regressors,
        ),
        _try_fit(
            frame.loc[~discontinued],
            "R_not_discontinued_upc",
            "M5 on UPCs without the discontinued mark.",
            confirmatory_regressors,
        ),
        _try_fit(
            high,
            "R_high_tier_stores",
            "M5 on stores coded High in the store codebook.",
            confirmatory_regressors,
        ),
        _try_fit(
            cub,
            "R_cubfighter_stores",
            "M5 on CubFighter stores. Few clusters make the interval rough.",
            confirmatory_regressors,
        ),
        _try_fit(
            early,
            "R_weeks_1_through_200",
            "M5 on weeks 1–200.",
            confirmatory_regressors,
        ),
        _try_fit(
            late,
            "R_weeks_201_through_399",
            "M5 on weeks 201–399, which contain the 1995 gap.",
            confirmatory_regressors,
        ),
        _try_fit(
            lead_frame,
            "R_adjacent_price_lead",
            "M5 plus next week's log price when that week is adjacent and observed.",
            ("log_unit_price", "log_price_next", "promo_coded"),
            {"log_price_next": lead_values},
        ),
        _try_fit(
            varying,
            "R_pairs_with_a_price_change",
            "M5 on pairs whose unit price changes by more than $0.001.",
            confirmatory_regressors,
        ),
    ]

    full_screen = _pair_screen(
        frame["unit_price"].to_numpy(dtype=np.float64),
        pair,
    )
    support_share = (
        full_screen["multiweek_pairs_with_log_range_at_least_log_1_10"]
        / full_screen["multiweek_pairs"]
    )
    price_table = pd.read_csv(root / "reports" / "tables" / "baseline_regression.csv")
    scenarios = []
    assumed = {
        "observational_confirmatory_association": _table_estimate(price_table, "M5_confirmatory"),
        "observational_pooled_association": _table_estimate(price_table, "M0_pooled_ols"),
        "assumed_unit_elasticity": -1.0,
        "assumed_more_price_sensitive": -3.0,
    }
    for name, beta in assumed.items():
        scenarios.append(
            {
                "scenario": name,
                "assumed_elasticity": beta,
                "price_ratio": 1.10,
                "associated_movement_change": assumed_movement_change(beta, 1.10),
                "associated_revenue_change_if_quantity_scales_that_way": assumed_revenue_change(
                    beta, 1.10
                ),
                "causal_estimate": False,
                "label": (
                    "Arithmetic under an assumed constant elasticity. "
                    "Not a causal effect and not a price that was charged."
                ),
                "share_of_multiweek_pairs_whose_historical_log_range_covers_10_percent": (
                    support_share
                ),
            }
        )

    synthetic = [item.__dict__ for item in synthetic_iv_examples()]
    raw_dir = root / "data" / "raw"
    raw_names = sorted(path.name for path in raw_dir.iterdir()) if raw_dir.exists() else []
    assignment_names = [
        name for name in raw_names if "assign" in name.lower() or "experiment" in name.lower()
    ]
    early_end = week_bounds(WEEK_SPLIT)[1]
    late_start = week_bounds(WEEK_SPLIT + 1)[0]

    document: dict[str, object] = {
        "generated_by": "python -m pricing_research.estimation.identify",
        "branch": "B",
        "branch_label": "Identification is inadequate. No causal elasticity is claimed.",
        "iv_estimated_on_kilts_rows": False,
        "overidentification_test": "not applicable; no instrument was approved",
        "weak_instrument_diagnostics": "not applicable; 2SLS was not estimated on the scanner rows",
        "endogeneity_test": (
            "A Hausman test was not computed. It would require one estimator to be "
            "consistent for a causal parameter, and that estimator was not established."
        ),
        "ols_bias_direction": (
            "Not claimed. Pooled and fixed-effects slopes are different associations. "
            "Reading the gap as the sign of omitted-variable bias would require the "
            "fixed-effects slope to be the causal parameter."
        ),
        "retained_observational_model": "M5_confirmatory",
        "dataset_rows": expected_rows,
        "week_split": {
            "early_weeks": f"1–{WEEK_SPLIT}",
            "early_ends": str(early_end),
            "late_weeks": f"{WEEK_SPLIT + 1}–399",
            "late_starts": str(late_start),
            "late_includes_missing_weeks": "262–265, 284–309, and 370–371",
        },
        "hoch_assignment_filenames_in_raw": assignment_names,
        "raw_filenames": raw_names,
        "pair_screen": full_screen,
        "instruments": evidence,
        "robustness": robustness,
        "scenarios": scenarios,
        "synthetic_iv_is_not_empirical": True,
        "causal_claim": False,
    }
    out = root / "reports" / "results" / "identification_audit.json"
    out.write_text(json.dumps(_jsonable(document), indent=2) + "\n")
    synthetic_path = root / "reports" / "results" / "synthetic_iv_demonstration.json"
    synthetic_path.write_text(
        json.dumps(
            {"empirical": False, "kilts_rows": 0, "designs": synthetic},
            indent=2,
        )
        + "\n"
    )
    table_dir = root / "reports" / "tables"
    _write_evidence_table(evidence, table_dir / "instrument_evidence.csv")
    _write_robustness_table(robustness, table_dir / "identification_robustness.csv")
    _plot_robustness(
        robustness,
        root / "reports" / "figures",
        expected_rows,
        reference=_table_estimate(price_table, "M5_confirmatory"),
    )
    logger.info("Wrote %s.", out)
    return document


def _table_estimate(table: pd.DataFrame, model_id: str) -> float:
    match = (table["model_id"] == model_id) & (table["term"] == "log_unit_price")
    rows = table.loc[match, "estimate"]
    if len(rows) != 1:
        raise EstimationError(f"The baseline table lacks one price coefficient for {model_id}.")
    return float(rows.iloc[0])


def _write_evidence_table(evidence: list[dict[str, object]], path: Path) -> None:
    fields = [
        "variable",
        "verdict",
        "source",
        "construction",
        "correlation_with_log_unit_price",
        "within_pair_correlation_with_log_unit_price",
        "ss_share_remaining_after_pair_and_week",
        "missing_share",
        "rows_used_for_correlation",
        "cross_section_note",
        "time_note",
        "exclusion",
        "direct_demand_effects",
        "common_shocks",
        "required_controls",
        "verdict_reason",
    ]
    rows = [{field: item.get(field) for field in fields} for item in evidence]
    write_regression_table(rows, path)


def _write_robustness_table(robustness: list[dict[str, object]], path: Path) -> None:
    fields = [
        "model_id",
        "status",
        "n",
        "stores",
        "pairs",
        "share_with_unit_price_change",
        "within_pair_reading_allowed",
        "few_store_clusters",
        "estimate",
        "se_cluster_store",
        "ci95_low",
        "ci95_high",
        "role",
    ]
    rows = [{field: item.get(field) for field in fields} for item in robustness]
    write_regression_table(rows, path)


def _plot_robustness(
    robustness: list[dict[str, object]],
    figure_dir: Path,
    n_rows: int,
    reference: float,
) -> None:
    estimated = [row for row in robustness if row.get("status") == "estimated"]
    if len(estimated) < 2:
        return
    labels = [str(row["model_id"]) for row in estimated]
    estimate = np.array([float(row["estimate"]) for row in estimated])
    low = np.array([float(row["ci95_low"]) for row in estimated])
    high = np.array([float(row["ci95_high"]) for row in estimated])
    position = np.arange(len(labels))
    figure, axes = new_figure()
    axes.axvline(0, color="#52606d", linewidth=0.8)
    axes.axvline(reference, color="#9fb3c8", linewidth=0.8)
    axes.errorbar(
        estimate,
        position,
        xerr=[estimate - low, high - estimate],
        fmt="o",
        color="#1d4e89",
        ecolor="#1f2933",
        capsize=3,
    )
    axes.set_yticks(position)
    axes.set_yticklabels(labels)
    axes.set_xlabel("Coefficient on log unit price")
    axes.set_title("Observational robustness of the cereals association")
    axes.invert_yaxis()
    catalog: list[dict[str, object]] = []
    save_figure(
        figure,
        figure_dir / "identification_01_robustness.png",
        catalog,
        figure_id="identification_01_robustness",
        title="Observational robustness of the cereals association",
        sample="cereals log sample and the pre-specified subsamples named on the axis",
        n_rows=n_rows,
        units="log item movement per log dollar of unit price",
        definition=(
            "Store-clustered 95 percent intervals. The pale line marks the full-sample "
            "confirmatory point estimate. These fits do not estimate a causal elasticity. "
            "CubFighter uses few store clusters."
        ),
    )
    write_catalog(figure_dir / "identification_figure_metadata.json", catalog)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Audit cereals price identification. Does not fit 2SLS."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    audit(args.root)


if __name__ == "__main__":
    main()
