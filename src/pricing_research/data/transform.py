"""Derived columns for one movement chunk.

Observed fields keep their recorded values. Derived fields are null when the
manual's identity does not apply. This function does not drop rows.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd

from pricing_research.data.calendar import week_bounds
from pricing_research.data.reconcile import EXCLUSION_ORDER
from pricing_research.validation.schema import classify_sale_code

STORE_CODEBOOK_PATH = Path(__file__).resolve().parent / "resources" / "store_codebook.csv"

OUTPUT_COLUMNS: tuple[str, ...] = (
    "store",
    "upc",
    "week",
    "move",
    "qty",
    "price",
    "sale",
    "profit",
    "ok",
    "price_hex",
    "profit_hex",
    "com_code",
    "descrip",
    "size",
    "nitem",
    "size_oz",
    "size_parse",
    "price_tier",
    "zone",
    "city",
    "unit_price",
    "unit_volume_items",
    "gross_sales",
    "margin_rate",
    "gross_profit_proxy",
    "price_per_oz",
    "sale_class",
    "promo_coded",
    "week_start",
    "week_end",
    "year",
    "month",
    "quarter",
    "log_move",
    "log_unit_price",
    "duplicate_upc_store_week",
    "ok_not_one",
    "price_not_positive",
    "qty_not_positive",
    "move_not_positive",
    "move_negative",
    "week_outside_published_calendar",
    "margin_out_of_bounds",
    "sale_unclassified",
    "upc_unmatched",
    "store_unmatched",
    "in_log_sample",
    "log_sample_exclusion",
)


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def prepare_movement_frame(
    movement: pd.DataFrame,
    upc_attributes: pd.DataFrame,
    stores: pd.DataFrame,
    duplicate_keys: set[tuple[str, str, str]],
) -> pd.DataFrame:
    """Attach attributes and derived fields. One output row per input row."""
    frame = movement.copy().reset_index(drop=True)
    frame.columns = [column.strip().lower() for column in frame.columns]
    for column in ("store", "upc", "week", "sale", "ok", "price_hex", "profit_hex"):
        frame[column] = frame[column].fillna("").astype(str).str.strip()

    move = _numeric(frame["move"])
    qty = _numeric(frame["qty"])
    price = _numeric(frame["price"])
    profit = _numeric(frame["profit"])
    week_number = pd.to_numeric(frame["week"], errors="coerce")

    attributes = upc_attributes.rename(
        columns={
            "COM_CODE": "com_code",
            "UPC": "upc",
            "DESCRIP": "descrip",
            "SIZE": "size",
            "NITEM": "nitem",
        }
    )
    keep_attr = ["upc", "com_code", "descrip", "size", "nitem", "size_oz", "size_parse"]
    merged = frame.merge(attributes[keep_attr], on="upc", how="left", indicator="upc_join")
    store_keep = stores.rename(columns={"store_id": "store"})[
        ["store", "price_tier", "zone", "city"]
    ]
    merged = merged.merge(store_keep, on="store", how="left", indicator="store_join")

    keys = list(zip(merged["upc"], merged["store"], merged["week"], strict=True))
    duplicate = np.fromiter((key in duplicate_keys for key in keys), dtype=bool, count=len(keys))
    ok_not_one = merged["ok"].ne("1").to_numpy()
    price_not_positive = ~(price.gt(0).fillna(False).to_numpy())
    qty_not_positive = ~(qty.gt(0).fillna(False).to_numpy())
    move_not_positive = ~(move.gt(0).fillna(False).to_numpy())
    move_negative = move.lt(0).fillna(False).to_numpy()
    week_ok = week_number.ge(1) & week_number.le(400) & week_number.notna()
    week_outside = ~week_ok.to_numpy()
    margin_out = (profit.lt(-100) | profit.gt(100) | profit.isna()).to_numpy()
    sale_class = merged["sale"].map(
        lambda value: classify_sale_code(value if value != "" else None)
    )
    sale_unclassified = sale_class.eq("unclassified").to_numpy()
    upc_unmatched = merged["upc_join"].eq("left_only").to_numpy()
    store_unmatched = merged["store_join"].eq("left_only").to_numpy()

    unit_price = price / qty
    unit_price = unit_price.where(price.gt(0) & qty.gt(0))
    unit_volume = move.where(move.ge(0))
    gross_sales = (price * move / qty).where(qty.gt(0) & move.ge(0) & price.notna())
    margin_rate = (profit / 100).where(profit.ge(-100) & profit.le(100))
    gross_profit = (gross_sales * margin_rate).where(gross_sales.notna() & margin_rate.notna())
    price_per_oz = (unit_price / merged["size_oz"]).where(
        merged["size_oz"].gt(0) & unit_price.notna()
    )

    week_start, week_end, year, month, quarter = _calendar_columns(week_number)
    exclusion_flags = {
        "duplicate_upc_store_week": duplicate,
        "ok_not_one": ok_not_one,
        "price_not_positive": price_not_positive,
        "qty_not_positive": qty_not_positive,
        "move_not_positive": move_not_positive,
        "week_outside_published_calendar": week_outside,
    }
    exclusions = pd.Series(pd.NA, index=merged.index, dtype="object")
    for rule in EXCLUSION_ORDER:
        hit = pd.Series(exclusion_flags[rule], index=merged.index)
        exclusions = exclusions.mask(hit & exclusions.isna(), rule)
    in_log_sample = exclusions.isna().to_numpy()
    log_move = np.log(move.where(in_log_sample))
    log_unit_price = np.log(unit_price.where(in_log_sample))

    prepared = pd.DataFrame(
        {
            "store": pd.to_numeric(merged["store"], errors="coerce").astype("Int32"),
            "upc": pd.to_numeric(merged["upc"], errors="coerce").astype("Int64"),
            "week": week_number.astype("Int16"),
            "move": move,
            "qty": qty,
            "price": price,
            "sale": merged["sale"].replace({"": pd.NA}),
            "profit": profit,
            "ok": pd.to_numeric(merged["ok"], errors="coerce").astype("Int8"),
            "price_hex": merged["price_hex"].replace({"": pd.NA}),
            "profit_hex": merged["profit_hex"].replace({"": pd.NA}),
            "com_code": merged["com_code"],
            "descrip": merged["descrip"],
            "size": merged["size"],
            "nitem": merged["nitem"],
            "size_oz": merged["size_oz"],
            "size_parse": merged["size_parse"],
            "price_tier": merged["price_tier"].replace({"": pd.NA}),
            "zone": merged["zone"].replace({"": pd.NA}),
            "city": merged["city"].replace({"": pd.NA}),
            "unit_price": unit_price,
            "unit_volume_items": unit_volume,
            "gross_sales": gross_sales,
            "margin_rate": margin_rate,
            "gross_profit_proxy": gross_profit,
            "price_per_oz": price_per_oz,
            "sale_class": sale_class,
            "promo_coded": sale_class.eq("coded"),
            "week_start": week_start,
            "week_end": week_end,
            "year": year,
            "month": month,
            "quarter": quarter,
            "log_move": log_move,
            "log_unit_price": log_unit_price,
            "duplicate_upc_store_week": duplicate,
            "ok_not_one": ok_not_one,
            "price_not_positive": price_not_positive,
            "qty_not_positive": qty_not_positive,
            "move_not_positive": move_not_positive,
            "move_negative": move_negative,
            "week_outside_published_calendar": week_outside,
            "margin_out_of_bounds": margin_out,
            "sale_unclassified": sale_unclassified,
            "upc_unmatched": upc_unmatched,
            "store_unmatched": store_unmatched,
            "in_log_sample": in_log_sample,
            "log_sample_exclusion": exclusions,
        }
    )
    prepared["log_sample_exclusion"] = prepared["log_sample_exclusion"].replace({None: pd.NA})
    return prepared[list(OUTPUT_COLUMNS)]


def _calendar_columns(
    week_number: pd.Series,
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    starts: list[object] = []
    ends: list[object] = []
    years: list[float] = []
    months: list[float] = []
    quarters: list[float] = []
    cache: dict[int, tuple[object, object, int, int, int]] = {}
    for value in week_number:
        if pd.isna(value):
            starts.append(pd.NaT)
            ends.append(pd.NaT)
            years.append(np.nan)
            months.append(np.nan)
            quarters.append(np.nan)
            continue
        week = int(value)
        if week not in cache:
            if week < 1 or week > 400:
                cache[week] = (pd.NaT, pd.NaT, np.nan, np.nan, np.nan)
            else:
                start, end = week_bounds(week)
                cache[week] = (start, end, start.year, start.month, (start.month - 1) // 3 + 1)
        start, end, year, month, quarter = cache[week]
        starts.append(start)
        ends.append(end)
        years.append(year)
        months.append(month)
        quarters.append(quarter)
    return (
        pd.to_datetime(pd.Series(starts, index=week_number.index)),
        pd.to_datetime(pd.Series(ends, index=week_number.index)),
        pd.Series(years, index=week_number.index, dtype="Float64"),
        pd.Series(months, index=week_number.index, dtype="Float64"),
        pd.Series(quarters, index=week_number.index, dtype="Float64"),
    )


def count_exclusions(exclusions: pd.Series) -> dict[str, int]:
    """Count first-reason exclusions, including zeros for rules that never hit."""
    counts = {rule: 0 for rule in EXCLUSION_ORDER}
    observed = exclusions.dropna().value_counts()
    for rule, count in observed.items():
        counts[str(rule)] = int(count)
    return counts


def load_upc_attributes(path: str | pd.PathLike[str] | object) -> pd.DataFrame:
    """Read a UPC file and attach the size parse. ``path`` is a filesystem path."""
    from pathlib import Path

    from pricing_research.data.size_parse import parse_package_ounces

    frame = pd.read_csv(Path(str(path)), dtype=str, encoding="latin-1")
    frame.columns = [column.strip() for column in frame.columns]
    parsed = frame["SIZE"].map(lambda value: parse_package_ounces(value))
    frame["size_oz"] = [item[0] for item in parsed]
    frame["size_parse"] = [item[1] for item in parsed]
    frame["UPC"] = frame["UPC"].str.strip()
    return frame


def load_store_codebook(path: str | pd.PathLike[str] | None = None) -> pd.DataFrame:
    """Read the store transcription. Blank tier and zone stay blank."""
    frame = pd.read_csv(Path(path or STORE_CODEBOOK_PATH), dtype=str, keep_default_na=False)
    frame["store_id"] = frame["store_id"].str.strip()
    return frame


def duplicate_key_set(keys: Mapping[tuple[str, str, str], int]) -> set[tuple[str, str, str]]:
    """Return keys whose row count is greater than one."""
    return {key for key, count in keys.items() if count > 1}
