"""Parse the UPC ``SIZE`` text. Unparsed sizes stay missing.

A bare number is not treated as ounces. Count and assortment strings are not
converted. Rows are never dropped because size did not parse.
"""

from __future__ import annotations

import re

_OUNCES = re.compile(r"^(\d+(?:\.\d+)?)\s*O(?:Z)?$", re.IGNORECASE)
_TRAILING_Z = re.compile(r"^(\d+(?:\.\d+)?)\s*Z$", re.IGNORECASE)


def parse_package_ounces(size: str | None) -> tuple[float | None, str]:
    """Return ``(ounces, rule)``.

    ``rule`` is ``ounces``, ``trailing_z``, or ``unparsed``. ``trailing_z``
    covers strings such as ``19.25Z`` and ``17.4 Z``, which use Z rather than OZ.
    """
    if size is None:
        return None, "unparsed"
    text = " ".join(size.strip().upper().split())
    if text == "":
        return None, "unparsed"
    ounces = _OUNCES.match(text)
    if ounces:
        return float(ounces.group(1)), "ounces"
    trailing_z = _TRAILING_Z.match(text)
    if trailing_z:
        return float(trailing_z.group(1)), "trailing_z"
    return None, "unparsed"
