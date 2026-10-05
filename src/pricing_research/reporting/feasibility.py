"""Phase 1 category profile. Streams a movement CSV and does not estimate demand.

Counts are feasibility facts: file coverage, cleaning defects, promotion codes,
and whether unit price actually moves inside a UPC-store pair. They are not
elasticities.
"""

from __future__ import annotations

import csv
import logging
import math
import struct
import zipfile
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pricing_research.data.calendar import week_bounds

LOGGER = logging.getLogger(__name__)

LOG_SAMPLE_NOTE = (
    "log_sample_rows count OK==1, PRICE>0, QTY>0, and MOVE>0. "
    "The count is a screen, not a fitted sample."
)


@dataclass
class PairState:
    """Running state for one UPC-store pair. Prices are truncated CSV strings."""

    first_price: str
    first_profit: str
    first_qty: str
    n_log_rows: int = 0
    price_varies: bool = False
    profit_varies: bool = False
    qty_varies: bool = False
    sale_coded_rows: int = 0
    min_log_unit_price: float = math.inf
    max_log_unit_price: float = -math.inf


@dataclass
class MovementProfile:
    """Aggregates from one movement file."""

    n_rows: int = 0
    header: list[str] = field(default_factory=list)
    ok_counts: Counter[str] = field(default_factory=Counter)
    sale_counts: Counter[str] = field(default_factory=Counter)
    qty_counts: Counter[str] = field(default_factory=Counter)
    weeks: set[int] = field(default_factory=set)
    stores: set[str] = field(default_factory=set)
    upcs: set[str] = field(default_factory=set)
    duplicate_keys: int = 0
    move_negative: int = 0
    move_zero: int = 0
    move_positive: int = 0
    price_nonpositive: int = 0
    price_zero: int = 0
    price_negative: int = 0
    positive_move_nonpositive_price: int = 0
    price_missing: int = 0
    qty_nonpositive: int = 0
    profit_missing: int = 0
    profit_outside_percent: int = 0
    profit_negative: int = 0
    hex_price_compared: int = 0
    hex_price_absdiff_gt_1e4: int = 0
    hex_price_absdiff_gt_half_cent: int = 0
    hex_profit_compared: int = 0
    hex_profit_absdiff_gt_1e4: int = 0
    hex_profit_absdiff_gt_half_point: int = 0
    log_sample_rows: int = 0
    log_sample_move: float = 0.0
    log_sample_sale_coded_rows: int = 0
    log_sample_sale_coded_move: float = 0.0
    month_move: Counter[int] = field(default_factory=Counter)
    month_rows: Counter[int] = field(default_factory=Counter)
    pairs: dict[tuple[str, str], PairState] = field(default_factory=dict)
    upc_weeks: dict[str, set[int]] = field(default_factory=dict)
    upc_stores: dict[str, set[str]] = field(default_factory=dict)
    _seen_keys: set[tuple[str, str, str]] = field(default_factory=set)
    _week_month: dict[int, int] = field(default_factory=dict)

    def add_row(self, row: dict[str, str]) -> None:
        self.n_rows += 1
        store = row["STORE"].strip()
        upc = row["UPC"].strip()
        week_text = row["WEEK"].strip()
        key = (upc, store, week_text)
        if key in self._seen_keys:
            self.duplicate_keys += 1
        else:
            self._seen_keys.add(key)

        self.stores.add(store)
        self.upcs.add(upc)
        ok = row["OK"].strip()
        self.ok_counts[ok] += 1
        sale = row["SALE"].strip().upper()
        self.sale_counts[sale if sale else "(blank)"] += 1
        qty_text = row["QTY"].strip()
        self.qty_counts[qty_text if qty_text else "(blank)"] += 1

        week = int(week_text)
        self.weeks.add(week)
        self.upc_weeks.setdefault(upc, set()).add(week)
        self.upc_stores.setdefault(upc, set()).add(store)

        move = _float_or_none(row["MOVE"])
        price = _float_or_none(row["PRICE"])
        qty = _float_or_none(row["QTY"])
        profit = _float_or_none(row["PROFIT"])

        if move is None:
            pass
        elif move < 0:
            self.move_negative += 1
        elif move == 0:
            self.move_zero += 1
        else:
            self.move_positive += 1

        if price is None:
            self.price_missing += 1
        elif price < 0:
            self.price_negative += 1
            self.price_nonpositive += 1
        elif price == 0:
            self.price_zero += 1
            self.price_nonpositive += 1
        if move is not None and move > 0 and price is not None and price <= 0:
            self.positive_move_nonpositive_price += 1
        if qty is None or qty <= 0:
            self.qty_nonpositive += 1
        if profit is None:
            self.profit_missing += 1
        else:
            if profit < 0:
                self.profit_negative += 1
            if profit < -100 or profit > 100:
                self.profit_outside_percent += 1

        self._compare_hex(row.get("PRICE", ""), row.get("PRICE_HEX", ""), "price")
        self._compare_hex(row.get("PROFIT", ""), row.get("PROFIT_HEX", ""), "profit")

        usable = (
            ok == "1"
            and move is not None
            and move > 0
            and price is not None
            and price > 0
            and qty is not None
            and qty > 0
        )
        if usable:
            self.log_sample_rows += 1
            self.log_sample_move += move
            coded = sale in {"B", "C", "S"}
            if coded:
                self.log_sample_sale_coded_rows += 1
                self.log_sample_sale_coded_move += move
            month = self._week_month.get(week)
            if month is None:
                month = week_bounds(week)[0].month
                self._week_month[week] = month
            self.month_move[month] += move
            self.month_rows[month] += 1
            self._update_pair(
                upc,
                store,
                row["PRICE"].strip(),
                row["PROFIT"].strip(),
                qty_text,
                price / qty,
                coded,
            )

    def _compare_hex(self, truncated: str, hex_value: str, kind: str) -> None:
        truncated = truncated.strip()
        hex_value = hex_value.strip()
        if not truncated or not hex_value:
            return
        try:
            recorded = float(truncated)
            decoded = struct.unpack(">d", bytes.fromhex(hex_value))[0]
        except ValueError:
            return
        gap = abs(decoded - recorded)
        if kind == "price":
            self.hex_price_compared += 1
            if gap > 1e-4:
                self.hex_price_absdiff_gt_1e4 += 1
            if gap > 0.005:
                self.hex_price_absdiff_gt_half_cent += 1
        else:
            self.hex_profit_compared += 1
            if gap > 1e-4:
                self.hex_profit_absdiff_gt_1e4 += 1
            if gap > 0.005:
                self.hex_profit_absdiff_gt_half_point += 1

    def _update_pair(
        self,
        upc: str,
        store: str,
        price_text: str,
        profit_text: str,
        qty_text: str,
        unit_price: float,
        sale_coded: bool,
    ) -> None:
        key = (upc, store)
        state = self.pairs.get(key)
        if state is None:
            state = PairState(first_price=price_text, first_profit=profit_text, first_qty=qty_text)
            self.pairs[key] = state
        if price_text != state.first_price:
            state.price_varies = True
        if profit_text != state.first_profit:
            state.profit_varies = True
        if qty_text != state.first_qty:
            state.qty_varies = True
        state.n_log_rows += 1
        if sale_coded:
            state.sale_coded_rows += 1
        log_price = math.log(unit_price)
        state.min_log_unit_price = min(state.min_log_unit_price, log_price)
        state.max_log_unit_price = max(state.max_log_unit_price, log_price)


