"""Synthetic checks of the Kilts manual's accounting identities.

The three SAS-hex fixtures are individual oatmeal movement rows inspected on
5 October 2026 to confirm the decoder. They are not summary statistics.
"""

from decimal import Decimal

import pytest

from pricing_research.economics.accounting import (
    AccountingError,
    average_acquisition_cost_share,
    cogs_cents_per_dollar,
    decode_sas_hex_double,
    gross_profit,
    revenue,
    unit_price,
)


def test_bundle_revenue_matches_manual_identity() -> None:
    # Manual example: a bundle of 3 items priced at $2. MOVE counts items.
    assert unit_price("2", "3") == Decimal("2") / Decimal("3")
    assert revenue("2", "6", "3") == Decimal("4")


def test_zero_movement_has_zero_revenue() -> None:
    assert revenue("1.99", "0", "1") == Decimal("0")


def test_negative_price_is_rejected() -> None:
    with pytest.raises(AccountingError, match="PRICE"):
        unit_price("-1.00", "1")


def test_zero_quantity_is_rejected() -> None:
    with pytest.raises(AccountingError, match="QTY"):
        revenue("2", "6", "0")


def test_negative_movement_is_rejected() -> None:
    with pytest.raises(AccountingError, match="MOVE"):
        revenue("2", "-1", "1")


def test_binary_float_is_rejected() -> None:
    with pytest.raises(AccountingError, match="binary float"):
        unit_price(1.99, "1")


def test_margin_example_from_the_manual() -> None:
    assert cogs_cents_per_dollar("25.3") == Decimal("74.7")
    assert gross_profit("10", "25.3") == Decimal("2.53")
    assert average_acquisition_cost_share("25.3") == Decimal("0.747")


def test_negative_margin_inside_bounds_is_retained() -> None:
    assert gross_profit("10", "-5") == Decimal("-0.5")


def test_margin_outside_percent_bounds_is_rejected() -> None:
    with pytest.raises(AccountingError, match="PROFIT"):
        gross_profit("10", "140")


def test_sas_hex_matches_inspected_oatmeal_rows() -> None:
    assert decode_sas_hex_double("3FFE3D70A3D70A3D") == pytest.approx(1.89)
    assert decode_sas_hex_double("403F7AE147AE147B") == pytest.approx(31.48)
    assert decode_sas_hex_double("403E428F5C28F5C3") == pytest.approx(30.26)


def test_malformed_hex_is_rejected() -> None:
    with pytest.raises(AccountingError):
        decode_sas_hex_double("3FFE")
