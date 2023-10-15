"""Utils for Husqvarna Automower."""
import jwt

from .model import JWT


async def async_structure_token(access_token) -> JWT:
    """Decode JWT and convert to dataclass."""
    token_decoded = jwt.decode(access_token, options={"verify_signature": False})
    return JWT(**token_decoded)
