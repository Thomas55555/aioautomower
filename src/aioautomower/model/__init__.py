"""Provide a model for the Automower Connect API."""

from .battery import Battery
from .capabilities import Capabilities
from .model import (
    WEEKDAYS,
    WEEKDAYS_TO_ICAL,
    Actions,
    AutomowerCalendarEvent,
    Calendar,
    ConvertScheduleToCalendar,
    DurationSerializationStrategy,
    Headlight,
    HeadlightModes,
    Metadata,
    MowerActivities,
    MowerAttributes,
    MowerData,
    MowerList,
    MowerModes,
    MowerStates,
    Override,
    Planner,
    Positions,
    RestrictedReasons,
    Settings,
    Statistics,
    StayOutZones,
    Tasks,
    TimeSerializationStrategy,
    WorkArea,
    Zone,
    generate_work_area_dict,
    generate_work_area_names_list,
    get_work_area_name,
    make_name_string,
)
from .mower import (
    Mower,
    error_key_dict,
    error_key_list,
)
from .system import System
from .token import (
    JWT,
    User,
)

__all__ = [
    "Actions",
    "AutomowerCalendarEvent",
    "Battery",
    "Calendar",
    "Capabilities",
    "convert_timestamp_to_aware_datetime",
    "ConvertScheduleToCalendar",
    "DurationSerializationStrategy",
    "error_key_dict",
    "error_key_list",
    "generate_work_area_dict",
    "generate_work_area_names_list",
    "get_work_area_name",
    "Headlight",
    "HeadlightModes",
    "JWT",
    "make_name_string",
    "Metadata",
    "Mower",
    "MowerActivities",
    "MowerAttributes",
    "MowerData",
    "MowerList",
    "MowerModes",
    "MowerStates",
    "Override",
    "Planner",
    "Positions",
    "RestrictedReasons",
    "Settings",
    "Statistics",
    "StayOutZones",
    "System",
    "Tasks",
    "TimeSerializationStrategy",
    "User",
    "WEEKDAYS_TO_ICAL",
    "WEEKDAYS",
    "WorkArea",
    "Zone",
]
