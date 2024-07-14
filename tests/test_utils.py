"""Test aioautomower utils."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import zoneinfo

from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession
from aioautomower.utils import naive_to_aware

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_timezone(mock_automower_client: AbstractAuth):
    """Test automower session patch commands."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    mower_tz = zoneinfo.ZoneInfo("Europe/Berlin")
    next_start_aware = naive_to_aware(
        automower_api.data[MOWER_ID].planner.next_start_datetime_naive, mower_tz
    )
    assert next_start_aware == datetime(2023, 6, 5, 19, 0, tzinfo=UTC)
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()
