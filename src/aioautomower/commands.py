"""Commands for the Automower."""

import datetime
import logging
import zoneinfo
from dataclasses import dataclass

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

        # Verify capability
        if not client.data[mower_id].capabilities.work_areas:
            msg = "This mower does not support this command."
            raise FeatureNotSupportedError(msg)

    async def cutting_height(
        self,
        cutting_height: int,
    ) -> None:
        """Set the cutting height for this work area."""
        payload = {
            "data": {
                "type": "workArea",
                "id": self.work_area_id,
                "attributes": {"cuttingHeight": cutting_height},
            }
        }
        url = AutomowerEndpoint.work_area_cutting_height.format(
            mower_id=self.mower_id,
            work_area_id=self.work_area_id,
        )
        await self._client.auth.patch_json(url, json=payload)

    async def enabled(
        self,
        *,
        enabled: bool,
    ) -> None:
        """Enable or disable this work area."""
        payload = {
            "data": {
                "type": "workArea",
                "id": self.work_area_id,
                "attributes": {"enable": enabled},
            }
        }
        url = AutomowerEndpoint.work_area_cutting_height.format(
            mower_id=self.mower_id,
            work_area_id=self.work_area_id,
        )
        await self._client.auth.patch_json(url, json=payload)


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

    async def reset_cutting_blade_usage_time(self, mower_id: str) -> None:
        """Reset the cutting blade usage time.

        Same function that is available in the Automower Connect app. The statistics
        value cuttingBladeUsageTime will be reset. Can be used when cutting blades are
        changed on the Automower to know when its time to the blades next time.
        """
        url = AutomowerEndpoint.reset_cutting_blade_usage_time.format(mower_id=mower_id)
        await self.auth.post_json(url)

    async def resume_schedule(self, mower_id: str) -> None:
        """Resume schedule.

        Remove any override on the Planner and let the mower
        resume to the schedule set by the Calendar.
        """
        body = {"data": {"type": "ResumeSchedule"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def pause_mowing(self, mower_id: str) -> None:
        """Send pause mowing command to the mower via Rest."""
        body = {"data": {"type": "Pause"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def park_until_next_schedule(self, mower_id: str) -> None:
        """Send park until next schedule command to the mower."""
        body = {"data": {"type": "ParkUntilNextSchedule"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def park_until_further_notice(self, mower_id: str) -> None:
        """Send park until further notice command to the mower."""
        body = {"data": {"type": "ParkUntilFurtherNotice"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def park_for(self, mower_id: str, tdelta: datetime.timedelta) -> None:
        """Parks the mower for a period of minutes.

        The mower will drive to
        the charching station and park for the duration set by the command.
        """
        body = {
            "data": {
                "type": "Park",
                "attributes": {"duration": timedelta_to_minutes(tdelta)},
            }
        }
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def start_in_workarea(
        self,
        mower_id: str,
        work_area_id: int,
        tdelta: datetime.timedelta,
    ) -> None:
        """Start the mower in a work area for a period of minutes."""
        if not self.data[mower_id].capabilities.work_areas:
            msg = "This mower does not support this command."
            raise FeatureNotSupportedError(msg)
        body = {
            "data": {
                "type": "StartInWorkArea",
                "attributes": {
                    "duration": timedelta_to_minutes(tdelta),
                    "workAreaId": work_area_id,
                },
            }
        }
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def start_for(self, mower_id: str, tdelta: datetime.timedelta) -> None:
        """Start the mower for a period of minutes."""
        body = {
            "data": {
                "type": "Start",
                "attributes": {"duration": timedelta_to_minutes(tdelta)},
            }
        }
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def set_cutting_height(self, mower_id: str, cutting_height: int) -> None:
        """Set the cutting height for the mower."""
        body = {
            "data": {
                "type": "settings",
                "attributes": {"cuttingHeight": cutting_height},
            }
        }
        url = AutomowerEndpoint.settings.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def set_datetime(
        self, mower_id: str, current_time: datetime.datetime | None = None
    ) -> None:
        """Set the datetime of the mower.

        Timestamp in seconds from 1970-01-01. The timestamp needs to be in 24 hours in
        the local time of the mower.
        """
        current_time = current_time or datetime.datetime.now(tz=self.mower_tz)
        body = {
            "data": {
                "type": "settings",
                "attributes": {
                    "dateTime": int(
                        current_time.astimezone(self.mower_tz)
                        .replace(tzinfo=datetime.UTC)
                        .timestamp()
                    )
                },
            }
        }
        url = AutomowerEndpoint.settings.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def set_datetime_new(
        self, mower_id: str, current_time: datetime.datetime | None = None
    ) -> None:
        """Set the datetime of the mower.

        If the current has not tz_info, the mower_tz will be used as tz_info.
        """
        current_time = current_time or datetime.datetime.now(tz=self.mower_tz)
        body = {
            "data": {
                "type": "settings",
                "attributes": {
                    "timer": {
                        "dateTime": int(
                            current_time.astimezone(self.mower_tz)
                            .replace(tzinfo=datetime.UTC)
                            .timestamp()
                        ),
                        "timeZone": str(self.mower_tz),
                    },
                },
            }
        }
        url = AutomowerEndpoint.settings.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def set_headlight_mode(
        self,
        mower_id: str,
        headlight_mode: HeadlightModes,
    ) -> None:
        """Send headlight mode to the mower."""
        if not self.data[mower_id].capabilities.headlights:
            msg = "This mower does not support this command."
            raise FeatureNotSupportedError(msg)
        body = {
            "data": {
                "type": "settings",
                "attributes": {"headlight": {"mode": headlight_mode.upper()}},
            }
        }
        url = AutomowerEndpoint.settings.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def set_calendar(
        self,
        mower_id: str,
        tasks: Tasks,
    ) -> None:
        """Send calendar task to the mower."""
        if not self.data[mower_id].capabilities.work_areas:
            body = {
                "data": {
                    "type": "calendar",
                    "attributes": tasks.to_dict(),
                }
            }
            url = AutomowerEndpoint.calendar.format(mower_id=mower_id)
            await self.auth.post_json(url, json=body)
        if self.data[mower_id].capabilities.work_areas:
            task_list: list[Calendar] = tasks.tasks
            first_work_area_id = None
            for task in task_list:
                work_area_id = task.work_area_id
                if first_work_area_id is None:
                    first_work_area_id = work_area_id
                elif work_area_id != first_work_area_id:
                    msg = "Only identical work areas are allowed in one command."
                    raise WorkAreasDifferentError(msg)
            body = {
                "data": {
                    "type": "calendar",
                    "attributes": tasks.to_dict(),
                }
            }
            url = AutomowerEndpoint.work_area_calendar.format(
                mower_id=mower_id, work_area_id=work_area_id
            )
            await self.auth.post_json(url, json=body)

    async def switch_stay_out_zone(
        self, mower_id: str, stay_out_zone_id: str, *, switch: bool
    ) -> None:
        """Enable or disable a stay out zone."""
        if not self.data[mower_id].capabilities.stay_out_zones:
            msg = "This mower does not support this command."
            raise FeatureNotSupportedError(msg)
        body = {
            "data": {
                "type": "stayOutZone",
                "id": stay_out_zone_id,
                "attributes": {"enable": switch},
            }
        }
        url = AutomowerEndpoint.stay_out_zones.format(
            mower_id=mower_id, stay_out_id=stay_out_zone_id
        )
        await self.auth.patch_json(url, json=body)

    async def error_confirm(self, mower_id: str) -> None:
        """Confirm non-fatal mower error."""
        if not self.data[mower_id].capabilities.can_confirm_error:
            msg = "This mower does not support this command."
            raise FeatureNotSupportedError(msg)
        url = AutomowerEndpoint.error_confirm.format(mower_id=mower_id)
        await self.auth.post_json(url)