def _float_or_none(value: str) -> float | None:
    text = value.strip()
    if text == "":
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def profile_rows(rows: Iterable[dict[str, str]]) -> MovementProfile:
    """Profile an iterable of movement rows with the official column names."""
    profile = MovementProfile()
    for row in rows:
        profile.add_row(row)
    return profile


def iter_movement_csv(path: Path) -> Iterator[dict[str, str]]:
    """Yield rows from a CSV or from the single CSV inside a zip."""
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != 1:
                raise RuntimeError(f"{path} contains {names}, expected one CSV.")
            with archive.open(names[0]) as handle:
                text = (line.decode("latin-1") for line in handle)
                yield from csv.DictReader(text)
        return
    with path.open(newline="", encoding="latin-1") as handle:
        yield from csv.DictReader(handle)


def summarize_upcs(path: Path) -> dict[str, object]:
    """Summarize a Kilts UPC attribute file."""
    with path.open(newline="", encoding="latin-1") as handle:
        reader = csv.DictReader(handle)
        header = [name.strip() for name in (reader.fieldnames or [])]
        descriptions: Counter[str] = Counter()
        size_kinds: Counter[str] = Counter()
        codes: Counter[str] = Counter()
        upcs: list[str] = []
        for raw in reader:
            row = {key.strip(): (value or "").strip() for key, value in raw.items() if key}
            upcs.append(row["UPC"])
            codes[row["COM_CODE"]] += 1
            desc = row["DESCRIP"]
            if desc.startswith("~"):
                descriptions["tilde_discontinued"] += 1
            elif desc.startswith("#"):
                descriptions["hash_combo_sale_flag"] += 1
            elif desc.startswith("<"):
                descriptions["trial_size_flag"] += 1
            elif desc.startswith("$"):
                descriptions["dollar_prefix_no_manual_meaning"] += 1
            size = row["SIZE"].upper()
            if "OZ" in size or size.endswith("O"):
                size_kinds["ounces_like"] += 1
            elif size in {"ASST", ""}:
                size_kinds["unparsed"] += 1
            else:
                size_kinds["other"] += 1
    return {
        "header": header,
        "n_rows": len(upcs),
        "n_unique_upc": len(set(upcs)),
        "commodity_codes": dict(codes),
        "description_flags": dict(descriptions),
        "size_kinds": dict(size_kinds),
        "upcs": upcs,
    }


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def movement_summary(profile: MovementProfile, attribute_upcs: set[str]) -> dict[str, object]:
    """Collapse a profile into JSON-ready counts. Drops row-level state."""
    pairs = list(profile.pairs.values())
    ranges = [
        state.max_log_unit_price - state.min_log_unit_price
        for state in pairs
        if state.n_log_rows >= 2 and math.isfinite(state.min_log_unit_price)
    ]
    n_pairs = len(pairs)
    n_pairs_price_varies = sum(state.price_varies for state in pairs)
    n_pairs_profit_varies_price_fixed = sum(
        state.profit_varies and not state.price_varies for state in pairs
    )
    n_pairs_qty_varies = sum(state.qty_varies for state in pairs)
    n_pairs_any_sale = sum(state.sale_coded_rows > 0 for state in pairs)

    spans: list[float] = []
    for upc, weeks in profile.upc_weeks.items():
        if upc not in attribute_upcs and attribute_upcs:
            continue
        span = max(weeks) - min(weeks) + 1
        spans.append(len(weeks) / span)
    store_counts = [
        float(len(profile.upc_stores[upc]))
        for upc in profile.upc_weeks
        if not attribute_upcs or upc in attribute_upcs
    ]
    movement_only = sorted(profile.upcs - attribute_upcs) if attribute_upcs else []
    attribute_only = sorted(attribute_upcs - profile.upcs) if attribute_upcs else []

    month_move = {str(month): profile.month_move[month] for month in range(1, 13)}
    positive_months = [
        profile.month_move[month] for month in range(1, 13) if profile.month_move[month] > 0
    ]

    def share(part: int, whole: int) -> float | None:
        if whole == 0:
            return None
        return part / whole

    return {
        "n_rows": profile.n_rows,
        "header": profile.header,
        "n_stores": len(profile.stores),
        "n_upcs_in_movement": len(profile.upcs),
        "n_weeks": len(profile.weeks),
        "min_week": min(profile.weeks) if profile.weeks else None,
        "max_week": max(profile.weeks) if profile.weeks else None,
        "min_week_start": week_bounds(min(profile.weeks))[0].isoformat() if profile.weeks else None,
        "max_week_end": week_bounds(max(profile.weeks))[1].isoformat() if profile.weeks else None,
        "duplicate_upc_store_week_rows": profile.duplicate_keys,
        "ok_counts": dict(profile.ok_counts),
        "sale_counts": dict(profile.sale_counts),
        "qty_value_counts_top": dict(profile.qty_counts.most_common(12)),
        "move_negative": profile.move_negative,
        "move_zero": profile.move_zero,
        "move_positive": profile.move_positive,
        "price_missing": profile.price_missing,
        "price_nonpositive": profile.price_nonpositive,
        "price_zero": profile.price_zero,
        "price_negative": profile.price_negative,
        "positive_move_nonpositive_price": profile.positive_move_nonpositive_price,
        "qty_nonpositive": profile.qty_nonpositive,
        "profit_missing": profile.profit_missing,
        "profit_negative": profile.profit_negative,
        "profit_outside_minus100_to_100": profile.profit_outside_percent,
        "hex_price_compared": profile.hex_price_compared,
        "hex_price_absdiff_gt_0.0001": profile.hex_price_absdiff_gt_1e4,
        "hex_price_absdiff_gt_half_cent": profile.hex_price_absdiff_gt_half_cent,
        "hex_profit_compared": profile.hex_profit_compared,
        "hex_profit_absdiff_gt_0.0001": profile.hex_profit_absdiff_gt_1e4,
        "hex_profit_absdiff_gt_0.005": profile.hex_profit_absdiff_gt_half_point,
        "log_sample_definition": LOG_SAMPLE_NOTE,
        "log_sample_rows": profile.log_sample_rows,
        "log_sample_share_of_rows": share(profile.log_sample_rows, profile.n_rows),
        "log_sample_sale_coded_row_share": share(
            profile.log_sample_sale_coded_rows, profile.log_sample_rows
        ),
        "log_sample_sale_coded_move_share": (
            profile.log_sample_sale_coded_move / profile.log_sample_move
            if profile.log_sample_move
            else None
        ),
        "n_upc_store_pairs_in_log_sample": n_pairs,
        "share_pairs_with_truncated_price_variation": share(n_pairs_price_varies, n_pairs),
        "share_pairs_with_profit_variation_and_fixed_truncated_price": share(
            n_pairs_profit_varies_price_fixed, n_pairs
        ),
        "share_pairs_with_qty_variation": share(n_pairs_qty_varies, n_pairs),
        "share_pairs_with_any_coded_sale": share(n_pairs_any_sale, n_pairs),
        "median_within_pair_log_unit_price_range": _median(ranges),
        "share_pairs_with_log_price_range_at_least_log_1_05": share(
            sum(value >= math.log(1.05) for value in ranges),
            len(ranges),
        ),
        "median_week_coverage_within_upc_span": _median(spans),
        "median_stores_per_attribute_upc_with_movement": _median(store_counts),
        "n_movement_upcs_missing_from_attribute_file": len(movement_only),
        "n_attribute_upcs_missing_from_movement": len(attribute_only),
        "month_move_on_log_sample": month_move,
        "month_move_max_over_min": (
            max(positive_months) / min(positive_months) if positive_months else None
        ),
        "screened_on": date.today().isoformat(),
    }


