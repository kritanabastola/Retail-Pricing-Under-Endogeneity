"""Log-sample waterfall. Rows are classified, not deleted, by these rules.

The order matches the pre-specified log sample: a row is out of that sample
for the first reason that applies. Other problems are still counted as flags.
"""

from __future__ import annotations

EXCLUSION_ORDER: tuple[str, ...] = (
    "duplicate_upc_store_week",
    "ok_not_one",
    "price_not_positive",
    "qty_not_positive",
    "move_not_positive",
    "week_outside_published_calendar",
)


def first_log_sample_exclusion(flags: dict[str, bool]) -> str | None:
    """Return the first log-sample exclusion that applies, or ``None``."""
    for rule in EXCLUSION_ORDER:
        if flags[rule]:
            return rule
    return None


def waterfall_counts(rule_hits: dict[str, int], input_rows: int) -> list[dict[str, int | str]]:
    """Turn first-reason counts into a reconciliation that sums to the input."""
    classified = sum(rule_hits[rule] for rule in EXCLUSION_ORDER)
    kept = input_rows - classified
    rows: list[dict[str, int | str]] = [
        {
            "record_type": "input",
            "rule": "movement_data_rows",
            "rows": input_rows,
            "rows_remaining": input_rows,
        }
    ]
    remaining = input_rows
    for rule in EXCLUSION_ORDER:
        hit = rule_hits[rule]
        remaining -= hit
        rows.append(
            {
                "record_type": "sequential_exclusion",
                "rule": rule,
                "rows": hit,
                "rows_remaining": remaining,
            }
        )
    rows.append(
        {
            "record_type": "output",
            "rule": "log_sample",
            "rows": kept,
            "rows_remaining": kept,
        }
    )
    return rows
