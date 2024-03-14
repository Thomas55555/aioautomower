"""An example file to use this library."""

import asyncio
import logging
import time
from typing import cast

from aiohttp import ClientSession

from aioautomower.auth import AbstractAuth
from aioautomower.const import API_BASE_URL
from aioautomower.session import AutomowerSession
from aioautomower.model import MowerAttributes
from aioautomower.utils import async_get_access_token, structure_token

_LOGGER = logging.getLogger(__name__)


CLIENT_ID = "1e33fa27-ca34-4762-9a9e-5967f873a733"
CLIENT_SECRET = "763adf3c-1b16-4c3b-91cd-c07316243880"
CLOCK_OUT_OF_SYNC_MAX_SEC = 20
MAX_WS_RECONNECT_TIME = 600


class AsyncTokenAuth(AbstractAuth):
    """Provide Automower authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        websession: ClientSession,
    ) -> None:
        """Initialize Husqvarna Automower auth."""
        super().__init__(websession, API_BASE_URL)
        self.token: dict = {}

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        if not self.token:
            self.token = await async_get_access_token(CLIENT_ID, CLIENT_SECRET)
            token_structured = structure_token(self.token["access_token"])
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
        self.token = await async_get_access_token(CLIENT_ID, CLIENT_SECRET)


async def main():
    """Establish connection to mower and print states for 5 minutes."""
    websession = ClientSession()
    automower_api = AutomowerSession(AsyncTokenAuth(websession), poll=True)
    # Add a callback, can be done at any point in time and
    # multiple callbacks can be added.
    asyncio.create_task(_client_listen(automower_api))
    await asyncio.sleep(1)
    await automower_api.connect()
    automower_api.register_data_callback(callback)
    # pylint: disable=unused-variable
    for mower_id in automower_api.data:
        await asyncio.sleep(5)
        # await automower_api.park_until_next_schedule(mower_id)
        # Uncomment the line above to let all your mowers park until next schedule.
        await asyncio.sleep(5)
        # await automower_api.park_until_further_notice(mower_id)
        # Uncomment the line above to let all your mowers park until further notice.
        await asyncio.sleep(5)
        # await automower_api.resume_schedule(mower_id)
        # Uncomment the line above to let all your mowers resume their schedule.
        await asyncio.sleep(5)
        # await automower_api.pause_mowing(mower_id)
        # Uncomment the line above to let all your mowers pause.
    await asyncio.sleep(3000)
    # The close() will stop the websocket and the token refresh tasks
    await automower_api.close()
    await websession.close()


def callback(ws_data: dict[str, MowerAttributes]):
    """Process websocket callbacks and write them to the DataUpdateCoordinator."""
    for mower_id in ws_data:
        print(ws_data[mower_id])


async def _client_listen(
    automower_client: AutomowerSession,
    reconnect_time: int = 2,
) -> None:
    """Listen with the client."""
    try:
        await automower_client.auth.websocket_connect()
        await automower_client.start_listening()
    except Exception as err:  # pylint: disable=broad-except
        # We need to guard against unknown exceptions to not crash this task.
        print("Unexpected exception: %s", err)
    while True:
        await asyncio.sleep(reconnect_time)
        reconnect_time = min(reconnect_time * 2, MAX_WS_RECONNECT_TIME)
        await _client_listen(
            automower_client=automower_client,
            reconnect_time=reconnect_time,
        )


asyncio.run(main())
