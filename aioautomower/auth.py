"""Module for AbstractAuth for Husqvarna Automower."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from http import HTTPStatus
import logging
from typing import Any, Optional

import aiohttp
from aiohttp import ClientError, ClientResponse, ClientResponseError, ClientSession

from .const import API_BASE_URL, AUTH_HEADER_FMT, EVENT_TYPES, WS_URL
from .exceptions import ApiException, ApiForbiddenException, AuthException
from .utils import async_structure_token

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
        self._client_id = None
        self.loop = websession.loop
        self.ws_update_cbs = []
        self.ws_data = {}

    @abstractmethod
    async def async_get_access_token(self) -> str:
        """Return a valid access token."""

    async def request(
        self, method: str, url: str, **kwargs: Optional[Mapping[str, Any]]
    ) -> ClientResponse:
        """Make a request."""
        headers = await self.headers()
        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"{self._host}/{url}"
        _LOGGER.debug("request[%s]=%s %s", method, url, kwargs.get("params"))
        if method != "get" and "json" in kwargs:
            _LOGGER.debug("request[post json]=%s", kwargs["json"])
        return await self._websession.request(method, url, **kwargs, headers=headers)

    async def get(self, url: str, **kwargs: Mapping[str, Any]) -> ClientResponse:
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

    async def post(self, url: str, **kwargs: Mapping[str, Any]) -> ClientResponse:
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

    async def patch(self, url: str, **kwargs: Mapping[str, Any]) -> ClientResponse:
        """Make a post request."""
        try:
            resp = await self.request("patch", url, **kwargs)
        except ClientError as err:
            raise ApiException(f"Error connecting to API: {err}") from err
        return await AbstractAuth._raise_for_status(resp)

    async def patch_json(self, url: str, **kwargs: Mapping[str, Any]) -> dict[str, Any]:
        """Make a post request and return a json response."""
        resp = await self.patch(url, **kwargs)
        try:
            result = await resp.json()
        except ClientError as err:
            raise ApiException("Server returned malformed response") from err
        if not isinstance(result, dict):
            raise ApiException(f"Server returned malformed response: {result}")
        _LOGGER.debug("response=%s", result)
        return result

    async def _async_get_access_token(self) -> None:
        """Requests a new access token."""
        try:
            return await self.async_get_access_token()
        except ClientError as err:
            raise AuthException(f"Access token failure: {err}") from err

    async def headers(self) -> None:
        """Generate headers for ReST requests."""
        access_token = await self._async_get_access_token()
        if not self._client_id:
            token_structured = await async_structure_token(access_token)
            self._client_id = token_structured.client_id
        return {
            "Authorization": f"Bearer {access_token}",
            "Authorization-Provider": "husqvarna",
            "Content-Type": "application/vnd.api+json",
            "X-Api-Key": self._client_id,
        }

    @staticmethod
    async def _raise_for_status(resp: ClientResponse) -> ClientResponse:
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
    async def _error_detail(resp: ClientResponse) -> list[str]:
        """Return an error message string from the API response."""
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

    def register_ws_callback(self, callback):
        """Register a websocket update callback.

        :param func callback: Callback fired on data updates.
        Takes one dict argument which is the latest websocket data.
        """
        if callback not in self.ws_update_cbs:
            self.ws_update_cbs.append(callback)

    def _schedule_ws_callback(self, cb, delay=0.0):
        """Schedule websocket callback."""
        self.loop.call_later(delay, cb, self.ws_data)

    def _schedule_ws_callbacks(self):
        """Schedule all websocket callbacks."""
        for cb in self.ws_update_cbs:
            self._schedule_ws_callback(cb)

    async def websocket(self) -> dict[str, dict]:
        """Start a websocket conenction."""
        async with self._websession.ws_connect(
            url=WS_URL,
            headers={
                "Authorization": AUTH_HEADER_FMT.format(
                    await self._async_get_access_token()
                )
            },
            heartbeat=60,
        ) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    msg_dict = msg.json()
                    if "type" in msg_dict:
                        if msg_dict["type"] in EVENT_TYPES:
                            _LOGGER.debug(
                                "Got %s, data: %s", msg_dict["type"], msg_dict
                            )
                            self.ws_data = msg_dict
                            self._schedule_ws_callbacks()
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
                    else:
                        _LOGGER.debug("Discarded websocket response: %s", msg_dict)
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
                    await ws.close()
                elif msg.type == aiohttp.WSMsgType.CLOSING:
                    _LOGGER.debug("Received CLOSING")
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    _LOGGER.debug("Received CLOSED")
                else:
                    _LOGGER.debug("Received msg.type=%d", msg.type)
