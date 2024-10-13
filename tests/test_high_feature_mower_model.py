"""Tests for asynchronous Python client for aioautomower."""

from dataclasses import fields
from typing import cast

import zoneinfo
from freezegun import freeze_time
from syrupy.assertion import SnapshotAssertion

from aioautomower.auth import AbstractAuth
from aioautomower.model import WorkArea
from aioautomower.session import AutomowerSession

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_high_feature_mower(mock_automower_client: AbstractAuth) -> None:
    """Test converting a high feature mower."""
    automower_api = AutomowerSession(
        mock_automower_client, mower_tz=zoneinfo.ZoneInfo("America/Regina"), poll=True
    )
    await automower_api.connect()
    mowers = automower_api.data
    assert mowers[MOWER_ID].battery.battery_percent == 100
    assert mowers[MOWER_ID].stay_out_zones.dirty is False  # type: ignore[union-attr]
    assert mowers[MOWER_ID].stay_out_zones.zones is not None  # type: ignore[union-attr]
    assert (
        mowers[MOWER_ID]  # type: ignore[union-attr]
        .stay_out_zones.zones["81C6EEA2-D139-4FEA-B134-F22A6B3EA403"]
        .name
        == "Springflowers"
    )
    assert (
        mowers[MOWER_ID]  # type: ignore[union-attr]
        .stay_out_zones.zones["81C6EEA2-D139-4FEA-B134-F22A6B3EA403"]
        .enabled
        is True
    )
    assert mowers[MOWER_ID].work_areas is not None
    workarea = cast(dict[int, WorkArea], mowers[MOWER_ID].work_areas)
    assert workarea[123456] is not None
    assert workarea[123456].name == "Front lawn"
    assert workarea[123456].cutting_height == 50
    assert mowers[MOWER_ID].statistics.cutting_blade_usage_time == 1234
    assert len(mowers[MOWER_ID].positions) != 0  # type: ignore[arg-type]

    # Test empty task list
    # mower_fixture = load_fixture("high_feature_mower.json")
    # mower_python = json.loads(mower_fixture)
    # mowers = mower_list_to_dictionary_dataclass(mower_python)
    # mower_python["data"][0]["attributes"]["calendar"]["tasks"] = []
    # mowers = mower_list_to_dictionary_dataclass(mower_python)
    # assert mowers[MOWER_ID].calendar.tasks == []
    # assert mowers[MOWER_ID].calendar.events == []


@freeze_time("2024-05-04 8:00:00")
async def test_mower_snapshot(
    mock_automower_client: AbstractAuth, snapshot: SnapshotAssertion
):
    """Testing a snapshot of a high feature mower."""
    # pylint: disable=duplicate-code
    automower_api = AutomowerSession(
        mock_automower_client, mower_tz=zoneinfo.ZoneInfo("America/Regina"), poll=True
    )
    await automower_api.connect()
    automower_api.data[MOWER_ID]
    for field in fields(automower_api.data[MOWER_ID]):
        field_name = field.name
        field_value = getattr(automower_api.data[MOWER_ID], field_name)
        assert field_value == snapshot(name=f"{field_name}")
