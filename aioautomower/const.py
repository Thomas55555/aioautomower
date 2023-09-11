"""The constants for aioautomower."""
from enum import StrEnum, Enum

AUTH_API_BASE_URL = "https://api.authentication.husqvarnagroup.dev/v1"
AUTH_API_TOKEN_URL = f"{AUTH_API_BASE_URL}/oauth2/token"
AUTH_API_REVOKE_URL = f"{AUTH_API_BASE_URL}/oauth2/revoke"
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
REST_POLL_CYCLE = 300
REST_POLL_CYCLE_LE = 86400
TOKEN_URL = f"{AUTH_API_BASE_URL}/token"
USER_URL = f"{AUTH_API_BASE_URL}/users"
WS_STATUS_UPDATE_CYLE = 840.0
WS_TOLERANCE_TIME = 20.0
WS_URL = "wss://ws.openapi.husqvarna.dev/v1"


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
    GOOGLE_ASSISTANT = range(1000, 1999)
    AMAZON_ALEXA = range(2000, 2999)
    DEVELOPER_PORTAL = range(3000, 3999), range(200000, 299999)
    IFTT = 4000, range(4003, 4999)
    IFTT_WILDLIFE = 4001
    IFTT_FROST_AND_RAIN = 4002
    IFTT_CALENDAR_CONNECTION = 4003
    IFTT_APPLETS = range(100000, 199999)


ERRORCODES = {
    0: "Unexpected error",
    1: "Outside working area",
    2: "No loop signal",
    3: "Wrong loop signal",
    4: "Loop sensor problem, front",
    5: "Loop sensor problem, rear",
    6: "Loop sensor problem, left",
    7: "Loop sensor problem, right",
    8: "Wrong PIN code",
    9: "Trapped",
    10: "Upside down",
    11: "Low battery",
    12: "Empty battery",
    13: "No drive",
    14: "Mower lifted",
    15: "Lifted",
    16: "Stuck in charging station",
    17: "Charging station blocked",
    18: "Collision sensor problem, rear",
    19: "Collision sensor problem, front",
    20: "Wheel motor blocked, right",
    21: "Wheel motor blocked, left",
    22: "Wheel drive problem, right",
    23: "Wheel drive problem, left",
    24: "Cutting system blocked",
    25: "Cutting system blocked",
    26: "Invalid sub-device combination",
    27: "Settings restored",
    28: "Memory circuit problem",
    29: "Slope too steep",
    30: "Charging system problem",
    31: "STOP button problem",
    32: "Tilt sensor problem",
    33: "Mower tilted",
    34: "Cutting stopped - slope too steep",
    35: "Wheel motor overloaded, right",
    36: "Wheel motor overloaded, left",
    37: "Charging current too high",
    38: "Electronic problem",
    39: "Cutting motor problem",
    40: "Limited cutting height range",
    41: "Unexpected cutting height adj",
    42: "Limited cutting height range",
    43: "Cutting height problem, drive",
    44: "Cutting height problem, curr",
    45: "Cutting height problem, dir",
    46: "Cutting height blocked",
    47: "Cutting height problem",
    48: "No response from charger",
    49: "Ultrasonic problem",
    50: "Guide 1 not found",
    51: "Guide 2 not found",
    52: "Guide 3 not found",
    53: "GPS navigation problem",
    54: "Weak GPS signal",
    55: "Difficult finding home",
    56: "Guide calibration accomplished",
    57: "Guide calibration failed",
    58: "Temporary battery problem",
    59: "Temporary battery problem",
    60: "Temporary battery problem",
    61: "Temporary battery problem",
    62: "Battery restriction due to ambient temperature",
    63: "Temporary battery problem",
    64: "Temporary battery problem",
    65: "Temporary battery problem",
    66: "Battery problem",
    67: "Battery problem",
    68: "Temporary battery problem",
    69: "Alarm! Mower switched off",
    70: "Alarm! Mower stopped",
    71: "Alarm! Mower lifted",
    72: "Alarm! Mower tilted",
    73: "Alarm! Mower in motion",
    74: "Alarm! Outside geofence",
    75: "Connection changed",
    76: "Connection NOT changed",
    77: "Com board not available",
    78: "Slipped - Mower has Slipped.Situation not solved with moving pattern",
    79: "Invalid battery combination - Invalid combination of different battery types.",
    80: "Cutting system imbalance    Warning",
    81: "Safety function faulty",
    82: "Wheel motor blocked, rear right",
    83: "Wheel motor blocked, rear left",
    84: "Wheel drive problem, rear right",
    85: "Wheel drive problem, rear left",
    86: "Wheel motor overloaded, rear right",
    87: "Wheel motor overloaded, rear left",
    88: "Angular sensor problem",
    89: "Invalid system configuration",
    90: "No power in charging station",
    91: "Switch cord problem",
    92: "Work area not valid",
    93: "No accurate position from satellites",
    94: "Reference station communication problem",
    95: "Folding sensor activated",
    96: "Right brush motor overloaded",
    97: "Left brush motor overloaded",
    98: "Ultrasonic Sensor 1 defect",
    99: "Ultrasonic Sensor 2 defect",
    100: "Ultrasonic Sensor 3 defect",
    101: "Ultrasonic Sensor 4 defect",
    102: "Cutting drive motor 1 defect",
    103: "Cutting drive motor 2 defect",
    104: "Cutting drive motor 3 defect",
    105: "Lift Sensor defect",
    106: "Collision sensor defect",
    107: "Docking sensor defect",
    108: "Folding cutting deck sensor defect",
    109: "Loop sensor defect",
    110: "Collision sensor error",
    111: "No confirmed position",
    112: "Cutting system major imbalance",
    113: "Complex working area",
    114: "Too high discharge current",
    115: "Too high internal current",
    116: "High charging power loss",
    117: "High internal power loss",
    118: "Charging system problem",
    119: "Zone generator problem",
    120: "Internal voltage error",
    121: "High internal temperature",
    122: "CAN error",
    123: "Destination not reachable",
    701: "Connectivity problem",
    702: "Connectivity settings restored",
    703: "Connectivity problem",
    704: "Connectivity problem",
    705: "Connectivity problem",
    706: "Poor signal quality",
    707: "SIM card requires PIN",
    708: "SIM card locked",
    709: "SIM card not found",
    710: "SIM card locked",
    711: "SIM card locked",
    712: "SIM card locked",
    713: "Geofence problem",
    714: "Geofence problem",
    715: "Connectivity problem",
    716: "Connectivity problem",
    717: "SMS could not be sent",
    724: "Communication circuit board SW must be updated",
}
