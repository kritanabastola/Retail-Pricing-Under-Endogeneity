"""Schema, promotion-code, duplicate, and merge audits. No scanner extract is loaded."""

import pytest

from pricing_research.economics.accounting import AccountingError
from pricing_research.validation.schema import (
    MOVEMENT_COLUMNS,
    UPC_COLUMNS,
    audit_upc_coverage,
    duplicate_upc_store_weeks,
    require_columns,
    sale_code_is_set,
)


def test_observed_oatmeal_header_passes() -> None:
    header = [
        "STORE",
        "UPC",
        "WEEK",
        "MOVE",
        "QTY",
        "PRICE",
        "SALE",
        "PROFIT",
        "OK",
        "PRICE_HEX",
        "PROFIT_HEX",
    ]
    require_columns(header, MOVEMENT_COLUMNS, "movement")


def test_missing_column_is_an_error() -> None:
    with pytest.raises(AccountingError, match="PRICE_HEX"):
        require_columns(["STORE", "UPC", "PRICE"], MOVEMENT_COLUMNS, "movement")


def test_upc_attribute_columns() -> None:
    require_columns(
        ["COM_CODE", "UPC", "DESCRIP", "SIZE", "CASE", "NITEM"],
        UPC_COLUMNS,
        "UPC",
    )


@pytest.mark.parametrize("code", ["B", "c", " S "])
def test_documented_promotion_codes(code: str) -> None:
    assert sale_code_is_set(code) is True


def test_blank_sale_code_is_not_a_confirmed_regular_price() -> None:
    assert sale_code_is_set("") is False
    assert sale_code_is_set(None) is False


def test_unknown_sale_code_is_rejected() -> None:
    with pytest.raises(AccountingError, match="SALE"):
        sale_code_is_set("X")


def test_unclassified_codes_are_neither_promotions_nor_blank() -> None:
    from pricing_research.validation.schema import classify_sale_code

    assert classify_sale_code("G") == "unclassified"
    assert classify_sale_code("L") == "unclassified"
    assert classify_sale_code("B") == "coded"
    assert classify_sale_code("") == "blank"


def test_duplicate_keys_are_reported_and_not_removed() -> None:
    keys = [(10, 2, 91), (10, 2, 92), (10, 2, 91)]
    assert duplicate_upc_store_weeks(keys) == ((10, 2, 91),)


def test_unmatched_movement_upc_is_listed() -> None:
    audit = audit_upc_coverage([111, 222, 111], [111])
    assert audit["n_movement_upcs"] == 2
    assert audit["n_unmatched_movement_upcs"] == 1
    assert audit["unmatched_movement_upcs"] == (222,)
