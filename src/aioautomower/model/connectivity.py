from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin, field_options


@dataclass
class DeviceResponse(DataClassDictMixin):
    """Top-level response wrapper."""

    data: DeviceData = field(metadata=field_options(alias="data"))


@dataclass
class DeviceData(DataClassDictMixin):
    """Root data object."""

    device_id: str = field(metadata=field_options(alias="id"))
    type_: str = field(metadata=field_options(alias="type"))
    attributes: DeviceAttributes = field(metadata=field_options(alias="attributes"))


@dataclass
class DeviceAttributes(DataClassDictMixin):
    """Device attributes."""

    mower: Mower = field(metadata=field_options(alias="mower"))


@dataclass
class Mower(DataClassDictMixin):
    """Mower object."""

    specification_id: str = field(metadata=field_options(alias="specificationId"))
    payload: MowerPayload = field(metadata=field_options(alias="payload"))


@dataclass
class EmptyObject(DataClassDictMixin):
    """Empty JSON object placeholder."""


@dataclass
class EnabledValue(DataClassDictMixin):
    """Generic wrapper for {"enabled": bool}."""

    enabled: bool = field(metadata=field_options(alias="enabled"))


@dataclass
class AvailableValue(DataClassDictMixin):
    """Generic wrapper for {"available": bool}."""

    available: bool = field(metadata=field_options(alias="available"))


@dataclass
class DistanceValue(DataClassDictMixin):
    """Generic wrapper for {"distance": int}."""

    distance: int = field(metadata=field_options(alias="distance"))


@dataclass
class ProportionValue(DataClassDictMixin):
    """Generic wrapper for {"proportion": int}."""

    proportion: int = field(metadata=field_options(alias="proportion"))


@dataclass
class HeightValue(DataClassDictMixin):
    """Generic wrapper for {"height": int}."""

    height: int = field(metadata=field_options(alias="height"))


@dataclass
class RadiusValue(DataClassDictMixin):
    """Generic wrapper for {"radius": int}."""

    radius: int = field(metadata=field_options(alias="radius"))


# @dataclass
# class RangeValue(DataClassDictMixin):
#     """Range wrapper."""

#     range_: str = field(metadata=field_options(alias="range"))


@dataclass
class ActionValue(DataClassDictMixin):
    """Generic wrapper for {"action": str}."""

    action: str


@dataclass
class SensitivityValue(DataClassDictMixin):
    """Generic wrapper for {"sensitivity": str}."""

    sensitivity: str = field(metadata=field_options(alias="sensitivity"))


@dataclass
class PassageCuttingEnabledValue(DataClassDictMixin):
    """Wrapper for {"passageCuttingEnabled": bool}."""

    passage_cutting_enabled: bool = field(
        metadata=field_options(alias="passageCuttingEnabled")
    )


@dataclass
class DelayTimeValue(DataClassDictMixin):
    """Wrapper for {"delayTime": int}."""

    delay_time: int = field(metadata=field_options(alias="delayTime"))


@dataclass
class ICCIDValue(DataClassDictMixin):
    """Wrapper for {"iccid": str}."""

    iccid: str = field(metadata=field_options(alias="iccid"))


@dataclass
class IMEIValue(DataClassDictMixin):
    """Wrapper for {"imei": str}."""

    imei: str = field(metadata=field_options(alias="imei"))


@dataclass
class IMSIValue(DataClassDictMixin):
    """Wrapper for {"imsi": str}."""

    imsi: str = field(metadata=field_options(alias="imsi"))


@dataclass
class Autotimer(DataClassDictMixin):
    """Autotimer settings."""

    enabled: EnabledValue = field(metadata=field_options(alias="Enabled"))
    sensitivity: SensitivityValue = field(metadata=field_options(alias="Sensitivity"))


@dataclass
class CalendarTask(DataClassDictMixin):
    """Single calendar task."""

    duration: int = field(metadata=field_options(alias="duration"))
    start: int = field(metadata=field_options(alias="start"))
    use_on_friday: bool = field(metadata=field_options(alias="useOnFriday"))
    use_on_monday: bool = field(metadata=field_options(alias="useOnMonday"))
    use_on_saturday: bool = field(metadata=field_options(alias="useOnSaturday"))
    use_on_sunday: bool = field(metadata=field_options(alias="useOnSunday"))
    use_on_thursday: bool = field(metadata=field_options(alias="useOnThursday"))
    use_on_tuesday: bool = field(metadata=field_options(alias="useOnTuesday"))
    use_on_wednesday: bool = field(metadata=field_options(alias="useOnWednesday"))


