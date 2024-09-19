"""Models for Husqvarna Automower data."""

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime, time, timedelta
from enum import Enum, StrEnum
from re import sub

from ical.iter import (
    MergedIterable,
    SortableItem,
)
from ical.timespan import Timespan
from mashumaro import DataClassDictMixin, field_options
from mashumaro.config import BaseConfig
from mashumaro.types import SerializationStrategy

from .const import ERRORCODES, DayOfWeek, ProgramFrequency
from .timeline import ProgramEvent, ProgramTimeline, create_recurrence

logging.basicConfig(level=logging.DEBUG)

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


def snake_case(string: str | None) -> str:
    """Convert an error text to snake case."""
    if string is None:
        raise TypeError
    return "_".join(
        sub(
            "([A-Z][a-z][,]+)",
            r" \1",
            sub(
                "([A-Z]+)",
                r" \1",
                string.replace("-", " ")
                .replace(",", "")
                .replace(".", "")
                .replace("!", ""),
            ),
        ).split()
    ).lower()


def generate_work_area_names_list(workarea_list: list) -> list[str]:
    """Return a list of names extracted from each work area dictionary."""
    wa_names = [WorkArea.from_dict(area).name for area in workarea_list]
    wa_names.append("no_work_area_active")
    return wa_names


def generate_work_area_dict(workarea_list: list | None) -> dict[int, str] | None:
    """Return a dict of names extracted from each work area dictionary."""
    if workarea_list is None:
        return None
    return {
        area["workAreaId"]: get_work_area_name(area["name"]) for area in workarea_list
    }


def get_work_area_name(name: str) -> str:
    """Return the work area name, replacing empty strings with a default name 'my_lawn'."""
    return "my_lawn" if name == "" else name


def make_name_string(work_area_name: str | None, number: int) -> str:
    """Return a string for the calendar summary."""
    if work_area_name is not None:
        return f"{work_area_name} schedule {number}"
    return f"Schedule {number}"


@dataclass
class User(DataClassDictMixin):
    """The user details of the JWT."""

    first_name: str
    last_name: str
    custom_attributes: dict[str, str]
    customer_id: str


@dataclass
class JWT(DataClassDictMixin):
    """The content of the JWT."""

    jti: str
    iss: str
    roles: list[str]
    groups: list[str]
    scopes: list[str]
    scope: str
    client_id: str
    customer_id: str
    user: User
    iat: int
    exp: int
    sub: str


class TimeSerializationStrategy(SerializationStrategy):
    """SerializationStrategy for Recur object."""

    def serialize(self, value: time) -> int:
        """Serialize a time object to an integer representing minutes."""
        return value.hour * 60 + value.minute

    def deserialize(self, value: int) -> time:
        """Deserialize an integer to a time object."""
        hour = int(value / 60)
        minute = value - 60 * hour
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
class System(DataClassDictMixin):
    """System information about a Automower."""

    name: str
    model: str
    serial_number: str = field(metadata=field_options(alias="serialNumber"))


@dataclass
class Battery(DataClassDictMixin):
    """Information about the battery in the Automower."""

    battery_percent: int = field(metadata=field_options(alias="batteryPercent"))


@dataclass
class Capabilities(DataClassDictMixin):
    """Information about what capabilities the Automower has."""

    can_confirm_error: bool = field(metadata=field_options(alias="canConfirmError"))
    headlights: bool
    position: bool
    stay_out_zones: bool = field(metadata=field_options(alias="stayOutZones"))
    work_areas: bool = field(metadata=field_options(alias="workAreas"))


@dataclass
class Mower(DataClassDictMixin):
    """Information about the mowers current status."""

    mode: str
    activity: str
    state: str
    error_code: int = field(metadata=field_options(alias="errorCode"))
    error_key: str | None = field(
        metadata=field_options(
            deserialize=lambda x: None if x == 0 else snake_case(ERRORCODES.get(x)),
            alias="errorCode",
        )
    )
    error_timestamp: int = field(metadata=field_options(alias="errorCodeTimestamp"))
    error_datetime_naive: datetime | None = field(
        metadata=field_options(
            deserialize=lambda x: (
                None
                if x == 0
                else datetime.fromtimestamp(x / 1000, tz=UTC).replace(tzinfo=None)
            ),
            alias="errorCodeTimestamp",
        ),
    )
    inactive_reason: str = field(metadata=field_options(alias="inactiveReason"))
    is_error_confirmable: bool = field(
        metadata=field_options(alias="isErrorConfirmable"), default=False
    )
    work_area_id: int | None = field(
        metadata=field_options(alias="workAreaId"), default=None
    )
    work_area_name: str | None = field(init=False, default=None)

    def __post_init__(self):
        """Initialize work_area_name to None for later external setting."""
        self.work_area_name = None


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
    day_set: set


