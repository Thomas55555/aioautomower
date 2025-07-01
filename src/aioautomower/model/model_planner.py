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
    IFTTT_CALENDAR_CONNECTION = "ifttt_calendar_connection"
    IFTTT = "ifttt"
    SMART_ROUTINE_RAIN_GUARD = "smart_routine_rain_guard"
    SMART_ROUTINE_WILDLIFE_PROTECTION = "smart_routine_wildlife_protection"
    SMART_ROUTINE_FROST_GUARD = "smart_routine_frost_guard"
    SMART_ROUTINE = "smart_routine"
    GARDENA_SMART_SYSTEM = "gardena_smart_system"
    IFTTT_APPLETS = "ifttt_applets"
    DEVELOPER_PORTAL = "developer_portal"


def resolve_external_reason(reason_id: int) -> ExternalReasons | None:  # noqa: C901
    """Resolve the external reason based on the reason ID."""
    if 1000 <= reason_id <= 1999:
        return ExternalReasons.GOOGLE_ASSISTANT
    if 2000 <= reason_id <= 2999:
        return ExternalReasons.AMAZON_ALEXA
    if 3000 <= reason_id <= 3999:
        return ExternalReasons.HOME_ASSISTANT
    if reason_id == 4002:
        return ExternalReasons.IFTTT_CALENDAR_CONNECTION
    if 4000 <= reason_id <= 4999:
        return ExternalReasons.IFTTT
    if 5000 <= reason_id <= 5999:
        return ExternalReasons.GARDENA_SMART_SYSTEM
    if reason_id == 6000:
        return ExternalReasons.SMART_ROUTINE_RAIN_GUARD
    if reason_id == 6001:
        return ExternalReasons.SMART_ROUTINE_FROST_GUARD
    if reason_id == 6500:
        return ExternalReasons.SMART_ROUTINE_WILDLIFE_PROTECTION
    if 6000 <= reason_id <= 6999:
        return ExternalReasons.SMART_ROUTINE
    if 100000 <= reason_id <= 199999:
        return ExternalReasons.IFTTT_APPLETS
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
