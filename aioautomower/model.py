"""Models for Husqvarna Automower data."""
from enum import Enum, StrEnum

from pydantic import BaseModel, Field


class User(BaseModel):
    """The content of the JWT."""

    first_name: str
    last_name: str
    custom_attributes: dict
    customer_id: str


class JWT(BaseModel):
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


class System(BaseModel):
    """System information about a Automower."""

    name: str
    model: str
    serial_number: int = Field(alias="serialNumber")


class Battery(BaseModel):
    """Information about the battery in the Automower."""

    battery_percent: int = Field(alias="batteryPercent")


class Capabilities(BaseModel):
    """Information about what capabilities the Automower has."""

    headlights: bool
    work_areas: bool = Field(alias="workAreas")
    position: bool
    stay_out_zones: bool = Field(alias="stayOutZones")


class Mower(BaseModel):
    """Information about the mowers current status."""

    mode: str
    activity: str
    state: str
    error_code: int = Field(alias="errorCode")
    error_code_timestamp: int = Field(alias="errorCodeTimestamp")


class Calendar(BaseModel):
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


class Tasks(BaseModel):
    """DataClass for Task values."""

    tasks: list[Calendar]


class Override(BaseModel):
    """DataClass for Override values."""

    action: str


class Planner(BaseModel):
    """DataClass for Planner values."""

    next_start_timestamp: int = Field(alias="nextStartTimestamp")
    override: Override
    restricted_reason: str = Field(alias="restrictedReason")


class Metadata(BaseModel):
    """DataClass for Metadata values."""

    connected: bool
    status_timestamp: int = Field(alias="statusTimestamp")


class Positions(BaseModel):
    """List of the GPS positions.

    Latest registered position is first in the
    array and the oldest last in the array.
    Max number of positions is 50 after
    that the latest position is removed
    from the array.
    """

    latitude: float
    longitude: float


class Statistics(BaseModel):
    """DataClass for Statistics values."""

    cutting_blade_usage_time: int  = Field(alias="cuttingBladeUsageTime", default=None)
    number_of_charging_cycles: int = Field(alias="numberOfChargingCycles")
    number_of_collisions: int = Field(alias="numberOfCollisions")
    total_charging_time: int = Field(alias="totalChargingTime")
    total_cutting_time: int = Field(alias="totalCuttingTime")
    total_drive_distance: int = Field(alias="totalDriveDistance")
    total_running_time: int = Field(alias="totalRunningTime")
    total_searching_time: int = Field(alias="totalSearchingTime")


class Headlight(BaseModel):
    """DataClass for Headlight values."""

    mode: str | None


class Zones(BaseModel):
    """DataClass for Zone values."""

    id: str = Field(alias="Id")
    name: str
    enabled: bool


class StayOutZones(BaseModel):
    """DataClass for StayOutZone values."""

    dirty: bool
    zones: list[Zones]


class WorkAreas(BaseModel):
    """DataClass for WorkAreas values."""

    work_area_id: int = Field(alias="workAreaId")
    name: str
    cutting_height: int = Field(alias="cuttingHeight")


class MowerAttributes(BaseModel):
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
    cutting_height: int = Field(alias="cuttingHeight", default=None)
    headlight: Headlight
    stay_out_zones: StayOutZones = Field(alias="stayOutZones", default=None)
    work_areas: WorkAreas = Field(alias="workAreas", default=None)


class MowerData(BaseModel):
    """DataClass for MowerData values."""

    type: str
    id: str
    attributes: MowerAttributes


class MowerList(BaseModel):
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
