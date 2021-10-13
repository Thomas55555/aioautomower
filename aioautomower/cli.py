#!/usr/bin/env python3
import asyncio
import logging
import signal

import aioautomower

_LOGGER = logging.getLogger(__name__)


async def run_tester(username: str, password: str, api_key: str):

    sess = aioautomower.AutomowerSession(api_key, ws_heartbeat_interval=60)
    token = await sess.login(username, password)

    sess.register_data_callback(
        lambda x: logging.info("data callback;%s" % x), schedule_immediately=False
    )
    sess.register_token_callback(
        lambda x: logging.info("token callback;%s" % x), schedule_immediately=True
    )

    await sess.connect()

    def sigusr1():
        asyncio.ensure_future(sess.invalidate_token())

    def sigusr2():
        asyncio.ensure_future(sess.get_status())

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGUSR1, sigusr1)
    loop.add_signal_handler(signal.SIGUSR2, sigusr2)

    while True:
        await asyncio.sleep(0.1)


def main():
    """Tester for the Husqvarna Automower API

    The tester will login using username and password and connect to a
    websocket listening for mower updates.

    The tester listens to two signals on which it performs the following
    requests:
    SIGUSR1: Invalidate token
    SIGUSR2: Get status"""
    import argparse

    parser = argparse.ArgumentParser(
        description=main.__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-u", "--username", required=True, help="Husqvarna app username"
    )
    parser.add_argument(
        "-p", "--password", required=True, help="Husqvarna app password"
    )
    parser.add_argument("-k", "--api-key", required=True, help="Husqvarna API key")

    args = parser.parse_args()

    logging.basicConfig(level="DEBUG", format="%(asctime)s;%(levelname)s;%(message)s")
    asyncio.run(run_tester(args.username, args.password, args.api_key))