def profile_category(
    movement_path: Path,
    upc_path: Path,
    expected_week_min: int,
    expected_week_max: int,
) -> dict[str, object]:
    """Read one category's public files and return a feasibility summary."""
    LOGGER.info("Profiling movement %s", movement_path)
    profile = MovementProfile()
    rows = iter_movement_csv(movement_path)
    first = True
    for row in rows:
        if first:
            profile.header = list(row.keys())
            first = False
        profile.add_row(row)
        if profile.n_rows % 1_000_000 == 0:
            LOGGER.info("%s rows from %s", profile.n_rows, movement_path.name)
    attributes = summarize_upcs(upc_path)
    attribute_upcs = set(attributes["upcs"])
    summary = movement_summary(profile, attribute_upcs)
    attributes_public = {key: value for key, value in attributes.items() if key != "upcs"}
    summary["upc_file"] = attributes_public
    summary["movement_path_name"] = movement_path.name
    summary["upc_path_name"] = upc_path.name
    summary["movement_bytes"] = movement_path.stat().st_size
    summary["upc_bytes"] = upc_path.stat().st_size
    missing = sorted(set(range(expected_week_min, expected_week_max + 1)) - profile.weeks)
    summary["expected_week_min"] = expected_week_min
    summary["expected_week_max"] = expected_week_max
    summary["missing_weeks_inside_manual_window"] = missing
    summary["missing_week_spans"] = [
        {
            "week": week,
            "start": week_bounds(week)[0].isoformat(),
            "end": week_bounds(week)[1].isoformat(),
        }
        for week in missing
    ]
    return summary


def main() -> None:
    """Profile the three candidate categories from local Kilts files."""
    import argparse
    import json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Phase 1 movement feasibility profile")
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    categories = {
        "cereals": ("wcer.zip", "upccer.csv", 1, 399),
        "oatmeal": ("woat.zip", "upcoat.csv", 91, 399),
        "canned_soup": ("wcso.zip", "upccso.csv", 1, 399),
    }
    combined: dict[str, object] = {
        "purpose": "Phase 1 feasibility counts. Not elasticities and not a regression sample.",
        "source": "Kilts Center Dominick's CSV files profiled locally. Raw files are gitignored.",
        "categories": {},
    }
    category_payload = combined["categories"]
    assert isinstance(category_payload, dict)
    for name, (movement_name, upc_name, week_min, week_max) in categories.items():
        category_payload[name] = profile_category(
            args.raw_dir / movement_name,
            args.raw_dir / upc_name,
            week_min,
            week_max,
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(combined, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    LOGGER.info("Wrote %s", args.out)


if __name__ == "__main__":
    main()
