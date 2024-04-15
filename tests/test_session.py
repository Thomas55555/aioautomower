"""Test automower session."""

import json
from dataclasses import fields
from unittest.mock import AsyncMock

from syrupy.assertion import SnapshotAssertion

from aioautomower.session import AutomowerSession
from tests import load_fixture

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"


async def test_connect(snapshot: SnapshotAssertion):
    """Test automower session."""
    auth_mock = AsyncMock()
    session = AutomowerSession(auth_mock)

    # Call the connect method and assert
    await session.connect()
    auth_mock.get_json.return_value = json.loads(load_fixture("raw_data.json"))
    data = await session.get_status()
    for field in fields(data[MOWER_ID]):
        field_name = field.name
        field_value = getattr(data[MOWER_ID], field_name)
        assert field_value == snapshot(name=f"{field_name}")
