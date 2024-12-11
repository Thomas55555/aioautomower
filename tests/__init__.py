"""Tests for asynchronous Python client for aioautomower.

Run tests with `poetry run pytest`
and to update snapshots `poetry run pytest --snapshot-update`
"""

import zoneinfo
from pathlib import Path

from aioresponses import aioresponses

from aioautomower.const import API_BASE_URL
from aioautomower.session import AutomowerEndpoint, AutomowerSession
from aioautomower.utils import mower_list_to_dictionary_dataclass

MOWER_ID = "c7233734-b219-4287-a173-08e3643f89f0"
MOWER_ID_LOW_FEATURE = "1234"


def load_fixture(filename: str) -> str:
    """Load a fixture."""
    path = Path(__package__) / "fixtures" / filename
    return path.read_text(encoding="utf-8")


async def setup_connection(
    responses: aioresponses,
    automower_client: AutomowerSession,
    mower_data,
    mower_tz: zoneinfo.ZoneInfo,
) -> None:
    """Fixture for setting up the connection."""

    responses.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        status=200,
        payload=mower_data,
    )
    assert await automower_client.get_status() == mower_list_to_dictionary_dataclass(
        mower_data,
        mower_tz,
    )
