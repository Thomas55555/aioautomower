"""Models for Automower Connect API - Calendar."""

from dataclasses import dataclass, field, fields
from datetime import datetime, time, timedelta
from typing import TYPE_CHECKING

from ical.iter import (
    MergedIterable,
    SortableItem,
)
from mashumaro import DataClassDictMixin, field_options
from mashumaro.config import BaseConfig
from mashumaro.types import SerializationStrategy

from aioautomower import tz_util
from aioautomower.const import DayOfWeek, ProgramFrequency
from aioautomower.timeline import ProgramEvent, ProgramTimeline, create_recurrence

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ical.timespan import Timespan

WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

WEEKDAYS_TO_ICAL = {
    "sunday": DayOfWeek.SUNDAY,
    "monday": DayOfWeek.MONDAY,
    "tuesday": DayOfWeek.TUESDAY,
    "wednesday": DayOfWeek.WEDNESDAY,
    "thursday": DayOfWeek.THURSDAY,
    "friday": DayOfWeek.FRIDAY,
    "saturday": DayOfWeek.SATURDAY,
}


class TimeSerializationStrategy(SerializationStrategy):
    """SerializationStrategy for Recur object."""

    def serialize(self, value: time) -> int:
        """Serialize a time object to an integer representing minutes."""
        return value.hour * 60 + value.minute

    def deserialize(self, value: int) -> time:
        """Deserialize an integer to a time object."""
        hour = value // 60
        minute = value % 60
        return time(hour=hour, minute=minute)


class DurationSerializationStrategy(SerializationStrategy):
    """SerializationStrategy for timedelta object."""

    def serialize(self, value: timedelta) -> int:
        """Serialize a timedelta object to an integer representing total minutes."""
        return int(value.total_seconds() // 60)  # Convert total seconds to minutes

    def deserialize(self, value: int) -> timedelta:
        """Deserialize an integer representing total minutes to a timedelta object."""
        return timedelta(minutes=value)


@dataclass
class Calendar(DataClassDictMixin):
    """Information about the calendar tasks.

    An Automower can have several tasks. If the mower supports
    work areas the property workAreaId is required to connect
    the task to an work area.
    """

    start: time = field(
        metadata=field_options(serialization_strategy=TimeSerializationStrategy())
    )
    duration: timedelta = field(
        metadata=field_options(serialization_strategy=DurationSerializationStrategy())
    )
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool
    work_area_id: int | None = field(
        metadata=field_options(alias="workAreaId"), default=None
    )

    class Config(BaseConfig):
        """BaseConfig for Calendar."""

        serialize_by_alias = True
        omit_none = True


@dataclass
class AutomowerCalendarEvent:
    """Information about the calendar tasks.

    Internal class for creating recurrence.
    """

    start: datetime
    duration: timedelta
    uid: str
    day_set: set[DayOfWeek]


class ConvertScheduleToCalendar:
    """Convert the Husqvarna task to an AutomowerCalendarEvent."""

    def __init__(self, task: Calendar) -> None:
        """Initialize the schedule to calendar converter."""
        self.task = task
        self.now = datetime.now()  # noqa: DTZ005
        self.begin_of_current_day = self.now.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.current_day = self.now.weekday()

    def next_weekday_with_schedule(self) -> datetime:
        """Find the next weekday with a schedule entry."""
        for days in range(8):
            time_to_check = self.now + timedelta(days=days)
            time_to_check_begin_of_day = time_to_check.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_to_check = time_to_check.weekday()
            day_to_check_as_string = WEEKDAYS[day_to_check]
            for task_field in fields(self.task):
                field_name = task_field.name
                field_value = getattr(self.task, field_name)
                if field_value is True and field_name == day_to_check_as_string:
                    end_task = (
                        time_to_check_begin_of_day
                        + timedelta(
                            hours=self.task.start.hour, minutes=self.task.start.minute
                        )
                        + self.task.duration
                    )
                    if (
                        self.begin_of_current_day == time_to_check_begin_of_day
                        and end_task < self.now
                    ):
                        break
                    return self.now + timedelta(days=days)
        return self.now

    def make_dayset(self) -> set[DayOfWeek]:
        """Generate a set of days from a task."""
        return {
            day
            for day in (
                WEEKDAYS_TO_ICAL.get(day) for day in WEEKDAYS if getattr(self.task, day)
            )
            if day is not None
        }

    def make_event(self) -> AutomowerCalendarEvent:
        """Generate a AutomowerCalendarEvent from a task."""
        dayset = self.make_dayset()
        next_wd_with_schedule = self.next_weekday_with_schedule()
        begin_of_day_with_schedule = next_wd_with_schedule.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return AutomowerCalendarEvent(
            start=(
                begin_of_day_with_schedule
                + timedelta(hours=self.task.start.hour, minutes=self.task.start.minute)
            ).replace(tzinfo=tz_util.MOWER_TIME_ZONE),
            duration=self.task.duration,
            uid=f"{self.task.start}_{self.task.duration}_{dayset}",
            day_set=dayset,
        )


@dataclass
class Tasks(DataClassDictMixin):
    """DataClass for Task values."""

    tasks: list[Calendar]

    @property
    def timeline(self) -> ProgramTimeline:
        """Return a timeline of all schedules."""
        return self.timeline_tz()

    def timeline_tz(self) -> ProgramTimeline:
        """Return a timeline of all schedules."""
        schedule_no: dict[int, int] = {}
        for task in self.tasks:
            key = task.work_area_id if task.work_area_id is not None else -1
            schedule_no.setdefault(key, 0)

        iters: list[Iterable[SortableItem[Timespan, ProgramEvent]]] = []

        for task in self.tasks:
            event = ConvertScheduleToCalendar(task).make_event()
            number = self.generate_schedule_no(task, schedule_no)

            freq = (
                ProgramFrequency.DAILY
                if len(event.day_set) == 7
                else ProgramFrequency.WEEKLY
            )

            iters.append(
                create_recurrence(
                    schedule_no=number,
                    work_area_id=task.work_area_id,
                    frequency=freq,
                    dtstart=event.start,
                    duration=event.duration,
                    days_of_week=event.day_set,
                )
            )

        return ProgramTimeline(MergedIterable(iters))

    def generate_schedule_no(self, task: Calendar, schedule_no: dict[int, int]) -> int:
        """Return a schedule number."""
        key = task.work_area_id if task.work_area_id is not None else -1
        schedule_no[key] += 1
        return schedule_no[key]


def make_name_string(work_area_name: str | None, number: int) -> str:
    """Return a string for the calendar summary."""
    if work_area_name is not None:
        return f"{work_area_name} schedule {number}"
    return f"Schedule {number}"
