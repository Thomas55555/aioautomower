"""Automower library using aiohttp."""
from __future__ import annotations

import logging
import time
from urllib.parse import quote_plus, urlencode

import aiohttp

from .const import API_BASE_URL, AUTH_API_REVOKE_URL, AUTH_API_TOKEN_URL, AUTH_HEADERS

_LOGGER = logging.getLogger(__name__)

timeout = aiohttp.ClientTimeout(total=10)


class CommandNotPossibleError(Exception):
    """Raised when command couldn't be send to the mower que."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class TokenError(Exception):
    """Raised when Husqvarna Authentication API request ended in error 400."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class TokenRefreshError(Exception):
    """Raised when Husqvarna Authentication API is not able to refresh the token.

    on (Error 400 or 404).
    """

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class MowerApiConnectionsError(Exception):
    """Raised when Husqvarna Connect API request ended in error 403."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class GetAccessTokenClientCredentials:
    """Legacy class to get an acces token from the Authentication API with client_credentials.

    This grant type is intended only for you. If you want other users to use your
    application, then they should login using Authorization Code Grant.
    """

    def __init__(self, client_id, client_secret) -> None:
        """Initialize the Auth-API and store the auth so we can make requests."""
        _LOGGER.warning(
            """The GetAccessTokenClientCredentials class is depracated. Please migrate
            to async_get_access_token function in utils.py."""
        )
        self.auth_data = urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            quote_via=quote_plus,
        )

    async def async_get_access_token(self) -> dict:
        """Return the token."""
        async with aiohttp.ClientSession(headers=AUTH_HEADERS) as session, session.post(
            AUTH_API_TOKEN_URL, data=self.auth_data
        ) as resp:
            result = await resp.json(encoding="UTF-8")
            _LOGGER.debug("Resp.status get access token: %s", result)
            if resp.status == 200:
                result = await resp.json(encoding="UTF-8")
                result["expires_at"] = result["expires_in"] + time.time()
            if resp.status >= 400:
                raise TokenError(
                    f"""The token is invalid, respone
                        from Husqvarna Automower API: {result}"""
                )
        result["status"] = resp.status
        return result


class RefreshAccessToken:
    """Class to renew the Access Token."""

    def __init__(self, api_key, refresh_token) -> None:
        """Initialize the Auth-API and store the auth so we can make requests."""
        _LOGGER.warning(
            "The RefreshAccessToken class is depracated. Please migrate to AutomowerApi class"
        )
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

    async def async_refresh_access_token(self) -> dict:
        """Return the refresh token."""
        async with aiohttp.ClientSession(headers=AUTH_HEADERS) as session, session.post(
            AUTH_API_TOKEN_URL, data=self.auth_data
        ) as resp:
            result = await resp.json(encoding="UTF-8")
            _LOGGER.debug("Resp.status refresh token: %s", result)
            if resp.status == 200:
                result["expires_at"] = result["expires_in"] + time.time()
                result["status"] = resp.status
                return result
            if resp.status in [400, 401, 404]:
                raise TokenRefreshError(
                    f"""The token cannot be refreshed,
                        respone from Husqvarna Automower API: {result}"""
                )


class RevokeAccessToken:
    """Class to invalidate an access token."""

    def __init__(self, access_token) -> None:
        """Initialize the Auth-API and store the auth so we can make requests."""
        _LOGGER.warning(
            """The RevokeAccessToken class is depracated.
            Please migrate to async_get_access_token funtion in utils.py"""
        )
        self.access_token = access_token
        self.auth_data = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "*/*",
        }

    async def async_delete_access_token(self) -> dict:
        """Delete the token."""
        async with aiohttp.ClientSession(
            headers=self.auth_data
        ) as session, session.post(
            AUTH_API_REVOKE_URL, data=(f"token={self.access_token}")
        ) as resp:
            result = await resp.json(encoding="UTF-8")
            _LOGGER.debug("Resp.status delete token: %s", resp.status)
            if resp.status >= 400:
                resp.raise_for_status()
                _LOGGER.error("Response body delete token: %s", result)
        return result


class GetMowerData:
    """Class to communicate with the Automower Connect API."""

    def __init__(self, api_key, access_token, provider, token_type) -> None:
        """Initialize the Communication API to get data."""
        _LOGGER.warning(
            "The GetMowerData class is depracated. Please migrate to AutomowerSession class"
        )
        self.api_key = api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_headers = {
            "Authorization": f"{self.token_type} {self.access_token}",
            "Authorization-Provider": f"{self.provider}",
            "Content-Type": "application/vnd.api+json",
            "X-Api-Key": f"{self.api_key}",
        }

    async def async_mower_state(self) -> dict[str, list]:
        """Return the mowers data as a list of mowers."""
        async with aiohttp.ClientSession(
            headers=self.mower_headers, timeout=timeout
        ) as session, session.get(API_BASE_URL) as resp:
            result = await resp.json(encoding="UTF-8")
            _LOGGER.debug("Response mower data: %s", resp)
            if resp.status == 200:
                result = await resp.json(encoding="UTF-8")
                for idx, _ent in enumerate(result["data"]):
                    result["data"][idx]["attributes"].update(
                        result["data"][idx]["attributes"]["settings"]
                    )
                    del result["data"][idx]["attributes"]["settings"]
                _LOGGER.debug("Result mower data: %s", result)
            if resp.status >= 400:
                _LOGGER.error("Response mower data: %s", result)
                if resp.status == 403:
                    raise MowerApiConnectionsError(
                        f"""Error {resp.status},
                            the mower state can't be fetched: {result}"""
                    )
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
    ) -> None:
        """Initialize the API and store the auth so we can send commands."""
        _LOGGER.warning(
            "The Return class is depracated. Please migrate to AutomowerSession class"
        )
        self.api_key = api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_id = mower_id
        self.command_type = command_type
        self.mower_headers = {
            "Authorization": f"{self.token_type} {self.access_token}",
            "Authorization-Provider": f"{self.provider}",
            "Content-Type": "application/vnd.api+json",
            "accept": "*/*",
            "X-Api-Key": f"{self.api_key}",
        }
        self.mower_action_url = (
            f"{API_BASE_URL}/mowers/{self.mower_id}/{self.command_type}"
        )
        self.payload = payload

    async def async_mower_command(self) -> None:
        """Send a payload to the mower to execute a command."""
        async with aiohttp.ClientSession(headers=self.mower_headers) as session:
            async with session.post(self.mower_action_url, data=self.payload) as resp:
                await session.close()
            _LOGGER.debug("Mower Action URL: %s", self.mower_action_url)
            _LOGGER.debug("Sent payload: %s", self.payload)
            _LOGGER.debug("Resp status mower command: %s", resp.status)
            if resp.status >= 400:
                raise CommandNotPossibleError(resp.status)
