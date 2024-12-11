"""Test automower session."""

import zoneinfo
from datetime import UTC, datetime, time, timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
import tzlocal
from aiohttp import (
    WSMessage,
    WSMsgType,
)
from freezegun import freeze_time

from aioautomower.auth import AbstractAuth
from aioautomower.exceptions import (
    FeatureNotSupportedException,
    NoDataAvailableException,
    WorkAreasDifferentException,
)
from aioautomower.model import (
    Actions,
    Calendar,
    HeadlightModes,
    MowerModes,
    Positions,
    RestrictedReasons,
    Tasks,
)
from aioautomower.session import AutomowerSession

from . import load_fixture, load_fixture_json
from .const import MOWER_ID, MOWER_ID_LOW_FEATURE


async def test_connect_disconnect(mock_automower_client: AbstractAuth):
    """Test automower session post commands."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


@freeze_time("2024-05-04 8:00:00")
async def test_post_commands(mock_automower_client_two_mowers: AbstractAuth):
    """Test automower session post commands."""
    automower_api = AutomowerSession(mock_automower_client_two_mowers, poll=True)
    await automower_api.connect()
    mocked_method = AsyncMock()
    setattr(mock_automower_client_two_mowers, "post_json", mocked_method)
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

    # Test set_datetime with an aware datetime object in TZ UTC
    await automower_api.commands.set_datetime(
        MOWER_ID,
        datetime(2024, 5, 4, 8, 0, 0, 1234, tzinfo=UTC),
    )
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/settings",
        json={"data": {"type": "settings", "attributes": {"dateTime": 1714816800}}},
    )

    # Test set_datetime with an aware datetime object
    await automower_api.commands.set_datetime(
        MOWER_ID,
        datetime(2024, 5, 4, 8, 0, 0, 1234, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")),
    )
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/settings",
        json={"data": {"type": "settings", "attributes": {"dateTime": 1714809600}}},
    )

    # Test set_datetime with a naive datetime object
    await automower_api.commands.set_datetime(
        MOWER_ID,
        datetime(2024, 5, 4, 8),
    )
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/settings",
        json={"data": {"type": "settings", "attributes": {"dateTime": 1714809600}}},
    )

    # Test set_datetime without datetime object
    await automower_api.commands.set_datetime(
        MOWER_ID,
    )
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/settings",
        json={"data": {"type": "settings", "attributes": {"dateTime": 1714809600}}},
    )

    await automower_api.commands.set_headlight_mode(MOWER_ID, HeadlightModes.ALWAYS_OFF)
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/settings",
        json={
            "data": {
                "type": "settings",
                "attributes": {"headlight": {"mode": "ALWAYS_OFF"}},
            }
        },
    )

    # Test calendar with selfmade object
    calendar = [
        Calendar(
            time(8, 0),
            timedelta(hours=14),
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            123456,
        )
    ]
    tasks = Tasks(tasks=calendar)
    await automower_api.commands.set_calendar(MOWER_ID, tasks)
    tasks_test_dict = tasks.to_dict()
    for task in tasks_test_dict["tasks"]:
        assert task["workAreaId"] == 123456
        wa_id = task["workAreaId"]
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/workAreas/{wa_id}/calendar",
        json={"data": {"type": "calendar", "attributes": tasks_test_dict}},
    )

    # Test calendar with workareas
    tasks_dict: dict = load_fixture_json("tasks.json")
    tasks = Tasks.from_dict(tasks_dict)
    await automower_api.commands.set_calendar(MOWER_ID, tasks)
    for task in tasks_dict["tasks"]:
        assert task["workAreaId"] == 123456
        wa_id = task["workAreaId"]
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/workAreas/{wa_id}/calendar",
        json={"data": {"type": "calendar", "attributes": tasks_dict}},
    )

    # Test calendar with different work areas in one command.
    tasks_dict["tasks"][0]["workAreaId"] = 6789
    tasks = Tasks.from_dict(tasks_dict)
    with pytest.raises(
        WorkAreasDifferentException,
        match="Only identical work areas are allowed in one command.",
    ):
        await automower_api.commands.set_calendar(MOWER_ID, tasks)

    # Test calendar without workareas
    tasks_dict_without_work_areas: dict = load_fixture_json(
        "tasks_without_work_area.json"
    )
    tasks_without_work_areas = Tasks.from_dict(tasks_dict_without_work_areas)
    await automower_api.commands.set_calendar(
        MOWER_ID_LOW_FEATURE, tasks_without_work_areas
    )
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID_LOW_FEATURE}/calendar",
        json={
            "data": {"type": "calendar", "attributes": tasks_dict_without_work_areas}
        },
    )

    await automower_api.commands.error_confirm(MOWER_ID)
    mocked_method.assert_called_with(f"mowers/{MOWER_ID}/errors/confirm", json={})
    with pytest.raises(
        FeatureNotSupportedException,
        match="This mower does not support this command.",
    ):
        await automower_api.commands.set_headlight_mode(
            "1234", HeadlightModes.ALWAYS_OFF
        )

    with pytest.raises(
        FeatureNotSupportedException,
        match="This mower does not support this command.",
    ):
        await automower_api.commands.error_confirm("1234")

    with pytest.raises(
        FeatureNotSupportedException,
        match="This mower does not support this command.",
    ):
        await automower_api.commands.start_in_workarea("1234", 0, timedelta(minutes=10))

    mocked_method.reset_mock()
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_patch_commands(mock_automower_client_two_mowers: AbstractAuth):
    """Test automower session patch commands."""
    automower_api = AutomowerSession(mock_automower_client_two_mowers, poll=True)
    await automower_api.connect()
    mocked_method = AsyncMock()
    setattr(mock_automower_client_two_mowers, "patch_json", mocked_method)
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

    with pytest.raises(
        FeatureNotSupportedException,
        match="This mower does not support this command.",
    ):
        await automower_api.commands.switch_stay_out_zone("1234", "vallhala", True)

    await automower_api.commands.workarea_settings(MOWER_ID, 0, 9)
    assert mocked_method.call_count == 2
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/workAreas/0",
        json={
            "data": {
                "type": "workArea",
                "id": 0,
                "attributes": {
                    "cuttingHeight": 9,
                    "enable": False,
                },
            }
        },
    )

    await automower_api.commands.workarea_settings(MOWER_ID, 0, enabled=True)
    assert mocked_method.call_count == 3
    mocked_method.assert_called_with(
        f"mowers/{MOWER_ID}/workAreas/0",
        json={
            "data": {
                "type": "workArea",
                "id": 0,
                "attributes": {
                    "cuttingHeight": 10,
                    "enable": True,
                },
            }
        },
    )

    with pytest.raises(
        FeatureNotSupportedException,
        match="This mower does not support this command.",
    ):
        await automower_api.commands.workarea_settings("1234", 50, 0)

    mocked_method.reset_mock()
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_update_data(mock_automower_client: AbstractAuth):
    """Test automower session patch commands."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()

    # Test empty tasks. doesn't delete the tasks
    calendar = automower_api.data[MOWER_ID].calendar.tasks
    msg = WSMessage(WSMsgType.TEXT, load_fixture("settings_event.json"), None)
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].calendar.tasks == calendar
    assert (
        automower_api.data[MOWER_ID].settings.headlight.mode
        == HeadlightModes.EVENING_AND_NIGHT
    )

    # Test new tasks arrive
    msg = WSMessage(
        WSMsgType.TEXT, load_fixture("settings_event_with_tasks.json"), None
    )
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].calendar.tasks == [
        Calendar(
            start=time(hour=12),
            duration=timedelta(minutes=300),
            monday=True,
            tuesday=True,
            wednesday=True,
            thursday=True,
            friday=True,
            saturday=True,
            sunday=True,
            work_area_id=None,
        )
    ]

    # Test new positions arrive
    msg = WSMessage(WSMsgType.TEXT, load_fixture("positions_event.json"), None)
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].positions[0].latitude == 1  # type: ignore[index]
    assert automower_api.data[MOWER_ID].positions[0].longitude == 2  # type: ignore[index]

    msg = WSMessage(WSMsgType.TEXT, load_fixture("status_event.json"), None)
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].mower.work_area_id == 123456

    # Test NoDataAvailableException is risen, if there is no data
    automower_api._data = None  # noqa: SLF001
    with pytest.raises(NoDataAvailableException):
        automower_api._handle_text_message(msg)  # noqa: SLF001

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_battery_event(mock_automower_client: AbstractAuth):
    """Test automower websocket V2 battery update."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()

    msg = WSMessage(WSMsgType.TEXT, load_fixture("events/battery_event.json"), None)
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].battery.battery_percent == 77

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_calendar_event_work_area(mock_automower_client: AbstractAuth):
    """Test automower websocket V2 calendar update with work area."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()

    msg = WSMessage(
        WSMsgType.TEXT, load_fixture("events/calendar_event_work_area.json"), None
    )
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].calendar.tasks == [
        Calendar(
            start=time(hour=12),
            duration=timedelta(minutes=300),
            monday=True,
            tuesday=True,
            wednesday=True,
            thursday=True,
            friday=True,
            saturday=True,
            sunday=True,
            work_area_id=78543,
        )
    ]

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_cutting_height_event(mock_automower_client: AbstractAuth):
    """Test automower websocket V2 calendar update with work area."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()

    msg = WSMessage(
        WSMsgType.TEXT, load_fixture("events/cutting_height_event.json"), None
    )
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].settings.cutting_height == 5

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_headlights_event(mock_automower_client: AbstractAuth):
    """Test automower websocket V2 headlight update."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    assert (
        automower_api.data[MOWER_ID].settings.headlight.mode
        == HeadlightModes.EVENING_ONLY
    )
    msg = WSMessage(WSMsgType.TEXT, load_fixture("events/headlights_event.json"), None)
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert (
        automower_api.data[MOWER_ID].settings.headlight.mode == HeadlightModes.ALWAYS_ON
    )
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_single_mower_event(mock_automower_client: AbstractAuth):
    """Test automower websocket V2 mower event update with just one change."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    msg = WSMessage(
        WSMsgType.TEXT,
        b'{"id": "c7233734-b219-4287-a173-08e3643f89f0", "type": "mower-event-v2", "attributes": {"mower": {"mode": "DEMO"}}}',
        None,
    )
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].mower.mode == MowerModes.DEMO

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_sinlge_planner_event(mock_automower_client: AbstractAuth):
    """Test automower websocket V2 planner event update with just one change."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    assert automower_api.data[MOWER_ID].planner.next_start_datetime == datetime(
        2023, 6, 5, 19, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")
    )
    assert automower_api.data[MOWER_ID].planner.override.action == Actions.NOT_ACTIVE
    assert (
        automower_api.data[MOWER_ID].planner.restricted_reason
        == RestrictedReasons.WEEK_SCHEDULE
    )
    msg = WSMessage(
        WSMsgType.TEXT,
        b'{"id": "c7233734-b219-4287-a173-08e3643f89f0", "type": "planner-event-v2", "attributes": {"planner": {"restrictedReason": "ALL_WORK_AREAS_COMPLETED"}}}',
        None,
    )
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].planner.next_start_datetime == datetime(
        2023, 6, 5, 19, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")
    )
    assert automower_api.data[MOWER_ID].planner.override.action == Actions.NOT_ACTIVE
    assert (
        automower_api.data[MOWER_ID].planner.restricted_reason
        == RestrictedReasons.ALL_WORK_AREAS_COMPLETED
    )
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_full_planner_event(mock_automower_client: AbstractAuth):
    """Test automower websocket V2 planner event full update."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    assert automower_api.data[MOWER_ID].planner.next_start_datetime == datetime(
        2023, 6, 5, 19, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")
    )
    assert automower_api.data[MOWER_ID].planner.override.action == Actions.NOT_ACTIVE
    assert (
        automower_api.data[MOWER_ID].planner.restricted_reason
        == RestrictedReasons.WEEK_SCHEDULE
    )
    msg = WSMessage(WSMsgType.TEXT, load_fixture("events/planner_event.json"), None)
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].planner.next_start_datetime is None
    assert automower_api.data[MOWER_ID].planner.override.action == Actions.FORCE_MOW
    assert (
        automower_api.data[MOWER_ID].planner.restricted_reason
        == RestrictedReasons.PARK_OVERRIDE
    )

    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_positions_event(mock_automower_client: AbstractAuth):
    """Test automower websocket V2 positions update."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    assert automower_api.data[MOWER_ID].positions[0] == Positions(
        35.5402913, -82.5527055
    )
    msg = WSMessage(WSMsgType.TEXT, load_fixture("events/positions_event.json"), None)
    automower_api._handle_text_message(msg)  # noqa: SLF001
    assert automower_api.data[MOWER_ID].positions[0] == Positions(57.70074, 14.4787133)
    await automower_api.close()
    if TYPE_CHECKING:
        assert automower_api.rest_task is not None
    assert automower_api.rest_task.cancelled()


async def test_empty_tasks(mock_automower_client_without_tasks: AbstractAuth):
    """Test automower empty task."""
    automower_api = AutomowerSession(mock_automower_client_without_tasks, poll=True)
    await automower_api.connect()
    assert automower_api.data[MOWER_ID].calendar.tasks == []


async def test_timezone_default(mock_automower_client: AbstractAuth):
    """Test setting system timezone automatically if not defined."""
    automower_api = AutomowerSession(mock_automower_client, poll=True)
    await automower_api.connect()
    await automower_api.close()
    assert automower_api.mower_tz == tzlocal.get_localzone()

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
