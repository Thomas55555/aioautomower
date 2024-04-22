"""Utils for Husqvarna Automower."""

import logging
import time
from typing import Any, Mapping, cast
from urllib.parse import quote_plus, urlencode

import aiohttp
import jwt

from .const import AUTH_API_REVOKE_URL, AUTH_API_TOKEN_URL, AUTH_HEADERS, ERRORCODES
from .exceptions import ApiException
from .model import JWT, MowerAttributes, MowerList, snake_case

_LOGGER = logging.getLogger(__name__)


def structure_token(access_token: str) -> JWT:
    """Decode JWT and convert to dataclass."""
    token_decoded = jwt.decode(access_token, options={"verify_signature": False})
    return JWT.from_dict(token_decoded)


async def async_get_access_token(client_id: str, client_secret: str) -> dict[str, str]:
    """Get an access token from the Authentication API with client credentials.

    This grant type is intended only for you. If you want other
    users to use your application, then they should login using Authorization
    Code Grant.
    """
    auth_data = urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        quote_via=quote_plus,
    )
    async with (
        aiohttp.ClientSession(headers=AUTH_HEADERS) as session,
        session.post(AUTH_API_TOKEN_URL, data=auth_data) as resp,
    ):
        result = await resp.json(encoding="UTF-8")
        _LOGGER.debug("Resp.status get access token: %s", result)
        if resp.status == 200:
            result = await resp.json(encoding="UTF-8")
            result["expires_at"] = result["expires_in"] + time.time()
        if resp.status >= 400:
            raise ApiException(
                f"""The token is invalid, response from
                    Husqvarna Automower API: {result}"""
            )
    result["status"] = resp.status
    return cast(dict[str, str], result)


async def async_invalidate_access_token(
    valid_access_token: str, access_token_to_invalidate: str
) -> dict[str, str]:
    """Invalidate the token.

    :param str valid_access_token: A working access token to authorize this request.
    :param str access_token_to_delete: An access token to invalidate,
    can be th same like the first argument.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {valid_access_token}",
        "Accept": "*/*",
    }
    async with (
        aiohttp.ClientSession(headers=headers) as session,
        session.post(
            AUTH_API_REVOKE_URL, data=(f"token={access_token_to_invalidate}")
        ) as resp,
    ):
        result = await resp.json(encoding="UTF-8")
        _LOGGER.debug("Resp.status delete token: %s", resp.status)
        if resp.status >= 400:
            resp.raise_for_status()
            _LOGGER.error("Response body delete token: %s", result)
    return cast(dict[str, str], result)


def mower_list_to_dictionary_dataclass(
    mower_list: Mapping[Any, Any],
) -> dict[str, MowerAttributes]:
    """Convert mower data to a dictionary DataClass."""
    mowers_list = MowerList.from_dict(mower_list)
    mowers_dict = {}
    for mower in mowers_list.data:
        mowers_dict[mower.id] = mower.attributes
    return mowers_dict


def error_key_list() -> list[str]:
    """Create a list with all possible error keys."""
    codes = [snake_case(error_text) for error_text in ERRORCODES.values()]
    return sorted(codes)


def error_key_dict() -> dict[str, str]:
    """Create a dictionary with error keys and a human friendly text."""
    codes = {}
    for error_text in ERRORCODES.values():
        codes[snake_case(error_text)] = error_text
    return codes
