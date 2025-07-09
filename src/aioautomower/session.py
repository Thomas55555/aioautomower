"""Module to connect to Automower with websocket."""

import asyncio
import contextlib
import datetime
import logging
import zoneinfo
from collections.abc import Callable
from typing import Any, cast

import tzlocal
from aiohttp import WSMessage, WSMsgType

from .auth import AbstractAuth
from .commands import AutomowerEndpoint, MowerCommands
from .const import REST_POLL_CYCLE, EventTypesV2
from .exceptions import (
    HusqvarnaTimeoutError,
    NoDataAvailableError,
)
from .model import (
    MowerAttributes,
)
from .model_input import (
    CuttingHeightAttributes,
    GenericEventData,
    HeadLightAttributes,
    Message,
    MessageAttributes,
    MessageResponse,
    MowerDataItem,
    MowerDataResponse,
    PositionAttributes,
)
from .utils import mower_list_to_dictionary_dataclass

_LOGGER = logging.getLogger(__name__)


class AutomowerSession:
    """Automower API to communicate with an Automower.

    The `AutomowerSession` is the primary API service for this library. It supports
    operations like getting a status or sending commands.
    """

    __slots__ = (
        "_data",
        "_lock",
        "auth",
        "commands",
        "current_mowers",
        "data",
        "data_update_cbs",
        "last_ws_message",
        "loop",
        "mower_tz",
        "poll",
        "pong_cbs",
        "rest_task",
    )

    def __init__(
        self,
        auth: AbstractAuth,
        mower_tz: zoneinfo.ZoneInfo | None = None,
        *,
        poll: bool = False,
    ) -> None:
        """Create a session.

        :param class auth: The AbstractAuth class from aioautomower.auth.
        :param bool poll: Poll data with rest if True.
        """
        self._data: MowerDataResponse | None = None
        self.auth = auth
        self.data: dict[str, MowerAttributes] = {}
        self.mower_tz = mower_tz or tzlocal.get_localzone()
        self.commands = MowerCommands(self.auth, self.data, self.mower_tz)
        self.pong_cbs: list[Callable[[datetime.datetime], None]] = []
        self.data_update_cbs: list[Callable[[dict[str, MowerAttributes]], None]] = []
        self.last_ws_message: datetime.datetime
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self.poll = poll
        self.rest_task: asyncio.Task[None] | None = None
        self.current_mowers: set[str] = set()
        self._lock = asyncio.Lock()
        _LOGGER.debug("self.mower_tz: %s", self.mower_tz)

    def register_data_callback(
        self, callback: Callable[[dict[str, MowerAttributes]], None]
    ) -> None:
        """Register a data update callback."""
        if callback not in self.data_update_cbs:
            self.data_update_cbs.append(callback)

    def _schedule_data_callback(
        self, cb: Callable[[dict[str, MowerAttributes]], None]
    ) -> None:
        """Schedule a data callback."""
        if self.poll and self.data is None:
            raise NoDataAvailableError
        self.loop.call_soon_threadsafe(cb, self.data)

    def _schedule_data_callbacks(self) -> None:
        """Schedule a data callbacks."""
        for cb in self.data_update_cbs:
            self._schedule_data_callback(cb)

    def unregister_data_callback(
        self, callback: Callable[[dict[str, MowerAttributes]], None]
    ) -> None:
        """Unregister a data update callback.

        :param func callback: Takes one function, which should be unregistered.
        """
        if callback in self.data_update_cbs:
            self.data_update_cbs.remove(callback)

    def register_pong_callback(
        self, pong_callback: Callable[[datetime.datetime], None]
    ) -> None:
        """Register a pong callback.

        It's not real ping/pong, but a way to check if the websocket
        is still alive, by receiving an empty message.
        """
        if pong_callback not in self.pong_cbs:
            self.pong_cbs.append(pong_callback)

    def _schedule_pong_callback(self, cb: Callable[[datetime.datetime], None]) -> None:
        """Schedule a pong callback."""
        self.loop.call_soon_threadsafe(cb, self.last_ws_message)

    def _schedule_pong_callbacks(self) -> None:
        """Schedule pong callbacks."""
        for cb in self.pong_cbs:
            self._schedule_pong_callback(cb)

    def unregister_pong_callback(
        self, pong_callback: Callable[[datetime.datetime], None]
    ) -> None:
        """Unregister a pong update callback.

        :param func callback: Takes one function, which should be unregistered.
        """
        if pong_callback in self.pong_cbs:
            self.pong_cbs.remove(pong_callback)

    async def connect(self) -> None:
        """Connect to the API.

        This method handles the login. Also a REST task will be started, which
        periodically polls the REST endpoint, when polling is set to true.
        """
        self._schedule_data_callbacks()

        if self.poll:
            await self.get_status()
            for mower_id in self.current_mowers:
                await self.async_get_message(mower_id)
            self.rest_task = asyncio.create_task(self._rest_task())

    async def _handle_text_message(self, msg: WSMessage) -> None:
        """Process a text message to data."""
        if not msg.data:
            self.last_ws_message = datetime.datetime.now(tz=datetime.UTC)
            _LOGGER.debug("last_ws_message:%s", self.last_ws_message)
            self._schedule_pong_callbacks()
        if msg.data:
            msg_dict: GenericEventData = msg.json()
            if "type" in msg_dict:
                if msg_dict["type"] in {event.value for event in EventTypesV2}:
                    _LOGGER.debug("Received websocket message %s", msg_dict)
                    if msg_dict["id"] not in self.current_mowers:
                        _LOGGER.debug("New mower detected %s", msg_dict["id"])
                        self.current_mowers.add(msg_dict["id"])
                        await self.get_status()
                    self._update_data(msg_dict)
                else:
                    _LOGGER.debug("Received unknown ws type %s", msg_dict["type"])
            elif "ready" in msg_dict and "connectionId" in msg_dict:
                _LOGGER.debug(
                    "Websocket ready=%s (id='%s')",
                    msg_dict["ready"],
                    msg_dict["connectionId"],
                )

    async def start_listening(self) -> None:
        """Start listening to the websocket (and receive initial state)."""
        while not self.auth.ws.closed:
            try:
                msg = await self.auth.ws.receive(timeout=300)
                if msg.type in (
                    WSMsgType.CLOSE,
                    WSMsgType.CLOSING,
                    WSMsgType.CLOSED,
                ):
                    break
                if msg.type == WSMsgType.TEXT:
                    await self._handle_text_message(msg)
                elif msg.type == WSMsgType.ERROR:
                    continue
            except TimeoutError as exc:
                raise HusqvarnaTimeoutError from exc

    async def send_empty_message(self) -> None:
        """Send an empty message every 60s."""
        while True:
            await asyncio.sleep(60)
            _LOGGER.debug("ping:%s", datetime.datetime.now(tz=datetime.UTC))
            await self.auth.ws.send_str("")

    async def get_status(self) -> dict[str, MowerAttributes]:
        """Get mower status via REST."""
        async with self._lock:
            existing_messages: dict[str, list[Message]] = {}
            if self._data:
                existing_messages = {
                    mower["id"]: mower["attributes"].get("messages") or []
                    for mower in self._data.get("data", [])
                    if "messages" in mower["attributes"]
                }

            mower_list: MowerDataResponse = await self.auth.get_json(
                AutomowerEndpoint.mowers
            )

            for mower in mower_list.get("data", []):
                mower_id = mower.get("id")
                if mower_id in existing_messages:
                    mower["attributes"]["messages"] = existing_messages[mower_id]

            self._data = mower_list
            self.data = mower_list_to_dictionary_dataclass(self._data, self.mower_tz)
            self.current_mowers = set(self.data.keys())
            _LOGGER.debug("current_mowers: %s", self.current_mowers)
            self.commands = MowerCommands(self.auth, self.data, self.mower_tz)

            return self.data

    async def async_get_message(self, mower_id: str) -> None:
        """Fetch messages for one mower and merge into self._data."""
        messages: MessageResponse = await self.auth.get_json(
            AutomowerEndpoint.messages.format(mower_id=mower_id)
        )

        data = messages.get("data")
        attributes = data.get("attributes") if data else None

        message_list: list[Message] = []
        if attributes is not None:
            message_list = attributes.get("messages", [])
        if self._data is not None:
            async with self._lock:
                for mower in self._data["data"]:
                    if mower["id"] == mower_id:
                        mower["attributes"]["messages"] = message_list
                        break

            self.data = mower_list_to_dictionary_dataclass(self._data, self.mower_tz)

    def _update_data(self, new_data: GenericEventData) -> None:
        """Update internal data with new data from websocket."""
        if self._data is None:
            raise NoDataAvailableError

        data = self._data["data"]

        for mower in data:
            if mower["type"] == "mower" and mower["id"] == new_data["id"]:
                self._process_event(mower, new_data)
                break

        self.data = mower_list_to_dictionary_dataclass(self._data, self.mower_tz)
        self.commands = MowerCommands(self.auth, self.data, self.mower_tz)
        self._schedule_data_callbacks()

    def _process_event(self, mower: MowerDataItem, new_data: GenericEventData) -> None:
        """Process a specific event type."""
        handlers: dict[str, Callable[[MowerDataItem, Any], None]] = {
            "cuttingHeight": self._handle_cutting_height_event,
            "headlights": self._handle_headlight_event,
            "message": self._handle_message_event,
            "position": self._handle_position_event,
        }

        attributes = new_data.get("attributes", {})
        for key, handler in handlers.items():
            if key in attributes:
                handler(mower, attributes)  # Pass the specific attribute
                return
        mower_attributes = mower["attributes"]
        # General handling for other attributes
        self._update_nested_dict(cast("dict[str, Any]", mower_attributes), attributes)

    def _handle_cutting_height_event(
        self, mower: MowerDataItem, attributes: CuttingHeightAttributes
    ) -> None:
        """Handle cuttingHeight-specific updates."""
        mower["attributes"]["settings"]["cuttingHeight"] = attributes["cuttingHeight"][
            "height"
        ]

    def _handle_headlight_event(
        self, mower: MowerDataItem, attributes: HeadLightAttributes
    ) -> None:
        """Handle headLight-specific updates."""
        mower["attributes"]["settings"]["headlight"]["mode"] = attributes["headlights"][
            "mode"
        ]

    def _handle_message_event(
        self, mower: MowerDataItem, attributes: MessageAttributes
    ) -> None:
        mower["attributes"]["messages"].insert(0, attributes["message"])

    def _handle_position_event(
        self, mower: MowerDataItem, attributes: PositionAttributes
    ) -> None:
        mower["attributes"]["positions"].insert(0, attributes["position"])

    @staticmethod
    def _update_nested_dict(original: dict[str, Any], updates: dict[str, Any]) -> None:
        """Recursively update a nested dictionary with new values."""
        for key, value in updates.items():
            if (
                isinstance(value, dict)
                and key in original
                and isinstance(original[key], dict)
            ):
                AutomowerSession._update_nested_dict(original[key], value)
            else:
                original[key] = value

    async def _rest_task(self) -> None:
        """Poll data periodically via Rest."""
        while True:
            await self.get_status()
            self._schedule_data_callbacks()
            await asyncio.sleep(REST_POLL_CYCLE)

    async def close(self) -> None:
        """Close the session."""
        if self.rest_task:
            if not self.rest_task.cancelled():
                self.rest_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await asyncio.gather(self.rest_task)
