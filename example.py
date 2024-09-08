"""An example file to use this library."""

import asyncio
import datetime
import logging
import time
from pprint import pprint
from typing import cast

import yaml
import zoneinfo
from aiohttp import ClientSession

from aioautomower.auth import AbstractAuth
from aioautomower.const import API_BASE_URL
from aioautomower.model import MowerAttributes
from aioautomower.session import AutomowerSession
from aioautomower.utils import (
    async_get_access_token,
    convert_timestamp_to_datetime_utc,
    naive_to_aware,
    structure_token,
)

_LOGGER = logging.getLogger(__name__)

# Fill out the secrets in secrets.yaml, you can find an example
# _secrets.yaml file, which has to be renamed after filling out the secrets.

with open("./secrets.yaml", encoding="UTF-8") as file:
    secrets = yaml.safe_load(file)

CLIENT_ID = secrets["CLIENT_ID"]
CLIENT_SECRET = secrets["CLIENT_SECRET"]
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
            pprint(token_structured)
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


async def main() -> None:
    """Establish connection to mower and print states for 5 minutes."""
    websession = ClientSession()
    tz_info = zoneinfo.ZoneInfo("Africa/Abidjan")
    automower_api = AutomowerSession(
        AsyncTokenAuth(websession), mower_tz=tz_info, poll=True
    )
    await asyncio.sleep(1)
    await automower_api.connect()
    api_task = asyncio.create_task(_client_listen(automower_api))
    ping_pong_task = asyncio.create_task(_send_messages(automower_api))
    # Add a callback, can be done at any point in time and
    # multiple callbacks can be added.
    automower_api.register_data_callback(callback)
    automower_api.register_pong_callback(pong_callback)
    # pylint: disable=unused-variable
    for _mower_id in automower_api.data:
        print(
            "next start:",
            naive_to_aware(
                automower_api.data[_mower_id].planner.next_start_datetime_naive,
                tz_info,
            ),
        )
        print(
            "from timestamp",
            convert_timestamp_to_datetime_utc(
                automower_api.data[_mower_id].planner.next_start, tz_info
            ),
        )
        # Uncomment one or more lines above to send this command to all the mowers
        # await automower_api.commands.set_datetime(_mower_id, datetime.datetime.now())
        # await automower_api.commands.park_until_next_schedule(_mower_id)
        # await automower_api.commands.park_until_further_notice(_mower_id)
        # await automower_api.commands.resume_schedule(_mower_id)
        # await automower_api.commands.pause_mowing(_mower_id)
        # await automower_api.commands.start_in_workarea(
        #     _mower_id, 0, datetime.timedelta(minutes=30)
        # )
    await asyncio.sleep(3000)
    # The close() will stop the websocket and the token refresh tasks
    await automower_api.close()
    api_task.cancel()
    ping_pong_task.cancel()
    await websession.close()


def callback(ws_data: dict[str, MowerAttributes]):
    """Process websocket callbacks and write them to the DataUpdateCoordinator."""
    for mower_id in ws_data:
        pprint(ws_data[mower_id])


def pong_callback(ws_data: datetime.datetime):
    """Process websocket callbacks and write them to the DataUpdateCoordinator."""
    print("Last websocket info: ", ws_data)


async def _client_listen(
    automower_client: AutomowerSession,
    reconnect_time: int = 2,
) -> None:
    """Listen with the client."""
    try:
        await automower_client.auth.websocket_connect()
        await automower_client.start_listening()
    except Exception as err:  # noqa: BLE001
        # We need to guard against unknown exceptions to not crash this task.
        print("Unexpected exception: %s", err)
    while True:
        await asyncio.sleep(reconnect_time)
        reconnect_time = min(reconnect_time * 2, MAX_WS_RECONNECT_TIME)
        await _client_listen(
            automower_client=automower_client,
            reconnect_time=reconnect_time,
        )


async def _send_messages(
    automower_client: AutomowerSession,
) -> None:
    """Listen with the client."""
    try:
        await automower_client.send_empty_message()
    except Exception as err:  # noqa: BLE001
        # We need to guard against unknown exceptions to not crash this task.
        print("Unexpected exception: %s", err)


asyncio.run(main())
