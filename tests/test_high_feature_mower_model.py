"""Tests for asynchronous Python client for aioautomower."""

import zoneinfo
from dataclasses import fields
from typing import TYPE_CHECKING, cast

import time_machine
from syrupy.assertion import SnapshotAssertion

from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession

if TYPE_CHECKING:
    from aioautomower.model import WorkArea

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_high_feature_mower(mock_automower_client: AutomowerSession) -> None:
    """Test converting a high feature mower."""
    await mock_automower_client.connect()
    mowers = mock_automower_client.data
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
    workarea = cast("dict[int, WorkArea]", mowers[MOWER_ID].work_areas)
    assert workarea[123456] is not None
    assert workarea[123456].name == "Front lawn"
    assert workarea[123456].cutting_height == 50
    assert mowers[MOWER_ID].statistics.cutting_blade_usage_time == 1234
    assert len(mowers[MOWER_ID].positions) != 0  # type: ignore[arg-type]


@time_machine.travel("2024-05-04 8:00:00")
async def test_mower_snapshot(
    mock_automower_client: AutomowerSession, snapshot: SnapshotAssertion
) -> None:
    """Testing a snapshot of a high feature mower."""
    # pylint: disable=duplicate-code
    await mock_automower_client.connect()
    mowers = mock_automower_client.data
    mock_automower_client.data[MOWER_ID]
    for field in fields(mock_automower_client.data[MOWER_ID]):
        field_name = field.name
        field_value = getattr(mock_automower_client.data[MOWER_ID], field_name)
        assert field_value == snapshot(name=f"{field_name}")
