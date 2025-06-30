"""Tests for asynchronous Python client for aioautomower."""

import zoneinfo
from dataclasses import fields

import pytest
from syrupy.assertion import SnapshotAssertion

from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession
from aioautomower.utils import mower_list_to_dictionary_dataclass
from tests import load_fixture_json

MOWER_ID = "1234"


async def test_low_feature_mower(mower_tz: zoneinfo.ZoneInfo) -> None:
    """Test converting a low feature mower."""
    mower_python = load_fixture_json("low_feature_mower.json")
    mowers = mower_list_to_dictionary_dataclass(mower_python, mower_tz)
    assert mowers[MOWER_ID].settings.headlight.mode is None
    assert mowers[MOWER_ID].settings.cutting_height is None
    assert len(mowers[MOWER_ID].positions) == 0
    assert isinstance(mowers[MOWER_ID].positions, list)
    assert isinstance(mowers[MOWER_ID].calendar.tasks, list)


@pytest.mark.parametrize(
    ("mower_data", "message_data"),
    [("low_feature_mower_data", "low_feature_message_data")],
    indirect=True,
)
async def test_mower_snapshot(
    automower_client: AbstractAuth,
    snapshot: SnapshotAssertion,
    mower_tz: zoneinfo.ZoneInfo,
    mower_data: dict,
    message_data: dict,
) -> None:
    """Testing a snapshot of a low feature mower."""
    automower_api = AutomowerSession(automower_client, mower_tz=mower_tz, poll=True)
    await automower_api.connect()
    for field in fields(automower_api.data[MOWER_ID]):
        field_name = field.name
        field_value = getattr(automower_api.data[MOWER_ID], field_name)
        assert field_value == snapshot(name=field_name)
