# Aioautomower

## Asynchronous library to communicate with the Automower Connect API

## This library is under development.

```python
from aioautomower import GetAccessToken, GetMowerData, Return
from aiohttp import ClientError
from aiohttp.client_exceptions import ClientConnectorError
import asyncio

api_key = "12345678-abcd-1234-a1a1-efghijklmnop" ## Your API-Key
username = "username" ## Your username
password = "password" ## Your password


class Example_Token:
    """Returns the access token as dict."""
    def __init__(self, api_key, username, password):
        self.api_key = api_key
        self.username = username
        self.password = password

    async def token(self):
        try:
            get_token = GetAccessToken(
                self.api_key,
                self.username,
                self.password,
            )
            access_token_raw = await get_token.async_get_access_token()
        except (ClientConnectorError, ClientError):
            raise KeyError
        return access_token_raw

class Mower_Data:
    """Returns the data of all mowers as dict."""
    def __init__(self, api_key, access_token, provider, token_type):
        self.api_key = api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type

    async def mowers(self):
        try:
            get_mower_data = GetMowerData(
                self.api_key,
                self.access_token,
                self.provider,
                self.token_type,
            )
            mower_data = await get_mower_data.async_mower_state()
        except (ClientConnectorError, ClientError):
            return "Make sure, you are connected to the Authentication API and the Automower API"
        return mower_data

class SendingCommand:
    """Returns the data of all mowers as dict."""
    def __init__(self, api_key, access_token, provider, token_type, mower_id, payload):
        self.api_key = api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_id = mower_id
        self.payload = payload

    async def mowers(self):
        try:
            send = Return(
                self.api_key,
                self.access_token,
                self.provider,
                self.token_type,
                self.mower_id ,
            )
            send = await send.async_mower_command()
        except Exception:
            return "Something went wrong"
        return send


example = Example_Token(api_key, username, password)
token_output = asyncio.run(example.token())
print(token_output)

access_token = token_output["access_token"]
provider = token_output["provider"]
token_type = token_output["token_type"]

example2 = Mower_Data(api_key, access_token, provider, token_type)
mower_output = asyncio.run(example2.mowers())
print(mower_output)

mower_id = mower_output["data"][0]["id"] ## '0' is your first mower
print (mower_id)
payload = '{"data": {"type": "ResumeSchedule"}}'  ## For more commands see: https://developer.husqvarnagroup.cloud/apis/Automower+Connect+API#/swagger
SendingCommand(api_key, access_token, provider, token_type, mower_id, payload)
```