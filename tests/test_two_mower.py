"""Tests for two mowers in aioautomower."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch
from aiohttp import WSMessage, WSMsgType
import zoneinfo
from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession
from aioautomower.utils import mower_list_to_dictionary_dataclass

MOWER1_ID = "c7233734-b219-4287-a173-08e3643f89f0"
MOWER2_ID = "1234"


async def test_adding_mower(
    mock_automower_client: AbstractAuth,
    two_mower_data,
    mower_tz: zoneinfo.ZoneInfo,
) -> None:
    """Test converting a high feature mower."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    print(automower_api.data)
    assert automower_api.data[MOWER1_ID].battery.battery_percent == 100
    # Test event of other mower doesn't overwrite the data
    msg2 = WSMessage(
        WSMsgType.TEXT,
        b'{"id": "1234", "type": "battery-event-v2", "attributes": {"battery": {"batteryPercent": "99"}}}',
        None,
    )
    automower_api.data = automower_api.get_status = AsyncMock(
        return_value=two_mower_data
    )
    await automower_api._handle_text_message(msg2)  # noqa: SLF001
    automower_api.get_status.assert_awaited_once()
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


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
