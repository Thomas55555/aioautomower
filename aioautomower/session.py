"""Module to connect to Automower with websocket."""
import asyncio
import contextlib
import json
import logging
import time
from typing import Literal

import aiohttp
from dacite import from_dict

from . import rest
from .auth import AbstractAuth
from .const import (
    EVENT_TYPES,
    MARGIN_TIME,
    MIN_SLEEP_TIME,
    REST_POLL_CYCLE,
    HeadlightModes,
    MowerList,
)

_LOGGER = logging.getLogger(__name__)


class AutomowerEndpoint:
    mowers = "mowers/"
    actions = "mowers/{mower_id}/actions"
    calendar = "mowers/{mower_id}/calendar"
    settings = "mowers/{mower_id}/settings"
    stay_out_zones = "mowers/{mower_id}/stayOutZones/{stay_out_id}"
    work_area_calendar = "mowers/{mower_id}/workAreas{work_area_id}/calendar"


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
        self.ws_heartbeat_interval: float = (60.0,)
        self.rest_task = False
        self.loop = asyncio.get_event_loop()
        self.token = None
        self.data = {}
        self.mowers = {}

        self.ws_task = None

        self.token_task = None
        self.rest_task = None

    def register_data_callback(self, callback, schedule_immediately=False):
        """Register a data update callback.

        :param func callback: Callback fired on data updates. Takes one dict argument which is the up-to-date mower data list.
        :param bool schedule_immediately: Schedule callback immediately (if data is available).
        """
        if callback not in self.data_update_cbs:
            self.data_update_cbs.append(callback)
        if schedule_immediately:
            self._schedule_data_callback(
                callback, delay=1e-3
            )  # Need a delay for home assistant to finish entity setup.

    def unregister_data_callback(self, callback):
        """Unregister a data update callback.

        :param func callback: Callback fired on data updates. Takes one dict argument which is the up-to-date mower data list.
        """
        if callback in self.data_update_cbs:
            self.data_update_cbs.remove(callback)

    def register_token_callback(self, callback, schedule_immediately=False):
        """Register a token update callback.

        :param func callback: Callback fired on token updates. Takes one dict argument which is the newly received token.
        :param bool schedule_immediately: Schedule callback immediately (if token is available).
        """
        if callback not in self.token_update_cbs:
            self.token_update_cbs.append(callback)
        if schedule_immediately:
            self._schedule_token_callback(
                callback, delay=1e-3
            )  # Need a delay for home assistant to finish entity setup.

    async def logincc(self, api_key: str, client_secret: str) -> dict:
        """Login with client credentials.

        This method gets an access token with a client_id (Api key) and a client_secret.
        This token can't be refreshed. Create a new one after it is expired.

        :param str client_secret: Your client_secret
        :return dict: The token as returned by
        rest.GetAccessTokenClientCredentials.async_get_access_token().
        You can store this persistently and pass it to the constructor
        on subsequent instantiations.
        """
        a = rest.GetAccessTokenClientCredentials(api_key, client_secret)
        self.token = await a.async_get_access_token()
        self._schedule_token_callbacks()
        return self.token

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
            self.data = await self.get_status()
            self.rest_task = self.loop.create_task(self._rest_task())

        self.ws_task = self.loop.create_task(self._ws_task())

    async def close(self):
        """Close the session."""
        for task in [
            self.ws_task,
            self.token_task,
            self.websocket_monitor_task,
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

    async def action(self, mower_id: str, payload: str, command_type: str):
        """Send command to the mower via Rest."""
        if self.token is None:
            _LOGGER.warning("No token available")
            return None
        a = rest.Return(
            self.api_key,
            self.token["access_token"],
            self.token["provider"],
            self.token["token_type"],
            mower_id,
            payload,
            command_type,
        )
        return await a.async_mower_command()

    async def resume_schedule(self, mower_id: str):
        """Remove any ovveride on the Planner and let the mower
        resume to the schedule set by the Calendar.
        """
        data = {"data": {"type": "ResumeSchedule"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=data)

    async def pause_mowing(self, mower_id: str):
        """Send pause mowing command to the mower via Rest."""
        data = {"data": {"type": "Pause"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=data)

    async def park_until_next_schedule(self, mower_id: str):
        """Send park until next schedule command to the mower."""
        data = {"data": {"type": "ParkUntilNextSchedule"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=data)

    async def park_until_further_notice(self, mower_id: str):
        """Send park until further notice command to the mower."""
        data = {"data": {"type": "ParkUntilFurtherNotice"}}
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=data)

    async def park_for(self, mower_id: str, duration_in_min: int):
        """Parks the mower for a period of minutes. The mower will drive to
        the charching station and park for the duration set by the command.
        """
        data = {
            "data": {
                "type": "Park",
                "attributes": {"duration": duration_in_min},
            }
        }
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=data)

    async def start_for(self, mower_id: str, duration_in_min: int):
        """Start the mower for a period of minutes."""
        data = {
            "data": {
                "type": "Park",
                "attributes": {"duration": duration_in_min},
            }
        }
        url = AutomowerEndpoint.actions.format(mower_id=mower_id)
        await self.auth.post_json(url, json=data)

    async def set_cutting_height(self, mower_id: str, cutting_height: int):
        """Start the mower for a period of minutes."""
        data = {
            "data": {
                "type": "settings",
                "attributes": {"cuttingHeight": cutting_height},
            }
        }
        url = AutomowerEndpoint.settings.format(mower_id=mower_id)
        await self.auth.post_json(url, json=data)

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
        data = {
            "data": {
                "type": "settings",
                "attributes": {"headlight": {"mode": headlight_mode}},
            }
        }
        url = AutomowerEndpoint.settings.format(mower_id=mower_id)
        await self.auth.post_json(url, json=data)

    async def set_calendar(
        self,
        mower_id: str,
        task_list: list,
    ):
        """Send calendar task to the mower."""
        data = {
            "data": {
                "type": "calendar",
                "attributes": {"tasks": task_list},
            }
        }
        url = AutomowerEndpoint.calendar.format(mower_id=mower_id)
        await self.auth.post_json(url, json=data)

    async def send_command_via_rest(
        self, mower_id: str, payload: dict, command_type: str
    ):
        """Send a command to the mower."""
        json_payload = json.dumps(payload)
        rest_init = rest.Return(
            self.api_key,
            self.token["access_token"],
            self.token["provider"],
            self.token["token_type"],
            mower_id,
            json_payload,
            command_type,
        )
        try:
            await rest_init.async_mower_command()
        except rest.CommandNotPossibleError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

    async def invalidate_token(self):
        """Invalidate token via Rest."""
        if self.token is None:
            _LOGGER.warning("No token available")
            return None
        token = rest.RevokeAccessToken(self.token["access_token"])
        return await token.async_delete_access_token()

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
            _LOGGER.error("Failed to update data with ws response (no data)")
            return
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
        mowers_list = from_dict(data_class=MowerList, data=self.data)
        for mower in mowers_list.data:
            self.mowers[mower.id] = mower.attributes

    def _schedule_token_callback(self, cb, delay=0.0):
        if self.token is None:
            _LOGGER.debug("No token available. Will not schedule callback")
            return
        self.loop.call_later(delay, cb, self.token)

    def _schedule_token_callbacks(self):
        for cb in self.token_update_cbs:
            self._schedule_token_callback(cb)

    def _schedule_data_callback(self, cb, delay=0.0):
        if self.poll:
            if self.data is None:
                _LOGGER.debug("No data available. Will not schedule callback")
                return
        self.loop.call_later(delay, cb, self.mowers)

    def _schedule_data_callbacks(self):
        for cb in self.data_update_cbs:
            self._schedule_data_callback(cb)

    async def _ws_task(self):
        async with await self.auth.websocket() as ws:
            _LOGGER.debug("Websocket (re)connected")
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    j = msg.json()
                    if "type" in j:
                        if j["type"] in EVENT_TYPES:
                            _LOGGER.debug("Got %s, data: %s", j["type"], j)
                            self._update_data(j)
                            self._schedule_data_callbacks()
                        else:
                            _LOGGER.warning("Received unknown ws type %s", j["type"])
                    elif "ready" in j and "connectionId" in j:
                        _LOGGER.debug(
                            "Websocket ready=%s (id='%s')",
                            j["ready"],
                            j["connectionId"],
                        )
                    else:
                        _LOGGER.debug("Discarded websocket response: %s", j)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.debug("Received ERROR")
                    break
                elif msg.type == aiohttp.WSMsgType.CONTINUATION:
                    _LOGGER.debug("Received CONTINUATION")
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    _LOGGER.debug("Received BINARY")
                elif msg.type == aiohttp.WSMsgType.PING:
                    _LOGGER.debug("Received PING")
                elif msg.type == aiohttp.WSMsgType.PONG:
                    _LOGGER.debug("Received PONG")
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    _LOGGER.debug("Received CLOSE")
                elif msg.type == aiohttp.WSMsgType.CLOSING:
                    _LOGGER.debug("Received CLOSING")
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    _LOGGER.debug("Received CLOSED")
                else:
                    _LOGGER.debug("Received msg.type=%d", msg.type)

    async def _rest_task(self):
        """Poll data periodically via Rest."""
        while True:
            _LOGGER.debug(
                "LE: %s",
                self.low_energy,
            )
            if self.low_energy is True:
                await asyncio.sleep(REST_POLL_CYCLE_LE)
            if self.low_energy is False:
                await asyncio.sleep(REST_POLL_CYCLE)
            self.data = await self.get_status()
            self._schedule_data_callbacks()
