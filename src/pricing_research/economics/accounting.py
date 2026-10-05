"""Dominick's scanner accounting identities.

The formulas follow Part 4 of the Kilts Center Dominick's Data Manual
(created July 2013, updated October 2018). They convert recorded fields
into unit price, revenue, and an accounting gross-profit measure.

Nothing in this module is a demand estimate, a marginal cost, or an
instrument.
"""

from __future__ import annotations

import struct
from decimal import Decimal, InvalidOperation

Number = Decimal | int | str


class AccountingError(ValueError):
    """Raised when a manual-defined accounting input is unusable."""


def _decimal(value: Number, name: str) -> Decimal:
    """Parse a recorded number without accepting a binary float."""
    if isinstance(value, float):
        raise AccountingError(
            f"{name} must be a Decimal, int, or recorded decimal string, not a binary float."
        )
    try:
        parsed = Decimal(value) if isinstance(value, str) else Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise AccountingError(f"{name} is not a number: {value!r}") from exc
    if not parsed.is_finite():
        raise AccountingError(f"{name} must be finite.")
    return parsed


def unit_price(price: Number, qty: Number) -> Decimal:
    """Return the per-item price ``PRICE / QTY``.

    The manual's bundle example treats ``PRICE`` as the total price of the
    bundle and ``QTY`` as the number of items in that bundle. ``MOVE`` counts
    items sold, not bundles.
    """
    recorded_price = _decimal(price, "PRICE")
    bundle_size = _decimal(qty, "QTY")
    if recorded_price <= 0:
        raise AccountingError("PRICE must be positive to define a unit price.")
    if bundle_size <= 0:
        raise AccountingError("QTY must be positive to define a unit price.")
    return recorded_price / bundle_size


def revenue(price: Number, move: Number, qty: Number) -> Decimal:
    """Return dollar sales ``PRICE * MOVE / QTY``.

    ``MOVE`` may be zero: a recorded zero-movement row has zero sales. Negative
    movement is rejected. This function does not invent rows for weeks that
    are absent from the movement file.
    """
    item_movement = _decimal(move, "MOVE")
    if item_movement < 0:
        raise AccountingError("MOVE cannot be negative.")
    return unit_price(price, qty) * item_movement


def _margin_rate(profit_percent: Number) -> Decimal:
    """Convert the manual's cents-per-dollar margin into a revenue share.

    A value of 25.3 means 25.3 cents of gross margin per dollar of sales.
    Values outside [-100, 100] are rejected because they cannot be read as a
    percent of sales. Negative values inside that range are retained: the
    manual does not forbid loss-leader margins, and Hoch, Drèze, and Purk
    (1994) describe canned soup as having been priced as a loss leader.
    """
    percent = _decimal(profit_percent, "PROFIT")
    if percent < Decimal("-100") or percent > Decimal("100"):
        raise AccountingError("PROFIT percent must lie between -100 and 100.")
    return percent / Decimal("100")


def gross_profit(sales: Number, profit_percent: Number) -> Decimal:
    """Return accounting gross profit ``sales * PROFIT / 100``.

    This uses Dominick's reported gross margin on the sale. The manual states
    that the underlying wholesale cost is average acquisition cost of inventory,
    not replacement cost and not the marginal cost of an economist's pricing
    problem.
    """
    recorded_sales = _decimal(sales, "sales")
    if recorded_sales < 0:
        raise AccountingError("Sales cannot be negative in the gross-profit identity.")
    return recorded_sales * _margin_rate(profit_percent)


def cogs_cents_per_dollar(profit_percent: Number) -> Decimal:
    """Return cost-of-goods cents per dollar of sales, ``100 - PROFIT``.

    The manual's example maps a profit value of 25.3 into a cost of goods of
    74.7 cents on the dollar.
    """
    percent = _decimal(profit_percent, "PROFIT")
    if percent < Decimal("-100") or percent > Decimal("100"):
        raise AccountingError("PROFIT percent must lie between -100 and 100.")
    return Decimal("100") - percent


def average_acquisition_cost_share(profit_percent: Number) -> Decimal:
    """Return ``1 - PROFIT/100``, the accounting cost share of sales.

    Label this share as an average-acquisition-cost construct when it is used.
    Do not treat it as marginal cost, and do not treat it as an instrument
    without a separate identification argument.
    """
    return Decimal("1") - _margin_rate(profit_percent)


def decode_sas_hex_double(hex_value: str) -> float:
    """Decode ``PRICE_HEX`` or ``PROFIT_HEX`` as a big-endian IEEE-754 double.

    The Kilts CSV note says these fields preserve the SAS binary values, while
    ``PRICE`` and ``PROFIT`` are truncated. Estimation code must compare the
    two representations and record disagreements rather than picking the one
    that changes a result.
    """
    token = hex_value.strip().lower().removeprefix("0x")
    if len(token) != 16:
        raise AccountingError("SAS hex doubles must contain 16 hexadecimal characters.")
    try:
        raw = bytes.fromhex(token)
    except ValueError as exc:
        raise AccountingError(f"Invalid SAS hex value: {hex_value!r}") from exc
    decoded = struct.unpack(">d", raw)[0]
    if decoded != decoded or decoded in (float("inf"), float("-inf")):
        raise AccountingError("Decoded SAS hex value is not finite.")
    return decoded
