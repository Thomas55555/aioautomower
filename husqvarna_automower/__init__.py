"""Automower library using aiohttp."""
import time
import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)


AUTH_API_URL = 'https://api.authentication.husqvarnagroup.dev/v1/oauth2/token'
AUTH_HEADERS = {'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'}

MOWER_API_BASE_URL = 'https://api.amc.husqvarna.dev/v1/mowers/'

class GetAccessToken:
    """Class to communicate with the Authentication API."""

    def __init__(self, api_key, username, password):
        """Initialize the Auth-API and store the auth so we can make requests."""
        self.username = username
        self.password = password
        self.api_key= api_key
        self.auth_data= 'client_id={0}&grant_type=password&username={1}&password={2}'.format(self.api_key,self.username,self.password)

    async def async_get_access_token(self):
        """Return the token."""
        async with aiohttp.ClientSession(headers=AUTH_HEADERS) as session:
            async with session.post(AUTH_API_URL, data=self.auth_data) as resp:
                result = await resp.json()
                if resp.status != 200:
                    result = resp.status
        _LOGGER.info(f"result: {result}")
        _LOGGER.info(f"resp.status: {resp.status}")
        return result

class GetMowerData:
    """Class to communicate with the Automower Connect API."""

    def __init__(self, api_key, access_token, provider, token_type):
        """Initialize the Communication API to get data."""
        self.api_key= api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_headers = {'Authorization': '{0} {1}'.format(self.token_type,self.access_token),
                        'Authorization-Provider': '{0}'.format(self.provider),
                        'Content-Type': 'application/vnd.api+json',
                        'X-Api-Key': '{0}'.format(self.api_key)}

    async def async_mower_state(self):
        """Return the mowers data as a list of mowers."""
        async with aiohttp.ClientSession(headers=self.mower_headers) as session:
            async with session.get(MOWER_API_BASE_URL) as resp:
                result = await resp.json()
        return result

class Return:
    """Class to send commands to the Automower Connect API."""
    def __init__(self, api_key, access_token, provider, token_type, mower_id, payload):
        """Initialize the API and store the auth so we can make requests."""
        self.api_key= api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_id = mower_id
        self.mower_headers = {'Authorization': '{0} {1}'.format(self.token_type,self.access_token),
                        'Authorization-Provider': '{0}'.format(self.provider),
                        'Content-Type': 'application/vnd.api+json',
                        'accept': '*/*',
                        'X-Api-Key': '{0}'.format(self.api_key)}
        self.mower_action_url = f"{MOWER_API_BASE_URL}{self.mower_id}/actions"
        self.payload = payload

    async def async_mower_command(self):
        """Send a payload to the mower to execute a command."""
        async with aiohttp.ClientSession(headers=self.mower_headers) as session:
            async with session.post(self.mower_action_url, data=self.payload) as resp:
                result = await session.close()
        _LOGGER.debug(f"sent payload {self.payload}")
        _LOGGER.debug(f"API answer {resp.status}")
        time.sleep(5)
        _LOGGER.debug("Waited 5s until mower state is updated")
        return resp.status
