"""Exploratory description of the cereals panel.

The command reads the Phase 2 Parquet files and writes figures plus a JSON
summary. It does not estimate the confirmatory regression. Correlations of
log price and log movement are descriptions of this sample, not elasticities.

    python -m pricing_research.reporting.explore
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pricing_research.data.calendar import week_bounds
from pricing_research.reporting.descriptives import (
    PRICE_CHANGE_TOLERANCE,
    coverage_ratio,
    herfindahl,
    largest_share,
    pearson_correlation,
    quantile_bin_means,
    within_sum_of_squares_share,
)
from pricing_research.reporting.figures import (
    ACCENT,
    FILL,
    INK,
    MUTED,
    apply_style,
    new_figure,
    save_figure,
    write_catalog,
)

LOGGER = logging.getLogger(__name__)
DENSITY_SAMPLE_ROWS = 200_000
DENSITY_SAMPLE_SEED = 20261005
LOG_SAMPLE_NAME = "cereals log sample: OK = 1, positive price, quantity, and movement"
AUDITED_NAME = "cereals audited movement rows, including recorded zeros"
MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def _tier_label(frame: pd.DataFrame) -> pd.Series:
    """Separate a blank codebook tier from a store the codebook does not list."""
    label = frame["price_tier"].astype("string").fillna("blank tier in codebook")
    return label.mask(frame["store_unmatched"].astype(bool), "not in codebook")


def _sale_label(frame: pd.DataFrame) -> pd.Series:
    labels = pd.Series("unclassified", index=frame.index)
    labels = labels.mask(frame["sale_class"].eq("blank"), "blank")
    for code in ("B", "C", "S"):
        labels = labels.mask(frame["sale"].eq(code), code)
    return labels


def _pair_means(frame: pd.DataFrame, column: str) -> np.ndarray:
    return frame.groupby(["upc", "store"], sort=False)[column].transform("mean").to_numpy()


def _two_way_correlation(frame: pd.DataFrame, rounds: int = 8) -> dict[str, float]:
    """Correlation after alternating UPC-store and week demeaning.

    This is not the confirmatory coefficient. The promotion indicator is not
    removed, and the result has no standard error.
    """
    x = frame["log_unit_price"].to_numpy(dtype=float).copy()
    y = frame["log_move"].to_numpy(dtype=float).copy()
    pair = frame.groupby(["upc", "store"], sort=False).ngroup().to_numpy()
    week = frame.groupby("week", sort=False).ngroup().to_numpy()
    previous = None
    for _ in range(rounds):
        x = _demean(x, pair)
        y = _demean(y, pair)
        x = _demean(x, week)
        y = _demean(y, week)
        current = pearson_correlation(x, y)
        if previous is not None and abs(current - previous) < 1e-8:
            break
        previous = current
    return {"correlation": current, "rounds_used": float(_ + 1)}


def _demean(values: np.ndarray, codes: np.ndarray) -> np.ndarray:
    means = pd.Series(values).groupby(codes, sort=False).transform("mean").to_numpy()
    return values - means


def _load_quality(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _audited_facts(path: Path) -> dict[str, object]:
    frame = pd.read_parquet(
        path,
        columns=["store", "upc", "week", "move", "price", "month", "in_log_sample", "descrip"],
    )
    month = frame["month"].astype(int)
    by_month = (
        frame.groupby(month, sort=True)["move"]
        .agg(rows="size", total_move="sum", mean_move="mean")
        .reset_index()
    )
    zero_weeks = []
    for week, part in frame.groupby("week", sort=True):
        if bool(part["move"].eq(0).all() and part["price"].eq(0).all()):
            start, end = week_bounds(int(week))
            zero_weeks.append(
                {
                    "week": int(week),
                    "rows": int(len(part)),
                    "week_start": start.isoformat(),
                    "week_end": end.isoformat(),
                }
            )
    logged = set(frame.loc[frame["in_log_sample"], "upc"].dropna().astype(int))
    absent = (
        frame.loc[~frame["upc"].astype(int).isin(logged)]
        .groupby("upc", sort=True)
        .agg(rows=("move", "size"), move=("move", "sum"), descrip=("descrip", "first"))
        .reset_index()
    )
    by_week = frame.groupby("week", sort=True).size()
    facts: dict[str, object] = {
        "rows": int(len(frame)),
        "stores": int(frame["store"].nunique()),
        "upcs": int(frame["upc"].nunique()),
        "weeks": int(frame["week"].nunique()),
        "mean_move_items": float(frame["move"].mean()),
        "share_move_zero": float(frame["move"].eq(0).mean()),
        "share_price_zero": float(frame["price"].eq(0).mean()),
        "rows_positive_move_and_nonpositive_price_outside_log_sample": int(
            (frame["move"].gt(0) & ~frame["in_log_sample"] & frame["price"].le(0)).sum()
        ),
        "rows_positive_move_and_positive_price_outside_log_sample": int(
            (frame["move"].gt(0) & ~frame["in_log_sample"] & frame["price"].gt(0)).sum()
        ),
        "weeks_recorded_as_all_zero_price_and_movement": zero_weeks,
        "upcs_absent_from_log_sample": [
            {
                "upc": int(row.upc),
                "descrip": str(row.descrip).strip(),
                "rows": int(row.rows),
                "total_move_items": float(row.move),
            }
            for row in absent.itertuples(index=False)
        ],
        "mean_move_by_month": [
            {
                "month": int(row.month),
                "rows": int(row.rows),
                "total_move_items": float(row.total_move),
                "mean_move_items": float(row.mean_move),
            }
            for row in by_month.itertuples(index=False)
        ],
        "rows_by_week": {str(int(week)): int(count) for week, count in by_week.items()},
    }
    del frame
    return facts


def _upc_table(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("upc", sort=False)
        .agg(
            move=("move", "sum"),
            gross_sales=("gross_sales", "sum"),
            mean_log_price=("log_unit_price", "mean"),
            rows=("week", "size"),
            stores=("store", "nunique"),
            first_week=("week", "min"),
            last_week=("week", "max"),
            weeks=("week", "nunique"),
            descrip=("descrip", "first"),
        )
        .reset_index()
    )


def explore(interim: Path, processed: Path, reports: Path, quality_path: Path) -> dict[str, object]:
    """Describe the cereals log sample and write the figures."""
    quality = _load_quality(quality_path)
    missing_weeks = set(quality["weeks_missing_inside_manual_span"])
    expected_rows = int(quality["row_reconciliation"]["log_sample_rows"])
    audited_path = interim / "cereals_movement_audited.parquet"
    log_path = processed / "cereals_log_sample.parquet"
    LOGGER.info("Reading audited movement columns")
    audited = _audited_facts(audited_path)
    if int(audited["rows"]) != int(quality["row_reconciliation"]["audited_panel_rows"]):
        raise RuntimeError("Audited row count does not match data_quality.json.")

    LOGGER.info("Reading the log sample")
    frame = pd.read_parquet(
        log_path,
        columns=[
            "store",
            "upc",
            "week",
            "week_start",
            "month",
            "move",
            "unit_price",
            "log_move",
            "log_unit_price",
            "gross_sales",
            "sale",
            "sale_class",
            "promo_coded",
            "descrip",
            "price_tier",
            "store_unmatched",
        ],
    )
    if len(frame) != expected_rows:
        raise RuntimeError(f"Log sample has {len(frame)} rows; quality file says {expected_rows}.")
    if frame[["log_move", "log_unit_price", "unit_price", "move"]].isna().any().any():
        raise RuntimeError("Log sample has null price or movement where the logs should exist.")

    frame["sale_label"] = _sale_label(frame)
    summary = _summarize(frame, audited, missing_weeks)
    summary["inputs"] = {
        "log_sample": str(log_path),
        "audited_panel": str(audited_path),
        "log_sample_sha256": _output_sha(quality, "cereals_log_sample.parquet"),
        "audited_sha256": _output_sha(quality, "cereals_movement_audited.parquet"),
        "confirmatory_regression_estimated": False,
    }
    figures = reports / "figures"
    catalog: list[dict[str, object]] = []
    apply_style()
    _plot_all(frame, summary, figures, catalog)
    write_catalog(figures / "figure_metadata.json", catalog)
    results = reports / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "exploratory_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    LOGGER.info("Wrote %s figures", len(catalog))
    return summary


def _output_sha(quality: dict[str, object], name: str) -> str:
    for item in quality["outputs"]:
        if str(item["path"]).endswith(name):
            return str(item["sha256"])
    raise RuntimeError(f"Quality file has no hash for {name}.")


def _summarize(
    frame: pd.DataFrame,
    audited: dict[str, object],
    missing_weeks: set[int],
) -> dict[str, object]:
    LOGGER.info("Summarizing panel structure")
    log_price = frame["log_unit_price"].to_numpy(dtype=float)
    log_move = frame["log_move"].to_numpy(dtype=float)
    pair_mean = _pair_means(frame, "log_unit_price")
    week_mean = frame.groupby("week", sort=False)["log_unit_price"].transform("mean").to_numpy()
    move_week_mean = frame.groupby("week", sort=False)["log_move"].transform("mean").to_numpy()
    upc_mean = frame.groupby("upc", sort=False)["log_unit_price"].transform("mean").to_numpy()
    store_mean = frame.groupby("store", sort=False)["log_unit_price"].transform("mean").to_numpy()
    within_week_correlation = pearson_correlation(
        log_price - week_mean, log_move - move_week_mean
    )
    within_price = log_price - pair_mean
    within_move = log_move - _pair_means(frame, "log_move")

    pairs = (
        frame.groupby(["upc", "store"], sort=False)
        .agg(
            rows=("week", "size"),
            log_min=("log_unit_price", "min"),
            log_max=("log_unit_price", "max"),
            price_min=("unit_price", "min"),
            price_max=("unit_price", "max"),
            first_week=("week", "min"),
            last_week=("week", "max"),
        )
        .reset_index()
    )
    pairs["log_range"] = pairs["log_max"] - pairs["log_min"]
    pairs["price_range"] = pairs["price_max"] - pairs["price_min"]
    multi = pairs.loc[pairs["rows"] >= 2]
    changed = multi.loc[multi["price_range"] > PRICE_CHANGE_TOLERANCE]

    products = _upc_table(frame)
    products["coverage"] = [
        coverage_ratio(int(row.weeks), int(row.first_week), int(row.last_week), missing_weeks)
        for row in products.itertuples(index=False)
    ]
    products["discontinued_flag"] = products["descrip"].str.startswith("~")
    top = products.sort_values(["move", "upc"], ascending=[False, True]).iloc[0]

    labels = ["blank", "B", "C", "S", "unclassified"]
    promotion = []
    for label in labels:
        mask = frame["sale_label"].eq(label).to_numpy()
        if not mask.any():
            continue
        promotion.append(
            {
                "sale_label": label,
                "rows": int(mask.sum()),
                "share_of_rows": float(mask.mean()),
                "mean_move_items": float(frame.loc[mask, "move"].mean()),
                "mean_unit_price_dollars": float(frame.loc[mask, "unit_price"].mean()),
                "mean_log_move": float(log_move[mask].mean()),
                "mean_within_pair_log_move": float(within_move[mask].mean()),
                "mean_within_pair_log_price": float(within_price[mask].mean()),
                "total_move_items": float(frame.loc[mask, "move"].sum()),
                "total_gross_sales_dollars": float(frame.loc[mask, "gross_sales"].sum()),
            }
        )

    LOGGER.info("Measuring cross-store prices and price changes")
    co_movement = _price_co_movement(frame)
    store_position = _store_position(frame, log_price - upc_mean)
    month_log = (
        frame.groupby(frame["month"].astype(int), sort=True)
        .agg(rows=("move", "size"), mean_move=("move", "mean"), total_move=("move", "sum"))
        .reset_index()
    )
    present_both = products["first_week"].le(52) & products["last_week"].ge(348)

    return {
        "interpretation": (
            "Descriptive associations in the cereals log sample. "
            "Not causal elasticities and not the confirmatory regression."
        ),
        "log_sample": {
            "rows": int(len(frame)),
            "stores": int(frame["store"].nunique()),
            "upcs": int(frame["upc"].nunique()),
            "weeks": int(frame["week"].nunique()),
            "upc_store_pairs": int(len(pairs)),
            "pairs_with_at_least_two_weeks": int(len(multi)),
            "median_weeks_per_pair": float(pairs["rows"].median()),
            "p10_weeks_per_pair": float(pairs["rows"].quantile(0.10)),
            "p90_weeks_per_pair": float(pairs["rows"].quantile(0.90)),
        },
        "audited": audited,
        "missing_weeks": sorted(missing_weeks),
        "products": {
            "median_coverage_inside_own_span": float(products["coverage"].median()),
            "share_coverage_at_least_0_5": float(products["coverage"].ge(0.5).mean()),
            "upcs_with_an_observation_in_weeks_1_to_52": int((products["first_week"] <= 52).sum()),
            "upcs_with_an_observation_in_weeks_348_to_399": int(
                (products["last_week"] >= 348).sum()
            ),
            "upcs_observed_in_both_windows": int(present_both.sum()),
            "upcs_spanning_at_least_100_week_indexes": int(
                (products["last_week"] - products["first_week"]).ge(100).sum()
            ),
            "median_coverage_when_span_is_at_least_100_weeks": float(
                products.loc[
                    products["last_week"] - products["first_week"] >= 100, "coverage"
                ].median()
            ),
            "discontinued_tilde_upcs": int(products["discontinued_flag"].sum()),
            "discontinued_tilde_share_of_movement": float(
                products.loc[products["discontinued_flag"], "move"].sum() / products["move"].sum()
            ),
            "highest_movement_upc": {
                "selection_rule": "largest total MOVE in the log sample; UPC breaks ties",
                "upc": int(top.upc),
                "descrip": str(top.descrip),
                "total_move_items": float(top.move),
                "share_of_log_sample_movement": float(top.move / products["move"].sum()),
                "rows": int(top.rows),
                "stores": int(top.stores),
                "first_week": int(top.first_week),
                "last_week": int(top.last_week),
                "weeks": int(top.weeks),
                "coverage": float(top.coverage),
            },
        },
        "concentration": {
            "movement_herfindahl": herfindahl(products["move"].to_numpy(dtype=float)),
            "revenue_herfindahl": herfindahl(products["gross_sales"].to_numpy(dtype=float)),
            "movement_share_top_10_upcs": largest_share(products["move"].to_numpy(dtype=float), 10),
            "revenue_share_top_10_upcs": largest_share(
                products["gross_sales"].to_numpy(dtype=float), 10
            ),
            "movement_share_top_decile_upcs": largest_share(
                products["move"].to_numpy(dtype=float), max(1, len(products) // 10)
            ),
            "revenue_share_top_decile_upcs": largest_share(
                products["gross_sales"].to_numpy(dtype=float), max(1, len(products) // 10)
            ),
            "top_decile_upc_count": max(1, len(products) // 10),
            "upc_count": int(len(products)),
        },
        "between_upc_price_and_volume": {
            "rows": int(len(products)),
            "correlation_log_total_move_and_mean_log_unit_price": pearson_correlation(
                np.log(products["move"].to_numpy(dtype=float)),
                products["mean_log_price"].to_numpy(dtype=float),
            ),
            "definition": (
                "Each UPC is one point. Volume is the log of total log-sample item movement. "
                "Price is the unweighted mean of log unit price across that UPC's rows."
            ),
        },
        "price_movement_correlations": {
            "pooled": pearson_correlation(log_price, log_move),
            "within_upc_store": pearson_correlation(within_price, within_move),
            "within_week_only": within_week_correlation,
            "within_upc_store_and_week": _two_way_correlation(frame),
            "note": (
                "Within-week correlation subtracts week means only. "
                "The two-way figure subtracts UPC-store means and week means by alternating "
                "demeaning. Neither removes the promotion indicator. Neither is beta."
            ),
        },
        "log_price_variance_shares": {
            "within_upc_store": within_sum_of_squares_share(log_price, pair_mean),
            "within_upc": within_sum_of_squares_share(log_price, upc_mean),
            "within_store": within_sum_of_squares_share(log_price, store_mean),
            "within_week": within_sum_of_squares_share(log_price, week_mean),
            "definition": "One minus the between-group share of the total sum of squares.",
        },
        "within_pair_price_variation": {
            "all_pairs": int(len(pairs)),
            "pairs_with_at_least_two_weeks": int(len(multi)),
            "pairs_with_unit_price_range_above_0_001_dollars": int(len(changed)),
            "share_of_all_pairs": float(len(changed) / len(pairs)),
            "share_of_pairs_with_at_least_two_weeks": float(len(changed) / len(multi)),
            "median_log_range_among_multiweek_pairs": float(multi["log_range"].median()),
            "share_of_multiweek_pairs_with_log_range_at_least_log_1_05": float(
                multi["log_range"].ge(float(np.log(1.05))).mean()
            ),
            "phase1_sufficiency_rule": (
                "A later fixed-effects coefficient is not read as a within-pair association "
                "if fewer than 20 percent of log-sample pairs have any truncated price change."
            ),
        },
        "promotion": promotion,
        "cross_store_prices": co_movement,
        "store_price_position": store_position,
        "seasonality_log_sample_mean_move_by_month": [
            {
                "month": int(row.month),
                "rows": int(row.rows),
                "mean_move_items": float(row.mean_move),
                "total_move_items": float(row.total_move),
            }
            for row in month_log.itertuples(index=False)
        ],
        "unit_price_percentiles_dollars": {
            str(pct): float(frame["unit_price"].quantile(pct / 100))
            for pct in (1, 5, 25, 50, 75, 95, 99)
        },
        "move_percentiles_items": {
            str(pct): float(frame["move"].quantile(pct / 100)) for pct in (1, 5, 25, 50, 75, 95, 99)
        },
    }


def _price_co_movement(frame: pd.DataFrame) -> dict[str, object]:
    levels = (
        frame.groupby(["upc", "week"], sort=False)["unit_price"]
        .agg(stores="size", price_min="min", price_max="max")
        .reset_index()
    )
    levels["range"] = levels["price_max"] - levels["price_min"]
    multi = levels.loc[levels["stores"] >= 10]
    ordered = frame.sort_values(["upc", "store", "week"], kind="mergesort")
    previous = ordered.groupby(["upc", "store"], sort=False)["unit_price"].shift()
    comparable = previous.notna()
    changed = comparable & (ordered["unit_price"] - previous).abs().gt(PRICE_CHANGE_TOLERANCE)
    change_rows = ordered.loc[comparable, ["upc", "week"]].copy()
    change_rows["changed"] = changed.loc[comparable].to_numpy()
    by_week = change_rows.groupby(["upc", "week"], sort=False)["changed"].agg(
        stores_with_previous="size", stores_changed="sum"
    )
    active = by_week.loc[
        (by_week["stores_with_previous"] >= 10) & (by_week["stores_changed"] >= 1)
    ].copy()
    active["share"] = active["stores_changed"] / active["stores_with_previous"]
    return {
        "unit_price_tolerance_dollars": PRICE_CHANGE_TOLERANCE,
        "upc_weeks_with_at_least_10_stores": int(len(multi)),
        "share_with_cross_store_range_at_most_0_001": float(
            multi["range"].le(PRICE_CHANGE_TOLERANCE).mean()
        ),
        "median_cross_store_range_dollars": float(multi["range"].median()),
        "p90_cross_store_range_dollars": float(multi["range"].quantile(0.90)),
        "rows_with_a_previous_observed_week": int(comparable.sum()),
        "share_of_those_rows_whose_price_changed": float(changed.loc[comparable].mean()),
        "upc_weeks_with_at_least_10_comparable_stores_and_one_change": int(len(active)),
        "median_share_of_stores_changing_together": float(active["share"].median()),
        "share_of_those_upc_weeks_with_at_least_80_percent_of_stores_changing": float(
            active["share"].ge(0.8).mean()
        ),
        "previous_week_definition": (
            "The previous row is the preceding observed log-sample week for that UPC and store, "
            "not necessarily the previous calendar week."
        ),
    }


def _store_position(
    frame: pd.DataFrame, within_upc_log_price: np.ndarray
) -> list[dict[str, object]]:
    work = pd.DataFrame(
        {
            "store": frame["store"].to_numpy(),
            "tier": _tier_label(frame).to_numpy(),
            "position": within_upc_log_price,
        }
    )
    grouped = (
        work.groupby("store", sort=False)
        .agg(position=("position", "mean"), tier=("tier", "first"), rows=("position", "size"))
        .reset_index()
    )
    rows = []
    for tier, part in grouped.groupby("tier", sort=False):
        rows.append(
            {
                "price_tier": str(tier),
                "stores": int(len(part)),
                "rows": int(part["rows"].sum()),
                "median_store_log_price_position": float(part["position"].median()),
                "min_store_log_price_position": float(part["position"].min()),
                "max_store_log_price_position": float(part["position"].max()),
            }
        )
    return rows


def _plot_all(
    frame: pd.DataFrame,
    summary: dict[str, object],
    figures: Path,
    catalog: list[dict[str, object]],
) -> None:
    _stash_plot_inputs(frame, summary, set(summary["missing_weeks"]))
    n_rows = int(summary["log_sample"]["rows"])
    _plot_price(frame, figures, catalog, n_rows)
    _plot_quantity(frame, figures, catalog, n_rows)
    _plot_scatter(frame, summary, figures, catalog, n_rows)
    _plot_product(frame, summary, figures, catalog)
    _plot_stores(frame, summary, figures, catalog)
    _plot_promotion(summary, figures, catalog, n_rows)
    _plot_within(summary, figures, catalog)
    _plot_season(summary, figures, catalog)
    _plot_coverage(summary, figures, catalog)
    _plot_lorenz(frame, figures, catalog, n_rows)
    _plot_cross_store(frame, figures, catalog)
    _plot_between_products(summary, frame, figures, catalog)


def _note(axes: plt.Axes, text: str) -> None:
    axes.set_xlabel(axes.get_xlabel() + "\n" + text)


def _plot_price(frame, figures, catalog, n_rows: int) -> None:
    price = frame["unit_price"].to_numpy(dtype=float)
    cap = float(np.quantile(price, 0.99))
    figure, axes = new_figure()
    axes.hist(price[price <= cap], bins=40, color=FILL, edgecolor=ACCENT)
    axes.set_title("Distribution of unit price")
    axes.set_xlabel("Unit price (dollars per item)")
    axes.set_ylabel("Log-sample rows")
    _note(axes, f"Bars stop at the 99th percentile, ${cap:.2f}. n = {n_rows:,} rows.")
    save_figure(
        figure,
        figures / "01_unit_price_distribution.png",
        catalog,
        figure_id="01_unit_price_distribution",
        title="Distribution of unit price",
        sample=LOG_SAMPLE_NAME,
        n_rows=n_rows,
        units="dollars per item",
        definition="PRICE / QTY on the log sample. The histogram omits the top 1 percent of rows.",
    )


def _plot_quantity(frame, figures, catalog, n_rows: int) -> None:
    figure, axes = new_figure()
    axes.hist(frame["log_move"].to_numpy(dtype=float), bins=40, color=FILL, edgecolor=ACCENT)
    axes.set_title("Distribution of log item movement")
    axes.set_xlabel("Natural log of items sold in the store-week")
    axes.set_ylabel("Log-sample rows")
    _note(axes, f"Recorded zero-movement rows are not in this sample. n = {n_rows:,}.")
    save_figure(
        figure,
        figures / "02_log_movement_distribution.png",
        catalog,
        figure_id="02_log_movement_distribution",
        title="Distribution of log item movement",
        sample=LOG_SAMPLE_NAME,
        n_rows=n_rows,
        units="natural log of items",
        definition="log(MOVE) where MOVE > 0. Zero recorded movement is excluded.",
    )


def _plot_scatter(frame, summary, figures, catalog, n_rows: int) -> None:
    rng = np.random.default_rng(DENSITY_SAMPLE_SEED)
    take = rng.choice(n_rows, size=min(DENSITY_SAMPLE_ROWS, n_rows), replace=False)
    log_price = frame["log_unit_price"].to_numpy(dtype=float)
    log_move = frame["log_move"].to_numpy(dtype=float)
    within_price = log_price - _pair_means(frame, "log_unit_price")
    within_move = log_move - _pair_means(frame, "log_move")
    pooled_bins = quantile_bin_means(log_price, log_move)
    within_bins = quantile_bin_means(within_price, within_move)
    summary["pooled_bin_means"] = pooled_bins
    summary["within_pair_bin_means"] = within_bins
    figure, axes = new_figure(2)
    axes[0].hexbin(log_price[take], log_move[take], gridsize=35, cmap="Blues", mincnt=1)
    axes[0].plot(
        [row["x_mean"] for row in pooled_bins],
        [row["y_mean"] for row in pooled_bins],
        color=INK,
        marker="o",
        markersize=3,
    )
    axes[0].set_title("Pooled rows")
    axes[0].set_xlabel("Log unit price")
    axes[0].set_ylabel("Log item movement")
    axes[1].plot(
        [row["x_mean"] for row in within_bins],
        [row["y_mean"] for row in within_bins],
        color=ACCENT,
        marker="o",
    )
    axes[1].axhline(0, color=MUTED, linewidth=0.8)
    axes[1].axvline(0, color=MUTED, linewidth=0.8)
    axes[1].set_title("Within UPC and store")
    axes[1].set_xlabel("Log unit price minus the pair mean")
    axes[1].set_ylabel("Log movement minus the pair mean")
    figure.suptitle("Log price and log movement, binned means on every log-sample row", y=1.02)
    save_figure(
        figure,
        figures / "03_price_volume.png",
        catalog,
        figure_id="03_price_volume",
        title="Log price and log movement",
        sample=LOG_SAMPLE_NAME,
        n_rows=n_rows,
        units="natural log of dollars per item and natural log of items",
        definition=(
            f"Hex density uses {min(DENSITY_SAMPLE_ROWS, n_rows):,} rows drawn with seed "
            f"{DENSITY_SAMPLE_SEED}. Bin means use all {n_rows:,} rows. "
            "The within panel subtracts UPC-store means only."
        ),
    )


def _plot_product(frame, summary, figures, catalog) -> None:
    chosen = summary["products"]["highest_movement_upc"]
    part = frame.loc[frame["upc"].eq(chosen["upc"])]
    weekly = (
        part.groupby("week_start", sort=True)
        .agg(move=("move", "sum"), price=("unit_price", "median"), stores=("store", "nunique"))
        .reset_index()
    )
    weekly["week_start"] = pd.to_datetime(weekly["week_start"])
    dates = weekly["week_start"].map(lambda value: value.toordinal())
    figure, axes = new_figure()
    axes.plot(dates, weekly["move"], color=ACCENT)
    twin = axes.twinx()
    twin.plot(dates, weekly["price"], color=MUTED)
    year_ticks = [pd.Timestamp(year=year, month=1, day=1) for year in range(1990, 1998)]
    axes.set_xticks(
        [tick.toordinal() for tick in year_ticks],
        [str(tick.year) for tick in year_ticks],
    )
    twin.set_ylabel("Median unit price (dollars per item)")
    twin.grid(False)
    axes.set_title(f"{chosen['descrip'].strip()} (UPC {chosen['upc']})")
    axes.set_xlabel("Week starting date")
    axes.set_ylabel("Total items sold across observed stores")
    _note(
        axes,
        f"Highest total log-sample movement. {int(chosen['rows']):,} rows, "
        f"{int(chosen['stores'])} stores. Gaps are weeks with no observed row.",
    )
    save_figure(
        figure,
        figures / "04_product_trend.png",
        catalog,
        figure_id="04_product_trend",
        title=f"Weekly movement and median price, UPC {chosen['upc']}",
        sample=LOG_SAMPLE_NAME,
        n_rows=int(chosen["rows"]),
        units="items per week across stores; dollars per item",
        definition="UPC with the largest total MOVE. Price is the weekly median across stores.",
    )


def _plot_stores(frame, summary, figures, catalog) -> None:
    within = frame["log_unit_price"] - frame.groupby("upc", sort=False)["log_unit_price"].transform(
        "mean"
    )
    work = pd.DataFrame(
        {
            "tier": _tier_label(frame).to_numpy(),
            "position": within.to_numpy(),
            "store": frame["store"].to_numpy(),
        }
    )
    stores = work.groupby("store", sort=False).agg(
        position=("position", "mean"), tier=("tier", "first")
    )
    order = [
        "CubFighter",
        "Low",
        "Medium",
        "High",
        "blank tier in codebook",
        "not in codebook",
    ]
    order = [tier for tier in order if tier in set(stores["tier"])]
    figure, axes = new_figure()
    for index, tier in enumerate(order):
        values = stores.loc[stores["tier"].eq(tier), "position"].to_numpy()
        axes.scatter(np.full(len(values), index), values, color=ACCENT, s=18, zorder=3)
    axes.set_xticks(range(len(order)), order, rotation=15)
    axes.set_ylabel("Store mean of log unit price minus the UPC mean")
    axes.set_xlabel("Manual price tier")
    axes.set_title("Within-product store price position")
    _note(axes, "Each point is one store. Higher means higher prices for the same UPCs.")
    save_figure(
        figure,
        figures / "05_store_price_position.png",
        catalog,
        figure_id="05_store_price_position",
        title="Within-product store price position",
        sample=LOG_SAMPLE_NAME,
        n_rows=int(len(frame)),
        units="log points relative to the UPC mean",
        definition=(
            "For each row, subtract the UPC's mean log unit price. Average those residuals "
            "by store. Tiers come from the store codebook; seven stores are unlabeled."
        ),
    )


def _plot_promotion(summary, figures, catalog, n_rows: int) -> None:
    rows = [row for row in summary["promotion"] if row["sale_label"] != "unclassified"]
    labels = [f"{row['sale_label']}\n(n={row['rows']:,})" for row in rows]
    figure, axes = new_figure(2)
    axes[0].bar(labels, [row["mean_log_move"] for row in rows], color=FILL, edgecolor=ACCENT)
    axes[0].set_title("Pooled mean")
    axes[0].set_ylabel("Mean log item movement")
    axes[0].set_xlabel("SALE code")
    axes[1].bar(
        labels,
        [row["mean_within_pair_log_move"] for row in rows],
        color=FILL,
        edgecolor=ACCENT,
    )
    axes[1].axhline(0, color=MUTED, linewidth=0.8)
    axes[1].set_title("After UPC-store means")
    axes[1].set_ylabel("Mean residual log item movement")
    axes[1].set_xlabel("SALE code")
    figure.suptitle("Movement by promotion code", y=1.02)
    save_figure(
        figure,
        figures / "06_promotion_movement.png",
        catalog,
        figure_id="06_promotion_movement",
        title="Movement by promotion code",
        sample=LOG_SAMPLE_NAME,
        n_rows=n_rows,
        units="natural log of items",
        definition=(
            "Blank is not a confirmed regular price. Coupon weeks are few. "
            "Unclassified G and L codes are omitted from the bars."
        ),
    )


def _plot_within(summary, figures, catalog) -> None:
    # Recomputed from the summary's stored pair ranges is not available row-wise.
    # The caller passes the frame through summary only. This plot is filled in
    # _plot_all by reading pair ranges stashed on the summary.
    ranges = summary.pop("_multiweek_log_ranges")
    figure, axes = new_figure()
    axes.hist(ranges, bins=40, color=FILL, edgecolor=ACCENT)
    axes.axvline(float(np.log(1.05)), color=INK, linewidth=1)
    axes.set_title("Within UPC-store range of log unit price")
    axes.set_xlabel("Maximum minus minimum log unit price")
    axes.set_ylabel("UPC-store pairs with at least two weeks")
    variation = summary["within_pair_price_variation"]
    _note(
        axes,
        f"n = {variation['pairs_with_at_least_two_weeks']:,} pairs. "
        "The line is log(1.05).",
    )
    save_figure(
        figure,
        figures / "07_within_pair_price_range.png",
        catalog,
        figure_id="07_within_pair_price_range",
        title="Within UPC-store range of log unit price",
        sample=LOG_SAMPLE_NAME,
        n_rows=int(variation["pairs_with_at_least_two_weeks"]),
        units="difference in natural log of dollars per item",
        definition="Pairs with one week are excluded because a range is undefined.",
    )


def _plot_season(summary, figures, catalog) -> None:
    rows = summary["audited"]["mean_move_by_month"]
    figure, axes = new_figure()
    axes.bar(
        [MONTHS[row["month"] - 1] for row in rows],
        [row["mean_move_items"] for row in rows],
        color=FILL,
        edgecolor=ACCENT,
    )
    axes.set_title("Mean recorded item movement by month")
    axes.set_xlabel("Month of the week-start date")
    axes.set_ylabel("Mean items per observed store-UPC-week")
    n_rows = sum(row["rows"] for row in rows)
    _note(axes, f"Audited rows, zeros included. Absent weeks are not rows. n = {n_rows:,}.")
    save_figure(
        figure,
        figures / "08_seasonal_movement.png",
        catalog,
        figure_id="08_seasonal_movement",
        title="Mean recorded item movement by month",
        sample=AUDITED_NAME,
        n_rows=n_rows,
        units="items per observed store-UPC-week",
        definition=(
            "Month is the month of the Thursday that opens the Dominick's week. "
            "The mean gives each observed row equal weight, so a missing year does not "
            "shrink a month's bar by itself."
        ),
    )


def _plot_coverage(summary, figures, catalog) -> None:
    counts = summary.pop("_rows_by_week_series")
    coverage = summary.pop("_upc_coverage")
    figure, axes = new_figure(2)
    axes[0].plot(counts["week"], counts["rows"], color=ACCENT, linewidth=1)
    axes[0].set_title("Rows present by week")
    axes[0].set_xlabel("Week index")
    axes[0].set_ylabel("Audited rows")
    axes[1].hist(coverage, bins=30, color=FILL, edgecolor=ACCENT)
    axes[1].set_title("UPC coverage inside its own span")
    axes[1].set_xlabel("Observed weeks / category weeks in the UPC span")
    axes[1].set_ylabel("UPCs in the log sample")
    save_figure(
        figure,
        figures / "09_panel_coverage.png",
        catalog,
        figure_id="09_panel_coverage",
        title="Panel coverage",
        sample=AUDITED_NAME + "; coverage uses UPCs that appear in the log sample",
        n_rows=int(summary["audited"]["rows"]),
        units="rows; share of category weeks inside each UPC span",
        definition=(
            "The left panel is zero in weeks absent from the file. "
            "The coverage denominator excludes those category-wide missing weeks."
        ),
    )


def _plot_lorenz(frame, figures, catalog, n_rows: int) -> None:
    revenue = (
        frame.groupby("upc", sort=False)["gross_sales"].sum().sort_values().to_numpy(dtype=float)
    )
    share = np.cumsum(revenue) / revenue.sum()
    population = np.arange(1, len(revenue) + 1) / len(revenue)
    figure, axes = new_figure()
    axes.plot(population, share, color=ACCENT)
    axes.plot([0, 1], [0, 1], color=MUTED, linewidth=0.8)
    axes.set_title("Concentration of gross sales across UPCs")
    axes.set_xlabel("Cumulative share of UPCs, from lowest to highest sales")
    axes.set_ylabel("Cumulative share of gross sales")
    _note(axes, f"{len(revenue)} UPCs. Gross sales = PRICE × MOVE / QTY. n = {n_rows:,} rows.")
    save_figure(
        figure,
        figures / "10_revenue_concentration.png",
        catalog,
        figure_id="10_revenue_concentration",
        title="Concentration of gross sales across UPCs",
        sample=LOG_SAMPLE_NAME,
        n_rows=n_rows,
        units="share of UPCs and share of dollars",
        definition="Lorenz curve of UPC totals of PRICE × MOVE / QTY on the log sample.",
    )


def _plot_cross_store(frame, figures, catalog) -> None:
    levels = (
        frame.groupby(["upc", "week"], sort=False)["unit_price"]
        .agg(stores="size", price_min="min", price_max="max")
        .reset_index()
    )
    multi = levels.loc[levels["stores"] >= 10]
    ranges = (multi["price_max"] - multi["price_min"]).to_numpy(dtype=float)
    figure, axes = new_figure()
    cap = float(np.quantile(ranges, 0.99))
    axes.hist(ranges[ranges <= cap], bins=40, color=FILL, edgecolor=ACCENT)
    axes.set_title("Cross-store range of unit price in the same UPC-week")
    axes.set_xlabel("Maximum minus minimum unit price (dollars per item)")
    axes.set_ylabel("UPC-weeks with at least 10 stores")
    _note(axes, f"n = {len(multi):,} UPC-weeks. Bars stop at the 99th percentile, ${cap:.2f}.")
    save_figure(
        figure,
        figures / "11_cross_store_price_range.png",
        catalog,
        figure_id="11_cross_store_price_range",
        title="Cross-store range of unit price in the same UPC-week",
        sample=LOG_SAMPLE_NAME,
        n_rows=int(len(multi)),
        units="dollars per item",
        definition=(
            "A range near zero means the observed stores posted the same unit price that week."
        ),
    )


def _plot_between_products(summary, frame, figures, catalog) -> None:
    products = _upc_table(frame)
    figure, axes = new_figure()
    axes.scatter(
        products["mean_log_price"],
        np.log(products["move"]),
        s=12,
        color=ACCENT,
        alpha=0.8,
    )
    axes.set_title("Product volume and average log unit price")
    axes.set_xlabel("Mean log unit price across the UPC's rows")
    axes.set_ylabel("Natural log of total item movement")
    association = summary["between_upc_price_and_volume"]
    _note(
        axes,
        f"Each point is one UPC (n = {association['rows']}). "
        "This is a between-product comparison.",
    )
    save_figure(
        figure,
        figures / "12_product_volume_and_price.png",
        catalog,
        figure_id="12_product_volume_and_price",
        title="Product volume and average log unit price",
        sample=LOG_SAMPLE_NAME,
        n_rows=int(len(frame)),
        units="natural log of dollars per item; natural log of total items",
        definition="Unweighted mean of log unit price against the log of the UPC's total MOVE.",
    )


def _stash_plot_inputs(
    frame: pd.DataFrame,
    summary: dict[str, object],
    missing_weeks: set[int],
) -> None:
    pairs = (
        frame.groupby(["upc", "store"], sort=False)["log_unit_price"]
        .agg(rows="size", log_min="min", log_max="max")
        .reset_index()
    )
    multi = pairs.loc[pairs["rows"] >= 2]
    summary["_multiweek_log_ranges"] = (multi["log_max"] - multi["log_min"]).to_numpy(dtype=float)
    week_counts = summary["audited"]["rows_by_week"]
    weeks = list(range(1, 400))
    summary["_rows_by_week_series"] = {
        "week": weeks,
        "rows": [int(week_counts.get(str(week), 0)) for week in weeks],
    }
    products = _upc_table(frame)
    summary["_upc_coverage"] = [
        coverage_ratio(int(row.weeks), int(row.first_week), int(row.last_week), missing_weeks)
        for row in products.itertuples(index=False)
    ]


def main() -> None:
    """Write the cereals exploratory summary and figures."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    import argparse

    parser = argparse.ArgumentParser(description="Describe the cereals panel")
    parser.add_argument("--interim-dir", type=Path, default=Path("data/interim"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument(
        "--quality",
        type=Path,
        default=Path("reports/results/data_quality.json"),
    )
    args = parser.parse_args()
    explore(args.interim_dir, args.processed_dir, args.reports_dir, args.quality)


if __name__ == "__main__":
    main()
