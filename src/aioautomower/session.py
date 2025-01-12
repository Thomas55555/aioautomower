"""Module to connect to Automower with websocket."""

import asyncio
import contextlib
import datetime
import logging
import zoneinfo
from collections.abc import Callable, Mapping, MutableMapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import tzlocal
from aiohttp import WSMessage, WSMsgType

from .auth import AbstractAuth
from .const import EVENT_TYPES, REST_POLL_CYCLE, EventTypesV2
from .exceptions import (
    FeatureNotSupportedError,
    HusqvarnaTimeoutError,
    NoDataAvailableError,
    WorkAreasDifferentError,
)
from .model import HeadlightModes, MowerAttributes, Tasks
from .utils import mower_list_to_dictionary_dataclass, timedelta_to_minutes

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .model import Calendar

_LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)


@dataclass
class AutomowerEndpoint:
    """Endpoint URLs for the AutomowerConnect API."""

    mowers = "mowers/"
    "List data for all mowers linked to a user."

    actions = "mowers/{mower_id}/actions"
    "Accepts actions to control a mower linked to a user."

    calendar = "mowers/{mower_id}/calendar"
    "Update the calendar on the mower."

    settings = "mowers/{mower_id}/settings"
    "Update the settings on the mower."

    stay_out_zones = "mowers/{mower_id}/stayOutZones/{stay_out_id}"
    "Enable or disable the stay-out zone."

    work_area_cutting_height = "mowers/{mower_id}/workAreas/{work_area_id}"
    "This will update cutting height on the work area."

    work_area_calendar = "mowers/{mower_id}/workAreas/{work_area_id}/calendar"
    "Update the calendar for a work area on the mower."

    error_confirm = "mowers/{mower_id}/errors/confirm"
    "Confirm mower non-fatal error"


