"""Unit tests for Actra data models."""

import pytest
from actra.models import (
    Task, TaskStatus, ToolResult, ToolError, PlanStep, TaskEvent, SafetyLevel,
)


class TestToolResult:
    def test_ok_creates_success(self):
        result = ToolResult.ok("test_tool", key="value")
        assert result.success is True
        assert result.tool == "test_tool"
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_fail_creates_failure(self):
        result = ToolResult.fail("test_tool", "ERR_CODE", "Something broke")
        assert result.success is False
        assert result.tool == "test_tool"
        assert result.error is not None
        assert result.error.code == "ERR_CODE"
        assert result.error.message == "Something broke"

    def test_serialization_roundtrip(self):
        result = ToolResult.ok("test_tool", files=["a.txt", "b.txt"])
        dumped = result.model_dump()
        restored = ToolResult(**dumped)
        assert restored.success is True
        assert restored.data["files"] == ["a.txt", "b.txt"]


class TestTask:
    def test_default_values(self):
        task = Task(goal="Test goal")
        assert task.status == TaskStatus.RECEIVED
        assert task.step_index == 0
        assert task.retries == 0
        assert task.task_id  # UUID generated
        assert task.created_at is not None
        assert task.completed_at is None

    def test_mark_completed(self):
        task = Task(goal="Test goal")
        task.mark(TaskStatus.COMPLETED)
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None

    def test_mark_failed(self):
        task = Task(goal="Test goal")
        task.mark(TaskStatus.FAILED)
        assert task.status == TaskStatus.FAILED
        assert task.completed_at is not None

    def test_mark_non_terminal_leaves_completed_at_none(self):
        task = Task(goal="Test goal")
        task.mark(TaskStatus.PLANNING)
        assert task.status == TaskStatus.PLANNING
        assert task.completed_at is None


class TestPlanStep:
    def test_default_values(self):
        step = PlanStep(description="Open Safari")
        assert step.completed is False
        assert step.tool is None
        assert step.result is None


class TestTaskEvent:
    def test_creation(self):
        event = TaskEvent(task_id="abc-123", event="tool_completed", data={"tool": "open_application"})
        assert event.task_id == "abc-123"
        assert event.event == "tool_completed"
        assert event.timestamp is not None


class TestSafetyLevel:
    def test_values(self):
        assert SafetyLevel.SAFE == "SAFE"
        assert SafetyLevel.SENSITIVE == "SENSITIVE"
        assert SafetyLevel.DANGEROUS == "DANGEROUS"
