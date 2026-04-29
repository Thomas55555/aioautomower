"""Models for Automower Connect API - WorkAreas."""

import warnings
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from mashumaro import DataClassDictMixin, field_options

from .utils import convert_timestamp_to_aware_datetime


class WorkAreaType(StrEnum):
    """Types of work areas."""

    RANDOM = "random"
    SYSTEMATIC = "systematic"


def __getattr__(name: str) -> object:
    """Provide a deprecated alias for the previous, generic ``Type`` name.

    Accessing ``aioautomower.model.model_work_areas.Type`` keeps working but
    emits a DeprecationWarning so downstream consumers can migrate.
    """
    if name == "Type":
        warnings.warn(
            "aioautomower.model.model_work_areas.Type is deprecated, "
            "use WorkAreaType instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return WorkAreaType
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


@dataclass
class WorkArea(DataClassDictMixin):
    """DataClass for WorkArea values."""

    name: str = field(
        metadata=field_options(
            deserialize=lambda x: "my_lawn" if x == "" else x,
        ),
    )
    type: WorkAreaType = field(
        metadata=field_options(
            deserialize=lambda x: WorkAreaType(x.lower()), alias="type"
        )
    )
    cutting_height: int = field(metadata=field_options(alias="cuttingHeight"))
    use_global_cutting_height: bool = field(
        metadata=field_options(alias="useGlobalCuttingHeight")
    )
    enabled: bool = field(default=False)
    orientation: int | None = field(default=None)
    orientation_shift: int | None = field(
        metadata=field_options(alias="orientationShift"), default=None
    )
    current_orientation: int | None = field(
        metadata=field_options(alias="currentOrientation"), default=None
    )
    progress: int | None = field(default=None)
    last_time_completed: datetime | None = field(
        metadata=field_options(
            deserialize=convert_timestamp_to_aware_datetime,
            alias="lastTimeCompleted",
        ),
        default=None,
    )
    last_time_abandoned: datetime | None = field(
        metadata=field_options(
            deserialize=convert_timestamp_to_aware_datetime,
            alias="lastTimeAbandoned",
        ),
        default=None,
    )
