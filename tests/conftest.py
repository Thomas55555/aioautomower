"""Test helpers for Husqvarna Automower."""

import zoneinfo
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from aioresponses import aioresponses
from syrupy import SnapshotAssertion

from aioautomower.auth import AbstractAuth
from aioautomower.const import API_BASE_URL
from aioautomower.session import AutomowerSession
from tests import load_fixture_json

from .syrupy import AutomowerSnapshotExtension

TEST_TZ = zoneinfo.ZoneInfo("Europe/Berlin")


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Automower extension."""
    return snapshot.use_extension(AutomowerSnapshotExtension)


@pytest.fixture(name="mower_tz")
def mock_mower_tz() -> zoneinfo.ZoneInfo:
    """Return snapshot assertion fixture with the Automower extension."""
    return zoneinfo.ZoneInfo("Europe/Berlin")


@pytest.fixture(name="jwt_token")
def mock_jwt_token() -> str:
    """Return snapshot assertion fixture with the Automower extension."""
    return load_fixture_json("jwt.json")["data"]


@pytest.fixture(name="control_response")
def mock_control_response() -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    return load_fixture_json("control_response.json")


@pytest.fixture(name="mower_data")
def mock_mower_data() -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    return load_fixture_json("high_feature_mower.json")


@pytest.fixture
def mock_automower_client() -> Generator[AsyncMock, None, None]:
    """Mock a Auth Automower client."""
    with patch(
        "aioautomower.auth.AbstractAuth",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        client.get_json.return_value = load_fixture_json("high_feature_mower.json")
        yield client


@pytest.fixture
def mock_automower_client_without_tasks() -> Generator[AsyncMock, None, None]:
    """Mock a Auth Automower client."""
    with patch(
        "aioautomower.auth.AbstractAuth",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        client.get_json.return_value = load_fixture_json(
            "high_feature_mower_without_tasks.json"
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
        mower1_python = load_fixture_json("high_feature_mower.json")
        mower2_python = load_fixture_json("low_feature_mower.json")
        mowers_python = {"data": mower1_python["data"] + mower2_python["data"]}
        client.get_json.return_value = mowers_python
        yield client


@pytest.fixture(name="automower_client")
async def aio_client(
    jwt_token: str, mower_tz: zoneinfo.ZoneInfo
) -> AsyncGenerator[AutomowerSession, None]:
    """Return an Automower session client."""

    class MockAuth(AbstractAuth):
        async def async_get_access_token(self) -> str:
            return jwt_token

        async def __aenter__(self):
            # Perform any setup needed for MyAuth
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            # Perform any cleanup needed for MyAuth
            await self._websession.close()

    async with (
        aiohttp.ClientSession() as session,
        MockAuth(websession=session, host=API_BASE_URL) as auth,
    ):
        automower_client = AutomowerSession(auth=auth, mower_tz=mower_tz, poll=False)
        yield automower_client


@pytest.fixture(name="responses")
def aioresponses_fixture() -> Generator[aioresponses, None, None]:
    """Return aioresponses fixture."""
    with aioresponses() as mocked_responses:
        yield mocked_responses
