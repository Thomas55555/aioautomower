"""Module to connect to Automower with websocket."""
from abc import ABC, abstractmethod
from collections.abc import Mapping
import asyncio
import contextlib
import json
import logging
import time
from aiohttp import ClientSession, ClientResponse, ClientError, ClientResponseError
import aiohttp
from dacite import from_dict
from typing import Any, Optional, Literal, List
from . import rest
from .const import (
    AUTH_HEADER_FMT,
    EVENT_TYPES,
    HUSQVARNA_URL,
    MARGIN_TIME,
    MIN_SLEEP_TIME,
    REST_POLL_CYCLE,
    REST_POLL_CYCLE_LE,
    WS_URL,
    MOWER_API_BASE_URL,
    HeadlightModes,
    MowerList,
    MowerAttributes,
)
import jwt
from .const import (
    AUTH_API_BASE_URL as API_BASE_URL,
    AUTH_HEADERS as AUTHORIZATION_HEADER,
)
from .exceptions import ApiException, AuthException, ApiForbiddenException
from http import HTTPStatus

ERROR = "error"
STATUS = "status"
MESSAGE = "message"
_LOGGER = logging.getLogger(__name__)


class AbstractAuth(ABC):
    """Abstract class to make authenticated requests."""

    def __init__(self, websession: ClientSession, host: str) -> None:
        """Initialize the auth."""
        self._websession = websession
        self._host = host if host is not None else API_BASE_URL

    @abstractmethod
    async def async_get_access_token(self) -> str:
        """Return a valid access token."""

    async def request(
        self, method: str, url: str, **kwargs: Optional[Mapping[str, Any]]
    ) -> aiohttp.ClientResponse:
        """Make a request."""
        try:
            access_token = await self.async_get_access_token()
        except ClientError as err:
            raise AuthException(f"Access token failure: {err}") from err

        token_decoded = jwt.decode(access_token, options={"verify_signature": False})
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Authorization-Provider": "husqvarna",
            "Content-Type": "application/vnd.api+json",
            "X-Api-Key": token_decoded["client_id"],
        }
        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"{self._host}/{url}"
        _LOGGER.debug("request[%s]=%s %s", method, url, kwargs.get("params"))
        if method != "get" and "json" in kwargs:
            _LOGGER.debug("request[post json]=%s", kwargs["json"])
        return await self._websession.request(method, url, **kwargs, headers=headers)

    async def get(
        self, url: str, **kwargs: Mapping[str, Any]
    ) -> aiohttp.ClientResponse:
        """Make a get request."""
        try:
            resp = await self.request("get", url, **kwargs)
        except ClientError as err:
            raise ApiException(f"Error connecting to API: {err}") from err
        return await AbstractAuth._raise_for_status(resp)

    async def get_json(self, url: str, **kwargs: Mapping[str, Any]) -> dict[str, Any]:
        """Make a get request and return json response."""
        resp = await self.get(url, **kwargs)
        try:
            result = await resp.json(encoding="UTF-8")
        except ClientError as err:
            raise ApiException("Server returned malformed response") from err
        if not isinstance(result, dict):
            raise ApiException(f"Server return malformed response: {result}")
        _LOGGER.debug("response=%s", result)
        return result

    async def post(
        self, url: str, **kwargs: Mapping[str, Any]
    ) -> aiohttp.ClientResponse:
        """Make a post request."""
        try:
            resp = await self.request("post", url, **kwargs)
        except ClientError as err:
            raise ApiException(f"Error connecting to API: {err}") from err
        return await AbstractAuth._raise_for_status(resp)

    async def post_json(self, url: str, **kwargs: Mapping[str, Any]) -> dict[str, Any]:
        """Make a post request and return a json response."""
        resp = await self.post(url, **kwargs)
        try:
            result = await resp.json()
        except ClientError as err:
            raise ApiException("Server returned malformed response") from err
        if not isinstance(result, dict):
            raise ApiException(f"Server returned malformed response: {result}")
        _LOGGER.debug("response=%s", result)
        return result

    @staticmethod
    async def _raise_for_status(resp: aiohttp.ClientResponse) -> aiohttp.ClientResponse:
        """Raise exceptions on failure methods."""
        detail = await AbstractAuth._error_detail(resp)
        try:
            resp.raise_for_status()
        except ClientResponseError as err:
            if err.status == HTTPStatus.FORBIDDEN:
                raise ApiForbiddenException(
                    f"Forbidden response from API: {err}"
                ) from err
            if err.status == HTTPStatus.UNAUTHORIZED:
                raise AuthException(f"Unable to authenticate with API: {err}") from err
            detail.append(err.message)
            raise ApiException(": ".join(detail)) from err
        except ClientError as err:
            raise ApiException(f"Error from API: {err}") from err
        return resp

    @staticmethod
    async def _error_detail(resp: aiohttp.ClientResponse) -> List[str]:
        """Resturns an error message string from the APi response."""
        if resp.status < 400:
            return []
        try:
            result = await resp.json()
            error = result.get(ERROR, {})
        except ClientError:
            return []
        message = ["Error from API", f"{resp.status}"]
        if STATUS in error:
            message.append(f"{error[STATUS]}")
        if MESSAGE in error:
            message.append(error[MESSAGE])
        return message


