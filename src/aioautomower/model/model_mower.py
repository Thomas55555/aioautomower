"""Models for Automower Connect API - Mower."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from re import sub

from mashumaro import DataClassDictMixin, field_options

from .utils import convert_timestamp_to_aware_datetime

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


@dataclass
class Mower(DataClassDictMixin):
    """Information about the mowers current status."""

    mode: str = field(metadata=field_options(deserialize=lambda x: x.lower()))
    activity: str = field(metadata=field_options(deserialize=lambda x: x.lower()))
    state: str = field(metadata=field_options(deserialize=lambda x: x.lower()))
    error_code: int = field(metadata=field_options(alias="errorCode"))
    error_key: str | None = field(
        metadata=field_options(
            deserialize=lambda x: None if x == 0 else snake_case(ERRORCODES.get(x)),
            alias="errorCode",
        )
    )
    error_datetime: datetime | None = field(
        metadata=field_options(
            deserialize=convert_timestamp_to_aware_datetime,
            alias="errorCodeTimestamp",
        ),
    )
    inactive_reason: str = field(
        metadata=field_options(deserialize=lambda x: x.lower(), alias="inactiveReason"),
    )
    is_error_confirmable: bool = field(
        metadata=field_options(alias="isErrorConfirmable"), default=False
    )
    work_area_id: int | None = field(
        metadata=field_options(alias="workAreaId"), default=None
    )
    work_area_name: str | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Initialize work_area_name to None for later external setting."""
        self.work_area_name = None


def snake_case(string: str | None) -> str:
    """Convert an error text to snake case."""
    if string is None:
        raise TypeError
    return "_".join(
        sub(
            "([A-Z][a-z][,]+)",
            r" \1",
            sub(
                "([A-Z]+)",
                r" \1",
                string.replace("-", " ")
                .replace(",", "")
                .replace(".", "")
                .replace("!", ""),
            ),
        ).split()
    ).lower()


def error_key_list() -> list[str]:
    """Create a list with all possible error keys."""
    codes = [snake_case(error_text) for error_text in ERRORCODES.values()]
    return sorted(codes)


def error_key_dict() -> dict[str, str]:
    """Create a dictionary with error keys and a human friendly text."""
    codes = {}
    for error_text in ERRORCODES.values():
        codes[snake_case(error_text)] = error_text
    return codes


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
