# Aioautomower

[![codecov](https://codecov.io/gh/Thomas55555/aioautomower/graph/badge.svg?token=2BG3S61T6K)](https://codecov.io/gh/Thomas55555/aioautomower)
[![Python Versions](https://img.shields.io/pypi/pyversions/aioautomower)](https://pypi.org/project/aioautomower/)
[![License](https://img.shields.io/github/license/Thomas55555/aioautomower.svg)](LICENSE.md)

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

You need at least:

- Python 3.11+
- [Poetry][poetry-install]

For a first start you can run the `example.py`, by doing the following steps

- `git clone https://github.com/Thomas55555/aioautomower.git`
- `cd aioautomower`
- `poetry install`
- Enter your personal `client_id` and `client_secret` in the `_secrets.yaml` and rename it to `secrets.yaml`
- Run with `poetry run ./example.py`

## Contributing

This is an active open-source project. We are always open to people who want to use the code or contribute to it.
This Python project is fully managed using the [Poetry][poetry] dependency manager.

As this repository uses the [pre-commit][pre-commit] framework, all changes
are linted and tested with each commit. You can run all checks and tests
manually, using the following command:

```bash
poetry run pre-commit run --all-files
```

To run just the Python tests:

```bash
poetry run pytest
```

To update snapshots:

```bash
poetry run pytest --snapshot-update
```

[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[pre-commit]: https://pre-commit.com/


# Buying Equipment

Many mowers are available from your local garden dealer or major online retailers. Another like, the compact ideal for small and flat lawns, is available on Amazon.
The links provided below are affiliate links, so if you prefer shopping on Amazon and decide to purchase something there, you’ll also be supporting me at no additional cost to you.
Alternatively, if you'd like to support the project directly, consider contributing through [GitHub sponsors](https://github.com/sponsors/Thomas55555).
Here are some affiliate links to support my work:
- [Automower R4 Aspire](https://amzn.to/3Z987Oc)
- [Endurence blades](https://amzn.to/3OyK1YD)
- [Regular blades](https://amzn.to/3ZCn8Zt)
- [Cabel connector](https://amzn.to/4f3OtJn)
