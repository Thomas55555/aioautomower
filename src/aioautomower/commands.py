"""Commands for the Automower."""

import datetime
import logging
import zoneinfo
from dataclasses import dataclass
from typing import Any

from .auth import AbstractAuth
from .exceptions import (
    FeatureNotSupportedError,
    WorkAreasDifferentError,
)
from .model import (
    Calendar,
    HeadlightModes,
    MowerAttributes,
    Tasks,
)
from .utils import timedelta_to_minutes

_LOGGER = logging.getLogger(__name__)
FEATURE_NOT_SUPPORTED_MSG = "This mower does not support this command."


def _degrees_to_tenths_of_degree(value: float) -> int:
    """Convert an angle in degrees to the API's tenths-of-a-degree format."""
    return round(value * 10)


@dataclass
class AutomowerEndpoint:
    """Endpoint URLs for the AutomowerConnect API."""

    mowers = "mowers/"
    "List data for all mowers linked to a user."

    actions = "mowers/{mower_id}/actions"
    "Accepts actions to control a mower linked to a user."

    calendar = "mowers/{mower_id}/calendar"
    "Update the calendar on the mower."

    messages = "mowers/{mower_id}/messages"
    "List data for all mowers linked to a user."

    settings = "mowers/{mower_id}/settings"
    "Update the settings on the mower."

    reset_cutting_blade_usage_time = (
        "mowers/{mower_id}/statistics/resetCuttingBladeUsageTime"
    )
    """Reset the cutting blade usage time. Same function that is available in the
    Automower Connect app. The statistics value cuttingBladeUsageTime will be reset.
    Can be used when cutting blades are changed on the Automower to know when its time
    to the blades next time."""

    stay_out_zones = "mowers/{mower_id}/stayOutZones/{stay_out_id}"
    "Enable or disable the stay-out zone."

    work_area_cutting_height = "mowers/{mower_id}/workAreas/{work_area_id}"
    "This will update cutting height on the work area."

    work_area_calendar = "mowers/{mower_id}/workAreas/{work_area_id}/calendar"
    "Update the calendar for a work area on the mower."

    error_confirm = "mowers/{mower_id}/errors/confirm"
    "Confirm mower non-fatal error"


class WorkAreaSettings:
    """Namespace for work area settings commands."""

    def __init__(
        self,
        client: "MowerCommands",
        mower_id: str,
        work_area_id: int,
    ) -> None:
        """Initialize WorkAreaSettings for a mower's work area."""
        self._client = client
        self.mower_id = mower_id
        self.work_area_id = work_area_id

        if not client.data[mower_id].capabilities.work_areas:
            msg = FEATURE_NOT_SUPPORTED_MSG
            raise FeatureNotSupportedError(msg)

    def _validate_range(self, field: str, value: float) -> None:
        if not 0 <= value <= 180:
            msg = f"{field} must be between 0 and 180 degrees"
            raise ValueError(msg)

    async def update(
        self,
        *,
        cutting_height: int | None = None,
        enabled: bool | None = None,
        name: str | None = None,
        orientation: float | None = None,
        orientation_shift: float | None = None,
    ) -> None:
        """Update work area settings; angles are specified in degrees."""
        if orientation is not None:
            self._validate_range("orientation", orientation)

        if orientation_shift is not None:
            self._validate_range("orientation_shift", orientation_shift)

        attributes: dict[str, int | bool | str] = {}
        if cutting_height is not None:
            attributes["cuttingHeight"] = cutting_height
        if enabled is not None:
            attributes["enable"] = enabled
        if name is not None:
            attributes["name"] = name
        if orientation is not None:
            attributes["orientation"] = _degrees_to_tenths_of_degree(orientation)
        if orientation_shift is not None:
            attributes["orientationShift"] = _degrees_to_tenths_of_degree(
                orientation_shift
            )

        if not attributes:
            return

        payload = {
            "data": {
                "type": "workArea",
                "id": self.work_area_id,
                "attributes": attributes,
            }
        }

        url = AutomowerEndpoint.work_area_cutting_height.format(
            mower_id=self.mower_id,
            work_area_id=self.work_area_id,
        )

        await self._client.auth.patch_json(url, json=payload)

    async def cutting_height(self, cutting_height: int) -> None:
        """Set the cutting height for this work area."""
        await self.update(cutting_height=cutting_height)

    async def enabled(self, *, enabled: bool) -> None:
        """Enable or disable this work area."""
        await self.update(enabled=enabled)


class MowerCommands:
    """Sending commands."""

    def __init__(
        self,
        auth: AbstractAuth,
        data: dict[str, MowerAttributes],
        mower_tz: zoneinfo.ZoneInfo,
    ) -> None:
        """Send all commands to the API.

        :param class auth: The AbstractAuth class from aioautomower.auth.
        """
        self.auth = auth
        self.data = data
        self.mower_tz = mower_tz

    def workarea_settings(
        self,
        mower_id: str,
        work_area_id: int,
    ) -> WorkAreaSettings:
        """Return a settings helper for a specific work area.

        :param mower_id: Identifier of the mower.
        :param work_area_id: Identifier of the work area.
        :returns: Configured WorkAreaSettings instance.
        """
        return WorkAreaSettings(
            client=self,
            mower_id=mower_id,
            work_area_id=work_area_id,
        )
