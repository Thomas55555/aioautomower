"""Test automower session."""

from typing import TYPE_CHECKING

import zoneinfo

from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_timzeone_default(mock_automower_client: AbstractAuth):
    """Test setting system timezone automatically if not defined."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    await automower_api.close()

    assert automower_api.mower_tz == zoneinfo.ZoneInfo(key="Europe/Berlin")

    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_timzeone_overwrite(mock_automower_client: AbstractAuth):
    """Test overwriting timezone."""
    automower_api = AutomowerSession(
        mock_automower_client, mower_tz=zoneinfo.ZoneInfo("Europe/Stockholm"), poll=True
    )
    await automower_api.connect()
    await automower_api.close()

    assert automower_api.mower_tz == zoneinfo.ZoneInfo(key="Europe/Stockholm")
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()
