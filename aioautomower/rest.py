"""Automower library using aiohttp."""
import logging
import time
from urllib.parse import quote_plus, urlencode

import aiohttp

from .const import AUTH_API_URL, AUTH_HEADERS, MOWER_API_BASE_URL, TOKEN_URL, USER_URL

_LOGGER = logging.getLogger(__name__)

timeout = aiohttp.ClientTimeout(total=10)


class TokenError(Exception):
    """Raised when Husqvarna Authentication API request ended in error 400."""

    def __init__(self, status: str):
        """Initialize."""
        super().__init__(status)
        self.status = status


class TokenRefreshError(Exception):
    """Raised when Husqvarna Authentication API is not able to refresh the token (Error 400 or 404)."""

    def __init__(self, status: str):
        """Initialize."""
        super().__init__(status)
        self.status = status


class TokenValidationError(Exception):
    """Raised when Husqvarna Authentication API token request ended in error 404. The reason might be an invalid token or that a refresh is needed"""

    def __init__(self, status: str):
        """Initialize."""
        super().__init__(status)
        self.status = status


class GetAccessToken:
    """Class to get an acces token from the Authentication API."""

    def __init__(self, api_key, username, password):
        """Initialize the Auth-API and store the auth so we can make requests."""
        self.username = username
        self.password = password
        self.api_key = api_key
        self.auth_data = urlencode(
            {
                "client_id": self.api_key,
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            },
            quote_via=quote_plus,
        )

    async def async_get_access_token(self):
        """Return the token."""
        async with aiohttp.ClientSession(headers=AUTH_HEADERS) as session:
            async with session.post(AUTH_API_URL, data=self.auth_data) as resp:
                _LOGGER.debug("Resp.status get access token: %i", resp.status)
                if resp.status == 200:
                    result = await resp.json(encoding="UTF-8")
                    result["expires_at"] = result["expires_in"] + time.time()
                if resp.status >= 400:
                    raise TokenError(
                        f"The token is invalid, respone from Husqvarna Automower API: {resp.status}"
                    )
        result["status"] = resp.status
        return result


