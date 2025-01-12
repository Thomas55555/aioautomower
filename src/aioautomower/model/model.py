"""Models for Husqvarna Automower data."""

import logging
from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin, field_options

from .model_battery import Battery
from .model_calendar import Tasks
from .model_capabilities import Capabilities
from .model_metadata import Metadata
from .model_mower import Mower
from .model_planner import Planner
from .model_positions import Positions
from .model_settings import Settings
from .model_statistics import Statistics
from .model_stay_out_zones import StayOutZones
from .model_system import System
from .model_work_areas import WorkArea

_LOGGER = logging.getLogger(__name__)


def generate_work_area_names_list(workarea_list: list) -> list[str]:
    """Return a list of names extracted from each work area dictionary."""
    wa_names = [WorkArea.from_dict(area).name for area in workarea_list]
    wa_names.append("no_work_area_active")
    return wa_names


def generate_work_area_dict(workarea_list: list | None) -> dict[int, str] | None:
    """Return a dict of names extracted from each work area dictionary."""
    if workarea_list is None:
        return None
    return {
        area["workAreaId"]: get_work_area_name(area["name"]) for area in workarea_list
    }


def get_work_area_name(name: str) -> str:
    """Return the work area name.

    Replacing empty strings with a default name 'my_lawn'.
    """
    return "my_lawn" if name == "" else name


@dataclass
class MowerAttributes(DataClassDictMixin):
    """DataClass for MowerAttributes."""

    system: System
    battery: Battery
    capabilities: Capabilities
    mower: Mower
    calendar: Tasks
    planner: Planner
    metadata: Metadata
    positions: list[Positions]
    settings: Settings
    statistics: Statistics
    stay_out_zones: StayOutZones | None = field(
        metadata=field_options(alias="stayOutZones"), default=None
    )
    work_areas: dict[int, WorkArea] | None = field(
        metadata=field_options(
            deserialize=lambda workarea_list: {
                area["workAreaId"]: WorkArea.from_dict(area) for area in workarea_list
            },
            alias="workAreas",
        ),
        default=None,
    )
    work_area_names: list[str] | None = field(
        metadata=field_options(
            deserialize=generate_work_area_names_list,
            alias="workAreas",
        ),
        default=None,
    )
    work_area_dict: dict[int, str] | None = field(
        metadata=field_options(
            deserialize=generate_work_area_dict,
            alias="workAreas",
        ),
        default=None,
    )

    def __post_init__(self) -> None:
        """Set the name after init."""
        if self.capabilities.work_areas:
            if self.mower.work_area_id is None:
                self.mower.work_area_name = "no_work_area_active"
            if self.work_areas and self.mower.work_area_id is not None:
                work_area = self.work_areas.get(self.mower.work_area_id)
                if work_area:
                    self.mower.work_area_name = work_area.name


@dataclass
class MowerData(DataClassDictMixin):
    """DataClass for MowerData values."""

    type: str
    id: str
    attributes: MowerAttributes


@dataclass
class MowerList(DataClassDictMixin):
    """DataClass for a list of all mowers."""

    data: list[MowerData]