@dataclass
class CalendarTaskEntry(DataClassDictMixin):
    """Calendar task entry wrapper."""

    task: CalendarTask = field(metadata=field_options(alias="Task"))


@dataclass
class MaxNumberOfTasks(DataClassDictMixin):
    """Calendar max number of tasks."""

    max_number_of_tasks: int = field(metadata=field_options(alias="maxNumberOfTasks"))


@dataclass
class MaxNumberOfTasksPerDay(DataClassDictMixin):
    """Calendar max tasks per day."""

    max_number_of_tasks_per_day: int = field(
        metadata=field_options(alias="maxNumberOfTasksPerDay")
    )


@dataclass
class NumberOfTasks(DataClassDictMixin):
    """Calendar task count."""

    number_of_tasks: int = field(metadata=field_options(alias="numberOfTasks"))


@dataclass
class Calendar(DataClassDictMixin):
    """Calendar settings."""

    max_number_of_tasks: MaxNumberOfTasks = field(
        metadata=field_options(alias="MaxNumberOfTasks")
    )
    max_number_of_tasks_per_day: MaxNumberOfTasksPerDay = field(
        metadata=field_options(alias="MaxNumberOfTasksPerDay")
    )
    number_of_tasks: NumberOfTasks = field(
        metadata=field_options(alias="NumberOfTasks")
    )
    tasks: dict[str, CalendarTaskEntry] = field(metadata=field_options(alias="Tasks"))


@dataclass
class EcoModeEnabled(DataClassDictMixin):
    """Eco mode flag."""

    eco_mode_enabled: bool = field(metadata=field_options(alias="ecoModeEnabled"))


@dataclass
class MowerHouseInstalled(DataClassDictMixin):
    """Mower house installation flag."""

    mower_house_installed: bool = field(
        metadata=field_options(alias="mowerHouseInstalled")
    )


@dataclass
class ChargingStation(DataClassDictMixin):
    """Charging station settings."""

    eco_mode_enabled: EcoModeEnabled = field(
        metadata=field_options(alias="EcoModeEnabled")
    )
    mower_house_installed: MowerHouseInstalled = field(
        metadata=field_options(alias="MowerHouseInstalled")
    )


@dataclass
class DownCuttingEnabled(DataClassDictMixin):
    """Down cutting enabled flag."""

    down_cutting_enabled: bool = field(
        metadata=field_options(alias="downCuttingEnabled")
    )


@dataclass
class CuttingHeight(DataClassDictMixin):
    """Cutting height settings."""

    available: AvailableValue = field(metadata=field_options(alias="Available"))
    down_cutting_available: AvailableValue = field(
        metadata=field_options(alias="DownCuttingAvailable")
    )
    down_cutting_enabled: DownCuttingEnabled = field(
        metadata=field_options(alias="DownCuttingEnabled")
    )
    height: HeightValue = field(metadata=field_options(alias="Height"))


@dataclass
class MowerInformation(DataClassDictMixin):
    """Mower hardware and software information."""

    device_type_group: int = field(metadata=field_options(alias="deviceTypeGroup"))
    main_board_pcbaserial_no: int = field(
        metadata=field_options(alias="mainBoardPCBASerialNo")
    )
    main_board_prod_time: int = field(metadata=field_options(alias="mainBoardProdTime"))
    main_board_rev: int = field(metadata=field_options(alias="mainBoardRev"))
    main_board_type: int = field(metadata=field_options(alias="mainBoardType"))
    mower_applic_sw_build_no: int = field(
        metadata=field_options(alias="mowerApplicSwBuildNo")
    )
    mower_applic_sw_type: int = field(metadata=field_options(alias="mowerApplicSwType"))
    mower_applic_sw_ver: int = field(metadata=field_options(alias="mowerApplicSwVer"))
    mower_boot_sw_type: int = field(metadata=field_options(alias="mowerBootSwType"))
    mower_boot_sw_ver: int = field(metadata=field_options(alias="mowerBootSwVer"))
    mower_device_type: int = field(metadata=field_options(alias="mowerDeviceType"))
    mower_prod_time: int = field(metadata=field_options(alias="mowerProdTime"))
    mower_serial_no: int = field(metadata=field_options(alias="mowerSerialNo"))
    mower_sub_device_sw_build_no: int = field(
        metadata=field_options(alias="mowerSubDeviceSwBuildNo")
    )
    mower_sub_device_sw_type: int = field(
        metadata=field_options(alias="mowerSubDeviceSwType")
    )
    mower_sub_device_sw_ver: int = field(
        metadata=field_options(alias="mowerSubDeviceSwVer")
    )
    mower_variant_type: int = field(metadata=field_options(alias="mowerVariantType"))


