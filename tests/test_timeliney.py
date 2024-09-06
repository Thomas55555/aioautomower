"""Test automower session."""

from datetime import datetime
from typing import TYPE_CHECKING

from freezegun import freeze_time
from freezegun.api import FakeDatetime
from syrupy.assertion import SnapshotAssertion

from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


@freeze_time("2024-05-04 8:00:00")
async def test_timeline(
    mock_automower_client: AbstractAuth, snapshot: SnapshotAssertion
):
    """Test automower timeline."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()

    mower_timeline = automower_api.data[MOWER_ID].calendar.timeline
    if TYPE_CHECKING:
        assert mower_timeline is not None
    cursor = mower_timeline.overlapping(
        datetime(year=2024, month=5, day=4),
        datetime(year=2024, month=9, day=8),
    )
    overlapping = next(cursor, None)
    if TYPE_CHECKING:
        assert overlapping is not None
    assert overlapping.start == FakeDatetime(2024, 5, 4, 0, 0)
    assert overlapping.end == FakeDatetime(2024, 5, 4, 8, 0)
    assert overlapping.schedule_name == "my_lawn schedule 1"

    cursor = mower_timeline.active_after(datetime.now())
    active_after = next(cursor, None)
    if TYPE_CHECKING:
        assert active_after is not None
    assert active_after.start == FakeDatetime(2024, 5, 6, 19, 0)
    assert active_after.end == FakeDatetime(2024, 5, 7, 0, 0)
    assert active_after.schedule_name == "Front lawn schedule 1"

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()
