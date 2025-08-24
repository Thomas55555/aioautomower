"""Tests for asynchronous Python client for aioautomower."""

import zoneinfo
from dataclasses import fields
from typing import TYPE_CHECKING, cast

from syrupy.assertion import SnapshotAssertion

from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession

if TYPE_CHECKING:
    from aioautomower.model import WorkArea

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_high_feature_mower(
    automower_client: AbstractAuth, mower_tz: zoneinfo.ZoneInfo
) -> None:
    """Test converting a high feature mower."""
    automower_api = AutomowerSession(automower_client, mower_tz=mower_tz, poll=True)
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
    workarea = cast("dict[int, WorkArea]", mowers[MOWER_ID].work_areas)
    assert workarea[123456] is not None
    assert workarea[123456].name == "Front lawn"
    assert workarea[123456].cutting_height == 50
    assert mowers[MOWER_ID].statistics.cutting_blade_usage_time == 1234
    assert len(mowers[MOWER_ID].positions) != 0  # type: ignore[arg-type]
    await automower_api.close()
    assert automower_api._rest_task is not None


async def test_mower_snapshot(
    automower_client: AbstractAuth,
    snapshot: SnapshotAssertion,
    mower_tz: zoneinfo.ZoneInfo,
) -> None:
    """Testing a snapshot of a high feature mower."""
    automower_api = AutomowerSession(automower_client, mower_tz=mower_tz, poll=True)
    await automower_api.connect()
    mower_data = automower_api.data[MOWER_ID]
    for field in fields(mower_data):
        field_name = field.name
        field_value = getattr(mower_data, field_name)
        assert field_value == snapshot(name=f"status.{field_name}")

    message_data = automower_api.messages[MOWER_ID]
    for i, message in enumerate(message_data.attributes.messages):
        assert message == snapshot(name=f"message.{i}")

    await automower_api.close()
    assert automower_api._rest_task is not None