class ConvertScheduleToCalendar:
    """Convert the Husqvarna task to an AutomowerCalendarEvent."""

    def __init__(self, task: Calendar) -> None:
        """Initialize the schedule to calendar converter."""
        self.task = task
        self.now = datetime.now()
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
                if field_value is True and field_name is day_to_check_as_string:
                    end_task = (
                        time_to_check_begin_of_day
                        + timedelta(
                            hours=self.task.start.hour, minutes=self.task.start.minute
                        )
                        + self.task.duration
                    )
                    if self.begin_of_current_day == time_to_check_begin_of_day:
                        if end_task < self.now:
                            break
                    return self.now + timedelta(days)
        return self.now

    def make_dayset(self) -> set[DayOfWeek | None]:
        """Generate a set of days from a task."""
        return {
            WEEKDAYS_TO_ICAL.get(day) for day in WEEKDAYS if getattr(self.task, day)
        }

    def make_event(self) -> AutomowerCalendarEvent:
        """Generate a AutomowerCalendarEvent from a task."""
        dayset = self.make_dayset()
        next_wd_with_schedule = self.next_weekday_with_schedule()
        begin_of_day_with_schedule = next_wd_with_schedule.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return AutomowerCalendarEvent(
            start=begin_of_day_with_schedule
            + timedelta(hours=self.task.start.hour, minutes=self.task.start.minute),
            duration=self.task.duration,
            uid=f"{self.task.start}_{self.task.duration}_{dayset}",
            day_set=dayset,
        )


@dataclass
class Tasks(DataClassDictMixin):
    """DataClass for Task values."""

    tasks: list[Calendar] | None

    @property
    def timeline(self) -> ProgramTimeline | None:
        """Return a timeline of all schedules."""
        return self.timeline_tz()

    def timeline_tz(self) -> ProgramTimeline | None:
        """Return a timeline of all schedules."""
        if self.tasks is None:
            return None
        self.schedule_no: dict = {}  # pylint: disable=attribute-defined-outside-init
        for task in self.tasks:
            if task.work_area_id is not None:
                self.schedule_no[task.work_area_id] = 0
            if task.work_area_id is None:
                self.schedule_no["-1"] = 0

        iters: list[Iterable[SortableItem[Timespan, ProgramEvent]]] = []

        for task in self.tasks:
            event = ConvertScheduleToCalendar(task).make_event()
            number = self.generate_schedule_no(task)

            if len(event.day_set) == 7:
                freq = ProgramFrequency.DAILY
            else:
                freq = ProgramFrequency.WEEKLY

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

    def generate_schedule_no(self, task: Calendar) -> int:
        """Return a schedule number."""
        if task is not None:
            if task.work_area_id is not None:
                if task.work_area_id is not None:
                    self.schedule_no[task.work_area_id] = (
                        self.schedule_no[task.work_area_id] + 1
                    )
                    return self.schedule_no[task.work_area_id]
            self.schedule_no["-1"] = self.schedule_no["-1"] + 1
            return self.schedule_no["-1"]
        return None


@dataclass
class Override(DataClassDictMixin):
    """DataClass for Override values."""

    action: str


@dataclass
class Planner(DataClassDictMixin):
    """DataClass for Planner values."""

    next_start: int = field(
        metadata=field_options(
            alias="nextStartTimestamp",
        ),
    )
    next_start_datetime_naive: datetime | None = field(
        metadata=field_options(
            deserialize=lambda x: (
                None
                if x == 0
                else datetime.fromtimestamp(x / 1000, tz=UTC).replace(tzinfo=None)
            ),
            alias="nextStartTimestamp",
        ),
    )
    override: Override
    restricted_reason: str = field(metadata=field_options(alias="restrictedReason"))


