"""Dates read from the Kilts manual week decode table, Part 8."""

from datetime import date, timedelta

import pytest

from pricing_research.data.calendar import (
    CEREAL_LAST_WEEK,
    OATMEAL_FIRST_WEEK,
    PUBLISHED_WEEK_MAX,
    week_bounds,
)
from pricing_research.economics.accounting import AccountingError


@pytest.mark.parametrize(
    ("week", "start", "end"),
    [
        (1, date(1989, 9, 14), date(1989, 9, 20)),
        (7, date(1989, 10, 26), date(1989, 11, 1)),
        (91, date(1991, 6, 6), date(1991, 6, 12)),
        (115, date(1991, 11, 21), date(1991, 11, 27)),
        (116, date(1991, 11, 28), date(1991, 12, 4)),
        (399, date(1997, 5, 1), date(1997, 5, 7)),
        (400, date(1997, 5, 8), date(1997, 5, 14)),
    ],
)
def test_published_week_dates(week: int, start: date, end: date) -> None:
    assert week_bounds(week) == (start, end)


def test_weeks_are_contiguous_seven_day_blocks() -> None:
    previous_end = None
    for week in range(1, PUBLISHED_WEEK_MAX + 1):
        start, end = week_bounds(week)
        assert end - start == timedelta(days=6)
        if previous_end is not None:
            assert start - previous_end == timedelta(days=1)
        previous_end = end


def test_category_windows_match_the_manual() -> None:
    assert week_bounds(OATMEAL_FIRST_WEEK)[0] == date(1991, 6, 6)
    assert week_bounds(CEREAL_LAST_WEEK)[1] == date(1997, 5, 7)


def test_week_outside_the_published_table_is_rejected() -> None:
    with pytest.raises(AccountingError):
        week_bounds(0)
    with pytest.raises(AccountingError):
        week_bounds(401)
