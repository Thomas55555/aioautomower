"""Tests for aioautomower utils."""

import unittest
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from aioresponses import aioresponses

from aioautomower.utils import (
    ApiException,
    async_get_access_token,
    async_invalidate_access_token,
)


class TestAuthenticationFunctions(unittest.IsolatedAsyncioTestCase):
    """Test suite."""

    @patch("aiohttp.ClientSession.post")
    @patch("time.time", return_value=1733953391.0)  # Mock time to return a fixed value
    async def test_async_get_access_token_success(self, mock_time, mock_post):
        """Test the success case of async_get_access_token function."""
        # Prepare mock response data
        mock_response_data = {"access_token": "mock_token", "expires_in": 3600}

        # Create the mock response
        mock_response = AsyncMock(aiohttp.ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)

        # Mock the context manager behavior of post
        mock_post.return_value.__aenter__.return_value = mock_response

        client_id = "test_client_id"
        client_secret = "test_client_secret"

        # Call the async_get_access_token function
        result = await async_get_access_token(client_id, client_secret)

        # Assert the result
        assert result["access_token"] == "mock_token"

        # Mocked time will now be consistent, so we can directly calculate the expected expires_at
        expected_expires_at = 1733953391.0 + mock_response_data["expires_in"]
        assert result["expires_at"] == expected_expires_at

        assert result["status"] == 200

    @patch("aiohttp.ClientSession.post")
    async def test_async_get_access_token_failure(self, mock_post):
        """Test the failure case of async_get_access_token function."""
        # Prepare mock error response data
        mock_response_data = {"error": "invalid_grant"}

        # Create the mock response
        mock_response = AsyncMock(aiohttp.ClientResponse)
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value=mock_response_data)

        # Mock the context manager behavior of post
        mock_post.return_value.__aenter__.return_value = mock_response

        client_id = "test_client_id"
        client_secret = "test_client_secret"

        # Call the async_get_access_token function and assert exception
        with pytest.raises(ApiException):
            await async_get_access_token(client_id, client_secret)

    @aioresponses()
    async def test_async_invalidate_access_token_success(self, mock_post):
        """Test the success case of async_invalidate_access_token function."""
        # Mock the response data for token invalidation
        mock_response_data = {"message": "Token revoked successfully"}

        # Mock the POST request
        mock_post.post(
            "https://api.authentication.husqvarnagroup.dev/v1/oauth2/revoke",
            status=200,
            payload=mock_response_data,
        )

        valid_access_token = "valid_token"
        access_token_to_invalidate = "token_to_invalidate"

        # Call the async_invalidate_access_token function
        result = await async_invalidate_access_token(
            valid_access_token, access_token_to_invalidate
        )

        # Assert the result
        assert result["message"] == "Token revoked successfully"

    @aioresponses()
    async def test_async_invalidate_access_token_failure(self, mock_post):
        """Test the failure case of async_invalidate_access_token function."""
        # Mock the response data for token invalidation error
        mock_response_data = {"error": "invalid_token"}

        # Mock the POST request to return error
        mock_post.post(
            "https://api.authentication.husqvarnagroup.dev/v1/oauth2/revoke",
            status=400,
            payload=mock_response_data,
        )

        valid_access_token = "valid_token"
        access_token_to_invalidate = "token_to_invalidate"

        # Call the async_invalidate_access_token function and assert error handling
        with pytest.raises(aiohttp.ClientResponseError):
            await async_invalidate_access_token(
                valid_access_token, access_token_to_invalidate
            )
