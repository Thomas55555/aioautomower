"""Models for Automower Connect API messages."""

from typing import Literal, TypedDict


class Message(TypedDict):
    """A single message containing error or warning information."""

    time: int
    code: int
    severity: Literal["FATAL", "ERROR", "WARNING", "INFO", "DEBUG", "SW", "UNKNOWN"]
    latitude: float
    longitude: float


class MesssageAttributes(TypedDict):
    """Container for a list of diagnostic messages."""

    messages: list[Message]


class Data(TypedDict):
    """Root data object containing type, ID, and attributes."""

    type: Literal["messages"]
    id: Literal["messages"]
    attributes: MesssageAttributes | None


class MessageResponse(TypedDict):
    """Top-level response structure for messages."""

    data: Data
