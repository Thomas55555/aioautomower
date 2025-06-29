"""Test helpers for Husqvarna Automower."""

import asyncio
import zoneinfo
from collections.abc import AsyncGenerator, Generator
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from aioresponses import aioresponses
from syrupy import SnapshotAssertion

from aioautomower.auth import AbstractAuth
from aioautomower.const import API_BASE_URL
from aioautomower.session import AutomowerSession
from aioautomower.utils import mower_list_to_dictionary_dataclass
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


@pytest.fixture(name="two_mower_data")
def mock_two_mower_data() -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    mower1_python = load_fixture_json("high_feature_mower.json")
    mower2_python = load_fixture_json("low_feature_mower.json")
    return {"data": mower1_python["data"] + mower2_python["data"]}


@pytest.fixture(name="automower_api")
def automower_api(
    mower_tz: zoneinfo.ZoneInfo,
    monkeypatch: pytest.MonkeyPatch,
) -> AutomowerSession:
    """Mock a Auth Automower client."""
    raw = load_fixture_json("high_feature_mower.json")
    parsed = mower_list_to_dictionary_dataclass(raw, mower_tz)

    mock_auth = AsyncMock()

    loop = asyncio.new_event_loop()
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    session = AutomowerSession(mock_auth, mower_tz, poll=True)

    # Methode get_status patchen
    async def _fake_get_status() -> dict:
        session._data = raw  # noqa: SLF001
        session.data = parsed
        session.current_mowers = set(parsed.keys())
        return parsed

    # async_get_message patchen
    session.get_status = _fake_get_status  # type: ignore[method-assign]
    session.async_get_message = AsyncMock(return_value=None)  # type: ignore[attr-defined]

    return session


@pytest.fixture(name="automower_api_without_tasks")
def mock_automower_client_without_tasks(
    mower_tz: zoneinfo.ZoneInfo,
) -> Generator[AsyncMock, None, None]:
    """Mock a Auth Automower client."""
    mock = AsyncMock()
    data = mower_list_to_dictionary_dataclass(
        load_fixture_json("high_feature_mower_without_tasks.json"),
        mower_tz,
    )
    mock.get_status.return_value = data
    mock.async_get_message.return_value = None
    mock.data = data
    return mock


@pytest.fixture
def mock_automower_client_two_mowers(
    mower_tz: zoneinfo.ZoneInfo,
) -> Generator[AsyncMock, None, None]:
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
    # mock = AsyncMock()
    # mower1_python = load_fixture_json("high_feature_mower.json")
    # mower2_python = load_fixture_json("low_feature_mower.json")
    # mowers_python = {"data": mower1_python["data"] + mower2_python["data"]}
    # data = mower_list_to_dictionary_dataclass(
    #     mowers_python,
    #     mower_tz,
    # )
    # mock.get_status.return_value = data
    # mock.async_get_message.return_value = None
    # mock.data = data
    # return mock


@pytest.fixture(name="automower_client")
async def aio_client(
    jwt_token: str, mower_tz: zoneinfo.ZoneInfo
) -> AsyncGenerator[AutomowerSession, None]:
    """Return an Automower session client."""

    class MockAuth(AbstractAuth):
        async def async_get_access_token(self) -> str:
            return jwt_token

        async def __aenter__(self) -> Self:
            # Perform any setup needed for MyAuth
            return self

        async def __aexit__(
            self,
            exc_type: None | type[BaseException],
            exc_value: None | BaseException,
            traceback: None | TracebackType,
        ) -> bool:
            # Perform any cleanup needed for MyAuth
            await self._websession.close()
            return False

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
