"""Models for Automower Connect API - Statistics."""

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin, field_options


@dataclass
class Statistics(DataClassDictMixin):
    """DataClass for Statistics values."""

    cutting_blade_usage_time: int | None = field(
        metadata=field_options(alias="cuttingBladeUsageTime"), default=None
    )
    """The number of seconds since the last reset of the cutting blade usage counter."""

    downtime: int | None = field(metadata=field_options(alias="downTime"), default=None)
    """The number of seconds the mower has been disconnected from the cloud.
    Not available on all models."""

    number_of_charging_cycles: int | None = field(
        metadata=field_options(alias="numberOfChargingCycles"), default=None
    )
    """Number of charging cycles."""

    number_of_collisions: int | None = field(
        metadata=field_options(alias="numberOfCollisions"), default=None
    )
    """The total number of collisions."""

    total_charging_time: int | None = field(
        metadata=field_options(alias="totalChargingTime"), default=None
    )
    """Total charging time in seconds."""

    total_cutting_time: int | None = field(
        metadata=field_options(alias="totalCuttingTime"), default=None
    )
    """Total cutting time in seconds."""

    total_drive_distance: int | None = field(
        metadata=field_options(alias="totalDriveDistance"), default=None
    )
    """Total drive distance in meters. It's a calculated value based on totalRunningTime
     multiply with average speed for the mower depending on the model."""

    total_running_time: int | None = field(
        metadata=field_options(alias="totalRunningTime"), default=None
    )
    """The total running time in seconds. (the wheel motors have been running)"""

    total_searching_time: int | None = field(
        metadata=field_options(alias="totalSearchingTime"), default=None
    )
    """The total searching time in seconds."""

    uptime: int | None = field(metadata=field_options(alias="upTime"), default=None)
    """The number of seconds the mower has been connected to the cloud."""
