"""The CLI for aioautomower."""
import argparse
import asyncio
import logging
import signal
import time

from aiohttp import ClientSession

import aioautomower.utils
from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


async def run_tester(client_id: str, client_secret: str):
    """Run the tester."""
    automower_api = AutomowerSession(
        AsyncConfigEntryAuth(ClientSession(), client_id, client_secret), poll=True
    )
    automower_api.register_data_callback(
        lambda x: logging.info("data callback;%s", x),
    )

    await automower_api.connect()

    def sigusr1():
        asyncio.ensure_future(automower_api.invalidate_token())

    def sigusr2():
        asyncio.ensure_future(automower_api.get_status())

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGUSR1, sigusr1)
    loop.add_signal_handler(signal.SIGUSR2, sigusr2)

    while True:
        await asyncio.sleep(0.1)


def main():
    """Tester for the Husqvarna Automower API.

    The tester will login using client_id and client_secret and connect to a
    websocket listening for mower updates.

    The tester listens to two signals on which it performs the following
    requests:
    SIGUSR1: Invalidate token
    SIGUSR2: Get status
    """
    parser = argparse.ArgumentParser(
        description=main.__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-s", "--client_id", required=True, help="Husqvarna Application key"
    )
    parser.add_argument(
        "-k", "--client_secret", required=True, help="Husqvarna Application secret"
    )

    args = parser.parse_args()

    logging.basicConfig(level="DEBUG", format="%(asctime)s;%(levelname)s;%(message)s")
    asyncio.run(run_tester(args.client_id, args.client_secret))


class AsyncConfigEntryAuth(AbstractAuth):
    """Provide Husqvarna Automower authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        websession: ClientSession,
        client_id: str,
        client_secret: str,
    ) -> None:
        """Initialize Husqvarna Automower auth."""
        super().__init__(websession, API_BASE_URL)
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.websession = websession

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        if not self.token:
            self.token = await aioautomower.utils.async_get_access_token(
                self.client_id, self.client_secret, self.websession
            )
            token_structured = await aioautomower.utils.async_structure_token(
                self.token["access_token"]
            )
            _LOGGER.debug("token_structured.exp: %s", token_structured.exp)
            _LOGGER.debug(time.time())
        if token_structured.exp < time.time():
            self.token = await aioautomower.utils.async_get_access_token(
                self.client_id, self.client_secret, self.websession
            )
        return self.token["access_token"]
