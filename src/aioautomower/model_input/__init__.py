"""Models for inputs from the Autcomower Connect API."""

from .model_event import (
    CalendarAttributes,
    CuttingHeightAttributes,
    GenericEventData,
    HeadLightAttributes,
    MessageAttributes,
    PositionAttributes,
)
from .model_message import Message, MessageResponse
from .model_rest import (
    MowerDataAttributes,
    MowerDataItem,
    MowerDataResponse,
)

__all__ = [
    "CalendarAttributes",
    "CuttingHeightAttributes",
    "GenericEventData",
    "HeadLightAttributes",
    "Message",
    "MessageAttributes",
    "MessageResponse",
    "MowerDataAttributes",
    "MowerDataItem",
    "MowerDataResponse",
    "PositionAttributes",
]
