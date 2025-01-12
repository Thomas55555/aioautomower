"""Models for Automower Connect API - StayOutZones."""

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin, field_options


@dataclass
class Zone(DataClassDictMixin):
    """DataClass for Zone values."""

    name: str
    enabled: bool


@dataclass
class StayOutZones(DataClassDictMixin):
    """DataClass for StayOutZones values."""

    dirty: bool
    zones: dict[str, Zone] = field(
        metadata=field_options(
            deserialize=lambda zone_list: {
                zone["id"]: Zone.from_dict(zone) for zone in zone_list
            },
        ),
    )
