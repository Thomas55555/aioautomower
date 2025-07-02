"""Models for Husqvarna Automower data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime  # noqa:TC003
from enum import StrEnum

from mashumaro import DataClassDictMixin, field_options

from .model_mower import (
    ERRORCODES,
    snake_case,
)
from .utils import convert_timestamp_to_aware_datetime


class Severity(StrEnum):
    """Severity level of a diagnostic message."""

    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    SW = "sw"
    UNKNOWN = "unknown"


@dataclass
class Message(DataClassDictMixin):
    """Single diagnostic or error message."""

    time: datetime | None = field(
        metadata=field_options(
            deserialize=convert_timestamp_to_aware_datetime,
            alias="time",
        ),
    )
    code: str | None = field(
        metadata=field_options(
            deserialize=lambda x: None if x == 0 else snake_case(ERRORCODES.get(x)),
            alias="code",
        )
    )
    severity: Severity = field(
        metadata=field_options(
            alias="severity",
            deserialize=lambda x: Severity(x.lower()),
        )
    )
    latitude: float = field(metadata=field_options(alias="latitude"))
    longitude: float = field(metadata=field_options(alias="longitude"))
