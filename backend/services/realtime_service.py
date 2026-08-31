
from typing import Dict, Any, Optional
from loguru import logger
import os
import sys
import asyncio

try:
    import socketio
except ImportError:
    socketio = None

# Add backend directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


class RealtimeService:
    """
    InsForge Realtime service.

    InsForge Realtime uses Socket.IO/WebSockets rather than a REST
    endpoint such as /realtime/v1/broadcast.
    """

    def __init__(self):
        """Initialize the realtime service."""

        self.insforge_url = os.getenv("INSFORGE_URL")
        self.insforge_anon_key = os.getenv("INSFORGE_ANON_KEY")

        self.enabled = bool(
            self.insforge_url and self.insforge_anon_key
        )

        self.sio = None
        self.connected = False
        self._connect_lock = asyncio.Lock()

        if not self.enabled:
            logger.info(
                "Realtime service disabled "
                "(INSFORGE_URL or INSFORGE_ANON_KEY not set)"
            )
            return

        if socketio is None:
            logger.warning(
                "python-socketio is not installed. "
                "Realtime features disabled."
            )
            self.enabled = False
            return

        logger.info(
            f"Realtime service initialized: {self.insforge_url}"
        )

    async def _connect(self) -> bool:
        """Connect to the InsForge Socket.IO realtime server."""

        if not self.enabled or socketio is None:
            return False

        if self.connected and self.sio:
            return True

        async with self._connect_lock:

            if self.connected and self.sio:
                return True

            try:
                self.sio = socketio.AsyncClient(
                    reconnection=True,
                    reconnection_attempts=3,
                    logger=False,
                    engineio_logger=False,
                )

                @self.sio.event
                async def connect():
                    self.connected = True
                    logger.info(
                        "Connected to InsForge realtime"
                    )

                @self.sio.event
                async def disconnect():
                    self.connected = False
                    logger.warning(
                        "Disconnected from InsForge realtime"
                    )

                @self.sio.event
                async def connect_error(data):
                    self.connected = False
                    logger.warning(
                        f"InsForge realtime connection error: {data}"
                    )

                # InsForge's realtime service is exposed through
                # the main InsForge backend URL.
                await self.sio.connect(
    self.insforge_url,
    socketio_path="socket.io",
    transports=["websocket"],
    headers={
        "Authorization": f"Bearer {self.insforge_anon_key}",
        "apikey": self.insforge_anon_key,
    },
    wait_timeout=5,
)

                return self.connected

            except Exception as e:
                self.connected = False

                logger.warning(
                    f"Could not connect to InsForge realtime: {e}"
                )

                self.sio = None

                return False

    async def _subscribe(self, channel: str) -> bool:
        """Subscribe to an InsForge realtime channel."""

        if not await self._connect():
            return False

        try:
            # InsForge realtime requires subscription before
            # publishing to a channel.
            await self.sio.emit(
                "subscribe",
                {
                    "channel": channel,
                },
            )

            return True

        except Exception as e:
            logger.warning(
                f"Failed to subscribe to realtime channel "
                f"{channel}: {e}"
            )
            return False

    async def broadcast_progress(
        self,
        investigation_id: str,
        step: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Broadcast investigation progress through InsForge Realtime.

        Args:
            investigation_id:
                Unique investigation identifier.

            step:
                Current investigation step.

            details:
                Optional additional information.

        Returns:
            True if the message was sent successfully.
            False if realtime is unavailable.
        """

        if not self.enabled:
            return False

        channel = f"investigation:{investigation_id}"

        # Make sure we are connected.
        if not await self._connect():
            return False

        try:
            # InsForge requires subscribing before publishing.
            subscribed = await self._subscribe(channel)

            if not subscribed:
                return False

            payload = {
                "step": step,
                "investigation_id": investigation_id,
                "details": details or {},
            }

            # Publish through Socket.IO instead of the old
            # /realtime/v1/broadcast REST endpoint.
            await self.sio.emit(
                "publish",
                {
                    "channel": channel,
                    "event": "progress",
                    "payload": payload,
                },
            )

            logger.info(
                f"Broadcasted realtime progress: {step}"
            )

            return True

        except Exception as e:
            logger.warning(
                f"Failed to broadcast realtime progress: {e}"
            )
            return False

    async def close(self):
        """Close the realtime connection."""

        if self.sio and self.connected:
            try:
                await self.sio.disconnect()
            except Exception as e:
                logger.debug(
                    f"Error closing realtime connection: {e}"
                )

        self.connected = False
        self.sio = None

    def is_enabled(self) -> bool:
        """Return whether realtime is configured and available."""

        return self.enabled