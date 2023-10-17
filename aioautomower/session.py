"""Module to connect to Automower with websocket."""
import asyncio
import contextlib
import logging
import time
from typing import Literal

from . import rest
from .auth import AbstractAuth
from .const import MARGIN_TIME, MIN_SLEEP_TIME, REST_POLL_CYCLE
from .exceptions import NoDataAvailableException
from .model import HeadlightModes, MowerList

_LOGGER = logging.getLogger(__name__)


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
    "Enabe or disable the stay-out zone."

    work_area_calendar = "mowers/{mower_id}/workAreas{work_area_id}/calendar"
    "Update the calendar for a work area on the mower."


class AutomowerSession:
    """Session."""

    def __init__(
        self,
        auth: AbstractAuth,
        poll=False,
    ) -> None:
        """Create a session.

        :param str api_key: A 36 digit api key.
        :param dict token: A token as returned by rest.GetAccessToken.async_get_access_token()
        :param float ws_heartbeat_interval: Periodicity of keep-alive pings on the websocket in seconds.
        :param loop: Event-loop for task execution. If None, the event loop in the current OS thread is used.
        """
        self.auth = auth
        self.poll = poll
        self.data_update_cbs = []
        self.token_update_cbs = []
        self.rest_task = False
        self.loop = asyncio.get_event_loop()
        self.token = None
        self.data = {}
        self.mowers = {}
        self.listen_task = None
        self.ws_task = None

        self.token_task = None
        self.rest_task = None

    def register_data_callback(self, callback):
        """Register a data update callback.

        :param func callback: Callback fired on data updates. Takes one dict argument which is the up-to-date mower data list.
        :param bool schedule_immediately: Schedule callback immediately (if data is available).
        """
        if callback not in self.data_update_cbs:
            self.data_update_cbs.append(callback)

    def _schedule_data_callback(self, cb, delay=0.0):
        if self.poll:
            if self.data is None:
                raise NoDataAvailableException
        self.loop.call_later(delay, cb, self.mowers)

    def _schedule_data_callbacks(self):
        for cb in self.data_update_cbs:
            self._schedule_data_callback(cb)

    def unregister_data_callback(self, callback):
        """Unregister a data update callback.

        :param func callback: Callback fired on data updates. Takes one dict argument which is the up-to-date mower data list.
        """
        if callback in self.data_update_cbs:
            self.data_update_cbs.remove(callback)

    async def connect(self):
        """Connect to the API.

        This method handles the login and starts a task that keep the access
        token constantly fresh. Also a REST taks will be started, which
        periodically polls the REST endpoint. This method works only, if the
        token is created with the Authorization Code Grant. Call this method
        before any other methods.
        """

        self._schedule_data_callbacks()

        if self.poll:
            await self.get_status()
            self.rest_task = self.loop.create_task(self._rest_task())

        self.ws_task = self.loop.create_task(self.auth.websocket())
        self.auth.register_ws_callback(self.callback)

    async def close(self):
        """Close the session."""
        for task in [
            self.ws_task,
            self.token_task,
            self.rest_task,
        ]:
            tasks = []
            if task is not None:
                tasks.append(task)
                if not task.cancelled():
                    task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*tasks)

    async def get_status(self) -> MowerList:
        """Get mower status via Rest."""
        mower_list = await self.auth.get_json(AutomowerEndpoint.mowers)
        for idx, _ent in enumerate(mower_list["data"]):
            mower_list["data"][idx]["attributes"].update(
                mower_list["data"][idx]["attributes"]["settings"]
            )
            del mower_list["data"][idx]["attributes"]["settings"]
        self.data = mower_list
        self.mower_as_dict_dataclass()
        return self.mowers

    async def resume_schedule(self, mower_id: str):
        """Resume schedule.

        Remove any ovveride on the Planner and let the mower
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

    async def _token_monitor_task(self):
        while True:
            if "expires_at" in self.token:
                expires_at = self.token["expires_at"]
                sleep_time = max(MIN_SLEEP_TIME, expires_at - time.time() - MARGIN_TIME)
            else:
                sleep_time = MIN_SLEEP_TIME

            _LOGGER.debug("token_monitor_task sleeping for %s sec", sleep_time)
            await asyncio.sleep(sleep_time)
            await self.auth.async_get_access_token()

    def _update_data(self, j):
        if self.data is None:
            raise NoDataAvailableException
        if self.data is not None:
            for datum in self.data["data"]:
                if datum["type"] == "mower" and datum["id"] == j["id"]:
                    if j["type"] == "positions-event":
                        last_pos_identical = (
                            datum["attributes"]["positions"][0]
                            == j["attributes"]["positions"][0]
                        )
                        if not last_pos_identical:
                            j["attributes"]["positions"].extend(
                                datum["attributes"]["positions"]
                            )
                    for attrib in j["attributes"]:
                        try:
                            tasks = j["attributes"]["calendar"]["tasks"]
                            if len(tasks) == 0:
                                temp_task = datum["attributes"]["calendar"]["tasks"]
                                datum["attributes"][attrib] = j["attributes"][attrib]
                                datum["attributes"]["calendar"]["tasks"] = temp_task
                            if len(tasks) > 0:
                                datum["attributes"][attrib] = j["attributes"][attrib]
                        except KeyError:
                            datum["attributes"][attrib] = j["attributes"][attrib]
        self.mower_as_dict_dataclass()
        self._schedule_data_callbacks()

    def mower_as_dict_dataclass(self):
        """Convert mower data to a dictionary DataClass."""
        mowers_list = MowerList(**self.data)
        for mower in mowers_list.data:
            self.mowers[mower.id] = mower.attributes

    def callback(self, new_data):
        """Pass received websocket data to the update function."""
        if new_data:
            self._update_data(new_data)

    async def _rest_task(self):
        """Poll data periodically via Rest."""
        while True:
            await asyncio.sleep(REST_POLL_CYCLE)
            self.data = await self.get_status()
            self._schedule_data_callbacks()
