"""Build the cereals analysis panel from the local Kilts files.

The command keeps every movement row. The log sample is a flagged subset, and
the cleaning summary reconciles the two counts. A ``--max-rows`` run is a
development extract: it is written beside the official panel and is not the
file behind ``reports/results/data_quality.json``.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import struct
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pricing_research.data.acquire import ensure_category_files, sha256_file
from pricing_research.data.reconcile import waterfall_counts
from pricing_research.data.sources import CategoryFiles, category_files
from pricing_research.data.transform import (
    STORE_CODEBOOK_PATH,
    count_exclusions,
    load_store_codebook,
    load_upc_attributes,
    prepare_movement_frame,
)
from pricing_research.economics.accounting import AccountingError, revenue
from pricing_research.paths import portable_path

LOGGER = logging.getLogger(__name__)
CHUNK_SIZE = 200_000
FORMULA_ABSOLUTE_TOLERANCE = 1e-6


def _movement_reader(path: Path, csv_name: str, max_rows: int | None):
    archive = zipfile.ZipFile(path)
    handle = archive.open(csv_name)
    reader = pd.read_csv(
        handle,
        dtype=str,
        encoding="latin-1",
        chunksize=CHUNK_SIZE,
        keep_default_na=False,
        nrows=max_rows,
    )
    reader._pricing_archive = archive  # type: ignore[attr-defined]
    reader._pricing_handle = handle  # type: ignore[attr-defined]
    return reader


def _close_reader(reader: pd.io.parsers.TextFileReader) -> None:
    handle = getattr(reader, "_pricing_handle", None)
    archive = getattr(reader, "_pricing_archive", None)
    if handle is not None:
        handle.close()
    if archive is not None:
        archive.close()


def _duplicate_keys(
    movement_zip: Path, csv_name: str, max_rows: int | None
) -> set[tuple[str, str, str]]:
    seen_keys: set[tuple[str, str, str]] = set()
    duplicates: set[tuple[str, str, str]] = set()
    reader = _movement_reader(movement_zip, csv_name, max_rows)
    try:
        n_rows = 0
        for chunk in reader:
            for store, upc, week in zip(chunk["STORE"], chunk["UPC"], chunk["WEEK"], strict=True):
                key = (upc.strip(), store.strip(), week.strip())
                if key in seen_keys:
                    duplicates.add(key)
                else:
                    seen_keys.add(key)
            n_rows += len(chunk)
            if n_rows % 1_000_000 == 0:
                LOGGER.info("Keyed %s movement rows", n_rows)
    finally:
        _close_reader(reader)
    return duplicates


def _formula_gap(price: str, move: str, qty: str) -> float | None:
    try:
        expected = float(revenue(price.strip(), move.strip(), qty.strip()))
    except (AccountingError, ValueError):
        return None
    return abs((float(price) * float(move) / float(qty)) - expected)


def build_category(
    raw_dir: Path,
    interim_dir: Path,
    processed_dir: Path,
    reports_dir: Path,
    spec: CategoryFiles,
    max_rows: int | None,
) -> dict[str, object]:
    """Build one category panel and return the quality report."""
    movement_path = raw_dir / spec.movement_zip
    upc_path = raw_dir / spec.upc_csv
    suffix = "" if max_rows is None else "_dev"
    audited_path = interim_dir / f"{spec.name}_movement_audited{suffix}.parquet"
    log_path = processed_dir / f"{spec.name}_log_sample{suffix}.parquet"
    interim_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Finding duplicate keys in %s", movement_path.name)
    duplicates = _duplicate_keys(movement_path, spec.movement_csv, max_rows)
    attributes = load_upc_attributes(upc_path)
    stores = load_store_codebook(STORE_CODEBOOK_PATH)
    if attributes["UPC"].duplicated().any():
        raise RuntimeError(f"{upc_path.name} has duplicate UPC keys.")
    if stores["store_id"].duplicated().any():
        raise RuntimeError("Store codebook has duplicate store ids.")

    writer: pq.ParquetWriter | None = None
    input_rows = 0
    exclusion_counts = count_exclusions(pd.Series(dtype="object"))
    flag_counts: Counter[str] = Counter()
    formula_checks = 0
    formula_failures = 0
    formula_examples: list[dict[str, str]] = []
    hex_gaps = {"price": 0, "profit": 0, "malformed": 0}
    seen_stores: set[str] = set()
    unmatched_store_ids: set[str] = set()
    sorted_input = True
    previous_key: tuple[int, int, int] | None = None
    sale_class_counts: Counter[str] = Counter()
    pair_prices: dict[tuple[int, int], tuple[float, bool]] = {}

    reader = _movement_reader(movement_path, spec.movement_csv, max_rows)
    try:
        for chunk in reader:
            prepared = prepare_movement_frame(chunk, attributes, stores, duplicates)
            input_rows += len(prepared)
            for rule, count in count_exclusions(prepared["log_sample_exclusion"]).items():
                exclusion_counts[rule] += count
            for flag in (
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
            ):
                flag_counts[flag] += int(prepared[flag].sum())
            sale_class_counts.update(prepared["sale_class"].value_counts().to_dict())
            sorted_input, previous_key = _consume_order(
                chunk, sorted_input, previous_key
            )
            formula_checks, formula_failures = _check_formulas(
                chunk,
                input_rows - len(chunk),
                formula_checks,
                formula_failures,
                formula_examples,
            )
            price_gaps, profit_gaps, malformed = _hex_disagreements(chunk)
            hex_gaps["price"] += price_gaps
            hex_gaps["profit"] += profit_gaps
            hex_gaps["malformed"] += malformed
            seen_stores.update(chunk["STORE"].str.strip())
            if bool(prepared["store_unmatched"].any()):
                missing_ids = prepared.loc[prepared["store_unmatched"], "store"]
                unmatched_store_ids.update(missing_ids.dropna().astype(int).astype(str))
            _track_price_variation(prepared, pair_prices)
            table = pa.Table.from_pandas(prepared, preserve_index=False)
            if writer is None:
                audited_path.unlink(missing_ok=True)
                schema = pa.schema(
                    [pa.field(field.name, field.type, nullable=True) for field in table.schema]
                )
                writer = pq.ParquetWriter(audited_path, schema)
            writer.write_table(table.cast(writer.schema))
            if input_rows % 1_000_000 < CHUNK_SIZE:
                LOGGER.info("Wrote %s audited rows", input_rows)
    finally:
        if writer is not None:
            writer.close()
        _close_reader(reader)

    audited_rows = pq.ParquetFile(audited_path).metadata.num_rows
    if audited_rows != input_rows:
        raise RuntimeError(f"Audited panel has {audited_rows} rows; input had {input_rows}.")
    if not sorted_input:
        LOGGER.info("Input was not ordered by UPC, store, and week; sorting the panel")
        _sort_parquet(audited_path)
    log_rows = _write_log_sample(audited_path, log_path, resort=not sorted_input)
    waterfall = waterfall_counts(exclusion_counts, input_rows)
    if waterfall[-1]["rows"] != log_rows:
        raise RuntimeError(
            f"Log-sample reconciliation says {waterfall[-1]['rows']} rows; parquet has {log_rows}."
        )

    varied_pairs = sum(varied for _price, varied in pair_prices.values())
    report: dict[str, object] = {
        "category": spec.name,
        "role": spec.role,
        "full_sample": max_rows is None,
        "development_sample_row_limit": max_rows,
        "do_not_report_development_sample_as_full_sample": max_rows is not None,
        "research_question_changed": False,
        "inputs": [
            _file_record(movement_path, spec.movement_url),
            _file_record(upc_path, spec.upc_url),
            _file_record(
                STORE_CODEBOOK_PATH,
                "Kilts manual Part 6 via the Eurostat dff transcription",
            ),
        ],
        "row_reconciliation": {
            "input_data_rows": input_rows,
            "audited_panel_rows": audited_rows,
            "rows_deleted": audited_rows - input_rows,
            "log_sample_rows": log_rows,
            "sequential_exclusions_plus_log_sample": input_rows,
        },
        "unconditional_flag_rows": dict(flag_counts),
        "sale_class_counts": dict(sale_class_counts),
        "duplicate_keys": len(duplicates),
        "input_sorted_by_upc_store_week": sorted_input,
        "upc_attribute_rows": int(len(attributes)),
        "upc_size_unparsed": int(attributes["size_parse"].eq("unparsed").sum()),
        "store_codebook_rows": int(len(stores)),
        "movement_stores_missing_from_codebook": flag_counts["store_unmatched"],
        "movement_store_ids_missing_from_codebook": sorted(
            unmatched_store_ids, key=int
        ),
        "formula_checks": formula_checks,
        "formula_failures": formula_failures,
        "formula_failure_examples": formula_examples,
        "formula": "gross_sales = PRICE * MOVE / QTY when QTY > 0 and MOVE >= 0",
        "price_hex_abs_diff_above_0_0001": hex_gaps["price"],
        "profit_hex_abs_diff_above_0_0001": hex_gaps["profit"],
        "hex_malformed": hex_gaps["malformed"],
        "movement_store_ids": len(seen_stores),
        "codebook_stores_absent_from_movement": sorted(
            set(stores["store_id"]) - seen_stores
        ),
        "log_sample_pairs": len(pair_prices),
        "log_sample_pairs_with_unit_price_change": varied_pairs,
        "outputs": [
            {"path": str(audited_path), "rows": audited_rows, "sha256": sha256_file(audited_path)},
            {"path": str(log_path), "rows": log_rows, "sha256": sha256_file(log_path)},
        ],
        "absent_records": (
            "UPC-store-weeks that are not in the movement file are not in this panel. "
            "A recorded zero MOVE is a different object and is retained."
        ),
    }
    summary_paths, observed_weeks = _write_summaries(
        audited_path, reports_dir / "tables", spec.name, suffix
    )
    report["summary_tables"] = summary_paths
    expected = range(spec.manual_week_min, spec.manual_week_max + 1)
    report["weeks_observed"] = len(observed_weeks)
    report["weeks_missing_inside_manual_span"] = [
        week for week in expected if week not in observed_weeks
    ]
    _write_reports(reports_dir, spec.name, report, waterfall, max_rows is None)
    if formula_failures:
        raise RuntimeError(f"{formula_failures} revenue identities failed the decimal check.")
    LOGGER.info("Audited %s rows; log sample %s rows", audited_rows, log_rows)
    return report


def _consume_order(
    chunk: pd.DataFrame,
    sorted_input: bool,
    previous_key: tuple[int, int, int] | None,
) -> tuple[bool, tuple[int, int, int] | None]:
    for store, upc, week in zip(chunk["STORE"], chunk["UPC"], chunk["WEEK"], strict=True):
        try:
            key = (int(upc), int(store), int(week))
        except ValueError:
            return False, previous_key
        if previous_key is not None and key < previous_key:
            sorted_input = False
        previous_key = key
    return sorted_input, previous_key


def _check_formulas(
    chunk: pd.DataFrame,
    row_offset: int,
    checks: int,
    failures: int,
    examples: list[dict[str, str]],
) -> tuple[int, int]:
    for position, row in enumerate(chunk.itertuples(index=False)):
        absolute_row = row_offset + position
        qty_text = str(row.QTY).strip()
        if absolute_row % 5000 != 0 and qty_text in {"", "1"}:
            continue
        gap = _formula_gap(str(row.PRICE), str(row.MOVE), qty_text)
        if gap is None:
            continue
        checks += 1
        if gap > FORMULA_ABSOLUTE_TOLERANCE:
            failures += 1
            if len(examples) < 10:
                examples.append(
                    {
                        "row": str(absolute_row),
                        "price": str(row.PRICE),
                        "move": str(row.MOVE),
                        "qty": qty_text,
                        "absolute_gap": str(gap),
                    }
                )
    return checks, failures


def _track_price_variation(
    prepared: pd.DataFrame,
    pair_prices: dict[tuple[int, int], tuple[float, bool]],
) -> None:
    sample = prepared.loc[prepared["in_log_sample"], ["store", "upc", "unit_price"]]
    for store, upc, unit_price in sample.itertuples(index=False):
        key = (int(store), int(upc))
        seen = pair_prices.get(key)
        if seen is None:
            pair_prices[key] = (float(unit_price), False)
        elif not seen[1] and float(unit_price) != seen[0]:
            pair_prices[key] = (seen[0], True)


def _sort_parquet(path: Path) -> None:
    table = pq.read_table(path)
    table = table.sort_by(
        [("upc", "ascending"), ("store", "ascending"), ("week", "ascending")]
    )
    temporary = path.with_suffix(".sorting.parquet")
    pq.write_table(table, temporary)
    temporary.replace(path)


def _hex_disagreements(chunk: pd.DataFrame) -> tuple[int, int, int]:
    price_gaps, price_bad = _column_hex_gaps(chunk["PRICE"], chunk["PRICE_HEX"])
    profit_gaps, profit_bad = _column_hex_gaps(chunk["PROFIT"], chunk["PROFIT_HEX"])
    return price_gaps, profit_gaps, price_bad + profit_bad


def _column_hex_gaps(recorded: pd.Series, hex_text: pd.Series) -> tuple[int, int]:
    tokens = hex_text.fillna("").astype(str).str.strip().str.lower().str.removeprefix("0x")
    usable = tokens.str.fullmatch(r"[0-9a-f]{16}").fillna(False)
    malformed = int((~usable & tokens.ne("")).sum())
    if not bool(usable.any()):
        return 0, malformed
    decoded = np.fromiter(
        (struct.unpack(">d", bytes.fromhex(token))[0] for token in tokens.loc[usable]),
        dtype=float,
        count=int(usable.sum()),
    )
    observed = pd.to_numeric(recorded.loc[usable], errors="coerce").to_numpy(dtype=float)
    disagree = (~np.isfinite(observed)) | (np.abs(decoded - observed) > 1e-4)
    return int(disagree.sum()), malformed


def _write_log_sample(audited_path: Path, log_path: Path, resort: bool) -> int:
    table = pq.read_table(audited_path, filters=[("in_log_sample", "=", True)])
    if resort:
        table = table.sort_by(
            [("upc", "ascending"), ("store", "ascending"), ("week", "ascending")]
        )
    pq.write_table(table, log_path)
    return table.num_rows


def _file_record(path: Path, provenance: str) -> dict[str, object]:
    return {
        "path": portable_path(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "provenance": provenance,
    }


def _write_summaries(
    audited_path: Path, tables: Path, category: str, suffix: str
) -> tuple[list[str], set[int]]:
    """Write product and store coverage tables. These are counts, not a price panel."""
    tables.mkdir(parents=True, exist_ok=True)
    frame = pd.read_parquet(
        audited_path,
        columns=["upc", "store", "week", "in_log_sample", "descrip", "size", "com_code"],
    )
    observed_weeks = set(frame["week"].dropna().astype(int).unique())
    products = (
        frame.groupby(["upc", "com_code", "descrip", "size"], dropna=False)
        .agg(
            movement_rows=("week", "size"),
            log_sample_rows=("in_log_sample", "sum"),
            stores=("store", "nunique"),
            week_min=("week", "min"),
            week_max=("week", "max"),
            weeks_observed=("week", "nunique"),
        )
        .reset_index()
        .sort_values(["upc", "com_code"], kind="mergesort")
    )
    stores = (
        frame.groupby("store", dropna=False)
        .agg(
            movement_rows=("week", "size"),
            log_sample_rows=("in_log_sample", "sum"),
            upcs=("upc", "nunique"),
            week_min=("week", "min"),
            week_max=("week", "max"),
        )
        .reset_index()
        .sort_values(["store"], kind="mergesort")
    )
    product_path = tables / f"{category}_product_summary{suffix}.csv"
    store_path = tables / f"{category}_store_summary{suffix}.csv"
    products.to_csv(product_path, index=False)
    stores.to_csv(store_path, index=False)
    return [str(product_path), str(store_path)], observed_weeks


def _write_reports(
    reports_dir: Path,
    category: str,
    report: dict[str, object],
    waterfall: list[dict[str, int | str]],
    official: bool,
) -> None:
    results = reports_dir / "results"
    tables = reports_dir / "tables"
    results.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    if official and category == "cereals":
        quality_name = "data_quality.json"
        summary_name = "cleaning_summary.csv"
    else:
        quality_name = f"data_quality_{category}.json"
        summary_name = f"cleaning_summary_{category}.csv"
    (results / quality_name).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    input_rows = int(report["row_reconciliation"]["input_data_rows"])  # type: ignore[index]
    with (tables / summary_name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["record_type", "rule", "rows", "rows_remaining", "share_of_input"]
        )
        writer.writeheader()
        for row in waterfall:
            rows = int(row["rows"])
            writer.writerow(
                {
                    **row,
                    "share_of_input": rows / input_rows if input_rows else "",
                }
            )


def main() -> None:
    """Build the selected category panel. Cereals is the default."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Build the Dominick's analysis panel")
    parser.add_argument("--category", default="cereals")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--interim-dir", type=Path, default=Path("data/interim"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()
    spec = category_files(args.category)
    ensure_category_files(args.raw_dir, spec)
    build_category(
        args.raw_dir,
        args.interim_dir,
        args.processed_dir,
        args.reports_dir,
        spec,
        args.max_rows,
    )


if __name__ == "__main__":
    main()
