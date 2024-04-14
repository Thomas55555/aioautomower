# Aioautomower

Asynchronous library to communicate with the Automower Connect API
To use this library, you need to register on the [Husqvarna Developers Portal](https://developer.husqvarnagroup.cloud/).
And connect your account to the `Authentication API` and the `Automower Connect API`.

## Quickstart

In order to use the library, you'll need to do some work yourself to get authentication
credentials. This depends a lot on the context (e.g. redirecting to use OAuth via web)
but should be easy to incorporate using Husqvarna's authentication examples. See
Husqvarna's [Authentication API](https://developer.husqvarnagroup.cloud/apis/authentication-api) for details.

You will implement `AbstractAuth` to provide an access token. Your implementation
will handle any necessary refreshes. You can invoke the service with your auth implementation
to access the API.

For a first start you can run the `example.py`, by doing the following steps

- `git clone https://github.com/Thomas55555/aioautomower.git`
- `pip install -e ./`
- Enter your personal `client_id` and `client_secret` in the `example.py`
- Run with `python3 ./aioautomower/example.py`
