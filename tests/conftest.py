"""Test helpers for Husqvarna Automower."""

import json
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from tests import load_fixture


@pytest.fixture()
def mock_automower_client() -> Generator[AsyncMock, None, None]:
    """Mock a Auth Automower client."""
    with patch(
        "aioautomower.auth.AbstractAuth",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        client.get_json.return_value = json.loads(load_fixture("raw_data.json"))
        yield client
