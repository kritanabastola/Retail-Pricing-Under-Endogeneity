"""Week index from the Kilts Dominick's manual, Part 8.

Week 1 is the seven-day period beginning 14 September 1989. Each later index
is the next seven-day period. That rule reproduces the week-start and week-end
dates read directly from the manual for the weeks covered by the unit tests.

The published decode table continues through week 400 (ending 14 May 1997).
The cereals movement file's last week, as stated in the manual, is week 399.
This module does not attach the manual's special-event labels. A complete
transcription of that column is still open; week fixed effects do not require it.
"""

from __future__ import annotations

from datetime import date, timedelta

from pricing_research.economics.accounting import AccountingError

WEEK1_START = date(1989, 9, 14)
PUBLISHED_WEEK_MIN = 1
PUBLISHED_WEEK_MAX = 400
CEREAL_FIRST_WEEK = 1
CEREAL_LAST_WEEK = 399
OATMEAL_FIRST_WEEK = 91
OATMEAL_LAST_WEEK = 399


def week_bounds(week: int) -> tuple[date, date]:
    """Return the inclusive start and end dates for a published week index."""
    if isinstance(week, bool) or not isinstance(week, int):
        raise AccountingError("Week index must be an integer.")
    if week < PUBLISHED_WEEK_MIN or week > PUBLISHED_WEEK_MAX:
        raise AccountingError(
            f"Week {week} is outside the published decode table "
            f"({PUBLISHED_WEEK_MIN}–{PUBLISHED_WEEK_MAX})."
        )
    start = WEEK1_START + timedelta(weeks=week - 1)
    end = start + timedelta(days=6)
    return start, end
