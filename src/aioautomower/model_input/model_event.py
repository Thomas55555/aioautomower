"""Models for Automower Connect API websocket events."""

from typing import Any, TypedDict

from .model_message import Message


class GenericEventData(TypedDict):
    """Generic websocket event."""

    id: str
    type: str
    attributes: Any


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

    headlights: dict[str, str]
