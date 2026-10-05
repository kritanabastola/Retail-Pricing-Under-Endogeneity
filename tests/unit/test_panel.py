"""Pipeline rules on synthetic rows and the store codebook. No Kilts extract is loaded."""

from decimal import Decimal

import pandas as pd

from pricing_research.data.reconcile import waterfall_counts
from pricing_research.data.size_parse import parse_package_ounces
from pricing_research.data.transform import (
    STORE_CODEBOOK_PATH,
    duplicate_key_set,
    prepare_movement_frame,
)
from pricing_research.economics.accounting import revenue


def test_package_ounces_do_not_invent_units() -> None:
    assert parse_package_ounces("15 OZ") == (15.0, "ounces")
    assert parse_package_ounces("13.5OZ") == (13.5, "ounces")
    assert parse_package_ounces("15.5 O") == (15.5, "ounces")
    assert parse_package_ounces("19.25Z") == (19.25, "trailing_z")
    assert parse_package_ounces("17.4 Z") == (17.4, "trailing_z")
    assert parse_package_ounces("12.75")[0] is None
    assert parse_package_ounces("ASST")[0] is None
    assert parse_package_ounces("1 CT")[0] is None
    assert parse_package_ounces("2/20 O")[0] is None


def test_duplicate_keys_and_waterfall_reconcile() -> None:
    keys = {("1", "2", "3"): 1, ("1", "2", "4"): 2}
    assert duplicate_key_set(keys) == {("1", "2", "4")}
    hits = {
        "duplicate_upc_store_week": 2,
        "ok_not_one": 1,
        "price_not_positive": 3,
        "qty_not_positive": 0,
        "move_not_positive": 4,
        "week_outside_published_calendar": 0,
    }
    rows = waterfall_counts(hits, 20)
    assert rows[0]["rows"] == 20
    assert rows[-1]["rows"] == 10
    excluded = sum(
        int(row["rows"]) for row in rows if row["record_type"] == "sequential_exclusion"
    )
    assert excluded == 10


def test_store_codebook_matches_manual_rows() -> None:
    stores = pd.read_csv(STORE_CODEBOOK_PATH, dtype=str, keep_default_na=False)
    store_2 = stores.loc[stores["store_id"] == "2"].iloc[0]
    assert store_2["city"] == "River Forest"
    assert store_2["price_tier"] == "High"
    assert store_2["zone"] == "1"
    store_21 = stores.loc[stores["store_id"] == "21"].iloc[0]
    assert store_21["price_tier"] == "CubFighter"


