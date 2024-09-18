"""A timeline is a set of events on a calendar.

This timeline is used to iterate over program runtime events, managing
the logic for interpreting recurring events for the Husqvarna Automower
calendar. Only upcoming events will be shown.
"""

from __future__ import annotations

import datetime
import logging
from collections.abc import Iterable
from dataclasses import dataclass

from dateutil import rrule
from ical.iter import (
    LazySortableItem,
    RecurIterable,
    SortableItem,
    SortableItemTimeline,
)
from ical.timespan import Timespan

from .const import DayOfWeek, ProgramFrequency

__all__ = ["ProgramTimeline", "ProgramEvent"]

_LOGGER = logging.getLogger(__name__)

RRULE_WEEKDAY = {
    DayOfWeek.MONDAY: rrule.MO,
    DayOfWeek.TUESDAY: rrule.TU,
    DayOfWeek.WEDNESDAY: rrule.WE,
    DayOfWeek.THURSDAY: rrule.TH,
    DayOfWeek.FRIDAY: rrule.FR,
    DayOfWeek.SATURDAY: rrule.SA,
    DayOfWeek.SUNDAY: rrule.SU,
}


@dataclass
class ProgramEvent:
    """An instance of a program event."""

    schedule_no: int
    work_area_id: int | None
    start: datetime.datetime
    end: datetime.datetime
    rule: rrule.rrule | None = None

    @property
    def rrule_str(self) -> str | None:
        """Return the recurrence rule string."""
        rule_str = str(self.rule)
        if not self.rule or "DTSTART:" not in rule_str or "RRULE:" not in rule_str:
            return None
        parts = str(self.rule).split("\n")
        if len(parts) != 2:
            return None
        return parts[1].lstrip("RRULE:")  # noqa: B005


class ProgramTimeline(SortableItemTimeline[ProgramEvent]):
    """A timeline of events in an irrigation program."""


def create_recurrence(
    schedule_no: int,
    work_area_id: int | None,
    frequency: ProgramFrequency,
    dtstart: datetime.datetime,
    duration: datetime.timedelta,
    days_of_week: set[DayOfWeek],
) -> Iterable[SortableItem[Timespan, ProgramEvent]]:
    """Create a timeline using a recurrence rule."""

    byweekday = [RRULE_WEEKDAY[day_of_week] for day_of_week in days_of_week]
    ruleset = rrule.rruleset()
    rule: rrule.rrule
    if frequency == ProgramFrequency.DAILY:
        # Create a RRULE that is FREQ=DAILY
        rule = rrule.rrule(
            freq=rrule.DAILY,
            dtstart=dtstart,
            cache=True,
        )
    elif frequency == ProgramFrequency.WEEKLY:
        # Create a RRULE that is FREQ=WEEKLY
        rule = rrule.rrule(
            freq=rrule.WEEKLY,
            byweekday=byweekday,
            dtstart=dtstart,
            cache=True,
        )
    ruleset.rrule(rule)

    def adapter(
        dtstart: datetime.datetime | datetime.date,
    ) -> SortableItem[Timespan, ProgramEvent]:
        if not isinstance(dtstart, datetime.datetime):
            raise TypeError("Expected datetime, got date")
        dtend = dtstart + duration

        def build() -> ProgramEvent:
            return ProgramEvent(schedule_no, work_area_id, dtstart, dtend, rule)

        return LazySortableItem(Timespan.of(dtstart, dtend), build)

    return RecurIterable(adapter, ruleset)
