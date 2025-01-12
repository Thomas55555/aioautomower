"""Models for Automower Connect API - Capabilities."""

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin, field_options


@dataclass
class Capabilities(DataClassDictMixin):
    """Information about what capabilities the Automower has."""

    can_confirm_error: bool = field(metadata=field_options(alias="canConfirmError"))
    headlights: bool
    position: bool
    stay_out_zones: bool = field(metadata=field_options(alias="stayOutZones"))
    work_areas: bool = field(metadata=field_options(alias="workAreas"))
