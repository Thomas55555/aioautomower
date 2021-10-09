"""The constants for aioautomower."""
# Base component constants
HUSQVARNA_URL = "https://developer.husqvarnagroup.cloud/"
AUTH_API_URL = "https://api.authentication.husqvarnagroup.dev/v1/oauth2/token"
TOKEN_URL = "https://api.authentication.husqvarnagroup.dev/v1/token"
AUTH_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
}

MOWER_API_BASE_URL = "https://api.amc.husqvarna.dev/v1/mowers/"
WS_URL = "wss://ws.openapi.husqvarna.dev/v1"
AUTH_HEADER_FMT = "Bearer {}"
