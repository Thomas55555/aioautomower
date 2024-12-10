"""Tests for aioautomower auth module."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from aioautomower.auth import AbstractAuth
from aioautomower.const import API_BASE_URL, AUTH_HEADER_FMT, WS_URL
from aioautomower.session import AutomowerEndpoint
from tests import load_fixture

from .const import MOWER_ID


class MyAuth(AbstractAuth):
    """Auth for aioautomower auth module."""

    async def async_get_access_token(self, jwt_token) -> str:
        """Return mocked access token."""
        return jwt_token


# @pytest.mark.asyncio
# async def test_get_request_success(jwt_token):
#     async with ClientSession() as session:
#         # Initialize the subclass with a mocked session and host
#         auth = MyAuth(session, API_BASE_URL)

#         # Mock the access token method
#         auth.async_get_access_token = AsyncMock(return_value=jwt_token)

#         # Use aioresponses to mock HTTP GET request
#         with aioresponses() as m:
#             url = f"{API_BASE_URL}/{AutomowerEndpoint.mowers}"
#             mocked_response = json.loads(load_fixture("high_feature_mower.json"))
#             m.get(url, payload=mocked_response, status=200)

#             # Call the `get_json` method
#             response = await auth.get_json(AutomowerEndpoint.mowers)

#             # Assertions
#             assert response == mocked_response
#             auth.async_get_access_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_request_success(jwt_token):
    """Test post command."""
    async with ClientSession() as session:
        auth = MyAuth(session, "https://mockapi.com")

        # Mock the access token method
        auth.async_get_access_token = AsyncMock(return_value=jwt_token)

        with aioresponses() as m:
            url = "https://mockapi.com/resource"
            post_payload = {"data": "test"}
            mocked_response = {"result": "success"}
            m.post(url, payload=mocked_response, status=201)

            # Call the `post_json` method
            response = await auth.post_json("resource", json=post_payload)

            # Assertions
            assert response == mocked_response
            auth.async_get_access_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_patch_request_success(jwt_token):
    """Test patch command."""
    async with ClientSession() as session:
        # Initialize the subclass with a mocked session and host
        auth = MyAuth(session, API_BASE_URL)

        # Mock the access token method
        auth.async_get_access_token = AsyncMock(return_value=jwt_token)

        # Use aioresponses to mock HTTP GET request
        with aioresponses() as m:
            url = f"{API_BASE_URL}/{AutomowerEndpoint.stay_out_zones.format(
            mower_id=MOWER_ID, stay_out_id="1234")}"
            mocked_response = json.loads(load_fixture("high_feature_mower.json"))
            m.patch(url, payload=mocked_response, status=200)

            # Call the `get_json` method
            response = await auth.patch_json(
                url=AutomowerEndpoint.stay_out_zones.format(
                    mower_id=MOWER_ID, stay_out_id="1234"
                ),
            )

            # Assertions
            assert response == mocked_response
            auth.async_get_access_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_websocket_connect(jwt_token):
    """Test websocket connection."""
    async with ClientSession() as session:
        auth = MyAuth(session, "https://mockapi.com")

        # Mock the access token method
        auth.async_get_access_token = AsyncMock(return_value=jwt_token)

        # Mock websocket connection
        with patch(
            "aiohttp.ClientSession.ws_connect", new_callable=AsyncMock
        ) as mock_ws_connect:
            # Mock the websocket object
            mock_ws = AsyncMock()
            mock_ws_connect.return_value = mock_ws

            # Call the `websocket_connect` method
            await auth.websocket_connect()

            # Assertions
            mock_ws_connect.assert_called_once_with(
                url=WS_URL,
                headers={"Authorization": AUTH_HEADER_FMT.format(jwt_token)},
                heartbeat=60,
            )
            assert auth.ws == mock_ws
