import asyncio
import logging

import aiohttp

from . import rest

_LOGGER = logging.getLogger(__name__)

WS_URL = "wss://ws.openapi.husqvarna.dev/v1"
AUTH_HEADER_FMT = "Bearer {}"


class AutomowerSession:
    def __init__(self, api_key: str, username: str, password: str):
        self.api_key = api_key
        self.username = username
        self.password = password

        self.token = None
        self.ws_task = None
        self.token_task = None

    async def connect(
        self,
        status_cb=None,
        positions_cb=None,
        settings_cb=None,
        ws_heartbeat_interval=60.0,
    ):
        """Connect to the API.

        This method handles the login and starts a task that keep the access
        token constantly fresh. Call this method before any other methods.

        :param func status_cb: Callback for websocket status messages. Takes one dict argument which is the untouched WS response.
        :param func positions_cb: Callback for websocket positions messages. Takes one dict argument which is the untouched WS response.
        :param func settings_cb: Callback for websocket settings messages. Takes one dict argument which is the untouched WS response.
        :param float ws_heartbeat_interval: Periodicity of keep-alive pings on the websocket in seconds.

        """
        a = rest.GetAccessToken(self.api_key, self.username, self.password)
        self.token = await a.async_get_access_token()
        _LOGGER.debug("Initial token: %s", self.token)

        self.ws_task = asyncio.ensure_future(
            self._ws_task(
                status_cb,
                positions_cb,
                settings_cb,
                ws_heartbeat_interval,
            )
        )
        self.token_task = asyncio.ensure_future(self._token_monitor_task())

    async def wait(self):
        # Will hang forever. Fix stop conditions
        asyncio.gather(self.ws_task, self.token_task)

    async def get_status(self):
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

    async def action(self, mower_id, payload):
        if self.token is None:
            _LOGGER.warning("No token available")
            return None
        a = rest.Return(
            self.api_key,
            self.token["access_token"],
            self.token["provider"],
            self.token["provider"],
            self.token["token_type"],
            mower_id,
            payload,
        )
        return await a.async_mower_command()

    async def validate_token(self):
        if self.token is None:
            _LOGGER.warning("No token available")
            return None
        t = rest.ValidateAccessToken(
            self.api_key, self.token["access_token"], self.token["provider"]
        )
        return await t.async_validate_access_token()

    async def invalidate_token(self):
        if self.token is None:
            _LOGGER.warning("No token available")
            return None
        t = rest.DeleteAccessToken(
            self.api_key, self.token["provider"], self.token["access_token"]
        )
        return await t.async_delete_access_token()

    async def _token_monitor_task(self):
        while True:
            expires_in = self.token["expires_in"]

            MIN_SLEEP_TIME = 600.0  # Avoid hammering
            # Token is typically valid for 24h, request a new one some time before its expiration to avoid glitches.
            MARGIN_TIME = 60.0

            sleep_time = max(MIN_SLEEP_TIME, expires_in - MARGIN_TIME)

            _LOGGER.debug("_token_monitor_task sleeping for %s sec", sleep_time)
            await asyncio.sleep(sleep_time)

            r = rest.RefreshAccessToken(self.api_key, self.token["refresh_token"])
            self.token = await r.async_refresh_access_token()
            _LOGGER.debug("_token_monitor_task got new token %s", self.token)

    async def _ws_task(
        self,
        status_cb=None,
        positions_cb=None,
        settings_cb=None,
        ws_heartbeat_interval=60.0,
    ):
        session = aiohttp.ClientSession()
        cb_map = {
            "status-event": status_cb,
            "positions-event": positions_cb,
            "settings-event": settings_cb,
        }
        while True:
            async with session.ws_connect(
                url=WS_URL,
                headers={
                    "Authorization": AUTH_HEADER_FMT.format(self.token["access_token"])
                },
                heartbeat=ws_heartbeat_interval,
            ) as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        _LOGGER.debug("Received TEXT")
                        j = msg.json()
                        if "type" in j:
                            if j["type"] not in cb_map:
                                _LOGGER.debug("Received unknown ws type %s", j["type"])
                            cb = cb_map.get(j["type"])
                            if cb is not None:
                                session.loop.call_soon(cb, j)
                        else:
                            _LOGGER.debug("No type specified in ws resp: %s", j)
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
            _LOGGER.debug("Websocket end session")
