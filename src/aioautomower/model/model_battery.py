"""Models for Automower Connect API - Battery."""

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin, field_options


@dataclass
class Battery(DataClassDictMixin):
    """Information about the battery in the Automower."""

    battery_percent: int = field(metadata=field_options(alias="batteryPercent"))
