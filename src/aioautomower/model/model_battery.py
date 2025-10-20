"""Models for Automower Connect API - Battery."""

from dataclasses import dataclass, field
from datetime import timedelta

from mashumaro import DataClassDictMixin, field_options


@dataclass
class Battery(DataClassDictMixin):
    """Information about the battery in the Automower."""

    battery_percent: int = field(metadata=field_options(alias="batteryPercent"))
    remaining_charging_time: timedelta | None = field(
        metadata=field_options(
            alias="remainingChargingTime",
            deserialize=lambda x: None if x == 0 else timedelta(seconds=x),
        ),
    )
