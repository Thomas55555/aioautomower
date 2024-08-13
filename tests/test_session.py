"""Test automower session."""

import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from aiohttp import WSMessage, WSMsgType

from aioautomower.auth import AbstractAuth
from aioautomower.exceptions import NoDataAvailableException
from aioautomower.model import Calendar, HeadlightModes
from aioautomower.session import AutomowerSession
from tests import load_fixture

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_connect_disconnect(mock_automower_client: AbstractAuth):
    """Test automower session post commands."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_post_commands(mock_automower_client: AbstractAuth):
    """Test automower session post commands."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    mocked_method = AsyncMock()
    setattr(mock_automower_client, "post_json", mocked_method)
    await automower_api.commands.resume_schedule(MOWER_ID)
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={"data": {"type": "ResumeSchedule"}},
    )
    await automower_api.commands.pause_mowing(MOWER_ID)
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={"data": {"type": "Pause"}},
    )
    await automower_api.commands.park_until_next_schedule(MOWER_ID)
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={"data": {"type": "ParkUntilNextSchedule"}},
    )
    await automower_api.commands.park_until_further_notice(MOWER_ID)
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={"data": {"type": "ParkUntilFurtherNotice"}},
    )
    await automower_api.commands.park_for(MOWER_ID, timedelta(minutes=30, seconds=59))
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={
            "data": {
                "type": "Park",
                "attributes": {"duration": 30},
            }
        },
    )
    await automower_api.commands.start_in_workarea(MOWER_ID, 0, timedelta(minutes=30))
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={
            "data": {
                "type": "StartInWorkArea",
                "attributes": {"duration": 30, "workAreaId": 0},
            }
        },
    )
    await automower_api.commands.start_for(MOWER_ID, timedelta(hours=1, minutes=30))
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={
            "data": {
                "type": "Start",
                "attributes": {"duration": 90},
            }
        },
    )

    await automower_api.commands.set_cutting_height(MOWER_ID, 9)
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/settings",
        json={"data": {"type": "settings", "attributes": {"cuttingHeight": 9}}},
    )

    await automower_api.commands.set_datetime(
        MOWER_ID, datetime(2024, 8, 13, 12, 0, 0, 1234)
    )
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/settings",
        json={"data": {"type": "settings", "attributes": {"dateTime": 1723543200}}},
    )

    await automower_api.commands.set_headlight_mode(MOWER_ID, HeadlightModes.ALWAYS_OFF)
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/settings",
        json={
            "data": {
                "type": "settings",
                "attributes": {"headlight": {"mode": HeadlightModes.ALWAYS_OFF}},
            }
        },
    )
    task_list = json.loads(load_fixture("task_list.json"))
    await automower_api.commands.set_calendar(MOWER_ID, task_list)
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/calendar",
        json={"data": {"type": "calendar", "attributes": {"tasks": task_list}}},
    )
    await automower_api.commands.error_confirm(MOWER_ID)
    mocked_method.assert_called_with(f"mowers/{MOWER_ID}/errors/confirm", json={})
    mocked_method.reset_mock()
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_patch_commands(mock_automower_client: AbstractAuth):
    """Test automower session patch commands."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    mocked_method = AsyncMock()
    setattr(mock_automower_client, "patch_json", mocked_method)
    await automower_api.commands.switch_stay_out_zone(MOWER_ID, "fake", True)
    assert mocked_method.call_count == 1
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/stayOutZones/fake",
        json={
            "data": {
                "type": "stayOutZone",
                "id": "fake",
                "attributes": {"enable": True},
            }
        },
    )
    await automower_api.commands.set_cutting_height_workarea(MOWER_ID, 9, 0)
    assert mocked_method.call_count == 2
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/workAreas/0",
        json={
            "data": {"type": "workArea", "id": 0, "attributes": {"cuttingHeight": 9}}
        },
    )
    await automower_api.close()


async def test_update_data(mock_automower_client: AbstractAuth):
    """Test automower session patch commands."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()

    # Test empty tasks. doesn't delete the tasks
    calendar = automower_api.data[MOWER_ID].calendar.tasks
    msg = WSMessage(WSMsgType.TEXT, load_fixture("settings_event.json"), None)
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].calendar.tasks == calendar
    assert automower_api.data[MOWER_ID].settings.headlight.mode == "EVENING_AND_NIGHT"

    # Test new tasks arrive
    msg = WSMessage(
        WSMsgType.TEXT, load_fixture("settings_event_with_tasks.json"), None
    )
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].calendar.tasks == [
        Calendar(
            start=720,
            duration=300,
            monday=False,
            tuesday=False,
            wednesday=True,
            thursday=False,
            friday=False,
            saturday=False,
            sunday=False,
            work_area_id=None,
            work_area_name=None,
        )
    ]

    # Test new positions arrive
    msg = WSMessage(WSMsgType.TEXT, load_fixture("positions_event.json"), None)
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].positions[0].latitude == 1  # type: ignore[index]
    assert automower_api.data[MOWER_ID].positions[0].longitude == 2  # type: ignore[index]

    # Test NoDataAvailableException is risen, if there is no data
    automower_api._data = None  # noqa: SLF001
    with pytest.raises(NoDataAvailableException):
        automower_api._handle_text_message(msg)  # noqa: SLF001

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()
