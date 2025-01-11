"""Models for Husqvarna Automower data."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum

from mashumaro import DataClassDictMixin, field_options

from .battery import Battery
from .calendar import Tasks
from .capabilities import Capabilities
from .metadata import Metadata
from .mower import Mower
from .planner import Planner
from .positions import Positions
from .system import System
from .utils import convert_timestamp_to_aware_datetime

_LOGGER = logging.getLogger(__name__)


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

    mode: str | None = field(
        metadata=field_options(deserialize=lambda x: x.lower()), default=None
    )


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
    last_time_completed: datetime | None = field(
        metadata=field_options(
            deserialize=convert_timestamp_to_aware_datetime,
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
    positions: list[Positions]
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

    ALWAYS_ON = "always_on"
    ALWAYS_OFF = "always_off"
    EVENING_ONLY = "evening_only"
    EVENING_AND_NIGHT = "evening_and_night"


class MowerStates(StrEnum):
    """Mower states of a lawn mower."""

    FATAL_ERROR = "fatal_error"
    ERROR = "error"
    ERROR_AT_POWER_UP = "error_at_power_up"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"
    STOPPED = "stopped"
    OFF = "off"
    PAUSED = "paused"
    IN_OPERATION = "in_operation"
    WAIT_UPDATING = "wait_updating"
    WAIT_POWER_UP = "wait_power_up"
    RESTRICTED = "restricted"


class MowerActivities(StrEnum):
    """Mower activities of a lawn mower."""

    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"
    MOWING = "mowing"
    GOING_HOME = "going_home"
    CHARGING = "charging"
    LEAVING = "leaving"
    PARKED_IN_CS = "parked_in_cs"
    STOPPED_IN_GARDEN = "stopped_in_garden"


class MowerModes(StrEnum):
    """Mower activities of a lawn mower."""

    MAIN_AREA = "main_area"
    DEMO = "demo"
    SECONDARY_AREA = "secondary_area"
    HOME = "home"
    UNKNOWN = "unknown"


class RestrictedReasons(StrEnum):
    """Restricted reasons in the planner of lawn mower."""

    NONE = "none"
    WEEK_SCHEDULE = "week_schedule"
    PARK_OVERRIDE = "park_override"
    SENSOR = "sensor"
    DAILY_LIMIT = "daily_limit"
    FOTA = "fota"
    FROST = "frost"
    ALL_WORK_AREAS_COMPLETED = "all_work_areas_completed"
    EXTERNAL = "external"
    NOT_APPLICABLE = "not_applicable"


class Actions(StrEnum):
    """Actions in the planner of lawn mower."""

    NOT_ACTIVE = "not_active"
    FORCE_PARK = "force_park"
    FORCE_MOW = "force_mow"


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

    NONE = "none"
    PLANNING = "planing"
    SEARCHING_FOR_SATELLITES = "searching_for_satellites"
