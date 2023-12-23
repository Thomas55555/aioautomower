"""An example file to use this library."""

import asyncio
import logging
import time
from typing import cast

from aiohttp import ClientSession

from aioautomower.auth import AbstractAuth
from aioautomower.const import API_BASE_URL
from aioautomower.session import AutomowerSession
from aioautomower.utils import async_get_access_token, async_structure_token

_LOGGER = logging.getLogger(__name__)


CLIENT_ID = "1e33fa27-ca34-4762-9a9e-5967f873a731"
CLIENT_SECRET = "763adf3c-1b16-4c3b-91cd-c07316243881"
CLOCK_OUT_OF_SYNC_MAX_SEC = 20


class AsyncTokenAuth(AbstractAuth):
    """Provide Husqvarna Automower authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        websession: ClientSession,
    ) -> None:
        """Initialize Husqvarna Automower auth."""
        super().__init__(websession, API_BASE_URL)
        self.token = None

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        if not self.token:
            self.token = await async_get_access_token(CLIENT_ID, CLIENT_SECRET)
            token_structured = await async_structure_token(self.token["access_token"])
            print("Token expires at: ", token_structured.exp)
        return self.token["access_token"]

    @property
    def valid_token(self) -> bool:
        """Return if token is still valid."""
        return (
            cast(float, self.token["expires_at"])
            > time.time() + CLOCK_OUT_OF_SYNC_MAX_SEC
        )

    async def async_ensure_token_valid(self) -> None:
        """Ensure that the current token is valid."""
        if self.valid_token:
            return

        self.token = await async_get_access_token()


async def main():
    """Establish connection to mower and print states for 5 minutes."""
    websession = ClientSession()
    automower_api = AutomowerSession(AsyncTokenAuth(websession), poll=True)
    # Add a callback, can be done at any point in time and
    # multiple callbacks can be added.
    automower_api.register_data_callback(callback)
    await automower_api.connect()
    await asyncio.sleep(3000)
    # The close() will stop the websocket and the token refresh tasks
    await automower_api.close()


def callback(ws_data):
    """Process websocket callbacks and write them to the DataUpdateCoordinator."""
    print("Mowers data:", ws_data)


asyncio.run(main())
