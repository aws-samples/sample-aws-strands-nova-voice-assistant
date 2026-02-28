"""WebSocket-to-BidiAgent I/O channel implementations.

Bridges the frontend WebSocket connection to BidiAgent's BidiInput/BidiOutput protocols,
enabling browser audio to flow through the BidiAgent pipeline.
"""

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from websockets.exceptions import ConnectionClosed

from strands.experimental.bidi.types import (
    BidiAudioInputEvent,
    BidiAudioStreamEvent,
    BidiConnectionCloseEvent,
    BidiConnectionRestartEvent,
    BidiConnectionStartEvent,
    BidiErrorEvent,
    BidiInputEvent,
    BidiInterruptionEvent,
    BidiOutputEvent,
    BidiResponseCompleteEvent,
    BidiResponseStartEvent,
    BidiTextInputEvent,
    BidiTranscriptStreamEvent,
)

if TYPE_CHECKING:
    from strands.experimental.bidi import BidiAgent

logger = logging.getLogger(__name__)


class WebSocketBidiInput:
    """Reads events from the frontend WebSocket and yields BidiInputEvents to BidiAgent."""

    def __init__(self, websocket):
        self._websocket = websocket
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._reader_task = None
        self._agent = None

    async def start(self, agent: "BidiAgent") -> None:
        """Start reading from the WebSocket into an internal queue."""
        self._agent = agent
        self._running = True
        self._reader_task = asyncio.create_task(self._read_loop())

    async def __call__(self) -> BidiInputEvent:
        """Return the next input event for BidiAgent. Blocks until available."""
        return await self._queue.get()

    async def stop(self) -> None:
        """Stop reading and clean up."""
        self._running = False
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

    async def _read_loop(self) -> None:
        """Read JSON messages from the WebSocket and enqueue BidiInputEvents."""
        try:
            async for raw_message in self._websocket:
                if not self._running:
                    break

                try:
                    data = json.loads(raw_message)
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON from WebSocket, skipping message")
                    continue

                msg_type = data.get("type")

                if msg_type == "bidi_audio_input":
                    event = BidiAudioInputEvent(
                        audio=data["data"],
                        format="pcm",
                        sample_rate=16000,
                        channels=1,
                    )
                    await self._queue.put(event)

                elif msg_type == "bidi_text_input":
                    event = BidiTextInputEvent(text=data["text"])
                    await self._queue.put(event)

                elif msg_type == "close":
                    logger.info("Received close signal from frontend")
                    if self._agent:
                        await self._agent.stop()
                    break

        except ConnectionClosed:
            logger.info("WebSocket connection closed, signaling agent to stop")
            if self._agent:
                await self._agent.stop()
        except asyncio.CancelledError:
            logger.info("Reader task cancelled")
            raise


class WebSocketBidiOutput:
    """Receives BidiOutputEvents from BidiAgent and forwards them over the WebSocket."""

    def __init__(self, websocket):
        self._websocket = websocket

    async def start(self, agent: "BidiAgent") -> None:
        """No-op; WebSocket is already connected."""
        pass

    async def __call__(self, event: BidiOutputEvent) -> None:
        """Serialize the event and send it over the WebSocket."""
        message = self._serialize_event(event)
        if message:
            try:
                await self._websocket.send(json.dumps(message))
            except ConnectionClosed:
                logger.warning("WebSocket closed while sending output event")

    async def stop(self) -> None:
        """No-op; WebSocket lifecycle managed by server."""
        pass

    def _serialize_event(self, event: BidiOutputEvent) -> dict | None:
        """Map a BidiOutputEvent to a JSON-serializable dictionary.

        Returns None for unrecognized event types.
        """
        if isinstance(event, BidiAudioStreamEvent):
            return {
                "type": "bidi_audio_stream",
                "data": event.audio,
                "format": event.format,
                "sample_rate": event.sample_rate,
                "channels": event.channels,
            }

        if isinstance(event, BidiTranscriptStreamEvent):
            return {
                "type": "bidi_transcript_stream",
                "role": event.role,
                "text": event.text,
                "is_final": event.is_final,
                "delta": event.text,
            }

        if isinstance(event, BidiConnectionStartEvent):
            return {
                "type": "bidi_connection_start",
                "connection_id": event.connection_id,
                "model": event.model,
            }

        if isinstance(event, BidiConnectionCloseEvent):
            return {
                "type": "bidi_connection_close",
                "connection_id": event.connection_id,
                "reason": event.reason,
            }

        if isinstance(event, BidiConnectionRestartEvent):
            return {
                "type": "bidi_connection_restart",
            }

        if isinstance(event, BidiInterruptionEvent):
            return {
                "type": "bidi_interruption",
                "reason": event.reason,
            }

        if isinstance(event, BidiResponseStartEvent):
            return {
                "type": "bidi_response_start",
                "response_id": event.response_id,
            }

        if isinstance(event, BidiResponseCompleteEvent):
            return {
                "type": "bidi_response_complete",
                "response_id": event.response_id,
                "stop_reason": event.stop_reason,
            }

        if isinstance(event, BidiErrorEvent):
            return {
                "type": "bidi_error",
                "message": event.message,
                "code": event.code,
                "details": event.details,
            }

        # Internal events (ToolResultEvent, ToolUseStreamEvent, BidiUsageEvent, etc.)
        # are handled by BidiAgent internally and don't need to be forwarded.
        logger.debug("Skipping internal BidiOutputEvent type: %s", type(event).__name__)
        return None