@dataclass
class Metadata(DataClassDictMixin):
    """DataClass for Metadata values."""

    connected: bool
    status_dateteime: datetime = field(
        metadata=field_options(
            deserialize=lambda x: (datetime.fromtimestamp(x / 1000, tz=UTC)),
            alias="statusTimestamp",
        ),
    )


@dataclass
class Positions(DataClassDictMixin):
    """List of the GPS positions.

    Latest registered position is first in the
    array and the oldest last in the array.
    Max number of positions is 50 after
    that the latest position is removed
    from the array.
    """

    latitude: float
    longitude: float


@dataclass
class Statistics(DataClassDictMixin):
    """DataClass for Statistics values."""

    cutting_blade_usage_time: int | None = field(
        metadata=field_options(alias="cuttingBladeUsageTime"), default=None
    )
    number_of_charging_cycles: int | None = field(
        metadata=field_options(alias="numberOfChargingCycles"), default=None
    )
    number_of_collisions: int | None = field(
        metadata=field_options(alias="numberOfCollisions"), default=None
    )
    total_charging_time: int | None = field(
        metadata=field_options(alias="totalChargingTime"), default=None
    )
    total_cutting_time: int | None = field(
        metadata=field_options(alias="totalCuttingTime"), default=None
    )
    total_drive_distance: int | None = field(
        metadata=field_options(alias="totalDriveDistance"), default=None
    )
    total_running_time: int | None = field(
        metadata=field_options(alias="totalRunningTime"), default=None
    )
    total_searching_time: int | None = field(
        metadata=field_options(alias="totalSearchingTime"), default=None
    )


@dataclass
class Headlight(DataClassDictMixin):
    """DataClass for Headlight values."""

    mode: str | None


@dataclass
class Zone(DataClassDictMixin):
    """DataClass for Zone values."""

    name: str
    enabled: bool


@dataclass
class StayOutZones(DataClassDictMixin):
    """DataClass for StayOutZones values."""

    dirty: bool
    zones: dict[str, Zone] = field(
        metadata=field_options(
            deserialize=lambda zone_list: {
                zone["id"]: Zone.from_dict(zone) for zone in zone_list
            },
        ),
    )


@dataclass
class WorkArea(DataClassDictMixin):
    """DataClass for WorkArea values."""

    name: str = field(
        metadata=field_options(
            deserialize=lambda x: "my_lawn" if x == "" else x,
        ),
    )
    cutting_height: int = field(metadata=field_options(alias="cuttingHeight"))
    enabled: bool = field(default=False)
    progress: int | None = field(default=None)
    last_time_completed_naive: datetime | None = field(
        metadata=field_options(
            deserialize=lambda x: (
                None
                if x == 0
                else datetime.fromtimestamp(x / 1000, tz=UTC).replace(tzinfo=None)
            ),
            alias="lastTimeCompleted",
        ),
        default=None,
    )


@dataclass
class Settings(DataClassDictMixin):
    """DataClass for Settings values."""

    headlight: Headlight
    cutting_height: int | None = field(
        metadata=field_options(alias="cuttingHeight"), default=None
    )


@dataclass
class MowerAttributes(DataClassDictMixin):
    """DataClass for MowerAttributes."""

    system: System
    battery: Battery
    capabilities: Capabilities
    mower: Mower
    calendar: Tasks
    planner: Planner
    metadata: Metadata
    positions: list[Positions] | None
    settings: Settings
    statistics: Statistics
    stay_out_zones: StayOutZones | None = field(
        metadata=field_options(alias="stayOutZones"), default=None
    )
    work_areas: dict[int, WorkArea] | None = field(
        metadata=field_options(
            deserialize=lambda workarea_list: {
                area["workAreaId"]: WorkArea.from_dict(area) for area in workarea_list
            },
            alias="workAreas",
        ),
        default=None,
    )
    work_area_names: list[str] | None = field(
        metadata=field_options(
            deserialize=generate_work_area_names_list,
            alias="workAreas",
        ),
        default=None,
    )
    work_area_dict: dict[int, str] | None = field(
        metadata=field_options(
            deserialize=generate_work_area_dict,
            alias="workAreas",
        ),
        default=None,
    )

    def __post_init__(self):
        """Set the name after init."""
        if self.capabilities.work_areas:
            if self.mower.work_area_id is None:
                self.mower.work_area_name = "no_work_area_active"
            if self.work_areas is not None:
                work_area = self.work_areas.get(self.mower.work_area_id)
                if work_area:
                    self.mower.work_area_name = work_area.name
            for task in self.calendar.tasks:
                task.work_area_name = self.work_area_dict.get(task.work_area_id)
        if not self.capabilities.work_areas:
            for task in self.calendar.tasks:
                task.work_area_name = None


