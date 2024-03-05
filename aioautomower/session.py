"""Module to connect to Automower with websocket."""

import asyncio
import contextlib
import logging
from typing import Literal
from dataclasses import dataclass
from aiohttp import WSMsgType

from .auth import AbstractAuth
from .const import EVENT_TYPES, REST_POLL_CYCLE
from .exceptions import NoDataAvailableException, TimeoutException
from .model import HeadlightModes, MowerAttributes
from .utils import mower_list_to_dictionary_dataclass

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

    settings = "mowers/{mower_id}/settings"
    "Update the settings on the mower."

    stay_out_zones = "mowers/{mower_id}/stayOutZones/{stay_out_id}"
    "Enable or disable the stay-out zone."

    work_area_calendar = "mowers/{mower_id}/workAreas{work_area_id}/calendar"
    "Update the calendar for a work area on the mower."


class AutomowerSession:
    """Automower API to communicate with an Automower.

    The `AutomowerSession` is the primary API service for this library. It supports
    operations like getting a status or sending commands.
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-nested-blocks

    def __init__(
        self,
        auth: AbstractAuth,
        poll: bool = False,
    ) -> None:
        """Create a session.

        :param class auth: The AbstractAuth class from aioautomower.auth.
        :param bool poll: Poll data with rest if True.
        """
        self._data: dict = {}
        self.auth = auth
        self.data_update_cbs: list = []
        self.data: dict[str, MowerAttributes] = {}
        self.loop = asyncio.get_running_loop()
        self.poll = poll
        self.rest_task = None
        self.token = None
        self.token_task = None
        self.token_update_cbs: list = []

    def register_data_callback(self, callback):
        """Register a data update callback."""
        if callback not in self.data_update_cbs:
            self.data_update_cbs.append(callback)

    def _schedule_data_callback(self, cb):
        if self.poll and self.data is None:
            raise NoDataAvailableException
        self.loop.call_soon_threadsafe(cb, self.data)

    def _schedule_data_callbacks(self):
        for cb in self.data_update_cbs:
            self._schedule_data_callback(cb)

    def unregister_data_callback(self, callback):
        """Unregister a data update callback.

        :param func callback: Takes one function, which should be unregistered.
        """
        if callback in self.data_update_cbs:
            self.data_update_cbs.remove(callback)

    async def connect(self):
        """Connect to the API.

        This method handles the login and starts a task that keep the access
        token constantly fresh. Also a REST task will be started, which
        periodically polls the REST endpoint. This method works only, if the
        token is created with the Authorization Code Grant. Call this method
        before any other methods.
        """
        self._schedule_data_callbacks()

        if self.poll:
            await self.get_status()
            self.rest_task = asyncio.create_task(self._rest_task())

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
                    msg_dict = msg.json()
                    if "type" in msg_dict:
                        if msg_dict["type"] in EVENT_TYPES:
                            _LOGGER.debug(
                                "Got %s, data: %s", msg_dict["type"], msg_dict
                            )
                            self._update_data(msg_dict)
                        else:
                            _LOGGER.warning(
                                "Received unknown ws type %s", msg_dict["type"]
                            )
                    elif "ready" in msg_dict and "connectionId" in msg_dict:
                        _LOGGER.debug(
                            "Websocket ready=%s (id='%s')",
                            msg_dict["ready"],
                            msg_dict["connectionId"],
                        )
                elif msg.type == WSMsgType.ERROR:
                    continue
            except TimeoutError as exc:
                raise TimeoutException from exc

    async def get_status(self) -> dict[str, MowerAttributes]:
        """Get mower status via Rest."""
        mower_list = await self.auth.get_json(AutomowerEndpoint.mowers)
        for idx, _ent in enumerate(mower_list["data"]):
            mower_list["data"][idx]["attributes"].update(
                mower_list["data"][idx]["attributes"]["settings"]
            )
            del mower_list["data"][idx]["attributes"]["settings"]
        self._data = mower_list
        self.data = mower_list_to_dictionary_dataclass(self._data)
        return self.data

    async def resume_schedule(self, mower_id: str):
        """Resume schedule.

        Remove any override on the Planner and let the mower
        resume to the schedule set by the Calendar.
        """
        body = {"data": {"type": "ResumeSchedule"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def pause_mowing(self, mower_id: str):
        """Send pause mowing command to the mower via Rest."""
        body = {"data": {"type": "Pause"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def park_until_next_schedule(self, mower_id: str):
        """Send park until next schedule command to the mower."""
        body = {"data": {"type": "ParkUntilNextSchedule"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def park_until_further_notice(self, mower_id: str):
        """Send park until further notice command to the mower."""
        body = {"data": {"type": "ParkUntilFurtherNotice"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def park_for(self, mower_id: str, duration_in_min: int):
        """Parks the mower for a period of minutes.

        The mower will drive to
        the charching station and park for the duration set by the command.
        """
        body = {
            "data": {
                "type": "Park",
                "attributes": {"duration": duration_in_min},
            }
        }
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def start_for(self, mower_id: str, duration_in_min: int):
        """Start the mower for a period of minutes."""
        body = {
            "data": {
                "type": "Park",
                "attributes": {"duration": duration_in_min},
            }
        }
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def set_cutting_height(self, mower_id: str, cutting_height: int):
        """Start the mower for a period of minutes."""
        body = {
            "data": {
                "type": "settings",
                "attributes": {"cuttingHeight": cutting_height},
            }
        }
        url = AutomowerEndpoint.settings.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def set_headlight_mode(
        self,
        mower_id: str,
        headlight_mode: Literal[
            HeadlightModes.ALWAYS_OFF,
            HeadlightModes.ALWAYS_ON,
            HeadlightModes.EVENING_AND_NIGHT,
            HeadlightModes.EVENING_ONLY,
        ],
    ):
        """Send headlight mode to the mower."""
        body = {
            "data": {
                "type": "settings",
                "attributes": {"headlight": {"mode": headlight_mode}},
            }
        }
        url = AutomowerEndpoint.settings.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def set_calendar(
        self,
        mower_id: str,
        task_list: list,
    ):
        """Send calendar task to the mower."""
        body = {
            "data": {
                "type": "calendar",
                "attributes": {"tasks": task_list},
            }
        }
        url = AutomowerEndpoint.calendar.format(mower_id=mower_id)
        await self.auth.post_json(url, json=body)

    async def switch_stay_out_zone(
        self, mower_id: str, stay_out_zone_id: str, switch: bool
    ):
        """Enable or disable a stay out zone."""
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

    def _update_data(self, new_data):
        if self._data is None:
            raise NoDataAvailableException
        if self._data is not None:
            for datum in self._data["data"]:
                if datum["type"] == "mower" and datum["id"] == new_data["id"]:
                    for attrib in new_data["attributes"]:
                        try:
                            tasks = new_data["attributes"]["calendar"]["tasks"]
                            if len(tasks) == 0:
                                temp_task = datum["attributes"]["calendar"]["tasks"]
                                datum["attributes"][attrib] = new_data["attributes"][
                                    attrib
                                ]
                                datum["attributes"]["calendar"]["tasks"] = temp_task
                            if len(tasks) > 0:
                                datum["attributes"][attrib] = new_data["attributes"][
                                    attrib
                                ]
                        except KeyError:
                            datum["attributes"][attrib] = new_data["attributes"][attrib]
        self.data = mower_list_to_dictionary_dataclass(self._data)
        self._schedule_data_callbacks()

    async def _rest_task(self):
        """Poll data periodically via Rest."""
        while True:
            await self.get_status()
            self._schedule_data_callbacks()
            await asyncio.sleep(REST_POLL_CYCLE)

    async def close(self):
        """Close the session."""
        if self.rest_task:
            if not self.rest_task.cancelled():
                self.rest_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await asyncio.gather(self.rest_task)
