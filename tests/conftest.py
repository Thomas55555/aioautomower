"""Test helpers for Husqvarna Automower."""

import zoneinfo
from collections.abc import AsyncGenerator, Callable, Generator
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
import pytest_asyncio
from aiointercept import aiointercept
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
def mower_data_fixture(request: pytest.FixtureRequest) -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    param = getattr(request, "param", None)
    if param is None:
        param = "high_feature_mower_data"
    return request.getfixturevalue(param)


@pytest.fixture(name="high_feature_mower_data")
def mock_high_feature_mower_data() -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    return load_fixture_json("high_feature_mower.json")


@pytest.fixture(name="low_feature_mower_data")
def mock_low_feature_mower_data() -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    return load_fixture_json("low_feature_mower.json")


@pytest.fixture(name="two_mower_data")
def mock_two_mower_data() -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    mower1_python = load_fixture_json("high_feature_mower.json")
    mower2_python = load_fixture_json("low_feature_mower.json")
    return {"data": mower1_python["data"] + mower2_python["data"]}


@pytest.fixture(name="mower_data_without_tasks")
def mock_mower_data_without_tasks() -> dict:
    """Return a fixture for a high feature mower without tasks."""
    return load_fixture_json("high_feature_mower_without_tasks.json")


@pytest.fixture(name="trash_mower_data")
def mock_trash_mower_data() -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    return load_fixture_json("rest_trash.json")


@pytest.fixture(name="message_data")
def mock_message_data_fixture(request: pytest.FixtureRequest) -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    param = getattr(request, "param", None)
    if param is None:
        param = "high_feature_message_data"
    return request.getfixturevalue(param)


@pytest.fixture(name="high_feature_message_data")
def mock_message_data() -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    return load_fixture_json("message.json")


@pytest.fixture(name="low_feature_message_data")
def mock_empty_message_data() -> dict:
    """Return snapshot assertion fixture with the Automower extension."""
    return load_fixture_json("empty_message.json")


@pytest.fixture(name="automower_client")
def mock_automower_client(
    mower_data: dict,
    message_data: dict,
) -> Generator[AsyncMock, None, None]:
    """Mock a Auth Automower client with variable mower and message data."""

    def get_json_side_effect_factory(
        mower_data: dict,
        message_data: dict,
    ) -> Callable[[str], dict]:
        async def side_effect(url: str) -> dict:
            if "messages" in url:
                return message_data
            if "mowers" in url:
                return mower_data
            msg = f"Unexpected URL in get_json: {url}"
            raise ValueError(msg)

        return side_effect

    with patch(
        "aioautomower.auth.AbstractAuth",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        client.get_json = AsyncMock()
        client.get_json.side_effect = get_json_side_effect_factory(
            mower_data=mower_data,
            message_data=message_data,
        )
        yield client


@pytest_asyncio.fixture(name="aio_client", loop_scope="function")
async def mock_aio_client(
    jwt_token: str,
    mower_tz: zoneinfo.ZoneInfo,
) -> AsyncGenerator[AutomowerSession, None]:
    """Return an Automower session client."""

    class MockAuth(AbstractAuth):
        async def async_get_access_token(self) -> str:
            return jwt_token

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool:
            await self._websession.close()
            return False

    async with (
        aiohttp.ClientSession() as session,
        MockAuth(websession=session, host=API_BASE_URL) as auth,
    ):
        automower_client = AutomowerSession(
            auth=auth,
            mower_tz=mower_tz,
            poll=False,
        )
        yield automower_client


@pytest_asyncio.fixture(name="responses", loop_scope="function")
async def aiointercept_fixture() -> AsyncGenerator[aiointercept, None]:
    """Return aiointercept fixture."""
    async with aiointercept(mock_external_urls=True) as mocked_responses:
        yield mocked_responses
