"""Test automower session."""

import json
from dataclasses import fields
from unittest.mock import AsyncMock

from syrupy.assertion import SnapshotAssertion

from aioautomower.model import HeadlightModes
from aioautomower.session import AutomowerSession
from tests import load_fixture

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_connect(snapshot: SnapshotAssertion):
    """Test automower session."""
    auth_mock = AsyncMock()
    automower_api = AutomowerSession(auth_mock)
    await automower_api.connect()
    auth_mock.get_json.return_value = json.loads(load_fixture("raw_data.json"))
    data = await automower_api.get_status()
    for field in fields(data[MOWER_ID]):
        field_name = field.name
        field_value = getattr(data[MOWER_ID], field_name)
        assert field_value == snapshot(name=f"{field_name}")
    await automower_api.resume_schedule(MOWER_ID)
    await automower_api.pause_mowing(MOWER_ID)
    await automower_api.park_until_next_schedule(MOWER_ID)
    await automower_api.park_until_further_notice(MOWER_ID)
    await automower_api.park_for(MOWER_ID, 30)
    await automower_api.start_for(MOWER_ID, 30)
    await automower_api.set_cutting_height(MOWER_ID, 9)
    await automower_api.set_cutting_height_workarea(MOWER_ID, 9, 0)
    await automower_api.set_headlight_mode(MOWER_ID, HeadlightModes.ALWAYS_OFF)
    task_list = json.loads(load_fixture("task_list.json"))
    await automower_api.set_calendar(MOWER_ID, task_list)
    await automower_api.switch_stay_out_zone(MOWER_ID, "fake", True)
