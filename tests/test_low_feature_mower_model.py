"""Tests for asynchronous Python client for aioautomower."""

import json
from dataclasses import fields


from aioautomower.utils import mower_list_to_dictionary_dataclass
from tests import load_fixture

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_low_feature_mower() -> None:
    """Test converting a low feature mower."""
    mower_fixture = load_fixture("low_feature_mower.json")
    mower_python = json.loads(mower_fixture)
    mowers = mower_list_to_dictionary_dataclass(mower_python)
    assert mowers[MOWER_ID].headlight.mode is None
    assert mowers[MOWER_ID].cutting_height is None
    assert len(mowers[MOWER_ID].positions) == 0


def test_mower_snapshot(snapshot):
    """Testing a snapshot of a high feature mower."""
    mower_fixture = load_fixture("low_feature_mower.json")
    mower_python = json.loads(mower_fixture)
    mowers = mower_list_to_dictionary_dataclass(mower_python)
    for field in fields(mowers[MOWER_ID]):
        field_name = field.name
        field_value = getattr(mowers[MOWER_ID], field_name)
        assert field_value == snapshot(name=f"{field_name}")
