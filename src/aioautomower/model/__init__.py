"""Provide a model for the Automower Connect API."""

from .model import (
    WEEKDAYS,
    WEEKDAYS_TO_ICAL,
    Actions,
    AutomowerCalendarEvent,
    Battery,
    Calendar,
    Capabilities,
    ConvertScheduleToCalendar,
    DurationSerializationStrategy,
    Headlight,
    HeadlightModes,
    Metadata,
    Mower,
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
    System,
    Tasks,
    TimeSerializationStrategy,
    WorkArea,
    Zone,
    convert_timestamp_to_aware_datetime,
    generate_work_area_dict,
    generate_work_area_names_list,
    get_work_area_name,
    make_name_string,
    snake_case,
)
from .token_model import (
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
    "snake_case",
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
