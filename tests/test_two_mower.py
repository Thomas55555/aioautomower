"""Tests for two mowers in aioautomower."""

from typing import TYPE_CHECKING

from aiohttp import WSMessage, WSMsgType

from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession
from tests import load_fixture

MOWER1_ID = "c7233734-b219-4287-a173-08e3643f89f0"
MOWER2_ID = "1234"


async def test_two_mower(mock_automower_client_two_mowers: AbstractAuth) -> None:
    """Test converting a high feature mower."""
    automower_api = AutomowerSession(mock_automower_client_two_mowers, poll=True)
    await automower_api.connect()
    assert automower_api.data[MOWER1_ID].battery.battery_percent == 100
    assert automower_api.data[MOWER2_ID].battery.battery_percent == 50
    # Test event of other mower doesn't overwrite the data
    msg2 = WSMessage(WSMsgType.TEXT, load_fixture("status_event_mower2.json"), None)
    automower_api._handle_text_message(msg2)  # pylint: disable=protected-access
    assert automower_api.data[MOWER1_ID].battery.battery_percent == 100
    assert automower_api.data[MOWER2_ID].battery.battery_percent == 99
    msg1 = WSMessage(WSMsgType.TEXT, load_fixture("status_event_battery_50.json"), None)
    automower_api._handle_text_message(msg1)  # pylint: disable=protected-access
    assert automower_api.data[MOWER1_ID].battery.battery_percent == 50
    assert automower_api.data[MOWER2_ID].battery.battery_percent == 99

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()
