"""Module for AbstractAuth for Husqvarna Automower."""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from aiohttp import (
    ClientError,
    ClientResponse,
    ClientResponseError,
    ClientSession,
    ClientWebSocketResponse,
    WSServerHandshakeError,
)

from .const import API_BASE_URL, AUTH_HEADER_FMT, WS_URL
from .exceptions import (
    ApiException,
    ApiForbiddenException,
    AuthException,
    HusqvarnaWSServerHandshakeError,
)
from .utils import structure_token

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
        self._client_id = ""
        self.loop = asyncio.get_event_loop()
        self.ws_status: bool = True
        self.ws: ClientWebSocketResponse

    @abstractmethod
    async def async_get_access_token(self) -> str:
        """Return a valid access token."""

    async def request(
        self, method: str, url: str, **kwargs: Mapping[str, Any] | None
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

    async def _async_get_access_token(self) -> str:
        """Request a new access token."""
        try:
            return await self.async_get_access_token()
        except ClientError as err:
            raise AuthException(f"Access token failure: {err}") from err

    async def headers(self) -> dict:
        """Generate headers for ReST requests."""
        access_token = await self._async_get_access_token()
        if not self._client_id:
            token_structured = structure_token(access_token)
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

    async def websocket_connect(self) -> ClientWebSocketResponse:
        """Start a websocket connection."""
        token = await self._async_get_access_token()
        try:
            self.ws = await self._websession.ws_connect(
                url=WS_URL,
                headers={"Authorization": AUTH_HEADER_FMT.format(token)},
                heartbeat=60,
            )
        except WSServerHandshakeError as err:
            raise HusqvarnaWSServerHandshakeError(err) from err

        return self.ws
