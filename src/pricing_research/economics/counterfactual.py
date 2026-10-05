"""Hypothetical cereals price scenarios on historical UPC-store baselines.

The command reads the log sample and the saved associations. It does not
refit them, and it does not treat an association as a causal elasticity.
Bertrand markup optimization is not implemented: own-price substitution,
ownership, marginal cost, and equilibrium responses are not in the files.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from pricing_research.data.calendar import week_bounds
from pricing_research.economics.scenarios import (
    LESS_FAVORABLE_MARGIN_POINTS,
    NARROW_RATIOS,
    PRICE_RATIOS,
    ElasticityCase,
    ScenarioError,
    accounting_totals,
    less_favorable_unit_cost,
    prices_inside_support,
    support_for_ratios,
    unit_cost_from_profit_percent,
)
from pricing_research.reporting.figures import (
    ACCENT,
    INK,
    MUTED,
    new_figure,
    save_figure,
    write_catalog,
)

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
# Last missing-week block ends at 371. Week 374 is inside the final contiguous stretch.
RECENT_BASELINE_WEEK = 374
PANEL_COLUMNS = [
    "store",
    "upc",
    "week",
    "move",
    "unit_price",
    "profit",
    "sale_class",
    "descrip",
    "size",
]


def elasticity_cases(root: Path) -> tuple[ElasticityCase, ...]:
    """Read stated elasticities from the saved result files. Do not refit."""
    price = pd.read_csv(root / "reports" / "tables" / "baseline_regression.csv")
    robust = pd.read_csv(root / "reports" / "tables" / "identification_robustness.csv")
    m0 = _price_row(price, "M0_pooled_ols")
    m5 = _price_row(price, "M5_confirmatory")
    if bool(m5["causal_claim"]):
        raise ScenarioError("The baseline file marks the confirmatory slope as causal.")
    return (
        ElasticityCase(
            "low_sensitivity_pooled_association",
            float(m0["estimate"]),
            "estimated_association",
            "Least sensitive pre-specified association, used as a hypothetical elasticity.",
        ),
        ElasticityCase(
            "central_confirmatory_association",
            float(m5["estimate"]),
            "estimated_association",
            "M5 slope used as a hypothetical constant elasticity. Not a causal elasticity.",
        ),
        ElasticityCase(
            "assumed_unit",
            -1.0,
            "assumed",
            "Round benchmark. A uniform percent price change leaves revenue unchanged.",
        ),
        ElasticityCase(
            "high_sensitivity_assumed",
            -3.0,
            "assumed",
            "Round adverse case near the pair-PPML neighborhood. Not the PPML estimate.",
        ),
        ElasticityCase(
            "blank_sale_association",
            _robust_estimate(robust, "R_blank_sale_only"),
            "estimated_association",
            "Blank SALE slice. Blank is not a confirmed regular price.",
        ),
        ElasticityCase(
            "coded_sale_association",
            _robust_estimate(robust, "R_coded_sale_only"),
            "estimated_association",
            "Coded B/C/S slice. Exploratory specification check.",
        ),
        ElasticityCase(
            "early_window_association",
            _robust_estimate(robust, "R_weeks_1_through_200"),
            "estimated_association",
            "Weeks 1–200. Specification check, not a new confirmatory model.",
        ),
        ElasticityCase(
            "late_window_association",
            _robust_estimate(robust, "R_weeks_201_through_399"),
            "estimated_association",
            "Weeks 201–399. Specification check, not a new confirmatory model.",
        ),
    )


def parameter_band(root: Path) -> dict[str, object]:
    """Store-cluster interval for the M5 price coefficient, plus wider cluster SEs.

    The store-cluster standard error is the marginal cluster-robust standard
    error from the joint regression on price and the promotion flag. The
    covariance between those two coefficients is already inside that standard
    error. Promotion status is held fixed, so the promotion coefficient is
    not redrawn. Independent draws of the two coefficients are not used.
    """
    table = pd.read_csv(root / "reports" / "tables" / "baseline_regression.csv")
    row = _price_row(table, "M5_confirmatory")
    estimate = float(row["estimate"])
    critical = float(row["t_critical_store"])
    bands = {
        "estimate": estimate,
        "store_cluster_se": float(row["se_cluster_store"]),
        "store_cluster_low": float(row["ci95_low"]),
        "store_cluster_high": float(row["ci95_high"]),
        "week_cluster_se": float(row["se_cluster_week"]),
        "two_way_se": float(row["se_cluster_store_and_week"]),
        "critical_value_applied_to_wider_ses": critical,
        "draws": "none",
        "independent_coefficient_draws": False,
        "note": (
            "Endpoints use the published cluster-robust standard errors. "
            "They describe sampling uncertainty of the association. "
            "They are not a confidence set for a causal elasticity."
        ),
    }
    bands["week_cluster_low"] = estimate - critical * bands["week_cluster_se"]
    bands["week_cluster_high"] = estimate + critical * bands["week_cluster_se"]
    bands["two_way_low"] = estimate - critical * bands["two_way_se"]
    bands["two_way_high"] = estimate + critical * bands["two_way_se"]
    return bands


def pair_baselines(frame: pd.DataFrame) -> pd.DataFrame:
    """One historical shelf per UPC-store pair: the pair's last log-sample week."""
    required = ["store", "upc", "week", "move", "unit_price", "profit", "sale_class"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ScenarioError(f"The panel is missing {missing}.")
    if frame.duplicated(["store", "upc", "week"]).any():
        raise ScenarioError("A UPC-store-week key is duplicated.")
    grouped = frame.groupby(["upc", "store"], sort=False)
    last = frame.loc[grouped["week"].idxmax()].copy()
    span = grouped["unit_price"].agg(price_min="min", price_max="max")
    volume = grouped["move"].sum().rename("pair_move")
    last = last.merge(span, on=["upc", "store"], how="left")
    last = last.merge(volume, on=["upc", "store"], how="left")
    if last[["unit_price", "move", "profit", "price_min", "price_max"]].isna().any().any():
        raise ScenarioError("A baseline price, movement, or margin is missing.")
    return last.reset_index(drop=True)


def scenario_grid(
    baselines: pd.DataFrame,
    cases: tuple[ElasticityCase, ...],
    mask: np.ndarray,
    sample_id: str,
) -> list[dict[str, object]]:
    """Evaluate every elasticity, price ratio, and cost case on one pair mask."""
    quantity = baselines["move"].to_numpy(dtype=np.float64)
    price = baselines["unit_price"].to_numpy(dtype=np.float64)
    profit = baselines["profit"].to_numpy(dtype=np.float64)
    recorded = unit_cost_from_profit_percent(price, profit)
    adverse, _capped = less_favorable_unit_cost(price, profit)
    rows: list[dict[str, object]] = []
    for case in cases:
        for ratio in PRICE_RATIOS:
            for cost_name, cost in (
                ("recorded_average_acquisition_cost", recorded),
                ("less_favorable_margin", adverse),
            ):
                totals = accounting_totals(quantity, price, cost, ratio, case.elasticity, mask)
                _check_closed_form(totals)
                rows.append(
                    {
                        "sample": sample_id,
                        "elasticity_case": case.case_id,
                        "elasticity": case.elasticity,
                        "elasticity_origin": case.origin,
                        "price_ratio": ratio,
                        "price_change": ratio - 1.0,
                        "cost_case": cost_name,
                        "promotion_status": "held at the baseline week",
                        "cross_price_effects": "not modeled",
                        "causal": False,
                        "deployment_supported": False,
                        **totals,
                    }
                )
    return rows


def support_summary(baselines: pd.DataFrame) -> dict[str, object]:
    """Share of pairs, and of baseline revenue, that can host each price ratio."""
    price = baselines["unit_price"].to_numpy(dtype=np.float64)
    low = baselines["price_min"].to_numpy(dtype=np.float64)
    high = baselines["price_max"].to_numpy(dtype=np.float64)
    revenue = price * baselines["move"].to_numpy(dtype=np.float64)
    by_ratio = []
    for ratio in PRICE_RATIOS:
        mask = prices_inside_support(price, low, high, ratio)
        by_ratio.append(
            {
                "price_ratio": ratio,
                "pairs": int(mask.sum()),
                "pair_share": float(mask.mean()),
                "baseline_revenue_share": float(revenue[mask].sum() / revenue.sum()),
            }
        )
    wide = support_for_ratios(price, low, high, PRICE_RATIOS)
    narrow = support_for_ratios(price, low, high, NARROW_RATIOS)
    return {
        "rule": (
            "A candidate unit price is inside support when it lies between the "
            "minimum and maximum unit price observed for that UPC-store pair."
        ),
        "by_ratio": by_ratio,
        "comparable_full_menu_pairs": int(wide.sum()),
        "comparable_full_menu_pair_share": float(wide.mean()),
        "comparable_full_menu_revenue_share": float(revenue[wide].sum() / revenue.sum()),
        "comparable_narrow_menu_pairs": int(narrow.sum()),
        "comparable_narrow_menu_pair_share": float(narrow.mean()),
        "comparable_narrow_menu_revenue_share": float(revenue[narrow].sum() / revenue.sum()),
        "wide_mask_mean_price": float(price[wide].mean()) if wide.any() else None,
    }


def simulate(baselines: pd.DataFrame, cases: tuple[ElasticityCase, ...]) -> dict[str, object]:
    """Build category, promotion-slice, and top-UPC scenarios from pair baselines."""
    price = baselines["unit_price"].to_numpy(dtype=np.float64)
    low = baselines["price_min"].to_numpy(dtype=np.float64)
    high = baselines["price_max"].to_numpy(dtype=np.float64)
    wide = support_for_ratios(price, low, high, PRICE_RATIOS)
    narrow = support_for_ratios(price, low, high, NARROW_RATIOS)
    profit = baselines["profit"].to_numpy(dtype=np.float64)
    recorded = unit_cost_from_profit_percent(price, profit)
    adverse, capped = less_favorable_unit_cost(price, profit)
    sale = baselines["sale_class"].astype("string")
    grids = {
        "full_menu_historical_support": scenario_grid(
            baselines, cases, wide, "full_menu_historical_support"
        ),
        "narrow_menu_historical_support": scenario_grid(
            baselines, _primary_cases(cases), narrow, "narrow_menu_historical_support"
        ),
        "all_pairs_including_extrapolations": scenario_grid(
            baselines,
            _primary_cases(cases),
            np.ones(len(baselines), dtype=bool),
            "all_pairs_including_extrapolations",
        ),
    }
    return {
        "baselines": _baseline_facts(baselines, recorded, adverse, wide, capped),
        "support": support_summary(baselines),
        "grids": grids,
        "promotion_slices": _promotion_slices(baselines, cases, sale),
        "products": _top_products(baselines, cases, wide),
        "recent_baseline": _recent(baselines, cases),
    }


def run(root: Path) -> dict[str, object]:
    """Write the scenario files from the cereals log sample."""
    audit = json.loads((root / "reports" / "results" / "identification_audit.json").read_text())
    if audit.get("branch") != "B" or audit.get("causal_claim") is not False:
        raise ScenarioError("The identification audit is not Branch B.")
    quality = json.loads((root / "reports" / "results" / "data_quality.json").read_text())
    expected = int(quality["row_reconciliation"]["log_sample_rows"])
    frame = pd.read_parquet(
        root / "data" / "processed" / "cereals_log_sample.parquet",
        columns=PANEL_COLUMNS,
    )
    if len(frame) != expected:
        raise ScenarioError("The log sample row count does not match the quality report.")
    cases = elasticity_cases(root)
    band = parameter_band(root)
    logger.info("Building one baseline shelf per UPC-store pair.")
    baselines = pair_baselines(frame)
    logger.info("Evaluating price menus on %s pairs.", len(baselines))
    body = simulate(baselines, cases)
    document = {
        "causal_claim": False,
        "identification_branch": "B",
        "equilibrium_prices_computed": False,
        "bertrand_markup_optimization": "not estimated",
        "implemented_in_stores": False,
        "generated_by": "python -m pricing_research.economics.counterfactual",
        "decision_problem": (
            "Under stated assumptions about the own-price response, a constant "
            "unit acquisition-cost proxy, and no competitor response, how would "
            "feasible percent price changes move predicted item sales, revenue, "
            "and accounting gross profit?"
        ),
        "epsilon": {
            "represents": (
                "A constant own-price elasticity of item movement with respect to unit price."
            ),
            "estimated_or_assumed": (
                "M0, M5, the blank slice, the coded slice, and the two week windows "
                "are estimated associations used as hypothetical elasticities. "
                "Unit elasticity and −3 are assumed round numbers."
            ),
            "causal": False,
            "units": (
                "Unit price is dollars per item. Movement is items. "
                "Revenue and accounting gross profit are dollars."
            ),
        },
        "held_constant": [
            "the baseline week's promotion class",
            "other products' prices",
            "competitor prices",
            "the baseline unit acquisition-cost proxy, within a cost case",
            "store traffic and assortment",
        ],
        "promotion_validity": (
            "The M5 association holds the coded promotion flag fixed. "
            "These scenarios do not flip SALE. A price cut that would have been "
            "run as a promotion is a different intervention. Blank is not a "
            "confirmed regular-price week."
        ),
        "cost": {
            "recorded_proxy": (
                "Unit cost equals the baseline unit price times (1 - PROFIT/100). "
                "PROFIT is average acquisition cost as a percent of sales."
            ),
            "less_favorable_margin_points": LESS_FAVORABLE_MARGIN_POINTS,
            "reliability": (
                "The proxy is not replacement cost, not marginal cost, and not "
                "stable when the chain forward-buys. In the design notes, PROFIT "
                "changes while truncated PRICE is fixed in 5.3 percent of pairs. "
                "Accounting gross profit is not store operating profit."
            ),
        },
        "competition": (
            "No oligopoly model. Competitor prices are not in the files. "
            "Cross-cereal substitution is not estimated. Category totals are sums "
            "of own-price hypotheticals."
        ),
        "elasticity_cases": [
            {
                "case_id": case.case_id,
                "elasticity": case.elasticity,
                "origin": case.origin,
                "role": case.role,
            }
            for case in cases
        ],
        "parameter_uncertainty": _parameter_rows(band, body),
        **body,
        "decision": _decision(body),
    }
    out = root / "reports" / "results" / "pricing_scenarios.json"
    out.write_text(json.dumps(_jsonable(document), indent=2) + "\n")
    _write_table(document, root / "reports" / "tables" / "pricing_scenarios.csv")
    _plot(document, root / "reports" / "figures", expected)
    logger.info("Wrote %s.", out)
    return document


def _primary_cases(cases: tuple[ElasticityCase, ...]) -> tuple[ElasticityCase, ...]:
    keep = {
        "low_sensitivity_pooled_association",
        "central_confirmatory_association",
        "assumed_unit",
        "high_sensitivity_assumed",
    }
    return tuple(case for case in cases if case.case_id in keep)


def _promotion_slices(
    baselines: pd.DataFrame,
    cases: tuple[ElasticityCase, ...],
    sale: pd.Series,
) -> list[dict[str, object]]:
    """Apply each slice's own association to baselines that already have that SALE class."""
    wanted = {
        "blank": "blank_sale_association",
        "coded": "coded_sale_association",
    }
    by_id = {case.case_id: case for case in cases}
    slices = []
    price = baselines["unit_price"].to_numpy(dtype=np.float64)
    low = baselines["price_min"].to_numpy(dtype=np.float64)
    high = baselines["price_max"].to_numpy(dtype=np.float64)
    wide = support_for_ratios(price, low, high, PRICE_RATIOS)
    for label, case_id in wanted.items():
        mask = sale.eq(label).to_numpy() & wide
        case = by_id[case_id]
        rows = scenario_grid(baselines, (case,), mask, f"baseline_{label}_and_full_menu_support")
        slices.append(
            {
                "baseline_sale_class": label,
                "elasticity_case": case_id,
                "pairs_in_full_menu_support": int(mask.sum()),
                "rows": [
                    row
                    for row in rows
                    if row["cost_case"] == "recorded_average_acquisition_cost"
                    and row["price_ratio"] in {0.90, 1.00, 1.10}
                ],
            }
        )
    return slices


def _top_products(
    baselines: pd.DataFrame,
    cases: tuple[ElasticityCase, ...],
    wide: np.ndarray,
) -> list[dict[str, object]]:
    """Three UPCs with the largest scanned item movement, chosen before the profit comparison."""
    volume = baselines.groupby("upc", sort=False)["pair_move"].sum().sort_values(ascending=False)
    chosen = [int(upc) for upc in volume.head(3).index]
    central = tuple(
        case for case in cases if case.case_id == "central_confirmatory_association"
    )
    products = []
    for upc in chosen:
        member = baselines["upc"].eq(upc).to_numpy() & wide
        descrip = baselines.loc[baselines["upc"].eq(upc), "descrip"].astype("string").dropna()
        size = baselines.loc[baselines["upc"].eq(upc), "size"].astype("string").dropna()
        label = str(descrip.iloc[0]) if len(descrip) else ""
        package = str(size.iloc[0]) if len(size) else ""
        rows = scenario_grid(baselines, central, member, f"upc_{upc}")
        products.append(
            {
                "upc": upc,
                "descrip": label,
                "size": package,
                "selection": "largest total log-sample item movement",
                "pairs_total": int(baselines["upc"].eq(upc).sum()),
                "pairs_in_full_menu_support": int(member.sum()),
                "rows": [
                    row
                    for row in rows
                    if row["cost_case"] == "recorded_average_acquisition_cost"
                    and row["price_ratio"] in {0.98, 1.00, 1.02, 0.90, 1.10}
                ],
            }
        )
    return products


def _recent(baselines: pd.DataFrame, cases: tuple[ElasticityCase, ...]) -> dict[str, object]:
    """Baselines whose last week is in the final contiguous stretch of the file."""
    recent = baselines["week"].ge(RECENT_BASELINE_WEEK)
    sub = baselines.loc[recent].reset_index(drop=True)
    if sub.empty:
        return {"pairs": 0, "rows": []}
    price = sub["unit_price"].to_numpy(dtype=np.float64)
    wide = support_for_ratios(
        price,
        sub["price_min"].to_numpy(dtype=np.float64),
        sub["price_max"].to_numpy(dtype=np.float64),
        PRICE_RATIOS,
    )
    central = tuple(case for case in cases if case.case_id == "central_confirmatory_association")
    rows = scenario_grid(sub, central, wide, "recent_baseline_full_menu_support")
    start, _end = week_bounds(RECENT_BASELINE_WEEK)
    return {
        "rule": f"Last log-sample week is {RECENT_BASELINE_WEEK} or later.",
        "recent_week_starts": start.isoformat(),
        "pairs": int(len(sub)),
        "pairs_in_full_menu_support": int(wide.sum()),
        "rows": [
            row
            for row in rows
            if row["cost_case"] == "recorded_average_acquisition_cost"
            and row["price_ratio"] in {0.98, 1.02, 0.90, 1.10}
        ],
    }


def _baseline_facts(
    baselines: pd.DataFrame,
    recorded: np.ndarray,
    adverse: np.ndarray,
    wide: np.ndarray,
    capped_margins: int,
) -> dict[str, object]:
    price = baselines["unit_price"].to_numpy(dtype=np.float64)
    profit = baselines["profit"].to_numpy(dtype=np.float64)
    revenue = price * baselines["move"].to_numpy(dtype=np.float64)
    return {
        "rule": "Each UPC-store pair contributes its last week in the cereals log sample.",
        "pairs": int(len(baselines)),
        "upcs": int(baselines["upc"].nunique()),
        "stores": int(baselines["store"].nunique()),
        "baseline_week_min": int(baselines["week"].min()),
        "baseline_week_max": int(baselines["week"].max()),
        "baseline_week_median": float(baselines["week"].median()),
        "baseline_revenue_dollars": float(revenue.sum()),
        "revenue_weighted_profit_percent": float(
            np.average(profit, weights=revenue)
        ),
        "pairs_with_nonpositive_profit_share": float(np.mean(profit <= 0.0)),
        "pairs_where_less_favorable_cost_exceeds_price_share": float(
            np.mean(adverse >= price)
        ),
        "less_favorable_margins_capped_at_minus_100": capped_margins,
        "full_menu_support_revenue_weighted_profit_percent": (
            float(np.average(profit[wide], weights=revenue[wide])) if wide.any() else None
        ),
        "recorded_unit_cost_equals_price_times_cost_share": True,
        "median_recorded_unit_cost": float(np.median(recorded)),
        "sale_class_share": {
            str(key): float(value)
            for key, value in (
                baselines["sale_class"].astype("string").value_counts(normalize=True).items()
            )
        },
    }


def _parameter_rows(band: dict[str, object], body: dict[str, object]) -> dict[str, object]:
    """Map M5 sampling endpoints through the accounting identities on the supported menu."""
    evaluations = []
    for label, low_key, high_key in (
        ("store_cluster", "store_cluster_low", "store_cluster_high"),
        ("week_cluster", "week_cluster_low", "week_cluster_high"),
        ("store_and_week", "two_way_low", "two_way_high"),
    ):
        for ratio in (0.90, 1.10):
            evaluations.append(
                {
                    "clustering": label,
                    "price_ratio": ratio,
                    "elasticity_low": band[low_key],
                    "elasticity_high": band[high_key],
                    "revenue_change_at_low_elasticity": (ratio ** (1.0 + band[low_key])) - 1.0,
                    "revenue_change_at_high_elasticity": (ratio ** (1.0 + band[high_key])) - 1.0,
                    "sampling_interval_for": "the M5 association",
                    "causal_confidence_interval": False,
                }
            )
    context = [
        row
        for row in body["grids"]["full_menu_historical_support"]
        if row["elasticity_case"] == "central_confirmatory_association"
        and row["cost_case"] == "recorded_average_acquisition_cost"
        and row["price_ratio"] in {0.90, 1.10}
    ]
    return {
        "band": {key: band[key] for key in band if key != "note"},
        "note": band["note"],
        "central_supported_rows_for_context": context,
        "endpoint_revenue_changes": evaluations,
    }


def _strictly_up(value: object) -> bool:
    """Ignore floating-point dust around a zero accounting change."""
    return isinstance(value, (int, float)) and float(value) > 1e-6


def _decision(body: dict[str, object]) -> dict[str, object]:
    """Classify accounting signs. Deployment stays unsupported in every cell."""
    rows = [
        row
        for row in body["grids"]["full_menu_historical_support"]
        if row["cost_case"] == "recorded_average_acquisition_cost" and row["price_ratio"] != 1.0
    ]
    classified = []
    for row in rows:
        revenue = row["revenue_change"]
        profit = row["gross_profit_change"]
        classified.append(
            {
                "elasticity_case": row["elasticity_case"],
                "elasticity": row["elasticity"],
                "price_change": row["price_change"],
                "quantity_change": row["quantity_change"],
                "revenue_change": revenue,
                "gross_profit_change": profit,
                "both_accounting_totals_rise": _strictly_up(revenue) and _strictly_up(profit),
                "deployment_supported": False,
            }
        )
    both = [row for row in classified if row["both_accounting_totals_rise"]]
    return {
        "deployment_supported": False,
        "reason": (
            "Phase 5 did not establish a causal elasticity. Competitor response, "
            "cross-product substitution, and marginal cost are not identified. "
            "No price in this file was implemented in stores."
        ),
        "accounting_improvements_only_under_the_stated_elasticity": both,
        "manager_tests_before_any_deployment": [
            "Write the price assignment and the weeks down before looking at the response.",
            "Hold the promotion calendar fixed, so the test is not a promotion under another name.",
            "Measure substitution to other cereals and the change in store traffic.",
            "Use a replacement-cost record rather than the average-acquisition-cost margin.",
            "Start inside the historical price range of the tested UPC-store pairs.",
        ],
    }


def _check_closed_form(totals: dict[str, float | int | None]) -> None:
    if totals["pairs"] == 0:
        return
    quantity = totals["quantity_change"]
    revenue = totals["revenue_change"]
    if quantity is None or revenue is None:
        raise ScenarioError("A positive baseline produced a missing percent change.")
    if abs(quantity - totals["closed_form_quantity_change"]) > 1e-8:
        raise ScenarioError("Aggregate quantity departed from the constant-elasticity factor.")
    if abs(revenue - totals["closed_form_revenue_change"]) > 1e-8:
        raise ScenarioError("Aggregate revenue departed from the constant-elasticity factor.")


def _price_row(table: pd.DataFrame, model_id: str) -> pd.Series:
    match = (table["model_id"] == model_id) & (table["term"] == "log_unit_price")
    rows = table.loc[match]
    if len(rows) != 1:
        raise ScenarioError(f"The baseline table lacks one price coefficient for {model_id}.")
    return rows.iloc[0]


def _robust_estimate(table: pd.DataFrame, model_id: str) -> float:
    rows = table.loc[table["model_id"] == model_id, "estimate"]
    if len(rows) != 1 or not np.isfinite(rows.iloc[0]):
        raise ScenarioError(f"The robustness table lacks one estimate for {model_id}.")
    return float(rows.iloc[0])


def _write_table(document: dict[str, object], path: Path) -> None:
    rows = document["grids"]["full_menu_historical_support"]
    keep = [
        row
        for row in rows
        if row["elasticity_case"]
        in {
            "low_sensitivity_pooled_association",
            "central_confirmatory_association",
            "assumed_unit",
            "high_sensitivity_assumed",
        }
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(keep).to_csv(path, index=False)


def _plot(document: dict[str, object], figure_dir: Path, n_rows: int) -> None:
    catalog: list[dict[str, object]] = []
    grid = document["grids"]["full_menu_historical_support"]
    _revenue_figure(grid, figure_dir, catalog, n_rows)
    _profit_figure(grid, figure_dir, catalog, n_rows)
    write_catalog(figure_dir / "scenario_figure_metadata.json", catalog)


def _series(
    grid: list[dict[str, object]],
    case_id: str,
    cost: str,
) -> list[dict[str, object]]:
    rows = [
        row
        for row in grid
        if row["elasticity_case"] == case_id and row["cost_case"] == cost
    ]
    return sorted(rows, key=lambda row: float(row["price_change"]))


def _revenue_figure(grid, figure_dir: Path, catalog: list[dict[str, object]], n_rows: int) -> None:
    figure, axes = new_figure()
    styles = (
        ("low_sensitivity_pooled_association", "Pooled association", INK, "-"),
        ("assumed_unit", "Assumed −1", MUTED, "--"),
        ("central_confirmatory_association", "Confirmatory association", ACCENT, "-"),
        ("high_sensitivity_assumed", "Assumed −3", "#9fb3c8", "-"),
    )
    for case_id, label, color, style in styles:
        rows = _series(grid, case_id, "recorded_average_acquisition_cost")
        x = [100.0 * float(row["price_change"]) for row in rows]
        y = [100.0 * float(row["revenue_change"]) for row in rows]
        axes.plot(x, y, color=color, linestyle=style, marker="o", label=label)
    axes.axhline(0, color=MUTED, linewidth=0.8)
    axes.set_xlabel("Price change (percent)")
    axes.set_ylabel("Revenue change (percent)")
    axes.set_title("Hypothetical revenue on pairs inside the full price menu")
    axes.legend(frameon=False)
    figure.tight_layout()
    save_figure(
        figure,
        figure_dir / "scenario_01_revenue.png",
        catalog,
        figure_id="scenario_01_revenue",
        title="Hypothetical revenue on pairs inside the full price menu",
        sample="cereals log sample, last week per pair, full-menu historical support",
        n_rows=n_rows,
        units="percent change in dollar revenue",
        definition=(
            "Own-price constant-elasticity arithmetic. Not a causal prediction. "
            "Competitor response and cross-product substitution are omitted."
        ),
    )


def _profit_figure(grid, figure_dir: Path, catalog: list[dict[str, object]], n_rows: int) -> None:
    figure, axes = new_figure()
    styles = (
        ("recorded_average_acquisition_cost", "Recorded acquisition-cost proxy", ACCENT),
        ("less_favorable_margin", "Margin 10 points less favorable", INK),
    )
    for cost, label, color in styles:
        rows = _series(grid, "central_confirmatory_association", cost)
        x = [100.0 * float(row["price_change"]) for row in rows]
        y = [100.0 * float(row["gross_profit_change"]) for row in rows]
        axes.plot(x, y, color=color, marker="o", label=label)
    axes.axhline(0, color=MUTED, linewidth=0.8)
    axes.set_xlabel("Price change (percent)")
    axes.set_ylabel("Accounting gross-profit change (percent)")
    axes.set_title("Hypothetical gross profit if the confirmatory slope were the elasticity")
    axes.legend(frameon=False)
    figure.tight_layout()
    save_figure(
        figure,
        figure_dir / "scenario_02_gross_profit.png",
        catalog,
        figure_id="scenario_02_gross_profit",
        title="Hypothetical gross profit if the confirmatory slope were the elasticity",
        sample="cereals log sample, last week per pair, full-menu historical support",
        n_rows=n_rows,
        units="percent change in accounting gross profit dollars",
        definition=(
            "Unit cost is held at a baseline acquisition-cost proxy. "
            "The total is not operating profit and the slope is not causal."
        ),
    )


def _jsonable(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if not np.isfinite(number):
            return None
        return number
    if isinstance(value, (np.integer, int)):
        return int(value)
    if value is None or isinstance(value, str):
        return value
    raise ScenarioError(f"Cannot write {type(value)} to the scenario file.")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Hypothetical cereals price scenarios. Does not estimate a causal elasticity."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    run(args.root)


if __name__ == "__main__":
    main()
