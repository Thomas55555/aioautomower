"""Tests for two mowers in aioautomower."""

import asyncio
import contextlib
import zoneinfo
from typing import TYPE_CHECKING

from aiohttp import WSMessage, WSMsgType

from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession
from aioautomower.utils import mower_list_to_dictionary_dataclass

MOWER1_ID = "c7233734-b219-4287-a173-08e3643f89f0"
MOWER2_ID = "1234"


async def test_adding_mower(
    automower_api: AutomowerSession,
    two_mower_data,
    mower_tz: zoneinfo.ZoneInfo,
) -> None:
    """Test adding another mower via rest-polling."""
    await automower_api.connect()
    assert len(automower_api.data) == 1

    # neue get_status-Mockfunktion für 2 Mäher
    async def get_status_two() -> dict:
        automower_api._data = two_mower_data
        automower_api.data = mower_list_to_dictionary_dataclass(
            two_mower_data, mower_tz
        )
        automower_api.current_mowers = set(automower_api.data.keys())
        return automower_api.data

    automower_api.get_status = get_status_two  # type: ignore[method-assign]

    rest_task = asyncio.create_task(automower_api._rest_task())
    await asyncio.sleep(0)

    assert len(automower_api.data) == 2

    rest_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await rest_task


async def test_two_mower(mock_automower_client_two_mowers: AbstractAuth) -> None:
    """Test converting a high feature mower."""
    automower_api = AutomowerSession(mock_automower_client_two_mowers, poll=True)
    await automower_api.connect()
    assert automower_api.data[MOWER1_ID].battery.battery_percent == 100
    assert automower_api.data[MOWER2_ID].battery.battery_percent == 50
    # Test event of other mower doesn't overwrite the data
    msg2 = WSMessage(
        WSMsgType.TEXT,
        b'{"id": "1234", "type": "battery-event-v2", "attributes": {"battery": {"batteryPercent": "99"}}}',
        None,
    )
    await automower_api._handle_text_message(msg2)  # noqa: SLF001
    assert automower_api.data[MOWER1_ID].battery.battery_percent == 100
    assert automower_api.data[MOWER2_ID].battery.battery_percent == 99
    msg1 = WSMessage(
        WSMsgType.TEXT,
        b'{"id": "c7233734-b219-4287-a173-08e3643f89f0", "type": "battery-event-v2", "attributes": {"battery": {"batteryPercent": "50"}}}',
        None,
    )
    await automower_api._handle_text_message(msg1)  # noqa: SLF001
    assert automower_api.data[MOWER1_ID].battery.battery_percent == 50
    assert automower_api.data[MOWER2_ID].battery.battery_percent == 99

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()
