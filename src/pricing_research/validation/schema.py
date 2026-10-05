"""Movement-file checks that report problems instead of dropping them.

Column names were read from the oatmeal movement CSV header on 5 October 2026.
The Kilts manual describes the same movement schema for every category. Cereals
still need their own header check when that file is ingested.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence

from pricing_research.economics.accounting import AccountingError

MOVEMENT_COLUMNS: tuple[str, ...] = (
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
)

UPC_COLUMNS: tuple[str, ...] = (
    "COM_CODE",
    "UPC",
    "DESCRIP",
    "SIZE",
    "CASE",
    "NITEM",
)

PROMOTION_CODES: frozenset[str] = frozenset({"B", "C", "S"})

UpcStoreWeek = tuple[int, int, int]


def require_columns(columns: Sequence[str], required: Sequence[str], file_role: str) -> None:
    """Raise if any required column is absent. Extra columns are allowed."""
    present = set(columns)
    missing = [name for name in required if name not in present]
    if missing:
        raise AccountingError(f"{file_role} file is missing columns: {', '.join(missing)}")


def classify_sale_code(sale: str | None) -> str:
    """Classify ``SALE`` as ``coded``, ``blank``, or ``unclassified``.

    ``coded`` means B, C, or S, the three codes defined in manual Part 4.
    ``blank`` means the field is empty. The manual says a blank field does not
    prove that the week was unpromoted. ``unclassified`` means some other
    non-empty code. The cereals and soup movement files contain ``G``, and
    cereals contains a single ``L``. Those letters are not defined in the
    manual sections read for this project, so they are not treated as promotions
    and they are not treated as blank.
    """
    if sale is None or sale.strip() == "":
        return "blank"
    if sale.strip().upper() in PROMOTION_CODES:
        return "coded"
    return "unclassified"


def sale_code_is_set(sale: str | None) -> bool:
    """Return whether ``SALE`` is one of B, C, or S.

    Part 4 of the manual says a set code indicates a promotion (B bonus buy,
    C coupon, S simple price reduction), and an unset code does not prove that
    the week was unpromoted. A blank value therefore returns False without
    being interpreted as a confirmed regular-price week. Any other non-blank
    code is an error.
    """
    if sale is None:
        return False
    code = sale.strip().upper()
    if code == "":
        return False
    if code not in PROMOTION_CODES:
        raise AccountingError(f"Unrecognized SALE code: {sale!r}")
    return True


def duplicate_upc_store_weeks(keys: Iterable[UpcStoreWeek]) -> tuple[UpcStoreWeek, ...]:
    """Return keys that occur more than once, in first-seen order.

    The manual says movement files are sorted by UPC, store, and week. A
    duplicate key is a data defect. This function does not delete either copy.
    """
    counts: Counter[UpcStoreWeek] = Counter(keys)
    return tuple(key for key, count in counts.items() if count > 1)


def audit_upc_coverage(
    movement_upcs: Iterable[int],
    attribute_upcs: Iterable[int],
) -> dict[str, tuple[int, ...] | int]:
    """Count movement UPCs that do not appear in the UPC attribute file.

    The result is an audit. It is not a filtered analysis sample.
    """
    movement_set = set(movement_upcs)
    attribute_set = set(attribute_upcs)
    unmatched = tuple(sorted(movement_set - attribute_set))
    return {
        "n_movement_upcs": len(movement_set),
        "n_attribute_upcs": len(attribute_set),
        "n_unmatched_movement_upcs": len(unmatched),
        "unmatched_movement_upcs": unmatched,
    }