@dataclass
class DeviceInformation(DataClassDictMixin):
    """Device information block."""

    mower_information: MowerInformation = field(
        metadata=field_options(alias="MowerInformation")
    )


@dataclass
class DrivePastWire(DataClassDictMixin):
    """Drive-past-wire setting."""

    distance: int = field(metadata=field_options(alias="distance"))


@dataclass
class DrivingSettings(DataClassDictMixin):
    """Driving settings."""

    drive_past_wire: DrivePastWire = field(
        metadata=field_options(alias="DrivePastWire")
    )


@dataclass
class StartingPointWire(DataClassDictMixin):
    """Starting point wire."""

    wire: str = field(metadata=field_options(alias="wire"))


@dataclass
class StartingPoint(DataClassDictMixin):
    """Follow-wire starting point."""

    passage_cutting_enabled: PassageCuttingEnabledValue = field(
        metadata=field_options(alias="PassageCuttingEnabled")
    )
    starting_point_distance: DistanceValue = field(
        metadata=field_options(alias="StartingPointDistance")
    )
    starting_point_enabled: EnabledValue = field(
        metadata=field_options(alias="StartingPointEnabled")
    )
    starting_point_proportion: ProportionValue = field(
        metadata=field_options(alias="StartingPointProportion")
    )
    starting_point_wire: StartingPointWire = field(
        metadata=field_options(alias="StartingPointWire")
    )


# @dataclass
# class BoundaryCorridor(DataClassDictMixin):
#     """Boundary corridor limits."""

#     max_: int = field(metadata=field_options(alias="max"))
#     min_: int = field(metadata=field_options(alias="min"))


@dataclass
class FollowWire(DataClassDictMixin):
    """Follow-wire settings."""

    # boundary_corridor: BoundaryCorridor = field(metadata=field_options(alias="BoundaryCorridor"))
    starting_points: dict[str, StartingPoint] = field(
        metadata=field_options(alias="StartingPoints")
    )


@dataclass
class FrostSensor(DataClassDictMixin):
    """Frost sensor settings."""

    enabled: EnabledValue = field(metadata=field_options(alias="Enabled"))


@dataclass
class CenterPosition(DataClassDictMixin):
    """Geo fence center position."""

    latitude: int = field(metadata=field_options(alias="latitude"))
    longitude: int = field(metadata=field_options(alias="longitude"))


@dataclass
class GeoFence(DataClassDictMixin):
    """Geo fence settings."""

    center_position: CenterPosition = field(
        metadata=field_options(alias="CenterPosition")
    )
    radius: RadiusValue = field(metadata=field_options(alias="Radius"))


@dataclass
class GpsNavigation(DataClassDictMixin):
    """GPS navigation settings."""

    enabled: EnabledValue = field(metadata=field_options(alias="Enabled"))


@dataclass
class ErrorIndicationEnabled(DataClassDictMixin):
    """Headlight error indication setting."""

    error_indication_enabled: bool = field(
        metadata=field_options(alias="errorIndicationEnabled")
    )


@dataclass
class Headlights(DataClassDictMixin):
    """Headlight settings."""

    error_indication_enabled: ErrorIndicationEnabled = field(
        metadata=field_options(alias="ErrorIndicationEnabled")
    )


@dataclass
class ProportionFirstSector(DataClassDictMixin):
    """Leave-charging-station first-sector proportion."""

    proportion_first_sector: int = field(
        metadata=field_options(alias="proportionFirstSector")
    )


@dataclass
class ReversingDistance(DataClassDictMixin):
    """Leave-charging-station reversing distance."""

    distance: int = field(metadata=field_options(alias="distance"))


@dataclass
class LeaveChargingStation(DataClassDictMixin):
    """Leave-charging-station settings."""

    proportion_first_sector: ProportionFirstSector = field(
        metadata=field_options(alias="ProportionFirstSector")
    )
    reversing_distance: ReversingDistance = field(
        metadata=field_options(alias="ReversingDistance")
    )


@dataclass
class MobileLoop(DataClassDictMixin):
    """Mobile loop settings."""

    available: AvailableValue = field(metadata=field_options(alias="Available"))
    enabled: EnabledValue = field(metadata=field_options(alias="Enabled"))


@dataclass
class Modem(DataClassDictMixin):
    """Modem identifiers."""

    iccid: ICCIDValue = field(metadata=field_options(alias="ICCID"))
    imei: IMEIValue = field(metadata=field_options(alias="IMEI"))
    imsi: IMSIValue = field(metadata=field_options(alias="IMSI"))


