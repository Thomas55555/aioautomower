"""Test aioautomower utils."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
import zoneinfo

from aioautomower.auth import AbstractAuth
from aioautomower.model import naive_to_aware
from aioautomower.session import AutomowerSession
from aioautomower.utils import convert_timestamp_to_datetime_utc

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


@pytest.mark.parametrize(
    ("tz_str", "expected"),
    [
        ("Europe/Berlin", datetime(2023, 6, 5, 17, 0, tzinfo=UTC)),
        ("Africa/Abidjan", datetime(2023, 6, 5, 19, 0, tzinfo=UTC)),
        ("America/Regina", datetime(2023, 6, 6, 1, 0, tzinfo=UTC)),
    ],
)
async def test_naive_to_aware(
    mock_automower_client: AbstractAuth, tz_str: str, expected: datetime
):
    """Test naive_to_aware function."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    mower_tz = zoneinfo.ZoneInfo(tz_str)
    # automower_api.data[MOWER_ID].planner.next_start_datetime_naive is 19:00 in local time
    next_start_aware = naive_to_aware(
        automower_api.data[MOWER_ID].planner.next_start_datetime_naive, mower_tz
    )
    assert next_start_aware == expected
    assert next_start_aware.astimezone(mower_tz) == datetime(
        2023, 6, 5, 19, 0, tzinfo=mower_tz
    )
    automower_api.data[MOWER_ID].planner.next_start_datetime_naive = None
    next_start_aware = naive_to_aware(
        automower_api.data[MOWER_ID].planner.next_start_datetime_naive, mower_tz
    )
    assert next_start_aware is None
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


@pytest.mark.parametrize(
    ("tz_str", "expected"),
    [
        ("Europe/Berlin", datetime(2023, 6, 5, 17, 0, tzinfo=UTC)),
        ("Africa/Abidjan", datetime(2023, 6, 5, 19, 0, tzinfo=UTC)),
        ("America/Regina", datetime(2023, 6, 6, 1, 0, tzinfo=UTC)),
    ],
)
async def test_convert_timestamp_to_datetime_utc2(
    mock_automower_client: AbstractAuth, tz_str: str, expected: datetime
):
    """Test convert_timestamp_to_datetime_utc function."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    mower_tz = zoneinfo.ZoneInfo(tz_str)
    # automower_api.data[MOWER_ID].planner.next_start_datetime_naive is 19:00 in local time
    next_start_aware = convert_timestamp_to_datetime_utc(
        automower_api.data[MOWER_ID].planner.next_start, mower_tz
    )
    assert next_start_aware == expected
    assert next_start_aware.astimezone(mower_tz) == datetime(
        2023, 6, 5, 19, 0, tzinfo=mower_tz
    )
    automower_api.data[MOWER_ID].planner.next_start = 0
    next_start_aware = convert_timestamp_to_datetime_utc(
        automower_api.data[MOWER_ID].planner.next_start, mower_tz
    )
    assert next_start_aware is None
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()
