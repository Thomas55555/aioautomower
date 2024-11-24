"""Test helpers for Husqvarna Automower."""

import json
import zoneinfo
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession
from syrupy import SnapshotAssertion

from tests import load_fixture

from .syrupy import AutomowerSnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Automower extension."""
    return snapshot.use_extension(AutomowerSnapshotExtension)


@pytest.fixture(name="mower_tz")
def mower_tz() -> zoneinfo.ZoneInfo:
    """Return snapshot assertion fixture with the Automower extension."""
    return zoneinfo.ZoneInfo("Europe/Berlin")


@pytest.fixture(name="jwt_token")
def mock_jwt_token() -> str:
    """Return snapshot assertion fixture with the Automower extension."""
    return json.loads(load_fixture("jwt.json"))["data"]


@pytest.fixture
def mock_automower_client() -> Generator[AsyncMock, None, None]:
    """Mock a Auth Automower client."""
    with patch(
        "aioautomower.auth.AbstractAuth",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        client.get_json.return_value = json.loads(
            load_fixture("high_feature_mower.json")
        )
        yield client


@pytest.fixture
def mock_automower_client_without_tasks() -> Generator[AsyncMock, None, None]:
    """Mock a Auth Automower client."""
    with patch(
        "aioautomower.auth.AbstractAuth",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        client.get_json.return_value = json.loads(
            load_fixture("high_feature_mower_without_tasks.json")
        )
        yield client


@pytest.fixture
def mock_automower_client_two_mowers() -> Generator[AsyncMock, None, None]:
    """Mock a Auth Automower client."""
    with patch(
        "aioautomower.auth.AbstractAuth",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        mower_fixture = load_fixture("high_feature_mower.json")
        mower1_python = json.loads(mower_fixture)
        mower_fixture = load_fixture("low_feature_mower.json")
        mower2_python = json.loads(mower_fixture)
        mowers_python = {"data": mower1_python["data"] + mower2_python["data"]}
        client.get_json.return_value = mowers_python
        yield client


@pytest.fixture
async def async_session_fixture():
    """Fixture for creating an aiohttp session."""
    async with ClientSession() as session:
        yield session


@pytest.fixture
def test_host_fixture():
    """Fixture providing a mock host URL."""
    return "http://testhost"