@dataclass
class MowerAppActivity(DataClassDictMixin):
    """Mower app activity."""

    mower_activity: str = field(metadata=field_options(alias="mowerActivity"))


@dataclass
class MowerAppError(DataClassDictMixin):
    """Mower app error."""

    error_code: str = field(metadata=field_options(alias="errorCode"))


@dataclass
class MowerAppMode(DataClassDictMixin):
    """Mower app mode."""

    mode_of_operation: str = field(metadata=field_options(alias="modeOfOperation"))


@dataclass
class MowerAppState(DataClassDictMixin):
    """Mower app state."""

    mower_state: str = field(metadata=field_options(alias="mowerState"))


@dataclass
class MowerApp(DataClassDictMixin):
    """Mower app status."""

    activity: MowerAppActivity = field(metadata=field_options(alias="Activity"))
    error: MowerAppError = field(metadata=field_options(alias="Error"))
    mode: MowerAppMode = field(metadata=field_options(alias="Mode"))
    state: MowerAppState = field(metadata=field_options(alias="State"))


@dataclass
class MowerStatusStatus(DataClassDictMixin):
    """Detailed mower status values."""

    config_change_counter: int = field(
        metadata=field_options(alias="configChangeCounter")
    )
    gsm_rssi: int = field(metadata=field_options(alias="gsmRssi"))
    hdop: int = field(metadata=field_options(alias="hdop"))
    host_message: int = field(metadata=field_options(alias="hostMessage"))
    last_error_code: str = field(metadata=field_options(alias="lastErrorCode"))
    timestamp_last_error: int = field(
        metadata=field_options(alias="timestampLastError")
    )


@dataclass
class MowerStatus(DataClassDictMixin):
    """Mower status block."""

    status: MowerStatusStatus = field(metadata=field_options(alias="Status"))


@dataclass
class NextStartTime(DataClassDictMixin):
    """Planner next start time."""

    next_start_time: int = field(metadata=field_options(alias="nextStartTime"))


@dataclass
class Override(DataClassDictMixin):
    """Planner override."""

    action: str = field(metadata=field_options(alias="action"))


@dataclass
class RestrictionReason(DataClassDictMixin):
    """Planner restriction reason."""

    restriction_reason: str = field(metadata=field_options(alias="restrictionReason"))


@dataclass
class Planner(DataClassDictMixin):
    """Planner settings."""

    next_start_time: NextStartTime = field(
        metadata=field_options(alias="NextStartTime")
    )
    override: Override = field(metadata=field_options(alias="Override"))
    restriction_reason: RestrictionReason = field(
        metadata=field_options(alias="RestrictionReason")
    )


@dataclass
class SearchTypeSetting(DataClassDictMixin):
    """Search charging station search type configuration."""

    delay_time: DelayTimeValue = field(metadata=field_options(alias="DelayTime"))
    enabled: EnabledValue = field(metadata=field_options(alias="Enabled"))


# @dataclass
# class DirectSearchChargingStationRange(DataClassDictMixin):
#     """Direct search charging station range."""

#     range_: RangeValue = field(metadata=field_options(alias="range"))


@dataclass
class SearchChargingStation(DataClassDictMixin):
    """Search charging station settings."""

    # direct_search_charging_station_range: DirectSearchChargingStationRange = field(
    #     metadata=field_options(alias="DirectSearchChargingStationRange")
    # )
    search_types: dict[str, SearchTypeSetting] = field(
        metadata=field_options(alias="SearchTypes")
    )


@dataclass
class SpotCutting(DataClassDictMixin):
    """Spot cutting settings."""

    enabled: EnabledValue = field(metadata=field_options(alias="Enabled"))
    sensitivity: SensitivityValue = field(metadata=field_options(alias="Sensitivity"))


@dataclass
class NumberOfChargingCycles(DataClassDictMixin):
    """Statistics: charging cycles."""

    number_of_charging_cycles: int = field(
        metadata=field_options(alias="numberOfChargingCycles")
    )


@dataclass
class TotalChargingTime(DataClassDictMixin):
    """Statistics: total charging time."""

    total_charging_time: int = field(metadata=field_options(alias="totalChargingTime"))


@dataclass
class TotalCuttingTime(DataClassDictMixin):
    """Statistics: total cutting time."""

    total_cutting_time: int = field(metadata=field_options(alias="totalCuttingTime"))


@dataclass
class TotalRunningTime(DataClassDictMixin):
    """Statistics: total running time."""

    total_running_time: int = field(metadata=field_options(alias="totalRunningTime"))


