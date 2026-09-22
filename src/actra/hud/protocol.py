"""NDJSON IPC protocol definitions for Actra HUD communication."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class TaskUpdateMessage:
    """Status and progress update for an active or completed task."""
    task_id: str
    goal: str
    status: str
    step_index: int = 0
    step_description: str = ""
    progress_percent: float = 0.0
    retries: int = 0
    block_reason: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    type: str = "task_update"

    def to_ndjson(self) -> str:
        return f"{json.dumps(asdict(self))}\n"


@dataclass
class ConfirmationRequestMessage:
    """Prompt sent to HUD requesting user confirmation for a sensitive/dangerous action."""
    id: str
    tool: str
    arguments: dict[str, Any]
    safety_level: str
    details: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    type: str = "confirmation_request"

    def to_ndjson(self) -> str:
        return f"{json.dumps(asdict(self))}\n"


@dataclass
class ConfirmationResponseMessage:
    """Response received from HUD with user approval decision."""
    id: str
    approved: bool
    reason: str = ""
    type: str = "confirmation_response"

    def to_ndjson(self) -> str:
        return f"{json.dumps(asdict(self))}\n"


@dataclass
class HealthStatusMessage:
    """System health and connection status update."""
    llm_status: str = "connected"
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    active_tasks: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    type: str = "health_status"

    def to_ndjson(self) -> str:
        return f"{json.dumps(asdict(self))}\n"


@dataclass
class SystemAlertMessage:
    """Proactive alert notification displayed on HUD."""
    alert_id: str
    severity: str  # 'INFO', 'WARNING', 'CRITICAL'
    title: str
    message: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    type: str = "system_alert"

    def to_ndjson(self) -> str:
        return f"{json.dumps(asdict(self))}\n"


def parse_message(raw_line: str) -> dict[str, Any]:
    """Parse a single line of NDJSON into a message dictionary."""
    stripped = raw_line.strip()
    if not stripped:
        return {}
    return json.loads(stripped)
