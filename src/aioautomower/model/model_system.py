"""Models for Automower Connect API - System."""

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin, field_options


@dataclass
class System(DataClassDictMixin):
    """System information about a Automower."""

    name: str
    model: str
    serial_number: str = field(metadata=field_options(alias="serialNumber"))
