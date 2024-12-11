"""Tests for asynchronous Python client for aioautomower."""

from dataclasses import fields

from freezegun import freeze_time
from syrupy.assertion import SnapshotAssertion

from aioautomower.utils import mower_list_to_dictionary_dataclass
from tests import load_fixture_json

MOWER_ID = "1234"


async def test_low_feature_mower(mower_tz) -> None:
    """Test converting a low feature mower."""
    mower_python = load_fixture_json("low_feature_mower.json")
    mowers = mower_list_to_dictionary_dataclass(mower_python, mower_tz)
    assert mowers[MOWER_ID].settings.headlight.mode is None
    assert mowers[MOWER_ID].settings.cutting_height is None
    assert len(mowers[MOWER_ID].positions) == 0
    assert isinstance(mowers[MOWER_ID].positions, list)
    assert isinstance(mowers[MOWER_ID].calendar.tasks, list)


@freeze_time("2024-05-06 02:50:00")
def test_mower_snapshot(snapshot: SnapshotAssertion, mower_tz) -> None:
    """Testing a snapshot of a high feature mower."""
    mower_python = load_fixture_json("low_feature_mower.json")
    mowers = mower_list_to_dictionary_dataclass(mower_python, mower_tz)
    for field in fields(mowers[MOWER_ID]):
        field_name = field.name
        field_value = getattr(mowers[MOWER_ID], field_name)
        assert field_value == snapshot(name=f"{field_name}")
