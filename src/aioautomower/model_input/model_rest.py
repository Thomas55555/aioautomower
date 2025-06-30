"""Models for Automower Connect API for endpoint /mowers."""

from typing import Any, TypedDict

from .model_message import Message


class SystemAttributes(TypedDict):
    """Represents system attributes of the mower."""

    name: str
    model: str
    serialNumber: int


class BatteryAttributes(TypedDict):
    """Represents battery attributes of the mower."""

    batteryPercent: int


class CapabilitiesAttributes(TypedDict):
    """Represents capabilities attributes of the mower."""

    canConfirmError: bool
    headlights: bool
    position: bool
    stayOutZones: bool
    workAreas: bool


class MowerAttributes(TypedDict):
    """Represents mower-related attributes."""

    mode: str
    activity: str
    inactiveReason: str
    state: str
    workAreaId: int
    errorCode: int
    errorCodeTimestamp: int
    isErrorConfirmable: bool


class CalendarTask(TypedDict):
    """Represents a calendar task with its schedule and work area ID."""

    start: int
    duration: int
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool
    workAreaId: int


class PlannerOverride(TypedDict):
    """Represents override settings for the mower's planner."""

    action: str


class WorkAreaAttributes(TypedDict):
    """Represents attributes of a specific work area for the mower."""

    workAreaId: int
    name: str
    cuttingHeight: int
    enabled: bool
    progress: int | None
    lastTimeCompleted: int | None


class PositionAttributes(TypedDict):
    """Represents a position with latitude and longitude."""

    latitude: float
    longitude: float


class StatisticsAttributes(TypedDict):
    """Represents mower statistics."""

    cuttingBladeUsageTime: int
    downTime: int
    numberOfChargingCycles: int
    numberOfCollisions: int
    totalChargingTime: int
    totalCuttingTime: int
    totalDriveDistance: int
    totalRunningTime: int
    totalSearchingTime: int
    upTime: int


class StayOutZone(TypedDict):
    """Represents a stay-out zone with its id, name, and enabled status."""

    id: str
    name: str
    enabled: bool


class StayOutZonesAttributes(TypedDict):
    """Represents stay-out zones and their status."""

    dirty: bool
    zones: list[StayOutZone]


class SettingsAttributes(TypedDict):
    """Represents mower settings, including cutting height and headlight mode."""

    cuttingHeight: int
    headlight: dict[str, str]


class MowerDataAttributes(TypedDict):
    """Represents attributes of the mower data."""

    system: SystemAttributes
    battery: BatteryAttributes
    capabilities: CapabilitiesAttributes
    mower: MowerAttributes
    calendar: dict[str, list[CalendarTask]]
    planner: dict[str, Any]
    metadata: dict[str, Any]
    workAreas: list[WorkAreaAttributes]
    positions: list[PositionAttributes]
    statistics: StatisticsAttributes
    stayOutZones: StayOutZonesAttributes
    settings: SettingsAttributes
    messages: list[Message]


class MowerDataItem(TypedDict):
    """Represents a single mower data item with its type, id, and attributes."""

    type: str
    id: str
    attributes: MowerDataAttributes


class MowerDataResponse(TypedDict):
    """Represents the full response structure containing mower data."""

    data: list[MowerDataItem]
