"""Tests for two mowers in aioautomower."""

import asyncio
import contextlib
import json
import zoneinfo
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientWebSocketResponse, WSMessage, WSMsgType

from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession

MOWER1_ID = "c7233734-b219-4287-a173-08e3643f89f0"
MOWER2_ID = "1234"


async def test_adding_mower(
    automower_client: AbstractAuth,
    two_mower_data: dict,
    mower_tz: zoneinfo.ZoneInfo,
) -> None:
    """Test adding another mower via websocket."""
    automower_api = AutomowerSession(automower_client, poll=True)
    await automower_api.connect()
    assert len(automower_api.data) == 1, "There should be only one mower"
    automower_api.auth.ws = AsyncMock(spec=ClientWebSocketResponse)
    automower_api.auth.ws.closed = False
    msg_data = {
        "id": "1234",
        "type": "battery-event-v2",
        "attributes": {"battery": {"batteryPercent": "99"}},
    }
    automower_api.auth.ws.receive = AsyncMock(
        side_effect=[
            WSMessage(WSMsgType.TEXT, json.dumps(msg_data).encode(), None),
            asyncio.CancelledError(),
        ]
    )
    automower_client.get_json = AsyncMock(return_value=two_mower_data)
    rest_task = asyncio.create_task(automower_api._rest_task())
    listening_task = asyncio.create_task(automower_api.start_listening())
    await asyncio.sleep(1)
    automower_api.auth.ws.closed = True
    await automower_api.close()
    assert len(automower_api.data) == 2, "Required mowers are not two."

    for t in (rest_task, listening_task):
        t.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.wait_for(t, timeout=1.0)


@pytest.mark.parametrize(
    ("mower_data"),
    [("two_mower_data")],
    indirect=True,
)
async def test_two_mower(automower_client: AbstractAuth, mower_data: dict) -> None:
    """Test converting a high feature mower."""
    automower_api = AutomowerSession(automower_client, poll=True)
    await automower_api.connect()
    assert automower_api.data[MOWER1_ID].battery.battery_percent == 100
    assert automower_api.data[MOWER2_ID].battery.battery_percent == 50
    # Test event of other mower doesn't overwrite the data
    battery_event = {
        "id": "1234",
        "type": "battery-event-v2",
        "attributes": {"battery": {"batteryPercent": "99"}},
    }
    msg2 = WSMessage(
        WSMsgType.TEXT,
        json.dumps(battery_event).encode(),
        None,
    )
    await automower_api._handle_text_message(msg2)
    assert automower_api.data[MOWER1_ID].battery.battery_percent == 100
    assert automower_api.data[MOWER2_ID].battery.battery_percent == 99
    msg_data = {
        "id": "c7233734-b219-4287-a173-08e3643f89f0",
        "type": "battery-event-v2",
        "attributes": {"battery": {"batteryPercent": "50"}},
    }
    msg1 = WSMessage(
        WSMsgType.TEXT,
        json.dumps(msg_data).encode(),
        None,
    )
    await automower_api._handle_text_message(msg1)
    assert automower_api.data[MOWER1_ID].battery.battery_percent == 50
    assert automower_api.data[MOWER2_ID].battery.battery_percent == 99

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()
