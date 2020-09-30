import requests
import json
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
        """Return the token"""
        async with aiohttp.ClientSession(headers=AUTH_HEADERS) as session:
            async with session.post(AUTH_API_URL, data=self.auth_data) as resp:
                result = await resp.json()
        return result

class GetMowerData:
    """Class to communicate with the Automower Connect API."""

    def __init__(self, api_key, access_token, provider, token_type):
        """Initialize the API."""
        self.api_key= api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_headers = {'Authorization': '{0} {1}'.format(self.token_type,self.access_token),
                        'Authorization-Provider': '{0}'.format(self.provider),
                        'Content-Type': 'application/vnd.api+json',
                        'X-Api-Key': '{0}'.format(self.api_key)}

    async def async_mower_state(self):
        """Return the mowers data as a list of mowers"""
        async with aiohttp.ClientSession(headers=self.mower_headers) as session:
            async with session.get(MOWER_API_BASE_URL) as resp:
                result = await resp.json()
        return result

class Return:
    """Class to send commands to the Automower Connect API."""
    def __init__(self, api_key, access_token, provider, token_type, mower_id):
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


    def mower_parkuntilfurthernotice(self):
        """Return the token"""
        self.payload = '{"data": {"type": "ParkUntilFurtherNotice"}}'
        self.resp = requests.post(self.mower_action_url, headers=self.mower_headers, data=self.payload)
        _LOGGER.info("befehl wurde gesendet")
        _LOGGER.info('action_url: {0} \n mower_headers: {1} \n Payload: {2} \n payload_json: {3} \n'.format(self.mower_action_url,self.mower_headers,self.payload,json.dumps(self.payload)))
        _LOGGER.info(f"{self.resp}")
        # self.resp.raise_for_status()
        # self.resp_raw_dict = json.loads(self.resp.content.decode('utf-8'))
        return self.resp.status_code

    def mower_pause(self):
        """Return the token"""
        self.payload = '{"data": {"type": "Pause"}}'
        self.resp = requests.post(self.mower_action_url, headers=self.mower_headers, data=self.payload)
        _LOGGER.info("befehl wurde gesendet")
        _LOGGER.info('action_url: {0} \n mower_headers: {1} \n Payload: {2} \n payload_json: {3} \n'.format(self.mower_action_url,self.mower_headers,self.payload,json.dumps(self.payload)))
        _LOGGER.info(f"{self.resp}")
        # self.resp.raise_for_status()
        # self.resp_raw_dict = json.loads(self.resp.content.decode('utf-8'))
        return self.resp.status_code

    def mower_parkuntilnextschedule(self):
        """Return the token"""
        self.payload = '{"data": {"type": "ParkUntilNextSchedule"}}'
        self.resp = requests.post(self.mower_action_url, headers=self.mower_headers, data=self.payload)
        _LOGGER.info("befehl wurde gesendet")
        _LOGGER.info('action_url: {0} \n mower_headers: {1} \n Payload: {2} \n payload_json: {3} \n'.format(self.mower_action_url,self.mower_headers,self.payload,json.dumps(self.payload)))
        _LOGGER.info(f"{self.resp}")
        # self.resp.raise_for_status()
        # self.resp_raw_dict = json.loads(self.resp.content.decode('utf-8'))
        return self.resp.status_code

    def mower_resumeschedule(self):
        """Resume Scheudele"""
        self.payload = '{"data": {"type": "ResumeSchedule"}}'
        self.resp = requests.post(self.mower_action_url, headers=self.mower_headers, data=self.payload)
        _LOGGER.info("befehl wurde gesendet")
        _LOGGER.info('action_url: {0} \n mower_headers: {1} \n Payload: {2} \n payload_json: {3} \n'.format(self.mower_action_url,self.mower_headers,self.payload,json.dumps(self.payload)))
        _LOGGER.info(f"{self.resp}")
        # self.resp.raise_for_status()
        # self.resp_raw_dict = json.loads(self.resp.content.decode('utf-8'))
        return self.resp.status_code