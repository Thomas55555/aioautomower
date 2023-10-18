"""Utils for Husqvarna Automower."""
import logging
import time
from urllib.parse import quote_plus, urlencode

import aiohttp
import jwt

from .const import AUTH_API_TOKEN_URL, AUTH_HEADERS
from .model import JWT
from .rest import TokenError

_LOGGER = logging.getLogger(__name__)


async def async_structure_token(access_token) -> JWT:
    """Decode JWT and convert to dataclass."""
    token_decoded = jwt.decode(access_token, options={"verify_signature": False})
    return JWT(**token_decoded)


async def async_get_access_token(client_id, client_secret, websession) -> dict:
    """Function to get an acces token from the Authentication API with client
    credentials. This grant type is intended only for you. If you want other
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
    async with aiohttp.ClientSession(headers=AUTH_HEADERS) as session:
        async with session.post(AUTH_API_TOKEN_URL, data=auth_data) as resp:
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
