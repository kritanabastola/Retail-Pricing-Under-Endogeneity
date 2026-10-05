"""Load saved cereals artifacts and apply the scenario arithmetic.

Numbers shown in the dashboard come from these files. This module does not
refit a regression.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from pricing_research.economics.scenarios import (
    accounting_totals,
    less_favorable_unit_cost,
    prices_inside_support,
    unit_cost_from_profit_percent,
)

ROOT = Path(__file__).resolve().parents[3]
PANEL_COLUMNS = [
    "store",
    "upc",
    "week",
    "move",
    "unit_price",
    "profit",
    "sale_class",
    "promo_coded",
    "descrip",
    "size",
]


class ArtifactError(FileNotFoundError):
    """Raised when a result file is missing or internally inconsistent."""


def project_root() -> Path:
    """Return the repository root that holds ``reports/``."""
    override = os.environ.get("PRICING_RESEARCH_ROOT")
    if override:
        return Path(override)
    return ROOT


def skip_panel() -> bool:
    """Skip the log-sample parquet when a test only needs the result files."""
    return os.environ.get("PRICING_DASHBOARD_SKIP_PANEL") == "1"


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise ArtifactError(f"Missing result file: {path}")
    return json.loads(path.read_text())


def load_quality(root: Path | None = None) -> dict:
    root = project_root() if root is None else root
    return _read_json(root / "reports" / "results" / "data_quality.json")


def load_baseline(root: Path | None = None) -> dict:
    root = project_root() if root is None else root
    return _read_json(root / "reports" / "results" / "baseline_models.json")


def load_audit(root: Path | None = None) -> dict:
    root = project_root() if root is None else root
    return _read_json(root / "reports" / "results" / "identification_audit.json")


def load_scenarios(root: Path | None = None) -> dict:
    root = project_root() if root is None else root
    return _read_json(root / "reports" / "results" / "pricing_scenarios.json")


def load_exploratory(root: Path | None = None) -> dict:
    root = project_root() if root is None else root
    return _read_json(root / "reports" / "results" / "exploratory_summary.json")


def regression_table(root: Path | None = None) -> pd.DataFrame:
    root = project_root() if root is None else root
    path = root / "reports" / "tables" / "baseline_regression.csv"
    if not path.is_file():
        raise ArtifactError(f"Missing result file: {path}")
    return pd.read_csv(path)


def robustness_table(root: Path | None = None) -> pd.DataFrame:
    root = project_root() if root is None else root
    path = root / "reports" / "tables" / "identification_robustness.csv"
    if not path.is_file():
        raise ArtifactError(f"Missing result file: {path}")
    return pd.read_csv(path)


def instrument_table(root: Path | None = None) -> pd.DataFrame:
    root = project_root() if root is None else root
    path = root / "reports" / "tables" / "instrument_evidence.csv"
    if not path.is_file():
        raise ArtifactError(f"Missing result file: {path}")
    return pd.read_csv(path)


def product_table(root: Path | None = None) -> pd.DataFrame:
    root = project_root() if root is None else root
    path = root / "reports" / "tables" / "cereals_product_summary.csv"
    if not path.is_file():
        raise ArtifactError(f"Missing result file: {path}")
    return pd.read_csv(path)


def store_table(root: Path | None = None) -> pd.DataFrame:
    root = project_root() if root is None else root
    path = root / "reports" / "tables" / "cereals_store_summary.csv"
    if not path.is_file():
        raise ArtifactError(f"Missing result file: {path}")
    return pd.read_csv(path)


def price_rows(table: pd.DataFrame) -> pd.DataFrame:
    """Keep log-unit-price rows from the regression table."""
    rows = table.loc[table["term"] == "log_unit_price"].copy()
    if rows.empty:
        raise ArtifactError("The regression table has no log-unit-price rows.")
    return rows


def confirmatory_price(table: pd.DataFrame) -> pd.Series:
    """Return the single M5 price row."""
    rows = table.loc[
        (table["model_id"] == "M5_confirmatory") & (table["term"] == "log_unit_price")
    ]
    if len(rows) != 1:
        raise ArtifactError("The regression table does not have one M5 price coefficient.")
    return rows.iloc[0]


def filter_panel(
    frame: pd.DataFrame,
    *,
    upc: int | None = None,
    store: int | None = None,
    week_min: int | None = None,
    week_max: int | None = None,
) -> pd.DataFrame:
    """Subset a log-sample frame. An empty result is returned, not filled with zeros."""
    out = frame
    if upc is not None:
        out = out.loc[out["upc"].eq(upc)]
    if store is not None:
        out = out.loc[out["store"].eq(store)]
    if week_min is not None:
        out = out.loc[out["week"].ge(week_min)]
    if week_max is not None:
        out = out.loc[out["week"].le(week_max)]
    return out


def weekly_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Sum items and average unit price by week. Empty in, empty out."""
    if frame.empty:
        return pd.DataFrame(columns=["week", "items", "mean_unit_price", "rows", "coded_share"])
    coded = frame["promo_coded"]
    if coded.dtype != np.float64:
        coded = coded.astype(float)
    work = frame.assign(_coded=coded)
    return (
        work.groupby("week", as_index=False)
        .agg(
            items=("move", "sum"),
            mean_unit_price=("unit_price", "mean"),
            rows=("move", "size"),
            coded_share=("_coded", "mean"),
        )
        .sort_values("week")
    )


