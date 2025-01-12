"""Models for Automower Connect API - WorkAreas."""

from dataclasses import dataclass, field
from datetime import datetime

from mashumaro import DataClassDictMixin, field_options

from .utils import convert_timestamp_to_aware_datetime


@dataclass
class WorkArea(DataClassDictMixin):
    """DataClass for WorkArea values."""

    name: str = field(
        metadata=field_options(
            deserialize=lambda x: "my_lawn" if x == "" else x,
        ),
    )
    cutting_height: int = field(metadata=field_options(alias="cuttingHeight"))
    enabled: bool = field(default=False)
    progress: int | None = field(default=None)
    last_time_completed: datetime | None = field(
        metadata=field_options(
            deserialize=convert_timestamp_to_aware_datetime,
            alias="lastTimeCompleted",
        ),
        default=None,
    )
