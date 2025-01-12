"""Models for Automower Connect API - Settings."""

from dataclasses import dataclass, field
from enum import StrEnum

from mashumaro import DataClassDictMixin, field_options


@dataclass
class Headlight(DataClassDictMixin):
    """DataClass for Headlight values."""

    mode: str | None = field(
        metadata=field_options(deserialize=lambda x: x.lower()), default=None
    )


@dataclass
class Settings(DataClassDictMixin):
    """DataClass for Settings values."""

    headlight: Headlight
    cutting_height: int | None = field(
        metadata=field_options(alias="cuttingHeight"), default=None
    )


class HeadlightModes(StrEnum):
    """Headlight modes of a lawn mower."""

    ALWAYS_ON = "always_on"
    ALWAYS_OFF = "always_off"
    EVENING_ONLY = "evening_only"
    EVENING_AND_NIGHT = "evening_and_night"
