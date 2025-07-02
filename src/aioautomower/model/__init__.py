"""Provide a model for the Automower Connect API."""

from .model import (
    MowerAttributes,
    MowerData,
    MowerDictionary,
    MowerList,
    generate_work_area_dict,
    generate_work_area_names_list,
    get_work_area_name,
)
from .model_battery import Battery
from .model_calendar import (
    WEEKDAYS,
    WEEKDAYS_TO_ICAL,
    AutomowerCalendarEvent,
    Calendar,
    ConvertScheduleToCalendar,
    DurationSerializationStrategy,
    Tasks,
    TimeSerializationStrategy,
    make_name_string,
)
from .model_capabilities import Capabilities
from .model_message import Message, Severity
from .model_metadata import Metadata
from .model_mower import (
    InactiveReasons,
    Mower,
    MowerActivities,
    MowerModes,
    MowerStates,
    error_key_dict,
    error_key_list,
)
from .model_planner import (
    Actions,
    ExternalReasons,
    Override,
    Planner,
    RestrictedReasons,
)
from .model_positions import (
    Positions,
)
from .model_settings import (
    Headlight,
    HeadlightModes,
)
from .model_stay_out_zones import StayOutZones, Zone
from .model_system import System
from .model_token import (
    JWT,
    User,
)
from .model_work_areas import WorkArea

__all__ = [
    "JWT",
    "WEEKDAYS",
    "WEEKDAYS_TO_ICAL",
    "Actions",
    "AutomowerCalendarEvent",
    "Battery",
    "Calendar",
    "Capabilities",
    "ConvertScheduleToCalendar",
    "DurationSerializationStrategy",
    "ExternalReasons",
    "Headlight",
    "HeadlightModes",
    "InactiveReasons",
    "Message",
    "Metadata",
    "Mower",
    "MowerActivities",
    "MowerAttributes",
    "MowerData",
    "MowerDictionary",
    "MowerList",
    "MowerModes",
    "MowerStates",
    "Override",
    "Planner",
    "Positions",
    "RestrictedReasons",
    "Settings",
    "Severity",
    "Statistics",
    "StayOutZones",
    "System",
    "Tasks",
    "TimeSerializationStrategy",
    "User",
    "WorkArea",
    "Zone",
    "convert_timestamp_to_aware_datetime",
    "error_key_dict",
    "error_key_list",
    "generate_work_area_dict",
    "generate_work_area_names_list",
    "get_work_area_name",
    "make_name_string",
]
