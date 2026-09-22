"""Unit tests for Actra state machine with extended states."""

import pytest
from actra.models import Task, TaskStatus
from actra.agent.state import transition, is_terminal, StateError


def test_initial_transitions():
    task = Task(goal="Test Goal")
    assert task.status == TaskStatus.RECEIVED

    # RECEIVED -> AUTHENTICATING
    task.status = TaskStatus.RECEIVED
    transition(task, TaskStatus.AUTHENTICATING)
    assert task.status == TaskStatus.AUTHENTICATING

    # AUTHENTICATING -> PLANNING
    transition(task, TaskStatus.PLANNING)
    assert task.status == TaskStatus.PLANNING

    # PLANNING -> EXECUTING
    transition(task, TaskStatus.EXECUTING)
    assert task.status == TaskStatus.EXECUTING

    # EXECUTING -> BLOCKED
    transition(task, TaskStatus.BLOCKED)
    assert task.status == TaskStatus.BLOCKED

    # BLOCKED -> EXECUTING
    transition(task, TaskStatus.EXECUTING)
    assert task.status == TaskStatus.EXECUTING

    # EXECUTING -> OBSERVING
    transition(task, TaskStatus.OBSERVING)
    assert task.status == TaskStatus.OBSERVING

    # OBSERVING -> VERIFYING
    transition(task, TaskStatus.VERIFYING)
    assert task.status == TaskStatus.VERIFYING

    # VERIFYING -> COMPLETED
    transition(task, TaskStatus.COMPLETED)
    assert task.status == TaskStatus.COMPLETED
    assert is_terminal(task.status) is True
    assert task.completed_at is not None


def test_system_alert_state():
    task = Task(goal="Monitor System")
    transition(task, TaskStatus.SYSTEM_ALERT)
    assert task.status == TaskStatus.SYSTEM_ALERT

    transition(task, TaskStatus.PLANNING)
    assert task.status == TaskStatus.PLANNING


def test_blocked_with_reason():
    task = Task(goal="Unverified user command")
    transition(task, TaskStatus.BLOCKED)
    task.block_reason = "UNVERIFIED: voice signature mismatch"
    assert task.status == TaskStatus.BLOCKED
    assert "UNVERIFIED" in task.block_reason


def test_invalid_transitions():
    task = Task(goal="Test Goal")
    task.mark(TaskStatus.COMPLETED)

    # Cannot transition from terminal state
    with pytest.raises(StateError):
        transition(task, TaskStatus.PLANNING)

    with pytest.raises(StateError):
        transition(task, TaskStatus.EXECUTING)