class RefreshAccessToken:
    """Class to renew the Access Token."""

    def __init__(self, api_key, refresh_token):
        """Initialize the Auth-API and store the auth so we can make requests."""
        self.api_key = api_key
        self.refresh_token = refresh_token
        self.auth_data = urlencode(
            {
                "client_id": self.api_key,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            quote_via=quote_plus,
        )

    async def async_refresh_access_token(self):
        """Return the refresh token."""
        async with aiohttp.ClientSession(headers=AUTH_HEADERS) as session:
            async with session.post(AUTH_API_URL, data=self.auth_data) as resp:
                _LOGGER.debug("Resp.status refresh token: %i", resp.status)
                if resp.status == 200:
                    result = await resp.json(encoding="UTF-8")
                    result["expires_at"] = result["expires_in"] + time.time()
                    result["status"] = resp.status
                    return result
                elif resp.status in [400, 401, 404]:
                    raise TokenRefreshError(
                        f"The token cannot be refreshed, respone from Husqvarna Automower API: {resp.status}"
                    )


class ValidateAccessToken:
    """Class to validate the Access Token."""

    def __init__(self, api_key, access_token, provider):
        """Initialize the Auth-API and store the auth so we can make requests."""
        self.api_key = api_key
        self.access_token = access_token
        self.provider = provider
        self.token_url = f"{TOKEN_URL}/{self.access_token}"
        self.token_headers = {
            "Authorization-Provider": "{0}".format(self.provider),
            "Accept": "application/json",
            "X-Api-Key": "{0}".format(self.api_key),
        }

    async def async_validate_access_token(self):
        """Returns information about the current token."""
        _LOGGER.warning(
            "The class 'DeleteAccessToken' is depracated, use 'HandleAccessToken' instead"
        )
        async with aiohttp.ClientSession(headers=self.token_headers) as session:
            async with session.get(self.token_url) as resp:
                _LOGGER.debug("Resp.status validate token: %i", resp.status)
                if resp.status == 200:
                    result = await resp.json(encoding="UTF-8")
                if resp.status == 404:
                    raise TokenValidationError(
                        f"The token is probably expired or invalid, respone from Husqvarna Automower API: {resp.status}"
                    )
        result["status"] = resp.status
        return result


class DeleteAccessToken:
    """Class to invalidate an access token."""

    def __init__(self, api_key, provider, access_token):
        """Initialize the Auth-API and store the auth so we can make requests."""
        self.api_key = api_key
        self.provider = provider
        self.delete_headers = {
            "Authorization-Provider": "{0}".format(self.provider),
            "X-Api-Key": "{0}".format(self.api_key),
            "Accept": "application/json",
        }
        self.access_token = access_token
        self.delete_url = f"{TOKEN_URL}/{self.access_token}"

    async def async_delete_access_token(self):
        """Delete the token."""
        _LOGGER.warning(
            "The class 'DeleteAccessToken' is depracated, use 'HandleAccessToken' instead"
        )
        async with aiohttp.ClientSession(headers=self.delete_headers) as session:
            async with session.delete(self.delete_url) as resp:
                _LOGGER.debug("Resp.status delete token: %i", resp.status)
                if resp.status == 204:
                    result = await resp.json(encoding="UTF-8")
                if resp.status >= 400:
                    resp.raise_for_status()
        return result


class HandleAccessToken:
    """Class to validate and invalidate an access token."""

    def __init__(self, api_key, access_token, provider):
        """Initialize the Auth-API and store the auth so we can make requests."""
        self.api_key = api_key
        self.access_token = access_token
        self.provider = provider
        self.token_url = f"{TOKEN_URL}/{self.access_token}"
        self.token_headers = {
            "Authorization-Provider": "{0}".format(self.provider),
            "Accept": "application/json",
            "X-Api-Key": "{0}".format(self.api_key),
        }

    async def async_validate_access_token(self):
        """Returns information about the current token."""
        async with aiohttp.ClientSession(headers=self.token_headers) as session:
            async with session.get(self.token_url) as resp:
                _LOGGER.debug("Resp.status validate token: %i", resp.status)
                if resp.status == 200:
                    result = await resp.json(encoding="UTF-8")
                if resp.status == 404:
                    raise TokenValidationError(
                        f"The token is probably expired or invalid, respone from Husqvarna Automower API: {resp.status}"
                    )
        result["status"] = resp.status
        return result

    async def async_delete_access_token(self):
        """Delete the token."""
        async with aiohttp.ClientSession(headers=self.token_headers) as session:
            async with session.delete(self.token_url) as resp:
                _LOGGER.debug("Resp.status delete token: %i", resp.status)
                if resp.status == 204:
                    result = await resp.json(encoding="UTF-8")
                if resp.status >= 400:
                    resp.raise_for_status()
        return result


class GetMowerData:
    """Class to communicate with the Automower Connect API."""

    def __init__(self, api_key, access_token, provider, token_type):
        """Initialize the Communication API to get data."""
        self.api_key = api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_headers = {
            "Authorization": "{0} {1}".format(self.token_type, self.access_token),
            "Authorization-Provider": "{0}".format(self.provider),
            "Content-Type": "application/vnd.api+json",
            "X-Api-Key": "{0}".format(self.api_key),
        }

    async def async_mower_state(self):
        """Return the mowers data as a list of mowers."""
        async with aiohttp.ClientSession(
            headers=self.mower_headers, timeout=timeout
        ) as session:
            async with session.get(MOWER_API_BASE_URL) as resp:
                _LOGGER.debug("Resp.status mower data: %i", resp.status)
                if resp.status == 200:
                    result = await resp.json(encoding="UTF-8")
                    _LOGGER.debug("Result: %s", result)
                if resp.status >= 400:
                    resp.raise_for_status()
        result["status"] = resp.status
        return result


class Return:
    """Class to send commands to the Automower Connect API."""

    def __init__(
        self,
        api_key,
        access_token,
        provider,
        token_type,
        mower_id,
        payload,
        command_type,
    ):
        """Initialize the API and store the auth so we can send commands."""
        self.api_key = api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_id = mower_id
        self.command_type = command_type
        self.mower_headers = {
            "Authorization": "{0} {1}".format(self.token_type, self.access_token),
            "Authorization-Provider": "{0}".format(self.provider),
            "Content-Type": "application/vnd.api+json",
            "accept": "*/*",
            "X-Api-Key": "{0}".format(self.api_key),
        }
        self.mower_action_url = (
            f"{MOWER_API_BASE_URL}{self.mower_id}/{self.command_type}"
        )
        self.payload = payload

    async def async_mower_command(self):
        """Send a payload to the mower to execute a command."""
        async with aiohttp.ClientSession(headers=self.mower_headers) as session:
            async with session.post(self.mower_action_url, data=self.payload) as resp:
                await session.close()
        _LOGGER.debug("Mower Action URL: %s", self.mower_action_url)
        _LOGGER.debug("Sent payload: %s", self.payload)
        _LOGGER.debug("Resp status mower command: %s", resp.status)
        if resp.status >= 400:
            resp.raise_for_status()


class GetUserInformation:
    """Class to get user information."""

    def __init__(self, api_key, access_token, provider, token_type, user_id):
        """Initialize the Auth-API and store the auth so we can make requests."""
        self.api_key = api_key
        self.provider = provider
        self.token_type = token_type
        self.access_token = access_token
        self.user_id = user_id
        self.user_headers = {
            "Authorization": "{0} {1}".format(self.token_type, self.access_token),
            "Authorization-Provider": "{0}".format(self.provider),
            "X-Api-Key": "{0}".format(self.api_key),
            "Accept": "application/json",
        }
        self.user_url = f"{USER_URL}/{self.user_id}"
        _LOGGER.debug("user headers: %s", self.user_headers)
        _LOGGER.debug("user url: %s", self.user_url)

    async def async_get_user_information(self):
        """Get user information."""
        async with aiohttp.ClientSession(headers=self.user_headers) as session:
            async with session.get(self.user_url) as resp:
                _LOGGER.debug("Resp.status get user information: %i", resp.status)
                if resp.status == 200:
                    result = await resp.json(encoding="UTF-8")
                    _LOGGER.debug("User information: %s", result)
                if resp.status >= 400:
                    resp.raise_for_status()
        return result
