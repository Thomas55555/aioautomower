"""Models for Automower Connect API - Statistics."""

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin, field_options


@dataclass
class Statistics(DataClassDictMixin):
    """DataClass for Statistics values."""

    cutting_blade_usage_time: int | None = field(
        metadata=field_options(alias="cuttingBladeUsageTime"), default=None
    )
    number_of_charging_cycles: int | None = field(
        metadata=field_options(alias="numberOfChargingCycles"), default=None
    )
    number_of_collisions: int | None = field(
        metadata=field_options(alias="numberOfCollisions"), default=None
    )
    total_charging_time: int | None = field(
        metadata=field_options(alias="totalChargingTime"), default=None
    )
    total_cutting_time: int | None = field(
        metadata=field_options(alias="totalCuttingTime"), default=None
    )
    total_drive_distance: int | None = field(
        metadata=field_options(alias="totalDriveDistance"), default=None
    )
    total_running_time: int | None = field(
        metadata=field_options(alias="totalRunningTime"), default=None
    )
    total_searching_time: int | None = field(
        metadata=field_options(alias="totalSearchingTime"), default=None
    )
