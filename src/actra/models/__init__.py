"""Actra data models — task state, tool results, and events."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskStatus(str, Enum):
    """Lifecycle states for an Actra task."""

    RECEIVED = "RECEIVED"
    AUTHENTICATING = "AUTHENTICATING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    OBSERVING = "OBSERVING"
    VERIFYING = "VERIFYING"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    SYSTEM_ALERT = "SYSTEM_ALERT"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SafetyLevel(str, Enum):
    """Risk classification for tools."""

    SAFE = "SAFE"
    SENSITIVE = "SENSITIVE"
    DANGEROUS = "DANGEROUS"


# ---------------------------------------------------------------------------
# Tool result
# ---------------------------------------------------------------------------

class ToolError(BaseModel):
    """Structured error from a tool execution."""

    code: str
    message: str


class ToolResult(BaseModel):
    """Standardized result returned by every tool."""

    success: bool
    tool: str
    data: dict[str, Any] | None = None
    error: ToolError | None = None

    @classmethod
    def ok(cls, tool: str, **data: Any) -> ToolResult:
        return cls(success=True, tool=tool, data=data)

    @classmethod
    def fail(cls, tool: str, code: str, message: str) -> ToolResult:
        return cls(
            success=False,
            tool=tool,
            error=ToolError(code=code, message=message),
        )


# ---------------------------------------------------------------------------
# Plan step
# ---------------------------------------------------------------------------

class PlanStep(BaseModel):
    """A single step in an execution plan."""

    description: str
    tool: str | None = None
    arguments: dict[str, Any] | None = None
    completed: bool = False
    result: ToolResult | None = None


# ---------------------------------------------------------------------------
# Verification models
# ---------------------------------------------------------------------------

class CheckEvidence(BaseModel):
    """Evidence for an individual deterministic goal verification check."""

    name: str
    passed: bool
    evidence: str = ""


class GoalVerificationResult(BaseModel):
    """Structured result from goal-level outcome verification."""

    verified: bool
    checks: list[CheckEvidence] = Field(default_factory=list)
    reason: str = ""


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class Task(BaseModel):
    """Represents an active or completed Actra task."""

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    status: TaskStatus = TaskStatus.RECEIVED
    plan: list[PlanStep] = Field(default_factory=list)
    step_index: int = 0
    observations: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    verification: GoalVerificationResult | None = None
    retries: int = 0
    max_retries: int = 3
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None
    error_message: str | None = None
    block_reason: str | None = None

    def mark(self, status: TaskStatus) -> None:
        """Transition to a new status."""
        self.status = status
        if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            self.completed_at = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Task event (for logging / future streaming)
# ---------------------------------------------------------------------------

class TaskEvent(BaseModel):
    """An event emitted during task execution."""

    task_id: str
    event: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    data: dict[str, Any] = Field(default_factory=dict)

