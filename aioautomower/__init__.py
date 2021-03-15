"""Automower library using aiohttp."""
import logging
import time
from urllib.parse import quote_plus, urlencode

import aiohttp

_LOGGER = logging.getLogger(__name__)


AUTH_API_URL = "https://api.authentication.husqvarnagroup.dev/v1/oauth2/token"
TOKEN_URL = "https://api.authentication.husqvarnagroup.dev/v1/token"
AUTH_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
}

MOWER_API_BASE_URL = "https://api.amc.husqvarna.dev/v1/mowers/"


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
                result = await resp.json(encoding="UTF-8")
                result["status"] = resp.status
                result["expires_at"] = result["expires_in"] + time.time()
        _LOGGER.debug("Resp.status: %i", result["status"])
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
                result = await resp.json(encoding="UTF-8")
                result["status"] = resp.status
                result["expires_at"] = result["expires_in"] + time.time()
        _LOGGER.debug("Resp.status: %i", result["status"])
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
        async with aiohttp.ClientSession(headers=self.mower_headers) as session:
            async with session.get(MOWER_API_BASE_URL) as resp:
                result = await resp.json(encoding="UTF-8")
                result["status"] = resp.status
        _LOGGER.debug("Result: %s", result)
        _LOGGER.debug("Resp.status: %i", result["status"])
        return result


class Return:
    """Class to send commands to the Automower Connect API."""

    def __init__(self, api_key, access_token, provider, token_type, mower_id, payload):
        """Initialize the API and store the auth so we can send commands."""
        self.api_key = api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_id = mower_id
        self.mower_headers = {
            "Authorization": "{0} {1}".format(self.token_type, self.access_token),
            "Authorization-Provider": "{0}".format(self.provider),
            "Content-Type": "application/vnd.api+json",
            "accept": "*/*",
            "X-Api-Key": "{0}".format(self.api_key),
        }
        self.mower_action_url = f"{MOWER_API_BASE_URL}{self.mower_id}/actions"
        self.payload = payload

    async def async_mower_command(self):
        """Send a payload to the mower to execute a command."""
        async with aiohttp.ClientSession(headers=self.mower_headers) as session:
            async with session.post(self.mower_action_url, data=self.payload) as resp:
                result = await session.close()
        _LOGGER.debug("Sent payload: %s", self.payload)
        _LOGGER.debug("Resp status: %s", resp.status)
        time.sleep(5)
        _LOGGER.debug("Waited 5s until mower state is updated")
        return resp.status


class DeleteAccessToken:
    """Class to invalidate an acces token."""

    def __init__(self, api_key, provider, access_token):
        """Initialize the Auth-API and store the auth so we can make requests."""
        self.api_key = api_key
        self.provider = provider
        self.delete_headers = {
            "Authorization-Provider": "{0}".format(self.provider),
            "X-Api-Key": "{0}".format(self.api_key),
        }
        self.access_token = access_token
        self.delete_url = f"{TOKEN_URL}/{self.access_token}"

    async def async_delete_access_token(self):
        """Delete the token."""
        async with aiohttp.ClientSession(headers=self.delete_headers) as session:
            async with session.delete(self.delete_url) as resp:
                result = await resp.json(encoding="UTF-8")
                result["status"] = resp.status
        _LOGGER.debug("Result: %s", result)
        _LOGGER.debug("Resp.status: %i", result["status"])
        return result
