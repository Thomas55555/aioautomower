"""Tests for asynchronous Python client for aioautomower."""

import zoneinfo

from syrupy.assertion import SnapshotAssertion

from aioautomower.model import error_key_dict, error_key_list
from aioautomower.utils import mower_list_to_dictionary_dataclass
from tests import load_fixture_json

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_error_key(mower_tz: zoneinfo.ZoneInfo) -> None:
    """Test translating an error code to an error key."""
    mower_python = load_fixture_json("high_feature_mower.json")
    mowers = mower_list_to_dictionary_dataclass(mower_python, mower_tz)
    assert mowers[MOWER_ID].mower.error_key is None

    mower_python["data"][0]["attributes"]["mower"]["errorCode"] = 1
    mowers = mower_list_to_dictionary_dataclass(mower_python, mower_tz)
    assert mowers[MOWER_ID].mower.error_key == "outside_working_area"

    mower_python["data"][0]["attributes"]["mower"]["errorCode"] = 8
    mowers = mower_list_to_dictionary_dataclass(mower_python, mower_tz)
    assert mowers[MOWER_ID].mower.error_key == "wrong_pin_code"

    mower_python["data"][0]["attributes"]["mower"]["errorCode"] = 18
    mowers = mower_list_to_dictionary_dataclass(mower_python, mower_tz)
    assert mowers[MOWER_ID].mower.error_key == "collision_sensor_problem_rear"

    mower_python["data"][0]["attributes"]["mower"]["errorCode"] = 78
    mowers = mower_list_to_dictionary_dataclass(mower_python, mower_tz)
    assert (
        mowers[MOWER_ID].mower.error_key
        == "slipped_mower_has_slipped_situation_not_solved_with_moving_pattern"
    )


async def test_error_keys_snapshot(snapshot: SnapshotAssertion) -> None:
    """Make a snapshot of the error keys."""
    assert error_key_list() == snapshot


async def test_error_key_dict_snapshot(snapshot: SnapshotAssertion) -> None:
    """Make a snapshot of the error key dictionary."""
    assert error_key_dict() == snapshot
