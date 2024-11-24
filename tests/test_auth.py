"""Test automower auth."""

import aiohttp
import pytest

from aioautomower.auth import AbstractAuth, AuthException


class MockAuth(AbstractAuth):
    """Mock authentication class for testing."""

    def __init__(self, websession, host, jwt_token, simulate_token=None):
        """Initialize with a session, host, and optional token simulation."""
        super().__init__(websession, host)
        self.simulate_token = simulate_token
        self.request_with_retry = None  # Initialize attribute
        self.jwt_token = jwt_token

    async def get_access_token(self):
        """Return a mock access token or raise exceptions."""
        if self.simulate_token == "invalid":
            raise AuthException("Invalid token")
        if self.simulate_token == "error":
            raise RuntimeError("Unexpected error")  # More specific exception
        return self.jwt_token

    async def async_get_access_token(self):
        """Return a mock access token asynchronously."""
        return await self.get_access_token()

    async def request_with_token(self, method, url, **kwargs):
        """Simulate an HTTP request with a token."""
        if self.simulate_token == "invalid":
            raise AuthException("Unauthorized access")
        return {"id": 1}

    async def _handle_response(self, response):
        """Process a simulated API response or error."""
        if isinstance(response, aiohttp.ClientResponseError) and response.status in [
            401,
            403,
        ]:
            raise AuthException("Unauthorized access")
        return response if isinstance(response, dict) else await response.json()


@pytest.mark.asyncio
async def test_request_with_token_success(
    async_session_fixture,
    test_host_fixture,
    jwt_token,
):
    """Test successful token-based request."""
    auth = MockAuth(
        async_session_fixture,
        test_host_fixture,
        jwt_token,
    )
    response = await auth.request_with_token(
        "GET", "https://jsonplaceholder.typicode.com/todos/1"
    )
    assert response["id"] == 1


@pytest.mark.asyncio
async def test_request_with_token_invalid_token(
    async_session_fixture, test_host_fixture, jwt_token
):
    """Test token-based request with invalid token simulation."""
    auth = MockAuth(
        async_session_fixture, test_host_fixture, jwt_token, simulate_token="invalid"
    )
    with pytest.raises(AuthException, match="Unauthorized access"):
        await auth.request_with_token(
            "GET", "https://jsonplaceholder.typicode.com/todos/1"
        )


@pytest.mark.asyncio
async def test_get_json_failure(async_session_fixture, test_host_fixture, jwt_token):
    """Test failure in the get_json method due to invalid token."""
    auth = MockAuth(
        async_session_fixture, test_host_fixture, jwt_token, simulate_token="invalid"
    )

    async def mock_request_with_retry(method, url, **kwargs):
        raise AuthException("Invalid token")

    auth.request_with_retry = mock_request_with_retry
    with pytest.raises(AuthException, match="Invalid token"):
        await auth.get_json("https://jsonplaceholder.typicode.com/todos/1")
