"""The constants for aioautomower."""

from enum import IntEnum, StrEnum

API_BASE_URL = "https://api.amc.husqvarna.dev/v1"
AUTH_API_BASE_URL = "https://api.authentication.husqvarnagroup.dev/v1"
AUTH_API_TOKEN_URL = f"{AUTH_API_BASE_URL}/oauth2/token"
AUTH_API_REVOKE_URL = f"{AUTH_API_BASE_URL}/oauth2/revoke"
AUTH_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
}
AUTH_HEADER_FMT = "Bearer {}"
HUSQVARNA_URL = "https://developer.husqvarnagroup.cloud/"
REST_POLL_CYCLE = 300
TOKEN_URL = f"{AUTH_API_BASE_URL}/token"
USER_URL = f"{AUTH_API_BASE_URL}/users"
WS_URL = "wss://ws.openapi.husqvarna.dev/v1"


class EventTypesV2(StrEnum):
    """Websocket events from websocket V2."""

    BATTERY = "battery-event-v2"
    CALENDAR = "calendar-event-v2"
    CUTTING_HEIGHT = "cuttingHeight-event-v2"
    HEADLIGHTS = "headlights-event-v2"
    MESSAGES = "message-event-v2"
    MOWER = "mower-event-v2"
    PLANNER = "planner-event-v2"
    POSITIONS = "position-event-v2"


class DayOfWeek(IntEnum):
    """Day of the week."""

    SUNDAY = 0
    """Sunday."""

    MONDAY = 1
    """Monday."""

    TUESDAY = 2
    """Tuesday."""

    WEDNESDAY = 3
    """Wednesday."""

    THURSDAY = 4
    """Thursday."""

    FRIDAY = 5
    """Friday."""

    SATURDAY = 6
    """Saturday."""


class ProgramFrequency(IntEnum):
    """Program frequency."""

    DAILY = 0
    """A daily schedule with every days of the week."""

    WEEKLY = 1
    """A schedule that cycles every N weeks."""