def shelf_snapshot(frame: pd.DataFrame) -> dict[str, float | int] | None:
    """Median store-week price, movement, and margin. None when the frame is empty."""
    if frame.empty:
        return None
    price = frame["unit_price"].to_numpy(dtype=np.float64)
    return {
        "rows": int(len(frame)),
        "stores": int(frame["store"].nunique()),
        "weeks": int(frame["week"].nunique()),
        "median_unit_price": float(np.median(price)),
        "min_unit_price": float(np.min(price)),
        "max_unit_price": float(np.max(price)),
        "median_items": float(np.median(frame["move"].to_numpy(dtype=np.float64))),
        "median_profit_percent": float(np.median(frame["profit"].to_numpy(dtype=np.float64))),
    }


def one_shelf_scenario(
    *,
    quantity: float,
    unit_price: float,
    profit_percent: float,
    price_ratio: float,
    elasticity: float,
    less_favorable: bool,
    price_min: float,
    price_max: float,
) -> dict[str, object]:
    """Hypothetical accounting for one median store-week.

    The quantity is a median store-week, not chain revenue. ``inside_history``
    is false when the candidate price leaves the observed min–max of the
    selected rows.
    """
    price = np.array([unit_price], dtype=np.float64)
    profit = np.array([profit_percent], dtype=np.float64)
    if less_favorable:
        cost, _capped = less_favorable_unit_cost(price, profit)
        cost_label = "margin 10 points less favorable than the median recorded margin"
    else:
        cost = unit_cost_from_profit_percent(price, profit)
        cost_label = "median recorded average-acquisition-cost margin, held constant"
    totals = accounting_totals(
        np.array([quantity], dtype=np.float64),
        price,
        cost,
        price_ratio,
        elasticity,
    )
    candidate = unit_price * price_ratio
    inside = bool(
        prices_inside_support(price, np.array([price_min]), np.array([price_max]), price_ratio)[0]
    )
    return {
        "cost_label": cost_label,
        "unit_cost": float(cost[0]),
        "candidate_price": float(candidate),
        "inside_history": inside,
        "causal": False,
        "quantity_unit": "items per median store-week",
        "money_unit": "dollars per median store-week",
        **totals,
    }


def specification_band(
    scenarios: dict,
    price_ratio: float,
    case_ids: tuple[str, ...] = (
        "low_sensitivity_pooled_association",
        "central_confirmatory_association",
        "assumed_unit",
        "high_sensitivity_assumed",
    ),
) -> dict[str, float]:
    """Revenue-change range across stated elasticities. Not a confidence interval."""
    by_id = {row["case_id"]: float(row["elasticity"]) for row in scenarios["elasticity_cases"]}
    changes = [price_ratio ** (1.0 + by_id[case_id]) - 1.0 for case_id in case_ids]
    return {
        "low": float(min(changes)),
        "high": float(max(changes)),
        "note": "Range across stated elasticities. Not a confidence interval.",
    }


def sampling_revenue_band(price_row: pd.Series, price_ratio: float) -> dict[str, float]:
    """Map the store-cluster interval for M5 through the revenue formula."""
    low = float(price_row["ci95_low"])
    high = float(price_row["ci95_high"])
    return {
        "elasticity_low": low,
        "elasticity_high": high,
        "revenue_change_at_low": float(price_ratio ** (1.0 + low) - 1.0),
        "revenue_change_at_high": float(price_ratio ** (1.0 + high) - 1.0),
        "note": (
            "Store-clustered sampling interval for the confirmatory association. "
            "Not a confidence interval for a causal elasticity."
        ),
    }


def consistency_checks(root: Path | None = None) -> list[dict[str, object]]:
    """Compare the result files with one another. A failure is a file conflict."""
    root = project_root() if root is None else root
    table = regression_table(root)
    price = confirmatory_price(table)
    baseline = load_baseline(root)
    audit = load_audit(root)
    scenarios = load_scenarios(root)
    quality = load_quality(root)
    hypothesis = baseline["hypotheses"]["h1_negative_confirmatory_slope"]["estimate"]
    central = next(
        row["elasticity"]
        for row in scenarios["elasticity_cases"]
        if row["case_id"] == "central_confirmatory_association"
    )
    instruments = instrument_table(root)
    checks = [
        _check("baseline causal flag is false", baseline.get("causal_claim") is False),
        _check("audit branch is B", audit.get("branch") == "B"),
        _check("audit causal flag is false", audit.get("causal_claim") is False),
        _check("no 2SLS on scanner rows", audit.get("iv_estimated_on_kilts_rows") is False),
        _check("scenario causal flag is false", scenarios.get("causal_claim") is False),
        _check("no equilibrium price", scenarios.get("equilibrium_prices_computed") is False),
        _check("deployment is unsupported", scenarios["decision"]["deployment_supported"] is False),
        _check(
            "M5 matches the baseline hypothesis file",
            abs(float(price["estimate"]) - float(hypothesis)) < 1e-9,
        ),
        _check(
            "scenario elasticity matches M5",
            abs(float(central) - float(price["estimate"])) < 1e-9,
        ),
        _check(
            "log-sample row count matches the regression table",
            int(price["n"]) == int(quality["row_reconciliation"]["log_sample_rows"]),
        ),
        _check(
            "no instrument is approved",
            set(instruments["verdict"].astype(str)) == {"REJECTED"},
        ),
        _check("M5 is not marked causal in the table", str(price["causal_claim"]) == "False"),
    ]
    return checks


def _check(name: str, passed: bool) -> dict[str, object]:
    return {"check": name, "passed": passed}


def panel_path(root: Path | None = None) -> Path:
    root = project_root() if root is None else root
    return root / "data" / "processed" / "cereals_log_sample.parquet"


def read_panel(root: Path | None = None) -> pd.DataFrame | None:
    """Read the log sample, or return None when the file is absent or skipped."""
    if skip_panel():
        return None
    path = panel_path(root)
    if not path.is_file():
        return None
    return pd.read_parquet(path, columns=PANEL_COLUMNS)
