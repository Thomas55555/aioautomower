"""Models for Husqvarna Automower data."""

from dataclasses import dataclass, field, fields
import datetime
from enum import Enum, StrEnum
import logging
import operator
from mashumaro import DataClassDictMixin, field_options

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


@dataclass
class User(DataClassDictMixin):
    """The user details of the JWT."""

    first_name: str
    last_name: str
    custom_attributes: dict
    customer_id: str


@dataclass
class JWT(DataClassDictMixin):
    """The content of the JWT."""

    # pylint: disable=too-many-instance-attributes
    jti: str
    iss: str
    roles: list
    groups: list
    scopes: list
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
    serial_number: int = field(metadata=field_options(alias="serialNumber"))


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
    error_code_dateteime: datetime.datetime | None = field(
        metadata=field_options(
            deserialize=lambda x: (
                None
                if x == 0
                else datetime.datetime.fromtimestamp(x / 1000).astimezone()
            ),
            alias="errorCodeTimestamp",
        ),
    )


@dataclass
class Calendar(DataClassDictMixin):
    """Information about the calendar tasks.

    An Automower can have several tasks. If the mower supports
    work areas the property workAreaId is required to connect
    the task to an work area.
    """

    # pylint: disable=too-many-instance-attributes
    start: int
    duration: int
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool


@dataclass
class AutomowerCalendarEvent(DataClassDictMixin):
    """Information about the calendar tasks.

    An Automower can have several tasks. If the mower supports
    work areas the property workAreaId is required to connect
    the task to an work area.
    """

    start: datetime.datetime
    end: datetime.datetime
    rrule: str
    uid: str


class ConvertScheduleToCalendar:
    """Convert the Husqvarna task to an AutomowerCalendarEvent"""

    def __init__(self, task: Calendar) -> None:
        """Initialize the schedule to calendar converter"""
        self.task = task
        self.now = datetime.datetime.now().astimezone()
        self.begin_of_current_day = self.now.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.current_day = self.now.weekday()

    # pylint: disable=inconsistent-return-statements
    def next_weekday_with_schedule(self) -> datetime.datetime:
        """Find the next weekday with a schedule entry."""
        # pylint: disable=too-many-nested-blocks
        for days in range(8):
            time_to_check = self.now + datetime.timedelta(days=days)
            time_to_check_begin_of_day = time_to_check.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_to_check = time_to_check.weekday()
            day_to_check_as_string = WEEKDAYS[day_to_check]
            for task_field in fields(self.task):
                field_name = task_field.name
                field_value = getattr(self.task, field_name)
                if field_value is True:
                    if field_name is day_to_check_as_string:
                        end_task = (
                            time_to_check_begin_of_day
                            + datetime.timedelta(minutes=self.task.start)
                            + datetime.timedelta(minutes=self.task.duration)
                        )
                        if self.begin_of_current_day == time_to_check_begin_of_day:
                            if end_task < self.now:
                                break
                        return self.now + datetime.timedelta(days)
        # return datetime.datetime.today() + datetime.timedelta(days_ahead)

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
        event = AutomowerCalendarEvent(
            start=begin_of_day_with_schedule
            + datetime.timedelta(minutes=self.task.start),
            end=begin_of_day_with_schedule
            + datetime.timedelta(minutes=self.task.start)
            + datetime.timedelta(minutes=self.task.duration),
            rrule=f"FREQ=WEEKLY;BYDAY={daylist}",
            uid=f"{self.task.start}_{self.task.duration}_{daylist}",
        )
        return event


@dataclass
class Tasks(DataClassDictMixin):
    """DataClass for Task values."""

    # pylint: disable=unnecessary-lambda
    events: list[AutomowerCalendarEvent] = field(
        metadata=field_options(
            deserialize=lambda v: husqvarna_schedule_to_calendar(v),
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

    next_start_dateteime: datetime.datetime | None = field(
        metadata=field_options(
            deserialize=lambda x: (
                None
                if x == 0
                else datetime.datetime.fromtimestamp(x / 1000).astimezone()
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
    status_dateteime: datetime.datetime = field(
        metadata=field_options(
            deserialize=lambda x: (
                datetime.datetime.fromtimestamp(x / 1000, tz=datetime.UTC)
            ),
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

    # pylint: disable=too-many-instance-attributes
    number_of_charging_cycles: int = field(
        metadata=field_options(alias="numberOfChargingCycles")
    )
    number_of_collisions: int = field(
        metadata=field_options(alias="numberOfCollisions")
    )
    total_charging_time: int = field(metadata=field_options(alias="totalChargingTime"))
    total_cutting_time: int = field(metadata=field_options(alias="totalCuttingTime"))
    total_drive_distance: int = field(
        metadata=field_options(alias="totalDriveDistance")
    )
    total_running_time: int = field(metadata=field_options(alias="totalRunningTime"))
    total_searching_time: int = field(
        metadata=field_options(alias="totalSearchingTime")
    )
    cutting_blade_usage_time: int | None = field(
        metadata=field_options(alias="cuttingBladeUsageTime"), default=None
    )


@dataclass
class Headlight(DataClassDictMixin):
    """DataClass for Headlight values."""

    mode: str | None


@dataclass
class Zones(DataClassDictMixin):
    """DataClass for Zone values."""

    id: str = field(metadata=field_options(alias="Id"))
    name: str
    enabled: bool


@dataclass
class StayOutZones(DataClassDictMixin):
    """DataClass for StayOutZone values."""

    dirty: bool
    zones: list[Zones]


@dataclass
class WorkAreas(DataClassDictMixin):
    """DataClass for WorkAreas values."""

    work_area_id: int = field(metadata=field_options(alias="workAreaId"))
    name: str
    cutting_height: int = field(metadata=field_options(alias="cuttingHeight"))


@dataclass
class MowerAttributes(DataClassDictMixin):
    """DataClass for MowerAttributes."""

    # pylint: disable=too-many-instance-attributes
    system: System
    battery: Battery
    capabilities: Capabilities
    mower: Mower
    calendar: Tasks
    planner: Planner
    metadata: Metadata
    positions: list[Positions] | None
    statistics: Statistics
    headlight: Headlight
    cutting_height: int | None = field(
        metadata=field_options(alias="cuttingHeight"), default=None
    )
    stay_out_zones: StayOutZones | None = field(
        metadata=field_options(alias="stayOutZones"), default=None
    )

    work_areas: list[WorkAreas] | None = field(
        metadata=field_options(alias="workAreas"), default=None
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


def husqvarna_schedule_to_calendar(
    calendar_list: list[Calendar],
) -> dict[str, MowerAttributes]:
    """Convert the schedule to an sorted list of calendar events."""
    eventlist = []
    for task_dict in calendar_list:
        calendar_dataclass = Calendar.from_dict(task_dict)
        event = ConvertScheduleToCalendar(calendar_dataclass)
        eventlist.append(event.make_event())
    eventlist.sort(key=operator.attrgetter("start"))
    return eventlist


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
