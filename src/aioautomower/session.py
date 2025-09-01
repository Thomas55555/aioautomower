"""Module to connect to Automower with websocket."""

import asyncio
import contextlib
import datetime
import logging
import zoneinfo
from collections.abc import Callable
from typing import Any, cast

import tzlocal
from aiohttp import ClientError, WSMessage, WSMsgType

from .auth import AbstractAuth
from .commands import AutomowerEndpoint, MowerCommands
from .const import REST_POLL_CYCLE, EventTypesV2
from .exceptions import HusqvarnaTimeoutError, NoDataAvailableError, NoValidDataError
from .model import Message, MessageData, MowerAttributes, SingleMessageData
from .model_input import (
    CuttingHeightAttributes,
    GenericEventData,
    HeadLightAttributes,
    MowerDataItem,
    MowerDataResponse,
    PositionAttributes,
)
from .utils import mower_list_to_dictionary_dataclass

_LOGGER = logging.getLogger(__name__)

INVALID_MOWER_ID = "0-0"


class AutomowerSession:
    """Automower API to communicate with an Automower.

    The `AutomowerSession` is the primary API service for this library. It supports
    operations like getting a status or sending commands.
    """

    __slots__ = (
        "_data",
        "auth",
        "commands",
        "current_mowers",
        "data",
        "data_update_cbs",
        "last_ws_message",
        "loop",
        "message_update_cbs",
        "messages",
        "mower_tz",
        "poll",
        "pong_cbs",
        "rest_task",
        "single_message",
        "single_message_cbs",
        "ws_ready_cbs",
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
        :param class mower_tz: The ZoneInfo object for the mower, default is None
        :param bool poll: Poll data with rest if True.
        """
        self._data: MowerDataResponse | None = None
        self.auth = auth
        self.mower_tz = mower_tz or tzlocal.get_localzone()
        self.data: dict[str, MowerAttributes] = {}
        self.commands = MowerCommands(self.auth, self.data, self.mower_tz)
        self.current_mowers: set[str] = set()
        self.data_update_cbs: list[Callable[[dict[str, MowerAttributes]], None]] = []
        self.last_ws_message: datetime.datetime
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self.message_update_cbs: list[tuple[str, Callable[[MessageData], None]]] = []
        self.single_message_cbs: list[Callable[[SingleMessageData], None]] = []
        self.single_message: SingleMessageData | None = None
        self.messages: dict[str, MessageData] = {}
        self.poll = poll
        self.pong_cbs: list[Callable[[datetime.datetime], None]] = []
        self.rest_task: asyncio.Task[None] | None = None
        self.ws_ready_cbs: list[Callable[[], None]] = []
        _LOGGER.debug("self.mower_tz: %s", self.mower_tz)

    def register_data_callback(
        self, callback: Callable[[dict[str, MowerAttributes]], None]
    ) -> None:
        """Register a data update callback."""
        if callback not in self.data_update_cbs:
            self.data_update_cbs.append(callback)

    def unregister_data_callback(
        self, callback: Callable[[dict[str, MowerAttributes]], None]
    ) -> None:
        """Unregister a data update callback.

        :param func callback: Takes one function, which should be unregistered.
        """
        if callback in self.data_update_cbs:
            self.data_update_cbs.remove(callback)

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

    def register_single_message_callback(
        self, cb: Callable[[SingleMessageData], None]
    ) -> None:
        """Register a callback for the latest single message of a specific mower."""
        self.single_message_cbs.append(cb)

    def unregister_single_message_callback(
        self,
        cb: Callable[[SingleMessageData], None],
    ) -> None:
        """Unregister a single message callback for a specific mower."""
        if cb in self.single_message_cbs:
            self.single_message_cbs.remove(cb)

    def _schedule_single_message_callbacks(self, message: SingleMessageData) -> None:
        """Dispatch only the most recent message to registered callbacks."""
        for cb in self.single_message_cbs:
            self.loop.call_soon_threadsafe(cb, message)

    def register_message_callback(
        self,
        callback: Callable[[MessageData], None],
        mower_id: str,
    ) -> None:
        """Register a callback triggered when new messages arrive for specific mower."""
        self.message_update_cbs.append((mower_id, callback))

    def unregister_message_callback(
        self,
        callback: Callable[[MessageData], None],
        mower_id: str,
    ) -> None:
        """Unregister a previously registered message callback."""
        self.message_update_cbs.remove((mower_id, callback))

    def _schedule_message_callback(
        self,
        msg_data: MessageData,
        cb: Callable[[MessageData], None],
    ) -> None:
        """Schedule a single message data callback (thread-safe)."""
        self.loop.call_soon_threadsafe(cb, msg_data)

    def _schedule_message_callbacks(self, msg_data: MessageData) -> None:
        """Schedule all registered message data callbacks for the given mower."""
        for mower_id, cb in self.message_update_cbs:
            if mower_id == msg_data.id:
                self._schedule_message_callback(msg_data, cb)

    def register_ws_ready_callback(self, cb: Callable[[], None]) -> None:
        """Register a callback that is called when WebSocket is ready."""
        if cb not in self.ws_ready_cbs:
            self.ws_ready_cbs.append(cb)

    def _schedule_ws_ready_callback(self) -> None:
        """Schedule all ws_ready callbacks (thread-safe)."""
        if not self.ws_ready_cbs:
            return
        for cb in list(self.ws_ready_cbs):
            try:
                self.loop.call_soon_threadsafe(cb)
            except RuntimeError:
                _LOGGER.exception("Error while scheduling ws_ready callback %s", cb)

    def unregister_ws_ready_callback(self, cb: Callable[[], None]) -> None:
        """Unregister a ws_ready callback."""
        if cb in self.ws_ready_cbs:
            self.ws_ready_cbs.remove(cb)

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
                await self.async_get_messages(mower_id)
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
                self._schedule_ws_ready_callback()

    async def start_listening(self) -> None:
        """Start listening to the websocket (and receive initial state)."""
        ws = self.auth.ws
        if ws is None:
            exc = RuntimeError("WebSocket not connected")
            raise exc
        while not ws.closed:
            try:
                msg = await ws.receive(timeout=300)
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

    async def send_empty_message(self, ping_timeout: int = 5) -> bool:
        """Send a single ping with timeout (in seconds)."""
        ws = getattr(self.auth, "ws", None)
        if ws is None:
            _LOGGER.debug("WebSocket not connected—skipping ping")
            return False

        try:
            await asyncio.wait_for(ws.send_str(""), timeout=ping_timeout)
        except TimeoutError:
            return False
        except ClientError as err:
            _LOGGER.warning("Ping failed due to client error: %s", err)
            return False

        return True

    async def get_status(self) -> dict[str, MowerAttributes]:
        """Get mower status via REST."""
        mower_list: MowerDataResponse = await self.auth.get_json(
            AutomowerEndpoint.mowers
        )
        self._data = mower_list
        for mower in self._data["data"]:
            if mower["id"] == INVALID_MOWER_ID:
                raise NoValidDataError
        self.data = mower_list_to_dictionary_dataclass(self._data, self.mower_tz)
        self.current_mowers = set(self.data.keys())
        _LOGGER.debug("current_mowers: %s", self.current_mowers)
        self.commands = MowerCommands(self.auth, self.data, self.mower_tz)
        return self.data

    async def async_get_messages(self, mower_id: str) -> MessageData:
        """Fetch messages for one mower and merge into self._messages."""
        raw_data = await self.auth.get_json(
            AutomowerEndpoint.messages.format(mower_id=mower_id)
        )
        msg_resp = MessageData.from_dict(raw_data["data"])
        msg_resp.id = mower_id
        self.messages[mower_id] = msg_resp
        return msg_resp

    def _update_data(self, new_data: GenericEventData) -> None:
        """Update internal data with new data from websocket."""
        if new_data["type"] == EventTypesV2.MESSAGES:
            if self.messages:
                new_msg = Message.from_dict(new_data["attributes"]["message"])
                mower_id = new_data["id"]
                self.messages[mower_id].attributes.messages.insert(0, new_msg)
                self._schedule_message_callbacks(self.messages[mower_id])
            if not self.messages:
                single_message = SingleMessageData.from_dict(new_data)
                if single_message != self.single_message:
                    self.single_message = single_message
                    self._schedule_single_message_callbacks(self.single_message)
                else:
                    _LOGGER.debug(
                        "Received same single message as before, not updating."
                    )

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
        for mower_id, cb in self.message_update_cbs[:]:
            self.unregister_message_callback(cb, mower_id)