def test_transform_keeps_invalid_rows_and_matches_revenue_identity() -> None:
    movement = pd.DataFrame(
        [
            {
                "STORE": "2",
                "UPC": "111",
                "WEEK": "1",
                "MOVE": "6",
                "QTY": "3",
                "PRICE": "2",
                "SALE": "B",
                "PROFIT": "25.3",
                "OK": "1",
                "PRICE_HEX": "",
                "PROFIT_HEX": "",
            },
            {
                "STORE": "2",
                "UPC": "111",
                "WEEK": "1",
                "MOVE": "6",
                "QTY": "3",
                "PRICE": "2",
                "SALE": "",
                "PROFIT": "25.3",
                "OK": "1",
                "PRICE_HEX": "",
                "PROFIT_HEX": "",
            },
            {
                "STORE": "8",
                "UPC": "222",
                "WEEK": "2",
                "MOVE": "0",
                "QTY": "1",
                "PRICE": "0",
                "SALE": "G",
                "PROFIT": "10",
                "OK": "0",
                "PRICE_HEX": "",
                "PROFIT_HEX": "",
            },
            {
                "STORE": "99",
                "UPC": "999",
                "WEEK": "1",
                "MOVE": "abc",
                "QTY": "1",
                "PRICE": "",
                "SALE": "",
                "PROFIT": "250",
                "OK": "1",
                "PRICE_HEX": "",
                "PROFIT_HEX": "",
            },
        ]
    )
    attributes = pd.DataFrame(
        {
            "UPC": ["111", "222"],
            "COM_CODE": ["311", "311"],
            "DESCRIP": ["BRAND", "OTHER"],
            "SIZE": ["15 OZ", "ASST"],
            "NITEM": ["1", "2"],
            "size_oz": [15.0, None],
            "size_parse": ["ounces", "unparsed"],
        }
    )
    stores = pd.DataFrame(
        {
            "store_id": ["2", "8"],
            "city": ["River Forest", "Oak Lawn"],
            "price_tier": ["High", "Low"],
            "zone": ["1", "5"],
        }
    )
    prepared = prepare_movement_frame(movement, attributes, stores, {("111", "2", "1")})
    assert len(prepared) == 4
    assert prepared["in_log_sample"].sum() == 0
    assert prepared.loc[0, "duplicate_upc_store_week"]
    assert prepared.loc[0, "gross_sales"] == 4
    assert prepared.loc[0, "unit_price"] == 2 / 3
    expected_profit = float(Decimal("4") * Decimal("25.3") / Decimal("100"))
    assert float(prepared.loc[0, "gross_profit_proxy"]) == expected_profit
    assert prepared.loc[0, "week_start"].date().isoformat() == "1989-09-14"
    assert prepared.loc[0, "promo_coded"]
    assert prepared.loc[2, "sale_class"] == "unclassified"
    assert prepared.loc[2, "unit_volume_items"] == 0
    assert pd.isna(prepared.loc[2, "unit_price"])
    assert prepared.loc[3, "upc_unmatched"]
    assert prepared.loc[3, "store_unmatched"]
    assert prepared.loc[3, "margin_out_of_bounds"]
    assert pd.isna(prepared.loc[3, "move"])
    assert float(prepared.loc[0, "gross_sales"]) == float(revenue("2", "6", "3"))
    again = prepare_movement_frame(movement, attributes, stores, {("111", "2", "1")})
    pd.testing.assert_frame_equal(prepared, again)


def test_build_reconciles_every_synthetic_row(tmp_path) -> None:
    import zipfile

    from pricing_research.data.build import build_category
    from pricing_research.data.sources import CategoryFiles

    raw = tmp_path / "raw"
    raw.mkdir()
    header = "STORE,UPC,WEEK,MOVE,QTY,PRICE,SALE,PROFIT,OK,PRICE_HEX,PROFIT_HEX\n"
    body = (
        "2,111,1,6,3,2,B,25.3,1,,\n"
        "2,111,2,0,1,0,,10,1,,\n"
        "8,111,1,4,1,1.5,,-5,1,,\n"
    )
    with zipfile.ZipFile(raw / "wcer.zip", "w") as archive:
        archive.writestr("wcer.csv", header + body)
    (raw / "upccer.csv").write_text(
        "COM_CODE,UPC,DESCRIP,SIZE,CASE,NITEM\n311,111,BRAND,15 OZ,1,1\n",
        encoding="latin-1",
    )
    spec = CategoryFiles(
        name="cereals",
        movement_zip="wcer.zip",
        movement_csv="wcer.csv",
        upc_csv="upccer.csv",
        movement_url="synthetic",
        upc_url="synthetic",
        manual_week_min=1,
        manual_week_max=399,
        role="test panel",
    )
    reports = tmp_path / "reports"
    first = build_category(raw, tmp_path / "interim", tmp_path / "processed", reports, spec, None)
    second = build_category(raw, tmp_path / "interim", tmp_path / "processed", reports, spec, None)
    assert first["row_reconciliation"]["input_data_rows"] == 3
    assert first["row_reconciliation"]["audited_panel_rows"] == 3
    assert first["row_reconciliation"]["rows_deleted"] == 0
    assert first["row_reconciliation"]["log_sample_rows"] == 2
    assert first["outputs"][0]["sha256"] == second["outputs"][0]["sha256"]
    summary = (reports / "tables" / "cleaning_summary.csv").read_text(encoding="utf-8")
    assert "log_sample" in summary
    quality = (reports / "results" / "data_quality.json").read_text(encoding="utf-8")
    assert '"rows_deleted": 0' in quality

