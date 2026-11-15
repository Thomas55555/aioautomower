"""Models for Automower Connect API - System."""

from dataclasses import dataclass, field
from datetime import date

from mashumaro import DataClassDictMixin, field_options

from .utils import decode_manufacture_date


@dataclass
class System(DataClassDictMixin):
    """System information about a Automower."""

    name: str
    model: str
    serial_number: str = field(metadata=field_options(alias="serialNumber"))
    manufacture_date: date | None = field(
        metadata=field_options(
            alias="serialNumber",
            deserialize=decode_manufacture_date,
        ),
        default=None,
    )
