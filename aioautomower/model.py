"""Models for Husqvarna Automower data."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, StrEnum

from mashumaro import DataClassDictMixin, field_options


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
    error_code_dateteime: datetime | None = field(
        metadata=field_options(
            deserialize=lambda x: (
                None if x == 0 else datetime.fromtimestamp(x / 1000).astimezone()
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
class Tasks(DataClassDictMixin):
    """DataClass for Task values."""

    tasks: list[Calendar]


@dataclass
class Override(DataClassDictMixin):
    """DataClass for Override values."""

    action: str


@dataclass
class Planner(DataClassDictMixin):
    """DataClass for Planner values."""

    next_start_dateteime: datetime | None = field(
        metadata=field_options(
            deserialize=lambda x: (
                None if x == 0 else datetime.fromtimestamp(x / 1000).astimezone()
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
    cutting_blade_usage_time: int = field(
        metadata=field_options(alias="cuttingBladeUsageTime"), default=0
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
        metadata=field_options(alias="cuttingHeight"), default=0
    )
    stay_out_zones: StayOutZones = field(
        metadata=field_options(alias="stayOutZones"), default=None
    )

    work_areas: list[WorkAreas] = field(
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
