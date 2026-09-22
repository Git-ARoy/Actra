"""Async Unix domain socket server for Actra HUD communication."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Any, Optional

from actra.hud.protocol import (
    ConfirmationRequestMessage,
    ConfirmationResponseMessage,
    HealthStatusMessage,
    TaskUpdateMessage,
    parse_message,
)
from actra.models import SafetyLevel, Task

logger = logging.getLogger(__name__)

DEFAULT_SOCKET_PATH = "/tmp/actra_hud.sock"


class HUDServer:
    """Unix domain socket server connecting the Python agent to the SwiftUI HUD."""

    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH) -> None:
        self.socket_path = socket_path
        self._server: Optional[asyncio.Server] = None
        self._clients: set[asyncio.StreamWriter] = set()
        self._pending_confirmations: dict[str, asyncio.Future[bool]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._user_command_handler: Any = None

    def set_user_command_handler(self, handler: Any) -> None:
        """Register a callback for incoming user commands from HUD."""
        self._user_command_handler = handler

    @property
    def has_connected_clients(self) -> bool:
        """Check if any HUD client is actively connected."""
        return len(self._clients) > 0

    def start(self) -> None:
        """Start the HUD server in a dedicated background daemon thread."""
        if self._running:
            return

        self._running = True
        started_event = threading.Event()

        def _run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._start_server_coro(started_event))
            self._loop.run_forever()

        self._thread = threading.Thread(target=_run_loop, daemon=True, name="ActraHUDServer")
        self._thread.start()
        started_event.wait(timeout=5.0)
        logger.info("HUD Server started listening at %s", self.socket_path)

    async def _start_server_coro(self, started_event: threading.Event) -> None:
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass

        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=self.socket_path,
        )
        started_event.set()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        logger.info("HUD Client connected to socket.")
        self._clients.add(writer)

        try:
            while True:
                line_bytes = await reader.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                try:
                    data = parse_message(line)
                    msg_type = data.get("type")
                    if msg_type == "confirmation_response":
                        conf_id = data.get("id")
                        approved = bool(data.get("approved", False))
                        if conf_id and conf_id in self._pending_confirmations:
                            fut = self._pending_confirmations.pop(conf_id)
                            if not fut.done():
                                fut.set_result(approved)
                    elif msg_type == "user_command":
                        action = data.get("action", "")
                        payload = data.get("payload", {})
                        if self._user_command_handler:
                            try:
                                self._user_command_handler(action, payload)
                            except Exception as ex:
                                logger.warning("Error in user command handler: %s", ex)
                except Exception as e:
                    logger.warning("Error handling HUD client message: %s", e)
        except (asyncio.CancelledError, ConnectionResetError):
            pass
        finally:
            self._clients.discard(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            logger.info("HUD Client disconnected.")

    def stop(self) -> None:
        """Stop the HUD server and clean up socket file."""
        self._running = False
        if self._loop and self._loop.is_running():
            def _shutdown():
                for writer in list(self._clients):
                    try:
                        writer.close()
                    except Exception:
                        pass
                self._clients.clear()
                if self._server:
                    try:
                        self._server.close()
                    except Exception:
                        pass
                if self._loop and self._loop.is_running():
                    self._loop.stop()

            self._loop.call_soon_threadsafe(_shutdown)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass
        logger.info("HUD Server stopped.")

    # ------------------------------------------------------------------
    # Broadcasting & Notification methods
    # ------------------------------------------------------------------

    def broadcast_raw(self, ndjson_message: str) -> None:
        """Send raw NDJSON string to all connected HUD clients."""
        if not self._running or not self._loop or not self._clients:
            return

        def _send():
            payload = ndjson_message.encode("utf-8")
            for writer in list(self._clients):
                try:
                    writer.write(payload)
                except Exception as e:
                    logger.warning("Failed to write to HUD client: %s", e)
                    self._clients.discard(writer)

        self._loop.call_soon_threadsafe(_send)

    def broadcast_task_update(
        self,
        task: Task,
        step_description: str = "",
        progress_percent: float = 0.0,
    ) -> None:
        """Broadcast task lifecycle and progress change to HUD."""
        msg = TaskUpdateMessage(
            task_id=task.task_id,
            goal=task.goal,
            status=task.status.value,
            step_index=task.step_index,
            step_description=step_description,
            progress_percent=progress_percent,
            retries=task.retries,
            block_reason=task.block_reason,
        )
        self.broadcast_raw(msg.to_ndjson())

    def broadcast_health(
        self,
        llm_status: str = "connected",
        cpu_percent: float = 0.0,
        memory_percent: float = 0.0,
        active_tasks: int = 0,
    ) -> None:
        """Broadcast system health status to HUD."""
        msg = HealthStatusMessage(
            llm_status=llm_status,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            active_tasks=active_tasks,
        )
        self.broadcast_raw(msg.to_ndjson())

    # ------------------------------------------------------------------
    # Confirmation round-trip
    # ------------------------------------------------------------------

    def request_confirmation_sync(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        safety_level: SafetyLevel,
        details: str = "",
        timeout: float = 60.0,
    ) -> Optional[bool]:
        """Synchronously request confirmation from HUD.
        Returns:
            True/False if confirmed/denied by HUD, or None if no HUD is connected.
        """
        if not self._running or not self._loop or not self.has_connected_clients:
            return None

        conf_id = f"conf_{uuid.uuid4().hex[:8]}"
        msg = ConfirmationRequestMessage(
            id=conf_id,
            tool=tool_name,
            arguments=arguments,
            safety_level=safety_level.name if hasattr(safety_level, "name") else str(safety_level),
            details=details,
        )

        future_done = threading.Event()
        decision_box: list[Optional[bool]] = [None]

        def _setup_async():
            fut = self._loop.create_future()
            self._pending_confirmations[conf_id] = fut

            def _on_done(f: asyncio.Future[bool]):
                try:
                    decision_box[0] = f.result()
                except Exception:
                    decision_box[0] = False
                future_done.set()

            fut.add_done_callback(_on_done)
            self.broadcast_raw(msg.to_ndjson())

        self._loop.call_soon_threadsafe(_setup_async)
        got_reply = future_done.wait(timeout=timeout)

        if not got_reply:
            logger.warning("HUD confirmation request timed out for tool %s", tool_name)
            # Remove future if still pending
            def _clean():
                self._pending_confirmations.pop(conf_id, None)
            if self._loop:
                self._loop.call_soon_threadsafe(_clean)
            return None

        return decision_box[0]


# Global singleton HUD server
_default_hud_server: Optional[HUDServer] = None


def get_hud_server(socket_path: str = DEFAULT_SOCKET_PATH) -> HUDServer:
    """Get or create the global default HUD server singleton."""
    global _default_hud_server
    if _default_hud_server is None:
        _default_hud_server = HUDServer(socket_path=socket_path)
    return _default_hud_server