class AutomowerSession:
    """Session."""

    def __init__(
        self,
        auth: AbstractAuth,
        low_energy=True,
        ws_heartbeat_interval: float = 60.0,
        loop=None,
        handle_token=True,
        handle_rest=True,
    ) -> None:
        """Create a session.

        :param str api_key: A 36 digit api key.
        :param dict token: A token as returned by rest.GetAccessToken.async_get_access_token()
        :param float ws_heartbeat_interval: Periodicity of keep-alive pings on the websocket in seconds.
        :param loop: Event-loop for task execution. If None, the event loop in the current OS thread is used.
        """
        self.auth = auth
        self.handle_token = handle_token
        self.handle_rest = handle_rest
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
        self.mowers = {}

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

        self._schedule_data_callbacks()

        if self.handle_rest:
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
        mower_list = await self.auth.get_json(MOWER_API_BASE_URL)
        for idx, ent in enumerate(mower_list["data"]):
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
        """Removes any ovveride on the Planner and let the mower
        resume to the schedule set by the Calendar.
        """
        command_type = "actions"
        data = {"data": {"type": "ResumeSchedule"}}
        url = f"{MOWER_API_BASE_URL}{mower_id}/{command_type}"
        await self.auth.post_json(url, json=data)

    async def pause_mowing(self, mower_id: str):
        """Send pause mowing command to the mower via Rest."""
        command_type = "actions"
        data = {"data": {"type": "Pause"}}
        url = f"{MOWER_API_BASE_URL}{mower_id}/{command_type}"
        await self.auth.post_json(url, json=data)

    async def park_until_next_schedule(self, mower_id: str):
        """Send park until next schedule command to the mower."""
        command_type = "actions"
        data = {"data": {"type": "ParkUntilNextSchedule"}}
        url = f"{MOWER_API_BASE_URL}{mower_id}/{command_type}"
        await self.auth.post_json(url, json=data)

    async def park_until_further_notice(self, mower_id: str):
        """Send park until further notice command to the mower."""
        command_type = "actions"
        data = {"data": {"type": "ParkUntilFurtherNotice"}}
        url = f"{MOWER_API_BASE_URL}{mower_id}/{command_type}"
        await self.auth.post_json(url, json=data)

    async def park_for(self, mower_id: str, duration_in_min: int):
        """Parks the mower for a period of minutes. The mower will drive to
        the charching station and park for the duration set by the command.
        """
        command_type = "actions"
        data = {
            "data": {
                "type": "Park",
                "attributes": {"duration": duration_in_min},
            }
        }
        url = f"{MOWER_API_BASE_URL}{mower_id}/{command_type}"
        await self.auth.post_json(url, json=data)

    async def start_for(self, mower_id: str, duration_in_min: int):
        """Start the mower for a period of minutes."""
        command_type = "actions"
        data = {
            "data": {
                "type": "Park",
                "attributes": {"duration": duration_in_min},
            }
        }
        url = f"{MOWER_API_BASE_URL}{mower_id}/{command_type}"
        await self.auth.post_json(url, json=data)

    async def set_cutting_height(self, mower_id: str, cutting_height: int):
        """Start the mower for a period of minutes."""
        command_type = "settings"
        data = {
            "data": {
                "type": "settings",
                "attributes": {"cuttingHeight": cutting_height},
            }
        }
        url = f"{MOWER_API_BASE_URL}{mower_id}/{command_type}"
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
        command_type = "settings"
        data = {
            "data": {
                "type": "settings",
                "attributes": {"headlight": {"mode": headlight_mode}},
            }
        }
        url = f"{MOWER_API_BASE_URL}{mower_id}/{command_type}"
        await self.auth.post_json(url, json=data)

    async def set_calendar(
        self,
        mower_id: str,
        task_list: list,
    ):
        """Send calendar task to the mower."""
        command_type = "calendar"
        data = {
            "data": {
                "type": "calendar",
                "attributes": {"tasks": task_list},
            }
        }
        url = f"{MOWER_API_BASE_URL}{mower_id}/{command_type}"
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

    async def refresh_token(self):
        """Refresh token via Rest."""
        if "refresh_token" not in self.token:
            _LOGGER.warning("No refresh token available")
            return None
        _LOGGER.debug("Refresh access token")
        r = rest.RefreshAccessToken(self.api_key, self.token["refresh_token"])
        self.token = await r.async_refresh_access_token()
        _LOGGER.debug("new token: %s", self.token)
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
            # await self.oauth_session.async_ensure_token_valid()
            await self.async_get_access_token()

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
        if self.handle_rest:
            if self.data is None:
                _LOGGER.debug("No data available. Will not schedule callback")
                return
        self.loop.call_later(delay, cb, self.mowers)

    def _schedule_data_callbacks(self):
        for cb in self.data_update_cbs:
            self._schedule_data_callback(cb)

    async def _ws_task(self):
        printed_err_msg = False
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
                                    _LOGGER.debug("Got %s, data: %s", j["type"], j)
                                    self._update_data(j)
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
