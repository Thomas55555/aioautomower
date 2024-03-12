"""Tests for asynchronous Python client for aioautomower."""

import json


from aioautomower.utils import (
    mower_list_to_dictionary_dataclass,
    error_key_list,
    error_key_dict,
)
from tests import load_fixture


MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_error_key() -> None:
    """Test translating an error code to an error key."""
    mower_fixture = load_fixture("high_feature_mower.json")
    mower_python = json.loads(mower_fixture)
    mowers = mower_list_to_dictionary_dataclass(mower_python)
    assert mowers[MOWER_ID].mower.error_key is None

    mower_python["data"][0]["attributes"]["mower"]["errorCode"] = 1
    mowers = mower_list_to_dictionary_dataclass(mower_python)
    assert mowers[MOWER_ID].mower.error_key == "outside_working_area"

    mower_python["data"][0]["attributes"]["mower"]["errorCode"] = 8
    mowers = mower_list_to_dictionary_dataclass(mower_python)
    assert mowers[MOWER_ID].mower.error_key == "wrong_pin_code"

    mower_python["data"][0]["attributes"]["mower"]["errorCode"] = 18
    mowers = mower_list_to_dictionary_dataclass(mower_python)
    assert mowers[MOWER_ID].mower.error_key == "collision_sensor_problem_rear"

    mower_python["data"][0]["attributes"]["mower"]["errorCode"] = 78
    mowers = mower_list_to_dictionary_dataclass(mower_python)
    assert (
        mowers[MOWER_ID].mower.error_key
        == "slipped_mower_has_slipped_situation_not_solved_with_moving_pattern"
    )


async def test_error_keys_snapshot(snapshot) -> None:
    """Make a snapshot of the error keys."""
    assert error_key_list() == snapshot


async def test_error_key_dict_snapshot(snapshot) -> None:
    """Make a snapshot of the error key dictionary."""
    assert error_key_dict() == snapshot
