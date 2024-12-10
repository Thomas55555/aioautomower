"""Tests for aioautomower auth module."""

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from aioautomower.auth import AbstractAuth
from aioautomower.const import AUTH_HEADER_FMT, WS_URL


class MyAuth(AbstractAuth):
    """Auth for aioautomower auth module."""

    async def async_get_access_token(self, jwt_token) -> str:
        """Return mocked access token."""
        return jwt_token


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
