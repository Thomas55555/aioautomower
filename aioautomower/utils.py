"""Utils for Husqvarna Automower."""
import logging
import time
from urllib.parse import quote_plus, urlencode

import aiohttp
import jwt

from .const import AUTH_API_REVOKE_URL, AUTH_API_TOKEN_URL, AUTH_HEADERS
from .model import JWT
from .rest import TokenError

_LOGGER = logging.getLogger(__name__)


async def async_structure_token(access_token) -> JWT:
    """Decode JWT and convert to dataclass."""
    token_decoded = jwt.decode(access_token, options={"verify_signature": False})
    return JWT(**token_decoded)


async def async_get_access_token(client_id, client_secret) -> dict:
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
    async with aiohttp.ClientSession(headers=AUTH_HEADERS) as session, session.post(
        AUTH_API_TOKEN_URL, data=auth_data
    ) as resp:
        result = await resp.json(encoding="UTF-8")
        _LOGGER.debug("Resp.status get access token: %s", result)
        if resp.status == 200:
            result = await resp.json(encoding="UTF-8")
            result["expires_at"] = result["expires_in"] + time.time()
        if resp.status >= 400:
            raise TokenError(
                f"""The token is invalid, respone from
                    Husqvarna Automower API: {result}"""
            )
    result["status"] = resp.status
    return result


async def async_invalidate_access_token(
    valid_access_token, access_token_to_invalidate
) -> dict:
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
    async with aiohttp.ClientSession(headers=headers) as session, session.post(
        AUTH_API_REVOKE_URL, data=(f"token={access_token_to_invalidate}")
    ) as resp:
        result = await resp.json(encoding="UTF-8")
        _LOGGER.debug("Resp.status delete token: %s", resp.status)
        if resp.status >= 400:
            resp.raise_for_status()
            _LOGGER.error("Response body delete token: %s", result)
    return result
