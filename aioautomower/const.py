"""The constants for aioautomower."""
AUTH_API_BASE_URL = "https://api.authentication.husqvarnagroup.dev/v1"
AUTH_API_URL = f"{AUTH_API_BASE_URL}/oauth2/token"
AUTH_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
}
AUTH_HEADER_FMT = "Bearer {}"
EVENT_TYPES = [
    "status-event",
    "positions-event",
    "settings-event",
]
HUSQVARNA_URL = "https://developer.husqvarnagroup.cloud/"
MARGIN_TIME = 60.0  # Token is typically valid for 24h, request a new one some time before its expiration to avoid glitches.
MIN_SLEEP_TIME = 600.0  # Avoid hammering
MOWER_API_BASE_URL = "https://api.amc.husqvarna.dev/v1/mowers/"
REST_POLL_CYCLE = 300.0
TOKEN_URL = f"{AUTH_API_BASE_URL}/token"
USER_URL = f"{AUTH_API_BASE_URL}/users"
WS_STATUS_UPDATE_CYLE = 840.0
WS_TOLERANCE_TIME = 20.0
WS_URL = "wss://ws.openapi.husqvarna.dev/v1"
