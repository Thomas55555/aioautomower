"""Models for Automower Connect API websocket events."""

from typing import Any, NotRequired, TypedDict

from .model_message import Message


class GenericEventData(TypedDict):
    """Generic websocket event."""

    id: str
    type: str
    attributes: Any


class CalendarTask(TypedDict):
    """Single calendar task entry."""

    start: int
    duration: int
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool
    workAreaId: NotRequired[int]


class CalendarData(TypedDict):
    """Calendar object with task list."""

    tasks: list[CalendarTask]


class CalendarAttributes(TypedDict):
    """Calendar event attributes."""

    calendar: CalendarData


class CuttingHeight(TypedDict):
    """Cutting height information."""

    height: int


class CuttingHeightAttributes(TypedDict):
    """Cutting height attributes."""

    cuttingHeight: CuttingHeight


class MessageAttributes(TypedDict):
    """Position attributes."""

    message: Message


class Position(TypedDict):
    """Position information."""

    latitude: float
    longitude: float


class PositionAttributes(TypedDict):
    """Position attributes."""

    position: Position


class HeadLightAttributes(TypedDict):
    """Head light attributes."""

    headLight: dict[str, str]
