"""Test automower session."""

import zoneinfo
from datetime import datetime
from typing import TYPE_CHECKING

import pytest
import time_machine
from aiohttp import WSMessage, WSMsgType
from syrupy.assertion import SnapshotAssertion

from aioautomower.auth import AbstractAuth
from aioautomower.model import make_name_string
from aioautomower.session import AutomowerSession
from tests import load_fixture

from .conftest import TEST_TZ

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


@pytest.mark.benchmark
@time_machine.travel(
    datetime(2024, 5, 4, 8, tzinfo=TEST_TZ),
    tick=False,
)
async def test_timeline(
    automower_client: AbstractAuth,
    snapshot: SnapshotAssertion,
    mower_tz: zoneinfo.ZoneInfo,
) -> None:
    """Test automower timeline."""
    automower_api = AutomowerSession(automower_client, mower_tz, poll=True)
    await automower_api.connect()
    mower_timeline = automower_api.data[MOWER_ID].calendar.timeline
    if TYPE_CHECKING:
        assert mower_timeline is not None
    cursor = mower_timeline.overlapping(
        datetime(year=2024, month=5, day=4),  # noqa: DTZ001
        datetime(year=2024, month=9, day=8),  # noqa: DTZ001
    )
    overlapping = next(cursor, None)
    if TYPE_CHECKING:
        assert overlapping is not None
    assert overlapping.start == datetime(
        2024, 5, 4, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")
    )
    assert overlapping.end == datetime(
        2024, 5, 4, 8, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")
    )
    assert overlapping.schedule_no == 1
    assert overlapping.work_area_id == 0
    work_area_dict = automower_api.data[MOWER_ID].work_area_dict
    assert work_area_dict is not None
    assert (
        make_name_string(
            work_area_dict[overlapping.work_area_id],
            overlapping.schedule_no,
        )
        == "my_lawn schedule 1"
    )

    cursor = mower_timeline.active_after(datetime.now())  # noqa: DTZ005
    active_after = next(cursor, None)
    if TYPE_CHECKING:
        assert active_after is not None
    assert active_after.start == datetime(
        2024, 5, 6, 19, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")
    )
    assert active_after.end == datetime(
        2024, 5, 7, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")
    )
    assert active_after.schedule_no == 1
    assert active_after.work_area_id == 123456
    work_area_dict = automower_api.data[MOWER_ID].work_area_dict
    assert work_area_dict is not None
    assert (
        make_name_string(
            work_area_dict.get(active_after.work_area_id),
            active_after.schedule_no,
        )
        == "Front lawn schedule 1"
    )
    assert active_after.rrule_str == "FREQ=WEEKLY;BYDAY=MO,WE,FR"

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


@pytest.mark.parametrize(
    ("mower_data"),
    [("two_mower_data")],
    indirect=True,
)
@time_machine.travel("2024-05-04 8:00:00")
async def test_daily_schedule(
    automower_client: AbstractAuth,
    mower_data: dict,
    mower_tz: zoneinfo.ZoneInfo,
) -> None:
    """Test automower timeline with low feature mower."""
    automower_api = AutomowerSession(automower_client, mower_tz, poll=True)
    await automower_api.connect()
    # Test event of other mower doesn't overwrite the data
    msg = WSMessage(WSMsgType.TEXT, load_fixture("events/calendar_event.json"), None)
    await automower_api._handle_text_message(msg)

    mower_timeline = automower_api.data["1234"].calendar.timeline
    cursor = mower_timeline.active_after(datetime(year=2024, month=5, day=4))  # noqa: DTZ001
    active_after = next(cursor, None)
    if TYPE_CHECKING:
        assert active_after is not None
    assert active_after.start == datetime(
        2024, 5, 6, 2, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")
    )
    assert active_after.end == datetime(
        2024, 5, 6, 2, 49, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")
    )
    assert active_after.schedule_no == 1
    assert automower_api.data["1234"].work_area_dict is None
    work_area_dict = automower_api.data["1234"].work_area_dict
    assert work_area_dict is None
    assert (
        make_name_string(
            None,
            active_after.schedule_no,
        )
        == "Schedule 1"
    )
    assert active_after.rrule_str == "FREQ=WEEKLY;BYDAY=MO"

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


@pytest.mark.parametrize(
    ("mower_data"),
    [("mower_data_without_tasks")],
    indirect=True,
)
@time_machine.travel("2024-05-04 8:00:00")
async def test_empty_tasks(automower_client: AbstractAuth, mower_data: dict) -> None:
    """Test automower session patch commands."""
    automower_api = AutomowerSession(automower_client, poll=True)
    await automower_api.connect()
    mower_timeline = automower_api.data[MOWER_ID].calendar.timeline
    cursor = mower_timeline.active_after(datetime(year=2024, month=5, day=4))  # noqa: DTZ001
    active_after = next(cursor, None)
    assert active_after is None