class _MowerCommands:
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

        If the current has not tz_info, the mower_tz will be used as tz_info.
        """
        current_time = current_time or datetime.datetime.now(tz=self.mower_tz)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=self.mower_tz)
        body = {
            "data": {
                "type": "settings",
                "attributes": {
                    "timer": {
                        "dateTime": int(current_time.timestamp()),
                        "timeZone": str(self.mower_tz),
                    },
                },
            }
        }
        url = AutomowerEndpoint.settings.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def workarea_settings(
        self,
        mower_id: str,
        work_area_id: int,
        cutting_height: int | None = None,
        enabled: bool | None = None,
    ) -> None:
        """Set the stettings for for a specific work area."""
        if not self.data[mower_id].capabilities.work_areas:
            msg = "This mower does not support this command."
            raise FeatureNotSupportedError(msg)
        current_mower = self.data[mower_id].work_areas
        if TYPE_CHECKING:
            assert current_mower is not None
        current_work_area = current_mower[work_area_id]
        body = {
            "data": {
                "type": "workArea",
                "id": work_area_id,
                "attributes": {
                    "cuttingHeight": cutting_height or current_work_area.cutting_height,
                    "enable": enabled or current_work_area.enabled,
                },
            }
        }
        url = AutomowerEndpoint.work_area_cutting_height.format(
            mower_id=mower_id, work_area_id=work_area_id
        )
        await self.auth.patch_json(url, json=body)

    async def set_headlight_mode(
        self,
        mower_id: str,
        headlight_mode: Literal[
            HeadlightModes.ALWAYS_OFF,
            HeadlightModes.ALWAYS_ON,
            HeadlightModes.EVENING_AND_NIGHT,
            HeadlightModes.EVENING_ONLY,
        ],
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
        body = {}  # type: dict[str, str]
        url = AutomowerEndpoint.error_confirm.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)


class AutomowerSession:
    """Automower API to communicate with an Automower.

    The `AutomowerSession` is the primary API service for this library. It supports
    operations like getting a status or sending commands.
    """

    def __init__(
        self,
        auth: AbstractAuth,
        mower_tz: zoneinfo.ZoneInfo | None = None,
        *,
        poll: bool = False,
    ) -> None:
        """Create a session.

        :param class auth: The AbstractAuth class from aioautomower.auth.
        :param bool poll: Poll data with rest if True.
        """
        self._data: dict[str, Iterable[Any]] | None = {}
        self.auth = auth
        self.data: dict[str, MowerAttributes] = {}
        self.mower_tz = mower_tz or tzlocal.get_localzone()
        self.commands = _MowerCommands(self.auth, self.data, self.mower_tz)
        self.pong_cbs: list = []
        self.data_update_cbs: list = []
        self.last_ws_message: datetime.datetime
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self.poll = poll
        self.rest_task: asyncio.Task | None = None
        _LOGGER.debug("self.mower_tz: %s", self.mower_tz)

    def register_data_callback(
        self, callback: Callable[[dict[str, MowerAttributes]], None]
    ) -> None:
        """Register a data update callback."""
        if callback not in self.data_update_cbs:
            self.data_update_cbs.append(callback)

    def _schedule_data_callback(
        self, cb: Callable[[dict[str, MowerAttributes]], None]
    ) -> None:
        """Schedule a data callback."""
        if self.poll and self.data is None:
            raise NoDataAvailableError
        self.loop.call_soon_threadsafe(cb, self.data)

    def _schedule_data_callbacks(self) -> None:
        """Schedule a data callbacks."""
        for cb in self.data_update_cbs:
            self._schedule_data_callback(cb)

    def unregister_data_callback(
        self, callback: Callable[[dict[str, MowerAttributes]], None]
    ) -> None:
        """Unregister a data update callback.

        :param func callback: Takes one function, which should be unregistered.
        """
        if callback in self.data_update_cbs:
            self.data_update_cbs.remove(callback)

    def register_pong_callback(
        self, pong_callback: Callable[[datetime.datetime], None]
    ) -> None:
        """Register a pong callback.

        It's not real ping/pong, but a way to check if the websocket
        is still alive, by receiving an empty message.
        """
        if pong_callback not in self.pong_cbs:
            self.pong_cbs.append(pong_callback)

    def _schedule_pong_callback(self, cb: Callable[[datetime.datetime], None]) -> None:
        """Schedule a pong callback."""
        self.loop.call_soon_threadsafe(cb, self.last_ws_message)

    def _schedule_pong_callbacks(self) -> None:
        """Schedule pong callbacks."""
        for cb in self.pong_cbs:
            self._schedule_pong_callback(cb)

    def unregister_pong_callback(
        self, pong_callback: Callable[[datetime.datetime], None]
    ) -> None:
        """Unregister a pong update callback.

        :param func callback: Takes one function, which should be unregistered.
        """
        if pong_callback in self.pong_cbs:
            self.pong_cbs.remove(pong_callback)

    async def connect(self) -> None:
        """Connect to the API.

        This method handles the login. Also a REST task will be started, which
        periodically polls the REST endpoint, when polling is set to true.
        """
        self._schedule_data_callbacks()

        if self.poll:
            await self.get_status()
            self.rest_task = asyncio.create_task(self._rest_task())

    def _handle_text_message(self, msg: WSMessage) -> None:
        """Process a text message to data."""
        if not msg.data:
            self.last_ws_message = datetime.datetime.now(tz=datetime.UTC)
            _LOGGER.debug("last_ws_message:%s", self.last_ws_message)
            self._schedule_pong_callbacks()
        if msg.data:
            msg_dict = msg.json()
            if "type" in msg_dict:
                if msg_dict["type"] in set(EVENT_TYPES):
                    _LOGGER.debug("Received websocket V1 type %s", msg_dict["type"])
                if msg_dict["type"] in {event.value for event in EventTypesV2}:
                    self._update_data(msg_dict)
                else:
                    _LOGGER.debug("Received unknown ws type %s", msg_dict["type"])
            elif "ready" in msg_dict and "connectionId" in msg_dict:
                _LOGGER.debug(
                    "Websocket ready=%s (id='%s')",
                    msg_dict["ready"],
                    msg_dict["connectionId"],
                )

    async def start_listening(self) -> None:
        """Start listening to the websocket (and receive initial state)."""
        while not self.auth.ws.closed:
            try:
                msg = await self.auth.ws.receive(timeout=300)
                if msg.type in (
                    WSMsgType.CLOSE,
                    WSMsgType.CLOSING,
                    WSMsgType.CLOSED,
                ):
                    break
                if msg.type == WSMsgType.TEXT:
                    self._handle_text_message(msg)
                elif msg.type == WSMsgType.ERROR:
                    continue
            except TimeoutError as exc:
                raise HusqvarnaTimeoutError from exc

    async def send_empty_message(self) -> None:
        """Send an empty message every 60s."""
        while True:
            await asyncio.sleep(60)
            _LOGGER.debug("ping:%s", datetime.datetime.now(tz=datetime.UTC))
            await self.auth.ws.send_str("")

    async def get_status(self) -> dict[str, MowerAttributes]:
        """Get mower status via Rest."""
        mower_list = await self.auth.get_json(AutomowerEndpoint.mowers)
        self._data = mower_list
        self.data = mower_list_to_dictionary_dataclass(self._data, self.mower_tz)
        self.commands = _MowerCommands(self.auth, self.data, self.mower_tz)
        return self.data

    def _update_data(self, new_data: Mapping[str, Any]) -> None:
        """Update internal data with new data from websocket."""
        if self._data is None:
            raise NoDataAvailableError

        data = self._data["data"]

        for mower in data:
            if mower["type"] == "mower" and mower["id"] == new_data["id"]:
                self._process_event(mower, new_data)
                break

        self.data = mower_list_to_dictionary_dataclass(self._data, self.mower_tz)
        self.commands = _MowerCommands(self.auth, self.data, self.mower_tz)
        self._schedule_data_callbacks()

    def _process_event(self, mower: dict, new_data: Mapping[str, Any]) -> None:
        """Process a specific event type."""
        handlers = {
            "cuttingHeight": self._handle_cutting_height_event,
            "headLight": self._handle_headlight_event,
            "position": self._handle_position_event,
        }

        attributes = new_data.get("attributes", {})
        for key, handler in handlers.items():
            if key in attributes:
                handler(mower, attributes)
                return

        # General handling for other attributes
        self._update_nested_dict(mower["attributes"], attributes)

    def _handle_cutting_height_event(self, mower: dict, attributes: dict) -> None:
        """Handle cuttingHeight-specific updates."""
        mower["attributes"]["settings"]["cuttingHeight"] = attributes["cuttingHeight"][
            "height"
        ]

    def _handle_headlight_event(self, mower: dict, attributes: dict) -> None:
        """Handle headLight-specific updates."""
        mower["attributes"]["settings"]["headlight"]["mode"] = attributes["headLight"][
            "mode"
        ]

    def _handle_position_event(
        self, mower: dict[str, dict[str, list[dict]]], attributes: dict[str, dict]
    ) -> None:
        mower["attributes"]["positions"].insert(0, attributes["position"])

    @staticmethod
    def _update_nested_dict(
        original: MutableMapping[Any, Any], updates: Mapping[Any, Any]
    ) -> None:
        """Recursively update a nested dictionary with new values."""
        for key, value in updates.items():
            if (
                isinstance(value, dict)
                and key in original
                and isinstance(original[key], dict)
            ):
                AutomowerSession._update_nested_dict(original[key], value)
            else:
                original[key] = value

    async def _rest_task(self) -> None:
        """Poll data periodically via Rest."""
        while True:
            await self.get_status()
            self._schedule_data_callbacks()
            await asyncio.sleep(REST_POLL_CYCLE)

    async def close(self) -> None:
        """Close the session."""
        if self.rest_task:
            if not self.rest_task.cancelled():
                self.rest_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await asyncio.gather(self.rest_task)
