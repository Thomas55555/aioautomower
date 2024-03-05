"""Tests for asynchronous Python client for aioautomower."""

import json


from aioautomower.utils import (
    mower_list_to_dictionary_dataclass,
    husqvarna_schedule_to_calendar,
)
from tests import load_fixture

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


def test_mower_snapshot(snapshot):
    """Testing a snapshot of a high feature mower."""
    # pylint: disable=duplicate-code
    mower_fixture = load_fixture("high_feature_mower.json")
    mower_python = json.loads(mower_fixture)
    mowers = mower_list_to_dictionary_dataclass(mower_python)
    assert husqvarna_schedule_to_calendar(mowers[MOWER_ID].calendar) == snapshot(
        name="calendar"
    )