@dataclass
class MowerData(DataClassDictMixin):
    """DataClass for MowerData values."""

    type: str
    id: str
    attributes: MowerAttributes


@dataclass
class MowerList(DataClassDictMixin):
    """DataClass for a list of all mowers."""

    data: list[MowerData]


class HeadlightModes(StrEnum):
    """Headlight modes of a lawn mower."""

    ALWAYS_ON = "ALWAYS_ON"
    ALWAYS_OFF = "ALWAYS_OFF"
    EVENING_ONLY = "EVENING_ONLY"
    EVENING_AND_NIGHT = "EVENING_AND_NIGHT"


class MowerStates(StrEnum):
    """Mower states of a lawn mower."""

    FATAL_ERROR = "FATAL_ERROR"
    ERROR = "ERROR"
    ERROR_AT_POWER_UP = "ERROR_AT_POWER_UP"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"
    STOPPED = "STOPPED"
    OFF = "OFF"
    PAUSED = "PAUSED"
    IN_OPERATION = "IN_OPERATION"
    WAIT_UPDATING = "WAIT_UPDATING"
    WAIT_POWER_UP = "WAIT_POWER_UP"
    RESTRICTED = "RESTRICTED"


class MowerActivities(StrEnum):
    """Mower activities of a lawn mower."""

    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    MOWING = "MOWING"
    GOING_HOME = "GOING_HOME"
    CHARGING = "CHARGING"
    LEAVING = "LEAVING"
    PARKED_IN_CS = "PARKED_IN_CS"
    STOPPED_IN_GARDEN = "STOPPED_IN_GARDEN"


class MowerModes(StrEnum):
    """Mower activities of a lawn mower."""

    MAIN_AREA = "MAIN_AREA"
    DEMO = "DEMO"
    SECONDARY_AREA = "SECONDARY_AREA"
    HOME = "HOME"
    UNKNOWN = "UNKNOWN"


class RestrictedReasons(StrEnum):
    """Restricted reasons in the planner of lawn mower."""

    NONE = "NONE"
    WEEK_SCHEDULE = "WEEK_SCHEDULE"
    PARK_OVERRIDE = "PARK_OVERRIDE"
    SENSOR = "SENSOR"
    DAILY_LIMIT = "DAILY_LIMIT"
    FOTA = "FOTA"
    FROST = "FROST"
    ALL_WORK_AREAS_COMPLETED = "ALL_WORK_AREAS_COMPLETED"
    EXTERNAL = "EXTERNAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Actions(StrEnum):
    """Actions in the planner of lawn mower."""

    NOT_ACTIVE = "NOT_ACTIVE"
    FORCE_PARK = "FORCE_PARK"
    FORCE_MOW = "FORCE_MOW"


class ExternalReasons(Enum):
    """External reasons for restrictions."""

    GOOGLE_ASSISTANT = range(1000, 1999)
    AMAZON_ALEXA = range(2000, 2999)
    DEVELOPER_PORTAL = range(3000, 3999), range(200000, 299999)
    IFTT = 4000, range(4003, 4999)
    IFTT_WILDLIFE = 4001
    IFTT_FROST_AND_RAIN = 4002
    IFTT_CALENDAR_CONNECTION = 4003
    IFTT_APPLETS = range(100000, 199999)


class InactiveReasons(Enum):
    """Inactive reasons why the mower is not working."""

    NONE = "NONE"
    PLANNING = "PLANNING"
    SEARCHING_FOR_SATELLITES = "SEARCHING_FOR_SATELLITES"
