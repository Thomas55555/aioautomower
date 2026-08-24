"""Test websocket listener and callback registration."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from aioautomower.auth import AbstractAuth
from aioautomower.session import AutomowerSession


@pytest.mark.asyncio
async def test_start_listening_is_idempotent(automower_client: AbstractAuth) -> None:
    """Starting the websocket listener repeatedly must not create duplicate tasks."""

    async def wait_forever(session: AutomowerSession) -> None:
        await asyncio.Event().wait()

    automower_api = AutomowerSession(automower_client)
    with (
        patch.object(AutomowerSession, "_listen", new=wait_forever),
        patch.object(AutomowerSession, "_reconnect_scheduler", new=wait_forever),
    ):
        await automower_api.start_listening()
        ws_task = automower_api.ws_task
        reconnect_task = automower_api.reconnect_task

        await automower_api.start_listening()

        assert automower_api.ws_task is ws_task
        assert automower_api.reconnect_task is reconnect_task

    await automower_api.close()


@pytest.mark.asyncio
async def test_callback_registration_is_idempotent(
    automower_client: AbstractAuth,
) -> None:
    """Registering the same callback repeatedly must only register it once."""
    automower_api = AutomowerSession(automower_client)
    callback = Mock()

    automower_api.register_single_message_callback(callback)
    automower_api.register_single_message_callback(callback)
    automower_api.register_message_callback(callback, "mower-id")
    automower_api.register_message_callback(callback, "mower-id")

    assert automower_api.single_message_cbs == [callback]
    assert automower_api.message_update_cbs == [("mower-id", callback)]
