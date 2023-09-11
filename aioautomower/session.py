"""Module to connect to Automower with websocket."""
import asyncio
import datetime
import json
import logging
import time
from typing import Literal, Any, Optional
from dataclasses import dataclass
from dacite import from_dict
import aiohttp

from . import rest
from .const import (
    AUTH_HEADER_FMT,
    EVENT_TYPES,
    HUSQVARNA_URL,
    MARGIN_TIME,
    MIN_SLEEP_TIME,
    REST_POLL_CYCLE,
    REST_POLL_CYCLE_LE,
    WS_STATUS_UPDATE_CYLE,
    WS_TOLERANCE_TIME,
    WS_URL,
    HeadlightModes,
)

_LOGGER = logging.getLogger(__name__)


class AutomowerSession:
    """Session"""

    def __init__(
        self,
        api_key: str,
        token: dict = None,
        low_energy=True,
        ws_heartbeat_interval: float = 60.0,
        loop=None,
    ) -> None:
        """Create a session.

        :param str api_key: A 36 digit api key.
        :param dict token: A token as returned by rest.GetAccessToken.async_get_access_token()
        :param float ws_heartbeat_interval: Periodicity of keep-alive pings on the websocket in seconds.
        :param loop: Event-loop for task execution. If None, the event loop in the current OS thread is used.
        """
        self.api_key = api_key
        self.token = token
        self.data_update_cbs = []
        self.token_update_cbs = []
        self.ws_heartbeat_interval = ws_heartbeat_interval
        self.rest_task = False
        self.low_energy = low_energy
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

        self.data = {}
        self.dataclass = list()
        self.all_mowers = []

        self.ws_task = None
        self.token_task = None
        self.websocket_monitor_task = None
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

    async def logincc(self, client_secret: str) -> dict:
        """Login with client credentials.

        This method gets an access token with a client_id (Api key) and a client_secret.
        This token can't be refreshed. Create a new one after it is expired.

        :param str client_secret: Your client_secret
        :return dict: The token as returned by
        rest.GetAccessTokenClientCredentials.async_get_access_token().
        You can store this persistently and pass it to the constructor
        on subsequent instantiations.
        """
        a = rest.GetAccessTokenClientCredentials(self.api_key, client_secret)
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
        _LOGGER.debug("1")
        if self.token is None:
            raise AttributeError("No token to connect with.")
        if time.time() > (self.token["expires_at"] - MARGIN_TIME):
            await self.refresh_token()

        _LOGGER.debug("2")
        self.data = await self.get_status()
        self.dataclass = from_dict(data_class=MowerList, data=self.data)
        self._schedule_data_callbacks()

        if "amc:api" not in self.token["scope"]:
            _LOGGER.error(
                "Your API-Key is not compatible to the websocket, please refresh it on %s",
                HUSQVARNA_URL,
            )
        else:
            self.ws_task = self.loop.create_task(self._ws_task())
        self.rest_task = self.loop.create_task(self._rest_task())
        self.token_task = self.loop.create_task(self._token_monitor_task())

    async def ws_and_token_session(self):
        """Connect to the API.

        This method handles the login and starts a task that keep the access
        token constantly fresh. This method works only, if the token is created with the
        Authorization Code Grant. Call this method before any other methods.
        """
        if self.token is None:
            raise AttributeError("No token to connect with.")
        if time.time() > (self.token["expires_at"] - MARGIN_TIME):
            await self.refresh_token()

        self.data = await self.get_status()

        if "amc:api" not in self.token["scope"]:
            raise NotImplementedError()
        else:
            self.ws_task = self.loop.create_task(self._ws_task())
        self.token_task = self.loop.create_task(self._token_monitor_task())

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
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass

    async def get_status(self):
        """Get mower status via Rest."""
        if self.token is None:
            _LOGGER.warning("No token available")
            return None
        d = rest.GetMowerData(
            self.api_key,
            self.token["access_token"],
            self.token["provider"],
            self.token["token_type"],
        )
        return await d.async_mower_state()

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
        """Removes any ovveride on the Planner and let the mower
        resume to the schedule set by the Calendar"""
        command_type = "actions"
        payload = {"data": {"type": "ResumeSchedule"}}
        try:
            await self.send_command_via_rest(mower_id, payload, command_type)
        except rest.CommandNotPossibleError as exception:
            _LOGGER.error("Command couldn't be sent to the command que: %s", exception)

    async def pause_mowing(self, mower_id: str):
        """Send pause mowing command to the mower via Rest."""
        command_type = "actions"
        payload = {"data": {"type": "Pause"}}
        await self.send_command_via_rest(mower_id, payload, command_type)

    async def park_until_next_schedule(self, mower_id: str):
        """Send park until next schedule command to the mower."""
        command_type = "actions"
        payload = {"data": {"type": "ParkUntilNextSchedule"}}
        await self.send_command_via_rest(mower_id, payload, command_type)

    async def park_until_further_notice(self, mower_id: str):
        """Send park until further notice command to the mower."""
        command_type = "actions"
        payload = {"data": {"type": "ParkUntilFurtherNotice"}}
        await self.send_command_via_rest(mower_id, payload, command_type)

    async def park_for(self, mower_id: str, duration_in_min: int):
        """Parks the mower for a period of minutes. The mower will drive to
        the charching station and park for the duration set by the command."""
        command_type = "actions"
        payload = {
            "data": {
                "type": "Park",
                "attributes": {"duration": duration_in_min},
            }
        }
        await self.send_command_via_rest(mower_id, payload, command_type)

    async def start_for(self, mower_id: str, duration_in_min: int):
        """Start the mower for a period of minutes."""
        command_type = "actions"
        payload = {
            "data": {
                "type": "Park",
                "attributes": {"duration": duration_in_min},
            }
        }
        await self.send_command_via_rest(mower_id, payload, command_type)

    async def set_cutting_height(self, mower_id: str, cutting_height: int):
        """Start the mower for a period of minutes."""
        command_type = "settings"
        payload = {
            "data": {
                "type": "settings",
                "attributes": {"cuttingHeight": cutting_height},
            }
        }
        await self.send_command_via_rest(mower_id, payload, command_type)

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
        command_type = "settings"
        payload = {
            "data": {
                "type": "settings",
                "attributes": {"headlight": {"mode": headlight_mode}},
            }
        }
        await self.send_command_via_rest(mower_id, payload, command_type)

    async def set_calendar(
        self,
        mower_id: str,
        task_list: list,
    ):
        """Send calendar task to the mower."""
        command_type = "calendar"
        payload = {
            "data": {
                "type": "calendar",
                "attributes": {"tasks": task_list},
            }
        }
        await self.send_command_via_rest(mower_id, payload, command_type)

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

    async def refresh_token(self):
        """Refresh token via Rest."""
        if "refresh_token" not in self.token:
            _LOGGER.warning("No refresh token available")
            return None
        _LOGGER.debug("Refresh access token")
        r = rest.RefreshAccessToken(self.api_key, self.token["refresh_token"])
        self.token = await r.async_refresh_access_token()
        self._schedule_token_callbacks()

    async def _token_monitor_task(self):
        while True:
            if "expires_at" in self.token:
                expires_at = self.token["expires_at"]
                sleep_time = max(MIN_SLEEP_TIME, expires_at - time.time() - MARGIN_TIME)
            else:
                sleep_time = MIN_SLEEP_TIME

            _LOGGER.debug("token_monitor_task sleeping for %s sec", sleep_time)
            await asyncio.sleep(sleep_time)
            await self.refresh_token()

    def _update_data(self, j):
        if self.data is None:
            _LOGGER.error("Failed to update data with ws response (no data)")
            return
        _LOGGER.debug("5")
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
                        _LOGGER.debug(
                            "j['attributes']['positions']: %s",
                            j["attributes"]["positions"],
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
                return
        _LOGGER.error("Failed to update data with ws response (id not found)")

    def _schedule_token_callback(self, cb, delay=0.0):
        if self.token is None:
            _LOGGER.debug("No token available. Will not schedule callback")
            return
        self.dataclass = from_dict(data_class=MowerList, data=self.data)
        self.loop.call_later(delay, cb, self.token)

    def _schedule_token_callbacks(self):
        for cb in self.token_update_cbs:
            self._schedule_token_callback(cb)

    def _schedule_data_callback(self, cb, delay=0.0):
        if self.data is None:
            _LOGGER.debug("No data available. Will not schedule callback")
            return
        self.loop.call_later(delay, cb, self.data)

    def _schedule_data_callbacks(self):
        for cb in self.data_update_cbs:
            self._schedule_data_callback(cb)

    async def _ws_task(self):
        printed_err_msg = False
        self.websocket_monitor_task = self.loop.create_task(
            self._websocket_monitor_task()
        )
        async with aiohttp.ClientSession() as session:
            while True:
                if self.token is None or "access_token" not in self.token:
                    if not printed_err_msg:
                        # New login() needed but since we don't store username
                        # and password, we cannot get request one.
                        #
                        # TODO: Add callback for this to notify the user that
                        # this has happened.
                        _LOGGER.warning("No access token for ws auth. Retrying")
                        printed_err_msg = True
                    await asyncio.sleep(60.0)
                    continue
                printed_err_msg = False
                async with session.ws_connect(
                    url=WS_URL,
                    headers={
                        "Authorization": AUTH_HEADER_FMT.format(
                            self.token["access_token"]
                        )
                    },
                    heartbeat=self.ws_heartbeat_interval,
                ) as ws:
                    _LOGGER.debug("Websocket (re)connected")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            j = msg.json()
                            if "type" in j:
                                if j["type"] in EVENT_TYPES:
                                    self._update_data(j)
                                    _LOGGER.debug("Got %s, data: %s", j["type"], j)
                                    self._schedule_data_callbacks()
                                else:
                                    _LOGGER.warning(
                                        "Received unknown ws type %s", j["type"]
                                    )
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

    async def _websocket_monitor_task(self):
        """Monitor, if the websocket still sends updates. If not, check, via REST,
        if the mower is connected. If there are no recent updates, Start REST task
        to get information"""
        message_sent = []
        mower_connected = []
        for idx, ent in enumerate(self.data["data"]):
            mower_connected.append(
                self.data["data"][idx]["attributes"]["metadata"]["connected"]
            )
            message_sent.append(not mower_connected[idx])
        while True:
            for idx, ent in enumerate(self.data["data"]):
                mower_connected[idx] = self.data["data"][idx]["attributes"]["metadata"][
                    "connected"
                ]
                if not mower_connected[idx] and not message_sent[idx]:
                    message_sent[idx] = True
                    _LOGGER.warning(
                        "Connection to %s lost",
                        self.data["data"][idx]["attributes"]["system"]["name"],
                    )
                if mower_connected[idx] and message_sent[idx]:
                    message_sent[idx] = False
                    _LOGGER.info(
                        "Connected to %s again",
                        self.data["data"][idx]["attributes"]["system"]["name"],
                    )
                timestamp = (
                    self.data["data"][idx]["attributes"]["metadata"]["statusTimestamp"]
                    / 1000
                )
                now = datetime.datetime.now().timestamp()
                age = now - timestamp
                _LOGGER.debug("Age in sec: %i", age)
            ws_monitor_sleep_time = min(
                max(WS_STATUS_UPDATE_CYLE + WS_TOLERANCE_TIME - age, REST_POLL_CYCLE),
                WS_STATUS_UPDATE_CYLE + WS_TOLERANCE_TIME,
            )
            if age < (WS_STATUS_UPDATE_CYLE + WS_TOLERANCE_TIME):
                _LOGGER.debug(
                    "websocket_monitor_task sleeping for %ss", ws_monitor_sleep_time
                )
            any_mowers_connected = any(mower_connected)
            if age > (WS_STATUS_UPDATE_CYLE + WS_TOLERANCE_TIME):
                if not any_mowers_connected:
                    _LOGGER.debug("No ws updates anymore, and mower disconnected")
                if any_mowers_connected:
                    _LOGGER.debug(
                        "No ws updates anymore and mower connected, ws probably down or mower shortly before disconnecting"
                    )
            await asyncio.sleep(ws_monitor_sleep_time)


@dataclass
class System:
    name: str
    model: str
    serialNumber: int


@dataclass
class Battery:
    batteryPercent: int


@dataclass
class Capabilities:
    headlights: bool
    workAreas: bool
    position: bool
    stayOutZones: bool


@dataclass
class Mower:
    mode: str
    activity: str
    state: str
    errorCode: int
    errorCodeTimestamp: int


@dataclass
class Calendar:
    start: int
    duration: int
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool


@dataclass
class Tasks:
    tasks: list[Calendar]


@dataclass
class Override:
    action: str


@dataclass
class Planner:
    nextStartTimestamp: int
    override: Override
    restrictedReason: str


@dataclass
class Metadata:
    connected: bool
    statusTimestamp: int


@dataclass
class Positions:
    latitude: float
    longitude: float


@dataclass
class Statistics:
    cuttingBladeUsageTime: Optional[int]
    numberOfChargingCycles: int
    numberOfCollisions: int
    totalChargingTime: int
    totalCuttingTime: int
    totalDriveDistance: int
    totalRunningTime: int
    totalSearchingTime: int


@dataclass
class Headlight:
    mode: Optional[str]


@dataclass
class Zones:
    Id: str
    name: str
    enabled: bool


@dataclass
class StayOutZones:
    dirty: bool
    zones: list[Zones]


@dataclass
class WorkAreas:
    workAreaId: int
    name: str
    cuttingHeight: int


@dataclass
class MowerAttributes:
    system: System
    battery: Battery
    capabilities: Capabilities
    mower: Mower
    calendar: Tasks
    planner: Planner
    metadata: Metadata
    positions: Optional[list[Positions]]
    statistics: Statistics
    cuttingHeight: Optional[int]
    headlight: Headlight
    stayOutZones: Optional[StayOutZones]
    workAreas: Optional[WorkAreas]


@dataclass
class MowerData:
    type: str
    id: str
    attributes: MowerAttributes


@dataclass
class MowerList:
    data: list[MowerData]
