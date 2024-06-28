"""Models for Husqvarna Automower data."""

import logging
import operator
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime, timedelta
from enum import Enum, StrEnum
from re import sub

from mashumaro import DataClassDictMixin, field_options

from .const import ERRORCODES

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

WEEKDAYS_TO_RFC5545 = {
    "monday": "MO",
    "tuesday": "TU",
    "wednesday": "WE",
    "thursday": "TH",
    "friday": "FR",
    "saturday": "SA",
    "sunday": "SU",
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

    headlights: bool
    work_areas: bool = field(metadata=field_options(alias="workAreas"))
    position: bool
    stay_out_zones: bool = field(metadata=field_options(alias="stayOutZones"))


@dataclass
class Mower(DataClassDictMixin):
    """Information about the mowers current status."""

    mode: str
    activity: str
    state: str
    error_code: int = field(metadata=field_options(alias="errorCode"))
    error_key: str | None = field(
        metadata=field_options(
            deserialize=lambda x: (None if x == 0 else snake_case(ERRORCODES.get(x))),
            alias="errorCode",
        ),
    )
    error_datetime: datetime | None = field(
        metadata=field_options(
            deserialize=lambda x: (
                None
                if x == 0
                else datetime.fromtimestamp(x / 1000, tz=UTC)
                .replace(tzinfo=None)
                .astimezone(UTC)
            ),
            alias="errorCodeTimestamp",
        ),
    )
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


@dataclass
class Calendar(DataClassDictMixin):
    """Information about the calendar tasks.

    An Automower can have several tasks. If the mower supports
    work areas the property workAreaId is required to connect
    the task to an work area.
    """

    start: int
    duration: int
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


@dataclass
class AutomowerCalendarEvent(DataClassDictMixin):
    """Information about the calendar tasks.

    An Automower can have several tasks. If the mower supports
    work areas the property workAreaId is required to connect
    the task to an work area.
    """

    start: datetime
    end: datetime
    rrule: str
    uid: str
    work_area_id: int | None


def husqvarna_schedule_to_calendar(
    task_list: list,
) -> list[AutomowerCalendarEvent]:
    """Convert the schedule to an sorted list of calendar events."""
    eventlist = []
    for task_dict in task_list:
        calendar_dataclass = Calendar.from_dict(task_dict)
        event = ConvertScheduleToCalendar(calendar_dataclass)
        eventlist.append(event.make_event())
    eventlist.sort(key=operator.attrgetter("start"))
    return eventlist


class ConvertScheduleToCalendar:
    """Convert the Husqvarna task to an AutomowerCalendarEvent."""

    def __init__(self, task: Calendar) -> None:
        """Initialize the schedule to calendar converter."""
        self.task = task
        self.now = datetime.now().astimezone()
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
                        + timedelta(minutes=self.task.start)
                        + timedelta(minutes=self.task.duration)
                    )
                    if self.begin_of_current_day == time_to_check_begin_of_day:
                        if end_task < self.now:
                            break
                    return self.now + timedelta(days)
        return self.now

    def make_daylist(self) -> str:
        """Generate a RFC5545 daylist from a task."""
        day_list = ""
        for task_field in fields(self.task):
            field_name = task_field.name
            field_value = getattr(self.task, field_name)
            if field_value is True:
                today_rfc = WEEKDAYS_TO_RFC5545[field_name]
                if day_list == "":
                    day_list = today_rfc
                else:
                    day_list += "," + str(today_rfc)
        return day_list

    def make_event(self) -> AutomowerCalendarEvent:
        """Generate a AutomowerCalendarEvent from a task."""
        daylist = self.make_daylist()
        next_wd_with_schedule = self.next_weekday_with_schedule()
        begin_of_day_with_schedule = next_wd_with_schedule.replace(
            hour=0, minute=0, second=0, microsecond=0
        ).astimezone()
        return AutomowerCalendarEvent(
            start=(
                begin_of_day_with_schedule + timedelta(minutes=self.task.start)
            ).astimezone(tz=UTC),
            end=(
                begin_of_day_with_schedule
                + timedelta(minutes=self.task.start)
                + timedelta(minutes=self.task.duration)
            ).astimezone(tz=UTC),
            rrule=f"FREQ=WEEKLY;BYDAY={daylist}",
            uid=f"{self.task.start}_{self.task.duration}_{daylist}",
            work_area_id=self.task.work_area_id,
        )


@dataclass
class Tasks(DataClassDictMixin):
    """DataClass for Task values."""

    tasks: list[Calendar]
    events: list[AutomowerCalendarEvent] = field(
        metadata=field_options(
            deserialize=husqvarna_schedule_to_calendar,
            alias="tasks",
        ),
    )


@dataclass
class Override(DataClassDictMixin):
    """DataClass for Override values."""

    action: str


@dataclass
class Planner(DataClassDictMixin):
    """DataClass for Planner values."""

    next_start_datetime: datetime | None = field(
        metadata=field_options(
            deserialize=lambda x: (
                None
                if x == 0
                else datetime.fromtimestamp(x / 1000, tz=UTC)
                .replace(tzinfo=None)
                .astimezone(UTC)
            ),
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
class _Zones(DataClassDictMixin):
    """DataClass for Zone values."""

    id: str
    name: str
    enabled: bool


@dataclass
class Zone(DataClassDictMixin):
    """DataClass for Zone values."""

    name: str
    enabled: bool


@dataclass
class StayOutZones(DataClassDictMixin):
    """DataClass for StayOutZone values."""

    dirty: bool
    zones: dict[str, Zone] = field(
        metadata=field_options(
            deserialize=lambda zone_list: {
                area.id: Zone(name=area.name, enabled=area.enabled)
                for area in map(_Zones.from_dict, zone_list)
            },
        ),
    )


@dataclass
class _WorkAreas(DataClassDictMixin):
    """DataClass for WorkAreas values."""

    work_area_id: int = field(metadata=field_options(alias="workAreaId"))
    name: str = field(
        metadata=field_options(
            deserialize=lambda x: "my_lawn" if x == "" else x,
        ),
    )
    cutting_height: int = field(metadata=field_options(alias="cuttingHeight"))


@dataclass
class WorkArea(DataClassDictMixin):
    """DataClass for WorkAreas values."""

    name: str
    cutting_height: int


@dataclass
class Settings(DataClassDictMixin):
    """DataClass for WorkAreas values."""

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
                area.work_area_id: WorkArea(
                    name=area.name, cutting_height=area.cutting_height
                )
                for area in map(_WorkAreas.from_dict, workarea_list)
            },
            alias="workAreas",
        ),
        default=None,
    )


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
