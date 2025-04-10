"""Tests for two mowers in aioautomower."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from aiohttp import WSMessage, WSMsgType
from aiohttp import ClientWebSocketResponse
import zoneinfo
from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession
import asyncio
import contextlib

MOWER1_ID = "c7233734-b219-4287-a173-08e3643f89f0"
MOWER2_ID = "1234"


async def test_adding_mower(
    mock_automower_client: AbstractAuth,
    two_mower_data,
    mower_tz: zoneinfo.ZoneInfo,
) -> None:
    """Test adding another mower via websocket."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    assert len(automower_api.data) == 1, "There should be only one mower"
    automower_api.auth.ws = AsyncMock(spec=ClientWebSocketResponse)
    automower_api.auth.ws.closed = False
    automower_api.auth.ws.receive = AsyncMock(
        side_effect=[
            WSMessage(
                WSMsgType.TEXT,
                b'{"id": "1234", "type": "battery-event-v2", "attributes": {"battery": {"batteryPercent": "99"}}}',
                None,
            ),
            asyncio.CancelledError(),
        ]
    )
    mock_automower_client.get_json.return_value = two_mower_data
    rest_task = asyncio.create_task(automower_api._rest_task())
    listening_task = asyncio.create_task(automower_api.start_listening())
    await asyncio.sleep(0)
    automower_api.auth.ws.closed = True
    await automower_api.close()
    assert len(automower_api.data) == 2, "Required mowers are not two."

    for t in (rest_task, listening_task):
        t.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.wait_for(t, timeout=1.0)


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
