"""Models for Automower Connect API - Metadata."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from mashumaro import DataClassDictMixin, field_options


@dataclass
class Metadata(DataClassDictMixin):
    """DataClass for Metadata values."""

    connected: bool
    status_dateteime: datetime = field(
        metadata=field_options(
            deserialize=lambda x: (datetime.fromtimestamp(x / 1000, tz=UTC)),
            alias="statusTimestamp",
        ),
    )
