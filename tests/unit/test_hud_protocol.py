"""Unit tests for Actra HUD NDJSON protocol and server."""

import asyncio
import json
import os
import socket
import tempfile
import time
import uuid
from pathlib import Path
import pytest

from actra.hud.protocol import (
    TaskUpdateMessage,
    ConfirmationRequestMessage,
    ConfirmationResponseMessage,
    HealthStatusMessage,
    SystemAlertMessage,
    parse_message,
)
from actra.hud.server import HUDServer
from actra.models import SafetyLevel, Task, TaskStatus


@pytest.fixture
def short_sock_path():
    # macOS AF_UNIX paths must be < 104 characters, so use /tmp directly
    path = f"/tmp/actra_t_{uuid.uuid4().hex[:8]}.sock"
    yield path
    if os.path.exists(path):
        try:
            os.unlink(path)
        except OSError:
            pass


def test_protocol_serialization_roundtrip():
    # 1. TaskUpdateMessage
    task_msg = TaskUpdateMessage(
        task_id="task-123",
        goal="Test goal",
        status="EXECUTING",
        step_index=2,
        step_description="safari_open",
        progress_percent=40.0,
        retries=1,
    )
    raw = task_msg.to_ndjson()
    parsed = parse_message(raw)
    assert parsed["type"] == "task_update"
    assert parsed["task_id"] == "task-123"
    assert parsed["status"] == "EXECUTING"
    assert parsed["step_index"] == 2
    assert parsed["step_description"] == "safari_open"

    # 2. ConfirmationRequestMessage
    conf_req = ConfirmationRequestMessage(
        id="conf-456",
        tool="delete_file",
        arguments={"path": "/tmp/test.txt"},
        safety_level="DANGEROUS",
        details="Deleting file",
    )
    raw_conf = conf_req.to_ndjson()
    parsed_conf = parse_message(raw_conf)
    assert parsed_conf["type"] == "confirmation_request"
    assert parsed_conf["id"] == "conf-456"
    assert parsed_conf["tool"] == "delete_file"
    assert parsed_conf["safety_level"] == "DANGEROUS"

    # 3. ConfirmationResponseMessage
    conf_res = ConfirmationResponseMessage(id="conf-456", approved=True, reason="User approved in HUD")
    raw_res = conf_res.to_ndjson()
    parsed_res = parse_message(raw_res)
    assert parsed_res["type"] == "confirmation_response"
    assert parsed_res["approved"] is True

    # 4. HealthStatusMessage
    health = HealthStatusMessage(llm_status="ok", cpu_percent=15.2, memory_percent=45.0, active_tasks=1)
    raw_health = health.to_ndjson()
    parsed_health = parse_message(raw_health)
    assert parsed_health["type"] == "health_status"
    assert parsed_health["cpu_percent"] == 15.2


def test_hud_server_lifecycle_and_broadcast(short_sock_path: str):
    server = HUDServer(socket_path=short_sock_path)
    server.start()

    time.sleep(0.2)
    assert Path(short_sock_path).exists()
    assert server.has_connected_clients is False

    # Simulate client connection
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(short_sock_path)
    time.sleep(0.2)
    assert server.has_connected_clients is True

    # Broadcast task update
    task = Task(goal="Run HUD test")
    server.broadcast_task_update(task, step_description="Running test")

    time.sleep(0.2)
    data = client.recv(4096).decode("utf-8")
    lines = [ln.strip() for ln in data.splitlines() if ln.strip()]
    assert len(lines) > 0
    parsed = json.loads(lines[0])
    assert parsed["type"] == "task_update"
    assert parsed["task_id"] == task.task_id
    assert parsed["step_description"] == "Running test"

    client.close()
    time.sleep(0.2)
    assert server.has_connected_clients is False

    server.stop()
    time.sleep(0.1)
    assert not Path(short_sock_path).exists()


def test_hud_server_confirmation_roundtrip(short_sock_path: str):
    server = HUDServer(socket_path=short_sock_path)
    server.start()

    time.sleep(0.2)
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(short_sock_path)
    time.sleep(0.2)

    # In a separate thread, simulate HUD approving the prompt
    import threading

    def _simulated_hud_responder():
        data = client.recv(4096).decode("utf-8")
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            parsed = json.loads(line)
            if parsed.get("type") == "confirmation_request":
                req_id = parsed["id"]
                resp = json.dumps({"type": "confirmation_response", "id": req_id, "approved": True}) + "\n"
                client.sendall(resp.encode("utf-8"))

    responder_thread = threading.Thread(target=_simulated_hud_responder, daemon=True)
    responder_thread.start()

    # Request confirmation synchronously
    approved = server.request_confirmation_sync(
        tool_name="delete_file",
        arguments={"path": "/tmp/important.txt"},
        safety_level=SafetyLevel.DANGEROUS,
        timeout=5.0,
    )

    assert approved is True

    client.close()
    server.stop()


def test_hud_server_unconnected_fallback(short_sock_path: str):
    server = HUDServer(socket_path=short_sock_path)
    server.start()

    # When no HUD client is connected, request_confirmation_sync immediately returns None
    res = server.request_confirmation_sync("delete_file", {}, SafetyLevel.DANGEROUS)
    assert res is None

    server.stop()
