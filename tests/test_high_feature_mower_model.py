"""Tests for asynchronous Python client for aioautomower."""

import json
from dataclasses import fields
from typing import cast
from syrupy.assertion import SnapshotAssertion
from freezegun import freeze_time
from aioautomower.utils import mower_list_to_dictionary_dataclass
from aioautomower.model import WorkArea
from tests import load_fixture


MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_high_feature_mower() -> None:
    """Test converting a high feature mower."""
    mower_fixture = load_fixture("high_feature_mower.json")
    mower_python = json.loads(mower_fixture)
    mowers = mower_list_to_dictionary_dataclass(mower_python)
    assert mowers[MOWER_ID].battery.battery_percent == 100
    assert mowers[MOWER_ID].stay_out_zones.dirty is False  # type: ignore
    assert mowers[MOWER_ID].stay_out_zones.zones is not None  # type: ignore
    assert (
        mowers[MOWER_ID]  # type: ignore
        .stay_out_zones.zones["81C6EEA2-D139-4FEA-B134-F22A6B3EA403"]
        .name
        == "Springflowers"
    )
    assert (
        mowers[MOWER_ID]  # type: ignore
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
    assert len(mowers[MOWER_ID].positions) != 0  # type: ignore


@freeze_time(tz_offset=2)
def test_mower_snapshot(snapshot: SnapshotAssertion):
    """Testing a snapshot of a high feature mower."""
    # pylint: disable=duplicate-code
    mower_fixture = load_fixture("high_feature_mower.json")
    mower_python = json.loads(mower_fixture)
    mowers = mower_list_to_dictionary_dataclass(mower_python)
    for field in fields(mowers[MOWER_ID]):
        field_name = field.name
        field_value = getattr(mowers[MOWER_ID], field_name)
        assert field_value == snapshot(name=f"{field_name}")
