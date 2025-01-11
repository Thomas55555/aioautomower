"""Models for Automower Connect API - Planner."""

from dataclasses import dataclass, field
from datetime import datetime

from mashumaro import DataClassDictMixin, field_options

from .utils import convert_timestamp_to_aware_datetime


@dataclass
class Override(DataClassDictMixin):
    """DataClass for Override values."""

    action: str = field(metadata=field_options(deserialize=lambda x: x.lower()))


@dataclass
class Planner(DataClassDictMixin):
    """DataClass for Planner values."""

    next_start_datetime: datetime | None = field(
        metadata=field_options(
            deserialize=convert_timestamp_to_aware_datetime,
            alias="nextStartTimestamp",
        ),
    )
    override: Override
    restricted_reason: str = field(
        metadata=field_options(
            deserialize=lambda x: x.lower(), alias="restrictedReason"
        )
    )
