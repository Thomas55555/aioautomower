# Aioautomower

Asynchronous library to communicate with the Automower Connect API

## REST API Examples

```python
from aioautomower import GetAccessToken, GetMowerData, Return
from aiohttp import ClientError
from aiohttp.client_exceptions import ClientConnectorError
import asyncio

api_key = "12345678-abcd-1234-a1a1-efghijklmnop" ## Your API-Key
username = "username" ## Your username
password = "password" ## Your password


class ExampleToken:
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

class MowerData:
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
    def __init__(self, api_key, access_token, provider, token_type, mower_id, payload, command_type):
        self.api_key = api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_id = mower_id
        self.payload = payload
        self.command_type = command_type

    async def mowers(self):
        try:
            send = Return(
                self.api_key,
                self.access_token,
                self.provider,
                self.token_type,
                self.mower_id,
                self.payload
                self.command_type
            )
            send = await send.async_mower_command()
        except Exception:
            return "Something went wrong"
        return send


example = ExampleToken(api_key, username, password)
token_output = asyncio.run(example.token())
print(token_output)

access_token = token_output["access_token"]
provider = token_output["provider"]
token_type = token_output["token_type"]

example2 = MowerData(api_key, access_token, provider, token_type)
mower_output = asyncio.run(example2.mowers())
print(mower_output)

mower_id = mower_output["data"][0]["id"] ## '0' is your first mower
print ("Mower ID:", mower_id)
command_type = "actions"
payload = '{"data": {"type": "ResumeSchedule"}}'  ## For more commands see: https://developer.husqvarnagroup.cloud/apis/Automower+Connect+API#/swagger
example3 = SendingCommand(api_key, access_token, provider, token_type, mower_id, payload, command_type)
result = asyncio.run(example3.mowers())
print (result)  ## if, 202, then okay
```

## AutomowerSession examples

An AutomowerSession keeps track of the access token, refreshing it whenever
needed and monitors a websocket for updates, whose data is sent to callbacks
provided by the user.

```python
import asyncio
import logging

import aioautomower

USERNAME = "user@name.com"
PASSWORD = "mystringpassword"
API_KEY = "12312312-0126-6222-2662-3e6c49f0012c"


async def main():
    sess = aioautomower.AutomowerSession(API_KEY, token=None)

    # Add a callback, can be done at any point in time and
    # multiple callbacks can be added.
    sess.register_cb(lambda data:print(data))

    # If no token was passed to the constructor, we need to call login()
    # before connect(). The token can be stored somewhere and passed to
    # the constructor later on.
    token = await sess.login(USERNAME, PASSWORD)

    if not await sess.connect():
        # If the token is still None or too old, the connect will fail.
        print("Connect failed")
        return
    await asyncio.sleep(5)
    status = await sess.get_status()
    print(status)
    await asyncio.sleep(30)

    # The close() will stop the websocket and the token refresh tasks
    await sess.close()

asyncio.run(main())
```