@dataclass
class TotalSearchingTime(DataClassDictMixin):
    """Statistics: total searching time."""

    total_searching_time: int = field(
        metadata=field_options(alias="totalSearchingTime")
    )


@dataclass
class Statistics(DataClassDictMixin):
    """Statistics block."""

    number_of_charging_cycles: NumberOfChargingCycles = field(
        metadata=field_options(alias="NumberOfChargingCycles")
    )
    total_charging_time: TotalChargingTime = field(
        metadata=field_options(alias="TotalChargingTime")
    )
    total_cutting_time: TotalCuttingTime = field(
        metadata=field_options(alias="TotalCuttingTime")
    )
    total_running_time: TotalRunningTime = field(
        metadata=field_options(alias="TotalRunningTime")
    )
    total_searching_time: TotalSearchingTime = field(
        metadata=field_options(alias="TotalSearchingTime")
    )


@dataclass
class SystemModel(DataClassDictMixin):
    """System model info."""

    device_type: int = field(metadata=field_options(alias="deviceType"))
    device_variant: int = field(metadata=field_options(alias="deviceVariant"))


@dataclass
class SerialNumber(DataClassDictMixin):
    """System serial number."""

    serial_number: int = field(metadata=field_options(alias="serialNumber"))


@dataclass
class SwPackageVersionString(DataClassDictMixin):
    """Software package version string."""

    sw_package_version: str = field(metadata=field_options(alias="swPackageVersion"))


@dataclass
class SwUpdateRequired(DataClassDictMixin):
    """Sw update requirement."""

    required: bool = field(metadata=field_options(alias="required"))


@dataclass
class System(DataClassDictMixin):
    """System block."""

    model: SystemModel = field(metadata=field_options(alias="Model"))
    serial_number: SerialNumber = field(metadata=field_options(alias="SerialNumber"))
    sw_package_version_string: SwPackageVersionString | None = field(
        default=None,
        metadata=field_options(alias="SwPackageVersionString"),
    )

    sw_update_required: SwUpdateRequired | None = field(
        default=None,
        metadata=field_options(alias="SwUpdateRequired"),
    )


@dataclass
class Ultrasonic(DataClassDictMixin):
    """Ultrasonic settings."""

    enabled: EnabledValue = field(metadata=field_options(alias="Enabled"))


@dataclass
class MowerPayload(DataClassDictMixin):
    """Complete mower payload."""

    autotimer: Autotimer = field(metadata=field_options(alias="Autotimer"))
    battery: EmptyObject = field(metadata=field_options(alias="Battery"))
    calendar: Calendar = field(metadata=field_options(alias="Calendar"))
    charging_station: ChargingStation = field(
        metadata=field_options(alias="ChargingStation")
    )
    cutting_height: CuttingHeight = field(metadata=field_options(alias="CuttingHeight"))
    # device_information: DeviceInformation = field(
    #     metadata=field_options(alias="DeviceInformation")
    # )
    driving_settings: DrivingSettings = field(
        metadata=field_options(alias="DrivingSettings")
    )
    follow_wire: FollowWire = field(metadata=field_options(alias="FollowWire"))
    # frost_sensor: FrostSensor = field(metadata=field_options(alias="FrostSensor"))
    geo_fence: GeoFence = field(metadata=field_options(alias="GeoFence"))
    gps_navigation: GpsNavigation = field(metadata=field_options(alias="GpsNavigation"))
    headlights: Headlights = field(metadata=field_options(alias="Headlights"))
    # leave_charging_station: LeaveChargingStation = field(
    #     metadata=field_options(alias="LeaveChargingStation")
    # )
    mobile_loop: MobileLoop = field(metadata=field_options(alias="MobileLoop"))
    modem: Modem = field(metadata=field_options(alias="Modem"))
    mower_app: MowerApp = field(metadata=field_options(alias="MowerApp"))

    planner: Planner = field(metadata=field_options(alias="Planner"))
    position: EmptyObject = field(metadata=field_options(alias="Position"))
    search_charging_station: SearchChargingStation = field(
        metadata=field_options(alias="SearchChargingStation")
    )
    # spot_cutting: SpotCutting = field(metadata=field_options(alias="SpotCutting"))
    # statistics: Statistics = field(metadata=field_options(alias="Statistics"))
    system: System = field(metadata=field_options(alias="System"))
    # ultrasonic: Ultrasonic = field(metadata=field_options(alias="Ultrasonic"))

    mower_status: MowerStatus | None = field(
        metadata=field_options(alias="MowerStatus"), default=None
    )
