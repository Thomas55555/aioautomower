"""Models for Automower Connect API - Planner."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from mashumaro import DataClassDictMixin, field_options

from .utils import convert_timestamp_to_aware_datetime


class Actions(StrEnum):
    """Actions in the planner of lawn mower."""

    NOT_ACTIVE = "not_active"
    FORCE_PARK = "force_park"
    FORCE_MOW = "force_mow"


@dataclass
class Override(DataClassDictMixin):
    """DataClass for Override values."""

    action: Actions = field(
        metadata=field_options(deserialize=lambda x: Actions(x.lower()))
    )


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


class ExternalReasons(StrEnum):
    """External reasons for restrictions."""

    GOOGLE_ASSISTANT = "google_assistant"
    AMAZON_ALEXA = "amazon_alexa"
    HOME_ASSISTANT = "home_assistant"
    IFTT = "iftt"
    IFTT_WILDLIFE = "iftt_wildlife"
    IFTT_FROST_AND_RAIN = "iftt_frost_and_rain"
    IFTT_CALENDAR_CONNECTION = "iftt_calendar_connection"
    GARDENA_SMART_SYSTEM = "gardena_smart_system"
    IFTT_APPLETS = "iftt_applets"
    DEVELOPER_PORTAL = "developer_portal"


def resolve_external_reason(reason_id: int) -> ExternalReasons | None:  # noqa: C901
    """Resolve the external reason based on the reason ID."""
    if 1000 <= reason_id <= 1999:
        return ExternalReasons.GOOGLE_ASSISTANT
    if 2000 <= reason_id <= 2999:
        return ExternalReasons.AMAZON_ALEXA
    if 3000 <= reason_id <= 3999:
        return ExternalReasons.HOME_ASSISTANT
    if reason_id == 4000:
        return ExternalReasons.IFTT_WILDLIFE
    if reason_id == 4001:
        return ExternalReasons.IFTT_FROST_AND_RAIN
    if reason_id == 4002:
        return ExternalReasons.IFTT_CALENDAR_CONNECTION
    if 4003 <= reason_id <= 4999:
        return ExternalReasons.IFTT
    if 5000 <= reason_id <= 5999:
        return ExternalReasons.IFTT
    if 100000 <= reason_id <= 199999:
        return ExternalReasons.IFTT_APPLETS
    if 200000 <= reason_id <= 299999:
        return ExternalReasons.DEVELOPER_PORTAL
    return None


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
    restricted_reason: RestrictedReasons = field(
        metadata=field_options(
            deserialize=lambda x: RestrictedReasons(x.lower()),
            alias="restrictedReason",
        )
    )
    external_reason: ExternalReasons | None = field(
        metadata=field_options(
            alias="externalReason",
            deserialize=lambda x: resolve_external_reason(int(x)),
        ),
        default=None,
    )
