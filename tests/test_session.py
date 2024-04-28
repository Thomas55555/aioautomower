"""Test automower session."""

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from aioautomower.auth import AbstractAuth
from aioautomower.exceptions import NoDataAvailableException
from aioautomower.model import HeadlightModes
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
    await automower_api.resume_schedule(MOWER_ID)
    assert mocked_method.call_count == 1
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={"data": {"type": "ResumeSchedule"}},
    )
    await automower_api.pause_mowing(MOWER_ID)
    assert mocked_method.call_count == 2
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={"data": {"type": "Pause"}},
    )
    await automower_api.park_until_next_schedule(MOWER_ID)
    assert mocked_method.call_count == 3
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={"data": {"type": "ParkUntilNextSchedule"}},
    )
    await automower_api.park_until_further_notice(MOWER_ID)
    assert mocked_method.call_count == 4
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={"data": {"type": "ParkUntilFurtherNotice"}},
    )
    await automower_api.park_for(MOWER_ID, 30)
    assert mocked_method.call_count == 5
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={
            "data": {
                "type": "Park",
                "attributes": {"duration": 30},
            }
        },
    )
    await automower_api.start_for(MOWER_ID, 30)
    assert mocked_method.call_count == 6
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/actions",
        json={
            "data": {
                "type": "Start",
                "attributes": {"duration": 30},
            }
        },
    )
    await automower_api.set_cutting_height(MOWER_ID, 9)
    assert mocked_method.call_count == 7
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/settings",
        json={"data": {"type": "settings", "attributes": {"cuttingHeight": 9}}},
    )
    await automower_api.set_headlight_mode(MOWER_ID, HeadlightModes.ALWAYS_OFF)
    assert mocked_method.call_count == 8
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
    await automower_api.set_calendar(MOWER_ID, task_list)
    assert mocked_method.call_count == 9
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/calendar",
        json={"data": {"type": "calendar", "attributes": {"tasks": task_list}}},
    )
    await automower_api.error_confirm(MOWER_ID)
    assert mocked_method.call_count == 10
    mocked_method.assert_called_with(f"mowers/{MOWER_ID}/errors/confirm", json={})
    mocked_method.reset_mock()


async def test_patch_commands(mock_automower_client: AbstractAuth):
    """Test automower session patch commands."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    mocked_method = AsyncMock()
    setattr(mock_automower_client, "patch_json", mocked_method)
    await automower_api.switch_stay_out_zone(MOWER_ID, "fake", True)
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
    await automower_api.set_cutting_height_workarea(MOWER_ID, 9, 0)
    assert mocked_method.call_count == 2
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/workAreas/0",
        json={
            "data": {"type": "workArea", "id": 0, "attributes": {"cuttingHeight": 9}}
        },
    )


async def test_update_data(mock_automower_client: AbstractAuth):
    """Test automower session patch commands."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    automower_api._update_data(  # pylint: disable=protected-access
        {
            "id": MOWER_ID,
            "type": "status-event",
            "attributes": {
                "battery": {"batteryPercent": 100},
                "mower": {
                    "mode": "MAIN_AREA",
                    "activity": "PARKED_IN_CS",
                    "state": "RESTRICTED",
                    "errorCode": 0,
                    "errorCodeTimestamp": 0,
                },
                "planner": {
                    "nextStartTimestamp": 1713369600000,
                    "override": {"action": "NOT_ACTIVE"},
                    "restrictedReason": "WEEK_SCHEDULE",
                },
                "metadata": {"connected": True, "statusTimestamp": 1713342672602},
            },
        }
    )
    calendar = automower_api.data[MOWER_ID].calendar.tasks
    automower_api._update_data(  # pylint: disable=protected-access
        {
            "id": MOWER_ID,
            "type": "settings-event",
            "attributes": {
                "calendar": {"tasks": []},
                "cuttingHeight": 1,
                "headlight": {"mode": "EVENING_AND_NIGHT"},
            },
        }
    )
    assert automower_api.data[MOWER_ID].calendar.tasks == calendar

    automower_api._data = None  # pylint: disable=protected-access
    with pytest.raises(NoDataAvailableException):
        automower_api._update_data(  # pylint: disable=protected-access
            {
                "id": MOWER_ID,
                "type": "settings-event",
                "attributes": {
                    "calendar": {"tasks": []},
                    "cuttingHeight": 1,
                    "headlight": {"mode": "EVENING_AND_NIGHT"},
                },
            }
        )
