"""Models for Automower Connect API - Planner."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum

from mashumaro import DataClassDictMixin, field_options

from .utils import convert_timestamp_to_aware_datetime


@dataclass
class Override(DataClassDictMixin):
    """DataClass for Override values."""

    action: str = field(metadata=field_options(deserialize=lambda x: x.lower()))


@dataclass
class Planner(DataClassDictMixin):
    """DataClass for Planner values."""

    next_start_datetime: datetime | None = field(
        metadata=field_options(
            deserialize=convert_timestamp_to_aware_datetime,
            alias="nextStartTimestamp",
        ),
    )
    override: Override
    restricted_reason: str = field(
        metadata=field_options(
            deserialize=lambda x: x.lower(), alias="restrictedReason"
        )
    )


class Actions(StrEnum):
    """Actions in the planner of lawn mower."""

    NOT_ACTIVE = "not_active"
    FORCE_PARK = "force_park"
    FORCE_MOW = "force_mow"


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
